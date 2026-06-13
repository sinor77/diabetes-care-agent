"""
Plan Generator Tool
Synthesizes outputs from meal analyzer, lab interpreter, and risk predictor
into a structured, actionable daily routine.
"""

from typing import Any


def _generate_nutrition_plan(meal_analysis: dict = None, lab_data: dict = None,
                             risk_data: dict = None, preferences: dict = None) -> dict:
    """Generate nutrition recommendations."""
    plan = {
        "breakfast": {
            "time": "7:00-8:00 AM",
            "guidelines": [
                "Start with protein (eggs, Greek yogurt, or nuts) before carbs",
                "Include healthy fat (avocado, olive oil, or nut butter)",
                "Limit to 30-45g carbohydrates",
            ],
            "example_meals": [
                "2 eggs + ½ avocado + 1 slice whole grain toast",
                "Greek yogurt + berries + walnuts + chia seeds",
                "Veggie omelet with cheese + small apple",
            ],
        },
        "morning_snack": {
            "time": "10:00-10:30 AM",
            "guidelines": [
                "15-20g carbs paired with protein",
                "Helps prevent pre-lunch glucose dip",
            ],
            "example_meals": [
                "Handful of almonds + small apple",
                "String cheese + 5 whole grain crackers",
                "Celery + 2 tbsp peanut butter",
            ],
        },
        "lunch": {
            "time": "12:00-1:00 PM",
            "guidelines": [
                "Fill half the plate with non-starchy vegetables",
                "Quarter plate lean protein",
                "Quarter plate complex carbs",
                "Include fiber-rich foods to slow digestion",
            ],
            "example_meals": [
                "Large salad + grilled chicken + quinoa + olive oil dressing",
                "Lentil soup + side salad + whole grain roll",
                "Turkey lettuce wraps + bean salad",
            ],
        },
        "afternoon_snack": {
            "time": "3:00-3:30 PM",
            "guidelines": [
                "Especially important if dinner is after 6:30 PM",
                "Protein-focused to maintain energy",
            ],
            "example_meals": [
                "Hard-boiled egg + cherry tomatoes",
                "Hummus + raw vegetables",
                "Small handful of mixed nuts",
            ],
        },
        "dinner": {
            "time": "6:00-7:00 PM",
            "guidelines": [
                "Largest vegetable portion of the day",
                "Moderate protein, limited starchy carbs",
                "Finish eating 3+ hours before bed for better fasting glucose",
            ],
            "example_meals": [
                "Baked salmon + roasted broccoli + small sweet potato",
                "Stir-fry vegetables + tofu + cauliflower rice",
                "Grilled chicken + large salad + ½ cup brown rice",
            ],
        },
    }

    # Customize based on risk data
    adjustments = []
    if risk_data and risk_data.get("overall_risk", {}).get("level") == "high":
        adjustments.append("⚠️ Due to elevated risk: Reduce carbs by ~20% and increase monitoring frequency.")
        for meal_key in plan:
            plan[meal_key]["guidelines"].insert(0, "Check blood glucose before and 2hr after this meal.")

    if meal_analysis and meal_analysis.get("meal_summary", {}).get("overall_impact") == "high":
        adjustments.append("Previous meal had high glycemic impact. Next meal should emphasize protein + vegetables.")

    if lab_data:
        concerning = lab_data.get("concerning_results", [])
        for item in concerning:
            if "cholesterol" in item.get("metric", "").lower() or "ldl" in item.get("metric", "").lower():
                adjustments.append("Lipids elevated: Increase omega-3 sources (fatty fish 2x/week), reduce saturated fats.")
                break

    # Apply dietary preferences
    if preferences:
        diet_type = preferences.get("diet_type", "").lower()
        if diet_type in ["vegetarian", "vegan"]:
            adjustments.append(f"Adapted for {diet_type} diet. Ensure adequate B12 and iron intake.")
        if preferences.get("allergies"):
            adjustments.append(f"Note: Avoiding {', '.join(preferences['allergies'])}.")

    return {"meals": plan, "adjustments": adjustments}


