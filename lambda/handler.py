"""
AWS Lambda Handler for Bedrock Agent Action Group.
Routes requests from the Bedrock Agent to the appropriate tool function.
"""

import json
import logging
import traceback
from tools.meal_analyzer import analyze_meal
from tools.lab_interpreter import interpret_labs
from tools.risk_predictor import predict_risks
from tools.plan_generator import generate_plan

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _extract_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock Agent event format."""
    parameters = {}

    # Handle parameters array from Bedrock Agent
    params_list = (
        event.get("parameters", []) or
        event.get("requestBody", {}).get("content", {}).get("application/json", {}).get("properties", [])
    )

    if isinstance(params_list, list):
        for param in params_list:
            name = param.get("name", "")
            value = param.get("value", "")
            # Try to parse JSON values
            try:
                parameters[name] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                parameters[name] = value

    return parameters


def _build_response(action_group: str, api_path: str, http_method: str,
                    status_code: int, body: dict) -> dict:
    """Build a properly formatted Bedrock Agent response."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            }
        }
    }


def _validate_required_fields(params: dict, required: list[str]) -> str | None:
    """Validate required fields are present. Returns error message or None."""
    missing = [f for f in required if f not in params or params[f] is None]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    return None


def handler(event, context):
    """
    Main Lambda handler for Bedrock Agent Action Group.

    Processes incoming requests from the Bedrock Agent and routes them
    to the appropriate tool function.
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")

    try:
        # Extract request details
        action_group = event.get("actionGroup", "")
        api_path = event.get("apiPath", "")
        http_method = event.get("httpMethod", "POST")
        parameters = _extract_parameters(event)

        logger.info(f"Action: {action_group}, Path: {api_path}, Params: {json.dumps(parameters, default=str)}")

        # Route to appropriate tool
        if api_path == "/meal-analyzer" or api_path == "/meal_analyzer":
            # Validate input
            food_items = parameters.get("food_items", [])
            if not food_items:
                return _build_response(action_group, api_path, http_method, 400, {
                    "error": "food_items is required and must be a non-empty list",
                    "example": [{"name": "white rice", "serving_grams": 150}]
                })

            # Validate each food item
            for item in food_items:
                if not isinstance(item, dict) or "name" not in item:
                    return _build_response(action_group, api_path, http_method, 400, {
                        "error": "Each food item must have a 'name' field",
                        "example": {"name": "white rice", "serving_grams": 150}
                    })
                # Default serving size
                if "serving_grams" not in item:
                    item["serving_grams"] = 100

            result = analyze_meal(food_items)
            return _build_response(action_group, api_path, http_method, 200, result)

        elif api_path == "/lab-interpreter" or api_path == "/lab_interpreter":
            lab_results = parameters.get("lab_results", [])
            patient_sex = parameters.get("patient_sex", "unknown")

            if not lab_results:
                return _build_response(action_group, api_path, http_method, 400, {
                    "error": "lab_results is required and must be a non-empty list",
                    "example": [{"metric": "hba1c", "value": 7.2}]
                })

            for lab in lab_results:
                if not isinstance(lab, dict) or "metric" not in lab or "value" not in lab:
                    return _build_response(action_group, api_path, http_method, 400, {
                        "error": "Each lab result must have 'metric' and 'value' fields",
                        "valid_metrics": list(["hba1c", "fasting_glucose", "post_meal_glucose",
                                               "total_cholesterol", "ldl_cholesterol",
                                               "hdl_cholesterol", "triglycerides",
                                               "creatinine", "egfr",
                                               "urine_albumin_creatinine_ratio"])
                    })

            result = interpret_labs(lab_results, patient_sex)
            return _build_response(action_group, api_path, http_method, 200, result)

        elif api_path == "/risk-predictor" or api_path == "/risk_predictor":
            meals = parameters.get("meals", [])
            exercise = parameters.get("exercise", None)
            glucose_readings = parameters.get("glucose_readings", [])
            medication = parameters.get("medication", None)
            last_meal_time = parameters.get("last_meal_time", None)

            # At least one input is needed
            if not meals and not exercise and not glucose_readings:
                return _build_response(action_group, api_path, http_method, 400, {
                    "error": "At least one of meals, exercise, or glucose_readings is required",
                    "example": {
                        "meals": [{"name": "breakfast", "time": "07:00"}, {"name": "lunch", "time": "13:00"}],
                        "exercise": {"intensity": "moderate", "duration_minutes": 30, "time": "17:00"},
                        "glucose_readings": [{"value": 150, "time": "07:00"}, {"value": 180, "time": "10:00"}]
                    }
                })

            result = predict_risks(
                meals=meals,
                exercise=exercise,
                glucose_readings=glucose_readings,
                medication=medication,
                last_meal_time=last_meal_time,
            )
            return _build_response(action_group, api_path, http_method, 200, result)

        elif api_path == "/plan-generator" or api_path == "/plan_generator":
            meal_analysis = parameters.get("meal_analysis", None)
            lab_data = parameters.get("lab_data", None)
            risk_data = parameters.get("risk_data", None)
            patient_info = parameters.get("patient_info", {})

            result = generate_plan(
                meal_analysis=meal_analysis,
                lab_data=lab_data,
                risk_data=risk_data,
                patient_info=patient_info,
            )
            return _build_response(action_group, api_path, http_method, 200, result)

        else:
            logger.warning(f"Unknown API path: {api_path}")
            return _build_response(action_group, api_path, http_method, 404, {
                "error": f"Unknown action: {api_path}",
                "available_actions": [
                    "/meal-analyzer",
                    "/lab-interpreter",
                    "/risk-predictor",
                    "/plan-generator",
                ]
            })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return _build_response(
            event.get("actionGroup", ""),
            event.get("apiPath", ""),
            event.get("httpMethod", "POST"),
            500,
            {"error": "Internal server error", "message": str(e)}
        )
