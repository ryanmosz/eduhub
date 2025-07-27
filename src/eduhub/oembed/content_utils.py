"""
Content transformation utilities for oEmbed integration.

Provides functions to detect and transform media URLs into rich embeds within HTML content.
Supports auto-detection of YouTube, Twitter, Vimeo, and other oEmbed provider URLs.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .client import get_oembed_client

logger = logging.getLogger(__name__)

# URL patterns for media providers (case-insensitive)
MEDIA_URL_PATTERNS = [
    # YouTube
    (
        r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)",
        "youtube.com",
    ),
    # Twitter/X
    (r"https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)", "twitter.com"),
    # Vimeo
    (r"https?://(?:www\.)?vimeo\.com/(\d+)", "vimeo.com"),
    # Instagram
    (r"https?://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)", "instagram.com"),
    # TikTok
    (r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/(\d+)", "tiktok.com"),
    # Spotify
    (
        r"https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)",
        "spotify.com",
    ),
    # SoundCloud
    (r"https?://soundcloud\.com/[\w-]+/[\w-]+", "soundcloud.com"),
    # CodePen
    (r"https?://codepen\.io/[\w-]+/pen/([a-zA-Z0-9]+)", "codepen.io"),
    # SlideShare
    (r"https?://(?:www\.)?slideshare\.net/[\w-]+/[\w-]+", "slideshare.net"),
    # Flickr
    (r"https?://(?:www\.)?flickr\.com/photos/[\w@-]+/(\d+)", "flickr.com"),
]

# Compile regex patterns for performance
COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), domain)
    for pattern, domain in MEDIA_URL_PATTERNS
]


def detect_media_urls(text: str) -> list[tuple[str, str, int, int]]:
    """
    Detect media URLs in text content.

    Args:
        text: Text content to scan for media URLs

    Returns:
        List of tuples: (url, domain, start_pos, end_pos)
    """
    found_urls = []

    for pattern, domain in COMPILED_PATTERNS:
        for match in pattern.finditer(text):
            url = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            found_urls.append((url, domain, start_pos, end_pos))

    # Sort by position to process from end to beginning (prevents index shifting)
    found_urls.sort(key=lambda x: x[2], reverse=True)

    return found_urls


async def inject_oembed(
    html: str, maxwidth: Optional[int] = None, maxheight: Optional[int] = None
) -> str:
    """
    Replace media URLs in HTML content with oEmbed iframe embeds.

    Args:
        html: HTML content to process
        maxwidth: Maximum width for embeds (optional)
        maxheight: Maximum height for embeds (optional)

    Returns:
        HTML content with URLs replaced by embed iframes

    Example:
        Input:  "Check out this video: https://youtube.com/watch?v=dQw4w9WgXcQ"
        Output: "Check out this video: <iframe src='...' width='560' height='315'></iframe>"
    """
    if not html or not html.strip():
        return html

    # Detect media URLs
    media_urls = detect_media_urls(html)

    if not media_urls:
        return html  # No media URLs found

    # Get oEmbed client
    client = await get_oembed_client()

    # Process URLs (reverse order to maintain text positions)
    processed_html = html
    successful_embeds = 0

    for url, domain, start_pos, end_pos in media_urls:
        try:
            # Check if URL is in a link tag already
            before_text = processed_html[:start_pos]
            after_text = processed_html[end_pos:]

            # Skip if URL is already inside an HTML tag
            if _is_url_in_tag(before_text, after_text):
                logger.debug(f"Skipping URL already in HTML tag: {url}")
                continue

            # Fetch oEmbed data
            embed_data = await client.fetch_embed(url, maxwidth, maxheight)

            if embed_data and embed_data.get("html"):
                # Replace URL with embed HTML
                embed_html = embed_data["html"]

                # Add some styling for better integration
                styled_embed = f'<div class="oembed-embed" data-provider="{domain}">{embed_html}</div>'

                # Replace the URL with the embed
                processed_html = (
                    processed_html[:start_pos] + styled_embed + processed_html[end_pos:]
                )

                successful_embeds += 1
                logger.info(f"Successfully embedded {domain} URL: {url}")
            else:
                logger.warning(f"Failed to get embed data for URL: {url}")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            # Continue processing other URLs
            continue

    logger.info(
        f"Processed {len(media_urls)} media URLs, {successful_embeds} successful embeds"
    )
    return processed_html


def _is_url_in_tag(before_text: str, after_text: str) -> bool:
    """
    Check if a URL is already inside an HTML tag (like <a href="...">).

    Args:
        before_text: Text before the URL
        after_text: Text after the URL

    Returns:
        True if URL appears to be inside an HTML tag
    """
    # Look for unclosed tag before the URL
    last_open_bracket = before_text.rfind("<")
    last_close_bracket = before_text.rfind(">")

    # If there's an unclosed tag before the URL, check if it closes after
    if last_open_bracket > last_close_bracket:
        # Look for closing bracket after the URL
        next_close_bracket = after_text.find(">")
        if next_close_bracket != -1:
            return True  # URL is inside a tag

    # Additional check for href attributes
    if "href=" in before_text[-50:] and '"' in after_text[:10]:
        return True

    return False


async def inject_oembed_batch(
    html_contents: list[str],
    maxwidth: Optional[int] = None,
    maxheight: Optional[int] = None,
) -> list[str]:
    """
    Process multiple HTML contents in parallel for better performance.

    Args:
        html_contents: List of HTML content strings to process
        maxwidth: Maximum width for embeds (optional)
        maxheight: Maximum height for embeds (optional)

    Returns:
        List of processed HTML contents with embeds injected
    """
    if not html_contents:
        return []

    # Process all contents in parallel
    tasks = [inject_oembed(html, maxwidth, maxheight) for html in html_contents]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error processing HTML content {i}: {result}")
            processed_results.append(html_contents[i])  # Return original on error
        else:
            processed_results.append(result)

    return processed_results


def extract_plain_urls(text: str) -> list[str]:
    """
    Extract plain URLs that are not already in HTML tags.

    Args:
        text: Text to extract URLs from

    Returns:
        List of plain URLs found in text
    """
    urls = []

    for pattern, domain in COMPILED_PATTERNS:
        for match in pattern.finditer(text):
            url = match.group(0)
            start_pos = match.start()
            end_pos = match.end()

            # Check if URL is in a tag
            before_text = text[:start_pos]
            after_text = text[end_pos:]

            if not _is_url_in_tag(before_text, after_text):
                urls.append(url)

    return urls


def get_supported_domains() -> list[str]:
    """
    Get list of supported media domains for oEmbed injection.

    Returns:
        List of domain names supported by the oEmbed service
    """
    return [domain for _, domain in MEDIA_URL_PATTERNS]


# Configuration for content injection
INJECTION_CONFIG = {
    "default_maxwidth": 800,
    "default_maxheight": 600,
    "enable_batch_processing": True,
    "skip_existing_embeds": True,
    "add_wrapper_div": True,
    "log_successful_embeds": True,
}
