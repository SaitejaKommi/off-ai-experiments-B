"""Unit tests for the Product Intelligence Engine."""

import sys
import os

# Ensure the repo root is on the path so imports work from the tests/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from utils.product_helpers import (
    safe_float,
    safe_int,
    extract_nutriment,
    extract_allergens,
    extract_additives,
    normalise_grade,
    category_slug,
)
from utils.nutrition_rules import (
    FAT_HIGH,
    SUGAR_HIGH,
    NOVA_ULTRA_PROCESSED,
    NUTRISCORE_DESCRIPTIONS,
    NOVA_DESCRIPTIONS,
    CATEGORY_PAIRINGS,
)
from product_insights.insight_engine import analyse
from product_insights.score_explainer import explain_nutriscore, explain_nova, explain
from product_insights.summary import generate
from product_insights.pairings import get_pairings
from product_insights.fetcher import _barcode_from_url


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def peanut_butter_product():
    """Minimal product dict resembling a peanut butter."""
    return {
        "product_name": "Smooth Kraft Peanut Butter",
        "nutriscore_grade": "c",
        "nova_group": 4,
        "nutriments": {
            "fat_100g": 50.0,
            "sugars_100g": 10.0,
            "salt_100g": 0.8,
            "saturated-fat_100g": 8.0,
            "proteins_100g": 25.0,
            "fiber_100g": 5.0,
            "energy-kcal_100g": 600.0,
        },
        "labels_tags": [],
        "additives_tags": ["en:e471", "en:e322"],
        "allergens_tags": ["en:peanuts", "en:soybeans"],
        "categories_tags": ["en:nut-butters", "en:spreads"],
    }


@pytest.fixture()
def healthy_product():
    """Product with a good NutriScore and minimal processing."""
    return {
        "product_name": "Organic Oats",
        "nutriscore_grade": "a",
        "nova_group": 1,
        "nutriments": {
            "fat_100g": 6.0,
            "sugars_100g": 1.0,
            "salt_100g": 0.01,
            "saturated-fat_100g": 1.0,
            "proteins_100g": 13.0,
            "fiber_100g": 10.0,
            "energy-kcal_100g": 370.0,
        },
        "labels_tags": ["en:organic"],
        "additives_tags": [],
        "allergens_tags": ["en:gluten"],
        "categories_tags": ["en:cereals"],
    }


# ---------------------------------------------------------------------------
# utils.product_helpers
# ---------------------------------------------------------------------------

class TestSafeFloat:
    def test_converts_string(self):
        assert safe_float("3.14") == pytest.approx(3.14)

    def test_returns_default_on_none(self):
        assert safe_float(None) == 0.0

    def test_returns_default_on_invalid_string(self):
        assert safe_float("abc", default=1.0) == 1.0


class TestSafeInt:
    def test_converts_string(self):
        assert safe_int("4") == 4

    def test_returns_default_on_none(self):
        assert safe_int(None) == 0


class TestExtractNutriment:
    def test_extracts_100g_key(self):
        nutriments = {"fat_100g": 25.0}
        assert extract_nutriment(nutriments, "fat") == pytest.approx(25.0)

    def test_falls_back_to_plain_key(self):
        nutriments = {"sugars": 12.0}
        assert extract_nutriment(nutriments, "sugars") == pytest.approx(12.0)

    def test_returns_zero_when_absent(self):
        assert extract_nutriment({}, "fat") == 0.0


class TestExtractAllergens:
    def test_strips_language_prefix(self):
        product = {"allergens_tags": ["en:peanuts", "en:soybeans"]}
        assert extract_allergens(product) == ["peanuts", "soybeans"]

    def test_empty_tags(self):
        assert extract_allergens({}) == []


class TestExtractAdditives:
    def test_strips_prefix_and_uppercases(self):
        product = {"additives_tags": ["en:e471"]}
        assert extract_additives(product) == ["E471"]


class TestNormaliseGrade:
    def test_lowercases(self):
        assert normalise_grade("C") == "c"

    def test_returns_none_for_empty(self):
        assert normalise_grade(None) is None
        assert normalise_grade("") is None


class TestCategorySlug:
    def test_returns_first_slug(self):
        product = {"categories_tags": ["en:nut-butters", "en:spreads"]}
        assert category_slug(product) == "nut-butters"

    def test_returns_empty_string_when_no_tags(self):
        assert category_slug({}) == ""


# ---------------------------------------------------------------------------
# product_insights.insight_engine
# ---------------------------------------------------------------------------

