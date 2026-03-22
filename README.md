# Product Intelligence Engine (Canada + LLM)

AI-powered food product analysis using a DuckDB-backed Open Food Facts Canada catalog and LLM-generated insights.

## Overview

This project takes a product barcode (or OFF product URL) and produces:

- LLM-generated product summary
- LLM-generated NutriScore + NOVA explanations
- Risk indicators and positive indicators
- Better alternatives from the **Canada OFF catalog**
- LLM-generated suggested food pairings
- Fast DuckDB product lookup from a Canada-only parquet dataset

## What Changed (LLM Integration)

The project moved from mostly rule-based text to LLM-first outputs.

### Before
- Static/hardcoded text templates for summaries and explanations
- Rule-based pairings from category maps
- HTTP lookups against Open Food Facts for fetch and alternatives

### Now
- LLM-first summaries, score explanations, and pairings
- Groq model support added and enabled by default
- DuckDB-backed Canada-only product lookup and recommendation queries
- Optional rule fallback controlled by `LLM_FALLBACK_TO_RULES`

## Model and Provider

- Default provider: `groq`
- Default model: `llama-3.3-70b-versatile`
- Optional provider: `gemini`

Configuration is in `.env` via variables described in `.env.example`.

## Architecture

```text
Barcode / OFF URL
  -> data_store.py (persistent DuckDB connection + products view)
  -> fetcher.py (DuckDB product lookup)
   -> insight_engine.py (signals + optional LLM contextual insights)
   -> summary.py (LLM-first summary)
   -> score_explainer.py (LLM-first NutriScore/NOVA explanation)
  -> recommender.py (Canada alternatives by specific category)
   -> pairings.py (LLM-first pairings)
   -> cli.py (final report output)
```

## Repository Structure

```text
client/
  extension/

server/
  backend/
  product_insights/
  utils/
  scripts/
  tests/
```

## Setup (Beginner Friendly)

1) Create and activate a virtual environment

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Create the Canada development dataset

```bash
python server/scripts/create_canada_dev_dataset.py
```

This creates `server/product_insights/off_dev.parquet` with about 50k Canada products.

4) Optional dataset configuration

```bash
# default shown
OFF_PARQUET_PATH=server/product_insights/off_dev.parquet

# optional: set only if you explicitly want a file-backed DuckDB database
OFF_DUCKDB_PATH=off.duckdb
```

5) Create your environment file

```bash
copy .env.example .env
```

6) Edit `.env`

- Set `LLM_PROVIDER=groq` (default)
- Add `GROQ_API_KEY=...`
- Keep `USE_LLM_PAIRINGS=true`
- Keep `LLM_FALLBACK_TO_RULES=false` for LLM-only behavior

## Run

```bash
python -m server.product_insights.cli 0068100084245
python -m server.product_insights.cli 0068100084245 --scores
```

## Validate

Run tests:

```bash
python -m pytest server/tests/ -q
```

Check LLM config status:

```bash
python -c "from server.product_insights.llm_config import LLMConfig; print(LLMConfig.get_status())"
```

## Security Notes

- `.env` is ignored by git.
- Never commit real API keys.
- `.env.example` contains placeholders only.

## Current Behavior

- OFF data source is a Canada-only DuckDB `products` view
- LLM provider default is Groq
- LLM mode is enabled by default
- Rule fallback is disabled by default (can be re-enabled via env)

## DuckDB Notes

- By default each process opens an in-memory DuckDB connection to avoid file locks.
- Set `OFF_DUCKDB_PATH` only if you explicitly want a file-backed DuckDB database.
- The `products` view is created once per configured dataset path.
- All product fetch and alternatives queries read from `products`.
- If `server/product_insights/off_dev.parquet` exists it is preferred over the full `food.parquet` file.
