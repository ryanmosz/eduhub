"""
EduHub FastAPI Application

Main entry point for the FastAPI application that modernizes Plone CMS.
Includes integration endpoints for accessing legacy Plone content via modern REST API.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, Response

# Import the hello world module for basic endpoints
from hello import app as hello_app

# Import auth router
from .auth.oauth import router as auth_router
from .auth.test_console import (
    router as test_router,  # Re-enabled after fixing syntax error
)

# Import Plone integration
from .plone_integration import (
    PloneAPIError,
    PloneClient,
    PloneContent,
    close_plone_client,
    get_plone_client,
    transform_plone_content,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events - startup and shutdown."""
    # Startup
    logger.info("Starting EduHub FastAPI application...")
    try:
        # Initialize Plone client connection
        plone_client = await get_plone_client()
        logger.info("Plone integration initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Plone integration: {e}")
        # Continue without Plone integration for development

    yield

    # Shutdown
    logger.info("Shutting down EduHub FastAPI application...")
    await close_plone_client()
    logger.info("Plone integration closed")


# Create the main FastAPI application with lifespan events
app = FastAPI(
    title="EduHub API",
    description="Modern education portal API bridging FastAPI with legacy Plone CMS",
    version="0.1.0",
    lifespan=lifespan,
    # Add security scheme for OAuth2/JWT authentication
    openapi_components={
        "securitySchemes": {
            "HTTPBearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Auth0 JWT token authentication. Get your token from /auth/login",
            }
        }
    },
)

# Include the hello world endpoints
app.mount("/hello", hello_app)

# Include the authentication endpoints
app.include_router(auth_router)

# Include the test console
app.include_router(test_router)


