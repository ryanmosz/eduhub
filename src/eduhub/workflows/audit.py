"""
Audit logging system for workflow template operations.

Provides comprehensive logging and tracking of workflow template applications,
role assignments, permission changes, and user actions for compliance and debugging.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""

    timestamp: str
    operation: str
    user_id: str
    content_uid: str
    template_id: Optional[str] = None
    success: bool = True
    changes: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class WorkflowAuditLogger:
    """
    Comprehensive audit logging system for workflow operations.

    Provides structured logging with JSON format, file rotation,
    and query capabilities for compliance and debugging.
    """

    def __init__(self, log_directory: str = "logs/workflow_audit"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Setup file logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._setup_file_handler()

    def _setup_file_handler(self) -> None:
        """Setup rotating file handler for audit logs."""
        from logging.handlers import RotatingFileHandler

        audit_file = self.log_directory / "workflow_audit.log"

        # Create rotating file handler (10MB files, keep 10 files)
        handler = RotatingFileHandler(
            audit_file, maxBytes=10 * 1024 * 1024, backupCount=10  # 10MB
        )

        # JSON formatter
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger

    def log_template_application(
        self,
        user_id: str,
        content_uid: str,
        template_id: str,
        role_changes: list[dict[str, Any]],
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Log workflow template application.

        Args:
            user_id: User performing the operation
            content_uid: Target content UID
            template_id: Applied template ID
            role_changes: List of role assignment changes
            success: Whether operation succeeded
            error: Error message if failed
            metadata: Additional metadata

        Returns:
            Audit entry ID for reference
        """
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="apply_template",
            user_id=user_id,
            content_uid=content_uid,
            template_id=template_id,
            success=success,
            changes=role_changes,
            metadata=metadata or {},
            error=error,
        )

        return self._write_audit_entry(entry)

    def log_template_removal(
        self,
        user_id: str,
        content_uid: str,
        template_id: str,
        restored_backup: bool,
        success: bool = True,
        error: Optional[str] = None,
    ) -> str:
        """Log workflow template removal."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="remove_template",
            user_id=user_id,
            content_uid=content_uid,
            template_id=template_id,
            success=success,
            metadata={"restored_backup": restored_backup},
            error=error,
        )

        return self._write_audit_entry(entry)

    def log_workflow_transition(
        self,
        user_id: str,
        content_uid: str,
        transition_id: str,
        from_state: str,
        to_state: str,
        comments: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> str:
        """Log workflow state transition."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="execute_transition",
            user_id=user_id,
            content_uid=content_uid,
            success=success,
            changes=[
                {
                    "type": "state_change",
                    "transition_id": transition_id,
                    "from_state": from_state,
                    "to_state": to_state,
                    "comments": comments,
                }
            ],
            error=error,
        )

        return self._write_audit_entry(entry)

    def log_role_assignment_change(
        self,
        user_id: str,
        content_uid: str,
        role_changes: list[dict[str, Any]],
        operation: str = "modify_roles",
        success: bool = True,
        error: Optional[str] = None,
    ) -> str:
        """Log role assignment modifications."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation=operation,
            user_id=user_id,
            content_uid=content_uid,
            success=success,
            changes=role_changes,
            error=error,
        )

        return self._write_audit_entry(entry)

    def log_bulk_operation(
        self,
        user_id: str,
        operation: str,
        template_id: Optional[str],
        total_items: int,
        successful_items: int,
        failed_items: int,
        duration_seconds: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Log bulk operation summary."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation=f"bulk_{operation}",
            user_id=user_id,
            content_uid="BULK",  # Special marker for bulk operations
            template_id=template_id,
            success=failed_items == 0,
            metadata={
                "total_items": total_items,
                "successful_items": successful_items,
                "failed_items": failed_items,
                "duration_seconds": duration_seconds,
                "success_rate": (
                    successful_items / total_items if total_items > 0 else 0
                ),
                **(metadata or {}),
            },
        )

        return self._write_audit_entry(entry)

    def log_permission_check(
        self,
        user_id: str,
        content_uid: str,
        requested_action: str,
        granted: bool,
        user_roles: list[str],
        required_role: Optional[str] = None,
    ) -> str:
        """Log permission check results."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="permission_check",
            user_id=user_id,
            content_uid=content_uid,
            success=granted,
            metadata={
                "requested_action": requested_action,
                "user_roles": user_roles,
                "required_role": required_role,
                "granted": granted,
            },
        )

        return self._write_audit_entry(entry)

    def log_validation_error(
        self,
        user_id: str,
        operation: str,
        content_uid: Optional[str],
        template_id: Optional[str],
        validation_errors: list[str],
        warnings: list[str] = None,
    ) -> str:
        """Log validation failures."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation=f"validation_{operation}",
            user_id=user_id,
            content_uid=content_uid or "UNKNOWN",
            template_id=template_id,
            success=False,
            error="; ".join(validation_errors),
            metadata={
                "validation_errors": validation_errors,
                "warnings": warnings or [],
            },
        )

        return self._write_audit_entry(entry)

    def _write_audit_entry(self, entry: AuditEntry) -> str:
        """Write audit entry to log file."""
        try:
            # Convert to JSON
            entry_dict = asdict(entry)
            entry_json = json.dumps(entry_dict, separators=(",", ":"))

            # Log to file
            self.logger.info(entry_json)

            # Return entry ID (timestamp + hash)
            import hashlib

            entry_id = (
                f"{entry.timestamp}_{hashlib.md5(entry_json.encode()).hexdigest()[:8]}"
            )

            return entry_id

        except Exception as e:
            # Fallback logging
            logger.error(f"Failed to write audit entry: {e}")
            logger.error(f"Entry data: {entry}")
            return "FAILED"

    def query_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        content_uid: Optional[str] = None,
        template_id: Optional[str] = None,
        operation: Optional[str] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query audit logs with filtering.

        Args:
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            user_id: Filter by user ID
            content_uid: Filter by content UID
            template_id: Filter by template ID
            operation: Filter by operation type
            success_only: Filter by success status
            limit: Maximum number of entries to return

        Returns:
            List of matching audit entries
        """
        results = []
        entries_processed = 0

        try:
            # Read current log file
            current_log = self.log_directory / "workflow_audit.log"
            if current_log.exists():
                results.extend(
                    self._parse_log_file(
                        current_log,
                        {
                            "start_date": start_date,
                            "end_date": end_date,
                            "user_id": user_id,
                            "content_uid": content_uid,
                            "template_id": template_id,
                            "operation": operation,
                            "success_only": success_only,
                        },
                        limit,
                    )
                )

            # Read rotated log files if needed
            if len(results) < limit:
                for i in range(1, 11):  # Check up to 10 rotated files
                    rotated_log = self.log_directory / f"workflow_audit.log.{i}"
                    if rotated_log.exists():
                        additional_results = self._parse_log_file(
                            rotated_log,
                            {
                                "start_date": start_date,
                                "end_date": end_date,
                                "user_id": user_id,
                                "content_uid": content_uid,
                                "template_id": template_id,
                                "operation": operation,
                                "success_only": success_only,
                            },
                            limit - len(results),
                        )
                        results.extend(additional_results)

                        if len(results) >= limit:
                            break

        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")

        # Sort by timestamp (newest first) and apply limit
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]

    def _parse_log_file(
        self, log_file: Path, filters: dict[str, Any], limit: int
    ) -> list[dict[str, Any]]:
        """Parse log file and apply filters."""
        results = []

        try:
            with open(log_file) as f:
                for line in f:
                    if len(results) >= limit:
                        break

                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if self._entry_matches_filters(entry, filters):
                            results.append(entry)

                    except json.JSONDecodeError:
                        continue  # Skip malformed lines

        except Exception as e:
            logger.error(f"Failed to parse log file {log_file}: {e}")

        return results

    def _entry_matches_filters(
        self, entry: dict[str, Any], filters: dict[str, Any]
    ) -> bool:
        """Check if entry matches filter criteria."""
        # Date filters
        if filters.get("start_date"):
            entry_date = datetime.fromisoformat(
                entry["timestamp"].replace("Z", "+00:00")
            )
            if entry_date < filters["start_date"]:
                return False

        if filters.get("end_date"):
            entry_date = datetime.fromisoformat(
                entry["timestamp"].replace("Z", "+00:00")
            )
            if entry_date > filters["end_date"]:
                return False

        # String filters
        for field in ["user_id", "content_uid", "template_id", "operation"]:
            filter_value = filters.get(field)
            if filter_value and entry.get(field) != filter_value:
                return False

        # Boolean filters
        if filters.get("success_only") is not None:
            if entry.get("success") != filters["success_only"]:
                return False

        return True

    def get_audit_summary(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> dict[str, Any]:
        """Get audit log summary statistics."""
        entries = self.query_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Large limit for summary
        )

        # Calculate statistics
        total_operations = len(entries)
        successful_operations = sum(1 for e in entries if e.get("success", True))
        failed_operations = total_operations - successful_operations

        operations_by_type = {}
        users_active = set()
        templates_used = set()

        for entry in entries:
            operation = entry.get("operation", "unknown")
            operations_by_type[operation] = operations_by_type.get(operation, 0) + 1

            if entry.get("user_id"):
                users_active.add(entry["user_id"])

            if entry.get("template_id"):
                templates_used.add(entry["template_id"])

        return {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": (
                successful_operations / total_operations if total_operations > 0 else 0
            ),
            "operations_by_type": operations_by_type,
            "unique_users": len(users_active),
            "unique_templates": len(templates_used),
            "most_common_operations": sorted(
                operations_by_type.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }


