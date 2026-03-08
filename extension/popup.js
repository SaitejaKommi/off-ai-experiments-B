/**
 * Popup script for the extension.
 * Handles status checking and interactions.
 */

const API_BASE_URL = "http://localhost:8000";

/**
 * Check if the backend API is running.
 */
async function checkBackendStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { timeout: 3000 });
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Check if we're on a product page.
 */
async function isProductPage() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab && /openfoodfacts\.org\/product\//.test(tab.url);
  } catch (error) {
    return false;
  }
}

/**
 * Update status indicators.
 */
async function updateStatus() {
  // Check backend
  const backendOk = await checkBackendStatus();
  const backendIcon = document.getElementById("backendStatus");
  const backendText = document.getElementById("backendStatusText");
  
  if (backendOk) {
    backendIcon.className = "status-icon ok";
    backendText.textContent = "Backend: Connected ✓";
  } else {
    backendIcon.className = "status-icon error";
    backendText.textContent = "Backend: Not Connected ✗";
    
    document.getElementById("errorBox").style.display = "block";
    document.getElementById("errorBox").textContent = 
      "Backend API is not running. Start it with: python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000";
  }
  
  // Check if product page
  const isProduct = await isProductPage();
  const pageStatus = document.getElementById("pageStatus");
  const pageText = document.getElementById("pageStatusText");
  
  if (isProduct) {
    pageStatus.className = "status-icon ok";
    pageText.textContent = "Product Page Detected ✓";
  } else {
    pageStatus.className = "status-icon error";
    pageText.textContent = "Not on product page";
  }
}

/**
 * Refresh insights on current page.
 */
document.getElementById("refreshBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Reload the tab to retrigger the content script
  chrome.tabs.reload(tab.id);
  
  // Close popup after reload
  setTimeout(() => window.close(), 500);
});

/**
 * Open settings (placeholder).
 */
document.getElementById("settingsBtn").addEventListener("click", () => {
  chrome.runtime.openOptionsPage?.() || alert("Settings page not yet available");
});

// Check status when popup opens
updateStatus();

// Recheck status every 3 seconds
setInterval(updateStatus, 3000);
