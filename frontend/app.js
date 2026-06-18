/**
 * DiabetesControl AI Expert
 * Tabbed interface — each tool has dedicated AI calls.
 * Features: Cognito auth, Polly TTS, DynamoDB profiles, chat history, dark theme
 */

let sessionId = null;
let ttsEnabled = false;
let labImageBase64 = "";
let labImageType = "image/jpeg";
let labFileText = "";
let results = {};
let chatHistory = []; // AI Coach chat messages

document.addEventListener("DOMContentLoaded", () => {
    initSession();
    loadProfile();
    setupTabs();
    loadLatestInsight();
    loadTheme();
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
    const authEmail = localStorage.getItem("dc_cognito_email");
    const role = localStorage.getItem("dc_role") || "patient";
    if (authEmail) p.email = authEmail;

    localStorage.setItem("dc_profile", JSON.stringify(p));
    showBadge(p.name);
    renderProfileOverview();

    if (p.email) {
        fetch(`${CONFIG.API_ENDPOINT}/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...p, _role: role }),
        }).then(r => {
            if (r.ok) toast("☁️", "Profile saved to your account!");
            else toast("💾", "Saved locally (cloud sync failed).");
        }).catch(() => toast("💾", "Saved locally."));
    } else {
        toast("⚠️", "Sign in to save profile to your account.");
    }
}

async function loadCloudProfile(email) {
    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/profile?email=${encodeURIComponent(email)}`);
        if (res.ok) {
            const data = await res.json();
            if (data.status === "found" && data.profile) {
                applyProfile(data.profile);
                toast("☁️", `Profile loaded for ${email}`);
                return;
            }
        }
    } catch (e) { /* fallback to local */ }
    // No cloud profile found — try local
    const s = localStorage.getItem("dc_profile");
    if (s) { try { applyProfile(JSON.parse(s)); } catch {} }
}

function loadProfile() {
    // Only auto-load local profile if NOT signed in (signed-in users load via onSignedIn)
    const authEmail = localStorage.getItem("dc_cognito_email");
    if (authEmail) return; // Will be loaded after Cognito session check

    const s = localStorage.getItem("dc_profile");
    if (!s) return;
    try {
        const p = JSON.parse(s);
        applyProfile(p);
    } catch(e) { console.error(e); }
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
    loadUserData(p);
}

function deleteProfile() {
    const authEmail = localStorage.getItem("dc_cognito_email");
    const email = authEmail || v("input-email");
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

// ========== TTS (Amazon Polly) ==========
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    document.getElementById("tts-label").textContent = ttsEnabled ? "On" : "Off";
    document.getElementById("tts-btn").style.background = ttsEnabled ? "#dcfce7" : "";
    if (!ttsEnabled) { if (window.currentAudio) window.currentAudio.pause(); }
}

async function speakSection(id) {
    const txt = document.getElementById(id)?.innerText;
    if (!txt || txt.length < 30) return;

    // Try Polly first, fallback to browser TTS
    try {
        const clean = txt.replace(/[🥗🧪⚡📋🤖🔊📧👤📊⚠️📈✓✗💪💧🩺🍽️🏃✅🔴]/g, "").substring(0, 2900);
        const res = await fetch(`${CONFIG.API_ENDPOINT}/polly`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: clean }),
        });
        if (res.ok) {
            const data = await res.json();
            if (data.audio) {
                const audioBlob = Uint8Array.from(atob(data.audio), c => c.charCodeAt(0));
                const blob = new Blob([audioBlob], { type: "audio/mp3" });
                const url = URL.createObjectURL(blob);
                if (window.currentAudio) window.currentAudio.pause();
                window.currentAudio = new Audio(url);
                window.currentAudio.play();
                toast("🔊", "Playing with Amazon Polly...");
                return;
            }
        }
    } catch (e) { /* fallback to browser TTS */ }

    // Fallback: browser TTS
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

    // Save lab image to profile for doctor viewing
    const authEmail = localStorage.getItem("dc_cognito_email");
    if (authEmail && labImageBase64) {
        fetch(`${CONFIG.API_ENDPOINT}/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: authEmail, _labImage: labImageBase64.substring(0, 50000) }),
        }).catch(() => {});
    }

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

            // Persist insight
            localStorage.setItem("dc_latest_insight", data.response);
            renderLatestInsight(data.response);
            // Save insights to cloud
            saveUserData();
        } else {
            const err = await res.json().catch(() => ({}));
            el.innerHTML = errBox(err.error || "Error");
        }
    } catch(e) { el.innerHTML = errBox(e.message); }
}

// ========== AI COACH CHAT ==========
async function sendCoachMessage() {
    const input = document.getElementById("coach-input");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";

    // Add user message to UI
    addChatBubble("user", msg);
    chatHistory.push({ role: "user", text: msg });

    // Build context-aware prompt
    const p = getProfile();
    const ctx = `Patient: ${p.name||"User"}, ${p.age||"?"}yo, ${p.dtype||"Type 2"} for ${p.years||"?"} years. HbA1c: ${p.hba1c||"?"}%, BP: ${p.bp||"?"}, Weight: ${p.weight||"?"}kg. Meds: ${p.meds||"unknown"}. Challenge: ${p.challenge||"?"}.`;
    const analysisCtx = Object.entries(results).filter(([k,v])=>v).map(([k,v])=>`[${k} analysis]: ${v.substring(0,300)}`).join("\n");
    const recentChat = chatHistory.slice(-6).map(m => `${m.role}: ${m.text}`).join("\n");

    const prompt = `You are a compassionate diabetes coach chatbot. DO NOT call any tools. Respond directly.

PATIENT CONTEXT:
${ctx}

RECENT ANALYSES (for reference):
${analysisCtx || "None yet"}

CONVERSATION HISTORY:
${recentChat}

Current question: "${msg}"

Respond naturally as a chatbot. Be concise (2-4 sentences unless detail is needed). Use the patient context and analyses to give personalized answers. Be warm and encouraging.`;

    // Show typing indicator
    const typingId = "typing-" + Date.now();
    const container = document.getElementById("coach-messages");
    const typingEl = document.createElement("div");
    typingEl.id = typingId;
    typingEl.className = "flex gap-2";
    typingEl.innerHTML = `<div class="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-sm flex-shrink-0">🤖</div><div class="bg-gray-100 dark:bg-gray-700 rounded-xl px-3 py-2 text-sm text-gray-500"><span class="animate-pulse">Thinking...</span></div>`;
    container.appendChild(typingEl);
    container.scrollTop = container.scrollHeight;

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: prompt, session_id: sessionId }),
        });
        document.getElementById(typingId)?.remove();
        if (res.ok) {
            const data = await res.json();
            addChatBubble("bot", data.response);
            chatHistory.push({ role: "bot", text: data.response });
            saveUserData();
            if (ttsEnabled) speakSection("coach-messages");
        } else {
            addChatBubble("bot", "Sorry, I couldn't process that. Try again.");
        }
    } catch(e) {
        document.getElementById(typingId)?.remove();
        addChatBubble("bot", "Connection error. Please try again.");
    }
}

function addChatBubble(role, text) {
    const container = document.getElementById("coach-messages");
    const div = document.createElement("div");
    div.className = "flex gap-2" + (role === "user" ? " justify-end" : "");
    if (role === "user") {
        div.innerHTML = `<div class="bg-blue-600 text-white rounded-xl rounded-tr-sm px-3 py-2 text-sm max-w-[80%]">${esc(text)}</div>`;
    } else {
        div.innerHTML = `<div class="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-sm flex-shrink-0">🤖</div><div class="bg-gray-100 dark:bg-gray-700 rounded-xl rounded-tl-sm px-3 py-2 text-sm text-gray-700 dark:text-gray-200 max-w-[80%]">${formatMd(text)}</div>`;
    }
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function clearChat() {
    if (!confirm("Clear chat history?")) return;
    chatHistory = [];
    const container = document.getElementById("coach-messages");
    container.innerHTML = `<div class="flex gap-2"><div class="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-sm flex-shrink-0">🤖</div><div class="bg-gray-100 dark:bg-gray-700 rounded-xl rounded-tl-sm px-3 py-2 text-sm text-gray-700 dark:text-gray-200 max-w-[80%]">Chat cleared. Ask me anything!</div></div>`;
    saveUserData();
    toast("🗑️", "Chat cleared.");
}

function loadChatHistory() {
    if (!chatHistory.length) return;
    const container = document.getElementById("coach-messages");
    container.innerHTML = "";
    // Add welcome
    addChatBubble("bot", "Welcome back! I remember our conversation. How can I help today?");
    // Replay history
    chatHistory.forEach(m => addChatBubble(m.role, m.text));
}

// ========== DATA PERSISTENCE (per user) ==========
function saveUserData() {
    const authEmail = localStorage.getItem("dc_cognito_email");
    if (!authEmail) return;

    const userData = {
        email: authEmail,
        insights: results.insights || null,
        chatHistory: chatHistory.slice(-50), // Keep last 50 messages
        results: Object.fromEntries(Object.entries(results).map(([k,v]) => [k, v?.substring(0, 2000)])),
    };

    fetch(`${CONFIG.API_ENDPOINT}/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...getProfile(), _userData: JSON.stringify(userData) }),
    }).catch(() => {});
}

