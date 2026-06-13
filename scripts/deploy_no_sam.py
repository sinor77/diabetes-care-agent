"""
Direct AWS deployment script - deploys without SAM CLI Python version requirements.
Packages Lambda code as zip, uploads to S3, and deploys via CloudFormation.

Usage:
    python scripts/deploy_no_sam.py --region ap-southeast-1
"""

import argparse
import json
import os
import sys
import time
import zipfile
import tempfile
import boto3
from botocore.exceptions import ClientError

STACK_NAME = "diabetes-care-agent"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_zip(source_dir: str, output_path: str):
    """Create a zip file from a directory."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.pyc') or '__pycache__' in root:
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)


def ensure_s3_bucket(s3_client, bucket_name: str, region: str):
    """Create S3 bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"  ✓ S3 bucket exists: {bucket_name}")
    except ClientError:
        try:
            if region == "us-east-1":
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )
            print(f"  ✓ Created S3 bucket: {bucket_name}")
        except ClientError as e:
            if "BucketAlreadyOwnedByYou" in str(e):
                print(f"  ✓ S3 bucket exists: {bucket_name}")
            else:
                raise


def main():
    parser = argparse.ArgumentParser(description="Deploy DiabetesControl AI without SAM")
    parser.add_argument("--region", default="ap-southeast-1", help="AWS Region")
    parser.add_argument("--stack-name", default=STACK_NAME, help="CloudFormation stack name")
    args = parser.parse_args()

    print("\n🩺 DiabetesControl AI Expert - Direct Deployment")
    print("=" * 50)
    print(f"  Region: {args.region}")
    print(f"  Stack:  {args.stack_name}")

    # Initialize clients
    sts = boto3.client("sts", region_name=args.region)
    s3 = boto3.client("s3", region_name=args.region)
    cfn = boto3.client("cloudformation", region_name=args.region)
    lambda_client = boto3.client("lambda", region_name=args.region)

    # Get account ID
    account_id = sts.get_caller_identity()["Account"]
    bucket_name = f"diabetes-care-deploy-{account_id}-{args.region}"

    # Step 1: Create deployment bucket
    print("\n📦 Setting up deployment bucket...")
    ensure_s3_bucket(s3, bucket_name, args.region)

    # Step 2: Package Lambda functions
    print("\n📦 Packaging Lambda functions...")
    
    # Package tools Lambda
    tools_zip_path = os.path.join(tempfile.gettempdir(), "diabetes-tools-lambda.zip")
    tools_dir = os.path.join(BASE_DIR, "lambda")
    create_zip(tools_dir, tools_zip_path)
    tools_s3_key = "lambda/diabetes-tools-lambda.zip"
    s3.upload_file(tools_zip_path, bucket_name, tools_s3_key)
    print(f"  ✓ Uploaded tools Lambda ({os.path.getsize(tools_zip_path) // 1024} KB)")

    # Package API Lambda
    api_zip_path = os.path.join(tempfile.gettempdir(), "diabetes-api-lambda.zip")
    api_dir = os.path.join(BASE_DIR, "api")
    create_zip(api_dir, api_zip_path)
    api_s3_key = "lambda/diabetes-api-lambda.zip"
    s3.upload_file(api_zip_path, bucket_name, api_s3_key)
    print(f"  ✓ Uploaded API Lambda ({os.path.getsize(api_zip_path) // 1024} KB)")

    # Step 3: Deploy CloudFormation stack
    print("\n🚀 Deploying CloudFormation stack...")
    
    template_path = os.path.join(BASE_DIR, "cloudformation.yaml")
    
    # Create a CF-native template (not SAM) for direct deployment
    cf_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "DiabetesControl AI Expert - Bedrock Agent with Lambda tools",
        "Parameters": {
            "BedrockAgentId": {
                "Type": "String",
                "Default": "",
                "Description": "Bedrock Agent ID (set after agent creation)"
            },
            "BedrockAgentAliasId": {
                "Type": "String",
                "Default": "",
                "Description": "Bedrock Agent Alias ID (set after agent creation)"
            }
        },
        "Resources": {
            "DiabetesToolsRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": f"diabetes-care-tools-role-{args.region}",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ]
                }
            },
            "ApiRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": f"diabetes-care-api-role-{args.region}",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }]
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                    "Policies": [{
                        "PolicyName": "BedrockAgentInvoke",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Effect": "Allow",
                                "Action": ["bedrock:InvokeAgent"],
                                "Resource": f"arn:aws:bedrock:{args.region}:{account_id}:agent-alias/*"
                            }]
                        }
                    }]
                }
            },
            "DiabetesToolsFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": "diabetes-care-tools",
                    "Runtime": "python3.13",
                    "Handler": "handler.handler",
                    "Role": {"Fn::GetAtt": ["DiabetesToolsRole", "Arn"]},
                    "Code": {
                        "S3Bucket": bucket_name,
                        "S3Key": tools_s3_key
                    },
                    "Timeout": 60,
                    "MemorySize": 256
                }
            },
            "BedrockInvokePermission": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Ref": "DiabetesToolsFunction"},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "bedrock.amazonaws.com",
                    "SourceAccount": account_id
                }
            },
            "ApiFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": "diabetes-care-api",
                    "Runtime": "python3.13",
                    "Handler": "handler.handler",
                    "Role": {"Fn::GetAtt": ["ApiRole", "Arn"]},
                    "Code": {
                        "S3Bucket": bucket_name,
                        "S3Key": api_s3_key
                    },
                    "Timeout": 60,
                    "MemorySize": 256,
                    "Environment": {
                        "Variables": {
                            "BEDROCK_AGENT_ID": {"Ref": "BedrockAgentId"},
                            "BEDROCK_AGENT_ALIAS_ID": {"Ref": "BedrockAgentAliasId"},
                            "AWS_REGION_NAME": args.region
                        }
                    }
                }
            },
            "ApiGateway": {
                "Type": "AWS::ApiGateway::RestApi",
                "Properties": {
                    "Name": "diabetes-care-api",
                    "Description": "DiabetesControl AI Expert API"
                }
            },
            "ApiResourceChat": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "ParentId": {"Fn::GetAtt": ["ApiGateway", "RootResourceId"]},
                    "PathPart": "chat"
                }
            },
            "ApiResourceSession": {
                "Type": "AWS::ApiGateway::Resource",
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "ParentId": {"Fn::GetAtt": ["ApiGateway", "RootResourceId"]},
                    "PathPart": "session"
                }
            },
            "ChatPostMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "ResourceId": {"Ref": "ApiResourceChat"},
                    "HttpMethod": "POST",
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "Type": "AWS_PROXY",
                        "IntegrationHttpMethod": "POST",
                        "Uri": {"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiFunction.Arn}/invocations"}
                    }
                }
            },
            "ChatOptionsMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "ResourceId": {"Ref": "ApiResourceChat"},
                    "HttpMethod": "OPTIONS",
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "Type": "MOCK",
                        "IntegrationResponses": [{
                            "StatusCode": "200",
                            "ResponseParameters": {
                                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Session-Id'",
                                "method.response.header.Access-Control-Allow-Methods": "'POST,OPTIONS'",
                                "method.response.header.Access-Control-Allow-Origin": "'*'"
                            },
                            "ResponseTemplates": {"application/json": ""}
                        }],
                        "RequestTemplates": {"application/json": '{"statusCode": 200}'}
                    },
                    "MethodResponses": [{
                        "StatusCode": "200",
                        "ResponseParameters": {
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Methods": True,
                            "method.response.header.Access-Control-Allow-Origin": True
                        }
                    }]
                }
            },
            "SessionGetMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "ResourceId": {"Ref": "ApiResourceSession"},
                    "HttpMethod": "GET",
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "Type": "AWS_PROXY",
                        "IntegrationHttpMethod": "POST",
                        "Uri": {"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ApiFunction.Arn}/invocations"}
                    }
                }
            },
            "SessionOptionsMethod": {
                "Type": "AWS::ApiGateway::Method",
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "ResourceId": {"Ref": "ApiResourceSession"},
                    "HttpMethod": "OPTIONS",
                    "AuthorizationType": "NONE",
                    "Integration": {
                        "Type": "MOCK",
                        "IntegrationResponses": [{
                            "StatusCode": "200",
                            "ResponseParameters": {
                                "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Session-Id'",
                                "method.response.header.Access-Control-Allow-Methods": "'GET,OPTIONS'",
                                "method.response.header.Access-Control-Allow-Origin": "'*'"
                            },
                            "ResponseTemplates": {"application/json": ""}
                        }],
                        "RequestTemplates": {"application/json": '{"statusCode": 200}'}
                    },
                    "MethodResponses": [{
                        "StatusCode": "200",
                        "ResponseParameters": {
                            "method.response.header.Access-Control-Allow-Headers": True,
                            "method.response.header.Access-Control-Allow-Methods": True,
                            "method.response.header.Access-Control-Allow-Origin": True
                        }
                    }]
                }
            },
            "ApiDeployment": {
                "Type": "AWS::ApiGateway::Deployment",
                "DependsOn": ["ChatPostMethod", "SessionGetMethod", "ChatOptionsMethod", "SessionOptionsMethod"],
                "Properties": {
                    "RestApiId": {"Ref": "ApiGateway"},
                    "StageName": "prod"
                }
            },
            "ApiLambdaPermission": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "FunctionName": {"Ref": "ApiFunction"},
                    "Action": "lambda:InvokeFunction",
                    "Principal": "apigateway.amazonaws.com",
                    "SourceArn": {"Fn::Sub": "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${ApiGateway}/*"}
                }
            }
        },
        "Outputs": {
            "ApiGatewayUrl": {
                "Description": "API Gateway endpoint URL",
                "Value": {"Fn::Sub": "https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com/prod"}
            },
            "DiabetesToolsFunctionArn": {
                "Description": "ARN of the tools Lambda",
                "Value": {"Fn::GetAtt": ["DiabetesToolsFunction", "Arn"]}
            }
        }
    }

    # Write template
    with open(template_path, 'w') as f:
        json.dump(cf_template, f, indent=2)
    print(f"  ✓ Generated CloudFormation template")

    # Deploy
    template_body = json.dumps(cf_template)
    
    try:
        # Check if stack exists
        cfn.describe_stacks(StackName=args.stack_name)
        # Update
        print(f"  ⏳ Updating stack '{args.stack_name}'...")
        cfn.update_stack(
            StackName=args.stack_name,
            TemplateBody=template_body,
            Capabilities=["CAPABILITY_NAMED_IAM"],
            Parameters=[
                {"ParameterKey": "BedrockAgentId", "ParameterValue": ""},
                {"ParameterKey": "BedrockAgentAliasId", "ParameterValue": ""},
            ]
        )
    except ClientError as e:
        if "does not exist" in str(e):
            # Create
            print(f"  ⏳ Creating stack '{args.stack_name}'...")
            cfn.create_stack(
                StackName=args.stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_NAMED_IAM"],
                Parameters=[
                    {"ParameterKey": "BedrockAgentId", "ParameterValue": ""},
                    {"ParameterKey": "BedrockAgentAliasId", "ParameterValue": ""},
                ]
            )
        elif "No updates" in str(e):
            print(f"  ✓ Stack already up to date")
        else:
            raise

    # Wait for stack
    print(f"  ⏳ Waiting for stack deployment (this may take 2-3 minutes)...")
    waiter = cfn.get_waiter("stack_create_complete")
    try:
        waiter.wait(StackName=args.stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60})
    except Exception:
        # Try update waiter
        try:
            waiter = cfn.get_waiter("stack_update_complete")
            waiter.wait(StackName=args.stack_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60})
        except Exception as e2:
            # Check if it actually succeeded
            stack = cfn.describe_stacks(StackName=args.stack_name)
            status = stack["Stacks"][0]["StackStatus"]
            if status in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                pass
            else:
                print(f"  ✗ Stack status: {status}")
                print(f"  Check AWS Console > CloudFormation for details")
                sys.exit(1)

    # Get outputs
    stack = cfn.describe_stacks(StackName=args.stack_name)
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack["Stacks"][0].get("Outputs", [])}
    
    api_url = outputs.get("ApiGatewayUrl", "")
    tools_arn = outputs.get("DiabetesToolsFunctionArn", "")

    print(f"\n  ✓ Stack deployed successfully!")
    print(f"  API URL:    {api_url}")
    print(f"  Tools ARN:  {tools_arn}")

    # Step 4: Setup Bedrock Agent
    print("\n🤖 Setting up Bedrock Agent...")
    
    # Import and run agent setup
    sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
    from setup_agent import create_agent, create_action_group, prepare_and_create_alias, load_file
    
    bedrock_client = boto3.client("bedrock-agent", region_name=args.region)
    
    instruction = load_file("agents/instruction.txt")
    schema = load_file("schemas/openapi.yaml")
    
    agent_id = create_agent(bedrock_client, instruction, args.region)
    create_action_group(bedrock_client, agent_id, tools_arn, schema)
    alias_id = prepare_and_create_alias(bedrock_client, agent_id)

    # Step 5: Update API Lambda with agent IDs
    print("\n🔗 Linking API to Bedrock Agent...")
    lambda_client.update_function_configuration(
        FunctionName="diabetes-care-api",
        Environment={
            "Variables": {
                "BEDROCK_AGENT_ID": agent_id,
                "BEDROCK_AGENT_ALIAS_ID": alias_id,
                "AWS_REGION_NAME": args.region,
            }
        }
    )
    print(f"  ✓ API Lambda updated with Agent ID: {agent_id}")

    # Done!
    print("\n" + "=" * 50)
    print("✅ DEPLOYMENT COMPLETE!\n")
    print(f"  🌐 API Endpoint:    {api_url}")
    print(f"  🤖 Agent ID:        {agent_id}")
    print(f"  🏷️  Agent Alias ID:  {alias_id}")
    print(f"  📍 Region:          {args.region}")
    print(f"\n📋 Final step:")
    print(f"  Update frontend/config.js with:")
    print(f'    API_ENDPOINT: "{api_url}"')
    print(f"\n  Then open frontend/index.html in your browser!")
    print()

    # Clean up temp files
    os.remove(tools_zip_path)
    os.remove(api_zip_path)


if __name__ == "__main__":
    main()
