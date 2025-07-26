"""
Service layer for schedule import operations.

Orchestrates parsing, validation, conflict detection, and Plone content creation
for bulk schedule imports with rollback capabilities.
"""

import time
from typing import List, Optional
from fastapi import UploadFile, HTTPException

from .models import ImportSummary, ScheduleRow, ValidationError, ConflictError
from .parser import ScheduleParser
from .conflict_detector import ConflictDetector
from ..plone_integration import PloneClient
from ..auth.models import User


class ScheduleImportService:
    """Orchestrates the complete schedule import process."""
    
    def __init__(self, plone_client: PloneClient):
        self.plone_client = plone_client
        self.parser = ScheduleParser()
        self.conflict_detector = ConflictDetector()
    
    async def process_import(
        self, 
        file: UploadFile, 
        preview_only: bool, 
        current_user: User
    ) -> ImportSummary:
        """
        Process a schedule import file with full validation and optional content creation.
        
        Args:
            file: Uploaded CSV or Excel file
            preview_only: If True, validate only without creating content
            current_user: Authenticated user performing the import
            
        Returns:
            ImportSummary with processing results
        """
        start_time = time.time()
        
        try:
            # Step 1: Parse the file
            rows, validation_errors = await self.parser.parse_file(file)
            
            # Step 2: Detect conflicts
            conflicts = self.conflict_detector.detect_conflicts(rows)
            
            # Step 3: Determine success status
            valid_rows = len(rows) - len(validation_errors)
            has_blocking_errors = len(validation_errors) > 0 or len(conflicts) > 0
            success = not has_blocking_errors
            
            # Step 4: Create content if not preview and no errors
            created_uids = None
            rollback_performed = False
            
            if not preview_only and success:
                try:
                    created_uids = await self._create_plone_content(rows, current_user)
                except Exception as e:
                    # If content creation fails, mark as unsuccessful
                    success = False
                    rollback_performed = True
                    validation_errors.append(ValidationError(
                        row_number=0,
                        field=None,
                        message=f"Content creation failed: {str(e)}",
                        value=None
                    ))
            
            # Step 5: Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Step 6: Build summary
            return ImportSummary(
                filename=file.filename or "unknown",
                total_rows=len(rows),
                valid_rows=valid_rows,
                validation_errors=validation_errors,
                conflicts=conflicts,
                created_uids=created_uids,
                preview_only=preview_only,
                processing_time_ms=processing_time_ms,
                success=success,
                rollback_performed=rollback_performed
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions (file too large, unsupported type, etc.)
            raise
        except Exception as e:
            # Handle unexpected errors
            processing_time_ms = int((time.time() - start_time) * 1000)
            raise HTTPException(
                status_code=500,
                detail=f"Import processing failed: {str(e)}"
            )
    
    async def _create_plone_content(self, rows: List[ScheduleRow], user: User) -> List[str]:
        """
        Create Plone content for valid schedule rows.
        
        This method will be enhanced when we extend PloneClient with bulk operations.
        For now, it creates individual events and handles rollback on failure.
        
        Args:
            rows: Valid schedule rows to create content for
            user: User context for content creation
            
        Returns:
            List of created content UIDs
        """
        created_uids = []
        
        try:
            for row in rows:
                # Convert ScheduleRow to Plone event data
                event_data = self._schedule_row_to_event_data(row)
                
                # Create the event in Plone
                # Note: This will need to be updated when we implement bulk creation
                uid = await self._create_single_event(event_data, user)
                created_uids.append(uid)
            
            return created_uids
            
        except Exception as e:
            # If any creation fails, attempt to clean up created content
            if created_uids:
                await self._rollback_created_content(created_uids, user)
            raise e
    
    def _schedule_row_to_event_data(self, row: ScheduleRow) -> dict:
        """
        Convert a ScheduleRow to Plone event creation data.
        
        Maps CSV fields to Plone event fields according to our content model.
        """
        # Parse start time
        start_datetime = f"{row.date}T{row.time}:00"
        
        # Calculate end time based on duration
        duration_minutes = row.duration or 60
        try:
            from datetime import datetime, timedelta
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            end_datetime = end_dt.isoformat()
        except ValueError:
            # Fallback to 1-hour duration
            end_datetime = f"{row.date}T{int(row.time[:2]) + 1:02d}:{row.time[3:]}:00"
        
        return {
            "title": f"{row.program} - {row.instructor}",
            "description": row.description or f"Program: {row.program}",
            "start": start_datetime,
            "end": end_datetime,
            "location": row.room,
            "attendees": [row.instructor],
            # Custom fields for educational content
            "program_name": row.program,
            "instructor_name": row.instructor,
            "room_location": row.room,
            "duration_minutes": duration_minutes
        }
    
    async def _create_single_event(self, event_data: dict, user: User) -> str:
        """
        Create a single event in Plone.
        
        This is a placeholder that will be replaced with actual PloneClient integration.
        """
        # TODO: Implement actual Plone event creation
        # For now, simulate the creation and return a mock UID
        import uuid
        mock_uid = str(uuid.uuid4())
        
        # In real implementation, this would be:
        # uid = await self.plone_client.create_event(event_data, user_context=user)
        
        return mock_uid
    
    async def _rollback_created_content(self, uids: List[str], user: User) -> None:
        """
        Rollback (delete) content that was created during a failed import.
        
        This ensures atomicity - either all content is created or none is.
        """
        # TODO: Implement actual Plone content deletion
        # For now, this is a placeholder
        
        # In real implementation, this would be:
        # for uid in uids:
        #     await self.plone_client.delete_content(uid, user_context=user)
        
        pass 