"""DuckDB-backed access to the Canada Open Food Facts dataset."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Iterable

import duckdb

from server.product_insights.off_config import (
    BASE_OFF_URL,
    OFF_COUNTRY_TAG,
    OFF_INSTANCE_DOMAIN,
    normalise_off_product_url,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATASET_ENV = "OFF_PARQUET_PATH"
_DB_PATH_ENV = "OFF_DUCKDB_PATH"
_DEFAULT_DATASET_CANDIDATES = (
    _PROJECT_ROOT / "off_dev.parquet",
    _PROJECT_ROOT / "product_insights" / "off_dev.parquet",
    _PROJECT_ROOT / "product_insights" / "food.parquet",
)
_NORMALIZED_REQUIRED_COLUMNS = {
    "code",
    "product_name",
    "brands",
    "categories",
    "categories_tags",
    "countries_tags",
    "nutriscore_grade",
    "nova_group",
    "ingredients_text",
    "product_url",
    "energy_kcal_100g",
    "fat_100g",
    "sugars_100g",
    "proteins_100g",
    "salt_100g",
    "fiber_100g",
}
_NUTRIMENT_COLUMN_MAP = {
    "energy_kcal_100g": "energy-kcal_100g",
    "fat_100g": "fat_100g",
    "sugars_100g": "sugars_100g",
    "proteins_100g": "proteins_100g",
    "salt_100g": "salt_100g",
    "fiber_100g": "fiber_100g",
    "saturated_fat_100g": "saturated-fat_100g",
    "carbohydrates_100g": "carbohydrates_100g",
}

_CONNECTION: duckdb.DuckDBPyConnection | None = None
_INITIALIZED_DATASET: Path | None = None
_LOCK = threading.RLock()


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _product_url_sql() -> str:
    return f"concat({_sql_literal(BASE_OFF_URL)}, code, '/')"


def _normalised_product_url_sql(column_name: str = "product_url") -> str:
    return (
        f"regexp_replace(coalesce({column_name}, {_sql_literal('')}), '^https?://[^/]+', "
        f"{_sql_literal(OFF_INSTANCE_DOMAIN)})"
    )


def _resolve_dataset_path() -> Path:
    configured_path = os.getenv(_DATASET_ENV)
    if configured_path:
        return Path(configured_path).expanduser().resolve()

    for candidate in _DEFAULT_DATASET_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()

    return _DEFAULT_DATASET_CANDIDATES[-1].resolve()


def _resolve_db_path() -> Path:
    configured_path = os.getenv(_DB_PATH_ENV)
    if not configured_path:
        raise ValueError(f"{_DB_PATH_ENV} is not configured")

    path = Path(configured_path).expanduser()
    return (path if path.is_absolute() else (_PROJECT_ROOT / path)).resolve()


def _connect() -> duckdb.DuckDBPyConnection:
    configured_path = os.getenv(_DB_PATH_ENV)
    if not configured_path:
        return duckdb.connect(":memory:")

    return duckdb.connect(str(_resolve_db_path()))


def _get_dataset_columns(dataset_path: Path) -> set[str]:
    connection = duckdb.connect()
    try:
        query = f"DESCRIBE SELECT * FROM read_parquet({_sql_literal(str(dataset_path))})"
        rows = connection.execute(query).fetchall()
        return {row[0] for row in rows}
    finally:
        connection.close()


def _build_raw_products_select_sql(dataset_path: Path) -> str:
    source = _sql_literal(str(dataset_path))
    product_url_expr = _product_url_sql()
    return f"""
SELECT
    code,
    coalesce(
        list_filter(product_name, item -> item.lang = 'main')[1].text,
        list_filter(product_name, item -> item.lang = 'en')[1].text,
        product_name[1].text
    ) AS product_name,
    brands,
    categories,
    categories_tags,
    countries_tags,
    nullif(lower(nutriscore_grade), 'unknown') AS nutriscore_grade,
    nova_group,
    labels,
    labels_tags,
    additives_tags,
    allergens_tags,
    coalesce(
        list_filter(ingredients_text, item -> item.lang = 'main')[1].text,
        list_filter(ingredients_text, item -> item.lang = 'en')[1].text,
        ingredients_text[1].text,
        ingredients
    ) AS ingredients_text,
    {product_url_expr} AS product_url,
    CAST(NULL AS VARCHAR) AS image_url,
    serving_size,
    try_cast(serving_quantity AS DOUBLE) AS serving_quantity,
    packaging,
    packaging_tags,
    ingredients_analysis_tags,
    list_filter(nutriments, item -> item.name = 'energy-kcal')[1]."100g" AS energy_kcal_100g,
    list_filter(nutriments, item -> item.name = 'fat')[1]."100g" AS fat_100g,
    list_filter(nutriments, item -> item.name = 'sugars')[1]."100g" AS sugars_100g,
    list_filter(nutriments, item -> item.name = 'proteins')[1]."100g" AS proteins_100g,
    list_filter(nutriments, item -> item.name = 'salt')[1]."100g" AS salt_100g,
    list_filter(nutriments, item -> item.name = 'fiber')[1]."100g" AS fiber_100g,
    list_filter(nutriments, item -> item.name = 'saturated-fat')[1]."100g" AS saturated_fat_100g,
    list_filter(nutriments, item -> item.name = 'carbohydrates')[1]."100g" AS carbohydrates_100g
