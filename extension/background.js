/**
 * Background Service Worker for the extension.
 * Handles background tasks and messaging.
 */

// Log when service worker starts
console.log("[AI Insights] Background service worker started");

// Listen for extension installation/update
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("[AI Insights] Extension installed");
  } else if (details.reason === "update") {
    console.log("[AI Insights] Extension updated");
  }
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("[AI Insights] Message received:", request);
  
  if (request.action === "checkBackend") {
    fetch("http://localhost:8000/health")
      .then(response => {
        sendResponse({ ok: response.ok });
      })
      .catch(error => {
        console.error("[AI Insights] Backend check failed:", error);
        sendResponse({ ok: false });
      });
    
    // Return true to indicate we'll send response asynchronously
    return true;
  }
});
