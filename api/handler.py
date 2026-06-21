"""
API Gateway Lambda Handler.
Proxies chat requests from the frontend to the Bedrock Agent.
"""

import json
import logging
import os
import uuid
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
AGENT_ID = os.environ.get("BEDROCK_AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "")
REGION = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "ap-southeast-1"))

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)


def _cors_headers() -> dict:
    """Return CORS headers for all responses."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Session-Id",
        "Access-Control-Allow-Methods": "POST,GET,OPTIONS",
        "Content-Type": "application/json",
    }


def _error_response(status_code: int, message: str) -> dict:
    """Build an error response."""
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps({"error": message}),
    }


PROFILE_TABLE = "diabetes-care-profiles"
HEALTH_LOGS_TABLE = "diabetes-care-health-logs"
REFERRALS_TABLE = "diabetes-care-referrals"
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:823164611866:diabetes-care-reminders"


def _list_patients() -> dict:
    """List all patient profiles."""
    from decimal import Decimal
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(PROFILE_TABLE)
    response = table.scan()
    patients = []
    for item in response.get("Items", []):
        # Only include patients (not doctors)
        role = item.get("_role", "patient")
        if role == "expert":
            continue
        clean = {k: (int(v) if isinstance(v, Decimal) and v == int(v) else float(v) if isinstance(v, Decimal) else v) for k, v in item.items() if not k.startswith("_")}
        patients.append(clean)
    return {"patients": patients}


def _list_doctors() -> dict:
    """List all doctor/expert profiles."""
    from decimal import Decimal
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(PROFILE_TABLE)
    response = table.scan()
    doctors = []
    for item in response.get("Items", []):
        if item.get("_role") == "expert":
            clean = {}
            for k, v in item.items():
                if isinstance(v, Decimal):
                    clean[k] = int(v) if v == int(v) else float(v)
                elif isinstance(v, bool):
                    clean[k] = v
                else:
                    clean[k] = v
            doctors.append(clean)
    return {"doctors": doctors}


def _save_referral(data: dict) -> dict:
    """Save a patient referral to a doctor."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(REFERRALS_TABLE)
    import time
    item = {
        "doctorEmail": data.get("doctorEmail", ""),
        "timestamp": int(data.get("timestamp", time.time() * 1000)),
        "patientEmail": data.get("patientEmail", ""),
        "patientName": data.get("patientName", ""),
        "message": data.get("message", ""),
        "insights": data.get("insights", ""),
        "type": "referral",
    }
    # Remove empty strings
    item = {k: v for k, v in item.items() if v is not None and v != ""}
    table.put_item(Item=item)
    return {"status": "sent"}


def _get_referrals(doctor_email: str) -> dict:
    """Get referrals for a doctor."""
    from decimal import Decimal
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(REFERRALS_TABLE)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("doctorEmail").eq(doctor_email)
    )
    referrals = []
    for item in response.get("Items", []):
        clean = {k: (int(v) if isinstance(v, Decimal) and v == int(v) else float(v) if isinstance(v, Decimal) else v) for k, v in item.items()}
        if clean.get("type") == "referral":
            referrals.append(clean)
    return {"referrals": referrals}


