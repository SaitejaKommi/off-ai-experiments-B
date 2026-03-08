# Backend API - AI Product Insights

FastAPI wrapper for the AI-powered product insights engine.

## Setup

1. Install dependencies:
```bash
pip install -r ../requirements.txt
```

2. Set up environment variables (if using LLM features):
```bash
# Create a .env file in the root directory with:
GROQ_API_KEY=your_key_here
# or
GOOGLE_API_KEY=your_key_here
```

## Running the API

From the project root:

```bash
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **Alternative docs**: `http://localhost:8000/redoc`

## Endpoints

### Health Check
```
GET /health

Response:
{
  "status": "ok"
}
```

### Product Insights
```
POST /product-insights

Request Body:
{
  "barcode": "0068100084245"
}

Response:
{
  "product": {
    "name": "Product Name",
    "image_url": "...",
    "nutriscore": "C",
    "nova": 4,
    "brands": "Brand Name"
  },
  "summary": "...",
  "risk_indicators": [...],
  "positive_indicators": [...],
  "score_explanation": {...},
  "similar_products": [...],
  "pairings": [...]
}
```

## Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Get product insights
curl -X POST http://localhost:8000/product-insights \
  -H "Content-Type: application/json" \
  -d '{"barcode": "0068100084245"}'
```

## Architecture

The API is a thin wrapper around the existing `product_insights` module:

1. **Fetcher**: Retrieves product data from Open Food Facts API
2. **Insight Engine**: Analyzes nutrients and generates health indicators
3. **Summary Generator**: Creates human-readable product summaries
4. **Score Explainer**: Explains NutriScore and NOVA ratings
5. **Recommender**: Finds similar products with better nutritional scores
6. **Pairings**: Suggests complementary foods

All existing CLI logic is preserved and reused.
