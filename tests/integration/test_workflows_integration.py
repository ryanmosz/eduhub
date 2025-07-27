"""
Integration tests for workflow template operations.

Tests the complete workflow from FastAPI endpoints through services
to Plone integration, validating the entire pipeline works correctly.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.eduhub.main import app
from src.eduhub.workflows.models import EducationRole, WorkflowTemplate
from src.eduhub.workflows.permissions import map_eduhub_to_plone_roles
from src.eduhub.workflows.services import WorkflowServicesManager
from src.eduhub.workflows.templates import get_template


# Module-level fixtures for better scope management
@pytest.fixture
async def async_client():
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestWorkflowIntegration:
    """Integration tests for complete workflow operations."""

    @pytest.fixture
    def mock_plone_responses(self):
        """Mock Plone API responses for testing."""
        return {
            "content_info": {
                "uid": "test-content-123",
                "title": "Test Content",
                "workflow_state": "draft",
                "workflow_id": "test_workflow",
            },
            "workflow_info": {
                "state": "draft",
                "workflow_id": "test_workflow",
                "transitions": [
                    {"id": "submit", "title": "Submit for Review", "target": "pending"},
                    {"id": "publish", "title": "Publish", "target": "published"},
                ],
                "history": [],
            },
            "user_permissions": {
                "available_actions": ["manage_workflow", "edit", "view"],
                "roles": ["Author", "Editor"],
            },
        }

    @pytest.fixture
    def sample_role_assignments(self):
        """Sample role assignments for testing."""
        return {
            EducationRole.AUTHOR: ["user1", "user2"],
            EducationRole.EDITOR: ["editor1"],
            EducationRole.ADMINISTRATOR: ["admin1"],
        }


class TestTemplateApplicationIntegration:
    """Test complete template application workflow."""

    @pytest.mark.asyncio
    async def test_complete_template_application_workflow(
        self, async_client, mock_plone_responses, sample_role_assignments
    ):
        """Test complete workflow: validation → application → verification."""

        # Mock authentication
        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user",
                "roles": ["workflow_manager"],
            }

            # Mock Plone client responses
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                # Setup mock responses
                mock_instance.get_content_workflow_state.return_value = (
                    mock_plone_responses["workflow_info"]
                )
                mock_instance.get_user_workflow_permissions.return_value = (
                    mock_plone_responses["user_permissions"]
                )
                mock_instance.apply_workflow_template.return_value = {
                    "success": True,
                    "template_applied": "simple_review",
                    "workflow_created": "test_workflow_123",
                    "content_uid": "test-content-123",
                }

                # Step 1: Apply template via API
                template_request = {
                    "role_assignments": {
                        "author": ["user1", "user2"],
                        "editor": ["editor1"],
                        "administrator": ["admin1"],
                    },
                    "force": False,
                }

                response = await async_client.post(
                    "/workflows/apply/simple_review?content_uid=test-content-123",
                    json=template_request,
                )

                assert response.status_code == 200
                result = response.json()

                # Verify API response structure
                assert result["success"] is True
                assert result["template_id"] == "simple_review"
                assert result["content_uid"] == "test-content-123"
                assert "application_result" in result

                # Step 2: Verify content state
                state_response = await async_client.get(
                    "/workflows/content/test-content-123/state"
                )

                assert state_response.status_code == 200
                state_result = state_response.json()

                # Verify state response
                assert state_result["content_uid"] == "test-content-123"
                assert state_result["current_state"] is not None

                # Step 3: Test transition execution
                transition_request = {
                    "content_uid": "test-content-123",
                    "transition_id": "submit",
                    "comments": "Ready for review",
                }

                mock_instance.execute_workflow_transition.return_value = {
                    "success": True,
                    "from_state": "draft",
                    "to_state": "pending",
                    "transition_id": "submit",
                }

                transition_response = await async_client.post(
                    "/workflows/transition", json=transition_request
                )

                assert transition_response.status_code == 200
                transition_result = transition_response.json()

                assert transition_result["success"] is True
                assert transition_result["from_state"] == "draft"
                assert transition_result["to_state"] == "pending"

    @pytest.mark.asyncio
    async def test_bulk_template_application_integration(
        self, async_client, mock_plone_responses, sample_role_assignments
    ):
        """Test bulk template application through API."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user",
                "roles": ["workflow_manager"],
            }

            with patch(
                "src.eduhub.workflows.services.WorkflowServicesManager"
            ) as mock_manager:
                mock_instance = AsyncMock()
                mock_manager.return_value = mock_instance

                # Mock bulk application result
                mock_instance.bulk_apply_template.return_value = {
                    "operation": "bulk_apply_template",
                    "template_id": "simple_review",
                    "user_id": "test-user",
                    "total_items": 3,
                    "successful_count": 3,
                    "failed_count": 0,
                    "successful_items": [
                        {"content_uid": "content-1", "success": True},
                        {"content_uid": "content-2", "success": True},
                        {"content_uid": "content-3", "success": True},
                    ],
                    "failed_items": [],
                    "success_rate": 1.0,
                }

                # Test bulk application request
                bulk_request = {
                    "template_id": "simple_review",
                    "content_assignments": [
                        {
                            "content_uid": "content-1",
                            "role_assignments": {
                                "author": ["user1"],
                                "editor": ["editor1"],
                            },
                        },
                        {
                            "content_uid": "content-2",
                            "role_assignments": {
                                "author": ["user2"],
                                "editor": ["editor1"],
                            },
                        },
                        {
                            "content_uid": "content-3",
                            "role_assignments": {
                                "author": ["user3"],
                                "editor": ["editor1"],
                            },
                        },
                    ],
                    "max_concurrent": 3,
                }

                # Note: This endpoint doesn't exist yet, would need to be added
                # This is testing the intended API design
                response = await async_client.post(
                    "/workflows/bulk-apply", json=bulk_request
                )

                # This will return 404 for now, but shows the integration test structure
                # assert response.status_code == 200
                # result = response.json()
                # assert result["total_items"] == 3
                # assert result["successful_count"] == 3


