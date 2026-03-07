# off-ai-experiments-B — Product Intelligence Engine

AI-powered product insights backed by [Open Food Facts](https://world.openfoodfacts.org/).

## What it does

Given a product barcode or an Open Food Facts product URL the engine produces:

| Output | Description |
|---|---|
| **Product summary** | Plain-language overview of the product |
| **Health explanation** | Explanation of NutriScore, NOVA group, and nutrient density |
| **Risk indicators** | Warnings (high fat, high sugar, ultra-processed, …) |
| **Positive indicators** | Good news (high protein, organic label, good NutriScore, …) |
| **Better alternatives** | Healthier products in the same category |
| **Complementary pairings** | Foods that pair well with this product |

## Architecture

```
Product Barcode / URL
        ↓
Open Food Facts API Fetch   (product_insights/fetcher.py)
        ↓
Product Insight Engine
        ├── Insight Engine      (product_insights/insight_engine.py)
        ├── Score Explainer     (product_insights/score_explainer.py)
        ├── Summary Generator   (product_insights/summary.py)
        ├── Recommendation Eng. (product_insights/recommender.py)
        └── Pairing Suggestions (product_insights/pairings.py)
        ↓
CLI / JSON output               (product_insights/cli.py)
```

## Repository structure

```
off-ai-experiments-B/
│
├── product_insights/
│   ├── __init__.py
│   ├── __main__.py        ← enables python -m product_insights.cli
│   ├── fetcher.py
│   ├── insight_engine.py
│   ├── score_explainer.py
│   ├── recommender.py
│   ├── pairings.py
│   ├── summary.py
│   └── cli.py
│
├── utils/
│   ├── __init__.py
│   ├── nutrition_rules.py
│   └── product_helpers.py
│
├── tests/
│   ├── __init__.py
│   └── test_product_insights.py
│
├── requirements.txt
└── README.md
```

## Quick start

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run from the command line

```bash
# Using a barcode
python -m product_insights.cli 0068100084245

# Using an Open Food Facts URL
python -m product_insights.cli https://world.openfoodfacts.org/product/0068100084245/

# Include detailed score explanations
python -m product_insights.cli 0068100084245 --scores
```

### Example output

```
Fetching product: 0068100084245 …

Product: Smooth Kraft Peanut Butter

Summary
-------
Smooth Kraft Peanut Butter is a product with moderate nutritional quality
(NutriScore C). It is classified as an ultra-processed food, which may contain
additives, artificial flavors, and emulsifiers. It contains high levels of fat,
a good source of protein. Contains allergens: peanuts, soybeans.

Risk indicators
---------------
  ⚠  High fat
  ⚠  High saturated fat
  ⚠  High calorie density
  ⚠  Ultra-processed food (NOVA 4)

Positive indicators
-------------------
  ✓  High protein

Better alternatives
-------------------
  1. Organic Peanut Butter (B)
     NutriScore B and lower sugar and lower fat

Suggested pairings
------------------
  • Banana
  • Whole grain bread
  • Oatmeal
  • Apple slices
  • Celery
```

## Run tests

```bash
python -m pytest tests/ -v
```

## Future enhancements

- **LLM summarisation** – replace rule-based summaries with an LLM prompt
- **Vector similarity search** – find similar products via embeddings
- **Personalised recommendations** – filter by user dietary preferences
