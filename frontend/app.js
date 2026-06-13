/**
 * DiabetesControl AI Expert - Frontend
 * Each tool produces its own dedicated output via separate AI calls.
 */

let sessionId = null;
let isLoading = false;
let ttsEnabled = false;
let uploadedFileText = "";
let allResults = {};

document.addEventListener("DOMContentLoaded", () => {
    initSession();
    loadProfile();
});

async function initSession() {
    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/session`);
        if (res.ok) { sessionId = (await res.json()).session_id; }
        else { sessionId = crypto.randomUUID(); }
    } catch { sessionId = crypto.randomUUID(); }
}

// ========== PROFILE ==========

function gatherProfile() {
    return {
        email: val("input-email"),
        name: val("input-name"),
        diabetesType: val("input-diabetes-type"),
        age: val("input-age"),
        hba1c: val("input-hba1c"),
        goalHba1c: val("input-goal-hba1c"),
        weight: val("input-weight"),
        height: val("input-height"),
        bloodPressure: val("input-bp"),
        medications: val("input-medications"),
        challenge: val("input-challenge"),
        meals: val("input-meals"),
        labs: val("input-labs"),
        activity: val("input-activity"),
        uploadedLabs: uploadedFileText,
    };
}

function saveProfile() {
    const p = gatherProfile();
    localStorage.setItem("dc_profile", JSON.stringify(p));
    if (p.name) {
        document.getElementById("profile-status").classList.remove("hidden");
        document.getElementById("profile-status").classList.add("flex");
        document.getElementById("profile-name-display").textContent = p.name;
    }
    showToast("💾", "Profile saved!");
}

function loadProfile() {
    const saved = localStorage.getItem("dc_profile");
    if (!saved) return;
    try {
        const p = JSON.parse(saved);
        setVal("input-email", p.email);
        setVal("input-name", p.name);
        setVal("input-diabetes-type", p.diabetesType);
        setVal("input-age", p.age);
        setVal("input-hba1c", p.hba1c);
        setVal("input-goal-hba1c", p.goalHba1c);
        setVal("input-weight", p.weight);
        setVal("input-height", p.height);
        setVal("input-bp", p.bloodPressure);
        setVal("input-medications", p.medications);
        setVal("input-challenge", p.challenge);
        setVal("input-meals", p.meals);
        setVal("input-labs", p.labs);
        setVal("input-activity", p.activity);
        if (p.name) {
            document.getElementById("profile-status").classList.remove("hidden");
            document.getElementById("profile-status").classList.add("flex");
            document.getElementById("profile-name-display").textContent = p.name;
        }
        showToast("👤", `Welcome back, ${p.name || "User"}!`);
    } catch(e) { console.error(e); }
}

// ========== FILE UPLOAD ==========

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const area = document.getElementById("upload-area");
    area.innerHTML = `<p class="text-xs text-emerald-600 font-medium">📎 ${file.name}</p><p class="text-xs text-gray-400">${(file.size/1024).toFixed(1)} KB</p>`;

    // Read text files directly
    if (file.type.startsWith("text/") || file.name.endsWith(".csv") || file.name.endsWith(".txt")) {
        const reader = new FileReader();
        reader.onload = (e) => { uploadedFileText = e.target.result; };
        reader.readAsText(file);
    } else if (file.type.startsWith("image/")) {
        // For images, we'll pass a note to the AI that an image was uploaded
        uploadedFileText = `[User uploaded a lab result image: ${file.name}. Please analyze based on the typed values below or ask the user to type key values from the image.]`;
    } else {
        uploadedFileText = `[User uploaded file: ${file.name}. Type: ${file.type}]`;
    }
}

// ========== TTS ==========

function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    const btn = document.getElementById("tts-toggle");
    const label = document.getElementById("tts-label");
    if (ttsEnabled) {
        label.textContent = "TTS On";
        btn.classList.add("bg-emerald-100", "text-emerald-700");
        btn.classList.remove("bg-gray-100", "text-gray-600");
    } else {
        label.textContent = "TTS Off";
        btn.classList.remove("bg-emerald-100", "text-emerald-700");
        btn.classList.add("bg-gray-100", "text-gray-600");
        speechSynthesis.cancel();
    }
}

function speakSection(id) {
    const text = document.getElementById(id).innerText;
    if (!text || text.includes("Fill") || text.includes("Log your") || text.includes("analyzing")) return;
    speechSynthesis.cancel();
    const chunks = text.match(/.{1,250}[.!?\n]|.{1,250}/g) || [text];
    chunks.forEach(chunk => {
        const u = new SpeechSynthesisUtterance(chunk.replace(/[📊⚠️📈🤖🔊💪🥗💧🩺✓✗⚡📋🧪]/g, ""));
        u.rate = 0.95; u.pitch = 1;
        speechSynthesis.speak(u);
    });
}

// ========== RUN ALL ANALYSES ==========

async function runAllAnalyses() {
    if (isLoading) return;
    const p = gatherProfile();
    if (!p.name && !p.hba1c && !p.meals) {
        showToast("⚠️", "Please fill in at least your name, HbA1c, or log a meal.");
        return;
    }
    saveProfile();
    isLoading = true;
    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner"></div> Running 5 AI Analyses...`;

    // Set all panels to loading
    ["output-meal","output-lab","output-risk","output-plan","output-coach"].forEach(setLoading);

    // Run all analyses in parallel
    const [mealRes, labRes, riskRes, planRes, coachRes] = await Promise.allSettled([
        callAgent(buildMealPrompt(p)),
        callAgent(buildLabPrompt(p)),
        callAgent(buildRiskPrompt(p)),
        callAgent(buildPlanPrompt(p)),
        callAgent(buildCoachPrompt(p)),
    ]);

    // Display results
    allResults.meal = displayResult("output-meal", mealRes);
    allResults.lab = displayResult("output-lab", labRes);
    allResults.risk = displayResult("output-risk", riskRes);
    allResults.plan = displayResult("output-plan", planRes);
    allResults.coach = displayResult("output-coach", coachRes);

    // Enable email button
    document.getElementById("email-btn").disabled = false;

    // TTS on first result
    if (ttsEnabled && allResults.coach) speakSection("output-coach");

    isLoading = false;
    btn.disabled = false;
    btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Generate All AI Analyses`;
}

// ========== PROMPTS FOR EACH TOOL ==========

function buildMealPrompt(p) {
    if (!p.meals) return null;
    return `You are a diabetes meal analyzer. Analyze the following meal for a ${p.diabetesType} patient (HbA1c: ${p.hba1c || "unknown"}%).

MEALS EATEN:
${p.meals}

Provide:
1. Estimated total carbohydrates (grams)
2. Glycemic Index classification for each food (Low/Medium/High)
3. Estimated Glycemic Load of the full meal
4. Overall impact on blood sugar (Low/Moderate/High)
5. 3 healthier alternative swaps
6. One practical tip to reduce the glucose spike from this meal

Format with clear headers and bullet points.`;
}

function buildLabPrompt(p) {
    const labData = p.uploadedLabs || p.labs;
    if (!labData && !p.hba1c) return null;
    return `You are a clinical lab interpreter for diabetes patients. Analyze these lab results for a ${p.age || "adult"} year old with ${p.diabetesType} diabetes.

LAB RESULTS:
${labData || `HbA1c: ${p.hba1c}%`}
${p.bloodPressure ? `Blood Pressure: ${p.bloodPressure}` : ""}

For EACH metric provided:
1. State the value and its unit
2. Compare against ADA (American Diabetes Association) reference ranges
3. Flag if NORMAL, BORDERLINE, or OUT OF RANGE
4. Explain what it means in simple language

Then provide:
- Overall assessment
- Top 3 recommendations based on concerning values
- When to retest

Use clear formatting with ✓ for normal and ⚠️ for concerning values.`;
}

function buildRiskPrompt(p) {
    if (!p.meals && !p.activity && !p.hba1c) return null;
    return `You are a diabetes risk predictor. Assess near-term risks for this patient:

PROFILE: ${p.diabetesType}, ${p.age || "?"} years old, HbA1c ${p.hba1c || "?"}%, Medications: ${p.medications || "unknown"}

RECENT MEALS: ${p.meals || "No meal data"}
ACTIVITY/GLUCOSE: ${p.activity || "No activity data"}
CHALLENGE: ${p.challenge || "Not specified"}

Analyze and provide:
1. **Hypoglycemia Risk** (Low/Moderate/High) - based on meal gaps, exercise timing, medications
2. **Hyperglycemia Risk** (Low/Moderate/High) - based on food choices, carb load
3. **Glucose Variability Risk** - based on patterns described
4. **Immediate Actions** - 2-3 specific things to do RIGHT NOW
5. **When to Seek Help** - red flags to watch for

Be specific and actionable. Use risk level badges.`;
}

function buildPlanPrompt(p) {
    if (!p.name && !p.hba1c) return null;
    return `You are a diabetes care plan generator. Create a personalized daily plan for:

PATIENT: ${p.name || "Patient"}, ${p.age || "adult"} years old, ${p.weight || "?"}kg, ${p.height || "?"}cm
DIABETES: ${p.diabetesType}, ${p.hba1c || "?"}% HbA1c, Goal: ${p.goalHba1c || "?"}%
MEDICATIONS: ${p.medications || "unknown"}
CHALLENGE: ${p.challenge || "general management"}

Create a STRUCTURED DAILY PLAN with:

**🍽️ NUTRITION PLAN** (6 time slots: wake, breakfast, morning snack, lunch, afternoon snack, dinner)
- Specific food suggestions for each
- Carb targets per meal
- Key tips

**💧 HYDRATION SCHEDULE**
- Daily target (based on weight)
- Timing recommendations

**🏃 ACTIVITY PLAN**
- Morning, midday, evening recommendations
- Type, duration, and glucose precautions

**📊 MONITORING CHECKLIST**
- When to check glucose
- What to log

Keep it practical and achievable. Use emojis for visual clarity.`;
}

function buildCoachPrompt(p) {
    return `You are an empathetic diabetes coach. Give a brief overall assessment for:

PATIENT: ${p.name || "this patient"}, ${p.diabetesType}, Age ${p.age || "?"}, HbA1c ${p.hba1c || "?"}% (goal: ${p.goalHba1c || "?"}%)
WEIGHT: ${p.weight || "?"}kg, BP: ${p.bloodPressure || "?"}
MEDICATIONS: ${p.medications || "unknown"}
CHALLENGE: ${p.challenge || "not specified"}
MEALS TODAY: ${p.meals || "not logged"}
ACTIVITY: ${p.activity || "not logged"}

Provide:
1. **Overall Status** - How are they doing? (1-2 sentences, warm and encouraging)
2. **Top 3 Priorities** - Most important things to focus on this week
3. **Quick Win** - One small thing they can do TODAY that makes a difference
4. **Motivation** - An encouraging note personalized to their situation

Be warm, empathetic, evidence-based. Keep it concise.`;
}

// ========== API CALL ==========

async function callAgent(prompt) {
    if (!prompt) return { skipped: true };
    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Session-Id": sessionId },
            body: JSON.stringify({ message: prompt, session_id: sessionId }),
        });
        if (res.ok) {
            const data = await res.json();
            return { success: true, text: data.response };
        } else {
            const err = await res.json().catch(() => ({}));
            return { error: err.error || `Error ${res.status}` };
        }
    } catch (e) {
        return { error: "Connection failed: " + e.message };
    }
}

function displayResult(elementId, promiseResult) {
    const el = document.getElementById(elementId);
    if (promiseResult.status === "rejected") {
        el.innerHTML = errorHtml("Analysis failed. Try again.");
        return null;
    }
    const result = promiseResult.value;
    if (result.skipped) {
        el.innerHTML = `<div class="bg-yellow-50 rounded-xl p-4 border border-yellow-200"><p class="text-sm text-yellow-700">ℹ️ Not enough input data for this analysis. Fill in the relevant fields.</p></div>`;
        return null;
    }
    if (result.error) {
        el.innerHTML = errorHtml(result.error);
        return null;
    }
    el.innerHTML = `<div class="prose prose-sm max-w-none message-enter">${formatMd(result.text)}</div>`;
    return result.text;
}

// ========== EMAIL REPORT ==========

async function sendEmailReport() {
    const email = val("input-email");
    if (!email) { showToast("⚠️", "Enter your email in the profile section first."); return; }

    const btn = document.getElementById("email-btn");
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner-sm"></div> Sending to ${email}...`;

    const profile = gatherProfile();
    const fullReport = Object.entries(allResults)
        .filter(([k, v]) => v)
        .map(([k, v]) => `=== ${k.toUpperCase()} ===\n${v}`)
        .join("\n\n");

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/email-report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, name: profile.name || "User", analysis: fullReport, profile }),
        });
        if (res.ok) {
            showToast("📧", `Report sent to ${email}!`);
        } else {
            // Fallback: download
            downloadReport(email, profile, fullReport);
        }
    } catch {
        downloadReport(email, profile, fullReport);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `📧 Send Full Report to My Email`;
    }
}

