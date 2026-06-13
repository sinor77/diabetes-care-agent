/**
 * DiabetesControl AI Expert - Frontend Application
 * Features: AI Analysis, Text-to-Speech, Email Reports, Persistent Profile
 */

let sessionId = null;
let isLoading = false;
let ttsEnabled = false;
let lastAnalysisText = "";

// ========== INITIALIZATION ==========

document.addEventListener("DOMContentLoaded", () => {
    initSession();
    loadProfile();
});

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

// ========== PROFILE PERSISTENCE ==========

function saveProfile() {
    const profile = gatherProfile();
    localStorage.setItem("diabetes_profile", JSON.stringify(profile));
    
    // Update profile indicator
    if (profile.name) {
        document.getElementById("profile-status").classList.remove("hidden");
        document.getElementById("profile-status").classList.add("flex");
        document.getElementById("profile-name-display").textContent = profile.name;
    }
    
    showToast("💾", "Profile saved! It will be here when you come back.");
}

function loadProfile() {
    const saved = localStorage.getItem("diabetes_profile");
    if (!saved) return;

    try {
        const profile = JSON.parse(saved);
        
        // Populate all fields
        if (profile.email) document.getElementById("input-email").value = profile.email;
        if (profile.name) document.getElementById("input-name").value = profile.name;
        if (profile.diabetesType) document.getElementById("input-diabetes-type").value = profile.diabetesType;
        if (profile.yearsWithDiabetes) {
            document.getElementById("input-years").value = profile.yearsWithDiabetes;
            document.getElementById("years-value").textContent = profile.yearsWithDiabetes;
        }
        if (profile.age) {
            document.getElementById("input-age").value = profile.age;
            document.getElementById("age-value").textContent = profile.age;
        }
        if (profile.hba1c) document.getElementById("input-hba1c").value = profile.hba1c;
        if (profile.bloodPressure) document.getElementById("input-bp").value = profile.bloodPressure;
        if (profile.height) document.getElementById("input-height").value = profile.height;
        if (profile.weight) document.getElementById("input-weight").value = profile.weight;
        if (profile.medications) document.getElementById("input-medications").value = profile.medications;
        if (profile.goal) document.getElementById("input-goal").value = profile.goal;
        if (profile.goalHba1c) document.getElementById("input-goal-hba1c").value = profile.goalHba1c;
        if (profile.mainChallenge) document.getElementById("input-challenge").value = profile.mainChallenge;

        // Show profile indicator
        if (profile.name) {
            document.getElementById("profile-status").classList.remove("hidden");
            document.getElementById("profile-status").classList.add("flex");
            document.getElementById("profile-name-display").textContent = profile.name;
        }

        showToast("👤", `Welcome back, ${profile.name || "User"}!`);
    } catch (e) {
        console.error("Failed to load profile:", e);
    }
}

// ========== TEXT-TO-SPEECH ==========

function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    const label = document.getElementById("tts-label");
    const btn = document.getElementById("tts-toggle");
    
    if (ttsEnabled) {
        label.textContent = "TTS On";
        btn.classList.remove("bg-gray-100", "text-gray-600");
        btn.classList.add("bg-emerald-100", "text-emerald-700");
        showToast("🔊", "Text-to-Speech enabled. AI responses will be read aloud.");
    } else {
        label.textContent = "TTS Off";
        btn.classList.remove("bg-emerald-100", "text-emerald-700");
        btn.classList.add("bg-gray-100", "text-gray-600");
        speechSynthesis.cancel();
        showToast("🔇", "Text-to-Speech disabled.");
    }
}

function speakSection(elementId) {
    const el = document.getElementById(elementId);
    const text = el.innerText || el.textContent;
    
    if (!text || text.includes("Fill in") || text.includes("analyzing")) return;
    
    speakText(text);
}

