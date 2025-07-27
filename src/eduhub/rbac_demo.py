"""
Role-Based Access Control demonstration endpoints.

Shows how Plone roles integrate with FastAPI permissions.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from .auth.dependencies import get_current_user, get_admin_user
from .auth.models import User

router = APIRouter(prefix="/api/rbac", tags=["RBAC Demo"])


@router.get("/check-access")
async def check_user_access(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Check current user's access level and permissions.
    
    This endpoint demonstrates role-based access control integration.
    """
    # Determine access level based on roles
    is_manager = "Manager" in current_user.roles or "admin" in current_user.email.lower()
    is_editor = "Editor" in current_user.roles or "dev" in current_user.email.lower()
    is_student = "Student" in current_user.roles or "student" in current_user.email.lower()
    
    return {
        "user": {
            "email": current_user.email,
            "roles": current_user.roles,
            "permissions": current_user.permissions,
        },
        "access_level": {
            "is_manager": is_manager,
            "is_editor": is_editor,
            "is_student": is_student,
            "is_authenticated": True,
        },
        "allowed_operations": {
            "view_content": True,  # All authenticated users
            "create_content": is_manager or is_editor,
            "edit_content": is_manager or is_editor,
            "delete_content": is_manager,
            "import_schedules": is_manager or is_editor,
            "manage_users": is_manager,
            "send_alerts": is_manager,
            "export_data": True,  # All authenticated users
        },
        "plone_integration": {
            "roles_from_plone": current_user.roles,
            "plone_user_id": current_user.plone_user_id,
            "plone_groups": current_user.plone_groups or [],
        }
    }


@router.get("/manager-only")
async def manager_only_endpoint(admin_user: User = Depends(get_admin_user)) -> Dict[str, Any]:
    """
    Endpoint that requires Manager/Admin role.
    
    This demonstrates role-based protection at the endpoint level.
    """
    return {
        "message": "Access granted - Manager role verified",
        "user": admin_user.email,
        "roles": admin_user.roles,
        "operations": [
            "Delete any content",
            "Manage user accounts", 
            "Configure system settings",
            "Send system-wide alerts",
        ]
    }


@router.get("/editor-access")
async def editor_access_endpoint(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Endpoint that requires Editor role or higher.
    
    Students cannot access this endpoint.
    """
    # Check if user has editor permissions
    user_roles = [role.lower() for role in current_user.roles]
    is_editor_plus = any(role in user_roles for role in ["manager", "editor", "admin"])
    
    # Also check email-based access
    if not is_editor_plus:
        email = current_user.email.lower()
        is_editor_plus = "admin" in email or "dev" in email
    
    if not is_editor_plus:
        raise HTTPException(
            status_code=403,
            detail="Editor role or higher required. Students have read-only access."
        )
    
    return {
        "message": "Access granted - Editor permissions verified",
        "user": current_user.email,
        "roles": current_user.roles,
        "operations": [
            "Create new content",
            "Edit existing content",
            "Import CSV schedules",
            "Moderate comments",
        ]
    }


@router.get("/public-read")
async def public_read_endpoint(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Endpoint accessible to all authenticated users.
    
    Even students can access this.
    """
    return {
        "message": "Public content accessible to all authenticated users",
        "user": current_user.email,
        "role": "student" if "student" in current_user.email.lower() else "staff",
        "content": [
            {"id": 1, "title": "Introduction to Computer Science", "type": "course"},
            {"id": 2, "title": "Physics Lab Schedule", "type": "schedule"},
            {"id": 3, "title": "Campus Events Calendar", "type": "events"},
        ]
    }