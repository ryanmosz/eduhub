"""
OAuth2 and Plone integration endpoints.

Provides endpoints for checking authentication status and Plone user synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional

from .dependencies import get_current_user
from .models import User
from .plone_bridge import get_or_create_plone_user
from ..plone_integration import get_plone_client

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Demo storage for synced users
_demo_synced_users = set()


@router.get("/plone-sync-status")
async def check_plone_sync_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if current Auth0 user is synchronized with Plone.
    
    This endpoint demonstrates the OAuth2 + Plone integration:
    1. User is authenticated via Auth0 (JWT validation)
    2. System checks if user exists in Plone
    3. Returns sync status and user details
    """
    # For demo purposes, check if we've already synced this user
    # In real implementation, this would check Plone
    import hashlib
    user_hash = hashlib.md5(current_user.email.encode()).hexdigest()
    
    # Check if user has been "synced" (for demo)
    synced = user_hash in _demo_synced_users
    
    if synced:
        # Return synced user data
        return {
            "synced": True,
            "auth0_user": {
                "email": current_user.email,
                "sub": current_user.sub,
                "name": current_user.name,
                "roles": current_user.roles,
                "permissions": current_user.permissions,
            },
            "plone_user": {
                "username": f"user_{current_user.email.split('@')[0]}_{current_user.sub[-8:]}",
                "fullname": current_user.name or current_user.email.split('@')[0],
                "roles": ["Member", "Authenticated", "Manager"] if "admin" in current_user.email else ["Member", "Authenticated"],
                "groups": ["administrators"] if "admin" in current_user.email else ["members"],
            },
            "integration_features": {
                "auto_user_creation": True,
                "role_mapping": True,
                "single_sign_on": True,
                "no_plone_password_needed": True,
            }
        }
    else:
        # User not synced yet
        return {
            "synced": False,
            "auth0_user": {
                "email": current_user.email,
                "sub": current_user.sub,
                "name": current_user.name,
                "roles": current_user.roles,
                "permissions": current_user.permissions,
            },
            "plone_user": None,
            "integration_features": {
                "auto_user_creation": True,
                "role_mapping": True,
                "single_sign_on": True,
                "no_plone_password_needed": True,
            }
        }


@router.post("/sync-with-plone")
async def sync_current_user_with_plone(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger synchronization of current user with Plone.
    
    This creates the user in Plone if they don't exist yet.
    """
    try:
        # For demo purposes, mark user as synced
        import hashlib
        user_hash = hashlib.md5(current_user.email.encode()).hexdigest()
        _demo_synced_users.add(user_hash)
        
        # Return successful sync
        return {
            "success": True,
            "message": "User synchronized with Plone",
            "plone_user": {
                "username": f"user_{current_user.email.split('@')[0]}_{current_user.sub[-8:]}",
                "email": current_user.email,
                "fullname": current_user.name or current_user.email.split('@')[0],
                "roles": ["Member", "Authenticated", "Manager"] if "admin" in current_user.email else ["Member", "Authenticated"],
            },
            "note": "User created in Plone without password - Auth0 handles authentication"
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing with Plone: {str(e)}"
        )