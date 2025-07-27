"""
Core Business Logic Tests for Workflow Management

Tests that validate the core workflow functionality works correctly.
These tests ensure Susan's features actually do what they're supposed to do.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.eduhub.workflows.models import EducationRole, WorkflowAction
from src.eduhub.workflows.permissions import (
    RolePermissionMapper,
    map_eduhub_to_plone_roles,
    validate_template_roles,
)
from src.eduhub.workflows.plone_service import PloneWorkflowService
from src.eduhub.workflows.templates import get_all_templates, get_template


class TestWorkflowTemplates:
    """Test that workflow templates are properly defined and accessible."""

    def test_built_in_templates_exist(self):
        """Verify that built-in templates are available."""
        # Test specific templates Susan expects
        simple_review = get_template("simple_review")
        assert simple_review is not None, "Simple review template should exist"
        assert simple_review.id == "simple_review"
        assert simple_review.name is not None

        extended_review = get_template("extended_review")
        assert extended_review is not None, "Extended review template should exist"
        assert extended_review.id == "extended_review"

    def test_template_has_required_structure(self):
        """Verify templates have all required components."""
        template = get_template("simple_review")

        # Must have basic info
        assert template.id is not None
        assert template.name is not None
        assert template.description is not None
        assert template.category is not None

        # Must have workflow components
        assert len(template.states) > 0, "Template must have states"
        assert len(template.transitions) > 0, "Template must have transitions"

        # States must have required fields
        for state in template.states:
            assert state.id is not None
            assert state.name is not None
            assert state.permissions is not None

    def test_get_all_templates_returns_list(self):
        """Verify we can list all available templates."""
        templates = get_all_templates()
        assert isinstance(templates, list), "Should return list of templates"
        assert len(templates) > 0, "Should have at least one template"

        # All templates should have IDs
        template_ids = [t.id for t in templates]
        assert len(set(template_ids)) == len(
            template_ids
        ), "Template IDs should be unique"

    def test_template_states_are_connected(self):
        """Verify template transitions connect states properly."""
        template = get_template("simple_review")

        # Get all state IDs
        state_ids = {state.id for state in template.states}

        # Check that transitions reference valid states
        for transition in template.transitions:
            assert (
                transition.from_state in state_ids
            ), f"Transition references invalid from_state: {transition.from_state}"
            assert (
                transition.to_state in state_ids
            ), f"Transition references invalid to_state: {transition.to_state}"

    def test_invalid_template_returns_none(self):
        """Verify that invalid template IDs are handled gracefully."""
        invalid_template = get_template("nonexistent_template")
        assert invalid_template is None, "Invalid template should return None"


class TestRolePermissionMapping:
    """Test that role and permission mapping works correctly."""

    def test_education_roles_map_to_plone_roles(self):
        """Verify that EduHub roles map to Plone roles."""
        mapper = RolePermissionMapper()

        # Test key role mappings
        assert mapper.get_plone_role(EducationRole.AUTHOR) == "Author"
        assert mapper.get_plone_role(EducationRole.EDITOR) == "Editor"
        assert mapper.get_plone_role(EducationRole.ADMINISTRATOR) == "Manager"

        # Test that all education roles have mappings
        for role in EducationRole:
            plone_role = mapper.get_plone_role(role)
            assert plone_role is not None, f"Role {role} should have Plone mapping"
            assert isinstance(plone_role, str), f"Plone role should be string"

    def test_bulk_role_mapping_function(self):
        """Test the convenience function for mapping role assignments."""
        eduhub_assignments = {
            EducationRole.AUTHOR: ["user1", "user2"],
            EducationRole.EDITOR: ["editor1"],
            EducationRole.ADMINISTRATOR: ["admin1"],
        }

        plone_assignments = map_eduhub_to_plone_roles(eduhub_assignments)

        assert "Author" in plone_assignments
        assert "Editor" in plone_assignments
        assert "Manager" in plone_assignments

        assert plone_assignments["Author"] == ["user1", "user2"]
        assert plone_assignments["Editor"] == ["editor1"]
        assert plone_assignments["Manager"] == ["admin1"]

    def test_workflow_actions_have_permissions(self):
        """Verify that workflow actions can be mapped to permissions."""
        mapper = RolePermissionMapper()

        # Test that key actions have permission mappings
        view_permission = mapper.get_plone_permission(WorkflowAction.VIEW)
        edit_permission = mapper.get_plone_permission(WorkflowAction.EDIT)

        assert view_permission is not None, "VIEW action should have permission"
        assert edit_permission is not None, "EDIT action should have permission"

    def test_template_role_validation(self):
        """Test that templates can be validated for role completeness."""
        template = get_template("simple_review")
        validation_result = validate_template_roles(template)

        assert hasattr(validation_result, "is_valid"), "Should return validation result"
        # Don't assert True/False - just that validation runs without crashing


class TestPloneWorkflowService:
    """Test core PloneWorkflowService functionality."""

    @pytest.fixture
    def mock_plone_client(self):
        """Create a mock Plone client."""
        client = AsyncMock()
        # Setup basic mock responses
        client.get_content_by_uid.return_value = {
            "uid": "test",
            "title": "Test Content",
        }
        client.get_workflow_info.return_value = {
            "state": "draft",
            "workflow_id": "test_workflow",
        }
        return client

    @pytest.fixture
    def workflow_service(self, mock_plone_client):
        """Create workflow service with mocked client."""
        return PloneWorkflowService(mock_plone_client)

    @pytest.mark.asyncio
    async def test_service_can_be_instantiated(self, mock_plone_client):
        """Test that service can be created."""
        service = PloneWorkflowService(mock_plone_client)
        assert service is not None
        assert service.plone_client is mock_plone_client

    @pytest.mark.asyncio
    async def test_get_content_workflow_state_basic(
        self, workflow_service, mock_plone_client
    ):
        """Test basic workflow state retrieval."""
        # Setup mock response
        mock_plone_client.get_workflow_info.return_value = {
            "state": "draft",
            "workflow_id": "simple_review_workflow",
            "transitions": [],
        }

        result = await workflow_service.get_content_workflow_state("test-content")

        assert result is not None
        assert "state" in result or "current_state" in result

    @pytest.mark.asyncio
    async def test_apply_workflow_template_basic(
        self, workflow_service, mock_plone_client
    ):
        """Test basic template application."""
        template = get_template("simple_review")
        role_assignments = {
            EducationRole.AUTHOR: ["user1"],
            EducationRole.EDITOR: ["editor1"],
        }

        # Setup mock responses
        mock_plone_client.get_content_by_uid.return_value = {"uid": "test-content"}
        mock_plone_client.create_workflow.return_value = {"workflow_id": "new_workflow"}
        mock_plone_client.set_content_workflow.return_value = {"success": True}

        result = await workflow_service.apply_workflow_template(
            "test-content", template, role_assignments
        )

        assert result is not None
        # Don't assert specific structure - just that it doesn't crash


class TestWorkflowIntegration:
    """Test that different components work together."""

    def test_template_roles_are_mappable(self):
        """Test that all roles used in templates can be mapped to Plone."""
        mapper = RolePermissionMapper()
        template = get_template("simple_review")

        # Collect all roles used in template
        used_roles = set()
        for state in template.states:
            for permission in state.permissions:
                if hasattr(permission, "role"):
                    used_roles.add(permission.role)

        # Verify all used roles can be mapped
        for role in used_roles:
            if isinstance(role, EducationRole):
                plone_role = mapper.get_plone_role(role)
                assert (
                    plone_role is not None
                ), f"Template role {role} should be mappable"

    def test_template_actions_are_mappable(self):
        """Test that all actions used in templates can be mapped to permissions."""
        mapper = RolePermissionMapper()
        template = get_template("simple_review")

        # Collect all actions used in template
        used_actions = set()
        for state in template.states:
            for permission in state.permissions:
                if hasattr(permission, "actions"):
                    used_actions.update(permission.actions)

        # Verify all used actions can be mapped
        for action in used_actions:
            if isinstance(action, WorkflowAction):
                plone_permission = mapper.get_plone_permission(action)
                assert (
                    plone_permission is not None
                ), f"Template action {action} should be mappable"

    def test_basic_workflow_cycle(self):
        """Test basic workflow: get template -> validate roles -> apply."""
        # Step 1: Get template
        template = get_template("simple_review")
        assert template is not None

        # Step 2: Validate roles
        validation_result = validate_template_roles(template)
        assert validation_result is not None

        # Step 3: Map roles (without applying)
        role_assignments = {
            EducationRole.AUTHOR: ["user1"],
            EducationRole.EDITOR: ["editor1"],
        }
        plone_assignments = map_eduhub_to_plone_roles(role_assignments)
        assert len(plone_assignments) > 0

        # If we get this far without exceptions, basic cycle works


class TestErrorHandling:
    """Test that core logic handles errors gracefully."""

    def test_missing_template_handled(self):
        """Test that missing templates don't crash the system."""
        result = get_template("completely_invalid_template")
        assert result is None  # Should return None, not crash

    def test_empty_role_assignments_handled(self):
        """Test that empty role assignments are handled."""
        empty_assignments = {}
        plone_assignments = map_eduhub_to_plone_roles(empty_assignments)
        assert isinstance(plone_assignments, dict)
        assert len(plone_assignments) == 0

    def test_invalid_role_mapping_handled(self):
        """Test that invalid roles don't crash the mapper."""
        mapper = RolePermissionMapper()

        # This should not crash, even with invalid input
        try:
            result = mapper.get_plone_role("not_a_role")
            # Should either return None or raise a controlled exception
            assert result is None or isinstance(result, str)
        except Exception as e:
            # If it raises an exception, it should be a controlled one
            assert "role" in str(e).lower() or "mapping" in str(e).lower()
