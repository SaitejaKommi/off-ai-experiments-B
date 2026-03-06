"""Suggest healthier product alternatives using the Open Food Facts search API."""

import json
import urllib.parse
import urllib.request

from utils.product_helpers import normalise_grade, category_slug

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


def get_alternatives(product: dict, max_results: int = 3) -> list[dict]:
    """Return a list of healthier alternative products.

    The function queries OFF for products in the same category, then filters
    for those with a better (lower) NutriScore grade and lower sugar/fat.

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
    """
    current_grade = normalise_grade(product.get("nutriscore_grade"))
    current_rank = _grade_rank(current_grade)

    slug = category_slug(product)
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
    current_sugar = float(
        current_nutrients.get("sugars_100g") or current_nutrients.get("sugars") or 0
    )
    current_fat = float(
        current_nutrients.get("fat_100g") or current_nutrients.get("fat") or 0
    )

    alternatives = []
    for item in data.get("products", []):
        name = (item.get("product_name") or "").strip()
        if not name or name.lower() == current_name:
            continue

        grade = normalise_grade(item.get("nutriscore_grade"))
        rank = _grade_rank(grade)
        if rank >= current_rank:
            continue

        alt_nutrients = item.get("nutriments", {})
        alt_sugar = float(
            alt_nutrients.get("sugars_100g") or alt_nutrients.get("sugars") or 0
        )
        alt_fat = float(
            alt_nutrients.get("fat_100g") or alt_nutrients.get("fat") or 0
        )

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
