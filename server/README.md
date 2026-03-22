# Server

Backend code and data-processing logic for AI Product Insights.

## Contents

- `backend/` - FastAPI service
- `product_insights/` - Core insight engine modules
- `utils/` - Nutrition rules and helper utilities
- `scripts/` - Data preparation scripts
- `tests/` - Unit tests

## Common Commands

```bash
python server/scripts/create_canada_dev_dataset.py
python -m uvicorn server.backend.api:app --host 0.0.0.0 --port 8000 --reload
python -m server.product_insights.cli 0068100084245 --scores
python -m pytest server/tests/ -q
```
