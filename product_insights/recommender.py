"""Suggest healthier product alternatives using the Open Food Facts search API."""

import json
import urllib.parse
import urllib.request
from typing import Any

from utils.product_helpers import normalise_grade, extract_nutriment, safe_int

_GRADE_ORDER = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}

# V2 search API is more reliable and faster than the CGI endpoint
_SEARCH_URL_V2 = (
    "https://world.openfoodfacts.org/api/v2/search"
    "?categories_tags={category}"
    "&fields=product_name,nutriscore_grade,nova_group,nutriments,categories_tags,url,unique_scans_n"
    "&page_size=50"
    "&sort_by=unique_scans_n"
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


def _get_parent_categories(categories_tags: list, max_depth: int = 3) -> list[str]:
    """Return up to ``max_depth`` category slugs from specific to broader."""
    if not categories_tags:
        return []

    relevant = categories_tags[-max_depth:]
    slugs: list[str] = []
    for tag in reversed(relevant):
        parts = tag.split(":", 1)
        slug = parts[-1].lower() if parts[-1] else ""
        if slug:
            slugs.append(slug)
    return slugs


def _is_category_match(product_categories: list, search_categories: list[str]) -> bool:
    """Check if a product belongs to any searched category slug."""
    if not search_categories:
        return False

    wanted = set(search_categories)
    for tag in product_categories:
        parts = tag.split(":", 1)
        slug = parts[-1].lower() if parts[-1] else ""
        if slug in wanted:
            return True
    return False


def _fetch_candidates_for_category(category_slug: str) -> list[dict[str, Any]]:
    """Fetch candidate products using v2 API with caching and error handling."""
    if category_slug in _SEARCH_CACHE:
        return _SEARCH_CACHE[category_slug]

    url = _SEARCH_URL_V2.format(category=urllib.parse.quote(category_slug))

    # Retry transient network failures. Do not cache failures as empty lists.
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "off-ai-experiments-B/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())

            products = data.get("products", [])
            _SEARCH_CACHE[category_slug] = products
            return products
        except Exception:
            continue

    return []


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


def _build_simple_reason(
    grade: str | None,
    current_rank: int,
    alt_rank: int,
    alt_nova: int,
    current_nova: int,
) -> str:
    """Create a lightweight reason when nutrient fields are missing."""
    parts: list[str] = []

    if grade:
        parts.append(f"Better NutriScore ({grade.upper()})")

    grade_diff = current_rank - alt_rank
    if grade_diff >= 2:
        parts.append("significantly better nutritional quality")
    elif grade_diff == 1:
        parts.append("better nutritional quality")

    if current_nova > 0 and alt_nova > 0 and alt_nova < current_nova:
        parts.append(f"lower processing (NOVA {current_nova} -> {alt_nova})")

    if not parts:
        parts.append("better overall nutrition profile")

    return "; ".join(parts)


def _build_discovery_reason(
    grade: str | None,
    current_rank: int,
    alt_rank: int,
    current_nova: int,
    alt_nova: int,
) -> str:
    """Fallback message when strict healthier alternatives are scarce."""
    parts: list[str] = ["Category discovery option"]

    if grade and alt_rank < current_rank:
        parts.append(f"better NutriScore ({grade.upper()})")
    elif grade and alt_rank == current_rank:
        parts.append(f"same NutriScore ({grade.upper()})")

    if current_nova > 0 and alt_nova > 0:
        if alt_nova < current_nova:
            parts.append(f"lower processing (NOVA {current_nova} -> {alt_nova})")
        elif alt_nova == current_nova:
            parts.append(f"similar processing (NOVA {alt_nova})")

    return "; ".join(parts)


def get_alternatives(product: dict, max_results: int = 5) -> list[dict]:
    """Return a list of healthier alternative products.

    The function uses multiple category levels (specific to broader) and
    falls back to NutriScore-only reasoning when nutrient detail is sparse.

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

    # Use multiple category levels to avoid empty result sets in sparse categories.
    categories_tags = product.get("categories_tags", [])
    category_slugs = _get_parent_categories(categories_tags, max_depth=3)

    if not category_slugs:
        return []

    candidate_products: list[dict] = []
    for slug in category_slugs:
        candidates = _fetch_candidates_for_category(slug)
        if candidates:
            candidate_products.extend(candidates)

    if not candidate_products:
        return []

    # De-duplicate candidates fetched across category levels.
    deduped_candidates: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for item in candidate_products:
        key = (
            (item.get("product_name") or "").strip().lower(),
            (item.get("url") or "").strip().lower(),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped_candidates.append(item)
    candidate_products = deduped_candidates

    current_name = (product.get("product_name") or "").strip().lower()
    current_nutrients = product.get("nutriments", {})
    current_metrics = _extract_metrics(current_nutrients)
    has_detailed_nutrients = _has_min_nutrient_data(current_nutrients)

    alternatives = []
    for item in candidate_products:
        name = (item.get("product_name") or "").strip()
        if not name or name.lower() == current_name:
            continue

        item_categories = item.get("categories_tags", [])
        if not _is_category_match(item_categories, category_slugs):
            continue

        grade = normalise_grade(item.get("nutriscore_grade"))
        rank = _grade_rank(grade)
        is_strictly_better = rank < current_rank

        alt_nutrients = item.get("nutriments", {})
        alt_metrics = _extract_metrics(alt_nutrients)
        alt_nova = safe_int(item.get("nova_group"), 0)

        # Prefer detailed comparison when both products have enough data.
        if is_strictly_better:
            if has_detailed_nutrients and _has_min_nutrient_data(alt_nutrients):
                shared_metrics = {
                    key: _has_metric_key(current_nutrients, key) and _has_metric_key(alt_nutrients, key)
                    for key in ["sugars", "fat", "salt", "proteins", "fiber"]
                }

                if sum(1 for is_shared in shared_metrics.values() if is_shared) >= 1:
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
                else:
                    score = (current_rank - rank) * 0.25
                    confidence = 75
                    reason = _build_simple_reason(grade, current_rank, rank, alt_nova, current_nova)
            else:
                score = (current_rank - rank) * 0.25
                confidence = 75
                reason = _build_simple_reason(grade, current_rank, rank, alt_nova, current_nova)
        else:
            # Keep non-strict options as fallback product discovery entries.
            score = -0.05
            if rank < 99:
                score += max(-0.2, (current_rank - rank) * 0.05)
            if current_nova > 0 and alt_nova > 0:
                score += max(-0.1, min(0.1, (current_nova - alt_nova) * 0.03))
            confidence = 60
            reason = _build_discovery_reason(grade, current_rank, rank, current_nova, alt_nova)

        alternatives.append(
            {
                "name": name,
                "nutriscore_grade": grade.upper() if grade else "N/A",
                "reason": reason,
                "score": score,
                "confidence": confidence,
                "url": item.get("url", ""),
                "is_better": is_strictly_better,
            }
        )

    # Prefer strict healthier options first. If none exist, return fallback discovery options.
    better = [item for item in alternatives if item.get("is_better")]
    fallback = [item for item in alternatives if not item.get("is_better")]

    better.sort(key=lambda item: item.get("score", 0), reverse=True)
    fallback.sort(key=lambda item: item.get("score", 0), reverse=True)

    selected = better[:max_results] if better else fallback[:max_results]

    # Remove internal helper key before returning API response.
    for item in selected:
        item.pop("is_better", None)

    return selected
