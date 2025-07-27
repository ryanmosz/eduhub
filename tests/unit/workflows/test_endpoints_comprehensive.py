"""
Comprehensive API endpoint tests for workflow management.

Tests all FastAPI endpoints with various scenarios including:
- Success cases with valid data
- Error cases with invalid data
- Edge cases and boundary conditions
- Authentication and authorization
- Input validation and sanitization
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.eduhub.main import app
from src.eduhub.workflows.models import EducationRole


class TestWorkflowTemplateEndpoints:
    """Test workflow template management endpoints."""

    @pytest.fixture
    def async_client(self):
        """Create async HTTP client for API testing."""
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user."""
        return {"user_id": "test-user", "roles": ["workflow_manager", "administrator"]}

    @pytest.fixture
    def valid_role_assignments(self):
        """Valid role assignments for testing."""
        return {
            "author": ["user1", "user2"],
            "editor": ["editor1"],
            "administrator": ["admin1"],
        }

    
    def test_get_templates_success(self, async_client, mock_auth_user):
        """Test successful template listing."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            response = async_client.get("/workflows/templates")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "templates" in data
            assert "total_count" in data
            assert isinstance(data["templates"], list)
            assert len(data["templates"]) > 0

            # Verify template structure
            template = data["templates"][0]
            required_fields = [
                "id",
                "name",
                "description",
                "category",
                "states",
                "transitions",
            ]
            for field in required_fields:
                assert field in template

    
    def test_get_templates_with_filters(self, async_client, mock_auth_user):
        """Test template listing with category filters."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Test category filter
            response = async_client.get(
                "/workflows/templates?categories=educational"
            )
            assert response.status_code == 200

            data = response.json()
            assert "templates" in data

            # Verify all returned templates match filter
            for template in data["templates"]:
                assert template["category"] == "educational"

    
    def test_get_template_by_id_success(self, async_client, mock_auth_user):
        """Test successful template retrieval by ID."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            response = async_client.get("/workflows/templates/simple_review")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "template" in data
            template = data["template"]

            assert template["id"] == "simple_review"
            assert "states" in template
            assert "transitions" in template
            assert "default_permissions" in template

            # Verify states structure
            assert len(template["states"]) > 0
            state = template["states"][0]
            assert "id" in state
            assert "name" in state
            assert "permissions" in state

    
    def test_get_template_not_found(self, async_client, mock_auth_user):
        """Test template not found error."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            response = async_client.get("/workflows/templates/nonexistent")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "not found" in data["error"].lower()

    
    def test_templates_unauthorized(self, async_client):
        """Test unauthorized access to templates."""
        # No auth mock - should fail
        response = async_client.get("/workflows/templates")

        # Should return 401 or redirect to auth
        assert response.status_code in [401, 403]


