"""
Auth0 OAuth2 Flow Implementation

FastAPI router implementing Auth0 authorization code flow with login, callback,
logout, and user information endpoints.
"""

import os
import secrets
from typing import Optional
from urllib.parse import quote_plus, urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from .dependencies import get_current_user, validate_jwt_token
from .models import AuthResponse, User

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-1fx6yhxxi543ipno.us.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "s05QngyZXEI3XNdirmJu0CscW1hNgaRD")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Create the auth router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login")
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
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        User: Current user information
    """
    return User(**current_user)


@router.post("/logout")
async def logout(request: Request):
    """
    Logout user and clear session.

    Redirects to Auth0 logout URL to clear Auth0 session as well.

    Args:
        request: FastAPI request object (may contain return_to in JSON body)

    Returns:
        AuthResponse: Logout confirmation or redirect URL
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

    # Build Auth0 logout URL
    logout_params = {
        "client_id": AUTH0_CLIENT_ID,
        "returnTo": return_to,
    }

    logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?" + urlencode(logout_params)

    return AuthResponse(
        message="Logout successful",
        redirect_url=logout_url,
    )


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
