"""
Unit tests for PloneWorkflowService.

Tests the integration between workflow templates and Plone CMS,
including template application, role assignment, and permission management.
"""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.eduhub.workflows.models import (
    EducationRole,
    StateType,
    WorkflowAction,
    WorkflowPermission,
    WorkflowState,
    WorkflowTemplate,
    WorkflowTransition,
)
from src.eduhub.workflows.plone_service import PloneWorkflowError, PloneWorkflowService
from src.eduhub.workflows.templates import get_template


# Module-level fixtures that can be used across all test classes
@pytest.fixture
async def mock_plone_client():
    """Create a mock PloneClient for testing."""
    client = AsyncMock()

    # Mock common responses
    client.get_content_by_uid.return_value = {
        "uid": "test-content-uid",
        "title": "Test Content",
        "@type": "Document",
    }

    client.get_workflow_info.return_value = {
        "state": "draft",
        "workflow_id": "simple_publication_workflow",
        "transitions": [{"id": "submit", "title": "Submit for Review"}],
        "history": [],
    }

    return client


@pytest.fixture
def workflow_service(mock_plone_client):
    """Create PloneWorkflowService instance with mocked client."""
    return PloneWorkflowService(mock_plone_client)


@pytest.fixture
def simple_template():
    """Get simple review template for testing."""
    return get_template("simple_review")


@pytest.fixture
def role_assignments():
    """Sample role assignments for testing."""
    return {
        EducationRole.AUTHOR: ["user123", "user456"],
        EducationRole.EDITOR: ["reviewer789"],
        EducationRole.ADMINISTRATOR: ["admin001"],
    }


class TestPloneWorkflowService:
    """Test suite for PloneWorkflowService."""


class TestGetContentWorkflowState:
    """Test get_content_workflow_state method."""

    @pytest.mark.asyncio
    async def test_get_workflow_state_success(
        self, workflow_service, mock_plone_client
    ):
        """Test successful workflow state retrieval."""
        content_uid = "test-content-uid"

        # Setup mock responses
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Document",
            "@type": "Document",
            "workflow_template_metadata": {
                "template_id": "simple_review",
                "applied_at": "2024-01-01T00:00:00Z",
            },
        }

        mock_plone_client.get_workflow_info.return_value = {
            "state": "draft",
            "workflow_id": "template_simple_review",
            "transitions": [{"id": "submit_for_review", "title": "Submit for Review"}],
            "history": [],
        }

        # Execute
        result = await workflow_service.get_content_workflow_state(content_uid)

        # Verify
        assert result["content_uid"] == content_uid
        assert result["current_state"] == "draft"
        assert result["workflow_id"] == "template_simple_review"
        assert result["content_title"] == "Test Document"
        assert result["template_metadata"]["template_id"] == "simple_review"

        # Verify API calls
        mock_plone_client.get_content_by_uid.assert_called_once_with(content_uid)
        mock_plone_client.get_workflow_info.assert_called_once_with(content_uid)

    @pytest.mark.asyncio
    async def test_get_workflow_state_content_not_found(
        self, workflow_service, mock_plone_client
    ):
        """Test error when content is not found."""
        content_uid = "nonexistent-uid"
        mock_plone_client.get_content_by_uid.return_value = None

        with pytest.raises(
            PloneWorkflowError, match="Content with UID nonexistent-uid not found"
        ):
            await workflow_service.get_content_workflow_state(content_uid)

    @pytest.mark.asyncio
    async def test_get_workflow_state_plone_error(
        self, workflow_service, mock_plone_client
    ):
        """Test error handling when Plone API fails."""
        content_uid = "test-content-uid"
        mock_plone_client.get_content_by_uid.side_effect = Exception("Plone API error")

        with pytest.raises(PloneWorkflowError, match="Failed to get workflow state"):
            await workflow_service.get_content_workflow_state(content_uid)


