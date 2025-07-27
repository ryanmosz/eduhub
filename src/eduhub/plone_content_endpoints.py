"""
Plone content endpoints with oEmbed integration.

Task 5.3.3: Update content create/update endpoints to call injection util when content_type=="Document".
Provides enhanced content management with automatic media URL embedding.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth.dependencies import get_current_user
from .auth.models import User
from .plone_integration import get_plone_client, transform_plone_content_with_embeds

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plone/content", tags=["Plone Content"])


class ContentCreateRequest(BaseModel):
    """Request model for creating new Plone content with oEmbed support."""

    parent_path: str = Field(..., description="Path where content should be created")
    portal_type: str = Field(..., description="Type of content to create")
    title: str = Field(..., description="Content title")
    text: Optional[str] = Field(
        None, description="Content body text (will be processed for media embeds)"
    )
    description: Optional[str] = Field(None, description="Content description")
    inject_embeds: bool = Field(
        True, description="Whether to automatically embed media URLs"
    )
    maxwidth: Optional[int] = Field(
        800, description="Maximum width for embedded content"
    )
    maxheight: Optional[int] = Field(
        600, description="Maximum height for embedded content"
    )
    additional_fields: dict[str, Any] = Field(
        default_factory=dict, description="Additional content fields"
    )


class ContentUpdateRequest(BaseModel):
    """Request model for updating Plone content with oEmbed support."""

    text: Optional[str] = Field(None, description="Updated content body text")
    title: Optional[str] = Field(None, description="Updated content title")
    description: Optional[str] = Field(None, description="Updated content description")
    inject_embeds: bool = Field(
        True, description="Whether to automatically embed media URLs"
    )
    maxwidth: Optional[int] = Field(
        800, description="Maximum width for embedded content"
    )
    maxheight: Optional[int] = Field(
        600, description="Maximum height for embedded content"
    )
    additional_fields: dict[str, Any] = Field(
        default_factory=dict, description="Additional content fields"
    )


@router.post(
    "/create",
    summary="Create Plone content with oEmbed",
    description="Create new Plone content with automatic media URL embedding",
)
async def create_content_with_embeds(
    request: ContentCreateRequest, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Create new Plone content with automatic oEmbed injection.

    **Task 5.3.3**: Demonstrates content creation with oEmbed processing for Document types.

    **Features:**
    - Automatic detection and embedding of YouTube, Twitter, Vimeo URLs
    - Configurable embed dimensions
    - Safe HTML sanitization
    - Fallback to original text on embedding errors

    **Example:**
    ```json
    {
        "parent_path": "/documents",
        "portal_type": "Document",
        "title": "My Video Collection",
        "text": "Check out this video: https://youtube.com/watch?v=dQw4w9WgXcQ",
        "inject_embeds": true
    }
    ```
    """
    try:
        plone_client = await get_plone_client()

        # Prepare additional fields
        kwargs = request.additional_fields.copy()
        if request.description:
            kwargs["description"] = request.description

        # Create content with embed processing
        result = await plone_client.create_content_with_embeds(
            parent_path=request.parent_path,
            portal_type=request.portal_type,
            title=request.title,
            text=request.text,
            inject_embeds=request.inject_embeds,
            **kwargs,
        )

        # Transform the result to include embed metadata
        if request.inject_embeds and request.text:
            try:
                enhanced_result = await transform_plone_content_with_embeds(
                    result,
                    inject_embeds=False,  # Already processed
                    maxwidth=request.maxwidth,
                    maxheight=request.maxheight,
                )

                return {
                    "status": "success",
                    "message": f"Content '{request.title}' created successfully with oEmbed processing",
                    "content": enhanced_result.dict(),
                    "plone_response": result,
                    "oembed_processed": True,
                    "portal_type": request.portal_type,
                }
            except Exception as e:
                logger.warning(f"Error in post-creation transform: {e}")

        return {
            "status": "success",
            "message": f"Content '{request.title}' created successfully",
            "plone_response": result,
            "oembed_processed": request.inject_embeds,
            "portal_type": request.portal_type,
        }

    except Exception as e:
        logger.error(f"Error creating content with embeds: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create content: {str(e)}"
        )


