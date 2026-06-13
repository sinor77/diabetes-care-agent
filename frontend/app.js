/**
 * DiabetesControl AI Expert
 * Tabbed interface — each tool has dedicated AI calls.
 */

let sessionId = null;
let ttsEnabled = false;
let labImageBase64 = "";
let labImageType = "image/jpeg";
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

function switchTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach(b => {
        b.classList.toggle("active", b.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-content").forEach(c => { c.classList.remove("active"); c.classList.add("hidden"); });
    const t = document.getElementById("tab-" + tabName);
    if (t) { t.classList.remove("hidden"); t.classList.add("active"); }
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
    renderProfileOverview();

    // Save to cloud DB
    if (p.email) {
        fetch(`${CONFIG.API_ENDPOINT}/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(p),
        }).then(r => {
            if (r.ok) toast("☁️", "Profile saved to cloud!");
            else toast("💾", "Saved locally (cloud sync failed).");
        }).catch(() => toast("💾", "Saved locally."));
    } else {
        toast("💾", "Saved locally. Add email for cloud sync.");
    }
}

function loadProfile() {
    // Try cloud first if email in localStorage
    const s = localStorage.getItem("dc_profile");
    let localProfile = null;
    if (s) {
        try { localProfile = JSON.parse(s); } catch {}
    }

    if (localProfile && localProfile.email) {
        // Try loading from cloud
        fetch(`${CONFIG.API_ENDPOINT}/profile?email=${encodeURIComponent(localProfile.email)}`)
            .then(r => r.json())
            .then(data => {
                if (data.status === "found" && data.profile) {
                    applyProfile(data.profile);
                    toast("☁️", `Profile loaded from cloud!`);
                } else {
                    applyProfile(localProfile);
                }
            })
            .catch(() => applyProfile(localProfile));
    } else if (localProfile) {
        applyProfile(localProfile);
    }
}

function applyProfile(p) {
    if (!p) return;
    setV("input-name",p.name); setV("input-email",p.email); setV("input-dtype",p.dtype);
    setV("input-age",p.age); setV("input-sex",p.sex); setV("input-hba1c",p.hba1c);
    setV("input-goal-hba1c",p.goalHba1c); setV("input-bp",p.bp); setV("input-weight",p.weight);
    setV("input-height",p.height); setV("input-years",p.years); setV("input-meds",p.meds);
    setV("input-challenge",p.challenge); setV("input-goal",p.goal);
    localStorage.setItem("dc_profile", JSON.stringify(p));
    showBadge(p.name);
    renderProfileOverview();
    if (p.name) toast("👤", `Welcome back, ${p.name}!`);
}

function deleteProfile() {
    const email = v("input-email");
    if (!email) { toast("⚠️", "No profile to delete."); return; }
    if (!confirm(`Delete profile for ${email}? This cannot be undone.`)) return;

    // Delete from cloud
    fetch(`${CONFIG.API_ENDPOINT}/profile?email=${encodeURIComponent(email)}`, { method: "DELETE" })
        .then(r => r.json())
        .then(() => toast("🗑️", "Profile deleted from cloud."))
        .catch(() => {});

    // Clear local
    localStorage.removeItem("dc_profile");
    document.querySelectorAll(".inp").forEach(el => el.value = "");
    document.getElementById("overview-content").innerHTML = `<p class="text-sm text-gray-400 text-center py-8">Profile deleted. Start fresh!</p>`;
    document.getElementById("profile-badge").classList.add("hidden");
    toast("🗑️", "Profile deleted!");
}

function showBadge(name) {
    if (!name) return;
    const b = document.getElementById("profile-badge");
    b.classList.remove("hidden"); b.classList.add("inline-flex");
    document.getElementById("badge-name").textContent = name;
}

function renderProfileOverview() {
    const p = getProfile();
    const el = document.getElementById("overview-content");
    if (!el) return;
    const bmi = (p.weight && p.height) ? (parseFloat(p.weight) / Math.pow(parseFloat(p.height)/100, 2)).toFixed(1) : "—";
    el.innerHTML = `
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div class="stat-card"><div class="stat-label">Name</div><div class="stat-value">${p.name||"—"}</div></div>
            <div class="stat-card"><div class="stat-label">Diabetes Type</div><div class="stat-value">${p.dtype||"—"}</div></div>
            <div class="stat-card"><div class="stat-label">Age</div><div class="stat-value">${p.age||"—"} yrs</div></div>
            <div class="stat-card"><div class="stat-label">Years w/ Diabetes</div><div class="stat-value">${p.years||"—"}</div></div>
            <div class="stat-card"><div class="stat-label">Current HbA1c</div><div class="stat-value text-${parseFloat(p.hba1c)>7?'red':'green'}-600">${p.hba1c||"—"}%</div></div>
            <div class="stat-card"><div class="stat-label">Goal HbA1c</div><div class="stat-value text-brand-600">${p.goalHba1c||"—"}%</div></div>
            <div class="stat-card"><div class="stat-label">Blood Pressure</div><div class="stat-value">${p.bp||"—"}</div></div>
            <div class="stat-card"><div class="stat-label">Weight</div><div class="stat-value">${p.weight||"—"} kg</div></div>
            <div class="stat-card"><div class="stat-label">BMI</div><div class="stat-value">${bmi}</div></div>
            <div class="stat-card col-span-2 md:col-span-3"><div class="stat-label">Medications</div><div class="stat-value text-sm">${p.meds||"—"}</div></div>
            <div class="stat-card col-span-2 md:col-span-3"><div class="stat-label">Main Challenge</div><div class="stat-value text-sm">${p.challenge||"—"}</div></div>
        </div>
    `;
}

// ========== FILE UPLOAD (with compression) ==========
function onLabUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    document.getElementById("lab-upload-status").innerHTML = `<p class="text-xs text-brand-600 font-semibold">✓ ${file.name}</p><p class="text-xs text-gray-400">${(file.size/1024).toFixed(0)} KB</p>`;

    if (file.type.startsWith("image/")) {
        labImageType = file.type;
        // Compress image to max 800px and reasonable quality
        compressImage(file, 800, 0.7).then(b64 => {
            labImageBase64 = b64;
            labFileText = "[Image uploaded - will be analyzed with AI vision]";
            document.getElementById("lab-upload-status").innerHTML += `<p class="text-xs text-gray-400 mt-1">Compressed for analysis</p>`;
        });
    } else if (file.type.startsWith("text/") || file.name.match(/\.(txt|csv)$/)) {
        const reader = new FileReader();
        reader.onload = (ev) => { labFileText = ev.target.result; labImageBase64 = ""; };
        reader.readAsText(file);
    } else {
        labFileText = "[File: " + file.name + ". Please type key values below.]";
        labImageBase64 = "";
    }
}

function compressImage(file, maxSize, quality) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement("canvas");
                let w = img.width, h = img.height;
                if (w > maxSize || h > maxSize) {
                    if (w > h) { h = Math.round(h * maxSize / w); w = maxSize; }
                    else { w = Math.round(w * maxSize / h); h = maxSize; }
                }
                canvas.width = w; canvas.height = h;
                canvas.getContext("2d").drawImage(img, 0, 0, w, h);
                const dataUrl = canvas.toDataURL("image/jpeg", quality);
                resolve(dataUrl.split(",")[1]);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
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
    if (!txt || txt.length < 30) return;
    speechSynthesis.cancel();
    const clean = txt.replace(/[🥗🧪⚡📋🤖🔊📧👤📊⚠️📈✓✗💪💧🩺🍽️🏃✅🔴]/g, "");
    const chunks = clean.match(/.{1,280}[.!?\n]|.{1,280}/g) || [clean];
    chunks.forEach(c => { const u = new SpeechSynthesisUtterance(c); u.rate = 0.95; speechSynthesis.speak(u); });
}

// ========== RUN ANALYSIS ==========
async function runSingle(tool) {
    const p = getProfile();
    const outId = "out-" + tool;
    const el = document.getElementById(outId);
    if (!el) return;
    el.innerHTML = `<div class="loading-state"><div class="spinner"></div>Analyzing...</div>`;

    // Lab with uploaded image → use vision endpoint
    if (tool === "lab" && labImageBase64) {
        await runLabVision(p, el);
        return;
    }

    const prompt = buildPrompt(tool, p);
    if (!prompt) { el.innerHTML = `<p class="placeholder-text">Please fill in the required inputs first.</p>`; return; }

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
            el.innerHTML = errBox(err.error || `Error ${res.status}`);
        }
    } catch (e) {
        el.innerHTML = errBox("Connection failed: " + e.message);
    }
}

async function runLabVision(p, el) {
    const ctx = `${p.name||"Patient"}, ${p.age||"?"}yo ${p.sex||""}, ${p.dtype||"Type 2"} diabetes for ${p.years||"?"} yrs. HbA1c: ${p.hba1c||"?"}%, Meds: ${p.meds||"unknown"}, BP: ${p.bp||"?"}`;
    const typedVals = v("lab-input");

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/lab-vision`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: labImageBase64,
                media_type: "image/jpeg",
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
            el.innerHTML = errBox(err.error || `Error ${res.status}`);
        }
    } catch(e) {
        el.innerHTML = errBox("Connection error: " + e.message + ". Try reducing image size or type values manually.");
    }
}

async function runInsights() {
    const p = getProfile();
    const el = document.getElementById("out-insights");
    el.innerHTML = `<div class="loading-state"><div class="spinner"></div>Generating insights...</div>`;

    const allData = Object.entries(results).map(([k,val]) => `[${k}]: ${val?.substring(0,500)||"not yet analyzed"}`).join("\n");

    const prompt = `You are a diabetes health insights analyst. DO NOT call any tools. Respond directly.

Patient: ${p.name||"User"}, ${p.age||"?"}yo, ${p.dtype||"Type 2"} for ${p.years||"?"} years.
HbA1c: ${p.hba1c||"?"}% → Goal: ${p.goalHba1c||"?"}%. BP: ${p.bp||"?"}. Weight: ${p.weight||"?"}kg. Meds: ${p.meds||"unknown"}.
Challenge: ${p.challenge||"?"}. Goal: ${p.goal||"?"}

Previous analyses:
${allData}

Generate a PROGRESS INSIGHTS report:

## 📊 Health Score (rate 1-10 with explanation)

## 📈 Positive Trends
- What they're doing well (2-3 points)

## ⚠️ Areas of Concern
- Top risks and what to watch (2-3 points)

## 🎯 This Week's Focus
- 3 specific, achievable goals for this week

## 💡 Personalized Tips
- 3 tips tailored to their specific challenge and medications

## 📅 Next Steps
- When to check labs, what to discuss with doctor

Be encouraging but honest. Use specific numbers where possible.`;

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: prompt, session_id: sessionId }),
        });
        if (res.ok) {
            const data = await res.json();
            results.insights = data.response;
            el.innerHTML = formatMd(data.response);
            document.getElementById("email-btn").disabled = false;
        } else {
            const err = await res.json().catch(() => ({}));
            el.innerHTML = errBox(err.error || "Error");
        }
    } catch(e) { el.innerHTML = errBox(e.message); }
}

