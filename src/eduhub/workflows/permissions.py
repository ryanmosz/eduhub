"""
Role & Permission Mapping Engine for Workflow Templates.

This module provides utilities for translating EduHub educational roles
to Plone CMS roles, validating role mappings, and managing permission
consistency across both systems.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import EducationRole, WorkflowAction, WorkflowTemplate

logger = logging.getLogger(__name__)


class RoleMappingError(Exception):
    """Raised when role mapping validation fails."""

    pass


class PermissionMappingError(Exception):
    """Raised when permission mapping fails."""

    pass


@dataclass
class RoleMapping:
    """Represents a mapping between EduHub and Plone roles."""

    eduhub_role: EducationRole
    plone_role: str
    description: str
    permissions: set[WorkflowAction]
    is_privileged: bool = False


@dataclass
class ValidationResult:
    """Result of role/permission validation."""

    is_valid: bool
    missing_roles: list[str]
    invalid_permissions: list[str]
    warnings: list[str]
    errors: list[str]


# Core role mappings between EduHub and Plone
ROLE_MAPPINGS: dict[EducationRole, RoleMapping] = {
    EducationRole.AUTHOR: RoleMapping(
        eduhub_role=EducationRole.AUTHOR,
        plone_role="Author",
        description="Content creators who draft and submit materials for review",
        permissions={WorkflowAction.VIEW, WorkflowAction.EDIT, WorkflowAction.SUBMIT},
        is_privileged=False,
    ),
    EducationRole.PEER_REVIEWER: RoleMapping(
        eduhub_role=EducationRole.PEER_REVIEWER,
        plone_role="Reviewer",
        description="Subject matter experts who review content for accuracy and quality",
        permissions={
            WorkflowAction.VIEW,
            WorkflowAction.REVIEW,
            WorkflowAction.APPROVE,
            WorkflowAction.REJECT,
        },
        is_privileged=True,
    ),
    EducationRole.EDITOR: RoleMapping(
        eduhub_role=EducationRole.EDITOR,
        plone_role="Editor",
        description="Editorial staff who manage content workflow and quality",
        permissions={
            WorkflowAction.VIEW,
            WorkflowAction.EDIT,
            WorkflowAction.REVIEW,
            WorkflowAction.APPROVE,
            WorkflowAction.PUBLISH,
            WorkflowAction.REJECT,
            WorkflowAction.RETRACT,
        },
        is_privileged=True,
    ),
    EducationRole.SUBJECT_EXPERT: RoleMapping(
        eduhub_role=EducationRole.SUBJECT_EXPERT,
        plone_role="Subject Expert",
        description="Domain specialists who provide technical validation",
        permissions={
            WorkflowAction.VIEW,
            WorkflowAction.REVIEW,
            WorkflowAction.APPROVE,
            WorkflowAction.REJECT,
        },
        is_privileged=True,
    ),
    EducationRole.PUBLISHER: RoleMapping(
        eduhub_role=EducationRole.PUBLISHER,
        plone_role="Publisher",
        description="Publishing staff who control final content release",
        permissions={
            WorkflowAction.VIEW,
            WorkflowAction.PUBLISH,
            WorkflowAction.RETRACT,
        },
        is_privileged=True,
    ),
    EducationRole.ADMINISTRATOR: RoleMapping(
        eduhub_role=EducationRole.ADMINISTRATOR,
        plone_role="Manager",
        description="System administrators with full workflow control",
        permissions=set(WorkflowAction),  # All permissions
        is_privileged=True,
    ),
    EducationRole.VIEWER: RoleMapping(
        eduhub_role=EducationRole.VIEWER,
        plone_role="Reader",
        description="Users with read-only access to content",
        permissions={WorkflowAction.VIEW},
        is_privileged=False,
    ),
}

# Reverse mapping for lookups
PLONE_TO_EDUHUB_ROLES: dict[str, EducationRole] = {
    mapping.plone_role: mapping.eduhub_role for mapping in ROLE_MAPPINGS.values()
}

# Action to Plone permission mappings
ACTION_TO_PLONE_PERMISSION: dict[WorkflowAction, str] = {
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


class RolePermissionMapper:
    """Central utility for role and permission mapping operations."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_plone_role(self, eduhub_role: EducationRole) -> str:
        """
        Convert EduHub role to Plone role name.

        Args:
            eduhub_role: EduHub role to convert

        Returns:
            Corresponding Plone role name

        Raises:
            RoleMappingError: If role mapping is not found
        """
        if eduhub_role not in ROLE_MAPPINGS:
            raise RoleMappingError(
                f"No Plone role mapping found for EduHub role: {eduhub_role}"
            )

        return ROLE_MAPPINGS[eduhub_role].plone_role

    def get_eduhub_role(self, plone_role: str) -> EducationRole:
        """
        Convert Plone role to EduHub role.

        Args:
            plone_role: Plone role name to convert

        Returns:
            Corresponding EduHub role

        Raises:
            RoleMappingError: If role mapping is not found
        """
        if plone_role not in PLONE_TO_EDUHUB_ROLES:
            raise RoleMappingError(
                f"No EduHub role mapping found for Plone role: {plone_role}"
            )

        return PLONE_TO_EDUHUB_ROLES[plone_role]

    def get_role_permissions(self, eduhub_role: EducationRole) -> set[WorkflowAction]:
        """
        Get default permissions for an EduHub role.

        Args:
            eduhub_role: Role to get permissions for

        Returns:
            Set of workflow actions this role can perform
        """
        if eduhub_role not in ROLE_MAPPINGS:
            return set()

        return ROLE_MAPPINGS[eduhub_role].permissions.copy()

    def get_plone_permission(self, action: WorkflowAction) -> str:
        """
        Convert workflow action to Plone permission name.

        Args:
            action: Workflow action to convert

        Returns:
            Corresponding Plone permission name

        Raises:
            PermissionMappingError: If action mapping is not found
        """
        if action not in ACTION_TO_PLONE_PERMISSION:
            raise PermissionMappingError(
                f"No Plone permission mapping found for action: {action}"
            )

        return ACTION_TO_PLONE_PERMISSION[action]

    def validate_template_roles(self, template: WorkflowTemplate) -> ValidationResult:
        """
        Validate that all roles used in a template have valid mappings.

        Args:
            template: Workflow template to validate

        Returns:
            ValidationResult with validation details
        """
        missing_roles = []
        invalid_permissions = []
        warnings = []
        errors = []

        # Collect all roles used in the template
        used_roles = set()

        # Roles from state permissions
        for state in template.states:
            for permission in state.permissions:
                used_roles.add(permission.role)

        # Roles from transition requirements
        for transition in template.transitions:
            used_roles.add(transition.required_role)

        # Roles from default permissions
        for role in template.default_permissions.keys():
            used_roles.add(role)

        # Validate each role
        for role in used_roles:
            if role not in ROLE_MAPPINGS:
                missing_roles.append(role.value)
                errors.append(f"Role '{role.value}' has no Plone mapping")
            else:
                # Check if role permissions are valid
                role_mapping = ROLE_MAPPINGS[role]
                for permission in role_mapping.permissions:
                    if permission not in ACTION_TO_PLONE_PERMISSION:
                        invalid_permissions.append(f"{role.value}:{permission.value}")
                        errors.append(
                            f"Permission '{permission.value}' for role '{role.value}' has no Plone mapping"
                        )

        # Check for potential security issues
        for role in used_roles:
            if role in ROLE_MAPPINGS:
                mapping = ROLE_MAPPINGS[role]
                if mapping.is_privileged:
                    warnings.append(
                        f"Template uses privileged role '{role.value}' - ensure proper access control"
                    )

        is_valid = len(missing_roles) == 0 and len(invalid_permissions) == 0

        return ValidationResult(
            is_valid=is_valid,
            missing_roles=missing_roles,
            invalid_permissions=invalid_permissions,
            warnings=warnings,
            errors=errors,
        )

    def build_plone_role_assignments(
        self, eduhub_assignments: dict[EducationRole, list[str]]
    ) -> dict[str, list[str]]:
        """
        Convert EduHub role assignments to Plone format.

        Args:
            eduhub_assignments: Mapping of EduHub roles to user/group IDs

        Returns:
            Mapping of Plone roles to user/group IDs

        Raises:
            RoleMappingError: If any role mapping fails
        """
        plone_assignments = {}

        for eduhub_role, user_ids in eduhub_assignments.items():
            try:
                plone_role = self.get_plone_role(eduhub_role)
                plone_assignments[plone_role] = user_ids.copy()
            except RoleMappingError as e:
                self.logger.error(f"Failed to map role {eduhub_role}: {e}")
                raise

        return plone_assignments

    def build_permission_matrix(
        self, template: WorkflowTemplate
    ) -> dict[str, dict[str, set[str]]]:
        """
        Build a complete permission matrix for a workflow template.

        Returns a nested dictionary: state_id -> plone_permission -> [plone_roles]

        Args:
            template: Workflow template to analyze

        Returns:
            Permission matrix mapping states to permissions to roles
        """
        matrix = {}

        for state in template.states:
            state_permissions = {}

            # Process state-specific permissions
            for permission in state.permissions:
                plone_role = self.get_plone_role(permission.role)

                for action in permission.actions:
                    plone_permission = self.get_plone_permission(action)

                    if plone_permission not in state_permissions:
                        state_permissions[plone_permission] = set()

                    state_permissions[plone_permission].add(plone_role)

            # Add default permissions
            for eduhub_role, actions in template.default_permissions.items():
                plone_role = self.get_plone_role(eduhub_role)

                for action in actions:
                    plone_permission = self.get_plone_permission(action)

                    if plone_permission not in state_permissions:
                        state_permissions[plone_permission] = set()

                    state_permissions[plone_permission].add(plone_role)

            # Convert sets to lists for JSON serialization
            matrix[state.id] = {
                perm: list(roles) for perm, roles in state_permissions.items()
            }

        return matrix

    def get_role_hierarchy(self) -> dict[str, int]:
        """
        Get role hierarchy levels for privilege comparison.

        Returns:
            Mapping of Plone roles to privilege levels (higher = more privileged)
        """
        hierarchy = {}

        for eduhub_role, mapping in ROLE_MAPPINGS.items():
            if mapping.is_privileged:
                # Assign privilege levels based on permissions
                level = len(mapping.permissions)
                if eduhub_role == EducationRole.ADMINISTRATOR:
                    level = 1000  # Highest privilege
                elif eduhub_role == EducationRole.EDITOR:
                    level = 900
                elif eduhub_role == EducationRole.PUBLISHER:
                    level = 800
                elif eduhub_role == EducationRole.PEER_REVIEWER:
                    level = 700
                elif eduhub_role == EducationRole.SUBJECT_EXPERT:
                    level = 600
                else:
                    level = 500
            else:
                level = 100  # Low privilege

            hierarchy[mapping.plone_role] = level

        return hierarchy

    def check_role_compatibility(
        self, user_roles: list[str], required_role: EducationRole
    ) -> bool:
        """
        Check if user's Plone roles are compatible with required EduHub role.

        Args:
            user_roles: List of Plone roles assigned to user
            required_role: Required EduHub role for operation

        Returns:
            True if user has sufficient privileges
        """
        try:
            required_plone_role = self.get_plone_role(required_role)
            hierarchy = self.get_role_hierarchy()
            required_level = hierarchy.get(required_plone_role, 0)

            # Check if user has the exact role or higher privilege
            for user_role in user_roles:
                user_level = hierarchy.get(user_role, 0)
                if user_level >= required_level:
                    return True

            return False

        except RoleMappingError:
            self.logger.warning(
                f"Unable to check compatibility for unknown role: {required_role}"
            )
            return False

    def audit_role_changes(
        self,
        content_uid: str,
        old_assignments: Optional[dict[str, list[str]]],
        new_assignments: dict[str, list[str]],
        user_id: str,
        operation: str,
    ) -> dict[str, Any]:
        """
        Create audit log entry for role assignment changes.

        Args:
            content_uid: Content item being modified
            old_assignments: Previous role assignments (Plone format)
            new_assignments: New role assignments (Plone format)
            user_id: User making the changes
            operation: Operation being performed

        Returns:
            Audit log entry
        """
        changes = []

        if old_assignments:
            # Find additions and modifications
            for role, users in new_assignments.items():
                old_users = set(old_assignments.get(role, []))
                new_users = set(users)

                added_users = new_users - old_users
                removed_users = old_users - new_users

                if added_users:
                    changes.append(
                        {"type": "role_added", "role": role, "users": list(added_users)}
                    )

                if removed_users:
                    changes.append(
                        {
                            "type": "role_removed",
                            "role": role,
                            "users": list(removed_users),
                        }
                    )

            # Find role removals
            for role, users in old_assignments.items():
                if role not in new_assignments:
                    changes.append(
                        {"type": "role_removed", "role": role, "users": users}
                    )
        else:
            # All assignments are new
            for role, users in new_assignments.items():
                changes.append({"type": "role_added", "role": role, "users": users})

        from datetime import datetime

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "content_uid": content_uid,
            "user_id": user_id,
            "operation": operation,
            "changes": changes,
            "total_changes": len(changes),
        }