# Global audit logger instance
_audit_logger: Optional[WorkflowAuditLogger] = None


def get_audit_logger() -> WorkflowAuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = WorkflowAuditLogger()
    return _audit_logger


# Convenience functions for common audit operations
def audit_template_application(
    user_id: str,
    content_uid: str,
    template_id: str,
    role_changes: list[dict[str, Any]],
    success: bool = True,
    error: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Log template application audit entry."""
    return get_audit_logger().log_template_application(
        user_id, content_uid, template_id, role_changes, success, error, metadata
    )


def audit_workflow_transition(
    user_id: str,
    content_uid: str,
    transition_id: str,
    from_state: str,
    to_state: str,
    comments: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> str:
    """Log workflow transition audit entry."""
    return get_audit_logger().log_workflow_transition(
        user_id,
        content_uid,
        transition_id,
        from_state,
        to_state,
        comments,
        success,
        error,
    )


def audit_permission_check(
    user_id: str,
    content_uid: str,
    requested_action: str,
    granted: bool,
    user_roles: list[str],
    required_role: Optional[str] = None,
) -> str:
    """Log permission check audit entry."""
    return get_audit_logger().log_permission_check(
        user_id, content_uid, requested_action, granted, user_roles, required_role
    )


def audit_bulk_operation(
    user_id: str,
    operation: str,
    template_id: Optional[str],
    total_items: int,
    successful_items: int,
    failed_items: int,
    duration_seconds: float,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Log bulk operation audit entry."""
    return get_audit_logger().log_bulk_operation(
        user_id,
        operation,
        template_id,
        total_items,
        successful_items,
        failed_items,
        duration_seconds,
        metadata,
    )


def query_workflow_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    content_uid: Optional[str] = None,
    template_id: Optional[str] = None,
    operation: Optional[str] = None,
    success_only: Optional[bool] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Query audit logs with filtering."""
    return get_audit_logger().query_audit_logs(
        start_date,
        end_date,
        user_id,
        content_uid,
        template_id,
        operation,
        success_only,
        limit,
    )


def get_workflow_audit_summary(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> dict[str, Any]:
    """Get audit summary statistics."""
    return get_audit_logger().get_audit_summary(start_date, end_date)
