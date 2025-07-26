"""
Authentication Data Models

Pydantic models for user authentication, JWT tokens, and Auth0 integration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """
    User model representing authenticated user from Auth0 JWT token.
    """

    sub: str = Field(..., description="Auth0 user ID (subject)")
    email: EmailStr = Field(..., description="User email address")
    email_verified: bool = Field(default=False, description="Whether email is verified")
    name: Optional[str] = Field(None, description="User display name")
    picture: Optional[str] = Field(None, description="User profile picture URL")
    nickname: Optional[str] = Field(None, description="User nickname")

    # JWT token fields
    aud: str = Field(..., description="Token audience (client ID)")
    iss: str = Field(..., description="Token issuer (Auth0 domain)")
    exp: int = Field(..., description="Token expiration timestamp")
    iat: int = Field(..., description="Token issued at timestamp")

    # Additional metadata
    roles: list[str] = Field(default_factory=list, description="User roles")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    plone_user_id: Optional[str] = Field(None, description="Associated Plone user ID")

    # Plone integration fields
    plone_groups: list[str] = Field(
        default_factory=list, description="Plone user groups"
    )
    auth0_data: Optional[dict[str, Any]] = Field(
        None, description="Additional Auth0 metadata"
    )

    class Config:
        """Pydantic configuration"""

        json_schema_extra = {
            "example": {
                "sub": "auth0|507f1f77bcf86cd799439011",
                "email": "dev@example.com",
                "email_verified": True,
                "name": "Development User",
                "picture": "https://example.com/avatar.jpg",
                "nickname": "dev",
                "aud": "s05QngyZXEI3XNdirmJu0CscW1hNgaRD",
                "iss": "https://dev-1fx6yhxxi543ipno.us.auth0.com/",
                "exp": 1640995200,
                "iat": 1640908800,
                "roles": ["Member", "Faculty"],
                "permissions": ["view", "create", "edit"],
                "plone_user_id": "dev_68842107",
                "plone_groups": ["Faculty", "Content-Contributors"],
                "auth0_data": {
                    "aud": "s05QngyZXEI3XNdirmJu0CscW1hNgaRD",
                    "iss": "https://dev-1fx6yhxxi543ipno.us.auth0.com/",
                    "iat": 1640908800,
                    "exp": 1640995200,
                },
            }
        }


class UserCreate(BaseModel):
    """
    Model for creating new users (if needed for admin functionality).
    """

    email: EmailStr = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    roles: list[str] = Field(
        default_factory=lambda: ["user"], description="Initial user roles"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "name": "New User",
                "roles": ["user"],
            }
        }


class UserUpdate(BaseModel):
    """
    Model for updating user information.
    """

    name: Optional[str] = Field(None, description="Updated display name")
    roles: Optional[list[str]] = Field(None, description="Updated user roles")
    permissions: Optional[list[str]] = Field(
        None, description="Updated user permissions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated User Name",
                "roles": ["user", "admin"],
                "permissions": ["read:profile", "write:content"],
            }
        }


class Token(BaseModel):
    """
    JWT token model for API responses.
    """

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            }
        }


class TokenData(BaseModel):
    """
    Token validation data model.
    """

    sub: Optional[str] = Field(None, description="Token subject (user ID)")
    email: Optional[str] = Field(None, description="User email from token")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "auth0|507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "scopes": ["read:profile", "write:content"],
            }
        }


class AuthResponse(BaseModel):
    """
    Authentication response model.
    """

    message: str = Field(..., description="Response message")
    user: Optional[User] = Field(None, description="Authenticated user data")
    redirect_url: Optional[str] = Field(None, description="Redirect URL for OAuth flow")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Login successful",
                "user": {
                    "sub": "auth0|507f1f77bcf86cd799439011",
                    "email": "dev@example.com",
                    "name": "Development User",
                },
                "redirect_url": None,
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model for authentication failures.
    """

    error: str = Field(..., description="Error type")
    error_description: str = Field(..., description="Human-readable error description")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "invalid_token",
                "error_description": "The access token is invalid or has expired",
            }
        }


class PloneUserData(BaseModel):
    """
    Model for Plone user integration data.
    """

    plone_user_id: str = Field(..., description="Plone user ID")
    plone_roles: list[str] = Field(default_factory=list, description="Plone roles")
    plone_groups: list[str] = Field(default_factory=list, description="Plone groups")
    plone_properties: dict[str, Any] = Field(
        default_factory=dict, description="Plone user properties"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plone_user_id": "dev-user",
                "plone_roles": ["Member", "Contributor"],
                "plone_groups": ["educators", "content-creators"],
                "plone_properties": {
                    "fullname": "Development User",
                    "email": "dev@example.com",
                    "department": "Education Technology",
                },
            }
        }