function loadUserData(profile) {
    if (!profile || !profile._userData) return;
    try {
        const data = JSON.parse(profile._userData);
        if (data.insights) {
            results.insights = data.insights;
            localStorage.setItem("dc_latest_insight", data.insights);
            renderLatestInsight(data.insights);
            const el = document.getElementById("out-insights");
            if (el) el.innerHTML = formatMd(data.insights);
        }
        if (data.chatHistory && data.chatHistory.length) {
            chatHistory = data.chatHistory;
            loadChatHistory();
        }
        if (data.results) {
            Object.entries(data.results).forEach(([k, v]) => {
                if (v && !results[k]) results[k] = v;
            });
        }
    } catch(e) { console.error("loadUserData error:", e); }
}

// ========== THEME ==========
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.toggle("dark");
    localStorage.setItem("dc_theme", isDark ? "dark" : "light");
    document.getElementById("theme-icon").textContent = isDark ? "☀️" : "🌙";
}

function loadTheme() {
    const saved = localStorage.getItem("dc_theme");
    if (saved === "dark") {
        document.documentElement.classList.add("dark");
        document.getElementById("theme-icon").textContent = "☀️";
    }
}

function renderLatestInsight(text) {
    const el = document.getElementById("latest-insight");
    if (!el || !text) return;
    // Show a short preview (first 300 chars)
    const preview = text.substring(0, 300).replace(/\n/g, " ").replace(/[#*]/g, "");
    el.innerHTML = `<p class="text-sm text-gray-700 leading-relaxed">${esc(preview)}${text.length > 300 ? "..." : ""}</p>
        <button onclick="switchTab('insights')" class="mt-2 text-xs text-brand-600 font-medium hover:underline">View full insights →</button>`;
}

function loadLatestInsight() {
    const saved = localStorage.getItem("dc_latest_insight");
    if (saved) renderLatestInsight(saved);
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

// ========== STEP FUNCTIONS PIPELINE ==========
async function runPipeline() {
    const p = getProfile();
    if (!p.name && !p.hba1c) { toast("⚠️", "Fill your profile first (at least name + HbA1c)."); return; }

    const btn = document.getElementById("pipeline-btn");
    const status = document.getElementById("pipeline-status");
    btn.disabled = true;
    btn.textContent = "⏳ Running Pipeline...";
    status.classList.remove("hidden");

    const ctx = `Patient: ${p.name||"User"}, ${p.age||"?"}yo ${p.sex||""}, ${p.dtype||"Type 2"} diabetes for ${p.years||"?"} years. HbA1c: ${p.hba1c||"?"}% (goal: ${p.goalHba1c||"?"}%), BP: ${p.bp||"?"}, Weight: ${p.weight||"?"}kg, Height: ${p.height||"?"}cm. Medications: ${p.meds||"unknown"}. Challenge: ${p.challenge||"not specified"}.`;

    const steps = [
        { name: "Meal Analysis", id: "out-meal", prompt: `You are a diabetes nutritionist. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nThe patient hasn't logged a specific meal, so provide general meal guidance:\n1. **Recommended daily carb targets** for their profile\n2. **Sample breakfast, lunch, dinner** with glycemic index notes\n3. **Foods to avoid** and **foods to prefer**\n4. **Portion tips**\n\nBe specific to their diabetes type and medications.` },
        { name: "Lab Interpretation", id: "out-lab", prompt: `You are a clinical lab interpreter. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nBased on HbA1c of ${p.hba1c||"?"}% and BP of ${p.bp||"?"}:\n- Interpret their HbA1c against ADA guidelines\n- Assess cardiovascular risk from BP\n- Recommend which labs to get next (lipid panel, kidney function, etc.)\n- Provide timeline for retesting\n\nMark status with ✅ Normal / ⚠️ Borderline / 🔴 High Risk.` },
        { name: "Risk Prediction", id: "out-risk", prompt: `You are a diabetes risk specialist. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nBased on their profile, assess:\n1. **Hypoglycemia Risk** (Low/Mod/High) based on their medications\n2. **Hyperglycemia Risk** based on HbA1c level\n3. **Cardiovascular Risk** based on BP and diabetes duration\n4. **Complication Risk** (eyes, kidneys, nerves) based on years with diabetes\n5. **Immediate Actions** (2-3 things to do this week)\n\nBe specific and evidence-based.` },
        { name: "Plan Generation", id: "out-plan", prompt: `You are a diabetes plan generator. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nCreate a complete daily plan:\n**🍽️ NUTRITION** (6 meals with times and specific foods)\n**💧 HYDRATION** (daily target + schedule)\n**🏃 ACTIVITY** (morning/afternoon/evening)\n**📊 MONITORING** (when to check glucose)\n**💊 MEDICATION TIMING**\n\nMake it realistic and personalized to their challenge.` },
        { name: "Health Insights", id: "out-insights", prompt: null },
    ];

    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        status.innerHTML = `<span class="inline-block w-2 h-2 bg-brand-500 rounded-full animate-pulse mr-1"></span> Step ${i+1}/5: ${step.name}...`;

        // Build insights prompt using previous results
        let prompt = step.prompt;
        if (step.name === "Health Insights") {
            const allData = Object.entries(results).filter(([k,v])=>v&&k!=="insights").map(([k,v]) => `[${k}]: ${v?.substring(0,400)}`).join("\n");
            prompt = `You are a diabetes health insights analyst. DO NOT call any tools. Respond directly.\n\n${ctx}\n\nPrevious analyses:\n${allData}\n\nGenerate:\n## 📊 Health Score (1-10)\n## 📈 Positive Trends (2-3)\n## ⚠️ Concerns (2-3)\n## 🎯 This Week's Focus (3 goals)\n## 💡 Tips (3 personalized)\n## 📅 Next Steps`;
        }

        try {
            const res = await fetch(`${CONFIG.API_ENDPOINT}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: prompt, session_id: sessionId }),
            });
            if (res.ok) {
                const data = await res.json();
                const key = ["meal","lab","risk","plan","insights"][i];
                results[key] = data.response;
                const outEl = document.getElementById(step.id);
                if (outEl) outEl.innerHTML = formatMd(data.response);
            }
        } catch (e) { /* continue pipeline */ }
    }

    // Save insights
    if (results.insights) {
        localStorage.setItem("dc_latest_insight", results.insights);
        renderLatestInsight(results.insights);
    }

    status.innerHTML = `✅ Pipeline complete! All 5 analyses generated.`;
    btn.disabled = false;
    btn.textContent = "🚀 Run Full Analysis Pipeline";
    document.getElementById("email-btn").disabled = false;
    toast("✅", "Full analysis pipeline complete!");
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


// ========== COGNITO AUTH ==========
let authMode = "signin"; // signin, signup, confirm
let cognitoUser = null;

function getUserPool() {
    const poolData = {
        UserPoolId: CONFIG.COGNITO_USER_POOL_ID,
        ClientId: CONFIG.COGNITO_CLIENT_ID,
    };
    return new AmazonCognitoIdentity.CognitoUserPool(poolData);
}

function showAuthModal() {
    document.getElementById("auth-modal").classList.remove("hidden");
    document.getElementById("auth-modal").classList.add("flex");
}

function closeAuthModal() {
    document.getElementById("auth-modal").classList.add("hidden");
    document.getElementById("auth-modal").classList.remove("flex");
    document.getElementById("auth-error").classList.add("hidden");
}

function switchAuthMode(mode) {
    authMode = mode;
    const title = document.getElementById("auth-title");
    const submit = document.getElementById("auth-submit");
    const switchBtn = document.getElementById("auth-switch");
    const confirmRow = document.getElementById("auth-confirm-row");
    const roleRow = document.getElementById("auth-role-row");
    document.getElementById("auth-error").classList.add("hidden");

    if (mode === "signup") {
        title.textContent = "Create Account";
        submit.textContent = "Sign Up";
        switchBtn.textContent = "Already have an account? Sign In";
        switchBtn.setAttribute("onclick", "switchAuthMode('signin')");
        confirmRow.classList.add("hidden");
        roleRow.classList.remove("hidden");
    } else if (mode === "confirm") {
        title.textContent = "Verify Email";
        submit.textContent = "Confirm";
        confirmRow.classList.remove("hidden");
        roleRow.classList.add("hidden");
    } else {
        title.textContent = "Sign In";
        submit.textContent = "Sign In";
        switchBtn.textContent = "Need an account? Sign Up";
        switchBtn.setAttribute("onclick", "switchAuthMode('signup')");
        confirmRow.classList.add("hidden");
        roleRow.classList.add("hidden");
    }
}

function handleAuth() {
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    const errorEl = document.getElementById("auth-error");
    errorEl.classList.add("hidden");

    if (!email || !password) { showAuthError("Email and password required."); return; }

    if (authMode === "signup") {
        signUp(email, password);
    } else if (authMode === "confirm") {
        confirmSignUp(email);
    } else {
        signIn(email, password);
    }
}

function signUp(email, password) {
    const userPool = getUserPool();
    const roleRadio = document.querySelector('input[name="auth-role-radio"]:checked');
    const role = roleRadio ? roleRadio.value : "patient";
    const attributeList = [
        new AmazonCognitoIdentity.CognitoUserAttribute({ Name: "email", Value: email })
    ];
    userPool.signUp(email, password, attributeList, null, (err, result) => {
        if (err) { showAuthError(err.message); return; }
        localStorage.setItem("dc_role", role);
        // Save role to DynamoDB immediately so doctors appear in list
        fetch(`${CONFIG.API_ENDPOINT}/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, _role: role, name: email.split("@")[0], verified: role === "patient" }),
        }).catch(() => {});
        toast("✅", "Account created! Check email for verification code.");
        switchAuthMode("confirm");
    });
}

