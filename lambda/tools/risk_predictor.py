"""
Risk Predictor Tool
Analyzes current patterns to flag near-term risks such as hypoglycemic or hyperglycemic events.
"""

from typing import Any
from datetime import datetime


def _calculate_meal_gap_risk(meals: list[dict]) -> dict:
    """Assess risk from meal timing gaps."""
    if not meals or len(meals) < 2:
        return {"risk_level": "unknown", "detail": "Insufficient meal data to assess timing patterns."}

    gaps = []
    sorted_meals = sorted(meals, key=lambda m: m.get("time", "00:00"))

    for i in range(1, len(sorted_meals)):
        try:
            t1 = datetime.strptime(sorted_meals[i - 1].get("time", "00:00"), "%H:%M")
            t2 = datetime.strptime(sorted_meals[i].get("time", "00:00"), "%H:%M")
            gap_hours = (t2 - t1).seconds / 3600
            gaps.append({
                "between": f"{sorted_meals[i-1].get('name', 'meal')} → {sorted_meals[i].get('name', 'meal')}",
                "gap_hours": round(gap_hours, 1),
            })
        except (ValueError, TypeError):
            continue

    max_gap = max(gaps, key=lambda g: g["gap_hours"]) if gaps else None

    if max_gap and max_gap["gap_hours"] > 6:
        return {
            "risk_level": "high",
            "detail": f"Long gap of {max_gap['gap_hours']}h detected ({max_gap['between']}). "
                      f"Gaps >6 hours significantly increase hypoglycemia risk, especially if on insulin or sulfonylureas.",
            "gaps": gaps,
        }
    elif max_gap and max_gap["gap_hours"] > 4.5:
        return {
            "risk_level": "moderate",
            "detail": f"Moderate gap of {max_gap['gap_hours']}h detected ({max_gap['between']}). "
                      f"Consider a small protein-rich snack between meals.",
            "gaps": gaps,
        }
    else:
        return {
            "risk_level": "low",
            "detail": "Meal spacing appears regular. Good job maintaining consistent eating patterns!",
            "gaps": gaps,
        }


def _calculate_exercise_risk(exercise: dict, last_meal_time: str = None,
                             medication: str = None) -> dict:
    """Assess hypoglycemia risk from exercise patterns."""
    if not exercise:
        return {"risk_level": "low", "detail": "No exercise data provided."}

    intensity = exercise.get("intensity", "moderate").lower()
    duration_min = exercise.get("duration_minutes", 30)
    exercise_time = exercise.get("time", None)

    risk_factors = []
    risk_score = 0

    # High intensity + long duration
    if intensity == "high" and duration_min > 45:
        risk_factors.append("High-intensity exercise >45min significantly lowers blood glucose for up to 24 hours.")
        risk_score += 3
    elif intensity == "high":
        risk_factors.append("High-intensity exercise can cause delayed hypoglycemia 6-12 hours later.")
        risk_score += 2
    elif intensity == "moderate" and duration_min > 60:
        risk_factors.append("Extended moderate exercise (>60min) depletes glycogen stores.")
        risk_score += 2

    # Exercise timing relative to meals
    if exercise_time and last_meal_time:
        try:
            ex_t = datetime.strptime(exercise_time, "%H:%M")
            meal_t = datetime.strptime(last_meal_time, "%H:%M")
            hours_since_meal = (ex_t - meal_t).seconds / 3600
            if hours_since_meal > 3:
                risk_factors.append(
                    f"Exercising {hours_since_meal:.1f}h after last meal increases hypo risk. "
                    f"Have a 15-20g carb snack before exercise."
                )
                risk_score += 2
        except (ValueError, TypeError):
            pass

    # Medication interaction
    if medication and medication.lower() in ["insulin", "sulfonylurea", "glipizide",
                                              "glyburide", "glimepiride"]:
        risk_factors.append(
            f"Taking {medication} with exercise increases hypoglycemia risk. "
            f"Monitor glucose before, during, and after exercise."
        )
        risk_score += 2

    if risk_score >= 4:
        risk_level = "high"
    elif risk_score >= 2:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "detail": " ".join(risk_factors) if risk_factors else "Exercise plan appears safe with standard precautions.",
        "precautions": [
            "Check blood glucose before exercise (target: 90-250 mg/dL to start).",
            "Carry fast-acting glucose (juice box, glucose tabs) during exercise.",
            "If glucose <90 mg/dL before exercise, consume 15-30g carbs first.",
            "Stay hydrated — dehydration can concentrate blood glucose readings.",
        ] if risk_score >= 2 else [],
    }