def _save_doctor_report(data: dict) -> dict:
    """Doctor sends a report to a patient."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(REFERRALS_TABLE)
    import time
    item = {
        "doctorEmail": data.get("patientEmail", ""),  # Keyed by patient for easy lookup
        "timestamp": int(data.get("timestamp", time.time() * 1000)),
        "notes": data.get("notes", ""),
        "fromDoctor": data.get("doctorEmail", ""),
        "type": "doctor_report",
    }
    item = {k: v for k, v in item.items() if v is not None and v != ""}
    table.put_item(Item=item)
    return {"status": "sent"}


def _get_doctor_reports(patient_email: str) -> dict:
    """Get doctor reports sent to a patient."""
    from decimal import Decimal
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(REFERRALS_TABLE)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("doctorEmail").eq(patient_email)
    )
    reports = []
    for item in response.get("Items", []):
        clean = {k: (int(v) if isinstance(v, Decimal) and v == int(v) else float(v) if isinstance(v, Decimal) else v) for k, v in item.items()}
        if clean.get("type") == "doctor_report":
            reports.append(clean)
    return {"reports": reports}


def _save_health_log(data: dict) -> dict:
    """Save a health metric log entry."""
    from decimal import Decimal
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(HEALTH_LOGS_TABLE)
    import time
    item = {
        "email": data.get("email", ""),
        "timestamp": int(data.get("timestamp", time.time())),
    }
    # Add any numeric health metrics (use Decimal for DynamoDB)
    for key in ["hba1c", "fasting_glucose", "glucose", "ldl", "hdl", "triglycerides", "total_cholesterol", "creatinine", "egfr", "weight", "systolic", "diastolic"]:
        if key in data and data[key] is not None:
            try:
                item[key] = Decimal(str(data[key]))
            except Exception:
                pass
    table.put_item(Item=item)
    return {"status": "logged"}


def _get_health_logs(email: str) -> dict:
    """Get health logs for a patient (last 30 days)."""
    from decimal import Decimal
    import time
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(HEALTH_LOGS_TABLE)
    thirty_days_ago = int(time.time()) - (30 * 86400)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("email").eq(email) & boto3.dynamodb.conditions.Key("timestamp").gte(thirty_days_ago)
    )
    logs = []
    for item in response.get("Items", []):
        clean = {k: (int(v) if isinstance(v, Decimal) and v == int(v) else float(v) if isinstance(v, Decimal) else v) for k, v in item.items()}
        logs.append(clean)
    return {"logs": logs}


def _synthesize_speech(text: str) -> dict:
    """Convert text to speech using Amazon Polly."""
    import base64
    polly = boto3.client("polly", region_name=REGION)
    try:
        # Truncate text to Polly limit (3000 chars)
        clean_text = text[:3000].replace("**", "").replace("##", "").replace("*", "")
        response = polly.synthesize_speech(
            Text=clean_text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            Engine="neural"
        )
        audio_stream = response["AudioStream"].read()
        audio_base64 = base64.b64encode(audio_stream).decode("utf-8")
        return {"status": "success", "audio": audio_base64, "format": "mp3"}
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"Polly error: {error_msg}")
        return {"error": f"Polly failed: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def _detect_medical_entities(text: str) -> dict:
    """Extract medical entities using Amazon Comprehend Medical."""
    comprehend = boto3.client("comprehendmedical", region_name=REGION)
    try:
        response = comprehend.detect_entities_v2(Text=text)
        entities = []
        for entity in response.get("Entities", []):
            entities.append({
                "text": entity.get("Text", ""),
                "category": entity.get("Category", ""),
                "type": entity.get("Type", ""),
                "score": round(entity.get("Score", 0), 3),
                "traits": [t.get("Name", "") for t in entity.get("Traits", [])],
            })
        # Group by category
        grouped = {}
        for e in entities:
            cat = e["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(e)
        return {"status": "success", "entities": entities, "grouped": grouped, "entity_count": len(entities)}
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"Comprehend Medical error: {error_msg}")
        return {"error": f"Comprehend Medical failed: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def _send_sms(phone: str, message: str) -> dict:
    """Send an SMS via SNS."""
    sns = boto3.client("sns", region_name=REGION)
    try:
        response = sns.publish(
            PhoneNumber=phone,
            Message=message,
            MessageAttributes={
                "AWS.SNS.SMS.SenderID": {"DataType": "String", "StringValue": "DiabetesAI"},
                "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": "Transactional"},
            }
        )
        return {"status": "sent", "messageId": response.get("MessageId", "")}
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"SNS error: {error_msg}")
        return {"error": f"SMS failed: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def _extract_text_textract(image_base64: str) -> dict:
    """Extract text from an image using Amazon Textract."""
    import base64
    textract = boto3.client("textract", region_name=REGION)
    try:
        image_bytes = base64.b64decode(image_base64)
        response = textract.detect_document_text(
            Document={"Bytes": image_bytes}
        )
        # Extract all text blocks
        lines = []
        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                lines.append(block["Text"])

        full_text = "\n".join(lines)
        return {"status": "success", "text": full_text, "line_count": len(lines)}
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"Textract error: {error_msg}")
        return {"error": f"Textract failed: {error_msg}"}
    except Exception as e:
        return {"error": str(e)}


def _save_profile(email: str, profile_data: dict) -> dict:
    """Save/update a user profile in DynamoDB. Uses update to preserve existing fields."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(PROFILE_TABLE)
    import time

    # Build update expression dynamically — only update fields that are provided
    update_parts = []
    expr_values = {}
    expr_names = {}
    
    for key, value in profile_data.items():
        if key == "email":
            continue
        # Skip None and empty strings (but keep booleans and 0)
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
            
        # Handle reserved words and special chars in key names
        safe_key = f"#k_{key.replace('-','_').replace('.','_')}"
        val_key = f":v_{key.replace('-','_').replace('.','_')}"
        expr_names[safe_key] = key
        expr_values[val_key] = value
        update_parts.append(f"{safe_key} = {val_key}")

    # Always update timestamp
    expr_names["#ts"] = "updated_at"
    expr_values[":ts"] = int(time.time())
    update_parts.append("#ts = :ts")

    if not update_parts:
        return {"status": "no_changes", "email": email}

    update_expr = "SET " + ", ".join(update_parts)

    table.update_item(
        Key={"email": email},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return {"status": "saved", "email": email}


def _load_profile(email: str) -> dict:
    """Load a user profile from DynamoDB."""
    from decimal import Decimal
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(PROFILE_TABLE)
    response = table.get_item(Key={"email": email})
    item = response.get("Item")
    if item:
        # Convert Decimal to int/float for JSON serialization
        clean = {}
        for k, val in item.items():
            if isinstance(val, Decimal):
                clean[k] = int(val) if val == int(val) else float(val)
            else:
                clean[k] = val
        return {"status": "found", "profile": clean}
    return {"status": "not_found", "profile": None}


def _delete_profile(email: str) -> dict:
    """Delete a user profile from DynamoDB."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(PROFILE_TABLE)
    table.delete_item(Key={"email": email})
    return {"status": "deleted", "email": email}


def _send_email_report(to_email: str, name: str, analysis: str, profile: dict) -> dict:
    """Send analysis report via SES."""
    ses = boto3.client("ses", region_name=REGION)

    profile_summary = ""
    if profile:
        profile_summary = f"""
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
            <tr><td style="padding:4px 8px;color:#666;">Diabetes Type:</td><td style="padding:4px 8px;font-weight:bold;">{profile.get('diabetesType', 'N/A')}</td></tr>
            <tr><td style="padding:4px 8px;color:#666;">Age:</td><td style="padding:4px 8px;font-weight:bold;">{profile.get('age', 'N/A')}</td></tr>
            <tr><td style="padding:4px 8px;color:#666;">HbA1c:</td><td style="padding:4px 8px;font-weight:bold;">{profile.get('hba1c', 'N/A')}%</td></tr>
            <tr><td style="padding:4px 8px;color:#666;">Weight:</td><td style="padding:4px 8px;font-weight:bold;">{profile.get('weight', 'N/A')}</td></tr>
            <tr><td style="padding:4px 8px;color:#666;">Medications:</td><td style="padding:4px 8px;font-weight:bold;">{profile.get('medications', 'N/A')}</td></tr>
            <tr><td style="padding:4px 8px;color:#666;">Goal HbA1c:</td><td style="padding:4px 8px;font-weight:bold;">{profile.get('goalHba1c', 'N/A')}%</td></tr>
        </table>
        """

    analysis_html = analysis.replace("\n", "<br>")

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #16a34a, #0d9488); padding: 24px; border-radius: 16px; color: white; margin-bottom: 24px;">
            <h1 style="margin:0; font-size: 22px;">DiabetesControl AI Expert</h1>
            <p style="margin: 8px 0 0; opacity: 0.9; font-size: 14px;">Your Progress Insight Report</p>
        </div>
        <p style="color: #374151; font-size: 14px;">Hi {name},</p>
        <p style="color: #374151; font-size: 14px;">Here is your latest diabetes analysis:</p>
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin: 16px 0;">
            <h3 style="margin: 0 0 8px; color: #111827; font-size: 14px;">Your Profile Summary</h3>
            {profile_summary}
        </div>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; margin: 16px 0;">
            <h3 style="margin: 0 0 12px; color: #166534; font-size: 14px;">AI Analysis</h3>
            <div style="color: #374151; font-size: 13px; line-height: 1.7;">{analysis_html}</div>
        </div>
        <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 16px; margin: 16px 0;">
            <p style="margin: 0; color: #92400e; font-size: 12px;">
                Disclaimer: This report is AI-generated for educational purposes only. Always consult your healthcare provider.
            </p>
        </div>
        <p style="color: #9ca3af; font-size: 11px; margin-top: 24px;">Generated by DiabetesControl AI Expert - Powered by Amazon Bedrock</p>
    </body>
    </html>
    """

    try:
        ses.send_email(
            Source=f"DiabetesControl AI <ESSALEM.SIDI.MOHAMED@student.mmu.edu.my>",
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": f"Your Diabetes Progress Report - {name}", "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                    "Text": {"Data": f"DiabetesControl AI Report for {name}\n\n{analysis}", "Charset": "UTF-8"},
                }
            }
        )
        return {"status": "sent", "message": f"Report sent to {to_email}"}
    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"SES error: {error_msg}")
        if "not verified" in error_msg.lower() or "not authorized" in error_msg.lower():
            return {"error": "Email not configured. Verify sender email in Amazon SES."}
        return {"error": f"Email failed: {error_msg}"}
    except Exception as e:
        logger.error(f"Email error: {str(e)}")
        return {"error": str(e)}


