"""
Lab Interpreter Tool
Parses key metabolic lab results and highlights out-of-range values against ADA clinical guidelines.
"""

from typing import Any

# ADA Clinical Guidelines Reference Ranges
REFERENCE_RANGES = {
    "hba1c": {
        "unit": "%",
        "ranges": {
            "normal": {"min": 0, "max": 5.6, "label": "Normal (no diabetes)"},
            "prediabetes": {"min": 5.7, "max": 6.4, "label": "Prediabetes"},
            "diabetes": {"min": 6.5, "max": 100, "label": "Diabetes"},
        },
        "target_with_diabetes": {"min": 0, "max": 7.0, "label": "ADA target for most adults with diabetes"},
        "description": "Glycated Hemoglobin — reflects average blood glucose over 2-3 months",
    },
    "fasting_glucose": {
        "unit": "mg/dL",
        "ranges": {
            "normal": {"min": 70, "max": 99, "label": "Normal"},
            "prediabetes": {"min": 100, "max": 125, "label": "Prediabetes (impaired fasting glucose)"},
            "diabetes": {"min": 126, "max": 600, "label": "Diabetes"},
            "hypoglycemia": {"min": 0, "max": 69, "label": "Hypoglycemia — seek immediate attention if symptomatic"},
        },
        "target_with_diabetes": {"min": 80, "max": 130, "label": "ADA pre-meal target for diabetes"},
        "description": "Blood glucose after 8+ hours of fasting",
    },
    "post_meal_glucose": {
        "unit": "mg/dL",
        "ranges": {
            "normal": {"min": 0, "max": 139, "label": "Normal (2hr post-meal)"},
            "prediabetes": {"min": 140, "max": 199, "label": "Impaired glucose tolerance"},
            "diabetes": {"min": 200, "max": 600, "label": "Diabetes"},
        },
        "target_with_diabetes": {"min": 0, "max": 180, "label": "ADA post-meal target (<180 mg/dL 1-2hr after eating)"},
        "description": "Blood glucose 1-2 hours after eating",
    },
    "total_cholesterol": {
        "unit": "mg/dL",
        "ranges": {
            "desirable": {"min": 0, "max": 199, "label": "Desirable"},
            "borderline_high": {"min": 200, "max": 239, "label": "Borderline high"},
            "high": {"min": 240, "max": 999, "label": "High"},
        },
        "description": "Total cholesterol — important for cardiovascular risk in diabetes",
    },
    "ldl_cholesterol": {
        "unit": "mg/dL",
        "ranges": {
            "optimal": {"min": 0, "max": 99, "label": "Optimal"},
            "near_optimal": {"min": 100, "max": 129, "label": "Near optimal"},
            "borderline_high": {"min": 130, "max": 159, "label": "Borderline high"},
            "high": {"min": 160, "max": 189, "label": "High"},
            "very_high": {"min": 190, "max": 999, "label": "Very high"},
        },
        "target_with_diabetes": {"min": 0, "max": 100, "label": "ADA target: <100 mg/dL (or <70 if CVD history)"},
        "description": "LDL ('bad') cholesterol — primary lipid target for diabetes management",
    },
    "hdl_cholesterol": {
        "unit": "mg/dL",
        "ranges": {
            "low_risk_male": {"min": 40, "max": 999, "label": "Acceptable for males (>40)"},
            "low_risk_female": {"min": 50, "max": 999, "label": "Acceptable for females (>50)"},
            "low": {"min": 0, "max": 39, "label": "Low — increased cardiovascular risk"},
        },
        "description": "HDL ('good') cholesterol — higher is protective",
    },
    "triglycerides": {
        "unit": "mg/dL",
        "ranges": {
            "normal": {"min": 0, "max": 149, "label": "Normal"},
            "borderline_high": {"min": 150, "max": 199, "label": "Borderline high"},
            "high": {"min": 200, "max": 499, "label": "High"},
            "very_high": {"min": 500, "max": 9999, "label": "Very high — risk of pancreatitis"},
        },
        "target_with_diabetes": {"min": 0, "max": 150, "label": "ADA target: <150 mg/dL"},
        "description": "Triglycerides — elevated levels common with poorly controlled diabetes",
    },
    "creatinine": {
        "unit": "mg/dL",
        "ranges": {
            "normal_male": {"min": 0.74, "max": 1.35, "label": "Normal (male)"},
            "normal_female": {"min": 0.59, "max": 1.04, "label": "Normal (female)"},
        },
        "description": "Kidney function marker — diabetes can affect kidneys over time",
    },
    "egfr": {
        "unit": "mL/min/1.73m²",
        "ranges": {
            "normal": {"min": 90, "max": 999, "label": "Normal kidney function"},
            "mild_decrease": {"min": 60, "max": 89, "label": "Mildly decreased"},
            "moderate_decrease": {"min": 30, "max": 59, "label": "Moderately decreased — consult nephrologist"},
            "severe_decrease": {"min": 15, "max": 29, "label": "Severely decreased"},
            "kidney_failure": {"min": 0, "max": 14, "label": "Kidney failure"},
        },
        "description": "Estimated Glomerular Filtration Rate — kidney function assessment",
    },
    "urine_albumin_creatinine_ratio": {
        "unit": "mg/g",
        "ranges": {
            "normal": {"min": 0, "max": 29, "label": "Normal"},
            "moderately_increased": {"min": 30, "max": 299, "label": "Moderately increased (microalbuminuria)"},
            "severely_increased": {"min": 300, "max": 99999, "label": "Severely increased (macroalbuminuria)"},
        },
        "description": "Early marker of diabetic kidney disease — ADA recommends annual screening",
    },
}