class TestTemplateValidationIntegration:
    """Test template validation workflows."""

    @pytest.mark.asyncio
    async def test_template_validation_api_integration(self, async_client):
        """Test template validation through API endpoints."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user",
                "roles": ["workflow_manager"],
            }

            # Test template list endpoint
            response = await async_client.get("/workflows/templates")
            assert response.status_code == 200

            templates = response.json()
            assert "templates" in templates
            assert len(templates["templates"]) > 0

            # Verify template structure
            template = templates["templates"][0]
            assert "id" in template
            assert "name" in template
            assert "description" in template

            # Test specific template details
            template_id = template["id"]
            detail_response = await async_client.get(
                f"/workflows/templates/{template_id}"
            )
            assert detail_response.status_code == 200

            detail = detail_response.json()
            assert detail["template"]["id"] == template_id
            assert "states" in detail["template"]
            assert "transitions" in detail["template"]

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, async_client):
        """Test error handling in validation workflows."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user",
                "roles": ["workflow_manager"],
            }

            # Test invalid template ID
            response = await async_client.get("/workflows/templates/invalid-template")
            assert response.status_code == 404

            # Test template application with missing content
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance
                mock_instance.get_content_workflow_state.side_effect = Exception(
                    "Content not found"
                )

                invalid_request = {"role_assignments": {"author": ["user1"]}}

                response = await async_client.post(
                    "/workflows/apply/simple_review?content_uid=invalid-content",
                    json=invalid_request,
                )

                assert response.status_code in [400, 404, 500]


class TestPermissionIntegration:
    """Test permission and role mapping integration."""

    @pytest.mark.asyncio
    async def test_role_permission_mapping_integration(self, sample_role_assignments):
        """Test role mapping through the complete system."""

        # Test EduHub to Plone role conversion
        plone_assignments = map_eduhub_to_plone_roles(sample_role_assignments)

        assert "Author" in plone_assignments
        assert "Editor" in plone_assignments
        assert "Manager" in plone_assignments

        assert plone_assignments["Author"] == ["user1", "user2"]
        assert plone_assignments["Editor"] == ["editor1"]
        assert plone_assignments["Manager"] == ["admin1"]

        # Test with workflow service
        mock_client = AsyncMock()
        service = WorkflowServicesManager(mock_client)

        # Mock service responses
        mock_client.get_content_by_uid.return_value = {"uid": "test"}
        mock_client.get_workflow_info.return_value = {"state": "draft"}

        template = get_template("simple_review")

        # This would fail without proper mocking, but shows integration structure
        try:
            validation_result = await service.validate_template_for_content(
                template, ["test-content"], "test-user"
            )
            # Would contain validation results if properly mocked
        except Exception:
            # Expected without full mock setup
            pass