@app.get("/favicon.ico")
async def favicon():
    """Serve a simple graduation cap favicon for all pages."""
    # Simple SVG favicon with graduation cap emoji
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <text y=".9em" font-size="90">🎓</text>
    </svg>"""
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Welcome to EduHub API",
        "version": "0.1.0",
        "description": "Modern education portal bridging FastAPI with Plone CMS",
        "endpoints": {
            "auth": "/auth - OAuth2 authentication endpoints (login, callback, user, logout)",
            "hello": "/hello - Hello world and async demo endpoints",
            "plone": "/plone - Plone CMS integration endpoints",
            "content": "/content - Content management endpoints",
            "docs": "/docs - API documentation",
            "test": "/test/auth-console - OAuth2 testing console",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "service": "eduhub-api",
            "version": "0.1.0",
            "components": {"fastapi": "healthy"},
        }

        # Check Plone integration if available
        try:
            plone_client = await get_plone_client()
            site_info = await plone_client.get_site_info()
            health_status["components"]["plone"] = "healthy"
            health_status["plone_version"] = site_info.get("plone_version", "unknown")
        except Exception as e:
            health_status["components"]["plone"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Plone Integration Endpoints


@app.get("/plone/info")
async def get_plone_info():
    """Get basic information about the connected Plone site."""
    try:
        plone_client = await get_plone_client()
        site_info = await plone_client.get_site_info()

        return {
            "plone_site": site_info.get("title", "Unknown"),
            "description": site_info.get("description", ""),
            "plone_version": site_info.get("plone_version", "unknown"),
            "url": site_info.get("@id", ""),
            "available": True,
        }

    except PloneAPIError as e:
        logger.error(f"Plone API error: {e}")
        raise HTTPException(status_code=502, detail=f"Plone API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error accessing Plone: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to Plone")


@app.get("/content/", response_model=list[PloneContent])
async def list_content(
    query: Optional[str] = Query(None, description="Search query text"),
    content_type: Optional[str] = Query(None, description="Plone content type filter"),
    path: Optional[str] = Query(None, description="Content path filter"),
    limit: int = Query(25, ge=1, le=100, description="Maximum number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
):
    """List and search content from Plone CMS."""
    try:
        plone_client = await get_plone_client()

        # Search content using the Plone client
        search_results = await plone_client.search_content(
            query=query, portal_type=content_type, path=path, limit=limit, start=skip
        )

        # Transform Plone results to our standardized format
        content_items = []
        for item in search_results.get("items", []):
            try:
                content_item = transform_plone_content(item)
                content_items.append(content_item)
            except Exception as e:
                logger.warning(f"Failed to transform content item: {e}")
                continue

        return content_items

    except PloneAPIError as e:
        logger.error(f"Plone API error during content search: {e}")
        raise HTTPException(status_code=502, detail=f"Plone API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during content search: {e}")
        raise HTTPException(status_code=500, detail="Failed to search content")


@app.get("/content/{path:path}", response_model=PloneContent)
async def get_content_by_path(path: str):
    """Get specific content from Plone by path."""
    try:
        plone_client = await get_plone_client()

        # Get content from Plone
        content_data = await plone_client.get_content(path)

        # Transform to standardized format
        content_item = transform_plone_content(content_data)

        return content_item

    except PloneAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Content not found: {path}")
        logger.error(f"Plone API error getting content: {e}")
        raise HTTPException(status_code=502, detail=f"Plone API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content")


@app.post("/content/", response_model=PloneContent)
async def create_content(
    parent_path: str,
    content_type: str,
    title: str,
    description: Optional[str] = None,
    text: Optional[str] = None,
    **additional_fields,
):
    """Create new content in Plone CMS."""
    try:
        plone_client = await get_plone_client()

        # Prepare content data
        content_kwargs = {}
        if description:
            content_kwargs["description"] = description
        if text:
            content_kwargs["text"] = {"data": text, "content-type": "text/html"}

        # Add any additional fields
        content_kwargs.update(additional_fields)

        # Create content in Plone
        created_content = await plone_client.create_content(
            parent_path=parent_path,
            portal_type=content_type,
            title=title,
            **content_kwargs,
        )

        # Transform to standardized format
        content_item = transform_plone_content(created_content)

        return content_item

    except PloneAPIError as e:
        logger.error(f"Plone API error creating content: {e}")
        raise HTTPException(status_code=502, detail=f"Plone API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating content: {e}")
        raise HTTPException(status_code=500, detail="Failed to create content")


@app.put("/content/{path:path}", response_model=PloneContent)
async def update_content(
    path: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    text: Optional[str] = None,
    **additional_fields,
):
    """Update existing content in Plone CMS."""
    try:
        plone_client = await get_plone_client()

        # Prepare update data
        update_kwargs = {}
        if title:
            update_kwargs["title"] = title
        if description:
            update_kwargs["description"] = description
        if text:
            update_kwargs["text"] = {"data": text, "content-type": "text/html"}

        # Add any additional fields
        update_kwargs.update(additional_fields)

        # Update content in Plone
        updated_content = await plone_client.update_content(path=path, **update_kwargs)

        # Transform to standardized format
        content_item = transform_plone_content(updated_content)

        return content_item

    except PloneAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Content not found: {path}")
        logger.error(f"Plone API error updating content: {e}")
        raise HTTPException(status_code=502, detail=f"Plone API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error updating content: {e}")
        raise HTTPException(status_code=500, detail="Failed to update content")


@app.delete("/content/{path:path}")
async def delete_content(path: str):
    """Delete content from Plone CMS."""
    try:
        plone_client = await get_plone_client()

        # Delete content from Plone
        success = await plone_client.delete_content(path)

        if success:
            return {"message": f"Content deleted successfully: {path}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete content")

    except PloneAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Content not found: {path}")
        logger.error(f"Plone API error deleting content: {e}")
        raise HTTPException(status_code=502, detail=f"Plone API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error deleting content: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete content")


# Error handlers


@app.exception_handler(PloneAPIError)
async def plone_api_error_handler(request, exc: PloneAPIError):
    """Handle Plone API errors gracefully."""
    logger.error(f"Plone API error: {exc}")

    status_code = exc.status_code or 502
    detail = str(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "Plone API Error",
            "detail": detail,
            "plone_response": exc.response_data,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
