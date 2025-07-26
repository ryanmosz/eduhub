# EduHub OAuth2 Authentication Setup Guide

## Overview

This guide provides complete setup instructions for the EduHub OAuth2/SSO Gateway using Auth0. Follow these steps to configure authentication for development and testing.

## Prerequisites

- Auth0 free account
- FastAPI server running locally
- Python virtual environment activated
- Test email accounts for development

## 🔧 Auth0 Configuration

### Step 1: Create Auth0 Tenant

1. **Sign up for Auth0**: Go to [auth0.com](https://auth0.com) and create a free account
2. **Choose tenant domain**: Select a unique domain (e.g., `your-project-dev.us.auth0.com`)
3. **Note your domain**: Save this for environment variables

### Step 2: Create Application

1. **Navigate to Applications** in Auth0 Dashboard
2. **Click "Create Application"**
3. **Application Details:**
   - Name: `EduHub MVP`
   - Type: `Single Page Applications`
4. **Save Application**
5. **Note Client ID**: Save this for environment variables

### Step 3: Configure Application Settings

Navigate to your application's **Settings** tab:

#### Allowed Callback URLs
```
http://localhost:8000/auth/callback
```

#### Allowed Logout URLs
```
http://localhost:8000/test/auth-console
http://localhost:8000/
```

#### Allowed Web Origins
```
http://localhost:8000
```

#### Allowed Origins (CORS)
```
http://localhost:8000
```

**Important**: Each URL must be on a separate line in Auth0's configuration fields.

### Step 4: Configure Authentication Database

1. **Go to Authentication > Database** in sidebar
2. **Ensure "Username-Password-Authentication" is enabled**
3. **Disable any social connections** (Google, GitHub, etc.) for MVP
4. **Enable "Disable Sign Ups"** if desired (optional)

### Step 5: Create Test Users

1. **Go to User Management > Users**
2. **Click "Create User"**
3. **Create two test users:**

**User 1 (Standard User):**
- Email: `dev@example.com`
- Password: `DevPassword123!`
- Connection: `Username-Password-Authentication`

**User 2 (Admin User):**
- Email: `admin@example.com`
- Password: `AdminPassword123!`
- Connection: `Username-Password-Authentication`

## 🏗️ FastAPI Server Configuration

### Environment Variables

Create these environment variables (or add to your `.env` file):

```bash
# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_CLIENT_ID=your_client_id_here
AUTH0_CLIENT_SECRET=your_client_secret_here  # Optional for SPA flow

# FastAPI Configuration
ENVIRONMENT=development
```

### Install Dependencies

Ensure all auth dependencies are installed:

```bash
pip install python-jose cryptography python-multipart httpx email-validator
```

### Start Server

```bash
source .venv/bin/activate.fish  # or .venv/bin/activate for bash
uvicorn src.eduhub.main:app --reload --host 127.0.0.1 --port 8000
```

## 🧪 Testing Your Setup

### Quick Verification Checklist

1. **✅ Server Running**: Visit http://localhost:8000 - should see API welcome message
2. **✅ Documentation**: Visit http://localhost:8000/docs - should see Swagger UI with auth endpoints
3. **✅ Test Console**: Visit http://localhost:8000/test/auth-console - should see OAuth test interface

### Step-by-Step Testing Instructions

#### Test 1: Basic Authentication Flow

1. **Open Test Console**: Navigate to http://localhost:8000/test/auth-console
2. **Click "🚀 Start Login Flow"**
3. **You should be redirected to Auth0 Universal Login**
4. **Login with test credentials**: `dev@example.com` / `DevPassword123!`
5. **After login**: You should be redirected back to the test console
6. **Verify Success**: The console should show your user information
7. **Test User Info**: Click "👤 Get User Info" - should show user details
8. **Test Logout**: Click "🚪 Test Logout" - should log you out and return to console

#### Test 2: API Endpoints via Swagger UI

1. **Open Swagger UI**: Navigate to http://localhost:8000/docs
2. **Test Protected Endpoint**:
   - Try `/auth/user` without authentication - should get 403 Forbidden
3. **Get Token** (after completing Test 1):
   - Open browser developer tools
   - Check Application > Cookies > `access_token`
   - Copy the JWT token value
4. **Authorize in Swagger**:
   - Click "Authorize" button in Swagger UI
   - Enter: `Bearer YOUR_JWT_TOKEN_HERE`
   - Click "Authorize"
5. **Test Protected Endpoint Again**:
   - Try `/auth/user` - should now return user information
   - Try `/auth/token-status` - should show token is valid

#### Test 3: Error Handling

1. **Invalid Token Test**:
   - In Swagger UI, set Authorization to `Bearer invalid.token.here`
   - Try `/auth/user` - should get 401 Unauthorized
2. **Rate Limiting Test**:
   - Make multiple rapid requests to `/auth/login`
   - Should eventually get rate limited (429 status)
3. **CORS Test**:
   - Open browser developer tools
   - Try making cross-origin requests - should work with proper headers

### Integration Test Script

Run the automated integration test suite:

```bash
python scripts/quick_integration_test.py
```

**Expected Result**: All tests should pass (9/9 or 8/9 if rate limited)

## 🔍 Troubleshooting

### Common Issues

#### "Service not found" Error from Auth0
- **Cause**: Incorrect audience parameter or CORS issue
- **Solution**: Remove audience from URL, ensure CORS is configured

#### "allowed_logout_urls must be a valid uri"
- **Cause**: Comma-separated URLs in Auth0 config
- **Solution**: Put each URL on a separate line

#### 403 "Not authenticated" on protected endpoints
- **Cause**: Missing or invalid JWT token
- **Solution**: Complete login flow and check cookies/authorization header

#### Rate limiting (429 errors)
- **Cause**: Too many rapid requests to auth endpoints
- **Solution**: Wait 60 seconds for rate limit to reset

#### Server won't start - "Address already in use"
- **Cause**: Another process using port 8000
- **Solution**: Kill existing process or use different port

### Debug Mode

Enable verbose logging by setting:

```bash
export LOG_LEVEL=DEBUG
```

View server logs for detailed authentication events and errors.

## 🎯 Verification Success Criteria

Your Auth0 setup is complete when:

- ✅ Login flow redirects to Auth0 and back successfully
- ✅ User information is displayed after login
- ✅ JWT tokens are properly validated and stored
- ✅ Logout clears session and redirects properly
- ✅ Protected endpoints work with valid tokens
- ✅ Invalid tokens are rejected with proper error messages
- ✅ Rate limiting protects auth endpoints
- ✅ CORS allows Auth0 callback handling
- ✅ Integration test script passes all tests

## 📚 Additional Resources

- [Auth0 Documentation](https://auth0.com/docs)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io) - JWT token decoder for debugging
- [EduHub API Documentation](http://localhost:8000/docs) - When server is running

## 🔐 Security Notes

- **Development Only**: This setup is for development/testing
- **Production**: Use proper secrets management, HTTPS, and security headers
- **Token Storage**: Consider secure storage for production (HttpOnly cookies, etc.)
- **Rate Limiting**: Adjust limits based on production requirements
- **User Management**: Implement proper user roles and permissions for production

---

**Need Help?** Check the server logs, use the integration test script, or review the FastAPI error messages for specific guidance.
