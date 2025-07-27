"""
FastAPI Authentication Dependencies

Provides dependency injection functions for JWT validation and user authentication.
Uses Auth0 JWKS for token validation and integrates with Plone user system.
"""

import json
import os
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from .models import User
from .plone_bridge import sync_auth0_user_to_plone

# Security scheme for FastAPI automatic documentation
security = HTTPBearer()

# Auth0 configuration from environment variables
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-1fx6yhxxi543ipno.us.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "s05QngyZXEI3XNdirmJu0CscW1hNgaRD")
AUTH0_ALGORITHMS = ["RS256"]


@lru_cache
def get_auth0_public_key():
    """
    Fetch Auth0 public keys (JWKS) for JWT signature validation.
    Cached to avoid repeated API calls.
    """
    try:
        response = httpx.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to fetch Auth0 public keys: {str(e)}",
        )


def validate_jwt_token(token: str) -> dict:
    """
    Validate JWT token using Auth0 public keys with enhanced security.

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid with specific error details
    """
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is required",
        )

    try:
        # Get Auth0 public keys
        jwks = get_auth0_public_key()

        # Decode token header to get key ID
        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
            )

        token_kid = unverified_header.get("kid")
        if not token_kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key identifier",
            )

        # Find the correct key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == token_kid:
                # Validate required key components
                required_fields = ["kty", "kid", "use", "n", "e"]
                if not all(field in key for field in required_fields):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid key format in JWKS",
                    )

                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token key not found in JWKS",
            )

        # Validate and decode token with strict security options
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=AUTH0_ALGORITHMS,
            issuer=f"https://{AUTH0_DOMAIN}/",
            options={
                "verify_aud": False,  # Skip audience verification for MVP
                "verify_exp": True,  # Verify token expiration
                "verify_iat": True,  # Verify issued at time
                "verify_nbf": True,  # Verify not before time
                "verify_signature": True,  # Verify token signature
                "require_exp": True,  # Require expiration claim
                "require_iat": True,  # Require issued at claim
            },
        )

        # Additional payload validation
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )

        # Check if token is not too old (additional security)
        import time

        current_time = int(time.time())
        token_age = current_time - payload.get("iat", 0)
        MAX_TOKEN_AGE = 24 * 60 * 60  # 24 hours

        if token_age > MAX_TOKEN_AGE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is too old, please re-authenticate",
            )

        return payload

    except HTTPException:
        # Re-raise our custom HTTP exceptions
        raise
    except JWTError as e:
        error_msg = str(e).lower()
        if "expired" in error_msg:
            detail = "Token has expired, please re-authenticate"
        elif "signature" in error_msg:
            detail = "Token signature verification failed"
        elif "invalid" in error_msg:
            detail = "Token format is invalid"
        else:
            detail = f"Token validation failed: {str(e)}"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )
    except Exception as e:
        # Log unexpected errors but don't expose internal details
        print(f"Unexpected JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> User:
    """
    FastAPI dependency to get current authenticated user from JWT token with Plone integration.

    Args:
        request: FastAPI request object (to access cookies)
        credentials: HTTP Bearer token from request (optional)

    Returns:
        User: Combined user information from Auth0 JWT + Plone user data

    Raises:
        HTTPException: If token is missing or invalid
    """
    # Try to get token from Authorization header first, then from cookies
    token = None

    if credentials:
        token = credentials.credentials
    else:
        # Try to get token from cookies
        token = request.cookies.get("access_token") or request.cookies.get("id_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required (header or cookie)",
        )

    # Validate token and extract user info
    token_payload = validate_jwt_token(token)

    # Sync with Plone and get combined user context
    try:
        combined_user = await sync_auth0_user_to_plone(token_payload)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Plone sync failed: {e}")
        combined_user = None

    if not combined_user:
        # If Plone integration fails, fall back to Auth0-only user
        # This ensures authentication still works even if Plone is down
        combined_user = User(
            sub=token_payload.get("sub", ""),
            email=token_payload.get("email", ""),
            email_verified=token_payload.get("email_verified", False),
            name=token_payload.get("name", ""),
            picture=token_payload.get("picture"),
            nickname=token_payload.get("nickname", ""),
            aud=token_payload.get("aud", ""),
            iss=token_payload.get("iss", ""),
            exp=token_payload.get("exp", 0),
            iat=token_payload.get("iat", 0),
            roles=["Member"],  # Default role if Plone integration fails
            permissions=["view"],  # Default permission
        )

    return combined_user


def get_current_user_dict(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Legacy function that returns user as dict for backward compatibility.
    Use get_current_user() for new code that supports Plone integration.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    # Validate token and extract user info
    token_payload = validate_jwt_token(credentials.credentials)

    # Extract user information from token
    user_info = {
        "sub": token_payload.get("sub"),  # Auth0 user ID
        "email": token_payload.get("email"),
        "email_verified": token_payload.get("email_verified", False),
        "name": token_payload.get("name"),
        "picture": token_payload.get("picture"),
        "aud": token_payload.get("aud"),  # Audience (client ID)
        "iss": token_payload.get("iss"),  # Issuer (Auth0 domain)
        "exp": token_payload.get("exp"),  # Expiration
        "iat": token_payload.get("iat"),  # Issued at
        "nickname": token_payload.get("nickname"),
        "roles": [],  # Empty for backward compatibility
        "permissions": [],  # Empty for backward compatibility
        "plone_user_id": None,  # Not available in legacy mode
    }

    return user_info


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to ensure current user has admin privileges.

    Args:
        current_user: Current authenticated user from get_current_user

    Returns:
        User: Admin user information

    Raises:
        HTTPException: If user is not an admin
    """
    # Check if user has admin roles or email-based admin access
    email = current_user.email.lower()
    user_roles = [role.lower() for role in current_user.roles]

    # Check for admin roles or email patterns
    is_admin = (
        "manager" in user_roles
        or "admin" in user_roles
        or "administrator" in user_roles
        or "admin" in email
        or email == "admin@example.com"
    )

    if is_admin:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
    )


async def get_alerts_write_user(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to ensure current user has alerts:write permission.

    Args:
        current_user: Current authenticated user from get_current_user

    Returns:
        User: User with alerts:write permission

    Raises:
        HTTPException: If user lacks alerts:write permission
    """
    # Check user permissions for alerts:write scope
    user_permissions = [perm.lower() for perm in current_user.permissions]
    has_alerts_write = (
        "alerts:write" in user_permissions
        or "alerts:*" in user_permissions
        or "write:alerts" in user_permissions
        or "*:write" in user_permissions
        or "admin" in user_permissions
        or "all" in user_permissions
    )

    # Check user roles for admin-level access
    user_roles = [role.lower() for role in current_user.roles]
    has_admin_role = (
        "manager" in user_roles
        or "admin" in user_roles
        or "administrator" in user_roles
    )

    if has_alerts_write or has_admin_role:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions. 'alerts:write' scope required for this operation.",
    )


# Optional: dependency for when authentication is optional
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    FastAPI dependency for optional authentication.
    Returns None if no token provided, validates if token is present.
    """
    if not credentials:
        return None

    return await get_current_user(credentials)
