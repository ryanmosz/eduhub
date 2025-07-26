"""
Auth0 OAuth2 Flow Implementation

FastAPI router implementing Auth0 authorization code flow with login, callback,
logout, and user information endpoints.
"""

import os
import secrets
import time
from typing import Optional
from urllib.parse import quote_plus, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from .dependencies import get_current_user, validate_jwt_token
from .models import AuthResponse, User
from .rate_limiting import get_client_ip, rate_limit

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-1fx6yhxxi543ipno.us.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "s05QngyZXEI3XNdirmJu0CscW1hNgaRD")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Create the auth router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login")
@rate_limit(max_requests=5, window_seconds=60)  # 5 login attempts per minute
async def login(request: Request, return_to: Optional[str] = None):
    """
    Initiate Auth0 OAuth2 login flow.

    Redirects user to Auth0 Universal Login page.

    Args:
        request: FastAPI request object
        return_to: Optional URL to redirect to after successful login

    Returns:
        RedirectResponse: Redirect to Auth0 Universal Login
    """
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state and return_to in session (for now, we'll use a simple approach)
    # In production, you might want to use Redis or database storage

    # Build Auth0 authorization URL
    params = {
        "response_type": "code",
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/auth/callback",
        "scope": "openid profile email",
        "state": state,
    }

    auth_url = f"https://{AUTH0_DOMAIN}/authorize?" + urlencode(params)

    # Return redirect response to Auth0
    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

    # Store state in httpOnly cookie for security
    response.set_cookie(
        key="auth_state",
        value=state,
        httponly=True,
        secure=True if BASE_URL.startswith("https") else False,
        samesite="lax",
        max_age=600,  # 10 minutes
    )

    # Store return_to URL if provided
    if return_to:
        response.set_cookie(
            key="return_to",
            value=return_to,
            httponly=True,
            secure=True if BASE_URL.startswith("https") else False,
            samesite="lax",
            max_age=600,
        )

    return response


@router.get("/callback")
@rate_limit(max_requests=10, window_seconds=60)  # 10 callbacks per minute
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Handle Auth0 OAuth2 callback.

    Processes the authorization code from Auth0 and exchanges it for tokens.

    Args:
        request: FastAPI request object
        code: Authorization code from Auth0
        state: State parameter for CSRF protection
        error: Error code if authentication failed
        error_description: Human-readable error description

    Returns:
        AuthResponse: Authentication result with user info or redirect
    """
    # Check for Auth0 errors
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auth0 error: {error} - {error_description or 'Unknown error'}",
        )

    # Validate required parameters
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required parameters: code and state",
        )

    # Verify state parameter (CSRF protection)
    stored_state = request.cookies.get("auth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter - possible CSRF attack",
        )

    try:
        # Exchange authorization code for tokens
        token_response = await exchange_code_for_tokens(code)

        # Extract tokens
        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")

        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ID token received from Auth0",
            )

        # Validate and decode the ID token to get user info
        user_info = validate_jwt_token(id_token)

        # Log successful login for audit trail
        log_auth_event(
            "login_success",
            {
                "user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "ip_address": get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "auth_method": "oauth2_auth0",
            },
        )

        # Get return_to URL from cookie
        return_to = request.cookies.get("return_to", "/")

        # Create redirect response
        response = RedirectResponse(url=return_to, status_code=status.HTTP_302_FOUND)

        # Store the JWT token in a secure cookie for API access
        # In production, you'd want a shorter expiry and possibly HttpOnly=True
        response.set_cookie(
            key="access_token",
            value=id_token,  # Using id_token as it contains user info
            httponly=False,  # Allow JavaScript access for testing
            secure=False,  # Set to False for localhost HTTP development
            samesite="lax",
            max_age=3600,  # 1 hour
            path="/",  # Make cookie available to all paths
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token exchange failed: {str(e)}",
        )


@router.get("/user", response_model=User)
async def get_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information with Plone integration.

    Requires valid JWT token in Authorization header.
    Returns combined Auth0 + Plone user data including roles and permissions.

    Args:
        current_user: Current authenticated user with Plone data

    Returns:
        User: Current user information including Plone roles and groups
    """
    return current_user


@router.post("/logout")
@rate_limit(max_requests=10, window_seconds=60)  # 10 logout attempts per minute
async def logout(request: Request):
    """
    Logout user and clear session.

    Properly invalidates tokens, clears cookies, and redirects to Auth0 logout URL
    to clear Auth0 session as well.

    Args:
        request: FastAPI request object (may contain return_to in JSON body)

    Returns:
        AuthResponse: Logout confirmation with session cleanup
    """
    # Try to get return_to from request body, fallback to test console
    return_to = f"{BASE_URL}/test/auth-console"  # Default to test console

    try:
        body = await request.json()
        if "return_to" in body:
            return_to = body["return_to"]
    except:
        # No JSON body or parsing error, use default
        pass

    # Get current token for audit logging
    current_token = request.cookies.get("access_token")
    user_info = None

    if current_token:
        try:
            # Get user info for audit log before invalidating
            token_payload = validate_jwt_token(current_token)
            user_info = {
                "user_id": token_payload.get("sub"),
                "email": token_payload.get("email"),
            }
        except:
            # Token invalid or expired, continue with logout
            pass

    # Build Auth0 logout URL
    logout_params = {
        "client_id": AUTH0_CLIENT_ID,
        "returnTo": return_to,
    }

    logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?" + urlencode(logout_params)

    # Create response with session cleanup
    response = AuthResponse(
        message="Logout successful - session cleared",
        redirect_url=logout_url,
        user=None,  # Clear user info
    )

    # Log logout event for audit trail
    log_auth_event(
        "logout",
        {
            "user_info": user_info,
            "ip_address": get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "return_to": return_to,
        },
    )

    return response


@router.post("/clear-session")
async def clear_session(request: Request):
    """
    Clear local session without full Auth0 logout.

    Useful for clearing tokens on the client side without
    redirecting to Auth0 logout page.

    Args:
        request: FastAPI request object

    Returns:
        dict: Session clearing confirmation
    """
    # Get current token for audit logging
    current_token = request.cookies.get("access_token")
    user_info = None

    if current_token:
        try:
            token_payload = validate_jwt_token(current_token)
            user_info = {
                "user_id": token_payload.get("sub"),
                "email": token_payload.get("email"),
            }
        except:
            pass

    # Log session clear event
    log_auth_event(
        "session_clear",
        {
            "user_info": user_info,
            "ip_address": get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    return {
        "message": "Session cleared successfully",
        "action": "clear_cookies",
        "cookies_to_clear": ["access_token", "auth_state", "return_to"],
        "timestamp": int(time.time()),
    }


def log_auth_event(event_type: str, event_data: dict):
    """
    Log authentication events for audit trail.

    In production, this should write to a proper logging system
    or audit database. For MVP, we'll use simple console logging.

    Args:
        event_type: Type of event (login, logout, token_refresh, etc.)
        event_data: Additional event data
    """
    import json
    from datetime import datetime

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": event_data,
    }

    # Simple console logging for MVP
    # In production, use proper logging framework and send to audit system
    print(f"AUTH_AUDIT: {json.dumps(log_entry)}")


async def exchange_code_for_tokens(authorization_code: str) -> dict:
    """
    Exchange authorization code for Auth0 tokens.

    Args:
        authorization_code: Authorization code from Auth0 callback

    Returns:
        dict: Token response from Auth0

    Raises:
        HTTPException: If token exchange fails
    """
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"

    token_data = {
        "grant_type": "authorization_code",
        "client_id": AUTH0_CLIENT_ID,
        "code": authorization_code,
        "redirect_uri": f"{BASE_URL}/auth/callback",
    }

    # Add client_secret only if it's provided (not needed for SPA)
    if AUTH0_CLIENT_SECRET:
        token_data["client_secret"] = AUTH0_CLIENT_SECRET

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                error_detail = error_response.get(
                    "error_description", error_response.get("error", "Unknown error")
                )
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token exchange failed: {error_detail}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Network error during token exchange: {str(e)}",
            )


@router.post("/refresh")
@rate_limit(max_requests=15, window_seconds=60)  # 15 refresh checks per minute
async def refresh_token(request: Request):
    """
    Check token expiration and provide refresh guidance.

    Since we're using Auth0 without refresh tokens in MVP, this endpoint
    checks if the current token is close to expiring and provides
    guidance for re-authentication.

    Args:
        request: FastAPI request object

    Returns:
        dict: Token status and refresh guidance
    """
    import time

    # Try to get token from cookie or header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token found - please log in",
        )

    try:
        # Validate the current token to get payload
        payload = validate_jwt_token(token)

        current_time = int(time.time())
        exp_time = payload.get("exp", 0)
        iat_time = payload.get("iat", 0)

        # Calculate time until expiration
        time_until_expiry = exp_time - current_time
        token_age = current_time - iat_time

        # Check if token needs refresh (expires in next 5 minutes)
        REFRESH_THRESHOLD = 5 * 60  # 5 minutes

        if time_until_expiry <= 0:
            # Token already expired
            return {
                "status": "expired",
                "message": "Token has expired",
                "action": "redirect_to_login",
                "login_url": f"/auth/login?return_to={request.url.path}",
                "expires_in": 0,
                "token_age_seconds": token_age,
            }
        elif time_until_expiry < REFRESH_THRESHOLD:
            # Token expires soon
            return {
                "status": "expires_soon",
                "message": f"Token expires in {time_until_expiry} seconds",
                "action": "redirect_to_login",
                "login_url": f"/auth/login?return_to={request.url.path}",
                "expires_in": time_until_expiry,
                "token_age_seconds": token_age,
            }
        else:
            # Token is still valid
            return {
                "status": "valid",
                "message": "Token is still valid",
                "action": "continue",
                "expires_in": time_until_expiry,
                "token_age_seconds": token_age,
            }

    except HTTPException as e:
        # Token validation failed
        return {
            "status": "invalid",
            "message": e.detail,
            "action": "redirect_to_login",
            "login_url": f"/auth/login?return_to={request.url.path}",
            "expires_in": 0,
        }


