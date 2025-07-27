"""
Mock Plone REST API server for demonstration purposes.
This simulates Plone REST API endpoints for the performance demo.
"""

import asyncio
import random
from fastapi import FastAPI, HTTPException, Header
from typing import Optional
import time

app = FastAPI()

# Mock data
MOCK_TOKEN = "mock-plone-token-12345"
MOCK_SITE_INFO = {
    "@id": "http://localhost:8080/Plone",
    "@type": "Plone Site", 
    "id": "Plone",
    "title": "EduHub Plone Site",
    "description": "Backend CMS for EduHub",
    "plone.version": "5.2.14",
    "plone.restapi.version": "8.43.3"
}

MOCK_NAVIGATION = {
    "@id": "http://localhost:8080/Plone/@navigation",
    "items": [
        {"@id": "http://localhost:8080/Plone/courses", "title": "Courses"},
        {"@id": "http://localhost:8080/Plone/events", "title": "Events"},
        {"@id": "http://localhost:8080/Plone/resources", "title": "Resources"}
    ]
}

MOCK_TYPES = {
    "@id": "http://localhost:8080/Plone/@types",
    "types": [
        {"@id": "Document", "title": "Page"},
        {"@id": "Event", "title": "Event"},
        {"@id": "News Item", "title": "News Item"}
    ]
}

@app.post("/Plone/@login")
async def login(credentials: dict):
    """Mock Plone login endpoint"""
    if credentials.get("login") == "admin" and credentials.get("password") == "admin":
        return {"token": MOCK_TOKEN}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/Plone/@site")
async def get_site(plone_user: Optional[str] = Header(None)):
    """Mock Plone site info endpoint"""
    # Simulate some processing time
    await asyncio.sleep(0.05 + random.random() * 0.05)
    return MOCK_SITE_INFO

@app.get("/Plone/@navigation")
async def get_navigation(plone_user: Optional[str] = Header(None)):
    """Mock Plone navigation endpoint"""
    await asyncio.sleep(0.05 + random.random() * 0.05)
    return MOCK_NAVIGATION

@app.get("/Plone/@types")
async def get_types(plone_user: Optional[str] = Header(None)):
    """Mock Plone content types endpoint"""
    await asyncio.sleep(0.05 + random.random() * 0.05)
    return MOCK_TYPES

@app.get("/Plone/@users")
async def get_users(query: Optional[str] = None):
    """Mock Plone users endpoint"""
    await asyncio.sleep(0.01)
    if query and query == "admin@example.com":
        return {
            "items": [{
                "@id": "http://localhost:8080/Plone/@users/admin",
                "id": "admin",
                "username": "admin",
                "email": "admin@example.com",
                "fullname": "Admin User",
                "roles": ["Manager", "Member"]
            }]
        }
    return {"items": []}

@app.post("/Plone/@users")
async def create_user(user_data: dict):
    """Mock Plone create user endpoint"""
    await asyncio.sleep(0.01)
    return {
        "@id": f"http://localhost:8080/Plone/@users/{user_data.get('username', 'newuser')}",
        "id": user_data.get("username", "newuser"),
        "username": user_data.get("username", "newuser"),
        "email": user_data.get("email", ""),
        "fullname": user_data.get("fullname", ""),
        "roles": ["Member"]
    }

@app.get("/Plone/@search")
async def search(
    SearchableText: Optional[str] = None,
    b_size: int = 10,
    plone_user: Optional[str] = Header(None)
):
    """Mock Plone search endpoint"""
    await asyncio.sleep(0.05 + random.random() * 0.05)
    return {
        "@id": "http://localhost:8080/Plone/@search",
        "items": [
            {
                "@id": f"http://localhost:8080/Plone/result-{i}",
                "@type": "Document",
                "title": f"Search result {i}",
                "description": f"Mock result for query: {SearchableText}"
            }
            for i in range(min(b_size, 5))
        ],
        "items_total": 42
    }

@app.get("/Plone/{path:path}")
async def catch_all(path: str):
    """Catch all other Plone paths"""
    return {"@id": f"http://localhost:8080/Plone/{path}", "title": "Mock Content"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)