"""
FastAPI endpoints for workflow template management.

Provides REST API endpoints for applying workflow templates to content,
managing templates, and querying workflow states with role-based access control.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..plone_integration import PloneClient, get_plone_client
from .models import EducationRole, WorkflowTemplate
from .plone_service import PloneWorkflowError, PloneWorkflowService
from .templates import get_template, list_templates, validate_all_templates

logger = logging.getLogger(__name__)

# FastAPI router for workflow endpoints
router = APIRouter(prefix="/workflows", tags=["Workflows"])

# Security scheme
security = HTTPBearer()


# Request/Response models
class ApplyTemplateRequest(BaseModel):
    """Request model for applying workflow templates."""

    content_uid: str = Field(
        ...,
        description="Unique identifier for the content item",
        examples=["abc123-def456-ghi789"],
    )

    role_assignments: dict[EducationRole, list[str]] = Field(
        ...,
        description="Mapping of workflow roles to user/group IDs",
        examples=[
            {
                "author": ["user123", "user456"],
                "editor": ["reviewer789"],
                "administrator": ["admin001"],
            }
        ],
    )

    force: bool = Field(
        default=False, description="Whether to force application over existing workflow"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content_uid": "abc123-def456-ghi789",
                    "role_assignments": {
                        "author": ["user123", "user456"],
                        "editor": ["reviewer789"],
                        "administrator": ["admin001"],
                    },
                    "force": False,
                }
            ]
        }
    }


class ApplyTemplateResponse(BaseModel):
    """Response model for template application."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable status message")
    content_uid: str = Field(..., description="Content item UID")
    template_id: str = Field(..., description="Applied template ID")
    workflow_id: str = Field(..., description="Generated workflow ID")
    initial_state: str = Field(..., description="Initial workflow state")
    applied_at: str = Field(..., description="Application timestamp (ISO 8601)")
    backup_created: bool = Field(..., description="Whether backup was created")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Workflow template applied successfully",
                    "content_uid": "abc123-def456-ghi789",
                    "template_id": "simple_review",
                    "workflow_id": "template_simple_review_abc12345",
                    "initial_state": "draft",
                    "applied_at": "2024-01-01T12:00:00Z",
                    "backup_created": True,
                }
            ]
        }
    }


class ExecuteTransitionRequest(BaseModel):
    """Request model for executing workflow transitions."""

    content_uid: str = Field(..., description="Unique identifier for the content item")

    transition_id: str = Field(..., description="ID of the transition to execute")

    comments: Optional[str] = Field(
        default=None, description="Optional comments for the transition"
    )

    validate_permissions: bool = Field(
        default=True, description="Whether to validate user permissions"
    )


class WorkflowStateResponse(BaseModel):
    """Response model for workflow state information."""

    content_uid: str = Field(..., description="Content item UID")
    content_title: str = Field(..., description="Content item title")
    content_type: str = Field(..., description="Content type")
    current_state: str = Field(..., description="Current workflow state")
    workflow_id: str = Field(..., description="Workflow ID")
    template_id: Optional[str] = Field(None, description="Template ID if applied")
    available_transitions: list[dict[str, Any]] = Field(
        default_factory=list, description="Available transitions for current user"
    )
    last_updated: str = Field(..., description="Last update timestamp")


class TemplateListResponse(BaseModel):
    """Response model for template listing."""

    templates: list[dict[str, Any]] = Field(
        ..., description="List of available workflow templates"
    )

    total_count: int = Field(..., description="Total number of templates")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "templates": [
                        {
                            "id": "simple_review",
                            "name": "Simple Review Workflow",
                            "description": "Basic 3-state workflow for educational content",
                            "complexity": "simple",
                            "category": "educational",
                            "states_count": 3,
                            "transitions_count": 3,
                        }
                    ],
                    "total_count": 2,
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Dependency functions
async def get_workflow_service() -> PloneWorkflowService:
    """Get PloneWorkflowService instance with authenticated client."""
    plone_client = await get_plone_client()
    return PloneWorkflowService(plone_client)


