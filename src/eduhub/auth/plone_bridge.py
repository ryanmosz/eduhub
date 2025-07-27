"""
Auth0 to Plone user integration bridge.

This module handles mapping Auth0 users to Plone users, creating users when needed,
and combining Auth0 claims with Plone user roles/groups.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..plone_integration import PloneAPIError, get_plone_client
from .models import User

logger = logging.getLogger(__name__)


def generate_plone_username(email: str, auth0_sub: str) -> str:
    """
    Generate a valid Plone username from Auth0 user data.

    Args:
        email: User's email address
        auth0_sub: Auth0 subject ID

    Returns:
        Valid Plone username
    """
    # Extract username part from email
    username_base = email.split("@")[0]

    # Clean username to be Plone-compatible (alphanumeric + . _ -)
    username_clean = re.sub(r"[^a-zA-Z0-9._-]", "_", username_base)

    # Ensure it starts with a letter
    if not username_clean[0].isalpha():
        username_clean = "user_" + username_clean

    # Limit length and add Auth0 suffix for uniqueness
    auth0_suffix = auth0_sub.split("|")[-1][:8]  # Last 8 chars of Auth0 ID
    max_base_length = 20 - len(auth0_suffix) - 1  # Leave room for suffix

    if len(username_clean) > max_base_length:
        username_clean = username_clean[:max_base_length]

    return f"{username_clean}_{auth0_suffix}"


def extract_roles_from_auth0(auth0_user: dict[str, Any]) -> list[str]:
    """
    Extract Plone roles from Auth0 user metadata.

    Args:
        auth0_user: Auth0 user data

    Returns:
        List of Plone role names
    """
    roles = []

    # Check Auth0 custom claims for roles
    user_metadata = auth0_user.get("user_metadata", {})
    app_metadata = auth0_user.get("app_metadata", {})

    # Look for roles in various places
    auth0_roles = (
        auth0_user.get("roles", [])
        or user_metadata.get("roles", [])
        or app_metadata.get("roles", [])
        or auth0_user.get("https://eduhub.edu/roles", [])  # Custom namespace
    )

    if auth0_roles:
        roles.extend(auth0_roles)

    # Default role mapping based on email domain
    email = auth0_user.get("email", "")
    if email.endswith("@example.edu"):
        roles.append("Faculty")
    elif email.endswith("@student.example.edu"):
        roles.append("Student")

    # Admin detection
    if email in ["admin@example.com", "admin@example.edu"]:
        roles.append("Manager")

    # Ensure all users get basic Member role
    if not roles:
        roles.append("Member")

    return list(set(roles))  # Remove duplicates


async def get_or_create_plone_user(
    auth0_user: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """
    Get existing Plone user or create new one based on Auth0 user data.

    Args:
        auth0_user: Auth0 user data with email, name, etc.

    Returns:
        Plone user data dict, or None if error
    """
    
    email = auth0_user.get("email")
    if not email:
        logger.error("Auth0 user missing email address")
        return None

    try:
        plone_client = await get_plone_client()

        # First, try to find existing user by email
        existing_user = await plone_client.get_user_by_email(email)

        if existing_user:
            logger.info(f"Found existing Plone user for email: {email}")
            return existing_user

        # User doesn't exist, create new one
        logger.info(f"Creating new Plone user for Auth0 user: {email}")

        # Generate username and extract user info
        username = generate_plone_username(email, auth0_user.get("sub", ""))
        fullname = (
            auth0_user.get("name")
            or auth0_user.get("given_name", "")
            + " "
            + auth0_user.get("family_name", "")
        ).strip()

        if not fullname:
            fullname = email.split("@")[0]  # Fallback to email username

        # Extract roles for user creation
        plone_roles = extract_roles_from_auth0(auth0_user)

        # Create user in Plone
        new_user = await plone_client.create_user(
            username=username,
            email=email,
            fullname=fullname,
            description=f"User created from Auth0: {auth0_user.get('sub', '')}",
            # Note: No password set - user authenticates via Auth0
        )

        logger.info(f"Successfully created Plone user: {username}")
        return new_user

    except PloneAPIError as e:
        logger.error(f"Error creating/retrieving Plone user for {email}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_or_create_plone_user: {e}")
        return None


def combine_user_context(
    auth0_claims: dict[str, Any], plone_user: Optional[dict[str, Any]]
) -> User:
    """
    Combine Auth0 claims with Plone user data into unified User model.

    Args:
        auth0_claims: Validated JWT claims from Auth0
        plone_user: Plone user data (if available)

    Returns:
        Combined User model with all available data
    """
    # Extract basic info from Auth0
    email = auth0_claims.get("email", "")
    name = auth0_claims.get("name", email.split("@")[0])
    sub = auth0_claims.get("sub", "")

    # Get Auth0 roles
    auth0_roles = extract_roles_from_auth0(auth0_claims)

    # Get Plone roles and user info if available
    plone_roles = []
    plone_groups = []
    plone_user_id = None

    if plone_user:
        plone_roles = plone_user.get("roles", [])
        plone_groups = plone_user.get("groups", [])
        plone_user_id = plone_user.get("username") or plone_user.get("id")

        # Use Plone fullname if available and more complete
        plone_fullname = plone_user.get("fullname", "")
        if plone_fullname and len(plone_fullname) > len(name):
            name = plone_fullname

    # Combine and deduplicate roles
    combined_roles = list(set(auth0_roles + plone_roles))

    # Create permissions list from roles
    permissions = []
    if "Manager" in combined_roles:
        permissions.extend(["create", "edit", "delete", "view", "admin"])
    elif "Faculty" in combined_roles:
        permissions.extend(["create", "edit", "view"])
    elif "Student" in combined_roles:
        permissions.extend(["view"])
    else:
        permissions.append("view")  # Default permission

    return User(
        sub=sub,
        email=email,
        email_verified=auth0_claims.get("email_verified", False),
        name=name,
        picture=auth0_claims.get("picture"),
        nickname=auth0_claims.get("nickname", email.split("@")[0]),
        # JWT required fields
        aud=auth0_claims.get("aud", ""),
        iss=auth0_claims.get("iss", ""),
        exp=auth0_claims.get("exp", 0),
        iat=auth0_claims.get("iat", 0),
        # Combined data fields
        roles=combined_roles,
        permissions=list(set(permissions)),  # Remove duplicates
        plone_user_id=plone_user_id,
        plone_groups=plone_groups,
        # Add metadata about the integration
        auth0_data={
            "aud": auth0_claims.get("aud"),
            "iss": auth0_claims.get("iss"),
            "iat": auth0_claims.get("iat"),
            "exp": auth0_claims.get("exp"),
        },
    )


async def sync_auth0_user_to_plone(auth0_claims: dict[str, Any]) -> Optional[User]:
    """
    Complete integration flow: lookup/create Plone user and return combined context.

    Args:
        auth0_claims: Validated JWT claims from Auth0

    Returns:
        Combined User model with Auth0 + Plone data, or None if error
    """
    try:
        # Get or create the Plone user
        plone_user = await get_or_create_plone_user(auth0_claims)

        # Combine the data into unified user context
        combined_user = combine_user_context(auth0_claims, plone_user)

        logger.info(
            f"Successfully synced Auth0 user {auth0_claims.get('email')} with Plone"
        )
        return combined_user

    except Exception as e:
        logger.error(f"Error syncing Auth0 user to Plone: {e}")
        return None
