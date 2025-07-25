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

### Notes

This list contains **parent tasks only**. After reviewing, reply "Go" and we will expand each into detailed sub-tasks.

OAuth Provider Decision: **Auth0** - Chosen for fast MVP implementation and educational institution compatibility.

Legacy Integration Depth: **Full user/role mapping** - Required for Plone security model and granular access control.

## Tasks — Phase 3 Detailed Subtasks

- [ ] **3.1 Auth0 Quick Setup & Configuration**
  - Set up Auth0 tenant and configure minimal application settings for FastAPI integration.
  - [ ] 3.1.1 Create Auth0 free tenant account and obtain domain URL
  - [ ] 3.1.2 Create Single Page Application in Auth0 dashboard for dev environment
  - [ ] 3.1.3 Configure callback URLs for local development (<http://localhost:8000>)
  - [ ] 3.1.4 Create test users in Auth0 for development (<dev@example.com>, <admin@example.com>)
  - [ ] 3.1.5 Note down Auth0 domain, client ID, and client secret for environment configuration
  - [ ] 3.1.6 Enable email/password database connection and disable social logins for MVP

- [ ] **3.2 FastAPI Authentication Infrastructure**
  - Add minimal auth module to existing FastAPI app without disrupting current architecture.
  - [ ] 3.2.1 Create `src/eduhub/auth/__init__.py` and auth module structure
  - [ ] 3.2.2 Add auth dependencies to requirements.txt (python-jose, python-multipart)
  - [ ] 3.2.3 Create JWT validation dependency using FastAPI Depends pattern
  - [ ] 3.2.4 Add Auth0 environment variables to .env.example and docker-compose.yml
  - [ ] 3.2.5 Create basic User model in `src/eduhub/auth/models.py`
  - [ ] 3.2.6 Add HTTPBearer security scheme for FastAPI automatic docs

- [ ] **3.3 Auth0 OAuth2 Flow Implementation**
  - Implement Auth0 authorization code flow with minimal FastAPI endpoints.
  - [ ] 3.3.1 Create `/auth/login` endpoint that redirects to Auth0 Universal Login
  - [ ] 3.3.2 Create `/auth/callback` endpoint to handle Auth0 callback with authorization code
  - [ ] 3.3.3 Implement token exchange logic (authorization code → access token)
  - [ ] 3.3.4 Create `/auth/logout` endpoint for Auth0 logout with return URL
  - [ ] 3.3.5 Add JWT token validation function using Auth0's public keys (JWKS)
  - [ ] 3.3.6 Create `/auth/user` endpoint to return current authenticated user info

- [ ] **3.4 Existing PloneClient Integration**
  - Integrate Auth0 user data with existing Plone user system using current PloneClient.
  - [ ] 3.4.1 Extend existing PloneClient with user lookup methods (no breaking changes)
  - [ ] 3.4.2 Create user mapping function (Auth0 email → Plone user lookup)
  - [ ] 3.4.3 Implement role mapping logic (Auth0 user metadata → Plone roles/groups)
  - [ ] 3.4.4 Add fallback user creation in Plone for new Auth0 users
  - [ ] 3.4.5 Create combined user context (Auth0 claims + Plone roles)
  - [ ] 3.4.6 Test integration with existing Plone test instance

- [ ] **3.5 Security & Session Management**
  - Implement secure token handling and session management using existing patterns.
  - [ ] 3.5.1 Add secure JWT token validation with proper error handling
  - [ ] 3.5.2 Implement token refresh logic for long-lived sessions
  - [ ] 3.5.3 Add rate limiting to auth endpoints using existing middleware patterns
  - [ ] 3.5.4 Create session cleanup and logout token invalidation
  - [ ] 3.5.5 Add CORS configuration for Auth0 callback handling
  - [ ] 3.5.6 Implement basic audit logging for authentication events

- [ ] **3.6 Testing & Documentation**
  - Add comprehensive tests using existing pytest framework and update documentation.
  - [ ] 3.6.1 Create unit tests for JWT validation functions in `tests/test_auth/`
  - [ ] 3.6.2 Add integration tests for Auth0 OAuth flow with mocked responses
  - [ ] 3.6.3 Test Plone user mapping with existing test infrastructure
  - [ ] 3.6.4 Add authentication middleware tests using existing FastAPI test client
  - [ ] 3.6.5 Update existing API documentation with authentication requirements
  - [ ] 3.6.6 Create Auth0 setup guide in `docs/authentication.md` for deployment
