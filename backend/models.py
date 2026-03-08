"""Pydantic models for AI Product Insights API."""

from typing import Optional, List
from pydantic import BaseModel


class ProductData(BaseModel):
    """Basic product information."""
    name: str
    image_url: Optional[str] = None
    nutriscore: Optional[str] = None
    nova: Optional[int] = None
    brands: Optional[str] = None


class ProductInsightsRequest(BaseModel):
    """Request body for product insights."""
    barcode: str


class ProductInsightsResponse(BaseModel):
    """Complete AI-powered product insights response."""
    product: ProductData
    summary: str
    risk_indicators: List[str]
    positive_indicators: List[str]
    score_explanation: dict
    similar_products: List[dict]
    pairings: List[str]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
