"""Prepare everything for the live demo showcase."""
import boto3
import json
import time
from decimal import Decimal

REGION = "ap-southeast-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
profiles = dynamodb.Table("diabetes-care-profiles")
logs = dynamodb.Table("diabetes-care-health-logs")
referrals = dynamodb.Table("diabetes-care-referrals")

# Load the lab image base64
with open("presentation/demo_lab_report_base64.txt", "r") as f:
    lab_image_b64 = f.read().strip()

print("🩺 Preparing Demo Data...")
print("=" * 50)

# ========== PATIENT ACCOUNT ==========
print("\n👤 Preparing Patient: patient.test@diabetes.demo")

# Rich userData with analysis results
user_data = {
    "insights": "## 📊 Health Score: 5/10\n\nYour diabetes management is improving but still needs work.\n\n## 📈 Positive Trends\n- HbA1c dropping: 8.1% → 7.8% over past 7 days — great progress!\n- Blood pressure stabilizing below 140 systolic\n- You're logging consistently — a key success factor\n\n## ⚠️ Areas of Concern\n- LDL cholesterol at 138 mg/dL (target: <100) — cardiovascular risk elevated\n- HDL too low at 38 mg/dL — need more omega-3 and exercise\n- Fasting glucose still above target at 145 mg/dL\n\n## 🎯 This Week's Focus\n1. Add 20-minute walk after dinner every night\n2. Switch from white rice to brown rice or cauliflower rice\n3. Schedule a lipid panel follow-up with your doctor\n\n## 💡 Personalized Tips\n- Your metformin works best taken WITH meals — make sure you're timing it right\n- Post-meal glucose of 215 is too high — try eating protein before carbs\n- Consider requesting a statin discussion at next appointment (LDL 138 is concerning for 8-year T2DM)",
    "chatHistory": [
        {"role": "user", "text": "My sugar was 245 after dinner last night. Should I be worried?"},
        {"role": "bot", "text": "A reading of 245 mg/dL is quite high and definitely something to take seriously, though it's not an emergency if you're feeling okay. This is likely a post-meal spike. What did you eat for dinner? High-carb meals (rice, noodles, bread) can cause this. For now: drink plenty of water, take a 15-minute walk if possible, and check again in 2 hours. If it stays above 300 or you feel dizzy/nauseous, seek medical attention."},
        {"role": "user", "text": "I had nasi lemak with extra rice and teh tarik"},
        {"role": "bot", "text": "That explains it! Nasi lemak with extra rice is a high glycemic load meal. The coconut rice alone is ~60g carbs per cup, plus the teh tarik adds ~25g sugar. Total: roughly 100g+ carbs in one meal — that's 2-3x your ideal per-meal target of 30-45g.\n\nFor tomorrow's breakfast, try: Nasi lemak but with half portion rice + extra egg + no sweet drink. Or better: roti canai (lower GI) with dhal. The protein and fat slow glucose absorption significantly."},
        {"role": "user", "text": "What should I eat tonight?"},
        {"role": "bot", "text": "For tonight, here's a diabetes-friendly dinner:\n\n🥗 Option 1: Grilled fish + stir-fried kangkung + 1/2 cup brown rice\n🍗 Option 2: Chicken soup with lots of vegetables + small portion mee hoon\n🥚 Option 3: Telur dadar (2 eggs) + ulam salad + tempeh\n\nKey rules: Fill half your plate with non-starchy vegetables, eat protein first, keep carbs to a fist-sized portion. Drink plain water. Take your metformin with the meal. Check glucose 2 hours after — aim for under 180."},
    ],
    "results": {
        "meal": "## Meal Analysis: Nasi Lemak + Teh Tarik\n\n| Food | Carbs | GI | GL |\n|------|-------|-----|----|\n| Coconut rice (1.5 cups) | 90g | High (73) | 65.7 |\n| Sambal | 5g | Low | 2.0 |\n| Fried egg | 1g | Low | 0 |\n| Cucumber | 2g | Low | 0.3 |\n| Teh Tarik | 25g | High | 17.5 |\n\n**Total: 123g carbs | Glycemic Load: 85.5 (VERY HIGH)**\n\n⚠️ This meal exceeds recommended carb intake by 3x. Predicted glucose spike: 200-250 mg/dL within 1 hour.\n\n### Healthier Alternatives:\n1. Half portion rice + extra egg + teh-o kosong\n2. Swap to nasi kerabu (lower GI due to herbs)\n3. Replace teh tarik with unsweetened Chinese tea",
        "lab": "## Lab Interpretation (20 Jun 2026)\n\n### Glycemic Control\n- ✅→⚠️ HbA1c: 7.8% — Above target (<7.0%) but improving from 8.1%\n- 🔴 Fasting Glucose: 148 mg/dL — Above target (70-100)\n- 🔴 Post-meal Glucose: 215 mg/dL — Above target (<180)\n\n### Lipid Panel\n- 🔴 Total Cholesterol: 228 mg/dL — Above target (<200)\n- 🔴 LDL: 138 mg/dL — Above target (<100). HIGH cardiovascular risk.\n- 🔴 HDL: 38 mg/dL — Below target (>40 for males)\n- 🔴 Triglycerides: 195 mg/dL — Above target (<150)\n\n### Kidney Function\n- ✅ Creatinine: 1.20 mg/dL — Within normal range\n- ⚠️ eGFR: 72 — Mildly decreased. Monitor quarterly.\n- ⚠️ Urine Microalbumin: 32 mg/g — Early kidney stress detected\n\n### Recommendations\n1. Discuss statin therapy for LDL (target <100 with 8yr T2DM history)\n2. Increase omega-3 intake for triglycerides and HDL\n3. Recheck eGFR and microalbumin in 3 months\n4. Current HbA1c trend is positive — maintain lifestyle changes",
        "risk": "## Risk Assessment\n\n### 🔻 Hypoglycemia Risk: LOW\n- Current medications (Metformin + Glimepiride) have moderate hypo risk\n- No recent low readings reported\n- Meal pattern seems regular\n\n### 🔺 Hyperglycemia Risk: HIGH\n- Fasting glucose 148 (above target)\n- Post-meal spike to 245 after high-carb dinner\n- HbA1c 7.8% indicates chronic elevation\n\n### ↕️ Glucose Variability: MODERATE\n- Range from 120 to 245 in past week (125 mg/dL swing)\n- Variability mainly driven by carb intake at dinner\n\n### ⏰ Immediate Actions\n1. Check glucose before bed tonight — if >250, consider extra water intake\n2. Tomorrow: eat protein-first breakfast to start the day stable\n3. Add a 15-minute post-dinner walk (reduces spikes by 20-30%)\n\n### 🚨 Seek Help If\n- Glucose stays above 300 mg/dL for 4+ hours\n- Nausea, vomiting, fruity breath (possible DKA)\n- Glucose below 54 mg/dL (severe hypo)",
        "plan": "## Your Daily Plan\n\n### 🍽️ Nutrition\n- **7:00 AM**: Roti canai (1 piece) + dhal + teh-o kosong | ~30g carbs\n- **10:00 AM**: Handful of almonds + small apple | ~15g carbs\n- **12:30 PM**: Chicken rice (half portion rice) + extra vegetables | ~35g carbs\n- **3:00 PM**: 2 pieces wholemeal crackers + cheese | ~10g carbs\n- **7:00 PM**: Grilled fish + kangkung + 1/2 cup brown rice | ~25g carbs\n- **Before bed**: Sugar-free yogurt if hungry\n\n### 💧 Hydration\n- Target: 2.5L water/day (8-10 glasses)\n- First 500ml upon waking\n- No sugary drinks — plain water, unsweetened tea, black coffee\n\n### 🏃 Activity\n- Morning: 10-minute stretching/walk before work\n- After lunch: 10-minute walk\n- After dinner: 20-minute brisk walk (KEY for glucose control)\n\n### 📊 Monitoring\n- Check fasting glucose: before breakfast\n- Check 2-hour post-meal: after dinner\n- Log both readings daily\n- Weekly weight check (target: lose 0.5kg/week)"
    }
}

