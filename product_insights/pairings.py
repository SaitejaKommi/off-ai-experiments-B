"""Suggest complementary food pairings for a product."""

from utils.nutrition_rules import CATEGORY_PAIRINGS
from utils.product_helpers import category_slug


def get_pairings(product: dict) -> list[str]:
    """Return a list of complementary food suggestions for *product*.

    The function matches the product's first category tag against the
    ``CATEGORY_PAIRINGS`` lookup table.  If no specific match is found the
    default pairings are returned.

    Parameters
    ----------
    product:
        Normalised product dictionary.

    Returns
    -------
    list of str
        Food items that pair well with this product.
    """
    slug = category_slug(product)

    # Try successively shorter category slugs (most → least specific)
    # e.g. "spreads-and-sauces" → "spreads" → default
    for key in CATEGORY_PAIRINGS:
        if key in slug:
            return CATEGORY_PAIRINGS[key]

    return CATEGORY_PAIRINGS["default"]
