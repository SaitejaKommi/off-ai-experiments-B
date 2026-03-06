"""Helper utilities for normalising and extracting product data."""

from typing import Any, Optional


def safe_float(value: Any, default: float = 0.0) -> float:
    """Return *value* as a float, or *default* if conversion fails."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Return *value* as an int, or *default* if conversion fails."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def extract_nutriment(nutriments: dict, key: str, per: str = "_100g") -> float:
    """Extract a nutriment value (per 100 g by default)."""
    return safe_float(nutriments.get(f"{key}{per}") or nutriments.get(key), 0.0)


def extract_allergens(product: dict) -> list[str]:
    """Return a deduplicated list of allergen names from a product dict."""
    raw = product.get("allergens_tags", [])
    allergens = []
    for tag in raw:
        # Tags are like "en:peanuts" – strip language prefix
        parts = tag.split(":", 1)
        name = parts[-1].replace("-", " ")
        allergens.append(name)
    return allergens


def extract_additives(product: dict) -> list[str]:
    """Return human-readable additive names from a product dict."""
    raw = product.get("additives_tags", [])
    additives = []
    for tag in raw:
        parts = tag.split(":", 1)
        name = parts[-1].replace("-", " ").upper()
        additives.append(name)
    return additives


def normalise_grade(grade: Optional[str]) -> Optional[str]:
    """Lowercase and strip a NutriScore grade, return None if absent or empty."""
    if grade:
        stripped = grade.lower().strip()
        return stripped if stripped else None
    return None


def category_slug(product: dict) -> str:
    """Return the first meaningful category slug from *product*."""
    tags = product.get("categories_tags", [])
    for tag in tags:
        parts = tag.split(":", 1)
        slug = parts[-1]
        if slug:
            return slug.lower()
    return ""
