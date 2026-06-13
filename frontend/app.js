/**
 * DiabetesControl AI Expert
 * Tabbed interface with dedicated AI calls per tool.
 * Prompts are designed to get direct AI responses (no action group calls).
 */

let sessionId = null;
let ttsEnabled = false;
let labFileText = "";
let results = {};

document.addEventListener("DOMContentLoaded", () => {
    initSession();
    loadProfile();
    setupTabs();
});

// ========== SESSION ==========
async function initSession() {
    try {
        const r = await fetch(`${CONFIG.API_ENDPOINT}/session`);
        sessionId = r.ok ? (await r.json()).session_id : crypto.randomUUID();
    } catch { sessionId = crypto.randomUUID(); }
}

// ========== TABS ==========
function setupTabs() {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => { c.classList.remove("active"); c.classList.add("hidden"); });
            btn.classList.add("active");
            const tab = document.getElementById("tab-" + btn.dataset.tab);
            tab.classList.remove("hidden");
            tab.classList.add("active");
        });
    });
}

// ========== PROFILE ==========
function getProfile() {
    return {
        name: v("input-name"), email: v("input-email"), dtype: v("input-dtype"),
        age: v("input-age"), sex: v("input-sex"), hba1c: v("input-hba1c"),
        goalHba1c: v("input-goal-hba1c"), bp: v("input-bp"), weight: v("input-weight"),
        height: v("input-height"), years: v("input-years"), meds: v("input-meds"),
        challenge: v("input-challenge"), goal: v("input-goal"),
    };
}

function saveProfile() {
    const p = getProfile();
    localStorage.setItem("dc_profile", JSON.stringify(p));
    showBadge(p.name);
    toast("💾", "Profile saved!");
}

function loadProfile() {
    const s = localStorage.getItem("dc_profile");
    if (!s) return;
    try {
        const p = JSON.parse(s);
        setV("input-name",p.name); setV("input-email",p.email); setV("input-dtype",p.dtype);
        setV("input-age",p.age); setV("input-sex",p.sex); setV("input-hba1c",p.hba1c);
        setV("input-goal-hba1c",p.goalHba1c); setV("input-bp",p.bp); setV("input-weight",p.weight);
        setV("input-height",p.height); setV("input-years",p.years); setV("input-meds",p.meds);
        setV("input-challenge",p.challenge); setV("input-goal",p.goal);
        showBadge(p.name);
        if (p.name) toast("👤", `Welcome back, ${p.name}!`);
    } catch(e) { console.error(e); }
}

function showBadge(name) {
    if (!name) return;
    const b = document.getElementById("profile-badge");
    b.classList.remove("hidden"); b.classList.add("inline-flex");
    document.getElementById("badge-name").textContent = name;
}

// ========== FILE UPLOAD ==========
let labImageBase64 = "";
let labImageType = "";

function onLabUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    document.getElementById("lab-upload-status").innerHTML = `<p class="text-xs text-brand-600 font-semibold">✓ ${file.name}</p><p class="text-xs text-gray-400">${(file.size/1024).toFixed(0)} KB uploaded</p>`;

    if (file.type.startsWith("image/")) {
        // Read as base64 for vision API
        labImageType = file.type;
        const reader = new FileReader();
        reader.onload = (ev) => {
            // Remove the data:image/xxx;base64, prefix
            labImageBase64 = ev.target.result.split(",")[1];
            labFileText = "[Image uploaded and will be analyzed with AI vision]";
        };
        reader.readAsDataURL(file);
    } else if (file.type.startsWith("text/") || file.name.match(/\.(txt|csv)$/)) {
        const reader = new FileReader();
        reader.onload = (ev) => { labFileText = ev.target.result; };
        reader.readAsText(file);
    } else {
        labFileText = "[File uploaded: " + file.name + ". Please type key values below for analysis.]";
    }
}

// ========== TTS ==========
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    document.getElementById("tts-label").textContent = ttsEnabled ? "On" : "Off";
    document.getElementById("tts-btn").style.background = ttsEnabled ? "#dcfce7" : "";
    if (!ttsEnabled) speechSynthesis.cancel();
}

function speakSection(id) {
    const txt = document.getElementById(id)?.innerText;
    if (!txt || txt.length < 20) return;
    speechSynthesis.cancel();
    const clean = txt.replace(/[🥗🧪⚡📋🤖🔊📧👤📊⚠️📈✓✗💪💧🩺🍽️🏃]/g, "");
    const chunks = clean.match(/.{1,300}[.!?\n]|.{1,300}/g) || [clean];
    chunks.forEach(c => { const u = new SpeechSynthesisUtterance(c); u.rate = 0.95; speechSynthesis.speak(u); });
}

