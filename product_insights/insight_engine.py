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

    return {
        "risk_indicators": risk,
        "positive_indicators": positive,
    }
