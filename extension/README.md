# Browser Extension - AI Product Insights

A Chrome/Firefox browser extension that augments Open Food Facts Canada product pages with AI-powered insights.

## Features

- **AI Summaries**: Automatic product summaries in plain language
- **Health Indicators**: Risk and positive nutritional indicators
- **Score Explanations**: NutriScore and NOVA processing explanations
- **Similar Products**: Find healthier alternatives in the same category
- **Food Pairings**: Complementary food suggestions
- **Bilingual Support**: Works with both EN and FR versions of OFF Canada
- **Smart Loading**: Loading skeleton while fetching insights
- **Error Handling**: Graceful fallback if backend is unavailable

## Installation (Development)

### Prerequisites

1. Backend API must be running on `http://localhost:8000`
   See [../backend/README.md](../backend/README.md) for setup instructions

### Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Navigate to the `extension/` folder and select it
5. The extension should now appear in your extensions list

### Load Extension in Firefox

1. Open Firefox and go to `about:debugging`
2. Click **This Firefox** (left sidebar)
3. Click **Load Temporary Add-on**
4. Select any file in the `extension/` folder
5. The extension should now appear in your Firefox toolbar

## Usage

1. Navigate to any product page on ca.openfoodfacts.org:
   - Examples:
     - https://ca-en.openfoodfacts.org/product/0068100084245/smooth-kraft
     - https://ca-fr.openfoodfacts.org/product/0068100084245/kraft-lisse

2. The extension will automatically:
   - Extract the product barcode from the URL
   - Fetch insights from the backend API
   - Inject a clean insights panel on the page

3. Click on collapsible sections to expand/collapse:
   - Similar Products
   - Food Pairings
   - Score Explanations

## File Structure

```
extension/
├── manifest.json           # Extension configuration (Manifest v3)
├── content.js             # Content script (runs on product pages)
├── inject.css             # Styles for insights panel
├── background.js          # Service worker for background tasks
├── popup.html             # Extension popup UI
├── popup.js               # Popup functionality
└── README.md              # This file
```

## How It Works

### 1. Content Script Injection
- Runs automatically on ca.openfoodfacts.org product pages
- Extracts barcode from URL (e.g., `/product/0068100084245/...`)
- Calls backend API with the barcode

### 2. Backend Communication
- Sends POST request to `http://localhost:8000/product-insights`
- Receives structured JSON response with:
  - Product information
  - Summary
  - Risk/positive indicators
  - Score explanations
  - Similar products
  - Food pairings

### 3. UI Injection
- Creates insights card from API response
- Injects into page below product title
- Applies custom CSS styling
- Shows loading skeleton while fetching

## Configuration

### Backend URL
To change the backend URL, edit `content.js`:
```javascript
const API_BASE_URL = "http://localhost:8000";
```

### Auto-Start Mode
To disable auto-injection on page load, comment out the last line in `content.js`:
```javascript
// injectAIInsights();  // Uncomment to disable auto-injection
```

## Troubleshooting

### "Backend: Not Connected" Error
1. Make sure the backend API is running:
   ```bash
   python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
   ```

2. Check that `http://localhost:8000/health` returns `{"status": "ok"}`

3. Check browser console for errors (F12 → Console tab)

### Insights Not Appearing
1. Make sure you're on a valid OFF Canada product page
2. Open browser DevTools (F12)
3. Check the Console tab for any errors
4. Verify URL format: `ca.openfoodfacts.org/product/{barcode}/...`

### CORS Errors
If you see CORS errors, make sure the backend has CORS enabled. The provided API already enables CORS for all origins.

## API Endpoints Used

### POST /product-insights
```json
Request:
{
  "barcode": "0068100084245"
}

Response:
{
  "product": {...},
  "summary": "...",
  "risk_indicators": [...],
  "positive_indicators": [...],
  "score_explanation": {...},
  "similar_products": [...],
  "pairings": [...]
}
```

## Permissions

- `activeTab`: Access to current tab information
- `scripting`: Ability to inject scripts
- `host_permissions`: Access to OFF Canada and backend API

## Performance

- Panel loads asynchronously so it doesn't block page rendering
- Uses in-process caching for repeated requests
- Skeleton loading state provides visual feedback
- Collapsible sections reduce initial panel height

## Browser Compatibility

- **Chrome 88+**: Fully supported
- **Firefox 109+**: Fully supported
- **Edge 88+**: Fully supported (Chromium-based)

## Development

### Modify Styles
Edit `inject.css` to adjust the appearance of the insights panel.

### Modify Content Script Logic
Edit `content.js` to change how barcode extraction, API calls, or UI injection works.

### Debug
1. Right-click extension icon → Inspect popup
2. Go to `chrome://extensions/` and click "Inspect views → service worker"
3. Check browser console on product pages (F12 → Console)

## Future Enhancements

- [ ] Settings page for user preferences
- [ ] Caching of recently viewed products
- [ ] Offline mode with cached data
- [ ] Dark mode theme
- [ ] Product comparison tool
- [ ] Share insights to social media

## License

Part of the open-ai-experiments-B project.

## Support

For issues or suggestions, check:
- Extension console logs (F12 → Console)
- Backend logs
- [Backend README](../backend/README.md)