def _analyze_lab_with_vision(image_base64: str, media_type: str, profile_context: str, typed_values: str) -> dict:
    """Analyze a lab result image using Claude Haiku's vision via the Converse API."""
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)

    system_prompt = """You are a clinical lab interpreter for diabetes patients. 
You will be shown a lab result document (image or text). Your job is to:
1. Extract ALL numeric lab values visible in the image
2. For each value, compare against ADA clinical guidelines
3. Flag abnormal results clearly
4. Provide a plain-language summary

Be ACCURATE — only report values you can actually read from the image. If a value is unclear, say so.
Never invent or guess values. Only interpret what is clearly visible."""

    # Build the message content
    content = []

    # Add image if provided
    if image_base64:
        import base64
        content.append({
            "image": {
                "format": media_type.split("/")[-1] if "/" in media_type else "jpeg",
                "source": {"bytes": base64.b64decode(image_base64)}
            }
        })

    # Build the text prompt
    text_prompt = "Analyze this lab result"
    if profile_context:
        text_prompt += f"\n\nPatient context: {profile_context}"
    if typed_values:
        text_prompt += f"\n\nAdditional typed values: {typed_values}"

    text_prompt += """

Please provide your analysis in this format:

## 📋 Extracted Lab Values
(List each value you can read from the image with its unit)

## 🔍 Interpretation
For each value:
- Value | Normal Range | Status (✅ Normal / ⚠️ Borderline / 🔴 High Risk)
- Brief explanation

## 📊 Overall Assessment
(2-3 sentence summary of overall metabolic health)

## ⚡ Priority Actions
(Top 3 recommendations based on concerning results)

## 📅 Follow-Up
(When to retest and what to discuss with doctor)"""

    content.append({"text": text_prompt})

    try:
        response = bedrock_runtime.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": content}],
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 2000, "temperature": 0.3}
        )

        # Extract the response text
        output_message = response.get("output", {}).get("message", {})
        response_text = ""
        for block in output_message.get("content", []):
            if "text" in block:
                response_text += block["text"]

        return {"response": response_text}

    except ClientError as e:
        error_msg = e.response["Error"]["Message"]
        logger.error(f"Bedrock vision error: {error_msg}")
        return {"error": f"Vision analysis failed: {error_msg}"}
    except Exception as e:
        logger.error(f"Vision error: {str(e)}")
        return {"error": str(e)}


