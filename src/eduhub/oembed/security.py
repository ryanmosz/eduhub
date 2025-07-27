"""
Security utilities for oEmbed service.

Task 5.4.1: HTML sanitization (bleach) and domain allow/deny lists.
Provides comprehensive security controls for oEmbed content processing.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import bleach

logger = logging.getLogger(__name__)

# Domain security configuration
ALLOWED_DOMAINS = {
    # Video platforms
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "dailymotion.com",
    "twitch.tv",
    # Social media
    "twitter.com",
    "x.com",
    "instagram.com",
    "facebook.com",
    "linkedin.com",
    # Audio platforms
    "spotify.com",
    "soundcloud.com",
    "bandcamp.com",
    # Development/Code
    "github.com",
    "codepen.io",
    "codesandbox.io",
    "jsfiddle.net",
    # Presentation/Document
    "slideshare.net",
    "speakerdeck.com",
    "flickr.com",
    # Short video
    "tiktok.com",
    "vine.co",
}

DENIED_DOMAINS = {
    # Known malicious domains (example list)
    "malicious-site.com",
    "phishing-example.com",
    "spam-domain.net",
    # Local/private networks (security risk)
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "192.168.0.1",
    "10.0.0.1",
    "172.16.0.1",
    "internal.company.com",
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
    "*": ["class", "id", "data-*"],
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
    "div": ["class", "id", "data-*"],
    "span": ["class", "id", "data-*"],
}

ALLOWED_PROTOCOLS = ["http", "https"]

# Security patterns for additional protection
DANGEROUS_PATTERNS = [
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(
        r"data:(?!image/)", re.IGNORECASE
    ),  # Allow data images but block other data URLs
    re.compile(r"vbscript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # Event handlers like onclick, onload
    re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<object[^>]*>.*?</object>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<embed[^>]*>", re.IGNORECASE),
    re.compile(r"<applet[^>]*>.*?</applet>", re.DOTALL | re.IGNORECASE),
]


class OEmbedSecurityManager:
    """
    Comprehensive security manager for oEmbed content processing.

    Features:
    - Domain allow/deny list validation
    - HTML sanitization with bleach
    - Additional pattern-based security checks
    - Configurable security policies
    """

    def __init__(
        self,
        allowed_domains: Optional[set[str]] = None,
        denied_domains: Optional[set[str]] = None,
        strict_mode: bool = True,
    ):
        """
        Initialize security manager.

        Args:
            allowed_domains: Set of allowed domains (None uses default)
            denied_domains: Set of explicitly denied domains (None uses default)
            strict_mode: If True, only allow explicitly listed domains
        """
        self.allowed_domains = allowed_domains or ALLOWED_DOMAINS.copy()
        self.denied_domains = denied_domains or DENIED_DOMAINS.copy()
        self.strict_mode = strict_mode

    def is_domain_allowed(self, url: str) -> bool:
        """
        Check if domain is allowed for oEmbed processing.

        Args:
            url: URL to check

        Returns:
            bool: True if domain is allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix for comparison
            if domain.startswith("www."):
                domain = domain[4:]

            # Check deny list first (takes precedence)
            if domain in self.denied_domains:
                logger.warning(f"Domain {domain} is explicitly denied")
                return False

            # Check if domain contains any denied patterns
            for denied_domain in self.denied_domains:
                if denied_domain in domain:
                    logger.warning(
                        f"Domain {domain} matches denied pattern {denied_domain}"
                    )
                    return False

            # In strict mode, only allow explicitly listed domains
            if self.strict_mode:
                allowed = domain in self.allowed_domains
                if not allowed:
                    # Check for parent domain matches
                    for allowed_domain in self.allowed_domains:
                        if (
                            domain.endswith("." + allowed_domain)
                            or domain == allowed_domain
                        ):
                            allowed = True
                            break

                if not allowed:
                    logger.info(f"Domain {domain} not in allowed list (strict mode)")

                return allowed

            # In permissive mode, allow unless explicitly denied
            return True

        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return False

    def sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML content to prevent XSS and other attacks.

        Args:
            html: Raw HTML content

        Returns:
            str: Sanitized HTML safe for display
        """
        if not html:
            return ""

        # First pass: Remove dangerous patterns
        cleaned = html
        for pattern in DANGEROUS_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # Second pass: Bleach sanitization
        cleaned = bleach.clean(
            cleaned,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True,
        )

        # Third pass: Additional security checks
        cleaned = self._additional_security_cleanup(cleaned)

        return cleaned

    def _additional_security_cleanup(self, html: str) -> str:
        """
        Additional security cleanup beyond basic sanitization.

        Args:
            html: Pre-sanitized HTML

        Returns:
            str: Further cleaned HTML
        """
        # Remove any remaining script content that might have slipped through
        html = re.sub(
            r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove javascript: and other dangerous protocols
        html = re.sub(r"javascript:", "", html, flags=re.IGNORECASE)
        html = re.sub(r"vbscript:", "", html, flags=re.IGNORECASE)
        html = re.sub(r"data:(?!image/)", "data:", html, flags=re.IGNORECASE)

        # Remove event handlers that might have been missed
        html = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', "", html, flags=re.IGNORECASE)
        html = re.sub(r"\son\w+\s*=\s*[^>\s]+", "", html, flags=re.IGNORECASE)

        # Remove style attributes with javascript
        html = re.sub(
            r'style\s*=\s*["\'][^"\']*expression\s*\([^"\']*["\']',
            "",
            html,
            flags=re.IGNORECASE,
        )

        return html

    def validate_oembed_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and sanitize oEmbed response data.

        Args:
            response_data: Raw oEmbed response

        Returns:
            Dict: Sanitized oEmbed response
        """
        if not response_data:
            return response_data

        # Sanitize HTML content
        if "html" in response_data:
            response_data["html"] = self.sanitize_html(response_data["html"])

        # Validate and sanitize URLs
        url_fields = ["url", "author_url", "provider_url", "thumbnail_url"]
        for field in url_fields:
            if field in response_data and response_data[field]:
                url = response_data[field]
                if not self._is_safe_url(url):
                    logger.warning(f"Removing unsafe URL from {field}: {url}")
                    response_data[field] = None

        # Sanitize text fields
        text_fields = ["title", "author_name", "provider_name", "description"]
        for field in text_fields:
            if field in response_data and response_data[field]:
                # Remove any HTML tags from text fields
                response_data[field] = bleach.clean(
                    response_data[field], tags=[], strip=True
                )

        return response_data

    def _is_safe_url(self, url: str) -> bool:
        """
        Check if URL is safe for inclusion in response.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is safe
        """
        try:
            parsed = urlparse(url)

            # Must use HTTPS or HTTP
            if parsed.scheme not in ["http", "https"]:
                return False

            # Check domain safety
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            # Avoid local/private network addresses
            local_patterns = [
                "localhost",
                "127.",
                "192.168.",
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
            ]
            for pattern in local_patterns:
                if pattern in domain:
                    return False

            return True

        except Exception:
            return False

    def add_allowed_domain(self, domain: str) -> None:
        """Add domain to allowed list."""
        self.allowed_domains.add(domain.lower())
        logger.info(f"Added {domain} to allowed domains")

    def add_denied_domain(self, domain: str) -> None:
        """Add domain to denied list."""
        self.denied_domains.add(domain.lower())
        logger.info(f"Added {domain} to denied domains")

    def remove_allowed_domain(self, domain: str) -> None:
        """Remove domain from allowed list."""
        self.allowed_domains.discard(domain.lower())
        logger.info(f"Removed {domain} from allowed domains")

    def remove_denied_domain(self, domain: str) -> None:
        """Remove domain from denied list."""
        self.denied_domains.discard(domain.lower())
        logger.info(f"Removed {domain} from denied domains")

    def get_security_report(self) -> dict[str, Any]:
        """
        Get security configuration report.

        Returns:
            Dict with security settings and statistics
        """
        return {
            "strict_mode": self.strict_mode,
            "allowed_domains_count": len(self.allowed_domains),
            "denied_domains_count": len(self.denied_domains),
            "allowed_domains": sorted(list(self.allowed_domains)),
            "denied_domains": sorted(list(self.denied_domains)),
            "allowed_tags_count": len(ALLOWED_TAGS),
            "dangerous_patterns_count": len(DANGEROUS_PATTERNS),
            "security_features": {
                "domain_filtering": True,
                "html_sanitization": True,
                "pattern_detection": True,
                "url_validation": True,
                "xss_protection": True,
            },
        }


# Global security manager instance
_security_manager: Optional[OEmbedSecurityManager] = None


def get_security_manager() -> OEmbedSecurityManager:
    """Get or create the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = OEmbedSecurityManager()
    return _security_manager


def is_domain_allowed(url: str) -> bool:
    """Check if domain is allowed for oEmbed processing."""
    return get_security_manager().is_domain_allowed(url)


def sanitize_html(html: str) -> str:
    """Sanitize HTML content using the global security manager."""
    return get_security_manager().sanitize_html(html)


def validate_oembed_response(response_data: dict[str, Any]) -> dict[str, Any]:
    """Validate and sanitize oEmbed response using the global security manager."""
    return get_security_manager().validate_oembed_response(response_data)