def _classify_value(metric: str, value: float, sex: str = "unknown") -> dict:
    """Classify a lab value against reference ranges."""
    if metric not in REFERENCE_RANGES:
        return {"status": "unknown_metric", "message": f"Metric '{metric}' not in database"}

    ref = REFERENCE_RANGES[metric]
    result = {
        "metric": metric,
        "value": value,
        "unit": ref["unit"],
        "description": ref["description"],
        "classification": "unknown",
        "is_concerning": False,
        "urgency": "routine",
    }

    # Special handling for sex-specific ranges
    if metric == "hdl_cholesterol":
        if sex.lower() in ["male", "m"]:
            threshold = 40
        elif sex.lower() in ["female", "f"]:
            threshold = 50
        else:
            threshold = 40  # Default to male threshold
        if value < threshold:
            result["classification"] = "Low — increased cardiovascular risk"
            result["is_concerning"] = True
            result["urgency"] = "follow_up"
        else:
            result["classification"] = "Acceptable"
            result["is_concerning"] = False
        return result

    if metric == "creatinine":
        if sex.lower() in ["male", "m"]:
            range_key = "normal_male"
        else:
            range_key = "normal_female"
        r = ref["ranges"][range_key]
        if r["min"] <= value <= r["max"]:
            result["classification"] = r["label"]
            result["is_concerning"] = False
        elif value > r["max"]:
            result["classification"] = "Elevated — possible kidney concern"
            result["is_concerning"] = True
            result["urgency"] = "follow_up"
        return result

    # General classification
    for range_name, r in ref["ranges"].items():
        if r["min"] <= value <= r["max"]:
            result["classification"] = r["label"]
            # Determine if concerning
            if range_name in ["diabetes", "high", "very_high", "hypoglycemia",
                              "severe_decrease", "kidney_failure", "severely_increased"]:
                result["is_concerning"] = True
                result["urgency"] = "urgent"
            elif range_name in ["prediabetes", "borderline_high", "moderate_decrease",
                                "moderately_increased"]:
                result["is_concerning"] = True
                result["urgency"] = "follow_up"
            break

    # Add diabetes-specific target comparison if available
    if "target_with_diabetes" in ref:
        target = ref["target_with_diabetes"]
        if target["min"] <= value <= target["max"]:
            result["meets_diabetes_target"] = True
            result["target_note"] = f"✓ Within {target['label']}"
        else:
            result["meets_diabetes_target"] = False
            result["target_note"] = f"✗ Outside {target['label']}"

    return result


