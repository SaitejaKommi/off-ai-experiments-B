"""Configuration for Open Food Facts instance/domain behavior."""

from __future__ import annotations

import os
from urllib.parse import quote_plus
from urllib.parse import urlparse


def _clean_domain(value: str) -> str:
    return value.strip().rstrip("/")


# Default to the Canada OFF instance.
OFF_INSTANCE_DOMAIN = _clean_domain(
    os.getenv("OFF_INSTANCE_DOMAIN", "https://ca.openfoodfacts.org")
)

# Canonical product URL prefix used across recommendation outputs and API payloads.
BASE_OFF_URL = f"{OFF_INSTANCE_DOMAIN}/product/"

# Canonical Canada tag used in OFF arrays such as countries_tags.
OFF_COUNTRY_TAG = os.getenv("OFF_COUNTRY_TAG", "en:canada").strip().lower()


def build_product_search_url(barcode: str) -> str:
    """Build a Canada OFF search URL that resolves to the canonical product page."""
    clean_barcode = str(barcode or "").strip()
    if not clean_barcode:
        return ""
    return (
        f"{OFF_INSTANCE_DOMAIN}/cgi/search.pl?search_terms="
        f"{quote_plus(clean_barcode)}&search_simple=1&action=process"
    )


def normalise_off_product_url(
    url: str | None,
    barcode: str,
    product_name: str | None = None,
) -> str:
    """Normalize an OFF product URL to the configured instance while preserving slug."""
    fallback_url = build_product_search_url(barcode)
    if not fallback_url:
        return ""

    if not url:
        return fallback_url

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return fallback_url

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "product" and parts[1] == str(barcode).strip():
        slug = "/".join(parts[2:]).strip("/")
        if slug:
            return f"{BASE_OFF_URL}{barcode}/{slug}"

    return fallback_url