# Update patient profile with full data + lab image + user data
profiles.update_item(
    Key={"email": "patient.test@diabetes.demo"},
    UpdateExpression="SET #ud = :ud, #li = :li, glucose = :g, ldl = :ldl, hdl = :hdl, triglycerides = :trig, egfr = :egfr, creatinine = :creat",
    ExpressionAttributeNames={"#ud": "_userData", "#li": "_labImage"},
    ExpressionAttributeValues={
        ":ud": json.dumps(user_data),
        ":li": lab_image_b64,
        ":g": "148",
        ":ldl": "138",
        ":hdl": "38",
        ":trig": "195",
        ":egfr": "72",
        ":creat": "1.2",
    }
)
print("  ✓ Patient profile updated with lab image + full analysis data")

# Make sure health logs exist (they should from earlier, but add more)
base_time = int(time.time())
new_logs = [
    {"days_ago": 14, "hba1c": 8.3, "glucose": 172, "weight": 92, "systolic": 145, "diastolic": 92, "ldl": 148, "hdl": 35, "triglycerides": 225, "egfr": 68, "creatinine": 1.35},
    {"days_ago": 10, "hba1c": 8.1, "glucose": 165, "weight": 91, "systolic": 142, "diastolic": 90, "ldl": 142, "hdl": 36, "triglycerides": 210, "egfr": 70, "creatinine": 1.3},
    {"days_ago": 7, "hba1c": 8.0, "glucose": 155, "weight": 90.5, "systolic": 140, "diastolic": 89, "ldl": 140, "hdl": 37, "triglycerides": 205, "egfr": 70, "creatinine": 1.27},
    {"days_ago": 5, "hba1c": 7.9, "glucose": 150, "weight": 90, "systolic": 139, "diastolic": 88, "ldl": 139, "hdl": 37, "triglycerides": 200, "egfr": 71, "creatinine": 1.24},
    {"days_ago": 3, "hba1c": 7.8, "glucose": 148, "weight": 89.5, "systolic": 138, "diastolic": 88, "ldl": 138, "hdl": 38, "triglycerides": 196, "egfr": 71, "creatinine": 1.22},
    {"days_ago": 1, "hba1c": 7.8, "glucose": 145, "weight": 89, "systolic": 137, "diastolic": 87, "ldl": 136, "hdl": 38, "triglycerides": 195, "egfr": 72, "creatinine": 1.2},
    {"days_ago": 0, "hba1c": 7.8, "glucose": 142, "weight": 89, "systolic": 136, "diastolic": 87, "ldl": 135, "hdl": 39, "triglycerides": 192, "egfr": 72, "creatinine": 1.2},
]
for log in new_logs:
    item = {"email": "patient.test@diabetes.demo", "timestamp": base_time - (log["days_ago"] * 86400)}
    for k, v in log.items():
        if k != "days_ago":
            item[k] = Decimal(str(v))
    logs.put_item(Item=item)