def _generate_hydration_plan(weight_kg: float = 70) -> dict:
    """Generate hydration recommendations."""
    # Base: 30-35 mL per kg body weight
    base_ml = weight_kg * 33
    glasses = round(base_ml / 250)

    return {
        "daily_target_ml": round(base_ml),
        "daily_target_glasses": glasses,
        "schedule": [
            {"time": "Upon waking", "amount_ml": 500, "note": "Warm water with lemon aids digestion and rehydrates after sleep."},
            {"time": "Mid-morning", "amount_ml": 250, "note": "Room temperature water. Helps maintain focus."},
            {"time": "Before lunch", "amount_ml": 250, "note": "Drinking 30min before meals may help with portion control."},
            {"time": "Early afternoon", "amount_ml": 500, "note": "Peak dehydration time. Add electrolytes if exercising."},
            {"time": "Late afternoon", "amount_ml": 250, "note": "Herbal tea is a good option here."},
            {"time": "Before dinner", "amount_ml": 250, "note": "Avoid large amounts with meals to aid digestion."},
            {"time": "Evening", "amount_ml": 250, "note": "Reduce intake 2hr before bed to avoid nighttime waking."},
        ],
        "tips": [
            "Dehydration can falsely elevate blood glucose readings.",
            "If blood glucose is high (>250 mg/dL), increase water intake.",
            "Avoid sugary drinks — they spike glucose without hydrating well.",
            "Coffee/tea count toward hydration but limit to 2-3 cups (caffeine can affect glucose).",
            "Keep a water bottle visible as a reminder.",
        ],
    }


def _generate_activity_plan(risk_data: dict = None, fitness_level: str = "moderate") -> dict:
    """Generate activity recommendations aligned with ADA guidelines."""
    # ADA recommends: 150+ min/week moderate aerobic + 2-3 days resistance training
    base_plan = {
        "weekly_target": {
            "aerobic_minutes": 150,
            "resistance_sessions": 2,
            "flexibility_sessions": 2,
        },
        "daily_schedule": {
            "morning": {
                "time": "6:30-7:00 AM or after breakfast",
                "activity": "10-minute walk or gentle stretching",
                "purpose": "Activates metabolism and improves insulin sensitivity for the day.",
                "glucose_note": "Check glucose. If <90, have a small snack first.",
            },
            "post_breakfast": {
                "time": "30-60 min after breakfast",
                "activity": "15-minute brisk walk",
                "purpose": "Significantly reduces post-meal glucose spike (by 20-30%).",
                "glucose_note": "Best time to walk for glucose management!",
            },
            "midday": {
                "time": "12:00-1:00 PM",
                "activity": "5-minute movement break every hour if sedentary",
                "purpose": "Breaks up prolonged sitting which worsens insulin resistance.",
                "glucose_note": "Even standing for 3 minutes helps.",
            },
            "post_lunch": {
                "time": "30-60 min after lunch",
                "activity": "10-15 minute walk",
                "purpose": "Controls afternoon glucose. Boosts energy without caffeine.",
                "glucose_note": "Pair with a colleague for accountability.",
            },
            "afternoon": {
                "time": "3:00-5:00 PM",
                "activity": "Resistance training (if scheduled) or 20-min moderate cardio",
                "purpose": "Builds muscle mass which improves long-term insulin sensitivity.",
                "glucose_note": "Have a pre-workout snack (15g carbs + protein) if glucose <120.",
            },
            "evening": {
                "time": "After dinner (30-60 min post-meal)",
                "activity": "15-20 minute relaxed walk",
                "purpose": "Lowers dinner glucose spike and aids sleep quality.",
                "glucose_note": "Gentle pace — this is for glucose, not fitness.",
            },
        },
    }

    # Adjust based on fitness level
    if fitness_level == "beginner":
        base_plan["weekly_target"]["aerobic_minutes"] = 90
        base_plan["note"] = "Start with shorter durations and build up by 10% per week."
    elif fitness_level == "advanced":
        base_plan["weekly_target"]["aerobic_minutes"] = 200
        base_plan["weekly_target"]["resistance_sessions"] = 3

    # Adjust based on risk data
    precautions = []
    if risk_data and risk_data.get("overall_risk", {}).get("level") == "high":
        precautions.append("High risk detected: Always carry glucose tabs during activity.")
        precautions.append("Avoid exercise if blood glucose >250 mg/dL with ketones.")
        precautions.append("Monitor glucose every 30 minutes during extended activity.")

    base_plan["precautions"] = precautions
    return base_plan


