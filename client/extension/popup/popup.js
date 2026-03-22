/**
 * Popup script
 * 
 * Responsibility:
 * 1. Retrieve barcode from chrome.storage.local
 * 2. If barcode exists, call backend API
 * 3. Display insights or appropriate state (empty/loading/error)
 */

const API_BASE_URL = "http://localhost:8000";
const API_ENDPOINT = `${API_BASE_URL}/product-insights`;

// DOM Elements
const emptyState = document.getElementById("emptyState");
const loadingState = document.getElementById("loadingState");
const errorState = document.getElementById("errorState");
const errorMessage = document.getElementById("errorMessage");
const insightsContainer = document.getElementById("insightsContainer");

// UI State Functions
function showEmptyState() {
    emptyState.style.display = "block";
    loadingState.style.display = "none";
    errorState.style.display = "none";
    insightsContainer.style.display = "none";
}

function showLoadingState() {
    emptyState.style.display = "none";
    loadingState.style.display = "block";
    errorState.style.display = "none";
    insightsContainer.style.display = "none";
}

function showErrorState(message) {
    errorMessage.textContent = message;
    emptyState.style.display = "none";
    loadingState.style.display = "none";
    errorState.style.display = "block";
    insightsContainer.style.display = "none";
}

function showInsights() {
    emptyState.style.display = "none";
    loadingState.style.display = "none";
    errorState.style.display = "none";
    insightsContainer.style.display = "block";
}

function extractBarcodeFromUrl(url) {
    if (!url) {
        return null;
    }

    const match = url.match(/openfoodfacts\.org\/product\/(\d+)/i);
    return match ? match[1] : null;
}

async function getActiveTabBarcode() {
    return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const activeTab = tabs && tabs[0] ? tabs[0] : null;
            const barcode = extractBarcodeFromUrl(activeTab ? activeTab.url : "");
            resolve(barcode);
        });
    });
}

/**
 * Fetch insights from backend API
 */
async function fetchInsights(barcode) {
    try {
        console.log("[AI Insights] Fetching insights for barcode:", barcode);
        const response = await fetch(API_ENDPOINT, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                barcode: barcode
            })
        });

        console.log("[AI Insights] API Response status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("[AI Insights] API error response:", errorText);
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log("[AI Insights] API Response data:", data);
        return data;
    } catch (error) {
        console.error("[AI Insights] Fetch error:", error);
        throw error;
    }
}

/**
 * Render insights in the popup
 */
function renderInsights(data) {
    // Product Name - handle both nested and flat structure
    const productName = (data.product ? data.product.name : data.product_name) || "Product";
    document.getElementById("productName").textContent = productName;

    // Summary
    document.getElementById("summary").textContent = 
        data.summary || "No summary available";

    // Health Indicators
    const positivesList = document.getElementById("positivesList");
    const risksList = document.getElementById("risksList");
    
    positivesList.innerHTML = "";
    risksList.innerHTML = "";

    // Get indicators - handle both field names
    const positives = data.positive_indicators || data.positives || [];
    const risks = data.risk_indicators || data.risks || [];

    if (positives.length > 0) {
        document.getElementById("positivesContainer").style.display = "block";
        positives.forEach(positive => {
            const li = document.createElement("li");
            li.textContent = positive;
            positivesList.appendChild(li);
        });
    } else {
        document.getElementById("positivesContainer").style.display = "none";
    }

    if (risks.length > 0) {
        document.getElementById("risksContainer").style.display = "block";
        risks.forEach(risk => {
            const li = document.createElement("li");
            li.textContent = risk;
            risksList.appendChild(li);
        });
    } else {
        document.getElementById("risksContainer").style.display = "none";
    }

    // Score Explanation - handle dict response
    const scoreSection = document.getElementById("scoreSection");
    let scoreText = "";
    if (data.score_explanation) {
        if (typeof data.score_explanation === "string") {
            scoreText = data.score_explanation;
        } else if (typeof data.score_explanation === "object") {
            // Extract nutriscore explanation from object
            scoreText = data.score_explanation.nutriscore || 
                       Object.values(data.score_explanation).find(v => v) || 
                       "Score explanation not available";
        }
    }
    
    if (scoreText) {
        scoreSection.style.display = "block";
        document.getElementById("scoreExplanation").textContent = scoreText;
    } else {
        scoreSection.style.display = "none";
    }

    // Alternatives - handle both field names
    const alternativesSection = document.getElementById("alternativesSection");
    const alternativesList = document.getElementById("alternativesList");
    
    alternativesList.innerHTML = "";
    
    const alternatives = data.similar_products || data.alternatives || [];
    if (alternatives.length > 0) {
        alternativesSection.style.display = "block";
        alternatives.forEach(alt => {
            const li = document.createElement("li");
            // Handle both string and object formats
            if (typeof alt === "string") {
                li.textContent = alt;
            } else if (alt.name || alt.product_name) {
                const label = alt.name || alt.product_name;
                if (alt.url) {
                    const link = document.createElement("a");
                    link.href = alt.url;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.textContent = label;
                    li.appendChild(link);
                } else {
                    li.textContent = label;
                }

                if (alt.reason) {
                    const reason = document.createElement("div");
                    reason.style.fontSize = "11px";
                    reason.style.color = "#6b7280";
                    reason.style.marginTop = "4px";
                    reason.textContent = alt.reason;
                    li.appendChild(reason);
                }
            }
            alternativesList.appendChild(li);
        });
    } else {
        alternativesSection.style.display = "block";
        const li = document.createElement("li");
        li.textContent = "No stronger alternatives found for this category yet.";
        alternativesList.appendChild(li);
    }

    // Pairings
    const pairingsSection = document.getElementById("pairingsSection");
    const pairingsList = document.getElementById("pairingsList");
    
    pairingsList.innerHTML = "";
    
    const pairings = data.pairings || [];
    if (pairings.length > 0) {
        pairingsSection.style.display = "block";
        pairings.forEach(pairing => {
            const li = document.createElement("li");
            li.textContent = `• ${pairing}`;
            pairingsList.appendChild(li);
        });
    } else {
        pairingsSection.style.display = "none";
    }

    showInsights();
}

/**
 * Main initialization
 */
async function initializePopup() {
    console.log("[AI Insights] Popup opened - initializing...");
    try {
        // Only work on actual OFF product pages.
        const barcode = await getActiveTabBarcode();

        if (!barcode) {
            console.log("[AI Insights] Active tab is not an OFF product page");
            showEmptyState();
            return;
        }

        // Keep latest barcode for convenience/history, but do not use stale storage as source.
        await new Promise((resolve) => {
            chrome.storage.local.set({ latest_barcode: barcode }, resolve);
        });

        console.log("[AI Insights] Active page barcode:", barcode);

        // Show loading state
        showLoadingState();

        // Fetch insights
        const insights = await fetchInsights(barcode);
        console.log("[AI Insights] Insights received successfully");

        // Render insights
        renderInsights(insights);

    } catch (error) {
        console.error("[AI Insights] Initialization error:", error);
        const errorMsg = error instanceof Error 
            ? error.message 
            : "Unable to fetch product insights. Make sure the backend API is running on http://localhost:8000";
        showErrorState(errorMsg);
    }
}

// Initialize when popup is opened
console.log("[AI Insights] Loading popup.js");
initializePopup();
