/**
 * Content script for Open Food Facts product pages.
 * 
 * Responsibility: Extract barcode from the product URL and store it.
 * Does NOT inject any UI elements into the webpage.
 */

/**
 * Extract barcode from the current product page URL.
 * 
 * URL format: https://[location].openfoodfacts.org/product/{barcode}/product-name
 * Example: https://ca.openfoodfacts.org/product/0068100084245/smooth-kraft
 * 
 * @returns {string|null} The barcode if found, null otherwise
 */
function extractBarcodeFromUrl() {
  const pathname = window.location.pathname;
  console.log("[AI Insights] Content script pathname:", pathname);
  
  const parts = pathname.split("/").filter(Boolean);
  console.log("[AI Insights] URL parts:", parts);
  
  // URL structure: /product/{barcode}/product-name
  // parts[0] = "product"
  // parts[1] = barcode
  if (parts.length >= 2 && parts[0] === "product") {
    const barcode = parts[1];
    // Validate: barcode should be numeric
    if (/^\d+$/.test(barcode)) {
      console.log("[AI Insights] Valid barcode extracted:", barcode);
      return barcode;
    } else {
      console.log("[AI Insights] Barcode part is not numeric:", barcode);
    }
  }
  
  return null;
}

/**
 * Send barcode to background script via chrome.runtime.sendMessage
 */
function notifyAboutProduct(barcode) {
  const message = {
    type: "OFF_PRODUCT_PAGE",
    barcode: barcode
  };
  
  console.log("[AI Insights] Sending message to background:", message);
  
  chrome.runtime.sendMessage(message, (response) => {
    if (chrome.runtime.lastError) {
      console.error("[AI Insights] Error sending message:", chrome.runtime.lastError);
    } else {
      console.log("[AI Insights] Background script response:", response);
    }
  });
}

// Extract barcode and notify background script
console.log("[AI Insights] Content script initialized");
const barcode = extractBarcodeFromUrl();
if (barcode) {
  notifyAboutProduct(barcode);
} else {
  console.log("[AI Insights] No valid barcode found in URL");
}