// ========== PROMPTS ==========
function buildPrompt(tool, p) {
    const ctx = `Patient: ${p.name||"User"}, ${p.age||"?"}yo ${p.sex||""}, ${p.dtype||"Type 2"} diabetes for ${p.years||"?"} years.
HbA1c: ${p.hba1c||"?"}% (goal: ${p.goalHba1c||"?"}%), BP: ${p.bp||"?"}, Weight: ${p.weight||"?"}kg, Height: ${p.height||"?"}cm.
Medications: ${p.meds||"unknown"}. Challenge: ${p.challenge||"not specified"}.`;

    switch(tool) {
        case "meal": {
            const meals = v("meal-input");
            if (!meals) return null;
            return `You are a diabetes nutritionist. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nMeals:\n${meals}\n\nAnalyze:\n1. **Carbs per item** and total\n2. **Glycemic Index** (Low/Med/High) per item\n3. **Glycemic Load** of full meal\n4. **Blood sugar impact** prediction\n5. **3 healthier swaps**\n6. **1 pro tip** to reduce the spike\n\nFormat with clear headers.`;
        }
        case "lab": {
            const labs = labFileText || v("lab-input");
            if (!labs && !p.hba1c) return null;
            return `You are a clinical lab interpreter. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nLab values:\n${labs || "HbA1c: "+p.hba1c+"%"}\n\nFor each value:\n- Value + unit → ADA range → ✅Normal / ⚠️Borderline / 🔴High Risk\n- Plain explanation\n\nThen: Overall Assessment, Top Concerns, 3 Recommendations, Retest Timeline.`;
        }
        case "risk": {
            const m = v("risk-meals"), ex = v("risk-exercise"), gl = v("risk-glucose"), lm = v("risk-lastmeal");
            if (!m && !ex && !gl && !p.hba1c) return null;
            return `You are a diabetes risk specialist. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nToday's meals: ${m||"not logged"}\nExercise: ${ex||"none"}\nGlucose readings: ${gl||"none"} mg/dL\nLast meal: ${lm||"unknown"}\n\nAssess:\n1. **Hypoglycemia Risk** (Low/Mod/High + why)\n2. **Hyperglycemia Risk** (Low/Mod/High + why)\n3. **Glucose Variability**\n4. **Immediate Actions** (2-3 NOW)\n5. **Red Flags** (when to seek help)`;
        }
        case "plan": {
            return `You are a diabetes plan generator. DO NOT call any tools. Respond directly.\n\n${ctx}\nFitness: ${v("plan-fitness")||"Moderate"}. Diet: ${v("plan-diet")||"No restriction"}. Allergies: ${v("plan-allergies")||"None"}. Notes: ${v("plan-notes")||"None"}.\n\nCreate daily plan:\n**🍽️ NUTRITION** (6 meals with times, foods, carb targets)\n**💧 HYDRATION** (daily mL + schedule)\n**🏃 ACTIVITY** (morning/post-meal/evening)\n**📊 MONITORING** (glucose check times)\n**💊 MEDICATION TIMING**\n\nBe specific, realistic, achievable.`;
        }
        case "coach": {
            const q = v("coach-input");
            if (!q) return null;
            return `You are a compassionate diabetes coach. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nQuestion: "${q}"\n\nProvide:\n- Direct answer (clear, actionable)\n- Evidence/reasoning\n- Motivational note personalized to them`;
        }
    }
    return null;
}