// ========== RUN ANALYSIS ==========
async function runSingle(tool) {
    const p = getProfile();
    const outId = "out-" + tool;
    const el = document.getElementById(outId);
    el.innerHTML = `<div class="loading-state"><div class="spinner"></div>Analyzing with AI...</div>`;

    // Special handling: Lab with image uses vision endpoint
    if (tool === "lab" && labImageBase64) {
        await runLabVision(p, el);
        return;
    }

    const prompt = buildPrompt(tool, p);
    if (!prompt) { el.innerHTML = `<div class="placeholder-text">Please fill in the required inputs.</div>`; return; }

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: prompt, session_id: sessionId }),
        });
        if (res.ok) {
            const data = await res.json();
            results[tool] = data.response;
            el.innerHTML = formatMd(data.response);
            document.getElementById("email-btn").disabled = false;
            if (ttsEnabled) speakSection(outId);
        } else {
            const err = await res.json().catch(() => ({}));
            el.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">Error: ${err.error || res.statusText}</div>`;
        }
    } catch (e) {
        el.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">Connection failed. Check your internet.</div>`;
    }
}

async function runLabVision(p, el) {
    const ctx = `${p.name||"Patient"}, ${p.age||"?"}yo, ${p.dtype||"Type 2"} diabetes, HbA1c: ${p.hba1c||"?"}%, Meds: ${p.meds||"unknown"}`;
    const typedVals = v("lab-input");

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/lab-vision`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: labImageBase64,
                media_type: labImageType,
                profile_context: ctx,
                typed_values: typedVals,
            }),
        });
        if (res.ok) {
            const data = await res.json();
            results.lab = data.response;
            el.innerHTML = formatMd(data.response);
            document.getElementById("email-btn").disabled = false;
            if (ttsEnabled) speakSection("out-lab");
        } else {
            const err = await res.json().catch(() => ({}));
            el.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">Error: ${err.error || res.statusText}</div>`;
        }
    } catch(e) {
        el.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">Connection failed: ${e.message}</div>`;
    }
}

function buildPrompt(tool, p) {
    // Profile context string shared across all prompts
    const ctx = `Patient: ${p.name||"User"}, ${p.age||"?"}yo ${p.sex||""}, ${p.dtype||"Type 2"} diabetes for ${p.years||"?"} years.
HbA1c: ${p.hba1c||"?"}% (goal: ${p.goalHba1c||"?"}%), BP: ${p.bp||"?"}, Weight: ${p.weight||"?"}kg, Height: ${p.height||"?"}cm.
Medications: ${p.meds||"unknown"}. Challenge: ${p.challenge||"not specified"}. Goal: ${p.goal||"improve management"}.`;

    const labData = labFileText || v("lab-input");

    switch(tool) {
        case "meal":
            const meals = v("meal-input");
            if (!meals) return null;
            return `You are an expert diabetes nutritionist. DO NOT call any tools or functions. Respond directly.

${ctx}

The patient ate:
${meals}

Analyze this meal and provide:
1. **Estimated Carbohydrates** — for each food item and total
2. **Glycemic Index** — classify each item as Low (≤55), Medium (56-69), or High (≥70)
3. **Overall Glycemic Load** — Low (<10), Moderate (10-20), or High (>20)
4. **Blood Sugar Impact** — predicted spike severity and timing
5. **Healthier Alternatives** — 3 specific swaps to reduce glycemic impact
6. **Pro Tip** — one actionable tip to minimize the glucose spike from this meal

Format clearly with headers and bullet points.`;

        case "lab":
            if (!labData && !p.hba1c) return null;
            return `You are a clinical lab interpreter for diabetes care. DO NOT call any tools or functions. Respond directly.

${ctx}

Lab results provided:
${labData || `HbA1c: ${p.hba1c}%`}

For EACH lab value:
- State the value with unit
- Show the ADA reference range
- Mark as ✅ Normal, ⚠️ Borderline, or 🔴 Out of Range
- Brief plain-language explanation

Then provide:
- **Overall Assessment** (2-3 sentences)
- **Top Concerns** (ranked by urgency)  
- **Recommendations** (3 specific actions)
- **Retest Timeline** (when to check again)

Be precise with numbers and evidence-based.`;

        case "risk":
            const riskMeals = v("risk-meals");
            const exercise = v("risk-exercise");
            const glucose = v("risk-glucose");
            const lastMeal = v("risk-lastmeal");
            if (!riskMeals && !exercise && !glucose && !p.hba1c) return null;
            return `You are a diabetes risk assessment specialist. DO NOT call any tools or functions. Respond directly.

${ctx}

Recent data:
- Meals today: ${riskMeals || "not logged"}
- Exercise: ${exercise || "none reported"}
- Recent glucose readings: ${glucose || "not provided"} mg/dL
- Last meal time: ${lastMeal || "unknown"}

Assess these risks (rate each as LOW / MODERATE / HIGH with explanation):

1. **🔻 Hypoglycemia Risk** — meal gaps, exercise timing, medication interactions
2. **🔺 Hyperglycemia Risk** — carb load, missed medication, stress
3. **↕️ Glucose Variability** — pattern analysis from readings
4. **⏰ Time-Sensitive Risks** — anything needing action in the next 2-4 hours

Then provide:
- **Immediate Actions** (2-3 things to do RIGHT NOW)
- **Red Flags** (when to seek emergency care)

Be specific and practical.`;

        case "plan":
            const fitness = v("plan-fitness");
            const diet = v("plan-diet");
            const allergies = v("plan-allergies");
            const notes = v("plan-notes");
            return `You are a diabetes daily plan generator. DO NOT call any tools or functions. Respond directly.

${ctx}
Fitness level: ${fitness||"Moderate"}. Diet: ${diet||"No restriction"}. Allergies: ${allergies||"None"}. Notes: ${notes||"None"}.

Create a COMPLETE daily plan:

**🍽️ NUTRITION** (with times and specific foods):
- Wake-up / Pre-breakfast
- Breakfast (with carb target)
- Mid-morning snack
- Lunch (with carb target)
- Afternoon snack
- Dinner (with carb target)
- Evening (if needed)

**💧 HYDRATION** (daily target in mL + schedule)

**🏃 ACTIVITY** (morning, post-meal, evening — type, duration, precautions)

**📊 MONITORING** (when to check glucose, what to log)

**💊 MEDICATION REMINDERS** (based on their meds)

Make it realistic, culturally aware, and achievable.`;

        case "coach":
            const question = v("coach-input");
            if (!question) return null;
            return `You are a compassionate, evidence-based diabetes coach. DO NOT call any tools or functions. Respond directly.

${ctx}
${labData ? `\nRecent labs: ${labData}` : ""}

Patient asks: "${question}"

Respond with:
- Direct answer to their question (clear, actionable)
- Evidence or reasoning behind your advice
- One motivational note personalized to them

Keep it warm but professional. Use simple language.`;
    }
    return null;
}