def interpret_labs(lab_results: list[dict], patient_sex: str = "unknown") -> dict[str, Any]:
    """
    Interpret lab results against clinical guidelines.

    Args:
        lab_results: List of dicts with keys: metric (str), value (float)
        patient_sex: "male", "female", or "unknown"

    Returns:
        Comprehensive lab interpretation with flags and recommendations.
    """
    if not lab_results:
        return {"error": "No lab results provided", "status": "invalid_input"}

    interpretations = []
    concerning_results = []
    urgent_flags = []
    positive_results = []

    for lab in lab_results:
        metric = lab.get("metric", "").lower().replace(" ", "_")
        value = lab.get("value")

        if value is None:
            interpretations.append({"metric": metric, "error": "No value provided"})
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            interpretations.append({"metric": metric, "error": f"Invalid value: {value}"})
            continue

        result = _classify_value(metric, value, patient_sex)
        interpretations.append(result)

        if result.get("urgency") == "urgent":
            urgent_flags.append(result)
        elif result.get("is_concerning"):
            concerning_results.append(result)
        elif not result.get("is_concerning") and result.get("classification") != "unknown":
            positive_results.append(result)

    # Generate summary
    summary = {
        "total_metrics_analyzed": len(interpretations),
        "urgent_flags": len(urgent_flags),
        "concerning_results": len(concerning_results),
        "within_normal": len(positive_results),
    }

    # Generate recommendations based on results
    recommendations = []
    if urgent_flags:
        recommendations.append(
            "⚠️ URGENT: Some results require immediate medical attention. "
            "Please contact your healthcare provider today."
        )
    if concerning_results:
        recommendations.append(
            "📋 Schedule a follow-up appointment to discuss concerning results with your doctor."
        )

    # Specific recommendations based on patterns
    metrics_dict = {r["metric"]: r for r in interpretations if "error" not in r}
    if "hba1c" in metrics_dict and metrics_dict["hba1c"].get("is_concerning"):
        recommendations.append(
            "Your HbA1c suggests room for improvement. Small daily changes in diet and "
            "activity can meaningfully lower this over 3 months."
        )
    if "ldl_cholesterol" in metrics_dict and metrics_dict["ldl_cholesterol"].get("is_concerning"):
        recommendations.append(
            "Elevated LDL increases cardiovascular risk, especially with diabetes. "
            "Discuss statin therapy and dietary changes with your provider."
        )
    if "triglycerides" in metrics_dict and metrics_dict["triglycerides"].get("is_concerning"):
        recommendations.append(
            "High triglycerides often improve with reduced refined carbs, regular exercise, "
            "and omega-3 fatty acids."
        )
    if "egfr" in metrics_dict and metrics_dict["egfr"].get("is_concerning"):
        recommendations.append(
            "Kidney function markers need attention. Stay well-hydrated, limit sodium, "
            "and ensure your blood pressure is well-controlled."
        )

    return {
        "status": "success",
        "summary": summary,
        "interpretations": interpretations,
        "urgent_flags": [{"metric": f["metric"], "value": f["value"],
                          "classification": f["classification"]} for f in urgent_flags],
        "concerning_results": [{"metric": c["metric"], "value": c["value"],
                                "classification": c["classification"]} for c in concerning_results],
        "positive_results": [{"metric": p["metric"], "value": p["value"],
                              "classification": p["classification"]} for p in positive_results],
        "recommendations": recommendations,
        "disclaimer": "This interpretation is for informational purposes only. "
                      "Always discuss lab results with your healthcare provider.",
    }
