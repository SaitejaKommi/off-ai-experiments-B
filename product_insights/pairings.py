"""Suggest complementary food pairings for a product."""

from utils.nutrition_rules import CATEGORY_PAIRINGS


def get_pairings(product: dict) -> list[str]:
    """Return a list of complementary food suggestions for *product*.

    The function matches the product's categories against the CATEGORY_PAIRINGS
    lookup table using a multi-strategy approach:
    1. Check all category tags (not just the first) for direct matches
    2. Substring matching on all tags with word-based fallback
    3. Default pairings if no match is found

    This approach ensures specific categories (e.g., 'peanut-butter') are
    matched even if they're not the first category tag.

    Parameters
    ----------
    product:
        Normalised product dictionary.

    Returns
    -------
    list of str
        Food items that pair well with this product.
    """
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

