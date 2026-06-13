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
REGION = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))

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
