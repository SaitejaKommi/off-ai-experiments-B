"""Fetch product data from the Open Food Facts API."""

import urllib.request
import json
from typing import Optional

_API_BASE = "https://world.openfoodfacts.org/api/v2/product/{barcode}?fields=product_name,nutriscore_grade,nova_group,nutriments,ingredients_text,categories,categories_tags,labels,labels_tags,additives_tags,allergens_tags,image_url"

_FIELDS = [
    "product_name",
    "nutriscore_grade",
    "nova_group",
    "nutriments",
    "ingredients_text",
    "categories",
    "categories_tags",
    "labels",
    "labels_tags",
    "additives_tags",
    "allergens_tags",
    "image_url",
]


def _barcode_from_url(url: str) -> str:
    """Extract a barcode from an OFF product URL like
    https://world.openfoodfacts.org/product/0068100084245/...
    """
    for part in url.rstrip("/").split("/"):
        if part.isdigit():
            return part
    raise ValueError(f"Could not extract barcode from URL: {url}")


def fetch_product(barcode_or_url: str) -> dict:
    """Fetch and return a normalised product dictionary.

    Parameters
    ----------
    barcode_or_url:
        Either a numeric barcode string (e.g. ``"0068100084245"``) or a full
        Open Food Facts product URL.

    Returns
    -------
    dict
        Normalised product dictionary with the fields listed in ``_FIELDS``.

    Raises
    ------
    ValueError
        If the product is not found or the API returns an error.
    """
    if barcode_or_url.startswith("http"):
        barcode = _barcode_from_url(barcode_or_url)
    else:
        barcode = barcode_or_url.strip()

    url = _API_BASE.format(barcode=barcode)
    req = urllib.request.Request(url, headers={"User-Agent": "off-ai-experiments-B/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode())

    if data.get("status") == 0 or data.get("status_verbose") == "product not found":
        raise ValueError(f"Product not found for barcode: {barcode}")

    product = data.get("product", {})
    product["_barcode"] = barcode
    return product