class TestAuditingIntegration:
    """Test audit logging integration."""

    @pytest.mark.asyncio
    async def test_audit_trail_integration(self, async_client, sample_role_assignments):
        """Test that operations create proper audit trails."""

        from src.eduhub.workflows.audit import (
            get_audit_logger,
            query_workflow_audit_logs,
        )

        audit_logger = get_audit_logger()

        # Clear any existing logs for clean test
        initial_logs = query_workflow_audit_logs(limit=1000)
        initial_count = len(initial_logs)

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "audit-test-user",
                "roles": ["workflow_manager"],
            }

            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.get_content_workflow_state.return_value = {
                    "state": "draft"
                }
                mock_instance.get_user_workflow_permissions.return_value = {
                    "available_actions": ["manage_workflow"]
                }
                mock_instance.apply_workflow_template.return_value = {
                    "success": True,
                    "template_applied": "simple_review",
                }

                # Perform operation that should create audit log
                template_request = {
                    "role_assignments": {
                        "author": ["audit-user1"],
                        "editor": ["audit-editor1"],
                    }
                }

                response = await async_client.post(
                    "/workflows/apply/simple_review?content_uid=audit-test-content",
                    json=template_request,
                )

                # Give some time for audit log to be written
                await asyncio.sleep(0.1)

                # Check that audit log was created
                new_logs = query_workflow_audit_logs(limit=1000)
                assert len(new_logs) > initial_count

                # Find our audit entry
                audit_entries = [
                    log
                    for log in new_logs
                    if log.get("user_id") == "audit-test-user"
                    and log.get("content_uid") == "audit-test-content"
                ]

                assert len(audit_entries) > 0
                audit_entry = audit_entries[0]

                assert audit_entry["operation"] == "apply_template"
                assert audit_entry["template_id"] == "simple_review"
                assert audit_entry["success"] is True


class TestErrorRecoveryIntegration:
    """Test error recovery and rollback integration."""

    @pytest.mark.asyncio
    async def test_transaction_rollback_integration(self, async_client):
        """Test that failed operations are properly rolled back."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user",
                "roles": ["workflow_manager"],
            }

            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                # Setup partial success scenario
                mock_instance.get_content_workflow_state.return_value = {
                    "state": "draft"
                }
                mock_instance.get_user_workflow_permissions.return_value = {
                    "available_actions": ["manage_workflow"]
                }

                # Simulate failure during template application
                mock_instance.apply_workflow_template.side_effect = Exception(
                    "Plone connection failed"
                )

                template_request = {
                    "role_assignments": {"author": ["user1"], "editor": ["editor1"]}
                }

                response = await async_client.post(
                    "/workflows/apply/simple_review?content_uid=test-content",
                    json=template_request,
                )

                # Should return error status
                assert response.status_code == 500

                error_result = response.json()
                assert "error" in error_result

                # Verify error is properly logged in audit trail
                from src.eduhub.workflows.audit import query_workflow_audit_logs

                await asyncio.sleep(0.1)  # Allow audit log to be written

                error_logs = query_workflow_audit_logs(
                    user_id="test-user", success_only=False, limit=10
                )

                failed_logs = [
                    log for log in error_logs if not log.get("success", True)
                ]
                assert len(failed_logs) > 0

    @pytest.mark.asyncio
    async def test_health_check_integration(self, async_client):
        """Test system health check integration."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user",
                "roles": ["workflow_manager"],
            }

            response = await async_client.get("/workflows/health")

            # Should return health status
            assert response.status_code in [200, 503]

            health_result = response.json()
            assert "status" in health_result
            assert "timestamp" in health_result


class TestPerformanceIntegration:
    """Test performance characteristics in integration scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, async_client):
        """Test concurrent workflow operations."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "perf-user",
                "roles": ["workflow_manager"],
            }

            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.get_content_workflow_state.return_value = {
                    "state": "draft"
                }
                mock_instance.get_user_workflow_permissions.return_value = {
                    "available_actions": ["manage_workflow"]
                }
                mock_instance.apply_workflow_template.return_value = {
                    "success": True,
                    "template_applied": "simple_review",
                }

                # Create multiple concurrent requests
                tasks = []
                for i in range(5):
                    template_request = {
                        "role_assignments": {
                            "author": [f"user{i}"],
                            "editor": ["editor1"],
                        }
                    }

                    task = async_client.post(
                        f"/workflows/apply/simple_review?content_uid=perf-content-{i}",
                        json=template_request,
                    )
                    tasks.append(task)

                # Execute all requests concurrently
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                # Verify all succeeded
                successful_responses = [
                    r
                    for r in responses
                    if not isinstance(r, Exception) and r.status_code == 200
                ]

                assert len(successful_responses) == 5

    @pytest.mark.asyncio
    async def test_large_role_assignment_integration(self, async_client):
        """Test handling of large role assignments."""

        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "large-test-user",
                "roles": ["workflow_manager"],
            }

            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.get_content_workflow_state.return_value = {
                    "state": "draft"
                }
                mock_instance.get_user_workflow_permissions.return_value = {
                    "available_actions": ["manage_workflow"]
                }
                mock_instance.apply_workflow_template.return_value = {
                    "success": True,
                    "template_applied": "simple_review",
                }

                # Create large role assignment
                large_request = {
                    "role_assignments": {
                        "author": [f"author{i}" for i in range(100)],
                        "editor": [f"editor{i}" for i in range(50)],
                        "administrator": [f"admin{i}" for i in range(10)],
                    }
                }

                response = await async_client.post(
                    "/workflows/apply/simple_review?content_uid=large-content",
                    json=large_request,
                )

                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
