# Product Intelligence Engine (Canada + LLM)

AI-powered food product analysis using Open Food Facts (Canada catalog) and LLM-generated insights.

## Overview

This project takes a product barcode (or OFF product URL) and produces:

- LLM-generated product summary
- LLM-generated NutriScore + NOVA explanations
- Risk indicators and positive indicators
- Better alternatives from the **Canada OFF catalog**
- LLM-generated suggested food pairings

## What Changed (LLM Integration)

The project moved from mostly rule-based text to LLM-first outputs.

### Before
- Static/hardcoded text templates for summaries and explanations
- Rule-based pairings from category maps
- Global OFF catalog lookups (`world.openfoodfacts.org`)

### Now
- LLM-first summaries, score explanations, and pairings
- Groq model support added and enabled by default
- Canada-only OFF endpoints (`ca-en.openfoodfacts.org`) for fetch and alternatives
- Optional rule fallback controlled by `LLM_FALLBACK_TO_RULES`

## Model and Provider

- Default provider: `groq`
- Default model: `llama-3.3-70b-versatile`
- Optional provider: `gemini`

Configuration is in `.env` via variables described in `.env.example`.

## Architecture

```text
Barcode / OFF URL
   -> fetcher.py (Canada OFF API)
   -> insight_engine.py (signals + optional LLM contextual insights)
   -> summary.py (LLM-first summary)
   -> score_explainer.py (LLM-first NutriScore/NOVA explanation)
   -> recommender.py (Canada OFF alternatives by specific category)
   -> pairings.py (LLM-first pairings)
   -> cli.py (final report output)
```

## Repository Structure

```text
product_insights/
  cli.py
  fetcher.py
  insight_engine.py
  llm_client.py
  llm_config.py
  pairings.py
  recommender.py
  score_explainer.py
  summary.py

utils/
  nutrition_rules.py
  product_helpers.py

tests/
  test_product_insights.py
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

3) Create your environment file

```bash
copy .env.example .env
```

4) Edit `.env`

- Set `LLM_PROVIDER=groq` (default)
- Add `GROQ_API_KEY=...`
- Keep `USE_LLM_PAIRINGS=true`
- Keep `LLM_FALLBACK_TO_RULES=false` for LLM-only behavior

## Run

```bash
python -m product_insights.cli 0068100084245
python -m product_insights.cli 0068100084245 --scores
```

## Validate

Run tests:

```bash
python -m pytest tests/ -q
```

Check LLM config status:

```bash
python -c "from product_insights.llm_config import LLMConfig; print(LLMConfig.get_status())"
```

## Security Notes

- `.env` is ignored by git.
- Never commit real API keys.
- `.env.example` contains placeholders only.

## Current Behavior

- OFF data source is Canada-only (`ca-en.openfoodfacts.org`)
- LLM provider default is Groq
- LLM mode is enabled by default
- Rule fallback is disabled by default (can be re-enabled via env)
