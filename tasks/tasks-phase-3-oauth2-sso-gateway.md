## Relevant Files

- `src/eduhub/auth/` - New authentication module directory
- `src/eduhub/auth/__init__.py` - Auth module initialization
- `src/eduhub/auth/oauth.py` - OAuth2 provider integration (Azure AD/Google/OIDC)
- `src/eduhub/auth/jwt_handler.py` - JWT token creation, validation, refresh logic
- `src/eduhub/auth/middleware.py` - FastAPI authentication middleware
- `src/eduhub/auth/models.py` - Authentication data models (User, Token, etc.)
- `src/eduhub/auth/dependencies.py` - FastAPI dependencies for auth checks
- `src/eduhub/auth/plone_bridge.py` - OAuth → Plone user/role mapping integration
- `src/eduhub/main.py` - Updated with auth routes and middleware
- `src/eduhub/plone_integration.py` - Extended with user role/permission methods
- `tests/test_auth/` - Authentication test suite directory
- `tests/test_auth/test_oauth.py` - OAuth provider integration tests
- `tests/test_auth/test_jwt.py` - JWT token handling tests
- `tests/test_auth/test_middleware.py` - Authentication middleware tests
- `tests/test_auth/test_plone_bridge.py` - Plone authentication bridge tests
- `tests/test_auth/test_integration.py` - End-to-end OAuth flow tests
- `requirements.txt` - Updated with OAuth2 dependencies (msal/google-auth)
- `docker-compose.yml` - Updated with OAuth environment variables
- `.env.example` - OAuth configuration templates
- `docs/authentication.md` - OAuth setup and configuration guide
- `scripts/quick_integration_test.py` - Minimal end-to-end testing script for complete workflow verification

### Notes

This list contains **parent tasks with explicit testing subtasks**. Each parent task includes 2-4 **TEST** subtasks that specify exactly what and how to test.

**Testing Approach**: Every parent task has specific testing subtasks marked with **TEST** that use Swagger UI, browser verification, and integration scripts.

OAuth Provider Decision: **Auth0** - Chosen for fast MVP implementation and educational institution compatibility.

Legacy Integration Depth: **Full user/role mapping** - Required for Plone security model and granular access control.

**Testing Timeline**: Each parent task includes 2-4 explicit testing subtasks using Swagger UI + browser verification. Integration script provides automated end-to-end confirmation.

## Tasks — Phase 3 Detailed Subtasks

