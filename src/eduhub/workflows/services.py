"""
Workflow Services for Template Application and Management.

This module provides high-level services for applying workflow templates
to content, managing permissions, and handling validation with comprehensive
audit logging and error recovery.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..plone_integration import PloneClient
from .models import EducationRole, WorkflowError, WorkflowTemplate
from .permissions import (
    RoleMappingError,
    ValidationResult,
    create_role_audit_log,
    map_eduhub_to_plone_roles,
    validate_template_roles,
)
from .plone_service import PloneWorkflowError, PloneWorkflowService

logger = logging.getLogger(__name__)


class WorkflowApplicationError(WorkflowError):
    """Raised when workflow application fails."""

    pass


class WorkflowValidationError(WorkflowError):
    """Raised when workflow validation fails."""

    pass


class WorkflowServicesManager:
    """
    High-level service manager for workflow template operations.

    Provides comprehensive workflow template application with validation,
    audit logging, and error recovery capabilities.
    """

    def __init__(self, plone_client: PloneClient):
        self.plone_service = PloneWorkflowService(plone_client)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def validate_and_apply_template(
        self,
        content_uid: str,
        template: WorkflowTemplate,
        role_assignments: dict[EducationRole, list[str]],
        user_id: str,
        force: bool = False,
        validate_roles: bool = True,
    ) -> dict[str, Any]:
        """
        Validate and apply a workflow template with comprehensive checks.

        This is the main service method that orchestrates:
        1. Template validation
        2. Role mapping validation
        3. Permission verification
        4. Template application
        5. Audit logging

        Args:
            content_uid: Target content item UID
            template: Workflow template to apply
            role_assignments: Mapping of roles to user/group IDs
            user_id: User performing the operation
            force: Whether to force application over existing workflow
            validate_roles: Whether to validate role mappings

        Returns:
            Comprehensive application result with validation details

        Raises:
            WorkflowValidationError: If validation fails
            WorkflowApplicationError: If application fails
        """
        self.logger.info(
            f"Starting template application: {template.id} to {content_uid} by {user_id}"
        )

        validation_results = {}
        application_result = None
        audit_log = None

        try:
            # Step 1: Validate template structure
            if validate_roles:
                template_validation = await self._validate_template_structure(template)
                validation_results["template"] = template_validation

                if not template_validation.is_valid:
                    raise WorkflowValidationError(
                        f"Template validation failed: {'; '.join(template_validation.errors)}"
                    )

            # Step 2: Validate role assignments
            role_validation = await self._validate_role_assignments(
                role_assignments, template
            )
            validation_results["roles"] = role_validation

            if not role_validation.is_valid:
                raise WorkflowValidationError(
                    f"Role validation failed: {'; '.join(role_validation.errors)}"
                )

            # Step 3: Check content permissions
            content_validation = await self._validate_content_permissions(
                content_uid, user_id
            )
            validation_results["content"] = content_validation

            if not content_validation.is_valid:
                raise WorkflowValidationError(
                    f"Content permission validation failed: {'; '.join(content_validation.errors)}"
                )

            # Step 4: Create audit log for the operation
            old_assignments = await self._get_current_role_assignments(content_uid)
            plone_assignments = map_eduhub_to_plone_roles(role_assignments)

            audit_log = create_role_audit_log(
                content_uid,
                old_assignments,
                plone_assignments,
                user_id,
                f"apply_template:{template.id}",
            )

            # Step 5: Apply the template
            application_result = await self.plone_service.apply_workflow_template(
                content_uid=content_uid,
                template=template,
                role_assignments=role_assignments,
                force=force,
            )

            # Step 6: Store audit log
            await self._store_audit_log(audit_log)

            # Step 7: Build comprehensive result
            result = {
                "success": True,
                "operation": "apply_template",
                "template_id": template.id,
                "content_uid": content_uid,
                "user_id": user_id,
                "validation_results": validation_results,
                "application_result": application_result,
                "audit_log": audit_log,
                "warnings": self._collect_warnings(validation_results),
                "applied_at": datetime.utcnow().isoformat(),
            }

            self.logger.info(
                f"Template application successful: {template.id} to {content_uid}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Template application failed: {e}")

            # Create failure audit log
            if audit_log:
                failure_audit = audit_log.copy()
                failure_audit["operation"] = f"failed_{audit_log['operation']}"
                failure_audit["error"] = str(e)
                await self._store_audit_log(failure_audit)

            # Re-raise with context
            if isinstance(e, (WorkflowValidationError, WorkflowApplicationError)):
                raise
            else:
                raise WorkflowApplicationError(f"Template application failed: {str(e)}")

    async def bulk_apply_template(
        self,
        template: WorkflowTemplate,
        content_assignments: list[dict[str, Any]],
        user_id: str,
        max_concurrent: int = 5,
    ) -> dict[str, Any]:
        """
        Apply a template to multiple content items concurrently.

        Args:
            template: Workflow template to apply
            content_assignments: List of dicts with content_uid and role_assignments
            user_id: User performing the operation
            max_concurrent: Maximum concurrent operations

        Returns:
            Bulk application results with success/failure details
        """
        self.logger.info(
            f"Starting bulk template application: {template.id} to {len(content_assignments)} items"
        )

        # Validate template once
        template_validation = await self._validate_template_structure(template)
        if not template_validation.is_valid:
            raise WorkflowValidationError(
                f"Template validation failed: {'; '.join(template_validation.errors)}"
            )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def apply_single(assignment: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                try:
                    result = await self.validate_and_apply_template(
                        content_uid=assignment["content_uid"],
                        template=template,
                        role_assignments=assignment["role_assignments"],
                        user_id=user_id,
                        force=assignment.get("force", False),
                        validate_roles=False,  # Already validated template
                    )
                    return {
                        "content_uid": assignment["content_uid"],
                        "success": True,
                        "result": result,
                    }
                except Exception as e:
                    return {
                        "content_uid": assignment["content_uid"],
                        "success": False,
                        "error": str(e),
                    }

        # Execute all applications concurrently
        tasks = [apply_single(assignment) for assignment in content_assignments]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        bulk_result = {
            "operation": "bulk_apply_template",
            "template_id": template.id,
            "user_id": user_id,
            "total_items": len(content_assignments),
            "successful_count": len(successful),
            "failed_count": len(failed) + len(exceptions),
            "successful_items": successful,
            "failed_items": failed,
            "exceptions": [str(e) for e in exceptions],
            "success_rate": (
                len(successful) / len(content_assignments) if content_assignments else 0
            ),
            "completed_at": datetime.utcnow().isoformat(),
        }

        self.logger.info(
            f"Bulk application completed: {len(successful)}/{len(content_assignments)} successful"
        )

        return bulk_result

    async def validate_template_for_content(
        self, template: WorkflowTemplate, content_uids: list[str], user_id: str
    ) -> dict[str, Any]:
        """
        Validate template applicability for multiple content items.

        Args:
            template: Template to validate
            content_uids: List of content UIDs to check
            user_id: User requesting validation

        Returns:
            Validation results for each content item
        """
        self.logger.info(
            f"Validating template {template.id} for {len(content_uids)} content items"
        )

        # Validate template structure
        template_validation = await self._validate_template_structure(template)

        # Validate each content item
        content_validations = {}
        for content_uid in content_uids:
            try:
                content_validation = await self._validate_content_permissions(
                    content_uid, user_id
                )
                content_validations[content_uid] = {
                    "valid": content_validation.is_valid,
                    "errors": content_validation.errors,
                    "warnings": content_validation.warnings,
                }
            except Exception as e:
                content_validations[content_uid] = {
                    "valid": False,
                    "errors": [str(e)],
                    "warnings": [],
                }

        return {
            "template_id": template.id,
            "template_validation": {
                "valid": template_validation.is_valid,
                "errors": template_validation.errors,
                "warnings": template_validation.warnings,
            },
            "content_validations": content_validations,
            "overall_valid": template_validation.is_valid
            and all(v["valid"] for v in content_validations.values()),
            "validated_at": datetime.utcnow().isoformat(),
        }

    # Private helper methods

    async def _validate_template_structure(
        self, template: WorkflowTemplate
    ) -> ValidationResult:
        """Validate template structure and role mappings."""
        try:
            return validate_template_roles(template)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                missing_roles=[],
                invalid_permissions=[],
                warnings=[],
                errors=[f"Template structure validation failed: {str(e)}"],
            )

    async def _validate_role_assignments(
        self,
        role_assignments: dict[EducationRole, list[str]],
        template: WorkflowTemplate,
    ) -> ValidationResult:
        """Validate that role assignments are compatible with template."""
        errors = []
        warnings = []

        # Check that all assigned roles are used in the template
        template_roles = set()
        for state in template.states:
            for permission in state.permissions:
                template_roles.add(permission.role)
        for transition in template.transitions:
            template_roles.add(transition.required_role)

        # Validate assigned roles
        for role, users in role_assignments.items():
            if role not in template_roles:
                warnings.append(
                    f"Role '{role.value}' assigned but not used in template"
                )

            if not users:
                errors.append(f"Role '{role.value}' has no assigned users")

        # Check for missing critical roles
        critical_roles = {
            r
            for r in template_roles
            if r in [EducationRole.ADMINISTRATOR, EducationRole.EDITOR]
        }
        for critical_role in critical_roles:
            if critical_role not in role_assignments:
                warnings.append(f"Critical role '{critical_role.value}' not assigned")

        return ValidationResult(
            is_valid=len(errors) == 0,
            missing_roles=[],
            invalid_permissions=[],
            warnings=warnings,
            errors=errors,
        )

    async def _validate_content_permissions(
        self, content_uid: str, user_id: str
    ) -> ValidationResult:
        """Validate that user has permission to modify content workflow."""
        try:
            # Check if content exists
            workflow_state = await self.plone_service.get_content_workflow_state(
                content_uid
            )

            # Check user permissions
            user_permissions = await self.plone_service.get_user_workflow_permissions(
                content_uid, user_id
            )

            errors = []
            warnings = []

            # Check if user can manage workflow
            if "manage_workflow" not in user_permissions.get("available_actions", []):
                errors.append(
                    f"User {user_id} lacks workflow management permissions for content {content_uid}"
                )

            # Check if content already has a template
            if workflow_state.get("template_metadata", {}).get("template_id"):
                warnings.append(
                    f"Content {content_uid} already has workflow template applied"
                )

            return ValidationResult(
                is_valid=len(errors) == 0,
                missing_roles=[],
                invalid_permissions=[],
                warnings=warnings,
                errors=errors,
            )

        except PloneWorkflowError as e:
            return ValidationResult(
                is_valid=False,
                missing_roles=[],
                invalid_permissions=[],
                warnings=[],
                errors=[f"Content validation failed: {str(e)}"],
            )

    async def _get_current_role_assignments(
        self, content_uid: str
    ) -> Optional[dict[str, list[str]]]:
        """Get current role assignments for content."""
        try:
            workflow_state = await self.plone_service.get_content_workflow_state(
                content_uid
            )
            template_metadata = workflow_state.get("template_metadata", {})
            return template_metadata.get("role_assignments")
        except Exception:
            return None

    async def _store_audit_log(self, audit_log: dict[str, Any]) -> None:
        """Store audit log entry (placeholder for actual implementation)."""
        # In a real implementation, this would store to a database or file
        self.logger.info(f"Audit log: {audit_log}")

    def _collect_warnings(
        self, validation_results: dict[str, ValidationResult]
    ) -> list[str]:
        """Collect all warnings from validation results."""
        warnings = []
        for validation_type, result in validation_results.items():
            for warning in result.warnings:
                warnings.append(f"{validation_type}: {warning}")
        return warnings


# Convenience functions for common operations
async def apply_template_to_content(
    plone_client: PloneClient,
    content_uid: str,
    template: WorkflowTemplate,
    role_assignments: dict[EducationRole, list[str]],
    user_id: str,
    force: bool = False,
) -> dict[str, Any]:
    """
    Convenience function to apply template to single content item.

    Args:
        plone_client: Plone client instance
        content_uid: Target content UID
        template: Workflow template
        role_assignments: Role assignments
        user_id: User performing operation
        force: Whether to force application

    Returns:
        Application result
    """
    service = WorkflowServicesManager(plone_client)
    return await service.validate_and_apply_template(
        content_uid, template, role_assignments, user_id, force
    )


async def bulk_apply_template_to_contents(
    plone_client: PloneClient,
    template: WorkflowTemplate,
    content_assignments: list[dict[str, Any]],
    user_id: str,
    max_concurrent: int = 5,
) -> dict[str, Any]:
    """
    Convenience function for bulk template application.

    Args:
        plone_client: Plone client instance
        template: Workflow template
        content_assignments: List of content/role assignment pairs
        user_id: User performing operation
        max_concurrent: Maximum concurrent operations

    Returns:
        Bulk application result
    """
    service = WorkflowServicesManager(plone_client)
    return await service.bulk_apply_template(
        template, content_assignments, user_id, max_concurrent
    )


async def validate_template_for_contents(
    plone_client: PloneClient,
    template: WorkflowTemplate,
    content_uids: list[str],
    user_id: str,
) -> dict[str, Any]:
    """
    Convenience function to validate template for multiple content items.

    Args:
        plone_client: Plone client instance
        template: Workflow template
        content_uids: List of content UIDs
        user_id: User requesting validation

    Returns:
        Validation results
    """
    service = WorkflowServicesManager(plone_client)
    return await service.validate_template_for_content(template, content_uids, user_id)