function confirmSignUp(email) {
    const code = document.getElementById("auth-code").value.trim();
    if (!code) { showAuthError("Enter the verification code from your email."); return; }
    const userPool = getUserPool();
    const userData = { Username: email, Pool: userPool };
    const cogUser = new AmazonCognitoIdentity.CognitoUser(userData);
    cogUser.confirmRegistration(code, true, (err, result) => {
        if (err) { showAuthError(err.message); return; }
        // Save role to DynamoDB now that account is confirmed
        const role = localStorage.getItem("dc_role") || "patient";
        fetch(`${CONFIG.API_ENDPOINT}/profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, _role: role, name: email.split("@")[0], verified: false }),
        }).then(() => {
            toast("✅", "Email verified! You can now sign in.");
            switchAuthMode("signin");
        }).catch(() => {
            toast("✅", "Email verified! You can now sign in.");
            switchAuthMode("signin");
        });
    });
}

function signIn(email, password) {
    const userPool = getUserPool();
    const authDetails = new AmazonCognitoIdentity.AuthenticationDetails({ Username: email, Password: password });
    const userData = { Username: email, Pool: userPool };
    const cogUser = new AmazonCognitoIdentity.CognitoUser(userData);

    // Get selected role from radio buttons
    const roleRadio = document.querySelector('input[name="auth-role-radio"]:checked');
    const role = roleRadio ? roleRadio.value : "patient";

    cogUser.authenticateUser(authDetails, {
        onSuccess: (session) => {
            cognitoUser = cogUser;
            localStorage.setItem("dc_cognito_email", email);
            localStorage.setItem("dc_role", role);

            if (role === "expert") {
                window.location.href = "doctor.html";
            } else {
                onSignedIn(email);
                closeAuthModal();
            }
        },
        onFailure: (err) => { showAuthError(err.message); }
    });
}

function onSignedIn(email) {
    const btn = document.getElementById("auth-btn");
    btn.textContent = "Sign Out";
    btn.setAttribute("onclick", "signOut()");
    btn.classList.remove("bg-brand-600");
    btn.classList.add("bg-gray-600");

    const role = localStorage.getItem("dc_role") || "patient";
    
    // If doctor, redirect to doctor dashboard
    if (role === "expert") {
        window.location.href = "doctor.html";
        return;
    }

    toast("✅", `Signed in as ${email}`);
    const emailInput = document.getElementById("input-email");
    if (emailInput) emailInput.value = email;
    loadCloudProfile(email);
    loadDoctors();
    loadDoctorReports();
}

function signOut() {
    const userPool = getUserPool();
    const currentUser = userPool.getCurrentUser();
    if (currentUser) currentUser.signOut();
    cognitoUser = null;
    localStorage.removeItem("dc_cognito_email");
    localStorage.removeItem("dc_profile");
    const btn = document.getElementById("auth-btn");
    btn.textContent = "Sign In";
    btn.setAttribute("onclick", "showAuthModal()");
    btn.classList.add("bg-brand-600");
    btn.classList.remove("bg-gray-600");
    // Clear form
    document.querySelectorAll(".inp").forEach(el => el.value = "");
    document.getElementById("profile-badge").classList.add("hidden");
    document.getElementById("profile-badge").classList.remove("flex");
    document.getElementById("overview-content").innerHTML = `<p class="text-sm text-gray-400 text-center py-8">Sign in to load your profile.</p>`;
    results = {};
    toast("👋", "Signed out. Profile cleared.");
}

function checkExistingSession() {
    const userPool = getUserPool();
    const currentUser = userPool.getCurrentUser();
    if (currentUser) {
        currentUser.getSession((err, session) => {
            if (!err && session && session.isValid()) {
                cognitoUser = currentUser;
                const email = localStorage.getItem("dc_cognito_email") || "";
                onSignedIn(email);
            }
        });
    }
}

function showAuthError(msg) {
    const el = document.getElementById("auth-error");
    el.textContent = msg;
    el.classList.remove("hidden");
}

function signInAsDoctor() {
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    if (!email || !password) { showAuthError("Enter email and password first."); return; }

    const userPool = getUserPool();
    const authDetails = new AmazonCognitoIdentity.AuthenticationDetails({ Username: email, Password: password });
    const userData = { Username: email, Pool: userPool };
    const cogUser = new AmazonCognitoIdentity.CognitoUser(userData);

    cogUser.authenticateUser(authDetails, {
        onSuccess: (session) => {
            localStorage.setItem("dc_cognito_email", email);
            localStorage.setItem("dc_role", "expert");
            window.location.href = "doctor.html";
        },
        onFailure: (err) => { showAuthError(err.message); }
    });
}

// Check for existing Cognito session on load
document.addEventListener("DOMContentLoaded", () => { setTimeout(checkExistingSession, 500); });


// ========== DOCTOR-PATIENT INTERACTION ==========
let selectedDoctorEmail = null;

async function loadDoctors() {
    const el = document.getElementById("doctor-list");
    if (!el) return;
    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/doctors`);
        if (res.ok) {
            const data = await res.json();
            const doctors = (data.doctors || []).filter(d => d.verified === true || d.verified === "true");
            if (!doctors.length) { el.innerHTML = `<p class="text-sm text-gray-400 text-center py-4">No verified doctors available yet.</p>`; return; }
            el.innerHTML = doctors.map(d => `
                <button onclick="selectDoctor('${d.email}')" class="w-full text-left px-3 py-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-blue-50 dark:hover:bg-gray-700 transition">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm">👨‍⚕️</div>
                        <div>
                            <p class="text-sm font-medium text-gray-900 dark:text-white">Dr. ${(d.name || d.email.split("@")[0])}</p>
                            <p class="text-xs text-gray-500">${d.email}</p>
                            <span class="text-xs text-green-600">✓ Verified</span>
                        </div>
                    </div>
                </button>
            `).join("");
        }
    } catch(e) { el.innerHTML = `<p class="text-sm text-gray-400">Could not load doctors.</p>`; }
}

function selectDoctor(email) {
    selectedDoctorEmail = email;
    document.getElementById("selected-doctor").innerHTML = `<span class="text-brand-600 font-medium">👨‍⚕️ Dr. ${email.split("@")[0]}</span> selected`;
}

async function sendToDoctor() {
    if (!selectedDoctorEmail) { toast("⚠️", "Select a doctor first."); return; }
    const authEmail = localStorage.getItem("dc_cognito_email");
    if (!authEmail) { toast("⚠️", "Sign in first."); return; }

    const p = getProfile();
    const message = document.getElementById("patient-message")?.value || "";
    const insightData = results.insights || localStorage.getItem("dc_latest_insight") || "";

    const referral = {
        doctorEmail: selectedDoctorEmail,
        patientEmail: authEmail,
        patientName: p.name || authEmail,
        profile: p,
        insights: insightData.substring(0, 2000),
        message: message,
        timestamp: Date.now(),
    };

    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/referral`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(referral),
        });
        if (res.ok) {
            toast("✅", `Health data sent to Dr. ${selectedDoctorEmail.split("@")[0]}!`);
            document.getElementById("patient-message").value = "";
        } else { toast("⚠️", "Failed to send. Try again."); }
    } catch(e) { toast("⚠️", "Connection error."); }
}

async function loadDoctorReports() {
    const el = document.getElementById("doctor-reports");
    if (!el) return;
    const authEmail = localStorage.getItem("dc_cognito_email");
    if (!authEmail) return;
    try {
        const res = await fetch(`${CONFIG.API_ENDPOINT}/doctor-reports?email=${encodeURIComponent(authEmail)}`);
        if (res.ok) {
            const data = await res.json();
            const reports = data.reports || [];
            if (!reports.length) return;
            el.innerHTML = reports.map(r => `
                <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-medium text-blue-700 dark:text-blue-300">From: Dr. ${(r.doctorEmail||"").split("@")[0]}</span>
                        <span class="text-xs text-gray-400">${r.timestamp ? new Date(r.timestamp).toLocaleDateString() : ""}</span>
                    </div>
                    <p class="text-sm text-gray-700 dark:text-gray-200">${r.notes || "No notes"}</p>
                </div>
            `).join("");
        }
    } catch(e) {}
}