// ========== EMAIL ==========
async function sendEmailReport() {
    const email = v("input-email");
    if (!email) { toast("⚠️", "Add email in Profile tab first."); return; }
    if (!Object.keys(results).length) { toast("⚠️", "Generate at least one analysis first."); return; }
    const btn = document.getElementById("email-btn");
    btn.disabled = true; btn.textContent = "Sending...";
    const report = Object.entries(results).filter(([k,v])=>v).map(([k,v]) => `=== ${k.toUpperCase()} ===\n${v}`).join("\n\n---\n\n");
    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/email-report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, name: v("input-name")||"User", analysis: report, profile: getProfile() }),
        });
        if (res.ok) { toast("📧", `Sent to ${email}!`); }
        else { downloadFallback(report); }
    } catch { downloadFallback(report); }
    finally { btn.disabled = false; btn.textContent = "Send Report to My Email"; }
}

function downloadFallback(report) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([`DiabetesControl AI Report\n${new Date().toLocaleString()}\n${"=".repeat(40)}\n\n${report}`]));
    a.download = `diabetes-report-${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    toast("📄", "Downloaded (set up SES for email delivery).");
}

// ========== HELPERS ==========
function v(id) { return document.getElementById(id)?.value?.trim() || ""; }
function setV(id, val) { const el = document.getElementById(id); if (el && val) el.value = val; }
function errBox(msg) { return `<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">⚠️ ${esc(msg)}</div>`; }