# API Endpoints


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List Available Workflow Templates",
    description="Get a list of all available workflow templates with their metadata",
    responses={
        200: {
            "description": "List of workflow templates",
            "content": {
                "application/json": {
                    "example": {
                        "templates": [
                            {
                                "id": "simple_review",
                                "name": "Simple Review Workflow",
                                "description": "Basic 3-state workflow for educational content",
                                "complexity": "simple",
                                "category": "educational",
                                "states_count": 3,
                                "transitions_count": 3,
                            }
                        ],
                        "total_count": 2,
                    }
                }
            },
        },
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def list_workflow_templates(
    complexity: Optional[str] = Query(
        None,
        description="Filter by complexity level (simple, advanced)",
        examples=["simple", "advanced"],
    ),
    category: Optional[str] = Query(
        None, description="Filter by category", examples=["educational", "corporate"]
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> TemplateListResponse:
    """
    List all available workflow templates.

    Returns a list of workflow templates with metadata including:
    - Template ID and name
    - Description and complexity level
    - Number of states and transitions
    - Category and recommended usage

    Filters can be applied to narrow results by complexity or category.
    """
    try:
        logger.info(f"User {current_user.sub} listing workflow templates")

        # Get all templates
        templates = list_templates()

        # Apply filters
        if complexity:
            templates = [t for t in templates if t.get("complexity") == complexity]

        if category:
            templates = [t for t in templates if t.get("category") == category]

        return TemplateListResponse(templates=templates, total_count=len(templates))

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="template_listing_failed",
                message=f"Failed to retrieve workflow templates: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/templates/{template_id}",
    response_model=WorkflowTemplate,
    summary="Get Specific Workflow Template",
    description="Retrieve detailed information about a specific workflow template",
    responses={
        200: {"description": "Workflow template details"},
        404: {"description": "Template not found", "model": ErrorResponse},
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
    },
)
async def get_workflow_template(
    template_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> WorkflowTemplate:
    """
    Get detailed information about a specific workflow template.

    Returns the complete template definition including states, transitions,
    permissions, and metadata.
    """
    try:
        logger.info(f"User {current_user.sub} requesting template {template_id}")

        template = get_template(template_id)
        return template

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error="template_not_found",
                message=f"Workflow template '{template_id}' not found",
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="template_retrieval_failed",
                message=f"Failed to retrieve template: {str(e)}",
            ).model_dump(),
        )


@router.post(
    "/apply/{template_id}",
    response_model=ApplyTemplateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Apply Workflow Template to Content",
    description="Apply a workflow template to a Plone content item with role assignments",
    responses={
        202: {"description": "Template application accepted and processing"},
        400: {"description": "Invalid request data", "model": ErrorResponse},
        403: {"description": "Insufficient permissions", "model": ErrorResponse},
        404: {"description": "Template or content not found", "model": ErrorResponse},
        409: {"description": "Template already applied", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def apply_workflow_template(
    template_id: str,
    request: ApplyTemplateRequest,
    workflow_service: PloneWorkflowService = Depends(get_workflow_service),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ApplyTemplateResponse:
    """
    Apply a workflow template to a Plone content item.

    This endpoint:
    1. Validates the template and content existence
    2. Creates a backup of the existing workflow state
    3. Applies the new workflow template
    4. Assigns roles to users/groups
    5. Sets the initial state

    The operation is atomic - if any step fails, changes are rolled back.
    """
    try:
        logger.info(
            f"User {current_user.sub} applying template {template_id} to {request.content_uid}"
        )

        # Get template
        try:
            template = get_template(template_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="template_not_found",
                    message=f"Workflow template '{template_id}' not found",
                ).model_dump(),
            )

        # Apply template
        result = await workflow_service.apply_workflow_template(
            content_uid=request.content_uid,
            template=template,
            role_assignments=request.role_assignments,
            force=request.force,
        )

        return ApplyTemplateResponse(
            success=result["success"],
            message="Workflow template applied successfully",
            content_uid=result["content_uid"],
            template_id=result["template_id"],
            workflow_id=result["workflow_id"],
            initial_state=result["initial_state"],
            applied_at=result["applied_at"],
            backup_created=bool(result.get("backup_info")),
        )

    except PloneWorkflowError as e:
        error_msg = str(e)

        # Determine appropriate HTTP status based on error type
        if "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
            error_type = "content_not_found"
        elif "already has template" in error_msg.lower():
            status_code = status.HTTP_409_CONFLICT
            error_type = "template_already_applied"
        elif "permission" in error_msg.lower():
            status_code = status.HTTP_403_FORBIDDEN
            error_type = "permission_denied"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            error_type = "workflow_application_failed"

        logger.error(f"Workflow application failed: {error_msg}")
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(error=error_type, message=error_msg).model_dump(),
        )
    except Exception as e:
        logger.error(f"Unexpected error applying template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred while applying the workflow template",
            ).model_dump(),
        )


@router.post(
    "/transition",
    summary="Execute Workflow Transition",
    description="Execute a workflow transition for content",
    responses={
        200: {"description": "Transition executed successfully"},
        400: {"description": "Invalid transition or content state"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Content or transition not found"},
        500: {"description": "Internal server error"},
    },
)
async def execute_workflow_transition(
    request: ExecuteTransitionRequest,
    workflow_service: PloneWorkflowService = Depends(get_workflow_service),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Execute a workflow transition for content.

    Validates user permissions and executes the requested transition,
    updating the content's workflow state and recording the action in history.
    """
    try:
        user_id = current_user.sub
        logger.info(
            f"User {user_id} executing transition {request.transition_id} for {request.content_uid}"
        )

        result = await workflow_service.execute_workflow_transition(
            content_uid=request.content_uid,
            transition_id=request.transition_id,
            user_id=user_id,
            comments=request.comments,
            validate_permissions=request.validate_permissions,
        )

        return result

    except PloneWorkflowError as e:
        error_msg = str(e)

        if "permission" in error_msg.lower():
            status_code = status.HTTP_403_FORBIDDEN
            error_type = "permission_denied"
        elif "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
            error_type = "content_not_found"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            error_type = "transition_failed"

        logger.error(f"Transition execution failed: {error_msg}")
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(error=error_type, message=error_msg).model_dump(),
        )
    except Exception as e:
        logger.error(f"Unexpected error executing transition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred while executing the transition",
            ).model_dump(),
        )


@router.get(
    "/content/{content_uid}/state",
    response_model=WorkflowStateResponse,
    summary="Get Content Workflow State",
    description="Get the current workflow state and available actions for content",
    responses={
        200: {"description": "Current workflow state"},
        404: {"description": "Content not found"},
        403: {"description": "Insufficient permissions"},
    },
)
async def get_content_workflow_state(
    content_uid: str,
    workflow_service: PloneWorkflowService = Depends(get_workflow_service),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> WorkflowStateResponse:
    """
    Get the current workflow state for a content item.

    Returns information about the current state, available transitions,
    and template metadata if a template is applied.
    """
    try:
        logger.info(
            f"User {current_user.sub} querying workflow state for {content_uid}"
        )

        # Get workflow state
        state = await workflow_service.get_content_workflow_state(content_uid)

        # Get user-specific permissions and transitions
        user_permissions = await workflow_service.get_user_workflow_permissions(
            content_uid, current_user.sub
        )

        return WorkflowStateResponse(
            content_uid=state["content_uid"],
            content_title=state["content_title"],
            content_type=state["content_type"],
            current_state=state["current_state"],
            workflow_id=state["workflow_id"],
            template_id=state.get("template_metadata", {}).get("template_id"),
            available_transitions=user_permissions.get("available_transitions", []),
            last_updated=state["last_updated"],
        )

    except PloneWorkflowError as e:
        error_msg = str(e)

        if "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
            error_type = "content_not_found"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            error_type = "workflow_query_failed"

        logger.error(f"Workflow state query failed: {error_msg}")
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(error=error_type, message=error_msg).model_dump(),
        )
    except Exception as e:
        logger.error(f"Unexpected error querying workflow state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred while querying workflow state",
            ).model_dump(),
        )


@router.delete(
    "/content/{content_uid}/template",
    summary="Remove Workflow Template",
    description="Remove workflow template from content and optionally restore backup",
    responses={
        200: {"description": "Template removed successfully"},
        404: {"description": "Content not found or no template applied"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"},
    },
)
async def remove_workflow_template(
    content_uid: str,
    restore_backup: bool = Query(
        True, description="Whether to restore original workflow"
    ),
    workflow_service: PloneWorkflowService = Depends(get_workflow_service),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Remove a workflow template from content.

    Optionally restores the original workflow from backup.
    This operation cannot be undone unless a backup exists.
    """
    try:
        logger.info(f"User {current_user.sub} removing template from {content_uid}")

        result = await workflow_service.remove_workflow_template(
            content_uid=content_uid, restore_backup=restore_backup
        )

        return result

    except PloneWorkflowError as e:
        error_msg = str(e)

        if "not found" in error_msg.lower() or "does not have" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
            error_type = "template_not_applied"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            error_type = "template_removal_failed"

        logger.error(f"Template removal failed: {error_msg}")
        raise HTTPException(
            status_code=status_code,
            detail=ErrorResponse(error=error_type, message=error_msg).model_dump(),
        )
    except Exception as e:
        logger.error(f"Unexpected error removing template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred while removing the template",
            ).model_dump(),
        )


@router.get(
    "/health",
    summary="Workflow System Health Check",
    description="Check the health and availability of the workflow system",
    responses={
        200: {"description": "System is healthy"},
        503: {"description": "System is unhealthy"},
    },
)
async def workflow_health_check(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Perform a health check of the workflow system.

    Validates that templates are loadable and the system is functioning properly.
    """
    try:
        # Validate all templates
        templates_valid = validate_all_templates()

        # Count available templates
        templates = list_templates()
        template_count = len(templates)

        # Check if we can load a simple template
        simple_template = get_template("simple_review")

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "templates_valid": templates_valid,
            "template_count": template_count,
            "test_template_loadable": simple_template.id == "simple_review",
            "version": "1.0.0",
        }

        return health_status

    except Exception as e:
        logger.error(f"Workflow health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse(
                error="system_unhealthy",
                message=f"Workflow system health check failed: {str(e)}",
            ).model_dump(),
        )
