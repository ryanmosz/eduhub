"""
Async HTTP client for oEmbed provider integration.

Handles fetching oEmbed JSON from various providers like YouTube, Vimeo, Twitter, etc.
Includes provider endpoint resolution, response caching, and error handling.
"""

import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse

import bleach
import httpx
from fastapi import HTTPException

from .cache import get_oembed_cache

# Provider endpoint configurations
OEMBED_PROVIDERS = {
    "youtube.com": {
        "endpoint": "https://www.youtube.com/oembed",
        "name": "YouTube",
        "supports_https": True,
        "max_width": 1920,
        "max_height": 1080,
    },
    "youtu.be": {
        "endpoint": "https://www.youtube.com/oembed",
        "name": "YouTube",
        "supports_https": True,
        "max_width": 1920,
        "max_height": 1080,
    },
    "vimeo.com": {
        "endpoint": "https://vimeo.com/api/oembed.json",
        "name": "Vimeo",
        "supports_https": True,
        "max_width": 1920,
        "max_height": 1080,
    },
    "twitter.com": {
        "endpoint": "https://publish.twitter.com/oembed",
        "name": "Twitter",
        "supports_https": True,
        "max_width": 550,
        "max_height": None,
    },
    "x.com": {
        "endpoint": "https://publish.twitter.com/oembed",
        "name": "Twitter/X",
        "supports_https": True,
        "max_width": 550,
        "max_height": None,
    },
    "instagram.com": {
        "endpoint": "https://graph.facebook.com/v8.0/instagram_oembed",
        "name": "Instagram",
        "supports_https": True,
        "max_width": 658,
        "max_height": None,
    },
    "soundcloud.com": {
        "endpoint": "https://soundcloud.com/oembed",
        "name": "SoundCloud",
        "supports_https": True,
        "max_width": 1920,
        "max_height": 400,
    },
    "spotify.com": {
        "endpoint": "https://open.spotify.com/oembed",
        "name": "Spotify",
        "supports_https": True,
        "max_width": 1000,
        "max_height": 600,
    },
    "codepen.io": {
        "endpoint": "https://codepen.io/api/oembed",
        "name": "CodePen",
        "supports_https": True,
        "max_width": 1000,
        "max_height": 600,
    },
    "github.com": {
        "endpoint": "https://github.com/api/oembed",
        "name": "GitHub",
        "supports_https": True,
        "max_width": 1000,
        "max_height": 400,
    },
}

# HTML sanitization configuration
ALLOWED_TAGS = [
    "iframe",
    "div",
    "span",
    "p",
    "br",
    "a",
    "img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "cite",
    "code",
    "pre",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "small",
    "ul",
    "ol",
    "li",
    "dl",
    "dt",
    "dd",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class", "id"],
    "iframe": [
        "src",
        "width",
        "height",
        "frameborder",
        "allowfullscreen",
        "sandbox",
        "allow",
    ],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height", "title"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


class OEmbedClient:
    """Async HTTP client for oEmbed provider integration."""

    def __init__(self, timeout: float = 10.0):
        """Initialize the oEmbed client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "User-Agent": "EduHub-oEmbed/1.0 (Educational Portal)",
                    "Accept": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def get_provider_config(self, domain: str) -> dict[str, Any]:
        """Get provider configuration for a domain.

        Args:
            domain: Normalized domain name (e.g., 'youtube.com')

        Returns:
            Provider configuration dictionary

        Raises:
            HTTPException: If provider is not supported
        """
        if domain not in OEMBED_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Unsupported provider",
                    "message": f"No oEmbed configuration found for domain: {domain}",
                    "supported_providers": list(OEMBED_PROVIDERS.keys()),
                },
            )
        return OEMBED_PROVIDERS[domain]

    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML content using bleach.

        Args:
            html: Raw HTML content from oEmbed provider

        Returns:
            Sanitized HTML safe for embedding
        """
        # First pass: Clean with allowed tags, strip disallowed ones completely
        cleaned = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,  # Remove disallowed tags but keep content
            strip_comments=True,
        )

        # Second pass: Remove any remaining script content that might be left
        # This handles cases where script content is left behind
        import re

        # Remove any remaining script-like content
        cleaned = re.sub(
            r"<script[^>]*>.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(r"javascript:", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r"on\w+\s*=", "", cleaned, flags=re.IGNORECASE
        )  # Remove event handlers

        return cleaned

    async def fetch_embed(
        self, url: str, maxwidth: Optional[int] = None, maxheight: Optional[int] = None
    ) -> dict[str, Any]:
        """Fetch oEmbed data from provider with caching.

        Args:
            url: URL to embed
            maxwidth: Maximum width for embed
            maxheight: Maximum height for embed

        Returns:
            oEmbed response data with sanitized HTML

        Raises:
            HTTPException: For HTTP errors, timeouts, or invalid responses
        """
        # Check cache first
        cache = await get_oembed_cache()
        cached_response = await cache.get(url, maxwidth, maxheight)
        if cached_response:
            return cached_response

        # Parse domain from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Get provider configuration
        provider_config = self.get_provider_config(domain)

        # Apply provider-specific size limits
        if maxwidth and provider_config.get("max_width"):
            maxwidth = min(maxwidth, provider_config["max_width"])
        if maxheight and provider_config.get("max_height"):
            maxheight = min(maxheight, provider_config["max_height"])

        # Build oEmbed request URL
        params = {"url": url, "format": "json"}
        if maxwidth:
            params["maxwidth"] = maxwidth
        if maxheight:
            params["maxheight"] = maxheight

        oembed_url = f"{provider_config['endpoint']}?{urlencode(params)}"

        # Fetch oEmbed data
        client = await self._get_client()
        try:
            response = await client.get(oembed_url)
            response.raise_for_status()

            oembed_data = response.json()

            # Validate required fields
            if "html" not in oembed_data and "type" not in oembed_data:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error": "Invalid oEmbed response",
                        "message": "Provider returned response without 'html' or 'type' field",
                        "provider": provider_config["name"],
                    },
                )

            # Sanitize HTML content
            if "html" in oembed_data:
                oembed_data["html"] = self.sanitize_html(oembed_data["html"])

            # Add provider information
            oembed_data["provider_name"] = provider_config["name"]
            oembed_data["cached"] = False  # Fresh from provider

            # Cache the response
            await cache.set(url, oembed_data, maxwidth, maxheight)

            return oembed_data

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Provider timeout",
                    "message": f"Request to {provider_config['name']} timed out after {self.timeout}s",
                    "provider": provider_config["name"],
                },
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "Provider error",
                    "message": f"{provider_config['name']} returned HTTP {e.response.status_code}",
                    "provider": provider_config["name"],
                    "status_code": e.response.status_code,
                },
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "Network error",
                    "message": f"Failed to connect to {provider_config['name']}: {str(e)}",
                    "provider": provider_config["name"],
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Unexpected error",
                    "message": f"Unexpected error while fetching oEmbed data: {str(e)}",
                    "provider": provider_config["name"],
                },
            )


# Global client instance
_oembed_client: Optional[OEmbedClient] = None


async def get_oembed_client() -> OEmbedClient:
    """Get or create the global oEmbed client instance."""
    global _oembed_client
    if _oembed_client is None:
        _oembed_client = OEmbedClient()
    return _oembed_client


async def cleanup_oembed_client():
    """Clean up the global oEmbed client and cache."""
    global _oembed_client
    if _oembed_client:
        await _oembed_client.close()
        _oembed_client = None

    # Also cleanup the cache
    from .cache import cleanup_oembed_cache

    await cleanup_oembed_cache()
