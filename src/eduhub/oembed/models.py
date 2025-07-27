"""
Pydantic models for oEmbed API requests and responses.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl


class EmbedRequest(BaseModel):
    """Request model for oEmbed proxy endpoint."""

    url: HttpUrl = Field(
        ...,
        description="URL to embed (must be from allowed provider)",
        examples=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://vimeo.com/123456789",
            "https://twitter.com/user/status/123456789",
        ],
    )
    maxwidth: Optional[int] = Field(
        None,
        ge=200,
        le=1920,
        description="Maximum width of embed in pixels",
        examples=[800, 1200],
    )
    maxheight: Optional[int] = Field(
        None,
        ge=200,
        le=1080,
        description="Maximum height of embed in pixels",
        examples=[450, 600],
    )


class EmbedResponse(BaseModel):
    """Response model for successful oEmbed proxy."""

    html: str = Field(
        ...,
        description="Sanitized HTML embed code ready for injection",
        examples=[
            '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" width="560" height="315"></iframe>'
        ],
    )
    title: Optional[str] = Field(
        None,
        description="Title of the embedded content",
        examples=["Rick Astley - Never Gonna Give You Up (Video)"],
    )
    provider_name: Optional[str] = Field(
        None,
        description="Name of the oEmbed provider",
        examples=["YouTube", "Vimeo", "Twitter"],
    )
    provider_url: Optional[str] = Field(
        None,
        description="URL of the oEmbed provider",
        examples=["https://www.youtube.com/", "https://vimeo.com/"],
    )
    width: Optional[int] = Field(
        None, description="Width of the embed in pixels", examples=[560, 800]
    )
    height: Optional[int] = Field(
        None, description="Height of the embed in pixels", examples=[315, 450]
    )
    thumbnail_url: Optional[str] = Field(
        None,
        description="URL of thumbnail image for the content",
        examples=["https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"],
    )
    cached: bool = Field(
        False,
        description="Whether response was served from cache",
        examples=[True, False],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "html": '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" width="560" height="315" frameborder="0" allowfullscreen></iframe>',
                "title": "Rick Astley - Never Gonna Give You Up (Video)",
                "provider_name": "YouTube",
                "provider_url": "https://www.youtube.com/",
                "width": 560,
                "height": 315,
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                "cached": True,
            }
        }


class EmbedError(BaseModel):
    """Error response for failed embed requests."""

    error: str = Field(
        ...,
        description="Error type identifier",
        examples=["provider_not_allowed", "invalid_url", "provider_timeout"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=[
            "Domain 'example.com' is not in the list of supported providers",
            "The provided URL is not a valid HTTP/HTTPS URL",
            "Provider request timed out",
        ],
    )
    url: Optional[str] = Field(
        None,
        description="The URL that failed to embed",
        examples=["https://example.com/video", "invalid-url"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "provider_not_allowed",
                "message": "Domain 'example.com' is not in the list of supported providers",
                "url": "https://example.com/video",
            }
        }


class ProviderConfig(BaseModel):
    """Configuration for an oEmbed provider."""

    name: str = Field(..., description="Provider name (e.g., 'YouTube')")
    url_patterns: list[str] = Field(
        ..., description="URL patterns this provider handles"
    )
    oembed_endpoint: str = Field(..., description="oEmbed API endpoint URL")
    supports_https: bool = Field(True, description="Whether provider supports HTTPS")