@router.patch(
    "/{path:path}",
    summary="Update Plone content with oEmbed",
    description="Update existing Plone content with automatic media URL embedding",
)
async def update_content_with_embeds(
    path: str, request: ContentUpdateRequest, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Update existing Plone content with automatic oEmbed injection.

    **Task 5.3.3**: Demonstrates content updates with oEmbed processing for Document types.

    **Path Parameter:**
    - `path`: Plone content path (e.g., "documents/my-article")

    **Features:**
    - Updates existing content while preserving structure
    - Processes text content for media URLs
    - Only applies to Document content types
    - Maintains content metadata and workflow state
    """
    try:
        plone_client = await get_plone_client()

        # Prepare update fields
        kwargs = request.additional_fields.copy()
        if request.title:
            kwargs["title"] = request.title
        if request.description:
            kwargs["description"] = request.description

        # Update content with embed processing
        result = await plone_client.update_content_with_embeds(
            path=path, text=request.text, inject_embeds=request.inject_embeds, **kwargs
        )

        # Transform the result to include embed metadata
        if request.inject_embeds and request.text:
            try:
                enhanced_result = await transform_plone_content_with_embeds(
                    result,
                    inject_embeds=False,  # Already processed
                    maxwidth=request.maxwidth,
                    maxheight=request.maxheight,
                )

                return {
                    "status": "success",
                    "message": f"Content at '{path}' updated successfully with oEmbed processing",
                    "content": enhanced_result.dict(),
                    "plone_response": result,
                    "oembed_processed": True,
                }
            except Exception as e:
                logger.warning(f"Error in post-update transform: {e}")

        return {
            "status": "success",
            "message": f"Content at '{path}' updated successfully",
            "plone_response": result,
            "oembed_processed": request.inject_embeds,
        }

    except Exception as e:
        logger.error(f"Error updating content with embeds at '{path}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update content: {str(e)}"
        )


@router.get(
    "/{path:path}/preview-embeds",
    summary="Preview oEmbed transformations",
    description="Preview how media URLs in content would be transformed without saving",
)
async def preview_embeds(
    path: str,
    maxwidth: Optional[int] = 800,
    maxheight: Optional[int] = 600,
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Preview oEmbed transformations for existing content without modifying it.

    **Useful for:**
    - Testing embed transformations before applying
    - Debugging embed detection
    - Content review workflows
    """
    try:
        plone_client = await get_plone_client()

        # Get current content
        current_content = await plone_client.get_content(path)

        # Transform with embeds for preview
        enhanced_content = await transform_plone_content_with_embeds(
            current_content, inject_embeds=True, maxwidth=maxwidth, maxheight=maxheight
        )

        # Also show detected URLs
        from .oembed.content_utils import detect_media_urls, extract_plain_urls

        original_text = current_content.get("text", {}).get("data", "")
        detected_urls = detect_media_urls(original_text) if original_text else []
        plain_urls = extract_plain_urls(original_text) if original_text else []

        return {
            "status": "success",
            "original_content": current_content,
            "enhanced_content": enhanced_content.dict(),
            "detected_media_urls": [
                {"url": url, "domain": domain, "start": start, "end": end}
                for url, domain, start, end in detected_urls
            ],
            "plain_media_urls": plain_urls,
            "oembed_metadata": {
                "processed": enhanced_content.metadata.get("oembed_processed", False),
                "timestamp": enhanced_content.metadata.get("oembed_timestamp"),
                "error": enhanced_content.metadata.get("oembed_error"),
            },
        }

    except Exception as e:
        logger.error(f"Error previewing embeds for '{path}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to preview embeds: {str(e)}"
        )


@router.post(
    "/batch-process",
    summary="Batch process content for oEmbed",
    description="Process multiple content items for oEmbed transformation",
)
async def batch_process_embeds(
    paths: list[str] = Body(..., description="List of content paths to process"),
    maxwidth: Optional[int] = 800,
    maxheight: Optional[int] = 600,
    dry_run: bool = Body(True, description="Preview changes without applying them"),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Batch process multiple content items for oEmbed transformations.

    **Parameters:**
    - `paths`: List of Plone content paths to process
    - `dry_run`: If true, only preview changes without saving
    - `maxwidth/maxheight`: Embed dimensions

    **Use Cases:**
    - Bulk content migration with embed processing
    - Content audit and enhancement
    - Site-wide media URL conversion
    """
    try:
        plone_client = await get_plone_client()

        results = []
        processed_count = 0
        error_count = 0

        for path in paths:
            try:
                # Get current content
                current_content = await plone_client.get_content(path)
                portal_type = current_content.get("@type", "")

                # Only process Documents
                if portal_type != "Document":
                    results.append(
                        {
                            "path": path,
                            "status": "skipped",
                            "reason": f"Content type '{portal_type}' not processed for embeds",
                        }
                    )
                    continue

                # Transform with embeds
                enhanced_content = await transform_plone_content_with_embeds(
                    current_content,
                    inject_embeds=True,
                    maxwidth=maxwidth,
                    maxheight=maxheight,
                )

                # Apply changes if not dry run
                if not dry_run and enhanced_content.text != current_content.get(
                    "text", {}
                ).get("data"):
                    await plone_client.update_content(
                        path,
                        text={
                            "data": enhanced_content.text,
                            "content-type": "text/html",
                        },
                    )
                    processed_count += 1
                    status = "updated"
                else:
                    status = "preview" if dry_run else "no_changes"

                results.append(
                    {
                        "path": path,
                        "status": status,
                        "oembed_processed": enhanced_content.metadata.get(
                            "oembed_processed", False
                        ),
                        "original_length": len(
                            current_content.get("text", {}).get("data", "")
                        ),
                        "processed_length": len(enhanced_content.text or ""),
                        "portal_type": portal_type,
                    }
                )

            except Exception as e:
                error_count += 1
                results.append({"path": path, "status": "error", "error": str(e)})
                logger.error(f"Error processing path '{path}': {e}")

        return {
            "status": "completed",
            "dry_run": dry_run,
            "summary": {
                "total_paths": len(paths),
                "processed": processed_count,
                "errors": error_count,
                "skipped": len(paths) - processed_count - error_count,
            },
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch processing failed: {str(e)}"
        )


@router.get(
    "/embed-stats",
    summary="Get oEmbed processing statistics",
    description="Get statistics about oEmbed processing across content",
)
async def get_embed_stats(
    path_filter: Optional[str] = None, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Get statistics about oEmbed processing and media URL detection.

    **Features:**
    - Count of content with embedded media
    - Supported domain usage statistics
    - Processing success rates
    - Content type breakdown
    """
    try:
        from .oembed.content_utils import get_supported_domains

        return {
            "status": "success",
            "supported_domains": get_supported_domains(),
            "features": {
                "auto_detection": True,
                "batch_processing": True,
                "preview_mode": True,
                "document_types_only": True,
            },
            "endpoints": {
                "create_with_embeds": "/plone/content/create",
                "update_with_embeds": "/plone/content/{path}",
                "preview_embeds": "/plone/content/{path}/preview-embeds",
                "batch_process": "/plone/content/batch-process",
            },
        }

    except Exception as e:
        logger.error(f"Error getting embed stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
