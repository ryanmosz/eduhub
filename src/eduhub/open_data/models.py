"""
Pydantic models for Open Data API requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemPublic(BaseModel):
    """Public representation of a CMS content item."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    uid: str = Field(
        ...,
        description="Unique identifier for the content item",
        examples=["abc123", "def456"],
    )
    title: str = Field(
        ...,
        description="Title of the content item",
        examples=["Welcome to EduHub", "Course Information"],
    )
    description: Optional[str] = Field(
        None,
        description="Brief description of the content",
        examples=["Learn about our educational programs"],
    )
    portal_type: str = Field(
        ...,
        description="Content type in the CMS",
        examples=["Document", "Event", "News Item"],
    )
    url: str = Field(
        ...,
        description="URL to access the full content",
        examples=["https://eduhub.example.com/welcome"],
    )
    created: Optional[str] = Field(
        None,
        description="ISO timestamp when content was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    modified: Optional[str] = Field(
        None,
        description="ISO timestamp when content was last modified",
        examples=["2024-01-20T14:45:00Z"],
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional public metadata",
        examples=[
            {
                "subject": ["education", "welcome"],
                "language": "en",
                "effective": "2024-01-15T10:30:00Z",
            }
        ],
    )


class ItemListResponse(BaseModel):
    """Response model for paginated list of content items."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    items: list[ItemPublic] = Field(..., description="List of content items")
    total: int = Field(
        ..., ge=0, description="Total number of items available", examples=[150, 0]
    )
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items requested per page",
        examples=[25, 50],
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Starting position in the total result set",
        examples=[0, 25],
    )
    has_more: bool = Field(
        ..., description="Whether more items are available", examples=[True, False]
    )
    next_cursor: Optional[str] = Field(
        None,
        description="Cursor for next page of results",
        examples=["eyJvZmZzZXQiOjI1LCJ0aW1lc3RhbXAiOiIyMDI0In0="],
    )


class OpenDataError(BaseModel):
    """Error response model for Open Data API."""

    model_config = ConfigDict(extra="forbid")

    error: str = Field(
        ...,
        description="Error type identifier",
        examples=["not_found", "rate_limit_exceeded", "invalid_parameters"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Content item not found", "Rate limit exceeded"],
    )
    details: Optional[dict[str, Any]] = Field(
        None,
        description="Additional error details",
        examples=[{"uid": "abc123", "timestamp": "2024-01-20T15:30:00Z"}],
    )