def _invoke_agent(user_message: str, session_id: str) -> dict:
    """Invoke the Bedrock Agent and collect the response."""
    if not AGENT_ID or not AGENT_ALIAS_ID:
        return {
            "error": "Agent not configured. Set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID environment variables."
        }

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=user_message,
        )

        # Collect streaming response
        completion = ""
        tool_outputs = []

        for event in response.get("completion", []):
            if "chunk" in event:
                chunk_data = event["chunk"]
                if "bytes" in chunk_data:
                    completion += chunk_data["bytes"].decode("utf-8")
            elif "trace" in event:
                # Extract tool use information from traces
                trace = event["trace"].get("trace", {})
                orchestration_trace = trace.get("orchestrationTrace", {})
                if "observation" in orchestration_trace:
                    obs = orchestration_trace["observation"]
                    if "actionGroupInvocationOutput" in obs:
                        action_output = obs["actionGroupInvocationOutput"]
                        tool_outputs.append({
                            "tool": action_output.get("actionGroupName", "unknown"),
                            "output": action_output.get("text", ""),
                        })

        return {
            "response": completion,
            "session_id": session_id,
            "tool_outputs": tool_outputs,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"Bedrock Agent error: {error_code} - {error_message}")
        return {"error": f"Agent error: {error_message}"}
    except Exception as e:
        logger.error(f"Unexpected error invoking agent: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


def handler(event, context):
    """
    API Gateway Lambda handler.
    
    Endpoints:
    - POST /chat: Send a message to the Bedrock Agent
    - GET /session: Generate a new session ID
    - OPTIONS /*: CORS preflight
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")

    http_method = event.get("httpMethod", "")
    path = event.get("path", "")

    # Handle CORS preflight
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": "",
        }

    # GET /session - Generate new session ID
    if http_method == "GET" and "/session" in path:
        session_id = str(uuid.uuid4())
        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps({"session_id": session_id}),
        }

    # POST /email-report - Send analysis report via SES
    if http_method == "POST" and "/email-report" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")

        email = body.get("email", "").strip()
        name = body.get("name", "User")
        analysis = body.get("analysis", "")

        if not email:
            return _error_response(400, "Email is required")
        if not analysis:
            return _error_response(400, "No analysis to send")

        result = _send_email_report(email, name, analysis, body.get("profile", {}))
        if "error" in result:
            return _error_response(500, result["error"])

        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(result),
        }

    # GET /patients - List all patient profiles (for doctor dashboard)
    if http_method == "GET" and "/patients" in path:
        result = _list_patients()
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # GET /doctors - List all expert/doctor profiles
    if http_method == "GET" and "/doctors" in path:
        result = _list_doctors()
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /referral - Patient sends data to doctor
    if http_method == "POST" and "/referral" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        result = _save_referral(body)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # GET /referrals - Doctor gets their referrals
    if http_method == "GET" and "/referrals" in path:
        params = event.get("queryStringParameters") or {}
        email = params.get("email", "").strip()
        if not email:
            return _error_response(400, "Email required")
        result = _get_referrals(email)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /doctor-report - Doctor sends report to patient
    if http_method == "POST" and "/doctor-report" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        result = _save_doctor_report(body)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # GET /doctor-reports - Patient gets reports from doctor
    if http_method == "GET" and "/doctor-reports" in path:
        params = event.get("queryStringParameters") or {}
        email = params.get("email", "").strip()
        if not email:
            return _error_response(400, "Email required")
        result = _get_doctor_reports(email)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # GET /health-logs - Get health logs for a patient (for charts)
    if http_method == "GET" and "/health-logs" in path:
        params = event.get("queryStringParameters") or {}
        email = params.get("email", "").strip()
        if not email:
            return _error_response(400, "Email required")
        result = _get_health_logs(email)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /health-logs - Log health metrics
    if http_method == "POST" and "/health-logs" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        result = _save_health_log(body)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /polly - Convert text to speech using Amazon Polly
    if http_method == "POST" and "/polly" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        text = body.get("text", "").strip()
        if not text:
            return _error_response(400, "Text is required")
        result = _synthesize_speech(text)
        if "error" in result:
            return _error_response(500, result["error"])
        # Return audio as base64
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /comprehend-medical - Extract medical entities from text
    if http_method == "POST" and "/comprehend-medical" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        text = body.get("text", "").strip()
        if not text:
            return _error_response(400, "Text is required")
        result = _detect_medical_entities(text)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /sms-reminder - Subscribe phone and send SMS reminder via SNS
    if http_method == "POST" and "/sms-reminder" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        phone = body.get("phone", "").strip()
        message = body.get("message", "").strip()
        if not phone:
            return _error_response(400, "Phone number required (e.g., +60123456789)")
        result = _send_sms(phone, message or "DiabetesControl AI Reminder: Time to check your blood glucose! Stay on track today.")
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /textract - Extract text from lab image using Amazon Textract
    if http_method == "POST" and "/textract" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        image_base64 = body.get("image", "")
        if not image_base64:
            return _error_response(400, "Image (base64) required")
        result = _extract_text_textract(image_base64)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /profile - Save profile to DynamoDB
    if http_method == "POST" and "/profile" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")
        email = body.get("email", "").strip()
        if not email:
            return _error_response(400, "Email is required as profile key")
        result = _save_profile(email, body)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # GET /profile?email=xxx - Load profile from DynamoDB
    if http_method == "GET" and "/profile" in path:
        params = event.get("queryStringParameters") or {}
        email = params.get("email", "").strip()
        if not email:
            return _error_response(400, "Email query param required")
        result = _load_profile(email)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # DELETE /profile?email=xxx - Delete profile from DynamoDB
    if http_method == "DELETE" and "/profile" in path:
        params = event.get("queryStringParameters") or {}
        email = params.get("email", "").strip()
        if not email:
            return _error_response(400, "Email query param required")
        result = _delete_profile(email)
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result)}

    # POST /lab-vision - Analyze lab image with Claude vision (Converse API)
    if http_method == "POST" and "/lab-vision" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")

        image_base64 = body.get("image", "")
        media_type = body.get("media_type", "image/jpeg")
        profile_context = body.get("profile_context", "")
        typed_values = body.get("typed_values", "")

        if not image_base64 and not typed_values:
            return _error_response(400, "Either image or typed lab values required")

        result = _analyze_lab_with_vision(image_base64, media_type, profile_context, typed_values)
        if "error" in result:
            return _error_response(500, result["error"])

        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(result),
        }

    # POST /chat - Send message to agent
    if http_method == "POST" and "/chat" in path:
        try:
            body = json.loads(event.get("body", "{}"))
        except json.JSONDecodeError:
            return _error_response(400, "Invalid JSON body")

        user_message = body.get("message", "").strip()
        if not user_message:
            return _error_response(400, "Message is required")

        if len(user_message) > 10000:
            return _error_response(400, "Message too long (max 10000 characters)")

        # Get or create session ID
        session_id = (
            body.get("session_id") or
            event.get("headers", {}).get("X-Session-Id") or
            event.get("headers", {}).get("x-session-id") or
            str(uuid.uuid4())
        )

        # Invoke the Bedrock Agent
        result = _invoke_agent(user_message, session_id)

        if "error" in result:
            return _error_response(500, result["error"])

        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(result),
        }

    return _error_response(404, f"Not found: {http_method} {path}")
