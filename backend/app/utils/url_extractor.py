"""
URL Extraction Utility

Robust URL extraction from SMS messages using regex.
"""
import re
from typing import List
from urllib.parse import urlparse


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text using comprehensive regex patterns.

    Handles:
    - Standard HTTP/HTTPS URLs
    - URLs without protocol (www.example.com)
    - Shortened URLs
    - URLs with query parameters and fragments

    Args:
        text: SMS message text to extract URLs from

    Returns:
        List of extracted URLs (deduplicated)
    """
    urls = []

    # Pattern 1: Standard HTTP/HTTPS URLs
    http_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls.extend(re.findall(http_pattern, text, re.IGNORECASE))

    # Pattern 2: www.example.com (without protocol)
    www_pattern = r'www\.[a-zA-Z0-9][-a-zA-Z0-9]*[a-zA-Z0-9]\.[^\s<>"{}|\\^`\[\]]+'
    www_urls = re.findall(www_pattern, text, re.IGNORECASE)
    urls.extend([f"http://{url}" for url in www_urls])

    # Pattern 3: Common shortened domains without www
    # bit.ly, t.co, tinyurl.com, etc.
    short_pattern = r'\b(bit\.ly|t\.co|tinyurl\.com|goo\.gl|ow\.ly|is\.gd|buff\.ly|short\.link)/[a-zA-Z0-9_-]+'
    short_urls = re.findall(short_pattern, text, re.IGNORECASE)
    urls.extend([f"http://{url}" for url in short_urls])

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        # Normalize URL for comparison
        normalized = url.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique_urls.append(url)

    return unique_urls


def is_shortened_url(url: str) -> bool:
    """
    Check if a URL uses a known URL shortening service.

    Args:
        url: URL to check

    Returns:
        True if URL is from a known shortening service
    """
    shortening_domains = [
        'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
        'is.gd', 'buff.ly', 'short.link', 'tiny.cc', 'tr.im',
    ]

    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc or parsed.path.split('/')[0]
        return any(short_domain in domain for short_domain in shortening_domains)
    except Exception:
        return False


def normalize_url_for_classification(url: str) -> str:
    """
    Normalize URL for ML model input.

    Some URL classification models expect just the domain and path,
    without protocol or query parameters.

    Args:
        url: URL to normalize

    Returns:
        Normalized URL string
    """
    try:
        parsed = urlparse(url)
        # Reconstruct with just domain and path
        normalized = f"{parsed.netloc}{parsed.path}"
        return normalized if normalized else url
    except Exception:
        return url