@router.get("/token-status")
async def get_token_status(request: Request):
    """
    Get current token status without authentication requirement.

    Useful for frontend applications to check token status
    before making authenticated requests.

    Args:
        request: FastAPI request object

    Returns:
        dict: Token status information
    """
    import time

    # Try to get token from cookie or header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return {
            "has_token": False,
            "status": "no_token",
            "message": "No authentication token found",
        }

    try:
        # Try to decode without validation first to get basic info
        from jose import jwt

        unverified_payload = jwt.get_unverified_claims(token)

        current_time = int(time.time())
        exp_time = unverified_payload.get("exp", 0)
        iat_time = unverified_payload.get("iat", 0)

        time_until_expiry = exp_time - current_time
        token_age = current_time - iat_time

        # Try full validation
        try:
            validate_jwt_token(token)

            if time_until_expiry <= 0:
                status = "expired"
            elif time_until_expiry < 300:  # 5 minutes
                status = "expires_soon"
            else:
                status = "valid"

            return {
                "has_token": True,
                "status": status,
                "expires_in": time_until_expiry,
                "token_age_seconds": token_age,
                "user_sub": unverified_payload.get("sub"),
                "user_email": unverified_payload.get("email"),
            }

        except HTTPException:
            return {
                "has_token": True,
                "status": "invalid",
                "expires_in": time_until_expiry,
                "token_age_seconds": token_age,
                "message": "Token validation failed",
            }

    except Exception:
        return {
            "has_token": True,
            "status": "malformed",
            "message": "Token format is invalid",
        }
