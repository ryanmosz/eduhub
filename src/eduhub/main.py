#!/usr/bin/env python3
"""
EduHub API main application module.

This module initializes and configures the FastAPI application with all routers,
middleware, and dependencies for the educational content management system.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .alerts.endpoints import router as alerts_router
from .auth.oauth import router as oauth_router
from .auth.endpoints import router as auth_endpoints_router
from .auth.test_console import router as auth_console_router
from .courses.endpoints import router as courses_router
from .oembed.endpoints import router as oembed_router
from .open_data.endpoints import router as open_data_router
from .performance_demo import router as performance_router
from .plone_content_endpoints import router as plone_content_router
from .schedule_importer.endpoints import router as schedule_router
from .workflows.endpoints import router as workflows_router
from .rbac_demo import router as rbac_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 EduHub API starting up...")

    # Initialize components
    try:
        # Import here to ensure all dependencies are ready
        from .oembed.client import get_oembed_client
        from .alerts.services import dispatch_service

        # Initialize oEmbed client
        oembed_client = await get_oembed_client()
        logger.info("✅ oEmbed client initialized")

        # Initialize alert dispatch service
        await dispatch_service.initialize()
        logger.info("✅ Alert dispatch service initialized")

        # Other startup tasks could go here

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 EduHub API shutting down...")

    try:
        # Cleanup oEmbed client
        from .oembed.client import get_oembed_client
        from .alerts.services import dispatch_service

        oembed_client = await get_oembed_client()
        await oembed_client.close()
        logger.info("✅ oEmbed client and cache cleaned up")

        # Cleanup alert dispatch service
        await dispatch_service.shutdown()
        logger.info("✅ Alert dispatch service cleaned up")

        # Other cleanup tasks could go here

    except Exception as e:
        logger.error(f"❌ Shutdown cleanup failed: {e}")


# Create FastAPI application
app = FastAPI(
    title="EduHub API",
    description="""
    Comprehensive educational content management system providing OAuth2 authentication,
    rich media embedding, open data access, workflow management, and Plone CMS integration.

    ## Features

    * **OAuth2 Authentication** - Secure user authentication and authorization
    * **Rich Media Embedding** - oEmbed protocol support for YouTube, Vimeo, Twitter, etc.
    * **Open Data API** - Public read-only access to educational content
    * **Workflow Management** - Role-based workflow templates for content approval
    * **Schedule Import** - CSV-based schedule and event management
    * **Plone Integration** - Seamless integration with Plone CMS

    ## Authentication

    Most endpoints require authentication via Bearer token. Use the `/auth/` endpoints
    to obtain tokens or visit the Auth Console for testing.
    """,
    version="1.0.0",
    contact={
        "name": "EduHub Development Team",
        "email": "dev@eduhub.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
# TEMPORARY: Allow all origins for demo
# TODO: Remove this after updating CORS_ORIGINS env var on Render
if os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth_router, tags=["Authentication"])
app.include_router(auth_endpoints_router, tags=["Authentication"])
app.include_router(auth_console_router, tags=["Auth Console"])
app.include_router(courses_router, tags=["Courses"])
app.include_router(oembed_router, prefix="/oembed", tags=["Rich Media"])
app.include_router(open_data_router, tags=["Open Data"])
app.include_router(workflows_router, tags=["Workflows"])
app.include_router(alerts_router, prefix="/alerts", tags=["Real-time Alerts"])
app.include_router(plone_content_router, prefix="/plone", tags=["Plone Content"])
app.include_router(schedule_router, prefix="/schedule", tags=["Schedule Import"])
app.include_router(performance_router, tags=["Performance Demo"])
app.include_router(rbac_router, tags=["RBAC Demo"])


@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint with basic information and available services.
    """
    return {
        "message": "Welcome to EduHub API",
        "version": "1.0.0",
        "services": {
            "authentication": "/auth/",
            "auth_console": "/test/",
            "courses": "/api/courses/",
            "rich_media": "/oembed/",
            "open_data": "/data/",
            "workflows": "/workflows/",
            "alerts": "/alerts/",
            "plone_content": "/plone/",
            "schedule_import": "/schedule/",
        },
        "documentation": {
            "openapi": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": "operational",
            "authentication": "operational",
            "oembed": "operational",
            "open_data": "operational",
            "workflows": "operational",
            "alerts": "operational",
            "plone_integration": "operational",
            "schedule_import": "operational",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
