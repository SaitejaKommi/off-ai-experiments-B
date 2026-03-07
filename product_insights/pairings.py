"""Suggest complementary food pairings for a product."""

from utils.nutrition_rules import CATEGORY_PAIRINGS
from product_insights.llm_config import LLMConfig

try:
    from product_insights.llm_client import get_llm_client
except ImportError:
    get_llm_client = None


def get_pairings(product: dict) -> list[str]:
    """Return a list of complementary food suggestions for *product*."""
    llm_pairings = _get_llm_pairings(product)
    if llm_pairings:
        return llm_pairings

    if LLMConfig.LLM_FALLBACK_TO_RULES:
        return _get_rule_based_pairings(product)

    return []


def _get_llm_pairings(product: dict) -> list[str]:
    """Get pairings using LLM, returning empty list if unavailable/failed."""
    if get_llm_client is None:
        return []

    try:
        client = get_llm_client()
        if not client:
            return []

        product_name = product.get("product_name") or "Unknown product"
        categories_tags = product.get("categories_tags", [])
        category_slug = _get_most_specific_category_slug(categories_tags)

        if not category_slug:
            return []

        nutriments = product.get("nutriments", {})
        nutrients = {
            "energy": nutriments.get("energy-kcal_100g", 0),
            "protein": nutriments.get("proteins_100g", 0),
            "fat": nutriments.get("fat_100g", 0),
            "carbs": nutriments.get("carbohydrates_100g", 0),
            "fiber": nutriments.get("fiber_100g", 0),
        }

        pairings = client.get_food_pairings(
            product_name=product_name,
            category=category_slug,
            nutrients=nutrients,
        )
        return pairings if isinstance(pairings, list) else []
    except Exception:
        return []


def _get_most_specific_category_slug(categories_tags: list[str]) -> str:
    """Extract most specific category slug from OFF category tags."""
    if not categories_tags:
        return ""

    tag = categories_tags[-1]
    parts = tag.split(":", 1)
    return parts[-1].lower() if parts and parts[-1] else ""


def _get_rule_based_pairings(product: dict) -> list[str]:
    """Get pairings with existing rule-based strategy."""
    categories_tags = product.get("categories_tags", [])

    if not categories_tags:
        return CATEGORY_PAIRINGS["default"]

    # Extract all category slugs from the tags format "en:category-name"
    slugs = []
    for tag in categories_tags:
        parts = tag.split(":", 1)
        slug = parts[-1].lower() if parts[-1] else ""
        if slug:
            slugs.append(slug)

    # Strategy 1: Exact matches and substring matches across all slugs
    # Sort keys by length (longest first) for prioritizing more specific matches
    sorted_keys = sorted(
        [k for k in CATEGORY_PAIRINGS.keys() if k != "default"],
        key=len,
        reverse=True
    )
    
    for key in sorted_keys:
        for slug in slugs:
            # Exact match
            if slug == key:
                return CATEGORY_PAIRINGS[key]
            # Substring match
            if key in slug:
                return CATEGORY_PAIRINGS[key]
    
    # Strategy 2: Word-based matching
    # Split each slug by hyphens and check if parts match category keys
    for slug in slugs:
        slug_parts = slug.split("-")
        for part in slug_parts:
            if part in CATEGORY_PAIRINGS:
                return CATEGORY_PAIRINGS[part]

    return CATEGORY_PAIRINGS["default"]

