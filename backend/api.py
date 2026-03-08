"""FastAPI wrapper for AI-powered product insights."""

import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path so we can import product_insights
sys.path.insert(0, str(Path(__file__).parent.parent))

from product_insights.fetcher import fetch_product
from product_insights.insight_engine import analyse
from product_insights.summary import generate
from product_insights.score_explainer import explain
from product_insights.recommender import get_alternatives
from product_insights.pairings import get_pairings
from backend.models import (
    ProductInsightsRequest,
    ProductInsightsResponse,
    ProductData,
    HealthCheckResponse,
)

app = FastAPI(
    title="AI Product Insights API",
    description="AI-powered insights for Open Food Facts products",
    version="1.0.0",
)

# Enable CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/product-insights", response_model=ProductInsightsResponse)
def get_product_insights(request: ProductInsightsRequest):
    """
    Get AI-powered insights for a product.
    
    Parameters:
    - barcode: Product barcode (e.g., "0068100084245")
    
    Returns:
    - Structured insights including summary, indicators, score explanation,
      similar products, and food pairings.
    """
    try:
        # Fetch product from OFF API
        product = fetch_product(request.barcode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Product not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

    try:
        # Extract basic product info
        product_name = product.get("product_name") or "Unknown product"
        image_url = product.get("image_url")
        nutriscore = product.get("nutriscore_grade")
        nova = product.get("nova_group")
        brands = product.get("brands")

        # Generate insights
        summary = generate(product)
        indicators = analyse(product)
        score_explanations = explain(product)
        alternatives = get_alternatives(product)
        pairings = get_pairings(product)

        # Build response
        response = ProductInsightsResponse(
            product=ProductData(
                name=product_name,
                image_url=image_url,
                nutriscore=nutriscore,
                nova=nova,
                brands=brands,
            ),
            summary=summary,
            risk_indicators=indicators.get("risk_indicators", []),
            positive_indicators=indicators.get("positive_indicators", []),
            score_explanation={
                "nutriscore": score_explanations.get("nutriscore", ""),
                "nova": score_explanations.get("nova", ""),
                "nutrient_density": score_explanations.get("nutrient_density", ""),
            },
            similar_products=alternatives,
            pairings=pairings if isinstance(pairings, list) else [],
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing product: {str(e)}")


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "name": "AI Product Insights API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "product_insights": "/product-insights",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