// ========== EMAIL ==========
async function sendEmailReport() {
    const email = v("input-email");
    if (!email) { toast("⚠️", "Add your email in the Profile tab first."); return; }
    if (!Object.keys(results).length) { toast("⚠️", "Generate at least one analysis first."); return; }

    const btn = document.getElementById("email-btn");
    btn.disabled = true; btn.textContent = "Sending...";

    const report = Object.entries(results).map(([k,v]) => `[${ {meal:"MEAL ANALYSIS",lab:"LAB INTERPRETATION",risk:"RISK ASSESSMENT",plan:"DAILY PLAN",coach:"AI COACHING"}[k]||k.toUpperCase()}]\n${v}`).join("\n\n---\n\n");

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/email-report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, name: v("input-name")||"User", analysis: report, profile: getProfile() }),
        });
        if (res.ok) { toast("📧", `Sent to ${email}!`); }
        else { downloadFallback(email, report); }
    } catch { downloadFallback(email, report); }
    finally { btn.disabled = false; btn.textContent = "Send Report to My Email"; }
}

function downloadFallback(email, report) {
    const txt = `DiabetesControl AI - Progress Report\nDate: ${new Date().toLocaleString()}\nEmail: ${email}\n${"=".repeat(50)}\n\n${report}`;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([txt]));
    a.download = `diabetes-report-${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    toast("📄", "Downloaded report (SES email not configured yet).");
}

// ========== HELPERS ==========
function v(id) { return document.getElementById(id)?.value?.trim() || ""; }
function setV(id, val) { const el = document.getElementById(id); if (el && val) el.value = val; }

function toast(icon, msg) {
    const t = document.getElementById("toast");
    document.getElementById("toast-icon").textContent = icon;
    document.getElementById("toast-msg").textContent = msg;
    t.classList.remove("translate-y-16","opacity-0");
    setTimeout(() => t.classList.add("translate-y-16","opacity-0"), 3500);
}

function formatMd(text) {
    if (!text) return "";
    return text
        .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
        .replace(/\*\*\*(.*?)\*\*\*/g,"<strong><em>$1</em></strong>")
        .replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>")
        .replace(/\*(.*?)\*/g,"<em>$1</em>")
        .replace(/`(.*?)`/g,'<code style="background:#f3f4f6;padding:1px 4px;border-radius:3px;font-size:0.8em">$1</code>')
        .replace(/^#### (.*$)/gm,'<h4>$1</h4>')
        .replace(/^### (.*$)/gm,'<h3>$1</h3>')
        .replace(/^## (.*$)/gm,'<h2>$1</h2>')
        .replace(/^# (.*$)/gm,'<h2>$1</h2>')
        .replace(/^[-•] (.*$)/gm,'<li>$1</li>')
        .replace(/^(\d+)\. (.*$)/gm,'<li>$1. $2</li>')
        .replace(/((<li>.*<\/li>\n?)+)/g,'<ul>$1</ul>')
        .replace(/\n\n/g,'<br><br>')
        .replace(/\n/g,'<br>');
}
