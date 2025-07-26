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

- [x] **3.3 Auth0 OAuth2 Flow Implementation**
  - Implement Auth0 authorization code flow with minimal FastAPI endpoints.
  - [x] 3.3.1 Create `/auth/login` endpoint that redirects to Auth0 Universal Login
  - [x] 3.3.2 Create `/auth/callback` endpoint to handle Auth0 callback with authorization code
  - [x] 3.3.3 Implement token exchange logic (authorization code → access token)
  - [x] 3.3.4 Create `/auth/logout` endpoint for Auth0 logout with return URL
  - [x] 3.3.5 Add JWT token validation function using Auth0's public keys (JWKS)
  - [x] 3.3.6 Create `/auth/user` endpoint to return current authenticated user info
  - [x] 3.3.7 **TEST**: Use Swagger UI to access `/auth/login` and verify redirect to Auth0 Universal Login
  - [x] 3.3.8 **TEST**: Complete login flow manually and verify `/auth/callback` processes authorization code
  - [x] 3.3.9 **TEST**: Verify JWT token generation by calling `/auth/user` endpoint via Swagger UI
  - [x] 3.3.10 **TEST**: Test `/auth/logout` endpoint redirects properly and clears session

- [ ] **3.4 Existing PloneClient Integration**
  - Integrate Auth0 user data with existing Plone user system using current PloneClient.
  - [ ] 3.4.1 Extend existing PloneClient with user lookup methods (no breaking changes)
  - [ ] 3.4.2 Create user mapping function (Auth0 email → Plone user lookup)
  - [ ] 3.4.3 Implement role mapping logic (Auth0 user metadata → Plone roles/groups)
  - [ ] 3.4.4 Add fallback user creation in Plone for new Auth0 users
  - [ ] 3.4.5 Create combined user context (Auth0 claims + Plone roles)
  - [ ] 3.4.6 Test integration with existing Plone test instance
  - [ ] 3.4.7 **TEST**: Login with Auth0 test user and verify Plone user lookup works via Swagger UI
  - [ ] 3.4.8 **TEST**: Check user role mapping by calling `/auth/user` and confirming Plone roles appear
  - [ ] 3.4.9 **TEST**: Verify new Auth0 user gets created in Plone automatically on first login
  - [ ] 3.4.10 **TEST**: Confirm combined user context (Auth0 claims + Plone roles) via `/auth/user` endpoint

- [ ] **3.5 Security & Session Management**
  - Implement secure token handling and session management using existing patterns.
  - [ ] 3.5.1 Add secure JWT token validation with proper error handling
  - [ ] 3.5.2 Implement token refresh logic for long-lived sessions
  - [ ] 3.5.3 Add rate limiting to auth endpoints using existing middleware patterns
  - [ ] 3.5.4 Create session cleanup and logout token invalidation
  - [ ] 3.5.5 Add CORS configuration for Auth0 callback handling
  - [ ] 3.5.6 Implement basic audit logging for authentication events
  - [ ] 3.5.7 **TEST**: Test invalid JWT token handling via Swagger UI (expect 401 errors)
  - [ ] 3.5.8 **TEST**: Verify token refresh works by testing with expired token via Swagger UI
  - [ ] 3.5.9 **TEST**: Test rate limiting by making multiple rapid requests to auth endpoints
  - [ ] 3.5.10 **TEST**: Verify CORS configuration allows Auth0 callback from browser
  - [ ] 3.5.11 **TEST**: Check audit logs show authentication events (login, logout, failures)

- [ ] **3.6 Testing & Documentation**
  - Implement comprehensive verification using Swagger UI and create integration testing script.
  - [ ] 3.6.1 **TEST**: Verify all auth endpoints appear in Swagger UI with clear descriptions and examples
  - [ ] 3.6.2 **TEST**: Use Swagger "Authorize" button to test protected endpoints with real JWT tokens
  - [ ] 3.6.3 **TEST**: Complete full OAuth flow via browser (login → callback → user info → logout)
  - [ ] 3.6.4 Create integration script `scripts/quick_integration_test.py` for automated end-to-end verification
  - [ ] 3.6.5 **TEST**: Run integration script and verify all OAuth → Plone workflows complete successfully
  - [ ] 3.6.6 **TEST**: Verify Swagger UI shows proper authentication examples and error responses
  - [ ] 3.6.7 Create Auth0 setup guide in `docs/authentication.md` with step-by-step testing instructions
  - [ ] 3.6.8 **TEST**: Follow setup guide from scratch to ensure it works for new developers