def _calculate_glucose_trend_risk(readings: list[dict]) -> dict:
    """Analyze glucose readings for concerning trends."""
    if not readings or len(readings) < 3:
        return {"risk_level": "unknown", "detail": "Need at least 3 glucose readings to assess trends."}

    values = [r.get("value", 0) for r in readings if r.get("value")]

    if not values:
        return {"risk_level": "unknown", "detail": "No valid glucose values found."}

    avg = sum(values) / len(values)
    high_readings = [v for v in values if v > 180]
    low_readings = [v for v in values if v < 70]
    very_high = [v for v in values if v > 250]
    variability = max(values) - min(values)

    risk_factors = []
    risk_score = 0

    if very_high:
        risk_factors.append(
            f"⚠️ {len(very_high)} reading(s) >250 mg/dL detected. "
            f"Persistent hyperglycemia increases DKA risk (Type 1) and causes organ damage."
        )
        risk_score += 4

    if low_readings:
        risk_factors.append(
            f"⚠️ {len(low_readings)} hypoglycemic reading(s) (<70 mg/dL). "
            f"Recurrent lows increase risk of hypoglycemia unawareness."
        )
        risk_score += 3

    if len(high_readings) > len(values) * 0.5:
        risk_factors.append(
            f"{len(high_readings)}/{len(values)} readings above target (>180). "
            f"Time-in-range goal is >70% between 70-180 mg/dL."
        )
        risk_score += 2

    if variability > 150:
        risk_factors.append(
            f"High glucose variability (range: {variability} mg/dL). "
            f"Large swings stress the cardiovascular system. Aim for <100 mg/dL variability."
        )
        risk_score += 2

    # Trend direction
    if len(values) >= 3:
        recent_trend = values[-1] - values[0]
        if recent_trend > 50:
            risk_factors.append("Upward glucose trend detected. Consider reviewing recent carb intake.")
            risk_score += 1
        elif recent_trend < -50:
            risk_factors.append("Downward glucose trend detected. Monitor for potential hypoglycemia.")
            risk_score += 1

    if risk_score >= 5:
        risk_level = "high"
    elif risk_score >= 2:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "statistics": {
            "average_mg_dl": round(avg, 1),
            "min_mg_dl": min(values),
            "max_mg_dl": max(values),
            "variability_mg_dl": variability,
            "readings_above_180": len(high_readings),
            "readings_below_70": len(low_readings),
            "time_in_range_percent": round(
                len([v for v in values if 70 <= v <= 180]) / len(values) * 100, 1
            ),
        },
        "risk_factors": risk_factors,
    }


def predict_risks(
    meals: list[dict] = None,
    exercise: dict = None,
    glucose_readings: list[dict] = None,
    medication: str = None,
    last_meal_time: str = None,
) -> dict[str, Any]:
    """
    Analyze current patterns to predict near-term diabetes risks.

    Args:
        meals: List of meals with time and name keys
        exercise: Dict with intensity, duration_minutes, time keys
        glucose_readings: List of dicts with value and time keys
        medication: Current diabetes medication name
        last_meal_time: Time of last meal (HH:MM format)

    Returns:
        Risk assessment with actionable prevention strategies.
    """
    risks = []
    overall_risk_score = 0

    # Assess meal gap risk
    meal_risk = _calculate_meal_gap_risk(meals or [])
    risks.append({"category": "meal_timing", **meal_risk})
    if meal_risk["risk_level"] == "high":
        overall_risk_score += 3
    elif meal_risk["risk_level"] == "moderate":
        overall_risk_score += 1

    # Assess exercise risk
    exercise_risk = _calculate_exercise_risk(exercise, last_meal_time, medication)
    risks.append({"category": "exercise", **exercise_risk})
    if exercise_risk["risk_level"] == "high":
        overall_risk_score += 3
    elif exercise_risk["risk_level"] == "moderate":
        overall_risk_score += 1

    # Assess glucose trend risk
    glucose_risk = _calculate_glucose_trend_risk(glucose_readings or [])
    risks.append({"category": "glucose_trends", **glucose_risk})
    if glucose_risk["risk_level"] == "high":
        overall_risk_score += 4
    elif glucose_risk["risk_level"] == "moderate":
        overall_risk_score += 2

    # Overall assessment
    if overall_risk_score >= 6:
        overall_level = "high"
        overall_message = (
            "⚠️ Multiple high-risk factors identified. Please review with your healthcare team soon. "
            "In the meantime, monitor glucose more frequently and keep fast-acting carbs accessible."
        )
    elif overall_risk_score >= 3:
        overall_level = "moderate"
        overall_message = (
            "Some risk factors detected. With small adjustments to timing and portions, "
            "you can reduce your near-term risk significantly."
        )
    else:
        overall_level = "low"
        overall_message = (
            "Your current patterns look stable. Keep maintaining regular meal timing, "
            "consistent activity, and monitoring. You're doing well! 💪"
        )

    # Immediate action items based on highest risks
    action_items = []
    if meal_risk["risk_level"] in ["high", "moderate"]:
        action_items.append("Set a reminder to eat a protein-rich snack within the next 2 hours.")
    if exercise_risk["risk_level"] in ["high", "moderate"]:
        action_items.append("Check blood glucose before your next workout. Target: 90-250 mg/dL.")
    if glucose_risk["risk_level"] in ["high", "moderate"]:
        action_items.append("Test blood glucose now and log the result. Contact your provider if >300 or <54 mg/dL.")

    return {
        "status": "success",
        "overall_risk": {
            "level": overall_level,
            "score": overall_risk_score,
            "message": overall_message,
        },
        "risk_breakdown": risks,
        "immediate_actions": action_items,
        "when_to_seek_help": [
            "Blood glucose >300 mg/dL with nausea/vomiting (possible DKA)",
            "Blood glucose <54 mg/dL or unable to treat low on your own",
            "Recurrent unexplained lows (3+ in a week)",
            "Symptoms of severe dehydration or confusion",
        ],
    }