class TestWorkflowApplicationEndpoints:
    """Test workflow template application endpoints."""

    @pytest.fixture
    def async_client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["workflow_manager"]}

    @pytest.fixture
    def mock_plone_service(self):
        """Mock PloneWorkflowService for testing."""
        with patch("src.eduhub.workflows.plone_service.PloneWorkflowService") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            # Default successful responses
            mock_instance.get_content_workflow_state.return_value = {
                "state": "draft",
                "workflow_id": "test_workflow",
                "transitions": [],
            }
            mock_instance.get_user_workflow_permissions.return_value = {
                "available_actions": ["manage_workflow", "edit", "view"]
            }
            mock_instance.apply_workflow_template.return_value = {
                "success": True,
                "template_applied": "simple_review",
                "workflow_created": "workflow_123",
            }

            yield mock_instance

    
    def test_apply_template_success(
        self, async_client, mock_auth_user, mock_plone_service, valid_role_assignments
    ):
        """Test successful template application."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            request_data = {"role_assignments": valid_role_assignments, "force": False}

            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content-123",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert data["success"] is True
            assert data["template_id"] == "simple_review"
            assert data["content_uid"] == "test-content-123"
            assert data["user_id"] == "test-user"
            assert "application_result" in data
            assert "audit_log" in data

    
    def test_apply_template_invalid_assignments(
        self, async_client, mock_auth_user, mock_plone_service
    ):
        """Test template application with invalid role assignments."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Empty role assignments should fail validation
            request_data = {
                "role_assignments": {
                    "author": []  # Empty list should cause validation error
                },
                "force": False,
            }

            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content",
                json=request_data,
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert "validation" in data["error"].lower()

    
    def test_apply_template_missing_content_uid(
        self, async_client, mock_auth_user, valid_role_assignments
    ):
        """Test template application without content UID."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            request_data = {"role_assignments": valid_role_assignments}

            # Missing content_uid query parameter
            response = async_client.post(
                "/workflows/apply/simple_review", json=request_data
            )

            assert response.status_code == 422  # Validation error

    
    def test_apply_template_plone_error(
        self, async_client, mock_auth_user, valid_role_assignments
    ):
        """Test template application with Plone service error."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                # Simulate Plone error
                mock_instance.get_content_workflow_state.side_effect = Exception(
                    "Plone connection failed"
                )

                request_data = {"role_assignments": valid_role_assignments}

                response = async_client.post(
                    "/workflows/apply/simple_review?content_uid=test-content",
                    json=request_data,
                )

                assert response.status_code == 500
                data = response.json()
                assert "error" in data

    
    def test_apply_template_force_override(
        self, async_client, mock_auth_user, mock_plone_service, valid_role_assignments
    ):
        """Test forced template application."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            request_data = {
                "role_assignments": valid_role_assignments,
                "force": True,  # Force override existing workflow
            }

            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify force parameter was processed
            # (Would need to check mock calls to verify)


class TestWorkflowTransitionEndpoints:
    """Test workflow transition execution endpoints."""

    @pytest.fixture
    def async_client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["editor"]}

    
    def test_execute_transition_success(self, async_client, mock_auth_user):
        """Test successful workflow transition."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.execute_workflow_transition.return_value = {
                    "success": True,
                    "from_state": "draft",
                    "to_state": "pending",
                    "transition_id": "submit",
                    "content_uid": "test-content",
                }

                request_data = {
                    "content_uid": "test-content",
                    "transition_id": "submit",
                    "comments": "Ready for review",
                }

                response = async_client.post(
                    "/workflows/transition", json=request_data
                )

                assert response.status_code == 200
                data = response.json()

                assert data["success"] is True
                assert data["from_state"] == "draft"
                assert data["to_state"] == "pending"
                assert data["transition_id"] == "submit"

    
    def test_execute_transition_invalid_transition(
        self, async_client, mock_auth_user
    ):
        """Test transition with invalid transition ID."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.execute_workflow_transition.side_effect = Exception(
                    "Invalid transition"
                )

                request_data = {
                    "content_uid": "test-content",
                    "transition_id": "invalid_transition",
                }

                response = async_client.post(
                    "/workflows/transition", json=request_data
                )

                assert response.status_code == 400
                data = response.json()
                assert "error" in data

    
    def test_execute_transition_missing_fields(
        self, async_client, mock_auth_user
    ):
        """Test transition with missing required fields."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Missing transition_id
            request_data = {"content_uid": "test-content"}

            response = async_client.post(
                "/workflows/transition", json=request_data
            )

            assert response.status_code == 422  # Validation error


class TestWorkflowStateEndpoints:
    """Test workflow state query endpoints."""

    @pytest.fixture
    def async_client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["viewer"]}

    
    def test_get_content_state_success(self, async_client, mock_auth_user):
        """Test successful content workflow state retrieval."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.get_content_workflow_state.return_value = {
                    "content_uid": "test-content",
                    "current_state": "draft",
                    "workflow_id": "simple_review_workflow",
                    "available_transitions": [
                        {
                            "id": "submit",
                            "title": "Submit for Review",
                            "target": "pending",
                        }
                    ],
                    "template_metadata": {
                        "template_id": "simple_review",
                        "applied_by": "admin",
                        "applied_at": "2025-01-01T00:00:00Z",
                    },
                }

                response = async_client.get(
                    "/workflows/content/test-content/state"
                )

                assert response.status_code == 200
                data = response.json()

                assert data["content_uid"] == "test-content"
                assert data["current_state"] == "draft"
                assert data["workflow_id"] == "simple_review_workflow"
                assert "available_transitions" in data
                assert "template_metadata" in data

    
    def test_get_content_state_not_found(self, async_client, mock_auth_user):
        """Test content state for non-existent content."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.get_content_workflow_state.side_effect = Exception(
                    "Content not found"
                )

                response = async_client.get(
                    "/workflows/content/nonexistent/state"
                )

                assert response.status_code == 404
                data = response.json()
                assert "error" in data


