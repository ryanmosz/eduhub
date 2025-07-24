"""
Hello World module for EduHub - FastAPI async endpoints
Demonstrates modern Python async capabilities and environment verification.
"""

import asyncio
import platform
import sys
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(
    title="EduHub Hello API",
    description="Development environment verification endpoints",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with basic async hello world."""
    await asyncio.sleep(0.001)  # Demonstrate async behavior
    return {
        "message": "Hello from EduHub!",
        "status": "Development environment ready",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for container readiness."""
    return {
        "status": "healthy",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "async_support": True,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/async-demo")
async def async_demo() -> dict[str, Any]:
    """Demonstrate async functionality with concurrent operations."""

    async def fetch_data(delay: float, data: str) -> str:
        await asyncio.sleep(delay)
        return f"Processed: {data}"

    # Run multiple async operations concurrently
    start_time = datetime.now()

    tasks = [
        fetch_data(0.1, "Task 1"),
        fetch_data(0.15, "Task 2"),
        fetch_data(0.05, "Task 3"),
    ]

    results = await asyncio.gather(*tasks)
    end_time = datetime.now()

    return {
        "message": "Async operations completed",
        "results": results,
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "demonstrates": "Python async/await with asyncio.gather()",
    }


@app.get("/external-api-test")
async def external_api_test() -> dict[str, Any]:
    """Test async HTTP client functionality."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://httpbin.org/json")
            response.raise_for_status()
            data = await response.json()

        return {
            "message": "External API call successful",
            "external_data": data,
            "client": "httpx async client",
            "status_code": response.status_code,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"External API call failed: {str(e)}"
        )


@app.get("/environment-info")
async def environment_info() -> dict[str, Any]:
    """Comprehensive environment information for debugging."""
    return {
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "fastapi": {
            "async_support": True,
            "framework": "FastAPI",
            "features": ["async/await", "type hints", "automatic docs"],
        },
        "deployment": {
            "container_ready": True,
            "development_mode": True,
            "auto_reload": True,
        },
        "timestamp": datetime.now().isoformat(),
    }


# Simple sync endpoint for comparison
@app.get("/sync-hello")
def sync_hello() -> dict[str, str]:
    """Synchronous hello endpoint for comparison."""
    return {
        "message": "Hello from sync endpoint",
        "type": "synchronous",
        "note": "Compare with async endpoints for performance",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
