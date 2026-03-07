"""Explain NutriScore and NOVA processing scores in plain language."""

from utils.nutrition_rules import NUTRISCORE_DESCRIPTIONS, NOVA_DESCRIPTIONS
from utils.product_helpers import normalise_grade, safe_int, extract_nutriment
from product_insights.llm_config import LLMConfig

try:
    from product_insights.llm_client import get_llm_client
except ImportError:
    get_llm_client = None


def explain_nutriscore(product: dict) -> str:
    """Return a human-readable explanation of the product's NutriScore."""
    # Try LLM-enhanced explanation first
    llm_explanation = _explain_nutriscore_llm(product)
    if llm_explanation:
        return llm_explanation
    
    if LLMConfig.LLM_FALLBACK_TO_RULES:
        return _explain_nutriscore_template(product)

    return "NutriScore explanation unavailable (LLM response not available)."


def _explain_nutriscore_llm(product: dict) -> str:
    """Get LLM-enhanced NutriScore explanation."""
    if get_llm_client is None:
        return ""
    
    try:
        client = get_llm_client()
        if not client:
            return ""
        
        grade = normalise_grade(product.get("nutriscore_grade"))
        if not grade or grade not in NUTRISCORE_DESCRIPTIONS:
            return ""
        
        product_name = product.get("product_name", "product")
        nutriments = product.get("nutriments", {})
        
        prompt = f"""Explain the NutriScore grade for this product in 2 sentences.

Product: {product_name}
NutriScore: {grade.upper()}
Nutrients per 100g:
- Fat: {extract_nutriment(nutriments, 'fat'):.1f}g
- Saturated Fat: {extract_nutriment(nutriments, 'saturated-fat'):.1f}g
- Sugar: {extract_nutriment(nutriments, 'sugars'):.1f}g
- Protein: {extract_nutriment(nutriments, 'proteins'):.1f}g
- Fiber: {extract_nutriment(nutriments, 'fiber'):.1f}g

Write a concise, helpful explanation of what this grade means and why this product received it. Focus on the key nutrients that influenced the score. Be specific and actionable."""
        prompt += """

Important nutrition guardrails:
- Do NOT call protein "high" unless protein >= 10g per 100g.
- Do NOT call fiber "high" unless fiber >= 6g per 100g.
- If sugar is low, prefer wording like "low sugar" rather than claiming high protein benefits.
- Avoid over-claiming healthiness for candy/confectionery products.
"""
        
        response = client._call_llm(prompt)
        return response.strip() if response else ""
    except Exception:
        return ""


def _explain_nutriscore_template(product: dict) -> str:
    """Template-based NutriScore explanation (fallback)."""
    grade = normalise_grade(product.get("nutriscore_grade"))
    if not grade or grade not in NUTRISCORE_DESCRIPTIONS:
        return "NutriScore is not available for this product."

    description = NUTRISCORE_DESCRIPTIONS[grade]
    explanation = f"NutriScore {grade.upper()} means {description}."

    nutriments = product.get("nutriments", {})
    fat = extract_nutriment(nutriments, "fat")
    sugars = extract_nutriment(nutriments, "sugars")
    saturated_fat = extract_nutriment(nutriments, "saturated-fat")
    fiber = extract_nutriment(nutriments, "fiber")
    protein = extract_nutriment(nutriments, "proteins")

    details = []
    if fat > 20:
        details.append("high fat content")
    if saturated_fat > 5:
        details.append("high saturated fat")
    if sugars > 15:
        details.append("high sugar content")
    if fiber > 6:
        details.append("good dietary fiber")
    if protein > 10:
        details.append("good protein content")

    if details:
        explanation += " This product has " + ", ".join(details) + "."

    return explanation


def explain_nova(product: dict) -> str:
    """Return a human-readable explanation of the product's NOVA group."""
    # Try LLM-enhanced explanation first
    llm_explanation = _explain_nova_llm(product)
    if llm_explanation:
        return llm_explanation
    
    if LLMConfig.LLM_FALLBACK_TO_RULES:
        return _explain_nova_template(product)

    return "NOVA explanation unavailable (LLM response not available)."


def _explain_nova_llm(product: dict) -> str:
    """Get LLM-enhanced NOVA explanation."""
    if get_llm_client is None:
        return ""
    
    try:
        client = get_llm_client()
        if not client:
            return ""
        
        nova = safe_int(product.get("nova_group"), 0)
        if nova not in NOVA_DESCRIPTIONS:
            return ""
        
        product_name = product.get("product_name", "product")
        categories = product.get("categories_tags", [])
        category = categories[-1].split(":", 1)[-1] if categories else ""
        additives_count = len(product.get("additives_tags", []))
        
        prompt = f"""Explain the NOVA processing level for this product in 2 sentences.

Product: {product_name}
Category: {category}
NOVA Group: {nova} ({NOVA_DESCRIPTIONS[nova]})
Additives: {additives_count}

Explain what this NOVA group means for this specific product type and why consumers should care. Be practical and balanced—avoid alarmism but be honest about processing concerns."""
        
        response = client._call_llm(prompt)
        return response.strip() if response else ""
    except Exception:
        return ""


def _explain_nova_template(product: dict) -> str:
    """Template-based NOVA explanation (fallback)."""
    nova = safe_int(product.get("nova_group"), 0)
    if nova not in NOVA_DESCRIPTIONS:
        return "NOVA processing level is not available for this product."

    description = NOVA_DESCRIPTIONS[nova]
    explanation = f"NOVA Group {nova}: This product is classified as a {description}."

    if nova == 1:
        explanation += " These foods are in their natural state with minimal processing."
    elif nova == 2:
        explanation += " These are substances extracted from natural foods, used in cooking."
    elif nova == 3:
        explanation += (
            " These products contain added salt, sugar, or other substances but are"
            " not significantly altered."
        )
    elif nova == 4:
        explanation += (
            " Ultra-processed foods often contain additives, artificial flavors,"
            " emulsifiers, and preservatives. Regular consumption is associated with"
            " higher health risks."
        )

    return explanation


def explain_nutrient_density(product: dict) -> str:
    """Return a brief nutrient density summary."""
    nutriments = product.get("nutriments", {})
    energy_kcal = extract_nutriment(nutriments, "energy-kcal")
    protein = extract_nutriment(nutriments, "proteins")
    fiber = extract_nutriment(nutriments, "fiber")

    if energy_kcal <= 0:
        return "Nutrient density information is not available."

    protein_density = protein / energy_kcal * 100 if energy_kcal else 0
    parts = [f"Energy: {energy_kcal:.0f} kcal per 100 g."]
    if protein > 0:
        parts.append(f"Protein: {protein:.1f} g per 100 g.")
    if fiber > 0:
        parts.append(f"Fiber: {fiber:.1f} g per 100 g.")
    if protein_density > 5:
        parts.append("Good protein-to-calorie ratio.")

    return " ".join(parts)


def explain(product: dict) -> dict:
    """Return a combined score explanation dict.

    Returns
    -------
    dict with keys ``nutriscore``, ``nova``, and ``nutrient_density``.
    """
    return {
        "nutriscore": explain_nutriscore(product),
        "nova": explain_nova(product),
        "nutrient_density": explain_nutrient_density(product),
    }