class TestAnalyse:
    def test_high_fat_detected(self, peanut_butter_product):
        result = analyse(peanut_butter_product)
        assert any("fat" in r.lower() for r in result["risk_indicators"])

    def test_ultra_processed_detected(self, peanut_butter_product):
        result = analyse(peanut_butter_product)
        assert any("ultra-processed" in r.lower() for r in result["risk_indicators"])

    def test_high_protein_positive(self, peanut_butter_product):
        result = analyse(peanut_butter_product)
        assert any("protein" in p.lower() for p in result["positive_indicators"])

    def test_organic_label_positive(self, healthy_product):
        result = analyse(healthy_product)
        assert any("organic" in p.lower() for p in result["positive_indicators"])

    def test_good_nutriscore_positive(self, healthy_product):
        result = analyse(healthy_product)
        assert any("nutriscore" in p.lower() for p in result["positive_indicators"])

    def test_no_false_positive_for_healthy(self, healthy_product):
        result = analyse(healthy_product)
        # No ultra-processed flag for NOVA 1
        assert not any("ultra-processed" in r.lower() for r in result["risk_indicators"])

    def test_returns_dict_with_required_keys(self, peanut_butter_product):
        result = analyse(peanut_butter_product)
        assert "risk_indicators" in result
        assert "positive_indicators" in result


# ---------------------------------------------------------------------------
# product_insights.score_explainer
# ---------------------------------------------------------------------------

class TestExplainNutriscore:
    def test_includes_grade_letter(self, peanut_butter_product):
        text = explain_nutriscore(peanut_butter_product)
        assert "NutriScore C" in text

    def test_includes_description(self, peanut_butter_product):
        text = explain_nutriscore(peanut_butter_product)
        assert "moderate" in text.lower()

    def test_missing_grade(self):
        text = explain_nutriscore({})
        assert "not available" in text.lower()

    def test_grade_a_description(self, healthy_product):
        text = explain_nutriscore(healthy_product)
        assert "NutriScore A" in text
        assert "excellent" in text.lower()


class TestExplainNova:
    def test_nova_4(self, peanut_butter_product):
        text = explain_nova(peanut_butter_product)
        assert "NOVA Group 4" in text
        assert "ultra-processed" in text.lower()

    def test_nova_1(self, healthy_product):
        text = explain_nova(healthy_product)
        assert "NOVA Group 1" in text

    def test_missing_nova(self):
        text = explain_nova({})
        assert "not available" in text.lower()


class TestExplain:
    def test_returns_all_keys(self, peanut_butter_product):
        result = explain(peanut_butter_product)
        assert set(result.keys()) == {"nutriscore", "nova", "nutrient_density"}


# ---------------------------------------------------------------------------
# product_insights.summary
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_includes_product_name(self, peanut_butter_product):
        text = generate(peanut_butter_product)
        assert "Smooth Kraft Peanut Butter" in text

    def test_includes_nutriscore(self, peanut_butter_product):
        text = generate(peanut_butter_product)
        assert "NutriScore C" in text

    def test_mentions_ultra_processed(self, peanut_butter_product):
        text = generate(peanut_butter_product)
        assert "ultra-processed" in text.lower()

    def test_mentions_allergens(self, peanut_butter_product):
        text = generate(peanut_butter_product)
        assert "peanuts" in text.lower()

    def test_healthy_product_no_ultra_processed(self, healthy_product):
        text = generate(healthy_product)
        assert "ultra-processed" not in text.lower()


# ---------------------------------------------------------------------------
# product_insights.pairings
# ---------------------------------------------------------------------------

class TestGetPairings:
    def test_returns_list(self, peanut_butter_product):
        result = get_pairings(peanut_butter_product)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_peanut_butter_pairings(self, peanut_butter_product):
        result = get_pairings(peanut_butter_product)
        # Should match "nut-butters" key
        assert "banana" in result

    def test_default_pairings_for_unknown_category(self):
        product = {"categories_tags": ["en:unknown-category-xyz"]}
        result = get_pairings(product)
        assert result == CATEGORY_PAIRINGS["default"]

    def test_no_categories(self):
        result = get_pairings({})
        assert result == CATEGORY_PAIRINGS["default"]


# ---------------------------------------------------------------------------
# product_insights.fetcher helpers
# ---------------------------------------------------------------------------

class TestBarcodeFromUrl:
    def test_extracts_barcode(self):
        url = "https://world.openfoodfacts.org/product/0068100084245/peanut-butter"
        assert _barcode_from_url(url) == "0068100084245"

    def test_raises_on_invalid_url(self):
        with pytest.raises(ValueError):
            _barcode_from_url("https://example.com/no-barcode-here")
