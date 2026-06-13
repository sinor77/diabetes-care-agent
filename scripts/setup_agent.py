"""
Bedrock Agent Setup Script
Creates and configures the Bedrock Agent with Action Groups after SAM deployment.

Usage:
    python scripts/setup_agent.py --region ap-southeast-1

Prerequisites:
    - SAM stack deployed (provides Lambda ARN)
    - Bedrock access enabled for Claude 3 Haiku (auto-enabled in ap-southeast-1)
    - boto3 installed
"""

import argparse
import json
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError


def load_file(path: str) -> str:
    """Load a file relative to the script location."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, path)
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def get_lambda_arn(cfn_client, stack_name: str, logical_id: str) -> str:
    """Get Lambda ARN from CloudFormation stack outputs."""
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
        outputs = response["Stacks"][0].get("Outputs", [])
        for output in outputs:
            if "ToolsFunction" in output.get("OutputKey", ""):
                return output["OutputValue"]
    except ClientError:
        pass

    # Fallback: try to get directly
    lambda_client = boto3.client("lambda")
    try:
        response = lambda_client.get_function(FunctionName="diabetes-care-tools")
        return response["Configuration"]["FunctionArn"]
    except ClientError as e:
        print(f"Error: Could not find Lambda function. Deploy the SAM stack first.")
        print(f"  Run: sam build && sam deploy --guided")
        sys.exit(1)


def create_agent(bedrock_client, instruction: str, region: str) -> str:
    """Create a Bedrock Agent."""
    # Create IAM role for the agent
    iam_client = boto3.client("iam")
    role_name = "DiabetesCareAgentRole"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for DiabetesControl AI Bedrock Agent",
        )
        print(f"  ✓ Created IAM role: {role_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"  ✓ IAM role already exists: {role_name}")
        else:
            raise

    # Attach Bedrock policy
    policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
    try:
        iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    except ClientError:
        pass

    # Get role ARN
    role_response = iam_client.get_role(RoleName=role_name)
    role_arn = role_response["Role"]["Arn"]

    # Wait for role propagation
    print("  ⏳ Waiting for IAM role propagation (10s)...")
    time.sleep(10)

    # Using Claude 3 Haiku via APAC inference profile
    # This is the model confirmed to work with the account's IAM policies
    foundation_model = "anthropic.claude-3-haiku-20240307-v1:0"

    try:
        response = bedrock_client.create_agent(
            agentName="DiabetesControl-AI-Expert",
            agentResourceRoleArn=role_arn,
            description="An empathetic, evidence-based digital diabetes care assistant powered by Claude 3 Haiku.",
            foundationModel=foundation_model,
            instruction=instruction,
            idleSessionTTLInSeconds=1800,
        )
        agent_id = response["agent"]["agentId"]
        print(f"  ✓ Created agent with model: {foundation_model}")
        print(f"  ✓ Agent ID: {agent_id}")
        return agent_id
    except ClientError as e:
        if "already exists" in str(e).lower() or "ConflictException" in str(e):
            # Find existing agent
            agents = bedrock_client.list_agents()
            for agent in agents.get("agentSummaries", []):
                if agent["agentName"] == "DiabetesControl-AI-Expert":
                    agent_id = agent["agentId"]
                    print(f"  ✓ Found existing agent: {agent_id}")
                    # Update instruction
                    bedrock_client.update_agent(
                        agentId=agent_id,
                        agentName="DiabetesControl-AI-Expert",
                        agentResourceRoleArn=role_arn,
                        foundationModel=foundation_model,
                        instruction=instruction,
                    )
                    print(f"  ✓ Updated agent with model: {foundation_model}")
                    return agent_id
        raise


def create_action_group(bedrock_client, agent_id: str, lambda_arn: str, schema_content: str) -> str:
    """Create an Action Group with the OpenAPI schema."""
    try:
        response = bedrock_client.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="DiabetesCareTools",
            description="Diabetes management tools: meal analysis, lab interpretation, risk prediction, and plan generation.",
            actionGroupExecutor={"lambda": lambda_arn},
            apiSchema={"payload": schema_content},
        )
        action_group_id = response["agentActionGroup"]["actionGroupId"]
        print(f"  ✓ Created action group: {action_group_id}")
        return action_group_id
    except ClientError as e:
        if "ConflictException" in str(e):
            print(f"  ✓ Action group already exists, updating...")
            # List action groups to find existing one
            groups = bedrock_client.list_agent_action_groups(
                agentId=agent_id, agentVersion="DRAFT"
            )
            for group in groups.get("actionGroupSummaries", []):
                if group["actionGroupName"] == "DiabetesCareTools":
                    bedrock_client.update_agent_action_group(
                        agentId=agent_id,
                        agentVersion="DRAFT",
                        actionGroupId=group["actionGroupId"],
                        actionGroupName="DiabetesCareTools",
                        description="Diabetes management tools: meal analysis, lab interpretation, risk prediction, and plan generation.",
                        actionGroupExecutor={"lambda": lambda_arn},
                        apiSchema={"payload": schema_content},
                    )
                    return group["actionGroupId"]
        raise


def prepare_and_create_alias(bedrock_client, agent_id: str) -> str:
    """Prepare the agent and create an alias."""
    # Prepare agent
    print("  ⏳ Preparing agent...")
    bedrock_client.prepare_agent(agentId=agent_id)

    # Wait for preparation
    for _ in range(30):
        time.sleep(5)
        response = bedrock_client.get_agent(agentId=agent_id)
        status = response["agent"]["agentStatus"]
        if status == "PREPARED":
            print(f"  ✓ Agent prepared successfully")
            break
        elif status == "FAILED":
            print(f"  ✗ Agent preparation failed")
            sys.exit(1)
        print(f"    Status: {status}...")
    else:
        print("  ✗ Timeout waiting for agent preparation")
        sys.exit(1)

    # Create alias
    try:
        response = bedrock_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName="prod",
            description="Production alias for DiabetesControl AI Expert",
        )
        alias_id = response["agentAlias"]["agentAliasId"]
        print(f"  ✓ Created alias 'prod': {alias_id}")
        return alias_id
    except ClientError as e:
        if "ConflictException" in str(e):
            # Find existing alias
            aliases = bedrock_client.list_agent_aliases(agentId=agent_id)
            for alias in aliases.get("agentAliasSummaries", []):
                if alias["agentAliasName"] == "prod":
                    alias_id = alias["agentAliasId"]
                    # Update the alias to point to latest version
                    bedrock_client.update_agent_alias(
                        agentId=agent_id,
                        agentAliasId=alias_id,
                        agentAliasName="prod",
                    )
                    print(f"  ✓ Updated existing alias 'prod': {alias_id}")
                    return alias_id
        raise


def main():
    parser = argparse.ArgumentParser(description="Setup Bedrock Agent for DiabetesControl AI")
    parser.add_argument("--region", default="ap-southeast-1", help="AWS Region")
    parser.add_argument("--stack-name", default="diabetes-care-agent", help="SAM stack name")
    args = parser.parse_args()

    print("\n🩺 DiabetesControl AI Expert - Agent Setup")
    print("=" * 50)

    # Initialize clients
    bedrock_client = boto3.client("bedrock-agent", region_name=args.region)
    cfn_client = boto3.client("cloudformation", region_name=args.region)

    # Step 1: Load files
    print("\n📄 Loading configuration files...")
    instruction = load_file("agents/instruction.txt")
    schema = load_file("schemas/openapi.yaml")
    print(f"  ✓ Loaded agent instruction ({len(instruction)} chars)")
    print(f"  ✓ Loaded OpenAPI schema ({len(schema)} chars)")

    # Step 2: Get Lambda ARN
    print("\n🔍 Finding Lambda function...")
    lambda_arn = get_lambda_arn(cfn_client, args.stack_name, "DiabetesToolsFunction")
    print(f"  ✓ Lambda ARN: {lambda_arn}")

    # Step 3: Create agent
    print("\n🤖 Creating Bedrock Agent...")
    agent_id = create_agent(bedrock_client, instruction, args.region)

    # Step 4: Create action group
    print("\n🔧 Creating Action Group...")
    create_action_group(bedrock_client, agent_id, lambda_arn, schema)

    # Step 5: Prepare and create alias
    print("\n🚀 Preparing agent and creating alias...")
    alias_id = prepare_and_create_alias(bedrock_client, agent_id)

    # Done!
    print("\n" + "=" * 50)
    print("✅ Setup complete!\n")
    print(f"  Agent ID:       {agent_id}")
    print(f"  Agent Alias ID: {alias_id}")
    print(f"  Region:         {args.region}")
    print(f"\n📋 Next steps:")
    print(f"  1. Update the API Lambda environment variables:")
    print(f"     aws lambda update-function-configuration \\")
    print(f"       --function-name diabetes-care-api \\")
    print(f"       --environment \"Variables={{BEDROCK_AGENT_ID={agent_id},BEDROCK_AGENT_ALIAS_ID={alias_id},AWS_REGION_NAME={args.region}}}\"")
    print(f"\n  2. Update frontend/config.js with your API Gateway URL")
    print(f"\n  3. Open frontend/index.html in a browser and start chatting!")
    print()


if __name__ == "__main__":
    main()
