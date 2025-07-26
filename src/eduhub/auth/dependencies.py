"""
FastAPI Authentication Dependencies

Provides dependency injection functions for JWT validation and user authentication.
Uses Auth0 JWKS for token validation.
"""

import json
import os
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

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
    Validate JWT token using Auth0 public keys.

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Get Auth0 public keys
        jwks = get_auth0_public_key()

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)

        token_kid = unverified_header.get("kid")

        # Find the correct key
        rsa_key = {}
        available_kids = []
        for key in jwks["keys"]:
            available_kids.append(key.get("kid"))
            if key["kid"] == token_kid:
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
                detail=f"Unable to find key with kid '{token_kid}'. Available kids: {available_kids}",
            )

        # Validate and decode token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=AUTH0_ALGORITHMS,
            issuer=f"https://{AUTH0_DOMAIN}/",
            options={"verify_aud": False},  # Skip audience verification for MVP
        )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token from request

    Returns:
        dict: User information from validated JWT token

    Raises:
        HTTPException: If token is missing or invalid
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
    }

    return user_info


def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency to ensure current user has admin privileges.

    Args:
        current_user: Current authenticated user from get_current_user

    Returns:
        dict: Admin user information

    Raises:
        HTTPException: If user is not an admin
    """
    # For MVP, check if email contains 'admin' or matches our test admin
    email = current_user.get("email", "").lower()

    if "admin" in email or email == "admin@example.com":
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
    )


# Optional: dependency for when authentication is optional
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    FastAPI dependency for optional authentication.
    Returns None if no token provided, validates if token is present.
    """
    if not credentials:
        return None

    return get_current_user(credentials)