class TestApplyWorkflowTemplate:
    """Test apply_workflow_template method."""

    @pytest.mark.asyncio
    async def test_apply_template_success(
        self, workflow_service, mock_plone_client, simple_template, role_assignments
    ):
        """Test successful template application."""
        content_uid = "test-content-uid"

        # Setup mocks for successful application
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
            "@type": "Document",
        }

        mock_plone_client.get_workflow_info.return_value = {
            "state": "private",
            "workflow_id": "simple_publication_workflow",
            "transitions": [],
            "history": [],
        }

        # Mock the various workflow operations
        mock_plone_client.create_workflow = AsyncMock()
        mock_plone_client.assign_workflow_to_content = AsyncMock()
        mock_plone_client.assign_local_roles = AsyncMock()
        mock_plone_client.update_content_metadata = AsyncMock()
        mock_plone_client.set_workflow_state = AsyncMock()

        # Execute
        result = await workflow_service.apply_workflow_template(
            content_uid, simple_template, role_assignments
        )

        # Verify result structure
        assert result["success"] is True
        assert result["content_uid"] == content_uid
        assert result["template_id"] == simple_template.id
        assert result["initial_state"] == "draft"
        assert "workflow_id" in result
        assert "backup_info" in result
        assert "applied_at" in result

        # Verify role assignments
        assert result["role_assignments"]["author"] == ["user123", "user456"]
        assert result["role_assignments"]["editor"] == ["reviewer789"]

        # Verify API calls were made
        mock_plone_client.create_workflow.assert_called_once()
        mock_plone_client.assign_workflow_to_content.assert_called_once()
        mock_plone_client.update_content_metadata.assert_called_once()
        mock_plone_client.set_workflow_state.assert_called_once_with(
            content_uid, "draft"
        )

    @pytest.mark.asyncio
    async def test_apply_template_content_not_found(
        self, workflow_service, mock_plone_client, simple_template, role_assignments
    ):
        """Test error when applying template to non-existent content."""
        content_uid = "nonexistent-uid"
        mock_plone_client.get_content_by_uid.return_value = None

        with pytest.raises(
            PloneWorkflowError, match="Content with UID nonexistent-uid not found"
        ):
            await workflow_service.apply_workflow_template(
                content_uid, simple_template, role_assignments
            )

    @pytest.mark.asyncio
    async def test_apply_template_already_has_template(
        self, workflow_service, mock_plone_client, simple_template, role_assignments
    ):
        """Test error when content already has a template applied."""
        content_uid = "test-content-uid"

        # Mock content with existing template
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
            "@type": "Document",
        }

        mock_plone_client.get_workflow_info.return_value = {
            "state": "draft",
            "workflow_id": "template_existing",
            "transitions": [],
            "history": [],
        }

        # Mock existing template metadata
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "template_metadata": {"template_id": "existing_template"}
            }

            with pytest.raises(
                PloneWorkflowError,
                match="Content already has template existing_template applied",
            ):
                await workflow_service.apply_workflow_template(
                    content_uid, simple_template, role_assignments, force=False
                )

    @pytest.mark.asyncio
    async def test_apply_template_with_force(
        self, workflow_service, mock_plone_client, simple_template, role_assignments
    ):
        """Test force application over existing template."""
        content_uid = "test-content-uid"

        # Setup mocks
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
            "@type": "Document",
        }

        # Mock existing template metadata
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "template_metadata": {"template_id": "existing_template"}
            }

            # Mock workflow operations
            mock_plone_client.create_workflow = AsyncMock()
            mock_plone_client.assign_workflow_to_content = AsyncMock()
            mock_plone_client.assign_local_roles = AsyncMock()
            mock_plone_client.update_content_metadata = AsyncMock()
            mock_plone_client.set_workflow_state = AsyncMock()

            # Should succeed with force=True
            result = await workflow_service.apply_workflow_template(
                content_uid, simple_template, role_assignments, force=True
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_apply_template_rollback_on_failure(
        self, workflow_service, mock_plone_client, simple_template, role_assignments
    ):
        """Test rollback when template application fails."""
        content_uid = "test-content-uid"

        # Setup mocks for initial success
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
            "@type": "Document",
        }

        mock_plone_client.get_workflow_info.return_value = {
            "state": "private",
            "workflow_id": "simple_publication_workflow",
            "transitions": [],
            "history": [],
        }

        # Mock successful backup but failed workflow creation
        mock_plone_client.create_workflow = AsyncMock(
            side_effect=Exception("Workflow creation failed")
        )

        # Mock rollback operations
        mock_plone_client.assign_workflow_to_content = AsyncMock()
        mock_plone_client.set_workflow_state = AsyncMock()
        mock_plone_client.update_content_metadata = AsyncMock()

        with pytest.raises(PloneWorkflowError, match="Template application failed"):
            await workflow_service.apply_workflow_template(
                content_uid, simple_template, role_assignments
            )


