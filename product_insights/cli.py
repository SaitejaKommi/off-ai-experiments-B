"""Command-line interface for the Product Intelligence Engine."""

import argparse
import sys

from product_insights.fetcher import fetch_product
from product_insights.insight_engine import analyse
from product_insights.score_explainer import explain
from product_insights.summary import generate
from product_insights.recommender import get_alternatives
from product_insights.pairings import get_pairings


def _section(title: str) -> str:
    return f"\n{title}\n" + "-" * len(title)


def run(barcode_or_url: str, show_scores: bool = False) -> None:
    """Fetch a product and print the full intelligence report."""
    print(f"\nFetching product: {barcode_or_url} …")

    try:
        product = fetch_product(barcode_or_url)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    name = product.get("product_name") or "Unknown product"

    print(f"\nProduct: {name}")

    # Summary
    print(_section("Summary"))
    print(generate(product))

    # Score explanation (optional)
    if show_scores:
        scores = explain(product)
        print(_section("Score Explanations"))
        print(scores["nutriscore"])
        print(scores["nova"])
        print(scores["nutrient_density"])

    # Risk / Positive indicators
    indicators = analyse(product)

    risks = indicators["risk_indicators"]
    positives = indicators["positive_indicators"]

    print(_section("Risk indicators"))
    if risks:
        for r in risks:
            print(f"  ⚠  {r}")
    else:
        print("  None detected.")

    print(_section("Positive indicators"))
    if positives:
        for p in positives:
            print(f"  ✓  {p}")
    else:
        print("  None detected.")

    # Alternatives
    print(_section("Better alternatives"))
    alternatives = get_alternatives(product)
    if alternatives:
        for i, alt in enumerate(alternatives, start=1):
            print(f"  {i}. {alt['name']} ({alt['nutriscore_grade']})")
            print(f"     {alt['reason']}")
    else:
        print("  No alternatives found.")

    # Pairings
    print(_section("Suggested pairings"))
    pairings = get_pairings(product)
    for item in pairings:
        print(f"  • {item.capitalize()}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m product_insights.cli",
        description="Product Intelligence Engine – powered by Open Food Facts",
    )
    parser.add_argument(
        "barcode_or_url",
        help="Product barcode (e.g. 0068100084245) or Open Food Facts product URL.",
    )
    parser.add_argument(
        "--scores",
        action="store_true",
        default=False,
        help="Include detailed NutriScore and NOVA score explanations.",
    )
    args = parser.parse_args()
    run(args.barcode_or_url, show_scores=args.scores)


if __name__ == "__main__":
    main()