function downloadReport(email, profile, report) {
    const content = `DiabetesControl AI Expert - Progress Report\nDate: ${new Date().toLocaleString()}\nPatient: ${profile.name || "N/A"}\nEmail: ${email}\n${"=".repeat(50)}\n\n${report}`;
    const blob = new Blob([content], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `diabetes-report-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    showToast("📄", "Report downloaded (email service requires SES setup).");
}

// ========== HELPERS ==========

function val(id) { return document.getElementById(id)?.value?.trim() || ""; }
function setVal(id, v) { if (v && document.getElementById(id)) document.getElementById(id).value = v; }

function setLoading(id) {
    document.getElementById(id).innerHTML = `<div class="flex items-center justify-center py-6 gap-3"><div class="spinner"></div><span class="text-sm text-gray-400">AI analyzing...</span></div>`;
}

function errorHtml(msg) {
    return `<div class="bg-red-50 rounded-xl p-4 border border-red-200"><p class="text-sm text-red-700">⚠️ ${escapeHtml(msg)}</p></div>`;
}

function showToast(icon, msg) {
    const t = document.getElementById("toast");
    document.getElementById("toast-icon").textContent = icon;
    document.getElementById("toast-message").textContent = msg;
    t.classList.remove("translate-y-20", "opacity-0");
    t.classList.add("translate-y-0", "opacity-100");
    setTimeout(() => { t.classList.add("translate-y-20", "opacity-0"); t.classList.remove("translate-y-0", "opacity-100"); }, 3500);
}

function formatMd(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/\*\*\*(.*?)\*\*\*/g, "<strong><em>$1</em></strong>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-xs">$1</code>')
        .replace(/^### (.*$)/gm, '<h4 class="font-semibold text-gray-800 mt-3 mb-1">$1</h4>')
        .replace(/^## (.*$)/gm, '<h3 class="font-semibold text-gray-800 text-base mt-3 mb-1">$1</h3>')
        .replace(/^# (.*$)/gm, '<h2 class="font-bold text-gray-900 text-lg mt-3 mb-2">$1</h2>')
        .replace(/^- (.*$)/gm, '• $1<br>')
        .replace(/^(\d+)\. (.*$)/gm, '$1. $2<br>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
