/**
 * DiabetesControl AI Expert - Frontend Application
 */

let sessionId = null;
let isLoading = false;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    initSession();
});

/**
 * Initialize or restore a chat session.
 */
async function initSession() {
    // Try to restore from localStorage
    sessionId = localStorage.getItem("diabetes_session_id");
    if (!sessionId) {
        await startNewSession();
    }
}

/**
 * Start a fresh session.
 */
async function startNewSession() {
    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/session`);
        if (response.ok) {
            const data = await response.json();
            sessionId = data.session_id;
        } else {
            // Fallback: generate locally
            sessionId = crypto.randomUUID();
        }
    } catch (error) {
        // Offline or API not configured — generate locally
        sessionId = crypto.randomUUID();
    }
    localStorage.setItem("diabetes_session_id", sessionId);

    // Clear chat (keep welcome message)
    const chatMessages = document.getElementById("chat-messages");
    const welcomeMessage = chatMessages.firstElementChild;
    chatMessages.innerHTML = "";
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }

    // Reset dashboard
    resetDashboard();
}

/**
 * Handle keyboard shortcuts in the input.
 */
function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Pre-fill input with a quick prompt.
 */
function quickPrompt(text) {
    const input = document.getElementById("message-input");
    input.value = text;
    input.focus();
}

/**
 * Send a message to the API.
 */
async function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();

    if (!message || isLoading) return;

    // Add user message to chat
    appendMessage("user", message);
    input.value = "";
    input.style.height = "auto";

    // Show typing indicator
    const typingId = showTypingIndicator();
    isLoading = true;
    updateSendButton(true);

    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Session-Id": sessionId,
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
            }),
        });

        removeTypingIndicator(typingId);

        if (response.ok) {
            const data = await response.json();
            appendMessage("assistant", data.response);

            // Update dashboard with tool outputs
            if (data.tool_outputs && data.tool_outputs.length > 0) {
                updateDashboard(data.tool_outputs);
            }
        } else {
            const errorData = await response.json().catch(() => ({}));
            appendMessage("error", errorData.error || `Error: ${response.status} ${response.statusText}`);
        }
    } catch (error) {
        removeTypingIndicator(typingId);

        if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
            appendMessage("error",
                "Unable to connect to the API. Please check that:\n" +
                "1. The API endpoint is configured in config.js\n" +
                "2. The SAM stack is deployed\n" +
                "3. CORS is enabled on the API Gateway"
            );
        } else {
            appendMessage("error", `Connection error: ${error.message}`);
        }
    } finally {
        isLoading = false;
        updateSendButton(false);
    }
}

/**
 * Append a message to the chat.
 */
function appendMessage(role, content) {
    const chatMessages = document.getElementById("chat-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = "flex gap-3 message-enter";

    if (role === "user") {
        messageDiv.innerHTML = `
            <div class="ml-auto max-w-[80%]">
                <div class="bg-primary-600 text-white rounded-2xl rounded-tr-md px-4 py-3">
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(content)}</p>
                </div>
            </div>
        `;
    } else if (role === "assistant") {
        messageDiv.innerHTML = `
            <div class="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                <span class="text-sm">🩺</span>
            </div>
            <div class="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100 max-w-[80%]">
                <div class="text-gray-800 text-sm leading-relaxed prose prose-sm">${formatMarkdown(content)}</div>
            </div>
        `;
    } else if (role === "error") {
        messageDiv.innerHTML = `
            <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                <span class="text-sm">⚠️</span>
            </div>
            <div class="bg-red-50 rounded-2xl rounded-tl-md px-4 py-3 border border-red-200 max-w-[80%]">
                <p class="text-red-800 text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(content)}</p>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show typing indicator.
 */
function showTypingIndicator() {
    const chatMessages = document.getElementById("chat-messages");
    const id = "typing-" + Date.now();
    const div = document.createElement("div");
    div.id = id;
    div.className = "flex gap-3 message-enter";
    div.innerHTML = `
        <div class="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
            <span class="text-sm">🩺</span>
        </div>
        <div class="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100">
            <div class="flex gap-1.5 items-center py-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

/**
 * Remove typing indicator.
 */
function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Update send button state.
 */
function updateSendButton(loading) {
    const btn = document.getElementById("send-button");
    btn.disabled = loading;
    if (loading) {
        btn.innerHTML = '<div class="spinner"></div>';
    } else {
        btn.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
        `;
    }
}

/**
 * Update dashboard with tool outputs.
 */
