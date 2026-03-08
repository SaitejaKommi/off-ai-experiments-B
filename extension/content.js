/**
 * Content script that runs on Open Food Facts product pages.
 * Extracts product barcode and fetches AI insights from the backend.
 */

// API configuration
const API_BASE_URL = "http://localhost:8000";
const API_ENDPOINT = `${API_BASE_URL}/product-insights`;

/**
 * Extract barcode from the current product page URL.
 * URL format: /product/{barcode}/product-name
 */
function extractBarcode() {
  const pathname = window.location.pathname;
  const parts = pathname.split("/").filter(Boolean);
  
  // Find the barcode (usually second part after 'product')
  if (parts[0] === "product" && parts[1]) {
    const barcode = parts[1];
    // Verify it's a valid barcode (numeric)
    if (/^\d+$/.test(barcode)) {
      return barcode;
    }
  }
  
  return null;
}

/**
 * Get the page language (EN or FR).
 */
function getPageLanguage() {
  const lang = document.documentElement.lang || "";
  return lang.toLowerCase().startsWith("fr") ? "fr" : "en";
}

/**
 * Create a skeleton loading card.
 */
function createSkeletonCard() {
  const skeleton = document.createElement("div");
  skeleton.className = "ai-insights-card skeleton-loading";
  skeleton.innerHTML = `
    <div class="ai-header">
      <h3>AI Product Insights</h3>
      <div class="skeleton-line" style="width: 60%; height: 16px;"></div>
    </div>
    <div class="skeleton-section">
      <div class="skeleton-line" style="width: 100%; height: 12px;"></div>
      <div class="skeleton-line" style="width: 90%; height: 12px; margin-top: 8px;"></div>
    </div>
    <div class="skeleton-section">
      <div class="skeleton-line" style="width: 100%; height: 12px;"></div>
      <div class="skeleton-line" style="width: 80%; height: 12px; margin-top: 8px;"></div>
    </div>
  `;
  return skeleton;
}

/**
 * Create an error card.
 */
function createErrorCard(message) {
  const errorCard = document.createElement("div");
  errorCard.className = "ai-insights-card error-card";
  errorCard.innerHTML = `
    <div class="ai-header">
      <h3>AI Product Insights</h3>
    </div>
    <div class="ai-error">
      <p>⚠️ ${message}</p>
      <p style="font-size: 12px; color: #666; margin-top: 8px;">
        Make sure the backend API is running on http://localhost:8000
      </p>
    </div>
  `;
  return errorCard;
}

/**
 * Create the insights panel from API response.
 */
