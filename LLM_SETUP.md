# LLM Setup Guide (Gemini + Groq)

This project supports **both Gemini and Groq** as LLM providers.

Current defaults:
- `LLM_PROVIDER=groq`
- `GROQ_MODEL=llama-3.3-70b-versatile`
- `USE_LLM_PAIRINGS=true`
- `LLM_FALLBACK_TO_RULES=false` (LLM-only mode)

## What Uses the LLM

- `product_insights/summary.py` → Product summary
- `product_insights/score_explainer.py` → NutriScore and NOVA explanations
- `product_insights/pairings.py` → Suggested pairings
- `product_insights/insight_engine.py` → Extra contextual positives

If LLM fallback is enabled (`LLM_FALLBACK_TO_RULES=true`), rule-based text is used when LLM is unavailable.

## Quick Setup

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Create `.env`

```bash
copy .env.example .env
```

### 3) Choose provider

#### Option A: Groq (default)

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

#### Option B: Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=models/gemini-2.0-flash
```

### 4) Common flags

```env
USE_LLM_PAIRINGS=true
LLM_FALLBACK_TO_RULES=false
```

## Verify Configuration

```bash
python -c "from product_insights.llm_config import LLMConfig; print(LLMConfig.get_status())"
```

Expected examples:
- `✓ Groq API configured (llama-3.3-70b-versatile)`
- `✓ Gemini API configured (models/gemini-2.0-flash)`

## Test End-to-End

```bash
python -m product_insights.cli 0068100084245
python -m product_insights.cli 0068100084245 --scores
```

## Provider Notes

### Groq
- Fast responses
- Good for daily development usage

### Gemini
- Works well, but can hit free-tier quota depending on account/project limits

## Troubleshooting

### `No module named 'groq'`

```bash
pip install groq
```

### `GEMINI_API_KEY not set` or `GROQ_API_KEY not set`

Set the matching key in `.env` based on `LLM_PROVIDER`.

### Gemini quota/rate limit errors (429)

- Check billing/quota for your Gemini project
- Retry later or switch provider to Groq

### Empty LLM output

- Confirm `.env` exists
- Confirm provider key is valid
- Set `LLM_FALLBACK_TO_RULES=true` if you want graceful fallback output

## Security

- Never commit `.env`
- Keep only placeholders in `.env.example`
- Rotate keys immediately if exposed
