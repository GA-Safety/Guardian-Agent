"""
Unit tests for URL extraction utility
"""
import pytest
from app.utils.url_extractor import (
    extract_urls,
    is_shortened_url,
    normalize_url_for_classification,
)


class TestExtractUrls:
    """Test URL extraction from text"""

    def test_extract_http_urls(self):
        """Test extraction of HTTP/HTTPS URLs"""
        text = "Visit http://example.com or https://secure.example.com/path"
        urls = extract_urls(text)
        assert len(urls) == 2
        assert "http://example.com" in urls
        assert "https://secure.example.com/path" in urls

    def test_extract_www_urls(self):
        """Test extraction of www URLs without protocol"""
        text = "Check www.example.com for more info"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert urls[0] == "http://www.example.com"

    def test_extract_shortened_urls(self):
        """Test extraction of shortened URLs"""
        text = "Click bit.ly/abc123 or t.co/xyz789"
        urls = extract_urls(text)
        assert len(urls) == 2
        assert any("bit.ly/abc123" in url for url in urls)
        assert any("t.co/xyz789" in url for url in urls)

    def test_extract_urls_with_query_params(self):
        """Test extraction of URLs with query parameters"""
        text = "Login at https://example.com/login?redirect=/dashboard&token=abc"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert "redirect=/dashboard" in urls[0]
        assert "token=abc" in urls[0]

    def test_no_urls(self):
        """Test text with no URLs"""
        text = "This is just plain text with no links"
        urls = extract_urls(text)
        assert len(urls) == 0

    def test_deduplicate_urls(self):
        """Test that duplicate URLs are removed"""
        text = "Visit http://example.com and http://example.com again"
        urls = extract_urls(text)
        assert len(urls) == 1

    def test_multiple_url_types(self):
        """Test text with multiple URL types"""
        text = (
            "Visit https://example.com, www.test.com, or use bit.ly/short "
            "for quick access"
        )
        urls = extract_urls(text)
        assert len(urls) == 3


class TestIsShortenedUrl:
    """Test shortened URL detection"""

    def test_bitly_url(self):
        """Test bit.ly detection"""
        assert is_shortened_url("http://bit.ly/abc123") is True

    def test_tinyurl(self):
        """Test tinyurl detection"""
        assert is_shortened_url("http://tinyurl.com/xyz") is True

    def test_twitter_shortener(self):
        """Test t.co detection"""
        assert is_shortened_url("http://t.co/abc") is True

    def test_normal_url(self):
        """Test that normal URLs are not flagged as shortened"""
        assert is_shortened_url("http://example.com/path") is False
        assert is_shortened_url("https://google.com") is False

    def test_invalid_url(self):
        """Test handling of invalid URLs"""
        assert is_shortened_url("not a url") is False
        assert is_shortened_url("") is False


class TestNormalizeUrlForClassification:
    """Test URL normalization for ML models"""

    def test_remove_protocol(self):
        """Test protocol removal"""
        url = "https://example.com/path"
        normalized = normalize_url_for_classification(url)
        assert "https://" not in normalized
        assert "example.com/path" in normalized

    def test_preserve_path(self):
        """Test that path is preserved"""
        url = "http://example.com/login/secure"
        normalized = normalize_url_for_classification(url)
        assert "/login/secure" in normalized

    def test_invalid_url_passthrough(self):
        """Test that invalid URLs are passed through unchanged"""
        url = "not-a-url"
        normalized = normalize_url_for_classification(url)
        assert normalized == url


class TestRealWorldScamSamples:
    """Test URL extraction with real-world scam patterns"""

    def test_bank_phishing_sms(self):
        """Test URL extraction from bank phishing SMS"""
        text = (
            "ALERT: Your account has been locked. "
            "Verify immediately at https://secure-bank-login.tk/verify"
        )
        urls = extract_urls(text)
        assert len(urls) == 1
        assert "secure-bank-login.tk" in urls[0]

    def test_shortened_url_scam(self):
        """Test shortened URL in scam message"""
        text = "You've won! Claim your prize at bit.ly/prize123"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert is_shortened_url(urls[0]) is True

    def test_multiple_suspicious_urls(self):
        """Test message with multiple suspicious URLs"""
        text = (
            "Update your payment at www.paypal-secure.tk or "
            "click bit.ly/update for mobile"
        )
        urls = extract_urls(text)
        assert len(urls) == 2