class TestWorkflowRemovalEndpoints:
    """Test workflow template removal endpoints."""

    @pytest.fixture
    def async_client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["workflow_manager"]}

    
    def test_remove_template_success(self, async_client, mock_auth_user):
        """Test successful template removal."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.remove_workflow_template.return_value = {
                    "success": True,
                    "content_uid": "test-content",
                    "template_removed": "simple_review",
                    "backup_restored": True,
                }

                response = async_client.delete(
                    "/workflows/content/test-content/template?restore_backup=true"
                )

                assert response.status_code == 200
                data = response.json()

                assert data["success"] is True
                assert data["content_uid"] == "test-content"
                assert data["backup_restored"] is True

    
    def test_remove_template_no_backup(self, async_client, mock_auth_user):
        """Test template removal without backup restoration."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                mock_instance.remove_workflow_template.return_value = {
                    "success": True,
                    "content_uid": "test-content",
                    "template_removed": "simple_review",
                    "backup_restored": False,
                }

                response = async_client.delete(
                    "/workflows/content/test-content/template?restore_backup=false"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["backup_restored"] is False


class TestHealthCheckEndpoint:
    """Test workflow system health check endpoint."""

    @pytest.fixture
    def async_client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["viewer"]}

    
    def test_health_check_success(self, async_client, mock_auth_user):
        """Test successful health check."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            response = async_client.get("/workflows/health")

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            assert "timestamp" in data
            assert "checks" in data

            # Verify health check structure
            checks = data["checks"]
            assert "templates_loadable" in checks
            assert "plone_connection" in checks


class TestInputValidationAndSecurity:
    """Test input validation and security aspects."""

    @pytest.fixture
    def async_client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["workflow_manager"]}

    
    def test_sql_injection_protection(self, async_client, mock_auth_user):
        """Test protection against SQL injection attacks."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Attempt SQL injection in content UID
            malicious_uid = "test'; DROP TABLE users; --"

            response = async_client.get(
                f"/workflows/content/{malicious_uid}/state"
            )

            # Should handle gracefully, not crash
            assert response.status_code in [400, 404, 500]

    
    def test_xss_protection(self, async_client, mock_auth_user):
        """Test protection against XSS attacks."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance
                mock_instance.execute_workflow_transition.return_value = {
                    "success": True
                }

                # Attempt XSS in comments
                malicious_comment = "<script>alert('xss')</script>"

                request_data = {
                    "content_uid": "test-content",
                    "transition_id": "submit",
                    "comments": malicious_comment,
                }

                response = async_client.post(
                    "/workflows/transition", json=request_data
                )

                # Should process without executing script
                # Response should be clean (exact behavior depends on sanitization)
                assert response.status_code in [200, 400]

    
    def test_oversized_request_protection(self, async_client, mock_auth_user):
        """Test protection against oversized requests."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Create extremely large role assignment
            huge_role_assignments = {
                "author": [f"user{i}" for i in range(10000)],  # Very large list
                "editor": [f"editor{i}" for i in range(5000)],
            }

            request_data = {"role_assignments": huge_role_assignments}

            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content",
                json=request_data,
            )

            # Should handle large requests appropriately
            # Might return 413 (Payload Too Large) or 400 (Bad Request)
            assert response.status_code in [200, 400, 413, 422]

    
    def test_invalid_json_handling(self, async_client, mock_auth_user):
        """Test handling of invalid JSON requests."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Send invalid JSON
            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content",
                content="{ invalid json }",
            )

            assert response.status_code == 422  # Unprocessable Entity

    
    def test_content_type_validation(self, async_client, mock_auth_user):
        """Test content type validation."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Send form data instead of JSON
            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content",
                data={"role_assignments": "invalid"},
            )

            assert response.status_code == 422


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def async_client(self):
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_auth_user(self):
        return {"user_id": "test-user", "roles": ["workflow_manager"]}

    
    def test_empty_role_assignments(self, async_client, mock_auth_user):
        """Test handling of empty role assignments."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            request_data = {"role_assignments": {}}  # Empty assignments

            response = async_client.post(
                "/workflows/apply/simple_review?content_uid=test-content",
                json=request_data,
            )

            # Should reject empty assignments
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    
    def test_unicode_content_handling(self, async_client, mock_auth_user):
        """Test handling of Unicode content."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance
                mock_instance.execute_workflow_transition.return_value = {
                    "success": True
                }

                # Unicode content in comments
                unicode_comment = "Готово для проверки 😀 中文测试"

                request_data = {
                    "content_uid": "test-content-unicode",
                    "transition_id": "submit",
                    "comments": unicode_comment,
                }

                response = async_client.post(
                    "/workflows/transition", json=request_data
                )

                assert response.status_code == 200

    
    def test_very_long_content_uid(self, async_client, mock_auth_user):
        """Test handling of very long content UIDs."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            # Very long content UID
            long_uid = "a" * 1000

            response = async_client.get(f"/workflows/content/{long_uid}/state")

            # Should handle gracefully
            assert response.status_code in [400, 404, 422]

    
    def test_concurrent_template_applications(self, async_client, mock_auth_user):
        """Test concurrent applications to same content."""
        with patch(
            "src.eduhub.auth.dependencies.get_current_user", return_value=mock_auth_user
        ):
            with patch(
                "src.eduhub.workflows.plone_service.PloneWorkflowService"
            ) as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance

                # First call succeeds
                mock_instance.apply_workflow_template.return_value = {"success": True}

                request_data = {
                    "role_assignments": {"author": ["user1"], "editor": ["editor1"]}
                }

                # Simulate multiple requests (sequential with TestClient)
                responses = []
                for _ in range(3):
                    try:
                        response = async_client.post(
                            "/workflows/apply/simple_review?content_uid=concurrent-content",
                            json=request_data,
                        )
                        responses.append(response)
                    except Exception as e:
                        responses.append(e)

                # At least one should succeed, others might conflict
                success_count = sum(
                    1
                    for r in responses
                    if not isinstance(r, Exception) and r.status_code == 200
                )

                assert success_count >= 1
