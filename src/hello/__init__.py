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


@app.get("/async-tasks-demo")
async def async_tasks_demo() -> dict[str, Any]:
    """Demonstrate async task patterns for long-running operations."""

    async def simulate_image_processing(image_id: str, size: str) -> dict[str, Any]:
        """Simulate async image scaling operation."""
        processing_time = (
            0.2 if size == "thumbnail" else 0.5
        )  # Simulate different processing times
        await asyncio.sleep(processing_time)
        return {
            "image_id": image_id,
            "size": size,
            "status": "processed",
            "processing_time_ms": processing_time * 1000,
        }

    async def simulate_data_migration(batch_size: int) -> dict[str, Any]:
        """Simulate async data migration operation."""
        processing_time = batch_size * 0.01  # 10ms per item
        await asyncio.sleep(processing_time)
        return {
            "batch_size": batch_size,
            "status": "migrated",
            "processing_time_ms": processing_time * 1000,
        }

    async def simulate_email_notification(recipient: str) -> dict[str, Any]:
        """Simulate async email sending operation."""
        await asyncio.sleep(0.1)  # Simulate email API call
        return {"recipient": recipient, "status": "sent", "processing_time_ms": 100}

    start_time = datetime.now()

    # Run multiple types of long-running operations concurrently
    long_running_tasks = [
        simulate_image_processing("img_001", "thumbnail"),
        simulate_image_processing("img_002", "full"),
        simulate_data_migration(50),
        simulate_data_migration(25),
        simulate_email_notification("admin@eduhub.local"),
        simulate_email_notification("user@eduhub.local"),
    ]

    results = await asyncio.gather(*long_running_tasks)
    end_time = datetime.now()

    return {
        "message": "Long-running async operations completed",
        "operations": len(results),
        "results": results,
        "total_execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "demonstrates": [
            "Concurrent image processing simulation",
            "Async data migration patterns",
            "Background email notifications",
            "asyncio.gather() for parallel execution",
        ],
        "use_cases": [
            "Plone content migration",
            "Batch image scaling",
            "Email notifications",
            "Data synchronization",
        ],
    }


@app.get("/async-patterns-advanced")
async def async_patterns_advanced() -> dict[str, Any]:
    """Demonstrate advanced async/await patterns for Python 3.11+."""

    class AsyncContextExample:
        """Demonstrate async context manager pattern."""

        async def __aenter__(self):
            await asyncio.sleep(0.01)  # Simulate async setup
            return {"connection": "established", "setup_time": 10}

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await asyncio.sleep(0.01)  # Simulate async cleanup

    async def async_generator_example():
        """Demonstrate async generator pattern."""
        for i in range(3):
            await asyncio.sleep(0.05)  # Simulate async data fetching
            yield {"batch": i + 1, "data": f"async_data_batch_{i + 1}"}

    async def async_comprehension_example():
        """Demonstrate async comprehensions (Python 3.6+ but optimized in 3.11)."""

        async def fetch_item(item_id: int):
            await asyncio.sleep(0.02)
            return {"id": item_id, "value": f"item_{item_id}"}

        # Async list comprehension
        results = [await fetch_item(i) for i in range(3)]
        return results

    start_time = datetime.now()

    # Demonstrate async context manager
    async with AsyncContextExample() as ctx:
        context_result = ctx

    # Demonstrate async generator
    generator_results = []
    async for item in async_generator_example():
        generator_results.append(item)

    # Demonstrate async comprehensions
    comprehension_results = await async_comprehension_example()

    # Demonstrate asyncio.create_task() for background tasks
    async def background_task(name: str):
        await asyncio.sleep(0.1)
        return f"Background task {name} completed"

    task1 = asyncio.create_task(background_task("A"))
    task2 = asyncio.create_task(background_task("B"))

    background_results = await asyncio.gather(task1, task2)

    end_time = datetime.now()

    return {
        "message": "Advanced async/await patterns demonstrated",
        "context_manager": context_result,
        "async_generator": generator_results,
        "async_comprehension": comprehension_results,
        "background_tasks": background_results,
        "execution_time_ms": (end_time - start_time).total_seconds() * 1000,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "patterns_demonstrated": [
            "Async context managers (__aenter__/__aexit__)",
            "Async generators with async for",
            "Async list comprehensions",
            "asyncio.create_task() for background execution",
            "asyncio.gather() for concurrent awaiting",
        ],
        "python311_optimizations": [
            "Faster async/await execution",
            "Improved asyncio performance",
            "Better async comprehension optimization",
            "Enhanced async context manager handling",
        ],
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