class TestExecuteWorkflowTransition:
    """Test execute_workflow_transition method."""

    @pytest.mark.asyncio
    async def test_execute_transition_success(
        self, workflow_service, mock_plone_client
    ):
        """Test successful transition execution."""
        content_uid = "test-content-uid"
        transition_id = "submit_for_review"
        user_id = "user123"
        comments = "Ready for review"

        # Mock current workflow state
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "current_state": "draft",
                "template_metadata": {
                    "template_id": "simple_review",
                    "role_assignments": {"author": ["user123"]},
                },
            }

            # Mock successful transition
            mock_plone_client.execute_workflow_transition.return_value = {
                "new_state": "review",
                "history_entry": {
                    "action": transition_id,
                    "actor": user_id,
                    "time": datetime.utcnow().isoformat(),
                },
            }

            # Mock permission validation
            mock_plone_client.can_user_execute_transition.return_value = True

            # Mock history update
            workflow_service._update_workflow_history = AsyncMock()

            # Execute
            result = await workflow_service.execute_workflow_transition(
                content_uid, transition_id, user_id, comments
            )

            # Verify
            assert result["success"] is True
            assert result["content_uid"] == content_uid
            assert result["transition_id"] == transition_id
            assert result["executed_by"] == user_id
            assert result["from_state"] == "draft"
            assert result["to_state"] == "review"
            assert result["comments"] == comments

            # Verify API calls
            mock_plone_client.execute_workflow_transition.assert_called_once_with(
                content_uid, transition_id, comments
            )

    @pytest.mark.asyncio
    async def test_execute_transition_no_template_metadata(
        self, workflow_service, mock_plone_client
    ):
        """Test error when content has no template metadata."""
        content_uid = "test-content-uid"
        transition_id = "submit_for_review"
        user_id = "user123"

        # Mock workflow state without template metadata
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "current_state": "draft",
                "template_metadata": {},
            }

            with pytest.raises(
                PloneWorkflowError,
                match="Content does not have workflow template metadata",
            ):
                await workflow_service.execute_workflow_transition(
                    content_uid, transition_id, user_id
                )

    @pytest.mark.asyncio
    async def test_execute_transition_permission_denied(
        self, workflow_service, mock_plone_client
    ):
        """Test error when user lacks permission for transition."""
        content_uid = "test-content-uid"
        transition_id = "approve_content"
        user_id = "user123"

        # Mock current workflow state
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "current_state": "review",
                "template_metadata": {
                    "template_id": "simple_review",
                    "role_assignments": {"author": ["user123"]},
                },
            }

            # Mock permission validation failure
            with patch.object(
                workflow_service, "_validate_transition_permissions"
            ) as mock_validate:
                mock_validate.side_effect = PloneWorkflowError(
                    "User lacks required role"
                )

                with pytest.raises(
                    PloneWorkflowError, match="User lacks required role"
                ):
                    await workflow_service.execute_workflow_transition(
                        content_uid, transition_id, user_id
                    )


class TestGetUserWorkflowPermissions:
    """Test get_user_workflow_permissions method."""

    @pytest.mark.asyncio
    async def test_get_user_permissions_success(
        self, workflow_service, mock_plone_client
    ):
        """Test successful user permission retrieval."""
        content_uid = "test-content-uid"
        user_id = "user123"

        # Mock workflow state
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "current_state": "draft",
                "template_metadata": {
                    "template_id": "simple_review",
                    "role_assignments": {"author": ["user123"]},
                },
                "available_transitions": [
                    {"id": "submit_for_review", "title": "Submit for Review"}
                ],
            }

            # Mock user roles
            with patch.object(
                workflow_service, "_get_user_roles_for_content"
            ) as mock_get_roles:
                mock_get_roles.return_value = ["Author"]

                # Mock available actions
                with patch.object(
                    workflow_service, "_get_available_actions_for_user"
                ) as mock_get_actions:
                    mock_get_actions.return_value = {
                        WorkflowAction.VIEW,
                        WorkflowAction.EDIT,
                        WorkflowAction.SUBMIT,
                    }

                    # Mock available transitions
                    with patch.object(
                        workflow_service, "_get_available_transitions_for_user"
                    ) as mock_get_transitions:
                        mock_get_transitions.return_value = [
                            {"id": "submit_for_review", "title": "Submit for Review"}
                        ]

                        # Execute
                        result = await workflow_service.get_user_workflow_permissions(
                            content_uid, user_id
                        )

                        # Verify
                        assert result["content_uid"] == content_uid
                        assert result["user_id"] == user_id
                        assert result["current_state"] == "draft"
                        assert result["user_roles"] == ["Author"]
                        assert "view" in result["available_actions"]
                        assert "edit" in result["available_actions"]
                        assert "submit" in result["available_actions"]
                        assert len(result["available_transitions"]) == 1
                        assert result["template_id"] == "simple_review"

    @pytest.mark.asyncio
    async def test_get_user_permissions_no_template(
        self, workflow_service, mock_plone_client
    ):
        """Test response when content has no template metadata."""
        content_uid = "test-content-uid"
        user_id = "user123"

        # Mock workflow state without template
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "current_state": "draft",
                "template_metadata": {},
            }

            result = await workflow_service.get_user_workflow_permissions(
                content_uid, user_id
            )

            assert result["error"] == "No workflow template metadata"


