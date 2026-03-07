"""Suggest healthier product alternatives using the Open Food Facts search API."""

import json
import urllib.parse
import urllib.request
from typing import Any

from utils.product_helpers import normalise_grade, extract_nutriment, safe_int

_GRADE_ORDER = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}

_SEARCH_URL = (
    "https://ca-en.openfoodfacts.org/cgi/search.pl"
    "?action=process"
    "&tagtype_0=categories"
    "&tag_contains_0=contains"
    "&tag_0={category}"
    "&sort_by=unique_scans_n"
    "&page_size=20"
    "&json=1"
    "&fields=product_name,nutriscore_grade,nova_group,nutriments,url,categories_tags,labels_tags"
)

_SEARCH_CACHE: dict[str, list[dict[str, Any]]] = {}

_NUTRIENT_WEIGHTS = {
    "sugars": 0.30,
    "fat": 0.20,
    "salt": 0.15,
    "proteins": 0.20,
    "fiber": 0.15,
}


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


def _fetch_candidates_for_category(category_slug: str) -> list[dict[str, Any]]:
    """Fetch candidate products for a category with simple in-process caching."""
    if category_slug in _SEARCH_CACHE:
        return _SEARCH_CACHE[category_slug]

    url = _SEARCH_URL.format(category=urllib.parse.quote(category_slug))
    req = urllib.request.Request(url, headers={"User-Agent": "off-ai-experiments-B/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode())

    products = data.get("products", [])
    _SEARCH_CACHE[category_slug] = products
    return products


def _extract_metrics(nutriments: dict) -> dict[str, float]:
    return {
        "sugars": extract_nutriment(nutriments, "sugars"),
        "fat": extract_nutriment(nutriments, "fat"),
        "salt": extract_nutriment(nutriments, "salt"),
        "proteins": extract_nutriment(nutriments, "proteins"),
        "fiber": extract_nutriment(nutriments, "fiber"),
    }


def _has_metric_key(nutriments: dict, key: str) -> bool:
    """Return True if a nutriment key is explicitly present in OFF payload."""
    return f"{key}_100g" in nutriments or key in nutriments


def _has_min_nutrient_data(nutriments: dict) -> bool:
    """Require at least 2 known nutrient fields for fair comparison."""
    keys = ["sugars", "fat", "salt", "proteins", "fiber"]
    available = sum(1 for key in keys if _has_metric_key(nutriments, key))
    return available >= 2


def _relative_improvement(current: float, candidate: float, lower_is_better: bool) -> float:
    """Compute capped relative improvement in range [-1, 1]."""
    denominator = max(abs(current), 1.0)
    if lower_is_better:
        raw = (current - candidate) / denominator
    else:
        raw = (candidate - current) / denominator
    return max(-1.0, min(1.0, raw))


def _compute_comparison_score(
    current_metrics: dict[str, float],
    alt_metrics: dict[str, float],
    current_grade_rank: int,
    alt_grade_rank: int,
    current_nova: int,
    alt_nova: int,
) -> float:
    """Compute weighted comparison score where higher is better."""
    score = 0.0
    total_weight = 0.0

    def add_component(metric: str, lower_is_better: bool):
        nonlocal score, total_weight
        weight = _NUTRIENT_WEIGHTS[metric]
        value = _relative_improvement(
            current_metrics[metric], alt_metrics[metric], lower_is_better=lower_is_better
        )
        score += weight * value
        total_weight += weight

    # Use all metrics by default; caller pre-validates available fields.
    add_component("sugars", lower_is_better=True)
    add_component("fat", lower_is_better=True)
    add_component("salt", lower_is_better=True)
    add_component("proteins", lower_is_better=False)
    add_component("fiber", lower_is_better=False)

    if total_weight > 0:
        score = score / total_weight

    if current_grade_rank < 99 and alt_grade_rank < 99:
        nutriscore_improvement = (current_grade_rank - alt_grade_rank) / 4.0
        score += 0.25 * max(-1.0, min(1.0, nutriscore_improvement))

    if current_nova > 0 and alt_nova > 0:
        nova_improvement = (current_nova - alt_nova) / 3.0
        score += 0.15 * max(-1.0, min(1.0, nova_improvement))

    return score


def _build_reason(
    current_metrics: dict[str, float],
    alt_metrics: dict[str, float],
    grade: str | None,
    current_nova: int,
    alt_nova: int,
    confidence: int,
) -> str:
    """Create a quantified explanation string for recommendation quality."""
    reason_parts: list[str] = []

    if grade:
        reason_parts.append(f"NutriScore {grade.upper()}")

    if alt_metrics["sugars"] < current_metrics["sugars"]:
        reason_parts.append(
            f"Sugar: {current_metrics['sugars']:.1f}g → {alt_metrics['sugars']:.1f}g"
        )
    if alt_metrics["fat"] < current_metrics["fat"]:
        reason_parts.append(
            f"Fat: {current_metrics['fat']:.1f}g → {alt_metrics['fat']:.1f}g"
        )
    if alt_metrics["salt"] < current_metrics["salt"]:
        reason_parts.append(
            f"Salt: {current_metrics['salt']:.2f}g → {alt_metrics['salt']:.2f}g"
        )
    if alt_metrics["fiber"] > current_metrics["fiber"]:
        reason_parts.append(
            f"Fiber: {current_metrics['fiber']:.1f}g → {alt_metrics['fiber']:.1f}g"
        )
    if alt_metrics["proteins"] > current_metrics["proteins"]:
        reason_parts.append(
            f"Protein: {current_metrics['proteins']:.1f}g → {alt_metrics['proteins']:.1f}g"
        )

    if current_nova > 0 and alt_nova > 0 and alt_nova < current_nova:
        reason_parts.append(f"NOVA: {current_nova} → {alt_nova}")

    if not reason_parts:
        reason_parts.append("Better overall nutrition profile")

    return f"{'; '.join(reason_parts)} (confidence: {confidence}%)"


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
    current_nova = safe_int(product.get("nova_group"), 0)

    # Use MOST SPECIFIC category instead of first
    categories_tags = product.get("categories_tags", [])
    slug = _get_most_specific_category(categories_tags)
    
    if not slug:
        return []

    try:
        candidate_products = _fetch_candidates_for_category(slug)
    except Exception:
        return []

    current_name = (product.get("product_name") or "").strip().lower()
    current_nutrients = product.get("nutriments", {})
    current_metrics = _extract_metrics(current_nutrients)
    if not _has_min_nutrient_data(current_nutrients):
        return []

    alternatives = []
    for item in candidate_products:
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
        if not _has_min_nutrient_data(alt_nutrients):
            continue

        alt_metrics = _extract_metrics(alt_nutrients)
        alt_nova = safe_int(item.get("nova_group"), 0)

        # Compare only across metrics that are explicitly present in BOTH products.
        shared_metrics = {
            key: _has_metric_key(current_nutrients, key) and _has_metric_key(alt_nutrients, key)
            for key in ["sugars", "fat", "salt", "proteins", "fiber"]
        }
        if sum(1 for is_shared in shared_metrics.values() if is_shared) < 2:
            continue

        current_comp = {key: current_metrics[key] if shared_metrics[key] else 0.0 for key in shared_metrics}
        alt_comp = {key: alt_metrics[key] if shared_metrics[key] else 0.0 for key in shared_metrics}

        score = _compute_comparison_score(
            current_metrics=current_comp,
            alt_metrics=alt_comp,
            current_grade_rank=current_rank,
            alt_grade_rank=rank,
            current_nova=current_nova,
            alt_nova=alt_nova,
        )

        confidence = max(50, min(98, int(50 + score * 35)))
        reason = _build_reason(
            current_metrics=current_metrics,
            alt_metrics=alt_metrics,
            grade=grade,
            current_nova=current_nova,
            alt_nova=alt_nova,
            confidence=confidence,
        )

        alternatives.append(
            {
                "name": name,
                "nutriscore_grade": grade.upper() if grade else "N/A",
                "reason": reason,
                "score": score,
                "confidence": confidence,
            }
        )

    alternatives.sort(key=lambda item: item.get("score", 0), reverse=True)

    # Stage 1: strict confidence cut for high-quality replacements.
    strict = [item for item in alternatives if item.get("score", 0) > 0.05]
    if strict:
        return strict[:max_results]

    # Stage 2: relaxed fallback when strict stage returns none.
    relaxed = [item for item in alternatives if item.get("score", 0) > 0.0]
    return relaxed[:max_results]
