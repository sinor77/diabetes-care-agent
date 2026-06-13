@echo off
REM DiabetesControl AI Expert - Full Deployment Script (Windows)
REM Usage: scripts\deploy.bat [region]
REM Example: scripts\deploy.bat us-east-1

setlocal enabledelayedexpansion

set REGION=%1
if "%REGION%"=="" set REGION=us-east-1
set STACK_NAME=diabetes-care-agent

echo.
echo  DiabetesControl AI Expert - Deployment
echo ==========================================
echo Region: %REGION%
echo Stack:  %STACK_NAME%
echo.

REM Check prerequisites
echo Checking prerequisites...
where sam >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: AWS SAM CLI not found.
    echo Install from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
    exit /b 1
)

where aws >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: AWS CLI not found.
    echo Install from: https://aws.amazon.com/cli/
    exit /b 1
)

echo   All prerequisites met

REM Step 1: Build
echo.
echo Building SAM application...
sam build --region %REGION%
if %errorlevel% neq 0 (
    echo ERROR: SAM build failed.
    exit /b 1
)
echo   Build complete

REM Step 2: Deploy
echo.
echo Deploying to AWS...
sam deploy --stack-name %STACK_NAME% --region %REGION% --capabilities CAPABILITY_IAM --resolve-s3 --no-confirm-changeset --parameter-overrides "BedrockAgentId= BedrockAgentAliasId="
if %errorlevel% neq 0 (
    echo ERROR: SAM deploy failed.
    exit /b 1
)
echo   SAM deployment complete

REM Step 3: Get outputs
echo.
echo Retrieving stack outputs...
for /f "tokens=*" %%a in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %REGION% --query "Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue" --output text') do set API_URL=%%a
echo   API URL: %API_URL%

REM Step 4: Setup Bedrock Agent
echo.
echo Setting up Bedrock Agent...
python scripts\setup_agent.py --region %REGION% --stack-name %STACK_NAME%

echo.
echo ==========================================
echo Deployment complete!
echo.
echo API Endpoint: %API_URL%
echo.
echo Update frontend\config.js with:
echo   API_ENDPOINT: "%API_URL%"
echo.