function updateDashboard(toolOutputs) {
    const container = document.getElementById("dashboard-cards");
    // Show dashboard on mobile via a class toggle if needed
    document.getElementById("dashboard-panel").classList.remove("hidden");
    document.getElementById("dashboard-panel").classList.add("lg:block");

    // Clear placeholder
    if (container.querySelector(".text-center")) {
        container.innerHTML = "";
    }

    for (const tool of toolOutputs) {
        let parsedOutput;
        try {
            parsedOutput = JSON.parse(tool.output);
        } catch {
            parsedOutput = { raw: tool.output };
        }

        const card = document.createElement("div");
        card.className = "dashboard-card bg-gray-50 rounded-xl p-4 border border-gray-100";

        const toolName = tool.tool || "Tool";
        const icon = getToolIcon(toolName);

        let cardContent = `
            <div class="flex items-center gap-2 mb-2">
                <span>${icon}</span>
                <span class="text-xs font-medium text-gray-700">${formatToolName(toolName)}</span>
                <span class="text-xs text-gray-400 ml-auto">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
        `;

        // Render based on tool type
        if (parsedOutput.meal_summary) {
            cardContent += renderMealCard(parsedOutput);
        } else if (parsedOutput.summary && parsedOutput.interpretations) {
            cardContent += renderLabCard(parsedOutput);
        } else if (parsedOutput.overall_risk) {
            cardContent += renderRiskCard(parsedOutput);
        } else if (parsedOutput.nutrition_plan) {
            cardContent += renderPlanCard(parsedOutput);
        } else {
            cardContent += `<p class="text-xs text-gray-600">${JSON.stringify(parsedOutput).substring(0, 200)}...</p>`;
        }

        card.innerHTML = cardContent;
        container.insertBefore(card, container.firstChild);
    }
}

function renderMealCard(data) {
    const summary = data.meal_summary;
    const impactColor = summary.overall_impact === "low" ? "risk-low" : summary.overall_impact === "moderate" ? "risk-moderate" : "risk-high";
    return `
        <div class="space-y-2">
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-600">Glycemic Load</span>
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${impactColor}">${summary.total_glycemic_load} (${summary.overall_impact})</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-xs text-gray-600">Total Carbs</span>
                <span class="text-xs font-medium text-gray-800">${summary.total_carbohydrates_grams}g</span>
            </div>
        </div>
    `;
}

function renderLabCard(data) {
    const s = data.summary;
    return `
        <div class="space-y-1.5">
            <div class="flex justify-between text-xs">
                <span class="text-gray-600">Metrics analyzed</span>
                <span class="font-medium">${s.total_metrics_analyzed}</span>
            </div>
            ${s.urgent_flags > 0 ? `<div class="flex justify-between text-xs"><span class="text-red-600">⚠️ Urgent flags</span><span class="font-medium text-red-700">${s.urgent_flags}</span></div>` : ''}
            ${s.concerning_results > 0 ? `<div class="flex justify-between text-xs"><span class="text-amber-600">⚡ Concerning</span><span class="font-medium text-amber-700">${s.concerning_results}</span></div>` : ''}
            <div class="flex justify-between text-xs">
                <span class="text-green-600">✓ Normal</span>
                <span class="font-medium text-green-700">${s.within_normal}</span>
            </div>
        </div>
    `;
}

function renderRiskCard(data) {
    const risk = data.overall_risk;
    const color = risk.level === "low" ? "risk-low" : risk.level === "moderate" ? "risk-moderate" : "risk-high";
    return `
        <div class="space-y-2">
            <div class="flex items-center gap-2">
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${color}">${risk.level.toUpperCase()} RISK</span>
            </div>
            <p class="text-xs text-gray-600 leading-relaxed">${risk.message.substring(0, 120)}${risk.message.length > 120 ? '...' : ''}</p>
        </div>
    `;
}

function renderPlanCard(data) {
    const actions = data.priority_actions || [];
    return `
        <div class="space-y-1.5">
            <p class="text-xs font-medium text-gray-700">Priority Actions:</p>
            ${actions.length > 0 ? actions.slice(0, 3).map(a => `<p class="text-xs text-gray-600">• ${a}</p>`).join('') : '<p class="text-xs text-gray-500">No urgent actions. Keep up the good work!</p>'}
        </div>
    `;
}

function resetDashboard() {
    const container = document.getElementById("dashboard-cards");
    container.innerHTML = `
        <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <p class="text-xs text-gray-500 text-center py-6">
                Insights will appear here as you interact with the assistant.
            </p>
        </div>
    `;
}

function getToolIcon(name) {
    const lower = name.toLowerCase();
    if (lower.includes("meal")) return "🥗";
    if (lower.includes("lab")) return "🧪";
    if (lower.includes("risk")) return "⚡";
    if (lower.includes("plan")) return "📋";
    return "🔧";
}

function formatToolName(name) {
    return name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Basic markdown formatting.
 */
function formatMarkdown(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs">$1</code>')
        .replace(/\n- /g, "\n• ")
        .replace(/\n\d+\. /g, (match) => "\n" + match.trim() + " ")
        .replace(/\n/g, "<br>");
}

/**
 * Escape HTML entities.
 */
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
