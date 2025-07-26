"""
Main FastAPI application for EduHub.

Modern education portal bridging FastAPI with Plone CMS.
Provides OAuth2 authentication, content management, and API endpoints.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.openapi.utils import get_openapi

# Import routers
from .auth.oauth import router as auth_router
from .auth.test_console import router as test_router
from .schedule_importer.endpoints import router as schedule_router
from .schedule_importer.test_console import router as schedule_test_router

# Import exception handlers
from .auth.dependencies import HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🚀 EduHub API starting up...")
    yield
    print("🛑 EduHub API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="EduHub API",
    description="Modern education portal bridging FastAPI with Plone CMS",
    version="0.1.0",
    lifespan=lifespan,
    openapi_components={
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
        "http://127.0.0.1:8000",  # Alternative localhost
        "https://dev-1fx6yhxxi543ipno.us.auth0.com",  # Auth0 domain
        "https://*.auth0.com",  # Auth0 subdomains
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(test_router, prefix="/test", tags=["Testing"])
app.include_router(schedule_router, tags=["Schedule Import"])
app.include_router(schedule_test_router, prefix="/test", tags=["Schedule Import Testing"])

@app.get("/")
async def root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to EduHub API",
        "version": "0.1.0",
        "description": "Modern education portal bridging FastAPI with Plone CMS",
        "endpoints": {
            "auth": "/auth - OAuth2 authentication endpoints (login, callback, user, logout)",
            "hello": "/hello - Hello world and async demo endpoints", 
            "plone": "/plone - Plone CMS integration endpoints",
            "import": "/import - Schedule import endpoints (CSV/Excel)",
            "content": "/content - Content management endpoints",
            "docs": "/docs - API documentation",
            "test": "/test/auth-console - OAuth2 testing console",
            "schedule_test": "/test/schedule-test - 📊 Unified CSV Schedule Import Test Console"
        }
    }


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors in browsers."""
    # Return a simple graduation cap emoji as favicon
    return Response(
        content="🎓",
        media_type="text/plain"
    )


@app.get("/hello")
async def hello():
    """Simple hello endpoint for testing."""
    return {"message": "Hello from EduHub!"}


@app.get("/hello/async")
async def hello_async():
    """Async hello endpoint demonstrating async capabilities."""
    import asyncio
    await asyncio.sleep(0.1)  # Simulate async work
    return {
        "message": "Hello from async EduHub!",
        "async": True,
        "python_version": os.sys.version
    }


# Plone Integration Endpoints (placeholder)
@app.get("/plone/status")
async def plone_status():
    """Check Plone CMS connectivity status."""
    # TODO: Implement actual Plone status check
    return {
        "status": "connected",
        "plone_version": "6.0.x",
        "integration": "active"
    }


@app.get("/plone/content")
async def get_plone_content():
    """Get content from Plone CMS."""
    # TODO: Implement actual Plone content retrieval
    return {
        "content": "Plone content integration coming soon",
        "endpoint": "placeholder"
    }


# Content Management Endpoints (placeholder)
@app.get("/content")
async def list_content():
    """List available content."""
    return {
        "content": [],
        "message": "Content management endpoints coming soon"
    }


# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent formatting."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc) if os.getenv("DEBUG") else None
        }
    )


# Custom OpenAPI Schema
def custom_openapi():
    """Generate custom OpenAPI schema with authentication."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="EduHub API",
        version="0.1.0",
        description="Modern education portal with OAuth2 authentication and Plone CMS integration",
        routes=app.routes,
    )
    
    # Add security requirement to all endpoints except public ones
    public_paths = ["/", "/hello", "/hello/async", "/favicon.ico", "/docs", "/openapi.json"]
    
    for path, path_item in openapi_schema["paths"].items():
        if path not in public_paths:
            for method in path_item.values():
                if isinstance(method, dict) and "security" not in method:
                    method["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