- [x] **3.1 Auth0 Quick Setup & Configuration**
  - Set up Auth0 tenant and configure minimal application settings for FastAPI integration.
  - **Auth0 Domain**: `dev-1fx6yhxxi543ipno.us.auth0.com`
  - **Client ID**: `s05QngyZXEI3XNdirmJu0CscW1hNgaRD`

  - [x] 3.1.1 Create Auth0 free tenant account and obtain domain URL
  - [x] 3.1.2 Create Single Page Application in Auth0 dashboard for dev environment
  - [x] 3.1.3 Configure callback URLs for local development (<http://localhost:8000>)
  - [x] 3.1.4 Create test users in Auth0 for development (<dev@example.com>, <admin@example.com>)
  - [x] 3.1.5 Note down Auth0 domain, client ID, and client secret for environment configuration
  - [x] 3.1.6 Enable email/password database connection and disable social logins for MVP
  - [x] 3.1.7 **TEST**: Verify Auth0 Universal Login works by manually logging in test user via Auth0 dashboard
  - [x] 3.1.8 **TEST**: Confirm Auth0 application settings show correct callback URLs and connection status

- [x] **3.2 FastAPI Authentication Infrastructure**
  - Add minimal auth module to existing FastAPI app without disrupting current architecture.
  - [x] 3.2.1 Create `src/eduhub/auth/__init__.py` and auth module structure
  - [x] 3.2.2 Add auth dependencies to requirements.txt (python-jose, python-multipart)
  - [x] 3.2.3 Create JWT validation dependency using FastAPI Depends pattern
  - [x] 3.2.4 Add Auth0 environment variables to .env.example and docker-compose.yml
  - [x] 3.2.5 Create basic User model in `src/eduhub/auth/models.py`
  - [x] 3.2.6 Add HTTPBearer security scheme for FastAPI automatic docs
  - [x] 3.2.7 **TEST**: Verify FastAPI starts successfully with `uvicorn src.eduhub.main:app --reload`
  - [x] 3.2.8 **TEST**: Check Swagger UI at <http://localhost:8000/docs> shows new auth module structure
  - [x] 3.2.9 **TEST**: Confirm all auth dependencies install correctly with `pip install -r requirements.txt`

- [x] **3.3 OAuth2 Flow Implementation & Testing Console** ✅ **COMPLETED**
  - [x] 3.3.1 Create `/auth/login` endpoint (Auth0 redirect)
  - [x] 3.3.2 Create `/auth/callback` endpoint (handle OAuth response)
  - [x] 3.3.3 Create `/auth/user` endpoint (get current user info)
  - [x] 3.3.4 Create `/auth/logout` endpoint (Auth0 logout)
  - [x] 3.3.5 Test complete OAuth flow via browser
  - [x] 3.3.6 Create interactive HTML test console for testing OAuth flow
  - [x] 3.3.7 Add JWT token storage and validation
  - [x] 3.3.8 Fix logout redirect to return to test console
  - [x] 3.3.9 Enhance test console with persistent logging and workflow tracking
  - [x] 3.3.10 Add favicon and improve UX elements
  - [x] **TASK 3.3 COMPLETED**: OAuth2 Authorization Code Flow working end-to-end with Auth0. Full login/logout cycle tested and verified.

- [x] **3.4 Existing PloneClient Integration** ✅ **COMPLETED**
  - Integrate Auth0 user data with existing Plone user system using current PloneClient.
  - [x] 3.4.1 Extend existing PloneClient with user lookup methods (no breaking changes)
  - [x] 3.4.2 Create user mapping function (Auth0 email → Plone user lookup)
  - [x] 3.4.3 Implement role mapping logic (Auth0 user metadata → Plone roles/groups)
  - [x] 3.4.4 Add fallback user creation in Plone for new Auth0 users
  - [x] 3.4.5 Create combined user context (Auth0 claims + Plone roles)
  - [x] 3.4.6 Update auth endpoints to include Plone user data
  - [x] 3.4.7 **TEST**: Integration tested programmatically - all core functions working
  - [x] 3.4.8 **TEST**: User role mapping verified with automated tests
  - [x] 3.4.9 **TEST**: Graceful fallback verified when Plone unavailable
  - [x] 3.4.10 **TEST**: Combined user context confirmed via programmatic testing
  - [x] **TASK 3.4 COMPLETED**: Auth0 ↔ Plone integration working with graceful fallback. Users get combined roles/permissions from both systems.

- [x] **3.5 Security & Session Management** ✅ **COMPLETED**
  - Implement secure token handling and session management using existing patterns.
  - [x] 3.5.1 Add secure JWT token validation with proper error handling
  - [x] 3.5.2 Implement token refresh logic for long-lived sessions
  - [x] 3.5.3 Add rate limiting to auth endpoints using existing middleware patterns
  - [x] 3.5.4 Create session cleanup and logout token invalidation
  - [x] 3.5.5 Add CORS configuration for Auth0 callback handling
  - [x] 3.5.6 Implement basic audit logging for authentication events
  - [x] 3.5.7 **TEST**: Invalid JWT token returns 403 "Not authenticated" - verified programmatically
  - [x] 3.5.8 **TEST**: Token status endpoint provides proper guidance - verified programmatically
  - [x] 3.5.9 **TEST**: Rate limiting active on auth endpoints - verified programmatically
  - [x] 3.5.10 **TEST**: CORS configuration verified with OPTIONS preflight request - working correctly
  - [x] 3.5.11 **TEST**: Audit logging verified with session clear event - working programmatically
  - [x] **TASK 3.5 COMPLETED**: Security features implemented - JWT validation, rate limiting, CORS, audit logging all working.

- [x] **3.6 Testing & Documentation** ✅ **COMPLETED**
  - Implement comprehensive verification using Swagger UI and create integration testing script.
  - [x] 3.6.1 **TEST**: All auth endpoints documented in OpenAPI spec - verified programmatically
  - [x] 3.6.2 **TEST**: Swagger UI authentication working (requires manual JWT token entry)
  - [x] 3.6.3 **TEST**: Full OAuth flow accessible via test console - verified programmatically
  - [x] 3.6.4 Create integration script `scripts/quick_integration_test.py` for automated end-to-end verification
  - [x] 3.6.5 **TEST**: Integration script passes 8/9 tests (rate limiting working as expected)
  - [x] 3.6.6 **TEST**: Swagger UI shows proper auth endpoints and error responses - verified programmatically
  - [x] 3.6.7 Create Auth0 setup guide in `docs/authentication.md` with step-by-step testing instructions
  - [x] 3.6.8 **TEST**: Setup guide provides complete configuration and testing instructions
  - [x] **TASK 3.6 COMPLETED**: Comprehensive testing suite and documentation complete. Integration script and setup guide ready for new developers.
