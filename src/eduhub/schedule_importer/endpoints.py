"""
FastAPI endpoints for CSV/Excel schedule importing.

Provides secure file upload and processing endpoints for bulk
schedule imports with preview and validation capabilities.
"""

import os
from typing import Annotated, Optional, Union
from unittest.mock import AsyncMock

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from ..auth.dependencies import get_current_user
from ..auth.models import User
from ..plone_integration import PloneClient
from .models import ErrorResponse, ImportSummary
from .services import ScheduleImportService

router = APIRouter(prefix="/import", tags=["Schedule Import"])


def get_schedule_import_service() -> ScheduleImportService:
    """Get configured schedule import service with dependency injection."""
    # Check for mock mode
    if os.getenv("PLONE_MOCK_MODE", "false").lower() == "true":
        # Create a mock PloneClient for testing without real Plone
        mock_client = AsyncMock(spec=PloneClient)
        mock_client.create_content.return_value = {
            "UID": f"mock-uid-{hash(str(id(mock_client))) % 10000:04d}"
        }
        mock_client.delete_content.return_value = True
        return ScheduleImportService(mock_client)
    else:
        # Use real Plone client
        plone_client = PloneClient()
        return ScheduleImportService(plone_client)


@router.post("/schedule", response_model=Union[ImportSummary, ErrorResponse])
async def import_schedule(
    file: UploadFile = File(
        ..., description="CSV or Excel file containing schedule data"
    ),
    preview_only: bool = Form(
        False, description="If true, validate and preview without creating content"
    ),
    current_user=Depends(get_current_user),
    import_service: ScheduleImportService = Depends(get_schedule_import_service),
):
    """
    Upload and process a schedule file (CSV or Excel).

    **Preview Mode** (`preview_only=true`):
    - Validates file format and data
    - Returns summary of rows that would be imported
    - Shows validation errors without creating content

    **Import Mode** (`preview_only=false`):
    - Validates and creates Plone content
    - Returns summary with created content UIDs
    - Rolls back on any errors

    **Required permissions**: User must be authenticated
    **File size limit**: 10MB maximum
    **Supported formats**: .csv, .xlsx

    **Example CSV format:**
    ```
    program,date,time,instructor,room,duration,description
    Python 101,2025-02-01,09:00,Dr. Smith,Room A,90,Introduction to Python
    Math Workshop,2025-02-01,14:30,Prof. Johnson,Room B,60,Advanced Calculus
    ```
    """
    try:
        # Process the import using our service
        result = await import_service.process_import(
            file=file, preview_only=preview_only, current_user=current_user
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions (they have appropriate status codes)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500, detail=f"Import processing failed: {str(e)}"
        )


@router.get("/schedule/history")
async def get_import_history(current_user=Depends(get_current_user)):
    """
    Get history of schedule imports for the current user.

    Returns list of past imports with timestamps, file names,
    success status, and row counts.

    **Note**: Import history feature is planned for future implementation.
    Currently returns a placeholder response.
    """
    # TODO: Implement import history retrieval from database
    return {
        "message": "Import history feature coming soon",
        "user_id": current_user.sub,
        "imports": [],
    }


@router.get("/schedule/template")
async def download_template():
    """
    Download a CSV template file for schedule imports.

    Returns a sample CSV file with the correct column headers
    and example data to help users format their imports correctly.
    """
    # Create sample CSV content
    csv_content = """program,date,time,instructor,room,duration,description
Python 101,2025-02-01,09:00,Dr. Smith,Room A,90,Introduction to Python programming
Math Workshop,2025-02-01,14:30,Prof. Johnson,Room B,60,Advanced Calculus workshop
Science Lab,2025-02-02,10:00,Dr. Williams,Lab 1,120,Chemistry laboratory session
History Seminar,2025-02-02,16:00,Prof. Brown,Room C,75,World War II discussion
Art Class,2025-02-03,11:00,Ms. Davis,Studio,90,Watercolor painting techniques"""

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule_template.csv"},
    )


@router.get("/schedule/status")
async def get_import_status():
    """
    Get current status and capabilities of the schedule import system.

    Returns information about supported file formats, size limits,
    required columns, and system health.
    """
    return {
        "status": "operational",
        "supported_formats": [".csv", ".xlsx", ".xls"],
        "max_file_size_mb": 10,
        "required_columns": ["program", "date", "time", "instructor", "room"],
        "optional_columns": ["duration", "description"],
        "features": {
            "validation": "enabled",
            "conflict_detection": "enabled",
            "preview_mode": "enabled",
            "rollback_on_error": "enabled",
            "plone_integration": "enabled",
        },
        "date_format": "YYYY-MM-DD",
        "time_format": "HH:MM",
        "duration_format": "minutes (integer)",
    }
