"""Analyse a product and produce risk and positive indicators."""

from utils.nutrition_rules import (
    FAT_HIGH,
    SUGAR_HIGH,
    SALT_HIGH,
    SATURATED_FAT_HIGH,
    PROTEIN_HIGH,
    FIBER_HIGH,
    CALORIES_HIGH,
    NOVA_ULTRA_PROCESSED,
)
from utils.product_helpers import extract_nutriment, safe_int, normalise_grade

try:
    from product_insights.llm_client import get_llm_client
except ImportError:
    get_llm_client = None


def analyse(product: dict) -> dict:
    """Return a dict with ``risk_indicators`` and ``positive_indicators`` lists.

    Parameters
    ----------
    product:
        Normalised product dictionary (as returned by :func:`fetcher.fetch_product`).

    Returns
    -------
    dict with keys:
        ``risk_indicators`` – list of warning strings.
        ``positive_indicators`` – list of positive strings.
    """
    nutriments = product.get("nutriments", {})
    nova = safe_int(product.get("nova_group"), 0)
    labels = [t.lower() for t in product.get("labels_tags", [])]
    additives = product.get("additives_tags", [])

    fat = extract_nutriment(nutriments, "fat")
    sugars = extract_nutriment(nutriments, "sugars")
    salt = extract_nutriment(nutriments, "salt")
    saturated_fat = extract_nutriment(nutriments, "saturated-fat")
    protein = extract_nutriment(nutriments, "proteins")
    fiber = extract_nutriment(nutriments, "fiber")
    energy_kcal = extract_nutriment(nutriments, "energy-kcal")

    risk: list[str] = []
    positive: list[str] = []

    # --- Risk indicators ---
    if fat > FAT_HIGH:
        risk.append("High fat")
    if sugars > SUGAR_HIGH:
        risk.append("High sugar")
    if salt > SALT_HIGH:
        risk.append("High salt")
    if saturated_fat > SATURATED_FAT_HIGH:
        risk.append("High saturated fat")
    if energy_kcal > CALORIES_HIGH:
        risk.append("High calorie density")
    if nova >= NOVA_ULTRA_PROCESSED:
        risk.append("Ultra-processed food (NOVA 4)")
    if len(additives) > 5:
        risk.append(f"Many additives ({len(additives)} found)")

    # --- Positive indicators ---
    if protein > PROTEIN_HIGH:
        positive.append("High protein")
    if sugars <= 5:
        positive.append("Low sugar content")
    if fiber > FIBER_HIGH:
        positive.append("High fiber")
    if any("organic" in t or "bio" in t for t in labels):
        positive.append("Organic label")
    if any("fair-trade" in t or "fairtrade" in t for t in labels):
        positive.append("Fair trade certified")
    if fat <= FAT_HIGH and sugars <= SUGAR_HIGH and salt <= SALT_HIGH:
        positive.append("Balanced fat, sugar, and salt levels")
    if nova == 1:
        positive.append("Minimally processed (NOVA 1)")
    if nova == 2:
        positive.append("Processed culinary ingredient (NOVA 2)")

    nutriscore = normalise_grade(product.get("nutriscore_grade"))
    if nutriscore in ("a", "b"):
        positive.append(f"Good NutriScore ({nutriscore.upper()})")

    # Enhance with LLM contextual insights if available
    llm_insights = _get_llm_insights(product, risk, positive, nutriments)
    if llm_insights:
        risk.extend(llm_insights.get("enhanced_risks", []))
        filtered_positives = _filter_llm_positives(
            llm_insights.get("enhanced_positives", []),
            nutriments,
            categories_tags=product.get("categories_tags", []),
            existing_positives=positive,
        )
        positive.extend(filtered_positives)

    return {
        "risk_indicators": risk,
        "positive_indicators": positive,
    }


def _get_llm_insights(product: dict, existing_risks: list, existing_positives: list, nutriments: dict) -> dict:
    """Get LLM-enhanced contextual insights."""
    if get_llm_client is None:
        return {}
    
    try:
        client = get_llm_client()
        if not client:
            return {}
        
        product_name = product.get("product_name") or "product"
        categories_tags = product.get("categories_tags", [])
        category = categories_tags[-1].split(":", 1)[-1] if categories_tags else "food"
        
        # Build context for LLM
        nutrients_info = {
            "fat": extract_nutriment(nutriments, "fat"),
            "sugar": extract_nutriment(nutriments, "sugars"),
            "salt": extract_nutriment(nutriments, "salt"),
            "protein": extract_nutriment(nutriments, "proteins"),
            "fiber": extract_nutriment(nutriments, "fiber"),
            "saturated_fat": extract_nutriment(nutriments, "saturated-fat"),
        }
        
        prompt = f"""Analyze this food product and provide 1-2 additional contextual insights.

Product: {product_name}
Category: {category}
Nutrients (per 100g): {nutrients_info}

Existing Analysis:
Risks: {existing_risks if existing_risks else 'None detected'}
Positives: {existing_positives if existing_positives else 'None detected'}

Provide ONLY a JSON response with this format:
{{
  "enhanced_risks": ["One contextual risk if relevant, empty if none"],
  "enhanced_positives": ["One contextual positive insight"]
}}

Rules:
- Keep insights brief (max 8 words each)
- Add context the existing analysis missed
- For olive oil: mention heart-healthy fats, not just "high fat"
- For lentils: mention plant-based protein quality
- Only add 0-2 items total, focus on most impactful insights
- Return valid JSON only"""
        
        response_text = client._call_llm(prompt)
        
        # Parse JSON response
        import json
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            # Filter out empty strings and limit additions
            enhanced_risks = [r for r in data.get("enhanced_risks", []) if r and isinstance(r, str)][:1]
            enhanced_positives = [p for p in data.get("enhanced_positives", []) if p and isinstance(p, str)][:2]
            
            return {
                "enhanced_risks": enhanced_risks,
                "enhanced_positives": enhanced_positives,
            }
        
        return {}
    except Exception:
        return {}


def _filter_llm_positives(
    llm_positives: list,
    nutriments: dict,
    categories_tags: list,
    existing_positives: list,
) -> list[str]:
    """Filter LLM positives to avoid nutrition-incorrect or duplicate claims."""
    if not llm_positives:
        return []

    protein = extract_nutriment(nutriments, "proteins")
    fiber = extract_nutriment(nutriments, "fiber")
    sugars = extract_nutriment(nutriments, "sugars")
    category_text = " ".join(categories_tags).lower()
    is_candy_like = any(
        key in category_text
        for key in ["candy", "candies", "sweets", "sweet", "confectionery", "gummies", "gummy"]
    )

    existing_lower = {item.lower() for item in existing_positives}
    filtered: list[str] = []

    for item in llm_positives:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue

        lower = text.lower()

        if "protein" in lower and protein <= PROTEIN_HIGH:
            continue
        if "fiber" in lower and fiber <= FIBER_HIGH:
            continue
        if "low sugar" in lower and sugars > 5:
            continue
        if is_candy_like and "protein" in lower:
            continue
        if lower in existing_lower:
            continue

        filtered.append(text)
        existing_lower.add(lower)

        if len(filtered) >= 2:
            break

    return filtered