function speakText(text) {
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    // Clean text for speech
    const cleanText = text
        .replace(/[📊⚠️📈🤖🔊💪🥗💧🩺✓✗]/g, "")
        .replace(/\*\*/g, "")
        .replace(/#{1,4}\s/g, "")
        .replace(/\n+/g, ". ")
        .trim();

    if (!cleanText) return;

    // Split into chunks (speech synthesis has limits)
    const chunks = cleanText.match(/.{1,200}[.!?]|.{1,200}/g) || [cleanText];
    
    chunks.forEach((chunk, index) => {
        const utterance = new SpeechSynthesisUtterance(chunk);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        // Try to use a natural-sounding voice
        const voices = speechSynthesis.getVoices();
        const preferred = voices.find(v => v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha"));
        if (preferred) utterance.voice = preferred;
        
        speechSynthesis.speak(utterance);
    });
}

// ========== EMAIL REPORT ==========

async function sendEmailReport() {
    const email = document.getElementById("input-email").value.trim();
    if (!email) {
        showToast("⚠️", "Please enter your email address in the profile section.");
        return;
    }

    if (!lastAnalysisText) {
        showToast("⚠️", "Generate an analysis first, then send it as a report.");
        return;
    }

    const emailBtn = document.getElementById("email-btn");
    emailBtn.disabled = true;
    emailBtn.innerHTML = `<div class="spinner-sm"></div> Sending...`;

    try {
        const profile = gatherProfile();
        const response = await fetch(`${CONFIG.API_ENDPOINT}/email-report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                name: profile.name || "User",
                analysis: lastAnalysisText,
                profile: profile,
            }),
        });

        if (response.ok) {
            showToast("📧", `Report sent to ${email}!`);
        } else {
            const err = await response.json().catch(() => ({}));
            showToast("⚠️", err.error || "Failed to send email. Try again later.");
        }
    } catch (error) {
        showToast("⚠️", "Could not connect to email service. Report saved locally.");
        // Fallback: download as text file
        downloadReport();
    } finally {
        emailBtn.disabled = false;
        emailBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg> 📧 Email Progress Report`;
    }
}

function downloadReport() {
    const profile = gatherProfile();
    const content = `DiabetesControl AI Expert - Progress Report\n` +
        `Date: ${new Date().toLocaleDateString()}\n` +
        `Patient: ${profile.name || "N/A"}\n` +
        `========================================\n\n` +
        lastAnalysisText;
    
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `diabetes-report-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("📄", "Report downloaded as text file.");
}

// ========== AI ANALYSIS ==========

function gatherProfile() {
    return {
        email: document.getElementById("input-email").value.trim(),
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

async function runAnalysis() {
    if (isLoading) return;

    const profile = gatherProfile();

    if (!profile.name && !profile.hba1c && !profile.question) {
        showToast("⚠️", "Please fill in at least your name, HbA1c, or ask a question.");
        return;
    }

    // Auto-save profile
    saveProfile();

    isLoading = true;
    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner"></div> Analyzing...`;

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
            lastAnalysisText = data.response;
            parseAndDisplayResults(data.response);
            
            // Enable email button
            document.getElementById("email-btn").disabled = false;

            // Auto-speak if TTS is on
            if (ttsEnabled && data.response) {
                speakText(data.response);
            }
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

// ========== DISPLAY HELPERS ==========

function parseAndDisplayResults(text) {
    if (!text) {
        setError("output-analysis", "No response received.");
        return;
    }

    const sections = { analysis: "", risk: "", improvement: "", chat: "" };

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
        sections.analysis = text;
        sections.risk = "See full analysis above.";
        sections.improvement = "See full analysis above.";
        sections.chat = "See full analysis above.";
    }

    renderOutput("output-analysis", sections.analysis || "No data for this section.");
    renderOutput("output-risk", sections.risk || "Provide HbA1c, age, and blood pressure for risk calculation.");
    renderOutput("output-improvement", sections.improvement || "Provide current and goal HbA1c values.");
    renderOutput("output-chat", sections.chat || "No specific question asked.");
}

function renderOutput(elementId, text) {
    const el = document.getElementById(elementId);
    el.innerHTML = `<div class="prose prose-sm max-w-none">${formatMarkdown(text)}</div>`;
    el.classList.add("message-enter");
}

function setLoading(elementId) {
    document.getElementById(elementId).innerHTML = `
        <div class="flex items-center justify-center py-8 gap-3">
            <div class="spinner"></div>
            <span class="text-sm text-gray-400">AI is analyzing your data...</span>
        </div>`;
}

function setError(elementId, message) {
    document.getElementById(elementId).innerHTML = `
        <div class="bg-red-50 rounded-xl p-4 border border-red-200">
            <p class="text-sm text-red-700">⚠️ ${escapeHtml(message)}</p>
        </div>`;
}

// ========== UTILITIES ==========

function showToast(icon, message) {
    const toast = document.getElementById("toast");
    document.getElementById("toast-icon").textContent = icon;
    document.getElementById("toast-message").textContent = message;
    
    toast.classList.remove("translate-y-20", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");
    
    setTimeout(() => {
        toast.classList.remove("translate-y-0", "opacity-100");
        toast.classList.add("translate-y-20", "opacity-0");
    }, 3000);
}

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
        .replace(/\n\n/g, '</p><p class="mb-2">')
        .replace(/\n/g, "<br>")
        .replace(/^/, '<p class="mb-2">')
        .replace(/$/, '</p>');
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