FROM read_parquet({source})
WHERE code IS NOT NULL
""".strip()


def build_products_select_sql(dataset_path: str | Path, canada_only: bool = True) -> str:
    """Build the canonical SELECT used for the products view."""
    path = Path(dataset_path).expanduser().resolve()
    columns = _get_dataset_columns(path)
    product_url_expr = _product_url_sql()
    country_filter = (
        f"AND list_contains(countries_tags, {_sql_literal(OFF_COUNTRY_TAG)})"
        if canada_only
        else ""
    )

    if _NORMALIZED_REQUIRED_COLUMNS.issubset(columns):
        source = _sql_literal(str(path))
        # Explicitly select all columns except product_url, then override with generated URL
        return f"""
SELECT
    * REPLACE (
        { _normalised_product_url_sql() } AS product_url
    )
FROM read_parquet({source})
WHERE code IS NOT NULL
  {country_filter}
""".strip()

    if canada_only:
        return (
            _build_raw_products_select_sql(path)
            + f"\n  AND list_contains(countries_tags, {_sql_literal(OFF_COUNTRY_TAG)})"
        )

    return _build_raw_products_select_sql(path)


def _ensure_connection() -> duckdb.DuckDBPyConnection:
    global _CONNECTION, _INITIALIZED_DATASET

    dataset_path = _resolve_dataset_path()
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. Set OFF_PARQUET_PATH or create off_dev.parquet."
        )

    if _CONNECTION is None:
        _CONNECTION = _connect()
        _CONNECTION.execute("PRAGMA threads=4")

    # Always rebuild views to ensure URL generation/domain and filters stay up-to-date.
    select_sql_all = build_products_select_sql(dataset_path, canada_only=False)
    select_sql_canada = build_products_select_sql(dataset_path, canada_only=True)
    _CONNECTION.execute(f"CREATE OR REPLACE VIEW products_all AS {select_sql_all}")
    _CONNECTION.execute(f"CREATE OR REPLACE VIEW products AS {select_sql_canada}")
    _INITIALIZED_DATASET = dataset_path

    return _CONNECTION


def get_dataset_path() -> Path:
    """Return the resolved parquet dataset path currently configured."""
    return _resolve_dataset_path()


def _rows_from_cursor(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_all(query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    """Execute a query against the persistent DuckDB connection."""
    with _LOCK:
        connection = _ensure_connection()
        cursor = connection.execute(query, list(params or []))
        return _rows_from_cursor(cursor)


def fetch_one(query: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
    """Execute a query and return the first row as a dict, if present."""
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def build_nutriments_from_row(row: dict[str, Any]) -> dict[str, float]:
    """Rebuild the nutriments dict shape used by the existing pipeline."""
    nutriments: dict[str, float] = {}

    for column_name, nutriment_key in _NUTRIMENT_COLUMN_MAP.items():
        value = row.get(column_name)
        if value is None:
            continue
        nutriments[nutriment_key] = float(value)

    energy_kcal = nutriments.get("energy-kcal_100g")
    if energy_kcal is not None:
        nutriments["energy-kcal"] = energy_kcal

    return nutriments


def row_to_product(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a products-view row into the normalised product dict."""
    barcode = (row.get("code") or "").strip()

    return {
        "_barcode": barcode,
        "code": barcode,
        "product_name": row.get("product_name") or "Unknown product",
        "brands": row.get("brands"),
        "categories": row.get("categories") or "",
        "categories_tags": _as_list(row.get("categories_tags")),
        "countries_tags": _as_list(row.get("countries_tags")),
        "nutriscore_grade": row.get("nutriscore_grade"),
        "nova_group": row.get("nova_group"),
        "ingredients_text": row.get("ingredients_text") or "",
        "labels": row.get("labels") or "",
        "labels_tags": _as_list(row.get("labels_tags")),
        "additives_tags": _as_list(row.get("additives_tags")),
        "allergens_tags": _as_list(row.get("allergens_tags")),
        "image_url": row.get("image_url"),
        "link": normalise_off_product_url(
            row.get("product_url"),
            barcode,
            row.get("product_name"),
        ),
        "serving_size": row.get("serving_size"),
        "serving_quantity": row.get("serving_quantity"),
        "packaging": row.get("packaging"),
        "packaging_tags": _as_list(row.get("packaging_tags")),
        "ingredients_analysis_tags": _as_list(row.get("ingredients_analysis_tags")),
        "nutriments": build_nutriments_from_row(row),
    }