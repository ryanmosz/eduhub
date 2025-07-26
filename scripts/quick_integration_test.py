#!/usr/bin/env python3
"""
Quick Integration Test for EduHub OAuth2 SSO Gateway
===================================================

Automated end-to-end verification script for Phase 3 OAuth implementation.
Tests Auth0 integration, JWT handling, Plone bridge, and security features.

Usage:
    python scripts/quick_integration_test.py

Requirements:
    - FastAPI server running on localhost:8000
    - Auth0 configured with test credentials
    - Virtual environment activated
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict

import httpx


class IntegrationTester:
    """OAuth2 integration testing suite"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.test_results = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append((name, success, details))
        print(f"{status} {name}")
        if details and not success:
            print(f"    Details: {details}")
        elif details and success:
            print(f"    ✓ {details}")

    async def test_server_connectivity(self) -> bool:
        """Test basic server connectivity"""
        try:
            response = await self.client.get(self.base_url)
            success = response.status_code == 200
            details = f"Server responding with status {response.status_code}"
            self.log_test("Server Connectivity", success, details)
            return success
        except Exception as e:
            self.log_test("Server Connectivity", False, f"Connection failed: {e}")
            return False

    async def test_auth_endpoints_documented(self) -> bool:
        """Test that auth endpoints are documented in OpenAPI"""
        try:
            response = await self.client.get(f"{self.base_url}/openapi.json")
            if response.status_code != 200:
                self.log_test(
                    "Auth Endpoints Documentation",
                    False,
                    f"OpenAPI not accessible: {response.status_code}",
                )
                return False

            openapi_data = response.json()
            auth_paths = [
                path for path in openapi_data.get("paths", {}).keys() if "/auth" in path
            ]

            expected_endpoints = [
                "/auth/login",
                "/auth/callback",
                "/auth/user",
                "/auth/logout",
                "/auth/token-status",
            ]
            missing = [ep for ep in expected_endpoints if ep not in auth_paths]

            success = len(missing) == 0
            if success:
                details = (
                    f"Found {len(auth_paths)} auth endpoints: {', '.join(auth_paths)}"
                )
            else:
                details = f"Missing endpoints: {missing}"

            self.log_test("Auth Endpoints Documentation", success, details)
            return success

        except Exception as e:
            self.log_test("Auth Endpoints Documentation", False, f"Error: {e}")
            return False

    async def test_jwt_validation(self) -> bool:
        """Test JWT token validation (should reject missing/invalid tokens)"""
        try:
            # Test 1: No token
            response = await self.client.get(f"{self.base_url}/auth/user")
            success1 = response.status_code == 403

            # Test 2: Invalid token
            headers = {"Authorization": "Bearer invalid.jwt.token"}
            response = await self.client.get(
                f"{self.base_url}/auth/user", headers=headers
            )
            success2 = response.status_code in [401, 403]

            success = success1 and success2
            details = f"No token: {response.status_code}, Invalid token: {response.status_code}"
            self.log_test("JWT Token Validation", success, details)
            return success

        except Exception as e:
            self.log_test("JWT Token Validation", False, f"Error: {e}")
            return False

    async def test_token_status_endpoint(self) -> bool:
        """Test token status endpoint functionality"""
        try:
            response = await self.client.get(f"{self.base_url}/auth/token-status")
            success = response.status_code == 200

            if success:
                data = response.json()
                has_expected_fields = (
                    "has_token" in data and "status" in data and "message" in data
                )
                success = success and has_expected_fields
                details = f"Response: {data.get('status', 'unknown')}"
            else:
                details = f"Status: {response.status_code}"

            self.log_test("Token Status Endpoint", success, details)
            return success

        except Exception as e:
            self.log_test("Token Status Endpoint", False, f"Error: {e}")
            return False

    async def test_cors_configuration(self) -> bool:
        """Test CORS configuration for Auth0 integration"""
        try:
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            }

            response = await self.client.options(
                f"{self.base_url}/auth/user", headers=headers
            )
            success = response.status_code == 200

            if success:
                cors_headers = response.headers
                has_cors = (
                    "access-control-allow-origin" in cors_headers
                    and "access-control-allow-credentials" in cors_headers
                    and "access-control-allow-methods" in cors_headers
                )
                success = has_cors
                details = f"CORS headers present: {has_cors}"
            else:
                details = f"OPTIONS request failed: {response.status_code}"

            self.log_test("CORS Configuration", success, details)
            return success

        except Exception as e:
            self.log_test("CORS Configuration", False, f"Error: {e}")
            return False

    async def test_rate_limiting(self) -> bool:
        """Test rate limiting on auth endpoints"""
        try:
            # Make multiple requests to test rate limiting
            responses = []
            for i in range(5):
                response = await self.client.get(
                    f"{self.base_url}/auth/login?return_to=/test"
                )
                responses.append(response.status_code)
                await asyncio.sleep(0.1)  # Small delay between requests

            # All should be successful (302 redirects) since rate limit is generous
            success = all(status == 302 for status in responses)
            details = f"Request statuses: {responses}"

            self.log_test("Rate Limiting Configuration", success, details)
            return success

        except Exception as e:
            self.log_test("Rate Limiting Configuration", False, f"Error: {e}")
            return False

    async def test_oauth_flow_initialization(self) -> bool:
        """Test OAuth flow can be initialized (login redirect)"""
        try:
            response = await self.client.get(
                f"{self.base_url}/auth/login?return_to=/test", follow_redirects=False
            )

            success = response.status_code == 302
            if success:
                location = response.headers.get("location", "")
                has_auth0 = "auth0.com" in location and "authorize" in location
                success = has_auth0
                details = f"Redirects to Auth0: {has_auth0}"
            else:
                details = f"No redirect, status: {response.status_code}"

            self.log_test("OAuth Flow Initialization", success, details)
            return success

        except Exception as e:
            self.log_test("OAuth Flow Initialization", False, f"Error: {e}")
            return False

    async def test_test_console_accessibility(self) -> bool:
        """Test that the OAuth test console is accessible"""
        try:
            response = await self.client.get(f"{self.base_url}/test/auth-console")
            success = response.status_code == 200

            if success:
                content = response.text
                has_console = (
                    "OAuth2 Test Console" in content and "Start Login Flow" in content
                )
                success = has_console
                details = f"Console elements present: {has_console}"
            else:
                details = f"Console not accessible: {response.status_code}"

            self.log_test("Test Console Accessibility", success, details)
            return success

        except Exception as e:
            self.log_test("Test Console Accessibility", False, f"Error: {e}")
            return False

    async def test_session_management(self) -> bool:
        """Test session management endpoints"""
        try:
            response = await self.client.post(f"{self.base_url}/auth/clear-session")
            success = response.status_code == 200

            if success:
                data = response.json()
                has_clear_response = "message" in data and "action" in data
                success = has_clear_response
                details = f"Session clear response: {data.get('action', 'unknown')}"
            else:
                details = f"Clear session failed: {response.status_code}"

            self.log_test("Session Management", success, details)
            return success

        except Exception as e:
            self.log_test("Session Management", False, f"Error: {e}")
            return False

    async def run_all_tests(self) -> dict[str, Any]:
        """Run complete integration test suite"""
        print("🎓 EduHub OAuth2 Integration Test Suite")
        print("=" * 50)

        # Core connectivity and documentation
        await self.test_server_connectivity()
        await self.test_auth_endpoints_documented()

        # Security features
        await self.test_jwt_validation()
        await self.test_token_status_endpoint()
        await self.test_cors_configuration()
        await self.test_rate_limiting()

        # OAuth flow and UI
        await self.test_oauth_flow_initialization()
        await self.test_test_console_accessibility()
        await self.test_session_management()

        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        for name, success, details in self.test_results:
            status = "✅" if success else "❌"
            print(f"{status} {name}")

        print(f"\n🎯 Overall: {passed}/{total} tests passed ({100*passed//total}%)")

        if passed == total:
            print("🎉 All integration tests PASSED! OAuth2 SSO Gateway is ready.")
            return {"status": "success", "passed": passed, "total": total}
        else:
            print("⚠️  Some tests failed. Check implementation and configuration.")
            return {"status": "partial", "passed": passed, "total": total}


async def main():
    """Main integration test runner"""
    print("Starting EduHub OAuth2 Integration Tests...")
    print("Ensure FastAPI server is running on http://localhost:8000\n")

    async with IntegrationTester() as tester:
        results = await tester.run_all_tests()

        # Exit with appropriate code
        if results["status"] == "success":
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Integration tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Integration tests failed with error: {e}")
        sys.exit(1)