class TestRemoveWorkflowTemplate:
    """Test remove_workflow_template method."""

    @pytest.mark.asyncio
    async def test_remove_template_success(self, workflow_service, mock_plone_client):
        """Test successful template removal."""
        content_uid = "test-content-uid"

        # Mock workflow state with template
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {
                "template_metadata": {
                    "template_id": "simple_review",
                    "workflow_id": "template_simple_review_12345678",
                    "backup_info": {
                        "original_workflow_id": "simple_publication_workflow",
                        "original_state": "private",
                    },
                }
            }

            # Mock removal operations
            workflow_service._remove_template_metadata = AsyncMock()
            workflow_service._restore_workflow_from_backup = AsyncMock()
            workflow_service._cleanup_template_workflow = AsyncMock()

            # Execute
            result = await workflow_service.remove_workflow_template(content_uid)

            # Verify
            assert result["success"] is True
            assert result["content_uid"] == content_uid
            assert result["removed_template_id"] == "simple_review"
            assert result["restored_backup"] is True

            # Verify operations were called
            workflow_service._remove_template_metadata.assert_called_once_with(
                content_uid
            )
            workflow_service._restore_workflow_from_backup.assert_called_once()
            workflow_service._cleanup_template_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_template_no_template_applied(
        self, workflow_service, mock_plone_client
    ):
        """Test error when no template is applied."""
        content_uid = "test-content-uid"

        # Mock workflow state without template
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {"template_metadata": {}}

            with pytest.raises(
                PloneWorkflowError,
                match="Content does not have workflow template applied",
            ):
                await workflow_service.remove_workflow_template(content_uid)


