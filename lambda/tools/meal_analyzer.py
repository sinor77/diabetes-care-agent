"""
Meal Analyzer Tool
Estimates glycemic impact, carbohydrate content, and provides alternative suggestions.
"""

import json
from typing import Any

# Glycemic Index reference database (common foods)
GI_DATABASE = {
    "white rice": {"gi": 73, "carbs_per_100g": 28, "category": "grain"},
    "brown rice": {"gi": 50, "carbs_per_100g": 23, "category": "grain"},
    "white bread": {"gi": 75, "carbs_per_100g": 49, "category": "grain"},
    "whole wheat bread": {"gi": 51, "carbs_per_100g": 41, "category": "grain"},
    "oatmeal": {"gi": 55, "carbs_per_100g": 12, "category": "grain"},
    "quinoa": {"gi": 53, "carbs_per_100g": 21, "category": "grain"},
    "pasta": {"gi": 49, "carbs_per_100g": 25, "category": "grain"},
    "potato": {"gi": 78, "carbs_per_100g": 17, "category": "vegetable"},
    "sweet potato": {"gi": 63, "carbs_per_100g": 20, "category": "vegetable"},
    "banana": {"gi": 51, "carbs_per_100g": 23, "category": "fruit"},
    "apple": {"gi": 36, "carbs_per_100g": 14, "category": "fruit"},
    "orange": {"gi": 43, "carbs_per_100g": 12, "category": "fruit"},
    "watermelon": {"gi": 76, "carbs_per_100g": 8, "category": "fruit"},
    "grapes": {"gi": 59, "carbs_per_100g": 18, "category": "fruit"},
    "berries": {"gi": 25, "carbs_per_100g": 10, "category": "fruit"},
    "milk": {"gi": 39, "carbs_per_100g": 5, "category": "dairy"},
    "yogurt": {"gi": 41, "carbs_per_100g": 7, "category": "dairy"},
    "cheese": {"gi": 0, "carbs_per_100g": 1, "category": "dairy"},
    "chicken": {"gi": 0, "carbs_per_100g": 0, "category": "protein"},
    "fish": {"gi": 0, "carbs_per_100g": 0, "category": "protein"},
    "eggs": {"gi": 0, "carbs_per_100g": 1, "category": "protein"},
    "lentils": {"gi": 32, "carbs_per_100g": 20, "category": "legume"},
    "beans": {"gi": 24, "carbs_per_100g": 22, "category": "legume"},
    "chickpeas": {"gi": 28, "carbs_per_100g": 27, "category": "legume"},
    "soda": {"gi": 63, "carbs_per_100g": 11, "category": "beverage"},
    "juice": {"gi": 50, "carbs_per_100g": 10, "category": "beverage"},
    "candy": {"gi": 78, "carbs_per_100g": 80, "category": "sweets"},
    "chocolate": {"gi": 40, "carbs_per_100g": 60, "category": "sweets"},
    "ice cream": {"gi": 51, "carbs_per_100g": 24, "category": "sweets"},
    "pizza": {"gi": 60, "carbs_per_100g": 33, "category": "mixed"},
    "burger": {"gi": 66, "carbs_per_100g": 24, "category": "mixed"},
    "french fries": {"gi": 75, "carbs_per_100g": 30, "category": "mixed"},
    "salad": {"gi": 10, "carbs_per_100g": 3, "category": "vegetable"},
    "broccoli": {"gi": 10, "carbs_per_100g": 7, "category": "vegetable"},
    "carrots": {"gi": 39, "carbs_per_100g": 10, "category": "vegetable"},
    "corn": {"gi": 52, "carbs_per_100g": 19, "category": "vegetable"},
    "nuts": {"gi": 15, "carbs_per_100g": 8, "category": "snack"},
    "cereal": {"gi": 72, "carbs_per_100g": 75, "category": "grain"},
    "pancakes": {"gi": 67, "carbs_per_100g": 35, "category": "grain"},
    "tortilla": {"gi": 52, "carbs_per_100g": 48, "category": "grain"},
}

# Healthier alternatives mapping
ALTERNATIVES = {
    "grain": {
        "high_gi": ["quinoa", "steel-cut oats", "barley", "cauliflower rice"],
        "tip": "Pair grains with protein and healthy fats to lower glycemic response.",
    },
    "fruit": {
        "high_gi": ["berries", "green apple", "grapefruit", "pear"],
        "tip": "Choose whole fruits over juices; fiber slows sugar absorption.",
    },
    "vegetable": {
        "high_gi": ["leafy greens", "zucchini", "cauliflower", "bell peppers"],
        "tip": "Non-starchy vegetables have minimal glycemic impact.",
    },
    "beverage": {
        "high_gi": ["water with lemon", "unsweetened tea", "sparkling water"],
        "tip": "Liquid sugars spike blood glucose fastest. Choose zero-calorie options.",
    },
    "sweets": {
        "high_gi": ["dark chocolate (70%+)", "berries with whipped cream", "sugar-free gelatin"],
        "tip": "If craving sweets, have a small portion after a protein-rich meal.",
    },
    "mixed": {
        "high_gi": ["grilled chicken salad", "lettuce-wrapped burger", "baked sweet potato fries"],
        "tip": "Build meals around protein + non-starchy vegetables + healthy fat.",
    },
    "snack": {
        "high_gi": ["almonds", "walnuts", "celery with peanut butter"],
        "tip": "Nuts provide healthy fats and protein with minimal glycemic impact.",
    },
}


