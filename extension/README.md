# Browser Extension - AI Product Insights

A Chrome/Firefox extension that shows AI insights for Open Food Facts products in the extension popup.

## What Changed

- No UI is injected into Open Food Facts pages.
- The extension only reads the product barcode from the active tab URL.
- Insights are rendered only inside the popup.

## Features

- AI summary for the current product
- Health indicators (positives and risks)
- Score explanation
- Product discovery alternatives (with fallback when strict matches are scarce)
- Suggested pairings
- Empty/loading/error popup states

## Installation (Development)

### Prerequisites

1. Start backend API on `http://localhost:8000`:
   ```bash
   python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
   ```
2. See `../backend/README.md` for backend setup details.

### Load Extension in Chrome

1. Open `chrome://extensions/`
2. Enable Developer mode
3. Click Load unpacked
4. Select the `extension/` folder

### Load Extension in Firefox

1. Open `about:debugging`
2. Click This Firefox
3. Click Load Temporary Add-on
4. Select any file in the `extension/` folder

## Usage

1. Open an Open Food Facts product URL, for example:
   - `https://ca.openfoodfacts.org/product/0068100084245/smooth-kraft`
2. Click the extension icon.
3. Popup fetches insights for the active tab product barcode.

If the current tab is not a product URL, popup shows an empty state.

## Current File Structure

```
extension/
├── manifest.json
├── background/
│   └── background.js
├── content/
│   └── content.js
├── popup/
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
└── README.md
```

## Architecture

1. `content/content.js`
- Runs on `https://*.openfoodfacts.org/product/*`
- Extracts barcode from URL
- Sends barcode to background

2. `background/background.js`
- Stores latest barcode in `chrome.storage.local`

3. `popup/popup.js`
- Reads active tab URL and validates product barcode
- Calls `POST http://localhost:8000/product-insights`
- Renders summary, indicators, score explanation, alternatives, and pairings

## API Contract Used

`POST /product-insights`

Request:
```json
{
  "barcode": "0068100084245"
}
```

Response fields used:
- `product.name`
- `summary`
- `positive_indicators`
- `risk_indicators`
- `score_explanation`
- `similar_products`
- `pairings`

## Permissions

- `storage`
- `activeTab`
- `host_permissions`
  - `https://*.openfoodfacts.org/product/*`
  - `http://localhost:8000/*`

## Troubleshooting

1. Backend health check:
   - `http://localhost:8000/health` should return `{"status":"ok"}`
2. Reload extension after code updates.
3. Confirm you are on a URL containing `/product/{barcode}/`.
4. Check popup console and service worker console for logs.