# Global mapper instance
role_mapper = RolePermissionMapper()


# Convenience functions for common operations
def validate_template_roles(template: WorkflowTemplate) -> ValidationResult:
    """Validate that all roles in template have valid mappings."""
    return role_mapper.validate_template_roles(template)


def map_eduhub_to_plone_roles(
    eduhub_assignments: dict[EducationRole, list[str]]
) -> dict[str, list[str]]:
    """Convert EduHub role assignments to Plone format."""
    return role_mapper.build_plone_role_assignments(eduhub_assignments)


def get_plone_role_for_eduhub(eduhub_role: EducationRole) -> str:
    """Get Plone role name for EduHub role."""
    return role_mapper.get_plone_role(eduhub_role)


def get_eduhub_role_for_plone(plone_role: str) -> EducationRole:
    """Get EduHub role for Plone role name."""
    return role_mapper.get_eduhub_role(plone_role)


def check_user_permission(user_roles: list[str], required_role: EducationRole) -> bool:
    """Check if user has sufficient privileges for required role."""
    return role_mapper.check_role_compatibility(user_roles, required_role)


def build_permission_matrix(
    template: WorkflowTemplate,
) -> dict[str, dict[str, set[str]]]:
    """Build complete permission matrix for template."""
    return role_mapper.build_permission_matrix(template)


def create_role_audit_log(
    content_uid: str,
    old_assignments: Optional[dict[str, list[str]]],
    new_assignments: dict[str, list[str]],
    user_id: str,
    operation: str,
) -> dict[str, Any]:
    """Create audit log for role changes."""
    return role_mapper.audit_role_changes(
        content_uid, old_assignments, new_assignments, user_id, operation
    )