def _find_food_match(food_item: str) -> dict | None:
    """Fuzzy match a food item against the database."""
    food_lower = food_item.lower().strip()
    # Direct match
    if food_lower in GI_DATABASE:
        return GI_DATABASE[food_lower]
    # Partial match
    for key, value in GI_DATABASE.items():
        if key in food_lower or food_lower in key:
            return value
    return None


def _classify_gi(gi_value: int) -> str:
    """Classify glycemic index value."""
    if gi_value <= 55:
        return "low"
    elif gi_value <= 69:
        return "medium"
    else:
        return "high"


def _estimate_glycemic_load(gi: int, carbs_g: float, serving_g: float) -> float:
    """Calculate glycemic load: GL = (GI × available carbs per serving) / 100."""
    available_carbs = (carbs_g / 100) * serving_g
    return round((gi * available_carbs) / 100, 1)


def analyze_meal(food_items: list[dict]) -> dict[str, Any]:
    """
    Analyze a meal for glycemic impact.

    Args:
        food_items: List of dicts with keys: name (str), serving_grams (float)

    Returns:
        Analysis including glycemic impact, carbs, and alternatives.
    """
    if not food_items:
        return {"error": "No food items provided", "status": "invalid_input"}

    analysis_results = []
    total_carbs = 0.0
    total_glycemic_load = 0.0
    high_gi_items = []

    for item in food_items:
        name = item.get("name", "unknown")
        serving_g = item.get("serving_grams", 100)

        match = _find_food_match(name)

        if match:
            gi = match["gi"]
            carbs_per_100g = match["carbs_per_100g"]
            category = match["category"]
            carbs_in_serving = round((carbs_per_100g / 100) * serving_g, 1)
            gl = _estimate_glycemic_load(gi, carbs_per_100g, serving_g)
            gi_class = _classify_gi(gi)

            total_carbs += carbs_in_serving
            total_glycemic_load += gl

            item_analysis = {
                "food": name,
                "serving_grams": serving_g,
                "glycemic_index": gi,
                "gi_classification": gi_class,
                "carbohydrates_grams": carbs_in_serving,
                "glycemic_load": gl,
                "category": category,
            }
            analysis_results.append(item_analysis)

            if gi_class == "high":
                high_gi_items.append({"food": name, "category": category})
        else:
            analysis_results.append({
                "food": name,
                "serving_grams": serving_g,
                "note": "Food not found in database. Estimate based on similar foods.",
                "glycemic_index": 50,
                "gi_classification": "medium",
                "carbohydrates_grams": round(serving_g * 0.2, 1),
                "glycemic_load": round(50 * (serving_g * 0.2 / 100), 1),
                "category": "unknown",
            })
            total_carbs += round(serving_g * 0.2, 1)
            total_glycemic_load += round(50 * (serving_g * 0.2 / 100), 1)

    # Generate alternatives for high-GI items
    alternatives = []
    for high_item in high_gi_items:
        cat = high_item["category"]
        if cat in ALTERNATIVES:
            alternatives.append({
                "instead_of": high_item["food"],
                "try": ALTERNATIVES[cat]["high_gi"],
                "tip": ALTERNATIVES[cat]["tip"],
            })

    # Overall meal assessment
    if total_glycemic_load <= 10:
        meal_impact = "low"
        meal_advice = "This meal has a low glycemic impact. Great choice for blood sugar stability!"
    elif total_glycemic_load <= 20:
        meal_impact = "moderate"
        meal_advice = "Moderate glycemic impact. Consider adding more fiber or protein to slow absorption."
    else:
        meal_impact = "high"
        meal_advice = "High glycemic impact. Consider swapping high-GI items or reducing portion sizes."

    return {
        "status": "success",
        "meal_summary": {
            "total_carbohydrates_grams": round(total_carbs, 1),
            "total_glycemic_load": round(total_glycemic_load, 1),
            "overall_impact": meal_impact,
            "advice": meal_advice,
            "item_count": len(analysis_results),
        },
        "food_analysis": analysis_results,
        "alternatives": alternatives,
        "general_tips": [
            "Eat protein or healthy fat before carbs to reduce glucose spikes.",
            "A 10-15 minute walk after eating can lower post-meal glucose by 20-30%.",
            "Vinegar-based dressings may help reduce glycemic response.",
            "Chew slowly — it takes 20 minutes for satiety signals to reach the brain.",
        ],
    }