class TestHelperMethods:
    """Test private helper methods."""

    def test_convert_template_to_plone_workflow(
        self, workflow_service, simple_template
    ):
        """Test template to Plone workflow conversion."""
        plone_workflow = workflow_service._convert_template_to_plone_workflow(
            simple_template
        )

        # Verify basic structure
        assert plone_workflow["id"] == f"template_{simple_template.id}"
        assert plone_workflow["title"] == simple_template.name
        assert plone_workflow["description"] == simple_template.description
        assert "states" in plone_workflow
        assert "transitions" in plone_workflow
        assert plone_workflow["initial_state"] == "draft"

        # Verify states conversion
        assert "draft" in plone_workflow["states"]
        assert "review" in plone_workflow["states"]
        assert "published" in plone_workflow["states"]

        # Verify transitions conversion
        assert "submit_for_review" in plone_workflow["transitions"]
        assert "approve_content" in plone_workflow["transitions"]
        assert "reject_to_draft" in plone_workflow["transitions"]

        # Verify metadata
        assert plone_workflow["metadata"]["template_id"] == simple_template.id
        assert plone_workflow["metadata"]["created_from_template"] is True

    def test_map_role_to_plone_role(self, workflow_service):
        """Test role mapping to Plone roles."""
        assert (
            workflow_service._map_role_to_plone_role(EducationRole.AUTHOR) == "Author"
        )
        assert (
            workflow_service._map_role_to_plone_role(EducationRole.EDITOR) == "Editor"
        )
        assert (
            workflow_service._map_role_to_plone_role(EducationRole.ADMINISTRATOR)
            == "Manager"
        )
        assert (
            workflow_service._map_role_to_plone_role(EducationRole.VIEWER) == "Reader"
        )

    def test_map_action_to_plone_permission(self, workflow_service):
        """Test action mapping to Plone permissions."""
        assert (
            workflow_service._map_action_to_plone_permission(WorkflowAction.VIEW)
            == "View"
        )
        assert (
            workflow_service._map_action_to_plone_permission(WorkflowAction.EDIT)
            == "Modify portal content"
        )
        assert (
            workflow_service._map_action_to_plone_permission(WorkflowAction.DELETE)
            == "Delete objects"
        )
        assert (
            workflow_service._map_action_to_plone_permission(WorkflowAction.REVIEW)
            == "Review portal content"
        )

    def test_convert_permissions_to_plone(self, workflow_service):
        """Test permission conversion to Plone format."""
        permissions = [
            WorkflowPermission(
                role=EducationRole.AUTHOR,
                actions={WorkflowAction.VIEW, WorkflowAction.EDIT},
            ),
            WorkflowPermission(
                role=EducationRole.EDITOR,
                actions={WorkflowAction.VIEW, WorkflowAction.REVIEW},
            ),
        ]

        plone_permissions = workflow_service._convert_permissions_to_plone(permissions)

        # Verify structure
        assert "View" in plone_permissions
        assert "Modify portal content" in plone_permissions
        assert "Review portal content" in plone_permissions

        # Verify role assignments
        assert "Author" in plone_permissions["View"]
        assert "Editor" in plone_permissions["View"]
        assert "Author" in plone_permissions["Modify portal content"]
        assert "Editor" in plone_permissions["Review portal content"]


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_plone_api_connection_error(
        self, workflow_service, mock_plone_client
    ):
        """Test handling of Plone API connection errors."""
        content_uid = "test-content-uid"
        mock_plone_client.get_content_by_uid.side_effect = ConnectionError(
            "Cannot connect to Plone"
        )

        with pytest.raises(PloneWorkflowError, match="Failed to get workflow state"):
            await workflow_service.get_content_workflow_state(content_uid)

    @pytest.mark.asyncio
    async def test_invalid_template_validation(
        self, workflow_service, mock_plone_client, role_assignments
    ):
        """Test error handling for invalid template validation."""
        content_uid = "test-content-uid"

        # Create an invalid template (this would fail validation)
        invalid_template = MagicMock()
        invalid_template.id = "invalid"
        invalid_template.model_validate.side_effect = ValueError("Invalid template")
        invalid_template.model_dump.return_value = {}

        # Mock content exists
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
        }

        # Mock no existing template
        with patch.object(
            workflow_service, "get_content_workflow_state"
        ) as mock_get_state:
            mock_get_state.return_value = {"template_metadata": {}}

            with pytest.raises(PloneWorkflowError, match="Template application failed"):
                await workflow_service.apply_workflow_template(
                    content_uid, invalid_template, role_assignments
                )


# Performance and Integration Tests
class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_apply_template_performance(
        self,
        workflow_service,
        mock_plone_client,
        simple_template,
        role_assignments,
        benchmark,
    ):
        """Test template application performance."""
        content_uid = "test-content-uid"

        # Setup mocks for successful application
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
            "@type": "Document",
        }

        mock_plone_client.get_workflow_info.return_value = {
            "state": "private",
            "workflow_id": "simple_publication_workflow",
            "transitions": [],
            "history": [],
        }

        # Mock all async operations
        mock_plone_client.create_workflow = AsyncMock()
        mock_plone_client.assign_workflow_to_content = AsyncMock()
        mock_plone_client.assign_local_roles = AsyncMock()
        mock_plone_client.update_content_metadata = AsyncMock()
        mock_plone_client.set_workflow_state = AsyncMock()

        # Benchmark the operation
        async def apply_template():
            return await workflow_service.apply_workflow_template(
                content_uid, simple_template, role_assignments
            )

        result = await benchmark.pedantic(apply_template, rounds=5)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_workflow_state_query_performance(
        self, workflow_service, mock_plone_client, benchmark
    ):
        """Test workflow state query performance."""
        content_uid = "test-content-uid"

        # Setup mock
        mock_plone_client.get_content_by_uid.return_value = {
            "uid": content_uid,
            "title": "Test Content",
        }

        mock_plone_client.get_workflow_info.return_value = {
            "state": "draft",
            "workflow_id": "template_simple_review",
            "transitions": [],
            "history": [],
        }

        # Benchmark the operation
        async def get_state():
            return await workflow_service.get_content_workflow_state(content_uid)

        result = await benchmark.pedantic(get_state, rounds=10)

        assert result["content_uid"] == content_uid