function toast(icon, msg) {
    const t = document.getElementById("toast");
    document.getElementById("toast-icon").textContent = icon;
    document.getElementById("toast-msg").textContent = msg;
    t.classList.remove("translate-y-16","opacity-0");
    setTimeout(() => t.classList.add("translate-y-16","opacity-0"), 3500);
}

function formatMd(text) {
    if (!text) return "";
    return text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
        .replace(/\*\*\*(.*?)\*\*\*/g,"<strong><em>$1</em></strong>")
        .replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>")
        .replace(/\*(.*?)\*/g,"<em>$1</em>")
        .replace(/`(.*?)`/g,'<code style="background:#f3f4f6;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>')
        .replace(/^#### (.*$)/gm,'<h4>$1</h4>').replace(/^### (.*$)/gm,'<h3>$1</h3>')
        .replace(/^## (.*$)/gm,'<h2>$1</h2>').replace(/^# (.*$)/gm,'<h2>$1</h2>')
        .replace(/^[-•] (.*$)/gm,'<li>$1</li>').replace(/^(\d+)\. (.*$)/gm,'<li>$1. $2</li>')
        .replace(/((<li>.*<\/li>\n?)+)/g,'<ul>$1</ul>')
        .replace(/\n\n/g,'<br><br>').replace(/\n/g,'<br>');
}
function esc(t) { const d=document.createElement("div"); d.textContent=t; return d.innerHTML; }