def generate_plan(
    meal_analysis: dict = None,
    lab_data: dict = None,
    risk_data: dict = None,
    patient_info: dict = None,
) -> dict[str, Any]:
    """
    Generate a comprehensive daily management plan.

    Args:
        meal_analysis: Output from meal_analyzer tool
        lab_data: Output from lab_interpreter tool
        risk_data: Output from risk_predictor tool
        patient_info: Dict with optional keys: weight_kg, fitness_level, diet_type, allergies

    Returns:
        Structured daily plan with nutrition, hydration, and activity components.
    """
    patient_info = patient_info or {}
    weight_kg = patient_info.get("weight_kg", 70)
    fitness_level = patient_info.get("fitness_level", "moderate")
    preferences = {
        "diet_type": patient_info.get("diet_type", ""),
        "allergies": patient_info.get("allergies", []),
    }

    # Generate each component
    nutrition = _generate_nutrition_plan(meal_analysis, lab_data, risk_data, preferences)
    hydration = _generate_hydration_plan(weight_kg)
    activity = _generate_activity_plan(risk_data, fitness_level)

    # Priority actions based on all inputs
    priority_actions = []
    if risk_data and risk_data.get("immediate_actions"):
        priority_actions.extend(risk_data["immediate_actions"])
    if lab_data and lab_data.get("urgent_flags"):
        priority_actions.append("📞 Contact your healthcare provider about urgent lab results.")
    if meal_analysis and meal_analysis.get("meal_summary", {}).get("overall_impact") == "high":
        priority_actions.append("🚶 Take a 15-minute walk within the next 30 minutes to offset the meal impact.")

    # Daily monitoring checklist
    monitoring = {
        "glucose_checks": [
            {"time": "Fasting (before breakfast)", "target": "80-130 mg/dL"},
            {"time": "2hr post-breakfast", "target": "<180 mg/dL"},
            {"time": "Before lunch", "target": "80-130 mg/dL"},
            {"time": "2hr post-dinner", "target": "<180 mg/dL"},
            {"time": "Bedtime", "target": "100-140 mg/dL"},
        ],
        "additional_checks": [
            "Check before and after exercise",
            "Check if feeling symptomatic (shaky, dizzy, blurred vision)",
            "Check before driving",
        ],
        "daily_log_items": [
            "All meals and snacks with times",
            "Physical activity type and duration",
            "Glucose readings",
            "Medication timing",
            "Mood/energy level (1-5 scale)",
            "Hours of sleep",
        ],
    }

    return {
        "status": "success",
        "plan_date": "today",
        "priority_actions": priority_actions,
        "nutrition_plan": nutrition,
        "hydration_plan": hydration,
        "activity_plan": activity,
        "monitoring_checklist": monitoring,
        "motivational_note": (
            "Remember: Perfect days don't exist in diabetes management, and that's completely okay. "
            "Every small positive choice adds up. You're taking control by using this tool — "
            "that's already a win! 🌟"
        ),
        "disclaimer": (
            "This plan is educational guidance, not medical advice. Always follow your healthcare "
            "team's specific instructions, especially regarding medication and insulin dosing."
        ),
    }
