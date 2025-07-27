"""
API Contract Tests for Workflow Management - FIXED VERSION

Tests that validate API endpoints exist, accept expected inputs,
and return expected JSON structures. Uses proper FastAPI dependency overrides.
"""

import time
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.eduhub.auth.dependencies import get_current_user
from src.eduhub.auth.models import User
from src.eduhub.main import app

# Create test client
client = TestClient(app)


# Mock user for testing
async def mock_get_current_user():
    """Mock current user dependency for testing."""
    current_time = int(time.time())
    return User(
        sub="auth0|test-user-123",
        email="test@example.com",
        name="Test User",
        aud="test-audience",
        iss="https://test-domain.auth0.com/",
        exp=current_time + 3600,  # Expires in 1 hour
        iat=current_time,
        roles=["workflow_manager", "editor"],
        permissions=["manage_workflow", "edit_content"],
        plone_user_id="test-user",
        plone_groups=["Site Administrators"],
    )


# Mock user with different permissions
async def mock_get_current_user_viewer():
    """Mock current user with viewer permissions."""
    current_time = int(time.time())
    return User(
        sub="auth0|viewer-user-123",
        email="viewer@example.com",
        name="Viewer User",
        aud="test-audience",
        iss="https://test-domain.auth0.com/",
        exp=current_time + 3600,
        iat=current_time,
        roles=["viewer"],
        permissions=["view_content"],
        plone_user_id="viewer-user",
        plone_groups=["Site Members"],
    )


class TestWorkflowAPIContracts:
    """Test API contracts that React frontend depends on."""

    def setup_method(self):
        """Setup dependency overrides for each test."""
        app.dependency_overrides[get_current_user] = mock_get_current_user

    def teardown_method(self):
        """Clear dependency overrides after each test."""
        app.dependency_overrides.clear()

    def test_get_templates_endpoint_exists(self):
        """React needs /workflows/templates to return template list."""
        response = client.get("/workflows/templates")
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

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
        ], f"Endpoint should exist (200 or 404), got {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            assert "template" in data, "Response missing 'template' key"

    def test_apply_template_endpoint_format(self):
        """Test that apply endpoint accepts expected payload format."""
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

        # Should not be a validation error (422)
        assert response.status_code != 422, f"Payload format rejected: {response.text}"
        # Might fail for other reasons (500, 400) but payload should be accepted
        assert response.status_code in [
            200,
            400,
            500,
        ], f"Unexpected status: {response.status_code}"

    def test_transition_endpoint_format(self):
        """Test transition endpoint accepts expected payload."""
        payload = {
            "content_uid": "test-content-123",
            "transition_id": "submit",
            "comments": "Ready for review",
        }

        response = client.post("/workflows/transition", json=payload)

        assert response.status_code != 422, f"Payload format rejected: {response.text}"
        assert response.status_code in [
            200,
            400,
            404,
            500,
        ], "Endpoint should process request"

    def test_content_state_endpoint_exists(self):
        """React needs to query content workflow state."""
        response = client.get("/workflows/content/test-content-123/state")

        # Endpoint should exist (not 405 Method Not Allowed)
        assert response.status_code != 405, "Method should be allowed"
        assert response.status_code in [200, 404, 500], "Endpoint should exist"

    def test_health_endpoint_exists(self):
        """React dashboard needs health check endpoint."""
        response = client.get("/workflows/health")

        assert response.status_code in [
            200,
            503,
        ], f"Health endpoint issue: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Health response missing 'status' key"

    def test_templates_endpoint_supports_filtering(self):
        """React needs to filter templates by category."""
        response = client.get("/workflows/templates?categories=educational")

        assert response.status_code == 200, f"Category filter failed: {response.text}"

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

    def test_authentication_behavior(self):
        """Test authentication behavior for React error handling."""
        # Test with no auth (clear override)
        app.dependency_overrides.clear()

        response = client.get("/workflows/templates")

        # Should return 401 when no auth provided
        assert response.status_code == 401, "Should require authentication"

        data = response.json()
        assert "detail" in data, "401 response should have detail message"

        # Restore auth for other tests
        app.dependency_overrides[get_current_user] = mock_get_current_user

    def test_viewer_permissions(self):
        """Test that viewer permissions work appropriately."""
        # Switch to viewer user
        app.dependency_overrides[get_current_user] = mock_get_current_user_viewer

        # Viewers should be able to list templates
        response = client.get("/workflows/templates")
        assert response.status_code == 200, "Viewers should access template list"

        # But might not be able to apply templates (depending on business logic)
        # This is more about testing the permission system exists
        payload = {"role_assignments": {"author": ["user1"]}}
        response = client.post(
            "/workflows/apply/simple_review?content_uid=test-content", json=payload
        )

        # Should either work or return permission error (not validation error)
        assert response.status_code != 422, "Should not be validation error"


class TestWorkflowAPIResponseFormats:
    """Test that API responses match expected formats for frontend consumption."""

    def setup_method(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user

    def teardown_method(self):
        app.dependency_overrides.clear()

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

    def test_openapi_schema_available(self):
        """Verify OpenAPI schema is available for frontend SDK generation."""
        response = client.get("/openapi.json")
        assert response.status_code == 200, "OpenAPI schema should be available"

        schema = response.json()
        assert "paths" in schema, "OpenAPI schema should have paths"

        # Check that workflow paths are documented
        workflow_paths = [path for path in schema["paths"] if "/workflows" in path]
        assert len(workflow_paths) > 0, "Workflow endpoints should be documented"

    def test_consistent_json_responses(self):
        """Test that all endpoints return valid JSON."""
        endpoints_to_test = [
            "/workflows/templates",
            "/workflows/health",
            "/workflows/templates/simple_review",
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint)

            # Should return valid JSON
            try:
                data = response.json()
                assert isinstance(
                    data, dict
                ), f"Endpoint {endpoint} should return JSON object"
            except Exception as e:
                pytest.fail(f"Endpoint {endpoint} returned invalid JSON: {e}")


class TestWorkflowAPISecurity:
    """Test security aspects of the API."""

    def test_endpoints_require_authentication(self):
        """Test that protected endpoints require authentication."""
        # No auth override - should get 401
        app.dependency_overrides.clear()

        protected_endpoints = [
            "/workflows/templates",
            "/workflows/health",
            "/workflows/templates/simple_review",
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert (
                response.status_code == 401
            ), f"Endpoint {endpoint} should require auth"

    def test_invalid_json_handled_gracefully(self):
        """Test that invalid JSON payloads are handled properly."""
        app.dependency_overrides[get_current_user] = mock_get_current_user

        # Send malformed JSON
        response = client.post(
            "/workflows/apply/simple_review?content_uid=test",
            data="invalid json",  # Not JSON
        )

        # Should get validation error, not server error
        assert response.status_code in [
            400,
            422,
        ], "Should handle invalid JSON gracefully"

        app.dependency_overrides.clear()