function createInsightsPanel(data) {
  const panel = document.createElement("div");
  panel.className = "ai-insights-card";
  
  const product = data.product;
  const scoreExplanation = data.score_explanation || {};
  
  // Create risk/positive indicators HTML
  const riskHTML = data.risk_indicators
    .map(indicator => `<div class="indicator risk">⚠️ ${indicator}</div>`)
    .join("");
  
  const positiveHTML = data.positive_indicators
    .map(indicator => `<div class="indicator positive">✓ ${indicator}</div>`)
    .join("");
  
  // Create similar products HTML
  let productsHTML = '';
  
  if (data.similar_products && data.similar_products.length > 0) {
    productsHTML = data.similar_products
      .slice(0, 5)
      .map(prod => {
        const name = prod.name || prod.product_name || 'Unknown product';
        const grade = (prod.nutriscore_grade || prod.grade || 'N/A').toLowerCase();
        const reason = prod.reason || 'Better nutritional profile';
        const url = prod.url || '#';
        
        return `<div class="similar-product">
          <div style="flex: 1;">
            <div style="margin-bottom: 4px;">
              <span style="color: #ff9900; font-weight: 600;">•</span>
              <a href="${url}" target="_blank" class="product-link">
                ${name}
              </a>
            </div>
            <div style="font-size: 12px; color: #7f8c8d;">${reason}</div>
          </div>
          <span class="nutriscore-badge grade-${grade}">${grade.toUpperCase()}</span>
        </div>`;
      })
      .join("");
  } else {
    productsHTML = `
      <div style="padding: 16px; text-align: center; color: #7f8c8d; background: #f8f9fa; border-radius: 6px; border: 1px dashed #dee2e6;">
        <div style="font-size: 16px; margin-bottom: 8px;">🔍</div>
        <div style="font-size: 13px; font-weight: 500; margin-bottom: 6px;">No alternatives found</div>
        <div style="font-size: 12px;">We couldn't find similar products with better nutritional scores in the same category.</div>
      </div>
    `;
  }
  
  // Create pairings HTML
  const pairingsHTML = data.pairings
    .slice(0, 6)
    .map(pairing => `<span class="pairing">${pairing}</span>`)
    .join("");
  
  panel.innerHTML = `
    <div class="ai-header">
      <h3>🤖 AI Product Insights</h3>
    </div>
    
    <div class="ai-section">
      <h4>📝 Summary</h4>
      <p>${data.summary}</p>
    </div>
    
    <div class="ai-section">
      <h4>🏥 Health Indicators</h4>
      <div class="indicators-container">
        ${riskHTML}
        ${positiveHTML}
      </div>
    </div>
    
    <div class="ai-section">
      <h4>🛒 Product Discovery</h4>
      <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 12px;">
        Similar products with better nutritional scores
      </div>
      ${productsHTML}
    </div>
    
    ${data.pairings.length > 0 ? `
    <div class="ai-section">
      <h4>🍽️ Food Pairings</h4>
      <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 12px;">
        Complementary foods that go well with this product
      </div>
      <div class="pairings-container">
        ${pairingsHTML}
      </div>
    </div>
    ` : ""}
    
    ${scoreExplanation.nutriscore ? `
    <div class="ai-section collapsible collapsed">
      <h4 class="collapsible-header">
        <span class="toggle-arrow">▶</span>
        📊 Score Explanation
      </h4>
      <div class="collapsible-content" style="display: none;">
        <p style="font-size: 13px; line-height: 1.7;">${scoreExplanation.nutriscore}</p>
      </div>
    </div>
    ` : ""}
  `;
  
  // Add event listeners for collapsible sections
  panel.querySelectorAll(".collapsible-header").forEach(header => {
    header.addEventListener("click", function() {
      const section = this.closest(".collapsible");
      const content = this.nextElementSibling;
      const isCollapsed = section.classList.contains("collapsed");
      
      if (isCollapsed) {
        section.classList.remove("collapsed");
        content.style.display = "block";
      } else {
        section.classList.add("collapsed");
        content.style.display = "none";
      }
    });
  });
  
  return panel;
}

/**
 * Find the best place to inject the insights panel.
 * Looks for common product information containers.
 */
function findInsertionPoint() {
  // Try to find the main product container
  const selectors = [
    "[data-testid='product-page-content']",
    ".product",
    ".product-info",
    ".col-md-8",
    ".main-content",
    "main",
    "#main"
  ];
  
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) return element;
  }
  
  // Fallback: insert after h1 title
  const h1 = document.querySelector("h1");
  if (h1 && h1.parentElement) return h1.parentElement;
  
  // Ultimate fallback: insert at body start
  return document.body;
}

/**
 * Fetch insights from the backend API.
 */
async function fetchInsights(barcode) {
  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ barcode }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch insights:", error);
    throw error;
  }
}

/**
 * Main function: Extract barcode, fetch insights, and inject panel.
 */
async function injectAIInsights() {
  try {
    console.log("[AI Insights] Starting injection...");
    
    const barcode = extractBarcode();
    if (!barcode) {
      console.warn("[AI Insights] Could not extract barcode from URL");
      return;
    }
    
    console.log(`[AI Insights] Found barcode: ${barcode}`);
    
    // Find insertion point
    const insertionPoint = findInsertionPoint();
    
    // Create and insert skeleton
    const skeleton = createSkeletonCard();
    insertionPoint.insertBefore(skeleton, insertionPoint.firstChild);
    
    // Fetch insights
    console.log("[AI Insights] Fetching from API...");
    const insights = await fetchInsights(barcode);
    
    // Replace skeleton with actual insights
    const insightsPanel = createInsightsPanel(insights);
    skeleton.replaceWith(insightsPanel);
    
    console.log("[AI Insights] Successfully injected insights panel");
  } catch (error) {
    console.error("[AI Insights] Error:", error);
    
    const insertionPoint = findInsertionPoint();
    const errorCard = createErrorCard(
      error.message || "Failed to load AI insights. Please try again."
    );
    insertionPoint.insertBefore(errorCard, insertionPoint.firstChild);
  }
}

// Run when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", injectAIInsights);
} else {
  injectAIInsights();
}
