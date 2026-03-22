"""Fetch product data from the local DuckDB-backed OFF dataset."""

from server.product_insights.data_store import fetch_one, row_to_product


def _barcode_from_url(url: str) -> str:
    """Extract a barcode from an OFF product URL like
    https://ca-en.openfoodfacts.org/product/0068100084245/...
    """
    for part in url.rstrip("/").split("/"):
        if part.isdigit():
            return part
    raise ValueError(f"Could not extract barcode from URL: {url}")


def fetch_product(barcode_or_url: str) -> dict:
    """Fetch and return a normalised product dictionary.

    Parameters
    ----------
    barcode_or_url:
        Either a numeric barcode string (e.g. ``"0068100084245"``) or a full
        Open Food Facts product URL.

    Returns
    -------
    dict
        Normalised product dictionary from the DuckDB ``products`` view.

    Raises
    ------
    ValueError
        If the product is not found in the local Canada dataset.
    """
    if barcode_or_url.startswith("http"):
        barcode = _barcode_from_url(barcode_or_url)
    else:
        barcode = barcode_or_url.strip()

    row = fetch_one(
        """
        SELECT *
        FROM products
        WHERE code = ?
        LIMIT 1
        """,
        [barcode],
    )

    if row is None:
        raise ValueError(f"Product not found for barcode: {barcode}")

    product = row_to_product(row)
    product["_barcode"] = barcode
    return product
