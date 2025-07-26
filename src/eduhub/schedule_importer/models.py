"""
Pydantic models for schedule import functionality.

Defines data structures for schedule rows, validation errors,
import summaries, and API responses.
"""

from datetime import datetime, time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class ScheduleRow(BaseModel):
    """Represents a single schedule entry from CSV/Excel."""
    
    program: str = Field(..., description="Program or course name")
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    time: str = Field(..., description="Time in HH:MM format")
    instructor: str = Field(..., description="Instructor name")
    room: str = Field(..., description="Room/location identifier")
    duration: Optional[int] = Field(60, description="Duration in minutes")
    description: Optional[str] = Field(None, description="Additional description")
    
    # Validation
    @validator('date')
    def validate_date_format(cls, v):
        """Ensure date follows ISO format."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('time')
    def validate_time_format(cls, v):
        """Ensure time follows HH:MM format."""
        if not re.match(r'^\d{2}:\d{2}$', v):
            raise ValueError('Time must be in HH:MM format')
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        """Ensure duration is reasonable."""
        if v is not None and (v < 15 or v > 480):  # 15 min to 8 hours
            raise ValueError('Duration must be between 15 and 480 minutes')
        return v


class ValidationError(BaseModel):
    """Represents a validation error for a specific row."""
    
    row_number: int = Field(..., description="1-based row number in the file")
    field: Optional[str] = Field(None, description="Field name that failed validation")
    message: str = Field(..., description="Human-readable error message")
    value: Optional[str] = Field(None, description="The invalid value")


class ConflictError(BaseModel):
    """Represents a scheduling conflict between rows."""
    
    row_numbers: List[int] = Field(..., description="Row numbers involved in conflict")
    conflict_type: str = Field(..., description="Type of conflict (room, instructor, etc.)")
    message: str = Field(..., description="Human-readable conflict description")


class ImportSummary(BaseModel):
    """Summary of schedule import operation."""
    
    filename: str = Field(..., description="Original filename")
    total_rows: int = Field(..., description="Total rows processed")
    valid_rows: int = Field(..., description="Number of valid rows")
    validation_errors: List[ValidationError] = Field(default_factory=list)
    conflicts: List[ConflictError] = Field(default_factory=list)
    created_uids: Optional[List[str]] = Field(None, description="UIDs of created Plone content")
    preview_only: bool = Field(..., description="Whether this was a preview operation")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    success: bool = Field(..., description="Whether the operation was successful")
    rollback_performed: bool = Field(False, description="Whether rollback was necessary")


class ErrorResponse(BaseModel):
    """Standard error response for import operations."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ImportHistoryEntry(BaseModel):
    """Represents a historical import operation."""
    
    id: int = Field(..., description="Unique import ID")
    user_id: str = Field(..., description="User who performed the import")
    filename: str = Field(..., description="Original filename")
    timestamp: datetime = Field(..., description="When the import was performed")
    total_rows: int = Field(..., description="Total rows in the file")
    success: bool = Field(..., description="Whether the import succeeded")
    duration_ms: int = Field(..., description="Processing duration in milliseconds")
    created_count: int = Field(..., description="Number of content items created") 