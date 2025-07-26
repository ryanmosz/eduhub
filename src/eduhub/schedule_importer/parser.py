"""
CSV/Excel parsing and validation for schedule imports.

Handles file parsing using pandas, data validation, and 
row-level error reporting for schedule import operations.
"""

import pandas as pd
import tempfile
import os
from typing import List, Tuple, Optional, BinaryIO
from fastapi import UploadFile, HTTPException

from .models import ScheduleRow, ValidationError


class ScheduleParser:
    """Handles parsing and validation of schedule files."""
    
    REQUIRED_COLUMNS = ['program', 'date', 'time', 'instructor', 'room']
    OPTIONAL_COLUMNS = ['duration', 'description']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self.validation_errors: List[ValidationError] = []
    
    async def parse_file(self, file: UploadFile) -> Tuple[List[ScheduleRow], List[ValidationError]]:
        """
        Parse uploaded CSV or Excel file into ScheduleRow objects.
        
        Returns:
            Tuple of (parsed_rows, validation_errors)
        """
        self.validation_errors = []
        
        # Validate file size
        if file.size and file.size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {self.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Validate file type
        if not self._is_supported_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload .csv or .xlsx files only"
            )
        
        # Save to temporary file for pandas processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_file_suffix(file.filename)) as tmp_file:
            try:
                content = await file.read()
                tmp_file.write(content)
                tmp_file.flush()
                
                # Parse with pandas
                df = self._read_dataframe(tmp_file.name, file.filename)
                
                # Validate structure and parse rows
                self._validate_columns(df)
                rows = self._parse_rows(df)
                
                return rows, self.validation_errors
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_file.name)
    
    def _is_supported_file(self, filename: Optional[str]) -> bool:
        """Check if file type is supported."""
        if not filename:
            return False
        return filename.lower().endswith(('.csv', '.xlsx', '.xls'))
    
    def _get_file_suffix(self, filename: Optional[str]) -> str:
        """Get appropriate file suffix for temporary file."""
        if not filename:
            return '.csv'
        if filename.lower().endswith('.xlsx'):
            return '.xlsx'
        if filename.lower().endswith('.xls'):
            return '.xls'
        return '.csv'
    
    def _read_dataframe(self, filepath: str, original_filename: Optional[str]) -> pd.DataFrame:
        """Read file into pandas DataFrame."""
        try:
            if original_filename and original_filename.lower().endswith(('.xlsx', '.xls')):
                return pd.read_excel(filepath, engine='openpyxl')
            else:
                return pd.read_csv(filepath)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse file: {str(e)}"
            )
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns are present."""
        # Normalize column names (lowercase, strip whitespace)
        df.columns = df.columns.str.lower().str.strip()
        
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
    
    def _parse_rows(self, df: pd.DataFrame) -> List[ScheduleRow]:
        """Parse DataFrame rows into ScheduleRow objects."""
        rows = []
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # +2 because pandas is 0-indexed and CSV has header
            
            try:
                # Extract required fields
                row_data = {
                    'program': self._safe_str(row.get('program')),
                    'date': self._safe_str(row.get('date')),
                    'time': self._safe_str(row.get('time')),
                    'instructor': self._safe_str(row.get('instructor')),
                    'room': self._safe_str(row.get('room')),
                }
                
                # Add optional fields if present
                if 'duration' in df.columns and pd.notna(row.get('duration')):
                    row_data['duration'] = self._safe_int(row.get('duration'))
                
                if 'description' in df.columns and pd.notna(row.get('description')):
                    row_data['description'] = self._safe_str(row.get('description'))
                
                # Validate required fields are not empty
                for field, value in row_data.items():
                    if field in self.REQUIRED_COLUMNS and (not value or value.strip() == ''):
                        self.validation_errors.append(ValidationError(
                            row_number=row_num,
                            field=field,
                            message=f"Required field '{field}' is empty",
                            value=str(value) if value else None
                        ))
                
                # Create ScheduleRow object (this will trigger Pydantic validation)
                schedule_row = ScheduleRow(**row_data)
                rows.append(schedule_row)
                
            except ValueError as e:
                # Pydantic validation error
                self.validation_errors.append(ValidationError(
                    row_number=row_num,
                    field=None,
                    message=str(e),
                    value=None
                ))
            except Exception as e:
                # Unexpected error
                self.validation_errors.append(ValidationError(
                    row_number=row_num,
                    field=None,
                    message=f"Unexpected error: {str(e)}",
                    value=None
                ))
        
        return rows
    
    def _safe_str(self, value) -> str:
        """Safely convert value to string."""
        if pd.isna(value):
            return ""
        return str(value).strip()
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer."""
        if pd.isna(value):
            return None
        try:
            return int(float(value))  # Handle cases where Excel stores integers as floats
        except (ValueError, TypeError):
            return None 