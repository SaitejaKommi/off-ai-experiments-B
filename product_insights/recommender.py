"""Suggest healthier product alternatives using the Open Food Facts search API."""

import json
import urllib.parse
import urllib.request

from utils.product_helpers import normalise_grade, extract_nutriment

_GRADE_ORDER = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}

_SEARCH_URL = (
    "https://world.openfoodfacts.org/cgi/search.pl"
    "?action=process"
    "&tagtype_0=categories"
    "&tag_contains_0=contains"
    "&tag_0={category}"
    "&sort_by=unique_scans_n"
    "&page_size=20"
    "&json=1"
    "&fields=product_name,nutriscore_grade,nutriments,url,categories_tags"
)


def _grade_rank(grade: str | None) -> int:
    """Return a sort rank (lower = better) for a NutriScore grade."""
    if grade:
        return _GRADE_ORDER.get(grade.lower(), 99)
    return 99


def _get_most_specific_category(categories_tags: list) -> str:
    """Extract the most specific (last) category slug from categories_tags.
    
    Open Food Facts categories are hierarchical, with the last one being 
    the most specific. Instead of using the first generic category,
    we use the last specific one for better alternatives matching.
    
    Example: ['en:plant-based-foods', 'en:spreads', 'en:nut-butters']
    Returns: 'nut-butters' (not 'plant-based-foods')
    """
    if not categories_tags:
        return ""
    
    # Get the last (most specific) category
    last_tag = categories_tags[-1]
    parts = last_tag.split(":", 1)
    slug = parts[-1].lower() if parts[-1] else ""
    return slug if slug else ""


def _is_category_match(product_categories: list, search_category: str) -> bool:
    """Check if a product's categories contain the search category.
    
    Ensures the product is actually in the searched category (not just
    a generic parent category).
    """
    for tag in product_categories:
        parts = tag.split(":", 1)
        slug = parts[-1].lower() if parts[-1] else ""
        if slug == search_category:
            return True
    return False


def get_alternatives(product: dict, max_results: int = 3) -> list[dict]:
    """Return a list of healthier alternative products.

    The function now uses the MOST SPECIFIC category (not the first generic one)
    to query OFF, ensuring alternatives are truly in the same category
    (e.g., peanut-butters, not just plant-based-foods).

    It also filters results to verify they belong to the searched category,
    preventing unrelated products from appearing.

    Parameters
    ----------
    product:
        Normalised product dictionary.
    max_results:
        Maximum number of alternatives to return.

    Returns
    -------
    list of dicts, each with keys:
        ``name``, ``nutriscore_grade``, ``reason``.
        
    Returns empty list if no suitable category or alternatives found.
    """
    current_grade = normalise_grade(product.get("nutriscore_grade"))
    current_rank = _grade_rank(current_grade)

    # Use MOST SPECIFIC category instead of first
    categories_tags = product.get("categories_tags", [])
    slug = _get_most_specific_category(categories_tags)
    
    if not slug:
        return []

    url = _SEARCH_URL.format(category=urllib.parse.quote(slug))

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "off-ai-experiments-B/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
    except Exception:
        return []

    current_name = (product.get("product_name") or "").strip().lower()
    current_nutrients = product.get("nutriments", {})
    current_sugar = extract_nutriment(current_nutrients, "sugars")
    current_fat = extract_nutriment(current_nutrients, "fat")

    alternatives = []
    for item in data.get("products", []):
        name = (item.get("product_name") or "").strip()
        if not name or name.lower() == current_name:
            continue

        # NEW: Verify the product is actually in the searched category
        # This prevents bread from showing up when searching peanut-butters
        item_categories = item.get("categories_tags", [])
        if not _is_category_match(item_categories, slug):
            continue

        grade = normalise_grade(item.get("nutriscore_grade"))
        rank = _grade_rank(grade)
        if rank >= current_rank:
            continue

        alt_nutrients = item.get("nutriments", {})
        alt_sugar = extract_nutriment(alt_nutrients, "sugars")
        alt_fat = extract_nutriment(alt_nutrients, "fat")

        reasons = []
        if grade:
            reasons.append(f"NutriScore {grade.upper()}")
        if alt_sugar < current_sugar:
            reasons.append("lower sugar")
        if alt_fat < current_fat:
            reasons.append("lower fat")

        alternatives.append(
            {
                "name": name,
                "nutriscore_grade": grade.upper() if grade else "N/A",
                "reason": " and ".join(reasons) if reasons else "Better nutritional profile",
            }
        )

        if len(alternatives) >= max_results:
            break

    return alternatives