print(f"  ✓ Added {len(new_logs)} health log entries (past 14 days)")

# ========== REFERRAL ==========
print("\n📤 Updating referral to doctor...")

# Delete old referrals and create fresh one with full shared data
response = referrals.scan()
for item in response.get("Items", []):
    referrals.delete_item(Key={"doctorEmail": item["doctorEmail"], "timestamp": item["timestamp"]})

referrals.put_item(Item={
    "doctorEmail": "doctor.test@diabetes.demo",
    "timestamp": base_time - 3600,
    "patientEmail": "patient.test@diabetes.demo",
    "patientName": "Ahmed Hassan",
    "message": "Hi Doctor, my blood sugar has been very high after dinner (245 mg/dL). I'm worried about my kidney numbers too. Can you review my latest labs?",
    "type": "referral",
    "_includes": json.dumps({"profile": True, "insights": True, "labs": True, "meal": True, "risk": True, "plan": True, "chat": True}),
    "profile": json.dumps({
        "name": "Ahmed Hassan", "age": "52", "dtype": "Type 2", "hba1c": "7.8",
        "weight": "89", "bp": "136/87", "meds": "Metformin 1000mg BD, Glimepiride 2mg OD",
        "challenge": "Post-meal spikes, high LDL", "goalHba1c": "6.5"
    }),
    "insights": user_data["insights"][:2000],
    "labs": user_data["results"]["lab"][:2000],
    "meal": user_data["results"]["meal"][:2000],
    "risk": user_data["results"]["risk"][:2000],
    "plan": user_data["results"]["plan"][:2000],
    "chat": json.dumps(user_data["chatHistory"]),
})
print("  ✓ Referral created with full shared data (profile, insights, labs, meal, risk, plan, chat)")

# ========== DOCTOR ACCOUNT ==========
print("\n👨‍⚕️ Verifying Doctor: doctor.test@diabetes.demo")
profiles.update_item(
    Key={"email": "doctor.test@diabetes.demo"},
    UpdateExpression="SET verified = :v, #n = :n",
    ExpressionAttributeNames={"#n": "name"},
    ExpressionAttributeValues={":v": True, ":n": "Dr. Sarah Chen"}
)
print("  ✓ Doctor verified as Dr. Sarah Chen")

print("\n" + "=" * 50)
print("✅ DEMO READY!\n")
print("  🌐 App URL: https://d3onijdn12lthk.cloudfront.net")
print("\n  Patient Account:")
print("    Email: patient.test@diabetes.demo")
print("    Pass:  Patient123!")
print("    Select: Patient")
print("\n  Doctor Account:")
print("    Email: doctor.test@diabetes.demo")
print("    Pass:  Doctor123!")
print("    Select: Doctor / Expert")
print("\n  Admin: /admin.html → diabetes2025admin")
print("\n  📸 Lab photo ready at: presentation/demo_lab_report.jpg")
print("\n  DEMO FLOW:")
print("  1. Sign in as patient → show pre-loaded profile")
print("  2. Go to Lab tab → upload demo_lab_report.jpg → click Interpret")
print("  3. Go to AI Coach → ask 'What should I eat tonight?'")
print("  4. Go to See a Doctor → show Dr. Sarah Chen → data already sent")
print("  5. Sign out → Sign in as Doctor → see Ahmed in patients")
print("  6. Click Ahmed → Charts tab → show real 14-day trends")
print("  7. Shared Data tab → show everything patient sent")
print("  8. AI Insights → click Analyze Charts → show AI interpretation")
print("  9. Alerts tab → show threshold alerts (HbA1c > 8)")
print(" 10. Send report back to patient")
