"""Generate a plain-language product summary."""

from utils.product_helpers import normalise_grade, safe_int, extract_allergens, extract_nutriment
from utils.nutrition_rules import NUTRISCORE_DESCRIPTIONS, NOVA_DESCRIPTIONS


def generate(product: dict) -> str:
    """Return a human-readable product summary string.

    Parameters
    ----------
    product:
        Normalised product dictionary.

    Returns
    -------
    str
        A multi-sentence summary of the product.
    """
    name = product.get("product_name") or "This product"
    grade = normalise_grade(product.get("nutriscore_grade"))
    nova = safe_int(product.get("nova_group"), 0)
    allergens = extract_allergens(product)

    sentences: list[str] = []

    # Opening sentence
    if grade and grade in NUTRISCORE_DESCRIPTIONS:
        quality = NUTRISCORE_DESCRIPTIONS[grade]
        sentences.append(
            f"{name} is a product with {quality} (NutriScore {grade.upper()})."
        )
    else:
        sentences.append(f"{name} is a food product.")

    # NOVA processing sentence
    if nova in NOVA_DESCRIPTIONS:
        nova_desc = NOVA_DESCRIPTIONS[nova]
        if nova == 4:
            sentences.append(
                f"It is classified as an {nova_desc}, which may contain additives,"
                " artificial flavors, and emulsifiers."
            )
        elif nova == 1:
            sentences.append(f"It is {nova_desc} with little to no industrial processing.")
        else:
            sentences.append(f"It is a {nova_desc}.")

    # Nutriment highlights
    nutriments = product.get("nutriments", {})
    fat = extract_nutriment(nutriments, "fat")
    sugars = extract_nutriment(nutriments, "sugars")
    protein = extract_nutriment(nutriments, "proteins")

    highlights = []
    if fat > 20:
        highlights.append("high levels of fat")
    if sugars > 15:
        highlights.append("high sugar content")
    if protein > 10:
        highlights.append("a good source of protein")

    if highlights:
        sentences.append("It contains " + ", ".join(highlights) + ".")

    # Allergen sentence
    if allergens:
        allergen_list = ", ".join(allergens)
        sentences.append(f"Contains allergens: {allergen_list}.")

    return " ".join(sentences)
