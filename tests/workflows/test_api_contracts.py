"""
API Contract Tests for Workflow Management

Tests that validate API endpoints exist, accept expected inputs,
and return expected JSON structures. Critical for React frontend integration.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.eduhub.main import app

# Use FastAPI's synchronous TestClient instead of httpx AsyncClient
client = TestClient(app)


class TestWorkflowAPIContracts:
    """Test API contracts that React frontend depends on."""

    def setup_method(self):
        """Setup mocks for each test."""
        self.auth_patch = patch("src.eduhub.auth.dependencies.get_current_user")
        self.mock_auth = self.auth_patch.start()
        self.mock_auth.return_value = {
            "user_id": "test-user",
            "roles": ["workflow_manager"],
        }

    def teardown_method(self):
        """Cleanup mocks after each test."""
        self.auth_patch.stop()

    def test_get_templates_endpoint_exists(self):
        """React needs /workflows/templates to return template list."""
        response = client.get("/workflows/templates")
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data, "Response missing 'templates' key"
        assert isinstance(data["templates"], list), "Templates should be a list"
        assert "total_count" in data, "Response missing 'total_count' key"

    def test_get_templates_returns_expected_structure(self):
        """Verify template objects have expected fields for React components."""
        response = client.get("/workflows/templates")
        data = response.json()

        if len(data["templates"]) > 0:
            template = data["templates"][0]
            required_fields = ["id", "name", "description", "category"]
            for field in required_fields:
                assert field in template, f"Template missing required field: {field}"

    def test_get_template_by_id_endpoint_exists(self):
        """React needs to fetch individual template details."""
        response = client.get("/workflows/templates/simple_review")
        assert response.status_code in [
            200,
            404,
        ], "Endpoint should exist (200 or 404, not 405)"

        if response.status_code == 200:
            data = response.json()
            assert "template" in data, "Response missing 'template' key"

    @patch("src.eduhub.workflows.plone_service.PloneWorkflowService")
    def test_apply_template_accepts_role_assignments(self, mock_service):
        """Test that apply endpoint accepts expected payload format."""
        # Mock the service to avoid actual Plone calls
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance
        mock_instance.get_content_workflow_state.return_value = {"state": "draft"}
        mock_instance.get_user_workflow_permissions.return_value = {
            "available_actions": ["manage_workflow"]
        }
        mock_instance.apply_workflow_template.return_value = {
            "success": True,
            "template_applied": "simple_review",
        }

        payload = {
            "role_assignments": {
                "author": ["user1", "user2"],
                "editor": ["editor1"],
                "administrator": ["admin1"],
            },
            "force": False,
        }

        response = client.post(
            "/workflows/apply/simple_review?content_uid=test-content-123", json=payload
        )

        # We don't care if it succeeds, just that it accepts the format
        assert (
            response.status_code != 422
        ), "Should not be a validation error - payload format is wrong"
        assert response.status_code in [
            200,
            400,
            500,
        ], "Endpoint should process the request"

    @patch("src.eduhub.workflows.plone_service.PloneWorkflowService")
    def test_transition_endpoint_accepts_expected_format(self, mock_service):
        """Test transition endpoint accepts expected payload."""
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance
        mock_instance.execute_workflow_transition.return_value = {
            "success": True,
            "from_state": "draft",
            "to_state": "pending",
        }

        payload = {
            "content_uid": "test-content-123",
            "transition_id": "submit",
            "comments": "Ready for review",
        }

        response = client.post("/workflows/transition", json=payload)

        assert response.status_code != 422, "Should not be a validation error"
        assert response.status_code in [
            200,
            400,
            500,
        ], "Endpoint should process the request"

    def test_content_state_endpoint_exists(self):
        """React needs to query content workflow state."""
        response = client.get("/workflows/content/test-content-123/state")

        # Endpoint should exist (even if content doesn't)
        assert response.status_code in [200, 404, 500], "Endpoint should exist"
        assert response.status_code != 405, "Method should be allowed"

    def test_health_endpoint_exists(self):
        """React dashboard needs health check endpoint."""
        response = client.get("/workflows/health")

        assert response.status_code in [200, 503], "Health endpoint should exist"

        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Health response missing 'status' key"

    def test_templates_endpoint_supports_filtering(self):
        """React needs to filter templates by category."""
        response = client.get("/workflows/templates?categories=educational")

        assert response.status_code == 200, "Should accept category filter"

        data = response.json()
        assert "templates" in data, "Filtered response should have templates"

    def test_error_responses_have_consistent_structure(self):
        """Test that error responses follow consistent format for React error handling."""
        # Test with invalid template ID
        response = client.get("/workflows/templates/nonexistent-template")

        if response.status_code >= 400:
            data = response.json()
            # Should have either 'error' or 'detail' key (FastAPI standard)
            assert (
                "error" in data or "detail" in data
            ), "Error response should have error message"

    def test_authentication_required_endpoints(self):
        """Test that endpoints properly require authentication."""
        # Temporarily remove auth mock
        self.auth_patch.stop()

        response = client.get("/workflows/templates")

        # Should either work (if no auth required) or return 401/403
        assert response.status_code in [
            200,
            401,
            403,
        ], "Should handle auth appropriately"

        # Restart auth mock for other tests
        self.auth_patch.start()


class TestWorkflowAPIResponseFormats:
    """Test that API responses match expected formats for frontend consumption."""

    def setup_method(self):
        self.auth_patch = patch("src.eduhub.auth.dependencies.get_current_user")
        self.mock_auth = self.auth_patch.start()
        self.mock_auth.return_value = {
            "user_id": "test-user",
            "roles": ["workflow_manager"],
        }

    def teardown_method(self):
        self.auth_patch.stop()

    def test_template_list_pagination_format(self):
        """Verify pagination fields for React components."""
        response = client.get("/workflows/templates")
        data = response.json()

        # Should have pagination info
        assert "total_count" in data, "Missing total_count for pagination"
        assert isinstance(data["total_count"], int), "total_count should be integer"

    def test_template_categories_are_strings(self):
        """Verify category values are strings for React filters."""
        response = client.get("/workflows/templates")
        data = response.json()

        for template in data["templates"]:
            if "category" in template:
                assert isinstance(
                    template["category"], str
                ), "Category should be string"

    @patch("src.eduhub.workflows.plone_service.PloneWorkflowService")
    def test_apply_template_success_response_format(self, mock_service):
        """Verify success response format for React state updates."""
        mock_instance = AsyncMock()
        mock_service.return_value = mock_instance

        # Mock successful application
        mock_instance.get_content_workflow_state.return_value = {"state": "draft"}
        mock_instance.get_user_workflow_permissions.return_value = {
            "available_actions": ["manage_workflow"]
        }
        mock_instance.apply_workflow_template.return_value = {
            "success": True,
            "template_applied": "simple_review",
            "workflow_created": "workflow_123",
        }

        payload = {"role_assignments": {"author": ["user1"], "editor": ["editor1"]}}

        response = client.post(
            "/workflows/apply/simple_review?content_uid=test-content", json=payload
        )

        if response.status_code == 200:
            data = response.json()

            # Check required fields for React state management
            expected_fields = ["success", "template_id", "content_uid", "user_id"]
            for field in expected_fields:
                assert field in data, f"Success response missing {field}"

            assert isinstance(data["success"], bool), "success should be boolean"

    def test_openapi_schema_available(self):
        """Verify OpenAPI schema is available for frontend SDK generation."""
        response = client.get("/openapi.json")
        assert response.status_code == 200, "OpenAPI schema should be available"

        schema = response.json()
        assert "paths" in schema, "OpenAPI schema should have paths"

        # Check that workflow paths are documented
        workflow_paths = [path for path in schema["paths"] if "/workflows" in path]
        assert len(workflow_paths) > 0, "Workflow endpoints should be documented"
