"""Create a smaller Canada-only development parquet dataset for Project B."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.product_insights.data_store import build_products_select_sql


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a normalized Canada-only OFF development dataset.",
    )
    parser.add_argument(
        "--source",
        default=str(ROOT / "product_insights" / "food.parquet"),
        help="Path to the full OFF parquet dataset.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "product_insights" / "off_dev.parquet"),
        help="Path for the generated development parquet dataset.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50000,
        help="Maximum number of Canada products to include.",
    )
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not source_path.exists():
        raise SystemExit(f"Source dataset not found: {source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    select_sql = build_products_select_sql(source_path)
    connection = duckdb.connect()
    try:
        connection.execute(
            f"COPY ({select_sql} LIMIT {max(args.limit, 1)}) TO {_sql_literal(str(output_path))} (FORMAT PARQUET)"
        )
        row_count = connection.execute(
            f"SELECT COUNT(*) FROM read_parquet({_sql_literal(str(output_path))})"
        ).fetchone()[0]
    finally:
        connection.close()

    print(f"Canada dev dataset created: {output_path}")
    print(f"Rows written: {row_count}")


if __name__ == "__main__":
    main()