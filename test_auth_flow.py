#!/usr/bin/env python3
"""Test the authentication flow programmatically."""

import asyncio
import httpx
from urllib.parse import urlparse, parse_qs

async def test_auth_flow():
    """Test the complete OAuth flow."""
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        # 1. Test the frontend is running
        print("1. Testing frontend at http://localhost:8001...")
        try:
            response = await client.get("http://localhost:8001")
            print(f"   ✓ Frontend is running: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Frontend error: {e}")
            return
        
        # 2. Test auth status endpoint
        print("\n2. Testing auth status endpoint...")
        response = await client.get("http://localhost:8000/auth/status")
        auth_status = response.json()
        print(f"   ✓ Auth status: {auth_status}")
        
        # 3. Test login redirect
        print("\n3. Testing login redirect...")
        response = await client.get(
            "http://localhost:8000/auth/login",
            params={"return_to": "http://localhost:8001/callback"}
        )
        if response.status_code == 302:
            auth0_url = response.headers.get("location", "")
            print(f"   ✓ Redirects to Auth0: {auth0_url[:50]}...")
            
            # Parse the Auth0 URL
            parsed = urlparse(auth0_url)
            params = parse_qs(parsed.query)
            print(f"   ✓ Client ID: {params.get('client_id', ['N/A'])[0]}")
            print(f"   ✓ Redirect URI: {params.get('redirect_uri', ['N/A'])[0]}")
            print(f"   ✓ Response Type: {params.get('response_type', ['N/A'])[0]}")
        else:
            print(f"   ✗ Unexpected status: {response.status_code}")
        
        # 4. Test API endpoints that should be protected
        print("\n4. Testing protected endpoints...")
        endpoints = [
            "/api/user",
            "/import/schedule", 
            "/embed",
            "/data/content"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"http://localhost:8000{endpoint}")
                if response.status_code == 401:
                    print(f"   ✓ {endpoint} - Protected (401)")
                elif response.status_code == 404:
                    print(f"   ? {endpoint} - Not Found (404)")
                else:
                    print(f"   ! {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"   ✗ {endpoint} - Error: {e}")
        
        # 5. Test backend health
        print("\n5. Testing backend health...")
        response = await client.get("http://localhost:8000/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ API Version: {data.get('version')}")
            print(f"   ✓ Status: {data.get('status')}")
            print("   ✓ Services available:")
            for service, path in data.get('services', {}).items():
                print(f"      - {service}: {path}")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())