/**
 * Background Service Worker
 * 
 * Responsibility: Receive barcode messages from content script and store them locally.
 */

console.log("[AI Insights] Background service worker initialized");

/**
 * Listen for messages from content script
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("[AI Insights] Background received message:", request, "from tab:", sender.tab.id);
  
  if (request.type === "OFF_PRODUCT_PAGE") {
    const barcode = request.barcode;
    console.log("[AI Insights] Processing barcode:", barcode);
    
    // Store the latest barcode in chrome.storage.local
    chrome.storage.local.set(
      { latest_barcode: barcode },
      () => {
        if (chrome.runtime.lastError) {
          console.error("[AI Insights] Storage error:", chrome.runtime.lastError);
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          console.log("[AI Insights] Successfully stored barcode in chrome.storage.local");
          sendResponse({ success: true });
        }
      }
    );
    
    // Return true to indicate async response
    return true;
  }
});
