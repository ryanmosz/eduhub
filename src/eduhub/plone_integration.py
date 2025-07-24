"""
FastAPI-Plone Integration Layer

This module provides the HTTP bridge between our modern FastAPI application
and the legacy Plone CMS instance. It handles authentication, content access,
and data transformation between the two systems.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PloneConfig(BaseModel):
    """Configuration for Plone instance connection."""

    base_url: str = Field(
        default="http://localhost:8080/Plone", description="Base URL of Plone instance"
    )
    username: str = Field(default="admin", description="Plone admin username")
    password: str = Field(default="admin", description="Plone admin password")
    timeout: int = Field(default=30, description="HTTP timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class PloneContent(BaseModel):
    """Standardized representation of Plone content."""

    uid: str = Field(description="Unique content identifier")
    title: str = Field(description="Content title")
    description: Optional[str] = Field(default=None, description="Content description")
    portal_type: str = Field(description="Plone content type")
    url: str = Field(description="Content URL")
    created: Optional[str] = Field(default=None, description="Creation timestamp")
    modified: Optional[str] = Field(default=None, description="Modification timestamp")
    state: Optional[str] = Field(default=None, description="Workflow state")
    text: Optional[str] = Field(default=None, description="Content body text")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class PloneAPIError(Exception):
    """Custom exception for Plone API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PloneClient:
    """HTTP client for communicating with Plone CMS."""

    def __init__(self, config: Optional[PloneConfig] = None):
        """Initialize Plone client with configuration."""
        self.config = config or PloneConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._auth_token: Optional[str] = None

        # Load configuration from environment if available
        if os.getenv("PLONE_URL"):
            self.config.base_url = os.getenv("PLONE_URL")
        if os.getenv("PLONE_USERNAME"):
            self.config.username = os.getenv("PLONE_USERNAME")
        if os.getenv("PLONE_PASSWORD"):
            self.config.password = os.getenv("PLONE_PASSWORD")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Establish connection to Plone instance."""
        if self._client is None:
            logger.info(f"Connecting to Plone at {self.config.base_url}")

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                follow_redirects=True,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "EduHub-FastAPI-Integration/1.0",
                },
            )

            # Authenticate with Plone
            await self._authenticate()

    async def close(self) -> None:
        """Close connection to Plone instance."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._auth_token = None
            logger.info("Closed Plone connection")

    async def _authenticate(self) -> None:
        """Authenticate with Plone using basic auth."""
        try:
            auth_url = urljoin(self.config.base_url, "/@login")
            auth_data = {
                "login": self.config.username,
                "password": self.config.password,
            }

            logger.debug(f"Authenticating with Plone at {auth_url}")
            response = await self._client.post(auth_url, json=auth_data)

            if response.status_code == 200:
                auth_result = await response.json()
                self._auth_token = auth_result.get("token")

                if self._auth_token:
                    # Add token to client headers for subsequent requests
                    self._client.headers["Authorization"] = f"Bearer {self._auth_token}"
                    logger.info("Successfully authenticated with Plone")
                else:
                    logger.warning(
                        "Plone authentication succeeded but no token received"
                    )
            else:
                logger.error(
                    f"Plone authentication failed: {response.status_code} - {response.text}"
                )
                response_data = None
                if response.content:
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_data = response.text

                raise PloneAPIError(
                    f"Authentication failed: {response.status_code}",
                    status_code=response.status_code,
                    response_data=response_data,
                )

        except httpx.RequestError as e:
            logger.error(f"Network error during Plone authentication: {e}")
            raise PloneAPIError(f"Network error during authentication: {e}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make authenticated request to Plone API."""
        if not self._client:
            await self.connect()

        url = urljoin(self.config.base_url, endpoint)

        try:
            logger.debug(f"Making {method} request to {url}")
            response = await self._client.request(
                method=method, url=url, params=params, json=json_data, **kwargs
            )

            # Handle authentication errors
            if response.status_code == 401:
                logger.warning("Plone request returned 401, re-authenticating...")
                await self._authenticate()
                # Retry the request
                response = await self._client.request(
                    method=method, url=url, params=params, json=json_data, **kwargs
                )

            response.raise_for_status()
            return response

        except httpx.RequestError as e:
            logger.error(f"Network error during Plone request: {e}")
            raise PloneAPIError(f"Network error: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during Plone request: {e.response.status_code} - {e.response.text}"
            )
            response_data = None
            if e.response.content:
                try:
                    response_data = await e.response.json()
                except Exception:
                    response_data = e.response.text

            raise PloneAPIError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                response_data=response_data,
            )

    async def get_content(self, path: str = "") -> Dict[str, Any]:
        """Get content from Plone by path."""
        endpoint = f"/{path.lstrip('/')}" if path else ""
        response = await self._request("GET", endpoint)
        return await response.json()

    async def search_content(
        self,
        query: Optional[str] = None,
        portal_type: Optional[Union[str, List[str]]] = None,
        path: Optional[str] = None,
        limit: int = 25,
        start: int = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Search for content in Plone."""
        params = {
            "b_size": limit,
            "b_start": start,
        }

        if query:
            params["SearchableText"] = query
        if portal_type:
            if isinstance(portal_type, list):
                params["portal_type"] = portal_type
            else:
                params["portal_type"] = [portal_type]
        if path:
            params["path"] = path

        # Add any additional search parameters
        params.update(kwargs)

        response = await self._request("GET", "/@search", params=params)
        return await response.json()

    async def create_content(
        self, parent_path: str, portal_type: str, title: str, **kwargs
    ) -> Dict[str, Any]:
        """Create new content in Plone."""
        endpoint = f"/{parent_path.lstrip('/')}"

        content_data = {
            "@type": portal_type,
            "title": title,
        }
        content_data.update(kwargs)

        response = await self._request("POST", endpoint, json_data=content_data)
        return await response.json()

    async def update_content(self, path: str, **kwargs) -> Dict[str, Any]:
        """Update existing content in Plone."""
        endpoint = f"/{path.lstrip('/')}"
        response = await self._request("PATCH", endpoint, json_data=kwargs)
        return await response.json()

    async def delete_content(self, path: str) -> bool:
        """Delete content from Plone."""
        endpoint = f"/{path.lstrip('/')}"
        response = await self._request("DELETE", endpoint)
        return response.status_code == 204

    async def get_site_info(self) -> Dict[str, Any]:
        """Get basic information about the Plone site."""
        response = await self._request("GET", "/")
        return await response.json()


def transform_plone_content(plone_data: Dict[str, Any]) -> PloneContent:
    """Transform raw Plone API response into standardized PloneContent model."""
    return PloneContent(
        uid=plone_data.get("UID", ""),
        title=plone_data.get("title", ""),
        description=plone_data.get("description"),
        portal_type=plone_data.get("@type", plone_data.get("portal_type", "")),
        url=plone_data.get("@id", ""),
        created=plone_data.get("created"),
        modified=plone_data.get("modified"),
        state=plone_data.get("review_state"),
        text=plone_data.get("text", {}).get("data") if plone_data.get("text") else None,
        metadata={
            k: v
            for k, v in plone_data.items()
            if k
            not in [
                "UID",
                "title",
                "description",
                "@type",
                "portal_type",
                "@id",
                "created",
                "modified",
                "review_state",
                "text",
            ]
        },
    )


# Singleton instance for application use
_plone_client: Optional[PloneClient] = None


async def get_plone_client() -> PloneClient:
    """Get or create singleton Plone client instance."""
    global _plone_client

    if _plone_client is None:
        _plone_client = PloneClient()
        await _plone_client.connect()

    return _plone_client


async def close_plone_client() -> None:
    """Close singleton Plone client instance."""
    global _plone_client

    if _plone_client:
        await _plone_client.close()
        _plone_client = None
