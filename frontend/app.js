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
 * Initialize a chat session.
 */
async function initSession() {
    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/session`);
        if (response.ok) {
            const data = await response.json();
            sessionId = data.session_id;
        } else {
            sessionId = crypto.randomUUID();
        }
    } catch (error) {
        sessionId = crypto.randomUUID();
    }
}

/**
 * Gather all form inputs into a structured profile object.
 */
function gatherProfile() {
    return {
        name: document.getElementById("input-name").value.trim(),
        diabetesType: document.getElementById("input-diabetes-type").value,
        yearsWithDiabetes: document.getElementById("input-years").value,
        age: document.getElementById("input-age").value,
        hba1c: document.getElementById("input-hba1c").value.trim(),
        bloodPressure: document.getElementById("input-bp").value.trim(),
        height: document.getElementById("input-height").value.trim(),
        weight: document.getElementById("input-weight").value.trim(),
        medications: document.getElementById("input-medications").value.trim(),
        goal: document.getElementById("input-goal").value.trim(),
        goalHba1c: document.getElementById("input-goal-hba1c").value.trim(),
        mainChallenge: document.getElementById("input-challenge").value.trim(),
        question: document.getElementById("input-question").value.trim(),
    };
}

/**
 * Build a comprehensive prompt from the user profile.
 */
function buildPrompt(profile) {
    let prompt = `Patient Profile:\n`;
    if (profile.name) prompt += `- Name: ${profile.name}\n`;
    prompt += `- Diabetes Type: ${profile.diabetesType}\n`;
    prompt += `- Years with Diabetes: ${profile.yearsWithDiabetes}\n`;
    prompt += `- Age: ${profile.age}\n`;
    if (profile.hba1c) prompt += `- Current HbA1c: ${profile.hba1c}%\n`;
    if (profile.bloodPressure) prompt += `- Blood Pressure: ${profile.bloodPressure}\n`;
    if (profile.height) prompt += `- Height: ${profile.height}\n`;
    if (profile.weight) prompt += `- Weight: ${profile.weight}\n`;
    if (profile.medications) prompt += `- Current Medications: ${profile.medications}\n`;
    if (profile.goal) prompt += `- Goal: ${profile.goal}\n`;
    if (profile.goalHba1c) prompt += `- Goal HbA1c: ${profile.goalHba1c}%\n`;
    if (profile.mainChallenge) prompt += `- Main Challenge: ${profile.mainChallenge}\n`;

    prompt += `\nPlease provide a comprehensive analysis with the following sections clearly labeled:\n`;
    prompt += `1. **INSTANT DIABETES ANALYSIS**: A personalized assessment of their current diabetes status, risks, and actionable recommendations based on all provided metrics.\n`;
    prompt += `2. **5-YEAR COMPLICATION RISK**: Based on their HbA1c, years with diabetes, age, and blood pressure, estimate their risk for complications (retinopathy, neuropathy, nephropathy, cardiovascular) over 5 years.\n`;
    prompt += `3. **HBA1C IMPROVEMENT IMPACT**: Explain what reducing their HbA1c from ${profile.hba1c || "current level"}% to ${profile.goalHba1c || "target"}% would mean for their health outcomes, risk reduction percentages, and quality of life.\n`;

    if (profile.question) {
        prompt += `4. **AI COACHING RESPONSE**: Answer this specific question: ${profile.question}\n`;
    } else {
        prompt += `4. **AI COACHING RESPONSE**: Provide 3 personalized daily tips they can start today based on their profile and main challenge.\n`;
    }

    return prompt;
}

/**
 * Run the full AI analysis.
 */
async function runAnalysis() {
    if (isLoading) return;

    const profile = gatherProfile();

    // Validate minimum inputs
    if (!profile.name && !profile.hba1c && !profile.question) {
        alert("Please fill in at least your name, HbA1c, or ask a question.");
        return;
    }

    isLoading = true;
    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner"></div> Analyzing...`;

    // Show loading in all panels
    setLoading("output-analysis");
    setLoading("output-risk");
    setLoading("output-improvement");
    setLoading("output-chat");

    const prompt = buildPrompt(profile);

    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Session-Id": sessionId,
            },
            body: JSON.stringify({
                message: prompt,
                session_id: sessionId,
            }),
        });

        if (response.ok) {
            const data = await response.json();
            parseAndDisplayResults(data.response);
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.error || `Error ${response.status}: ${response.statusText}`;
            setError("output-analysis", errorMsg);
            setError("output-risk", errorMsg);
            setError("output-improvement", errorMsg);
            setError("output-chat", errorMsg);
        }
    } catch (error) {
        const errorMsg = "Unable to connect to the AI service. Please check your connection and try again.";
        setError("output-analysis", errorMsg);
        setError("output-risk", errorMsg);
        setError("output-improvement", errorMsg);
        setError("output-chat", errorMsg);
    } finally {
        isLoading = false;
        btn.disabled = false;
        btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Generate AI Analysis`;
    }
}

/**
 * Parse the AI response and split it into the 4 output panels.
 */
function parseAndDisplayResults(text) {
    if (!text) {
        setError("output-analysis", "No response received from the AI.");
        return;
    }

    // Try to split by section headers
    const sections = {
        analysis: "",
        risk: "",
        improvement: "",
        chat: "",
    };

    // Match sections by numbered headers or keywords
    const analysisMatch = text.match(/(?:1\.\s*\*?\*?INSTANT DIABETES ANALYSIS\*?\*?[:\s]*)([\s\S]*?)(?=2\.\s*\*?\*?5-YEAR|$)/i);
    const riskMatch = text.match(/(?:2\.\s*\*?\*?5-YEAR COMPLICATION RISK\*?\*?[:\s]*)([\s\S]*?)(?=3\.\s*\*?\*?HBA1C|$)/i);
    const improvementMatch = text.match(/(?:3\.\s*\*?\*?HBA1C IMPROVEMENT\*?\*?[:\s]*)([\s\S]*?)(?=4\.\s*\*?\*?AI COACHING|$)/i);
    const chatMatch = text.match(/(?:4\.\s*\*?\*?AI COACHING RESPONSE\*?\*?[:\s]*)([\s\S]*?)$/i);

    if (analysisMatch || riskMatch || improvementMatch || chatMatch) {
        sections.analysis = analysisMatch ? analysisMatch[1].trim() : "";
        sections.risk = riskMatch ? riskMatch[1].trim() : "";
        sections.improvement = improvementMatch ? improvementMatch[1].trim() : "";
        sections.chat = chatMatch ? chatMatch[1].trim() : "";
    } else {
        // Couldn't parse sections — put everything in analysis
        sections.analysis = text;
        sections.risk = "Analysis included above.";
        sections.improvement = "Analysis included above.";
        sections.chat = "Analysis included above.";
    }

    // Render each section
    renderOutput("output-analysis", sections.analysis || "No data available for this section.");
    renderOutput("output-risk", sections.risk || "Insufficient data to calculate risk. Please provide HbA1c, age, and blood pressure.");
    renderOutput("output-improvement", sections.improvement || "Please provide current and goal HbA1c values.");
    renderOutput("output-chat", sections.chat || "No specific question was asked.");
}

/**
 * Render formatted output in a panel.
 */
function renderOutput(elementId, text) {
    const el = document.getElementById(elementId);
    el.innerHTML = `<div class="prose prose-sm max-w-none">${formatMarkdown(text)}</div>`;
    el.classList.add("message-enter");
}

/**
 * Show loading state.
 */
function setLoading(elementId) {
    const el = document.getElementById(elementId);
    el.innerHTML = `
        <div class="flex items-center justify-center py-8 gap-3">
            <div class="spinner"></div>
            <span class="text-sm text-gray-400">AI is analyzing your data...</span>
        </div>
    `;
}

/**
 * Show error state.
 */
function setError(elementId, message) {
    const el = document.getElementById(elementId);
    el.innerHTML = `
        <div class="bg-red-50 rounded-xl p-4 border border-red-200">
            <p class="text-sm text-red-700">⚠️ ${escapeHtml(message)}</p>
        </div>
    `;
}

/**
 * Format markdown text to HTML.
 */
function formatMarkdown(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\*\*\*(.*?)\*\*\*/g, "<strong><em>$1</em></strong>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
        .replace(/^### (.*$)/gm, '<h4 class="font-semibold text-gray-900 mt-3 mb-1">$1</h4>')
        .replace(/^## (.*$)/gm, '<h3 class="font-semibold text-gray-900 text-base mt-4 mb-2">$1</h3>')
        .replace(/^# (.*$)/gm, '<h2 class="font-bold text-gray-900 text-lg mt-4 mb-2">$1</h2>')
        .replace(/^- (.*$)/gm, '<li class="ml-4 list-disc text-gray-700">$1</li>')
        .replace(/^(\d+)\. (.*$)/gm, '<li class="ml-4 list-decimal text-gray-700">$2</li>')
        .replace(/(<li.*<\/li>\n?)+/g, '<ul class="space-y-1 my-2">$&</ul>')
        .replace(/\n\n/g, '</p><p class="mb-2">')
        .replace(/\n/g, "<br>")
        .replace(/^/, '<p class="mb-2">')
        .replace(/$/, '</p>');
}

/**
 * Escape HTML entities.
 */
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
