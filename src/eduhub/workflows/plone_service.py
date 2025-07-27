"""
Plone CMS integration service for workflow templates.

This module provides the bridge between our workflow template system
and Plone's native workflow engine, handling template application,
role assignment, and permission synchronization.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from ..plone_integration import PloneClient
from .models import (
    EducationRole,
    InvalidWorkflowError,
    WorkflowAction,
    WorkflowError,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)


class PloneWorkflowError(WorkflowError):
    """Raised when Plone workflow operations fail."""

    pass


class PloneWorkflowService:
    """
    Service for integrating workflow templates with Plone CMS.

    Handles:
    - Template-to-Plone workflow mapping
    - Workflow application and rollback
    - Role assignment and permission sync
    - State querying and transition execution
    """

    def __init__(self, plone_client: PloneClient):
        self.plone = plone_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def get_content_workflow_state(self, content_uid: str) -> dict[str, Any]:
        """
        Get the current workflow state of a Plone content item.

        Args:
            content_uid: Unique identifier for the content item

        Returns:
            Dictionary containing workflow state information

        Raises:
            PloneWorkflowError: If content not found or workflow access fails
        """
        try:
            # Get content item
            content = await self.plone.get_content_by_uid(content_uid)
            if not content:
                raise PloneWorkflowError(f"Content with UID {content_uid} not found")

            # Get workflow information
            workflow_info = await self.plone.get_workflow_info(content_uid)

            return {
                "content_uid": content_uid,
                "content_title": content.get("title", ""),
                "content_type": content.get("@type", ""),
                "current_state": workflow_info.get("state", ""),
                "workflow_id": workflow_info.get("workflow_id", ""),
                "available_transitions": workflow_info.get("transitions", []),
                "workflow_history": workflow_info.get("history", []),
                "template_metadata": content.get("workflow_template_metadata", {}),
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to get workflow state for {content_uid}: {e}")
            raise PloneWorkflowError(f"Failed to get workflow state: {str(e)}")

    async def apply_workflow_template(
        self,
        content_uid: str,
        template: WorkflowTemplate,
        role_assignments: dict[EducationRole, list[str]],
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Apply a workflow template to a Plone content item.

        Args:
            content_uid: Target content item UID
            template: WorkflowTemplate to apply
            role_assignments: Mapping of roles to user/group IDs
            force: Whether to force application over existing workflow

        Returns:
            Application result with rollback information

        Raises:
            PloneWorkflowError: If application fails
        """
        self.logger.info(f"Applying template {template.id} to content {content_uid}")

        try:
            # Validate template and content
            await self._validate_template_application(content_uid, template, force)

            # Backup existing workflow state
            backup_info = await self._backup_workflow_state(content_uid)

            # Create Plone workflow definition
            plone_workflow_def = self._convert_template_to_plone_workflow(template)

            # Apply workflow to Plone
            workflow_id = f"template_{template.id}_{content_uid[:8]}"
            await self._create_plone_workflow(workflow_id, plone_workflow_def)

            # Assign workflow to content
            await self._assign_workflow_to_content(content_uid, workflow_id)

            # Configure role assignments
            await self._apply_role_assignments(content_uid, role_assignments)

            # Store template metadata
            await self._store_template_metadata(content_uid, template, role_assignments)

            # Set initial state
            initial_state = next(s for s in template.states if s.is_initial)
            await self._set_content_workflow_state(content_uid, initial_state.id)

            result = {
                "success": True,
                "content_uid": content_uid,
                "template_id": template.id,
                "workflow_id": workflow_id,
                "initial_state": initial_state.id,
                "backup_info": backup_info,
                "role_assignments": {
                    role.value: users for role, users in role_assignments.items()
                },
                "applied_at": datetime.utcnow().isoformat(),
            }

            self.logger.info(
                f"Successfully applied template {template.id} to {content_uid}"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Failed to apply template {template.id} to {content_uid}: {e}"
            )

            # Attempt rollback if we got far enough
            try:
                if "backup_info" in locals():
                    await self._rollback_workflow_application(content_uid, backup_info)
            except Exception as rollback_error:
                self.logger.error(f"Rollback also failed: {rollback_error}")

            raise PloneWorkflowError(f"Template application failed: {str(e)}")

    async def execute_workflow_transition(
        self,
        content_uid: str,
        transition_id: str,
        user_id: str,
        comments: Optional[str] = None,
        validate_permissions: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a workflow transition for content.

        Args:
            content_uid: Target content UID
            transition_id: ID of transition to execute
            user_id: User executing the transition
            comments: Optional transition comments
            validate_permissions: Whether to validate user permissions

        Returns:
            Transition execution result

        Raises:
            PloneWorkflowError: If transition fails
        """
        self.logger.info(
            f"Executing transition {transition_id} for {content_uid} by {user_id}"
        )

        try:
            # Get current workflow state
            current_state = await self.get_content_workflow_state(content_uid)

            # Load template metadata
            template_metadata = current_state.get("template_metadata", {})
            if not template_metadata:
                raise PloneWorkflowError(
                    "Content does not have workflow template metadata"
                )

            template_id = template_metadata.get("template_id")
            if not template_id:
                raise PloneWorkflowError("No template ID in content metadata")

            # Validate transition permissions if requested
            if validate_permissions:
                await self._validate_transition_permissions(
                    content_uid, transition_id, user_id, template_metadata
                )

            # Execute transition in Plone
            transition_result = await self.plone.execute_workflow_transition(
                content_uid, transition_id, comments
            )

            # Update workflow history
            await self._update_workflow_history(
                content_uid, transition_id, user_id, comments, transition_result
            )

            result = {
                "success": True,
                "content_uid": content_uid,
                "transition_id": transition_id,
                "executed_by": user_id,
                "from_state": current_state["current_state"],
                "to_state": transition_result.get("new_state"),
                "comments": comments,
                "executed_at": datetime.utcnow().isoformat(),
                "workflow_history_entry": transition_result.get("history_entry", {}),
            }

            self.logger.info(
                f"Successfully executed transition {transition_id} for {content_uid}"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Failed to execute transition {transition_id} for {content_uid}: {e}"
            )
            raise PloneWorkflowError(f"Transition execution failed: {str(e)}")

    async def get_user_workflow_permissions(
        self, content_uid: str, user_id: str
    ) -> dict[str, Any]:
        """
        Get workflow permissions for a user on specific content.

        Args:
            content_uid: Target content UID
            user_id: User to check permissions for

        Returns:
            User's workflow permissions and available actions

        Raises:
            PloneWorkflowError: If permission check fails
        """
        try:
            # Get current workflow state
            workflow_state = await self.get_content_workflow_state(content_uid)

            # Load template metadata
            template_metadata = workflow_state.get("template_metadata", {})
            if not template_metadata:
                return {"error": "No workflow template metadata"}

            # Get user's roles for this content
            user_roles = await self._get_user_roles_for_content(content_uid, user_id)

            # Determine available actions based on current state and user roles
            current_state = workflow_state["current_state"]
            available_actions = await self._get_available_actions_for_user(
                template_metadata, current_state, user_roles
            )

            # Get available transitions
            available_transitions = await self._get_available_transitions_for_user(
                content_uid, user_roles, workflow_state["available_transitions"]
            )

            return {
                "content_uid": content_uid,
                "user_id": user_id,
                "current_state": current_state,
                "user_roles": user_roles,
                "available_actions": list(available_actions),
                "available_transitions": available_transitions,
                "template_id": template_metadata.get("template_id"),
                "checked_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(
                f"Failed to get user permissions for {content_uid}, user {user_id}: {e}"
            )
            raise PloneWorkflowError(f"Permission check failed: {str(e)}")

    async def remove_workflow_template(
        self, content_uid: str, restore_backup: bool = True
    ) -> dict[str, Any]:
        """
        Remove workflow template from content and optionally restore original workflow.

        Args:
            content_uid: Target content UID
            restore_backup: Whether to restore the original workflow

        Returns:
            Removal result

        Raises:
            PloneWorkflowError: If removal fails
        """
        self.logger.info(f"Removing workflow template from content {content_uid}")

        try:
            # Get current state
            current_state = await self.get_content_workflow_state(content_uid)
            template_metadata = current_state.get("template_metadata", {})

            if not template_metadata:
                raise PloneWorkflowError(
                    "Content does not have workflow template applied"
                )

            # Remove template metadata
            await self._remove_template_metadata(content_uid)

            # Restore original workflow if requested
            if restore_backup and template_metadata.get("backup_info"):
                await self._restore_workflow_from_backup(
                    content_uid, template_metadata["backup_info"]
                )

            # Clean up template-specific workflow
            template_workflow_id = template_metadata.get("workflow_id")
            if template_workflow_id:
                await self._cleanup_template_workflow(template_workflow_id)

            result = {
                "success": True,
                "content_uid": content_uid,
                "removed_template_id": template_metadata.get("template_id"),
                "restored_backup": restore_backup,
                "removed_at": datetime.utcnow().isoformat(),
            }

            self.logger.info(
                f"Successfully removed workflow template from {content_uid}"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Failed to remove workflow template from {content_uid}: {e}"
            )
            raise PloneWorkflowError(f"Template removal failed: {str(e)}")

    # Private helper methods

    async def _validate_template_application(
        self, content_uid: str, template: WorkflowTemplate, force: bool
    ) -> None:
        """Validate that template can be applied to content."""
        # Check if content exists
        content = await self.plone.get_content_by_uid(content_uid)
        if not content:
            raise PloneWorkflowError(f"Content with UID {content_uid} not found")

        # Check if template is already applied
        current_state = await self.get_content_workflow_state(content_uid)
        template_metadata = current_state.get("template_metadata", {})

        if template_metadata and not force:
            existing_template = template_metadata.get("template_id")
            raise PloneWorkflowError(
                f"Content already has template {existing_template} applied. Use force=True to override."
            )

        # Validate template integrity
        try:
            # This triggers the Pydantic validation
            template.model_validate(template.model_dump())
        except Exception as e:
            raise InvalidWorkflowError(f"Template validation failed: {str(e)}")

    async def _backup_workflow_state(self, content_uid: str) -> dict[str, Any]:
        """Create backup of current workflow state."""
        try:
            current_state = await self.get_content_workflow_state(content_uid)

            backup = {
                "content_uid": content_uid,
                "original_workflow_id": current_state.get("workflow_id"),
                "original_state": current_state.get("current_state"),
                "workflow_history": current_state.get("workflow_history", []),
                "backed_up_at": datetime.utcnow().isoformat(),
            }

            self.logger.debug(f"Created workflow backup for {content_uid}")
            return backup

        except Exception as e:
            self.logger.error(f"Failed to backup workflow state for {content_uid}: {e}")
            raise PloneWorkflowError(f"Workflow backup failed: {str(e)}")

    def _convert_template_to_plone_workflow(
        self, template: WorkflowTemplate
    ) -> dict[str, Any]:
        """Convert WorkflowTemplate to Plone workflow definition."""
        # Map our states to Plone states
        plone_states = {}
        for state in template.states:
            plone_states[state.id] = {
                "title": state.title,
                "description": state.description or "",
                "permissions": self._convert_permissions_to_plone(state.permissions),
                "metadata": {
                    "state_type": state.state_type.value,
                    "is_initial": state.is_initial,
                    "is_final": state.is_final,
                    "ui_metadata": state.ui_metadata or {},
                },
            }

        # Map our transitions to Plone transitions
        plone_transitions = {}
        for transition in template.transitions:
            plone_transitions[transition.id] = {
                "title": transition.title,
                "from_state": transition.from_state,
                "to_state": transition.to_state,
                "permission": self._map_role_to_plone_permission(
                    transition.required_role
                ),
                "conditions": transition.conditions or {},
                "metadata": {
                    "required_role": transition.required_role.value,
                },
            }

        return {
            "id": f"template_{template.id}",
            "title": template.name,
            "description": template.description,
            "states": plone_states,
            "transitions": plone_transitions,
            "initial_state": next(s.id for s in template.states if s.is_initial),
            "metadata": {
                "template_id": template.id,
                "template_version": template.version,
                "category": template.category,
                "created_from_template": True,
                "original_template": template.model_dump(),
            },
        }

    def _convert_permissions_to_plone(self, permissions: list) -> dict[str, list[str]]:
        """Convert our permission model to Plone's permission format."""
        plone_permissions = {}

        for permission in permissions:
            role_name = self._map_role_to_plone_role(permission.role)

            for action in permission.actions:
                plone_permission = self._map_action_to_plone_permission(action)
                if plone_permission not in plone_permissions:
                    plone_permissions[plone_permission] = []

                if role_name not in plone_permissions[plone_permission]:
                    plone_permissions[plone_permission].append(role_name)

        return plone_permissions

    def _map_role_to_plone_role(self, role: EducationRole) -> str:
        """Map our EducationRole to Plone role names."""
        role_mapping = {
            EducationRole.AUTHOR: "Author",
            EducationRole.PEER_REVIEWER: "Reviewer",
            EducationRole.EDITOR: "Editor",
            EducationRole.SUBJECT_EXPERT: "Subject Expert",
            EducationRole.PUBLISHER: "Publisher",
            EducationRole.ADMINISTRATOR: "Manager",
            EducationRole.VIEWER: "Reader",
        }
        return role_mapping.get(role, role.value)

    def _map_action_to_plone_permission(self, action: WorkflowAction) -> str:
        """Map our WorkflowAction to Plone permission names."""
        action_mapping = {
            WorkflowAction.VIEW: "View",
            WorkflowAction.EDIT: "Modify portal content",
            WorkflowAction.DELETE: "Delete objects",
            WorkflowAction.SUBMIT: "Request review",
            WorkflowAction.REVIEW: "Review portal content",
            WorkflowAction.APPROVE: "Review portal content",
            WorkflowAction.PUBLISH: "Review portal content",
            WorkflowAction.REJECT: "Review portal content",
            WorkflowAction.RETRACT: "Review portal content",
            WorkflowAction.MANAGE_WORKFLOW: "Manage portal content",
            WorkflowAction.ASSIGN_ROLES: "Manage users",
        }
        return action_mapping.get(action, action.value)

    def _map_role_to_plone_permission(self, role: EducationRole) -> str:
        """Map role to the permission needed to execute transitions."""
        return f"Workflow: {self._map_role_to_plone_role(role)} can execute"

    async def _create_plone_workflow(
        self, workflow_id: str, workflow_def: dict[str, Any]
    ) -> None:
        """Create workflow definition in Plone."""
        try:
            # Use PloneClient to create the workflow
            await self.plone.create_workflow(workflow_id, workflow_def)
            self.logger.debug(f"Created Plone workflow {workflow_id}")
        except Exception as e:
            raise PloneWorkflowError(f"Failed to create Plone workflow: {str(e)}")

    async def _assign_workflow_to_content(
        self, content_uid: str, workflow_id: str
    ) -> None:
        """Assign workflow to specific content item."""
        try:
            await self.plone.assign_workflow_to_content(content_uid, workflow_id)
            self.logger.debug(
                f"Assigned workflow {workflow_id} to content {content_uid}"
            )
        except Exception as e:
            raise PloneWorkflowError(f"Failed to assign workflow to content: {str(e)}")

    async def _apply_role_assignments(
        self, content_uid: str, role_assignments: dict[EducationRole, list[str]]
    ) -> None:
        """Apply role assignments to content."""
        try:
            for role, user_ids in role_assignments.items():
                plone_role = self._map_role_to_plone_role(role)
                await self.plone.assign_local_roles(content_uid, plone_role, user_ids)

            self.logger.debug(f"Applied role assignments to content {content_uid}")
        except Exception as e:
            raise PloneWorkflowError(f"Failed to apply role assignments: {str(e)}")

    async def _store_template_metadata(
        self,
        content_uid: str,
        template: WorkflowTemplate,
        role_assignments: dict[EducationRole, list[str]],
    ) -> None:
        """Store template metadata in content."""
        metadata = {
            "template_id": template.id,
            "template_name": template.name,
            "template_version": template.version,
            "role_assignments": {
                role.value: users for role, users in role_assignments.items()
            },
            "applied_at": datetime.utcnow().isoformat(),
        }

        try:
            await self.plone.update_content_metadata(
                content_uid, {"workflow_template_metadata": metadata}
            )
            self.logger.debug(f"Stored template metadata for content {content_uid}")
        except Exception as e:
            raise PloneWorkflowError(f"Failed to store template metadata: {str(e)}")

    async def _set_content_workflow_state(
        self, content_uid: str, state_id: str
    ) -> None:
        """Set content to specific workflow state."""
        try:
            await self.plone.set_workflow_state(content_uid, state_id)
            self.logger.debug(f"Set content {content_uid} to state {state_id}")
        except Exception as e:
            raise PloneWorkflowError(f"Failed to set workflow state: {str(e)}")

    async def _rollback_workflow_application(
        self, content_uid: str, backup_info: dict[str, Any]
    ) -> None:
        """Rollback workflow application using backup."""
        try:
            if backup_info.get("original_workflow_id"):
                await self._assign_workflow_to_content(
                    content_uid, backup_info["original_workflow_id"]
                )

            if backup_info.get("original_state"):
                await self._set_content_workflow_state(
                    content_uid, backup_info["original_state"]
                )

            # Remove template metadata
            await self._remove_template_metadata(content_uid)

            self.logger.info(f"Rolled back workflow application for {content_uid}")
        except Exception as e:
            self.logger.error(f"Rollback failed for {content_uid}: {e}")
            raise PloneWorkflowError(f"Rollback failed: {str(e)}")

    async def _validate_transition_permissions(
        self,
        content_uid: str,
        transition_id: str,
        user_id: str,
        template_metadata: dict[str, Any],
    ) -> None:
        """Validate user has permission to execute transition."""
        # Get user's roles
        user_roles = await self._get_user_roles_for_content(content_uid, user_id)

        # Check if user has required role for transition
        # This would involve loading the template and checking transition requirements
        # Implementation depends on how roles are stored and checked in Plone

        # For now, basic permission check via Plone
        can_execute = await self.plone.can_user_execute_transition(
            content_uid, transition_id, user_id
        )

        if not can_execute:
            raise PloneWorkflowError(
                f"User {user_id} does not have permission to execute transition {transition_id}"
            )

    async def _update_workflow_history(
        self,
        content_uid: str,
        transition_id: str,
        user_id: str,
        comments: Optional[str],
        transition_result: dict[str, Any],
    ) -> None:
        """Update workflow history with transition information."""
        # This would update the content's workflow history
        # Implementation depends on Plone's history tracking system
        pass

    async def _get_user_roles_for_content(
        self, content_uid: str, user_id: str
    ) -> list[str]:
        """Get user's roles for specific content."""
        try:
            roles = await self.plone.get_user_roles_for_content(content_uid, user_id)
            return roles
        except Exception as e:
            self.logger.error(
                f"Failed to get user roles for {content_uid}, user {user_id}: {e}"
            )
            return []

    async def _get_available_actions_for_user(
        self,
        template_metadata: dict[str, Any],
        current_state: str,
        user_roles: list[str],
    ) -> set[WorkflowAction]:
        """Get available actions for user in current state."""
        # This would load the template and check what actions the user can perform
        # based on their roles and the current state permissions
        available_actions = set()

        # Implementation would involve:
        # 1. Load template from metadata
        # 2. Find current state definition
        # 3. Check user roles against state permissions
        # 4. Return available actions

        return available_actions

    async def _get_available_transitions_for_user(
        self,
        content_uid: str,
        user_roles: list[str],
        available_transitions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter available transitions based on user permissions."""
        filtered_transitions = []

        for transition in available_transitions:
            # Check if user can execute this transition
            can_execute = await self.plone.can_user_execute_transition(
                content_uid, transition.get("id", ""), ""  # Would need actual user_id
            )

            if can_execute:
                filtered_transitions.append(transition)

        return filtered_transitions

    async def _remove_template_metadata(self, content_uid: str) -> None:
        """Remove template metadata from content."""
        try:
            await self.plone.update_content_metadata(
                content_uid, {"workflow_template_metadata": None}
            )
            self.logger.debug(f"Removed template metadata from content {content_uid}")
        except Exception as e:
            raise PloneWorkflowError(f"Failed to remove template metadata: {str(e)}")

    async def _restore_workflow_from_backup(
        self, content_uid: str, backup_info: dict[str, Any]
    ) -> None:
        """Restore workflow from backup information."""
        try:
            if backup_info.get("original_workflow_id"):
                await self._assign_workflow_to_content(
                    content_uid, backup_info["original_workflow_id"]
                )

            if backup_info.get("original_state"):
                await self._set_content_workflow_state(
                    content_uid, backup_info["original_state"]
                )

            self.logger.debug(f"Restored workflow from backup for {content_uid}")
        except Exception as e:
            raise PloneWorkflowError(
                f"Failed to restore workflow from backup: {str(e)}"
            )

    async def _cleanup_template_workflow(self, workflow_id: str) -> None:
        """Clean up template-specific workflow definition."""
        try:
            await self.plone.delete_workflow(workflow_id)
            self.logger.debug(f"Cleaned up template workflow {workflow_id}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup workflow {workflow_id}: {e}")
            # Don't raise here - cleanup failure shouldn't fail the main operation
