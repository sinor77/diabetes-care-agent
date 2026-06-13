# 🩺 DiabetesControl AI Expert - Amazon Bedrock Agent

A Digital Diabetes Care Assistant powered by Amazon Bedrock Agents (Claude 3.5 Sonnet) with 4 functional Lambda-backed tools, a modern chat frontend, and one-click AWS deployment via SAM.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (S3 / Local)                      │
│        HTML / Tailwind CSS / Vanilla JS Chat + Dashboard    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│                   API Gateway (REST)                         │
│              POST /chat    GET /session                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Amazon Bedrock Agent                            │
│      Model: anthropic.claude-3-5-sonnet-20241022-v2:0       │
│   Tone: Empathetic, evidence-based diabetes care assistant  │
└──────────┬───────────┬───────────┬───────────┬──────────────┘
           │           │           │           │
   ┌───────▼──┐ ┌──────▼───┐ ┌────▼─────┐ ┌──▼───────────┐
   │  Meal    │ │   Lab    │ │  Risk    │ │    Plan      │
   │ Analyzer │ │Interpeter│ │Predictor │ │  Generator   │
   │ (Lambda) │ │ (Lambda) │ │ (Lambda) │ │  (Lambda)    │
   └──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

## Features

- **Meal Analyzer** — Estimates glycemic impact, net carbs, glycemic load, and suggests healthier alternatives
- **Lab Interpreter** — Parses HbA1c, Fasting Glucose, Lipid Panel against ADA clinical guidelines
- **Risk Predictor** — Flags near-term risks (hypo/hyperglycemic events) based on meal/exercise patterns
- **Plan Generator** — Synthesizes all tool outputs into a structured daily routine (nutrition, hydration, activity)

## Prerequisites

1. **AWS Account** with Bedrock model access enabled for Claude 3.5 Sonnet
   - Go to AWS Console → Bedrock → Model access → Request access to Anthropic Claude 3.5 Sonnet
2. **AWS CLI v2** configured (`aws configure`)
3. **AWS SAM CLI** installed — [Install Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
4. **Python 3.11+**
5. **Git**

## IAM Policies Required

Your deploying user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "lambda:*",
        "apigateway:*",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:TagRole",
        "s3:*",
        "cloudformation:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

> ⚠️ For production, scope these down to least-privilege per resource ARN.

## 🚀 Step-by-Step Deployment

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/diabetes-care-agent.git
cd diabetes-care-agent
```

### Step 2: Build and Deploy with SAM

```bash
sam build
sam deploy --guided
```

During guided deployment, provide:
- **Stack Name:** `diabetes-care-agent`
- **Region:** `us-east-1` (or any Bedrock-enabled region)
- **Confirm changes:** Y
- **Allow SAM CLI IAM role creation:** Y
- **Save arguments to samconfig.toml:** Y

### Step 3: Create the Bedrock Agent

After SAM deploys the Lambda and API Gateway, run the setup script to create and configure the Bedrock Agent:

```bash
pip install boto3
python scripts/setup_agent.py --region us-east-1
```

This script will:
1. Create the Bedrock Agent with the system prompt
2. Create an Action Group with the OpenAPI schema
3. Attach the Lambda function
4. Prepare and create an alias
5. Print the Agent ID and Alias ID

### Step 4: Update API Lambda Environment

```bash
aws lambda update-function-configuration \
  --function-name diabetes-care-api \
  --environment "Variables={BEDROCK_AGENT_ID=<AGENT_ID>,BEDROCK_AGENT_ALIAS_ID=<ALIAS_ID>,AWS_REGION_NAME=us-east-1}"
```

### Step 5: Configure Frontend

Edit `frontend/config.js`:
```javascript
const CONFIG = {
  API_ENDPOINT: "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod",
};
```

### Step 6: Open the Frontend

Open `frontend/index.html` in your browser, or deploy to S3:

```bash
aws s3 mb s3://diabetes-care-frontend-YOUR_ACCOUNT_ID
aws s3 sync frontend/ s3://diabetes-care-frontend-YOUR_ACCOUNT_ID --acl public-read
```

## Environment Variables

| Variable | Description | Set By |
|----------|-------------|--------|
| `BEDROCK_AGENT_ID` | Agent ID from Step 3 | SAM / Manual |
| `BEDROCK_AGENT_ALIAS_ID` | Agent Alias ID from Step 3 | SAM / Manual |
| `AWS_REGION_NAME` | AWS Region (e.g., us-east-1) | SAM |

## Project Structure

```
diabetes-care-agent/
├── README.md
├── template.yaml                 # SAM/CloudFormation IaC
├── samconfig.toml
├── agents/
│   └── instruction.txt           # Bedrock Agent system prompt
├── lambda/
│   ├── requirements.txt
│   ├── handler.py                # Action Group Lambda handler
│   └── tools/
│       ├── __init__.py
│       ├── meal_analyzer.py
│       ├── lab_interpreter.py
│       ├── risk_predictor.py
│       └── plan_generator.py
├── api/
│   ├── requirements.txt
│   └── handler.py                # API Gateway → Bedrock Agent proxy
├── schemas/
│   └── openapi.yaml              # OpenAPI 3.0 for Action Groups
├── frontend/
│   ├── index.html
│   ├── config.js
│   ├── app.js
│   └── styles.css
└── scripts/
    ├── deploy.sh
    └── setup_agent.py
```

## Testing Locally

```bash
cd lambda
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Customization

- **Model**: Change the model ID in `scripts/setup_agent.py` (default: Claude 3.5 Sonnet)
- **System Prompt**: Edit `agents/instruction.txt` to adjust personality/tone
- **Tools**: Add new tools in `lambda/tools/` and update `schemas/openapi.yaml`

## License

MIT
