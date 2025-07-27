"""
Smoke Integration Tests for Workflow Management

Simple tests that verify major components can work together.
These are lightweight tests focused on integration points.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.eduhub.main import app
from src.eduhub.workflows.models import EducationRole
from src.eduhub.workflows.permissions import map_eduhub_to_plone_roles
from src.eduhub.workflows.templates import get_template

client = TestClient(app)


class TestBasicIntegration:
    """Test that basic integration points work."""

    def test_app_starts_with_workflow_endpoints(self):
        """Test that the app starts and includes workflow endpoints."""
        # This tests that our workflow module integrates properly with FastAPI
        response = client.get("/")
        assert response.status_code == 200, "App should start successfully"

        # Check that OpenAPI includes our endpoints
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200

        schema = openapi_response.json()
        workflow_paths = [path for path in schema["paths"] if "/workflows" in path]
        assert len(workflow_paths) > 0, "Workflow endpoints should be registered"

    @patch("src.eduhub.auth.dependencies.get_current_user")
    def test_template_endpoint_integration(self, mock_auth):
        """Test end-to-end template retrieval."""
        mock_auth.return_value = {"user_id": "test-user", "roles": ["workflow_manager"]}

        # This tests: FastAPI -> endpoints -> templates -> models
        response = client.get("/workflows/templates")
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0, "Should return actual templates"

        # Verify template structure matches what get_template returns
        api_template = data["templates"][0]
        template_id = api_template["id"]

        # Get same template via direct function call
        direct_template = get_template(template_id)
        assert direct_template is not None
        assert direct_template.id == api_template["id"]

    def test_role_mapping_integration(self):
        """Test that role mapping works with actual templates."""
        # Get a real template
        template = get_template("simple_review")
        assert template is not None

        # Create role assignments
        role_assignments = {
            EducationRole.AUTHOR: ["user1", "user2"],
            EducationRole.EDITOR: ["editor1"],
        }

        # Test mapping
        plone_assignments = map_eduhub_to_plone_roles(role_assignments)

        assert "Author" in plone_assignments
        assert "Editor" in plone_assignments
        assert plone_assignments["Author"] == ["user1", "user2"]
        assert plone_assignments["Editor"] == ["editor1"]

    @patch("src.eduhub.auth.dependencies.get_current_user")
    @patch("src.eduhub.workflows.plone_service.PloneWorkflowService")
    def test_apply_template_integration(self, mock_service_class, mock_auth):
        """Test template application integration without actual Plone."""
        mock_auth.return_value = {"user_id": "test-user", "roles": ["workflow_manager"]}

        # Mock the service instance
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        # Setup service responses
        mock_service.get_content_workflow_state.return_value = {
            "state": "draft",
            "workflow_id": "test_workflow",
        }
        mock_service.get_user_workflow_permissions.return_value = {
            "available_actions": ["manage_workflow"]
        }
        mock_service.apply_workflow_template.return_value = {
            "success": True,
            "template_applied": "simple_review",
            "workflow_created": "workflow_123",
        }

        # Test the full API call
        payload = {"role_assignments": {"author": ["user1"], "editor": ["editor1"]}}

        response = client.post(
            "/workflows/apply/simple_review?content_uid=test-content", json=payload
        )

        # Should succeed and return expected structure
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["template_id"] == "simple_review"


class TestModuleImports:
    """Test that all workflow modules can be imported together."""

    def test_all_workflow_modules_importable(self):
        """Test that we can import all workflow modules without errors."""
        try:
            from src.eduhub.workflows import (
                audit,
                endpoints,
                models,
                permissions,
                plone_service,
                services,
                templates,
            )

            # If we get here, all imports worked
            assert True

        except ImportError as e:
            pytest.fail(f"Failed to import workflow module: {e}")

    def test_template_models_integration(self):
        """Test that templates use models correctly."""
        template = get_template("simple_review")

        # Test that template contains proper model instances
        assert hasattr(template, "states")
        assert hasattr(template, "transitions")

        # Test that states have proper structure
        if len(template.states) > 0:
            state = template.states[0]
            assert hasattr(state, "id")
            assert hasattr(state, "name")
            assert hasattr(state, "permissions")

    def test_permissions_models_integration(self):
        """Test that permissions module works with models."""
        from src.eduhub.workflows.models import EducationRole, WorkflowAction
        from src.eduhub.workflows.permissions import RolePermissionMapper

        mapper = RolePermissionMapper()

        # Test that mapper can handle model enums
        author_role = mapper.get_plone_role(EducationRole.AUTHOR)
        assert isinstance(author_role, str)

        view_permission = mapper.get_plone_permission(WorkflowAction.VIEW)
        assert isinstance(view_permission, str)


class TestHealthChecks:
    """Simple health checks for workflow system."""

    @patch("src.eduhub.auth.dependencies.get_current_user")
    def test_workflow_health_endpoint(self, mock_auth):
        """Test workflow health check."""
        mock_auth.return_value = {"user_id": "test-user", "roles": ["viewer"]}

        response = client.get("/workflows/health")

        # Should exist and return some status
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    def test_templates_loadable(self):
        """Test that all built-in templates can be loaded."""
        templates = ["simple_review", "extended_review"]

        for template_id in templates:
            template = get_template(template_id)
            assert template is not None, f"Template {template_id} should be loadable"
            assert template.id == template_id

    def test_basic_workflow_components_functional(self):
        """Test that basic workflow components are functional."""
        # Test template loading
        template = get_template("simple_review")
        assert template is not None

        # Test role mapping
        from src.eduhub.workflows.permissions import RolePermissionMapper

        mapper = RolePermissionMapper()
        assert mapper is not None

        # Test basic mapping
        plone_role = mapper.get_plone_role(EducationRole.AUTHOR)
        assert plone_role == "Author"


class TestConfiguration:
    """Test workflow system configuration and setup."""

    def test_workflow_routes_registered(self):
        """Test that workflow routes are properly registered."""
        # Check that FastAPI app includes workflow routes
        route_paths = [route.path for route in app.routes if hasattr(route, "path")]

        workflow_routes = [path for path in route_paths if "/workflows" in path]
        assert len(workflow_routes) > 0, "Workflow routes should be registered"

        # Check for key routes
        expected_routes = [
            "/workflows/templates",
            "/workflows/templates/{template_id}",
            "/workflows/apply/{template_id}",
            "/workflows/health",
        ]

        for expected in expected_routes:
            # Check if route exists (may have different parameter names)
            route_exists = any(
                expected.replace("{template_id}", "{") in path
                for path in workflow_routes
            )
            assert route_exists, f"Expected route pattern {expected} should exist"

    def test_workflow_tags_configured(self):
        """Test that workflow endpoints have proper OpenAPI tags."""
        openapi_response = client.get("/openapi.json")
        schema = openapi_response.json()

        # Find workflow operations
        workflow_operations = []
        for path, methods in schema.get("paths", {}).items():
            if "/workflows" in path:
                for method, operation in methods.items():
                    if "tags" in operation:
                        workflow_operations.extend(operation["tags"])

        # Should have workflow-related tags
        assert len(workflow_operations) > 0, "Workflow operations should have tags"
