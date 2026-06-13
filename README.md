# 🩺 DiabetesControl AI Expert

A comprehensive Digital Diabetes Care Assistant powered by **13 AWS services** — built with Amazon Bedrock (Claude 3 Haiku), serverless architecture, and a modern web frontend.

**Live App:** [https://d3onijdn12lthk.cloudfront.net](https://d3onijdn12lthk.cloudfront.net)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER (Browser)                                      │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Frontend SPA (HTML / Tailwind CSS / Vanilla JS)                          │  │
│  │  • Profile Form & Auth (Cognito)   • Tabbed Analysis Interface            │  │
│  │  • File Upload (Lab Images)        • TTS Playback (Polly Audio)           │  │
│  │  • Real-time Pipeline Status       • Persistent localStorage             │  │
│  └───────────────────────────────┬───────────────────────────────────────────┘  │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Amazon CloudFront (CDN + HTTPS)                           │
│                      d3onijdn12lthk.cloudfront.net                                │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
┌─────────────────────────────┐   ┌─────────────────────────────────────────────────┐
│   Amazon S3 (Static Host)   │   │         Amazon API Gateway (REST)                │
│   Frontend files:           │   │         /chat  /session  /profile                │
│   index.html, app.js,       │   │         /lab-vision  /textract  /polly           │
│   config.js, styles.css     │   │         /email-report  /comprehend-medical       │
└─────────────────────────────┘   │         /sms-reminder                            │
                                  └────────────────────┬────────────────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        AWS Lambda: diabetes-care-api                              │
│                     (Python 3.13 — Main API Handler)                              │
│                                                                                  │
│  Routes to:                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  /chat   │ │/lab-vision│ │/textract │ │  /polly  │ │/profile  │ │ /email   │ │
│  │          │ │          │ │          │ │          │ │          │ │ -report  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
└───────┼─────────────┼────────────┼────────────┼────────────┼────────────┼────────┘
        │             │            │            │            │            │
        ▼             ▼            ▼            ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│Amazon Bedrock│ │ Bedrock  │ │ Amazon   │ │Amazon  │ │ Amazon   │ │ Amazon   │
│   Agent      │ │ Converse │ │ Textract │ │ Polly  │ │ DynamoDB │ │   SES    │
│(Claude Haiku)│ │API+Vision│ │  (OCR)   │ │ (TTS)  │ │(Profiles)│ │ (Email)  │
│              │ │          │ │          │ │        │ │          │ │          │
│ System Prompt│ │ Reads lab│ │ Extracts │ │Converts│ │Save/Load/│ │  Sends   │
│ + Tools      │ │  images  │ │ text from│ │text to │ │Delete by │ │formatted │
│              │ │ directly │ │  images  │ │ speech │ │  email   │ │ reports  │
└──────┬───────┘ └──────────┘ └──────────┘ └────────┘ └──────────┘ └──────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock Agent Runtime                                │
│                                                                              │
│  Agent: DiabetesControl-AI-Expert (ID: TR4NBWWQNA)                           │
│  Model: anthropic.claude-3-haiku-20240307-v1:0                               │
│  Alias: prod (DWSWRR9VPL)                                                    │
│                                                                              │
│  System Prompt: Empathetic diabetes care assistant                            │
│  Capabilities: Meal analysis, Lab interpretation, Risk prediction,           │
│                Plan generation, AI coaching                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │              Action Group: DiabetesCareTools                            │  │
│  │  ┌────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────────┐   │  │
│  │  │   Meal     │ │     Lab      │ │    Risk      │ │     Plan      │   │  │
│  │  │  Analyzer  │ │  Interpreter │ │  Predictor   │ │   Generator   │   │  │
│  │  │            │ │              │ │              │ │               │   │  │
│  │  │• GI Index  │ │• ADA Ranges  │ │• Hypo Risk   │ │• Nutrition    │   │  │
│  │  │• Carbs     │ │• Flag Values │ │• Hyper Risk  │ │• Hydration    │   │  │
│  │  │• GL Score  │ │• Kidney/Lipid│ │• Variability │ │• Activity     │   │  │
│  │  │• Swaps     │ │• Recommend   │ │• Actions     │ │• Monitoring   │   │  │
│  │  └────────────┘ └──────────────┘ └──────────────┘ └───────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│                                    ▼                                          │
│                    AWS Lambda: diabetes-care-tools                             │
│                    (Action Group Handler — OpenAPI 3.0)                        │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                      AWS Step Functions                                        │
│              State Machine: DiabetesControl-FullAnalysis                       │
│                                                                              │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌─────────┐   ┌────┐  │
│  │  Meal  │──▶│  Lab   │──▶│  Risk  │──▶│  Plan  │──▶│Insights │──▶│Done│  │
│  │Analysis│   │Interpret│   │Predict │   │Generate│   │ Summary │   │ ✓  │  │
│  └────────┘   └────────┘   └────────┘   └────────┘   └─────────┘   └────┘  │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                   Supporting Services                                          │
│                                                              │                │
│                                                              ▼                │
│                                                      ┌──────────────┐        │
│                                                      │  Amazon SNS  │        │
│                                                      │ Notification │        │
│                                                      └──────────────┘        │
└──────────────────────────────────────────────────────────────────────────────┘
│                                                                              │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐ │
│  │  Amazon Cognito   │  │ Amazon CloudWatch  │  │  Amazon Comprehend Medical│ │
│  │                   │  │                   │  │                           │ │
│  │ User Pool:        │  │ Dashboard:         │  │ Detects from free text:  │ │
│  │ Sign Up/In/Out    │  │ • API Requests     │  │ • Medications + dosages  │ │
│  │ Email verification│  │ • Latency          │  │ • Medical conditions     │ │
│  │ Session tokens    │  │ • Lambda calls     │  │ • Lab values             │ │
│  │ Password policy   │  │ • Errors           │  │ • Procedures             │ │
│  │                   │  │ • DynamoDB I/O     │  │                           │ │
│  └───────────────────┘  └───────────────────┘  └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 13 AWS Services Used

| # | Service | Purpose |
|---|---------|---------|
| 1 | **Amazon Bedrock** | AI Agent — Claude 3 Haiku foundation model with system prompts |
| 2 | **AWS Lambda** | Serverless compute — API handlers + Action Group tools |
| 3 | **Amazon API Gateway** | REST API — 9 endpoints with CORS |
| 4 | **Amazon S3** | Static website hosting for the frontend |
| 5 | **Amazon CloudFront** | HTTPS CDN distribution |
| 6 | **Amazon DynamoDB** | NoSQL database for user profile persistence |
| 7 | **Amazon SES** | Transactional email delivery for progress reports |
| 8 | **Amazon Textract** | OCR — extracts text from uploaded lab images |
| 9 | **AWS Step Functions** | Orchestrates the full 5-step analysis pipeline |
| 10 | **Amazon CloudWatch** | Operational monitoring dashboard (6 metric widgets) |
| 11 | **Amazon Comprehend Medical** | Healthcare NLP — extracts medications, conditions, dosages |
| 12 | **Amazon Polly** | Neural text-to-speech (Joanna voice) |
| 13 | **Amazon Cognito** | User authentication (sign up, email verify, sign in/out) |

---

## Features

### AI-Powered Analysis Tools
- **🥗 Meal Analyzer** — Glycemic index, carb estimation, glycemic load, healthier alternatives
- **🧪 Lab Interpreter** — Parses HbA1c, glucose, lipids, kidney markers against ADA guidelines
- **⚡ Risk Predictor** — Flags hypoglycemia, hyperglycemia, and glucose variability risks
- **📋 Plan Generator** — Full daily plan: nutrition, hydration, activity, monitoring
- **🤖 AI Coach** — Free-form Q&A about diabetes management
- **💡 Insights** — Overall health score, trends, weekly goals, personalized tips

### User Experience
- **👤 Persistent Profiles** — Saved to DynamoDB, auto-loads on return from any device
- **🔊 Text-to-Speech** — Amazon Polly neural voice reads analysis results aloud
- **📧 Email Reports** — Full analysis reports sent via Amazon SES
- **🔐 User Auth** — Sign up / sign in with Amazon Cognito
- **📷 Lab Upload** — Upload lab photos analyzed with Textract + Claude Vision
- **🚀 Pipeline** — One-click runs all 5 analyses via Step Functions orchestration
- **📊 Monitoring** — Live CloudWatch dashboard for operational metrics

---

## Project Structure

```
diabetes-care-agent/
├── README.md
├── template.yaml                    # SAM/CloudFormation template
├── samconfig.toml                   # SAM deployment config
├── cloudformation.yaml              # Generated CF template
├── agents/
│   └── instruction.txt              # Bedrock Agent system prompt
├── lambda/
│   ├── handler.py                   # Action Group Lambda (tools router)
│   ├── requirements.txt
│   └── tools/
│       ├── meal_analyzer.py         # Glycemic analysis engine
│       ├── lab_interpreter.py       # ADA reference range comparison
│       ├── risk_predictor.py        # Pattern-based risk scoring
│       └── plan_generator.py        # Daily routine builder
├── api/
│   ├── handler.py                   # API Gateway Lambda (9 endpoints)
│   └── requirements.txt
├── schemas/
│   └── openapi.yaml                 # OpenAPI 3.0 for Bedrock Action Groups
├── frontend/
│   ├── index.html                   # Main SPA (tabbed interface)
│   ├── app.js                       # Application logic + Cognito + Polly
│   ├── config.js                    # API endpoint + Cognito config
│   └── styles.css                   # Custom styles
└── scripts/
    ├── deploy_no_sam.py             # Direct deployment (no SAM CLI needed)
    ├── setup_agent.py               # Creates Bedrock Agent + Action Group
    ├── deploy.sh / deploy.bat       # Shell deployment scripts
    ├── cloudfront-config.json       # CloudFront distribution config
    ├── cloudwatch-dashboard.json    # CloudWatch dashboard definition
    ├── stepfunctions-definition.json # Step Functions state machine
    └── *.json                       # IAM policies and configs
```

---

## Deployment

### Prerequisites
- AWS Account with Bedrock access (ap-southeast-1)
- AWS CLI v2 configured
- Python 3.11+

### Quick Deploy

```bash
# Clone
git clone https://github.com/sinor77/diabetes-care-agent.git
cd diabetes-care-agent

# Deploy infrastructure + agent (one command)
python scripts/deploy_no_sam.py --region ap-southeast-1
```

This script:
1. Creates S3 deployment bucket
2. Packages and uploads Lambda code
3. Deploys CloudFormation stack (Lambda + API Gateway + IAM)
4. Creates Bedrock Agent with system prompt
5. Attaches Action Group with OpenAPI schema
6. Prepares agent and creates alias
7. Links API Lambda to agent
8. Prints the API URL

### Post-Deploy Setup
```bash
# Create DynamoDB table
aws dynamodb create-table --table-name diabetes-care-profiles \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region ap-southeast-1

# Verify email for SES
aws ses verify-email-identity --email-address YOUR_EMAIL --region ap-southeast-1

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://scripts/cloudfront-config.json

# Upload frontend
aws s3 sync frontend/ s3://YOUR-BUCKET/ --region ap-southeast-1
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /session | Generate new chat session ID |
| POST | /chat | Send message to Bedrock Agent |
| POST | /lab-vision | Analyze lab image with Claude Vision |
| POST | /textract | OCR text extraction from images |
| POST | /polly | Text-to-speech synthesis |
| POST | /comprehend-medical | Medical entity extraction |
| POST | /email-report | Send report via SES |
| POST/GET/DELETE | /profile | CRUD user profiles in DynamoDB |

---

## Environment Variables (API Lambda)

| Variable | Value |
|----------|-------|
| `BEDROCK_AGENT_ID` | TR4NBWWQNA |
| `BEDROCK_AGENT_ALIAS_ID` | DWSWRR9VPL |
| `AWS_REGION_NAME` | ap-southeast-1 |

---

## Security

- **Cognito** handles user authentication with email verification
- **IAM roles** follow least-privilege per Lambda function
- **CORS** configured on all API Gateway endpoints
- **CloudFront** enforces HTTPS redirect
- **No secrets in code** — all config via environment variables

---

## Cost Estimate (Monthly)

All services are serverless/pay-per-use:
- Bedrock (Haiku): ~$0.25/1M input tokens
- Lambda: Free tier covers 1M requests
- API Gateway: Free tier covers 1M calls
- DynamoDB: Free tier covers 25 RCU/WCU
- S3 + CloudFront: Pennies for static hosting
- **Estimated total for demo usage: < $5/month**

---

## License

MIT

---

*Built for AWS Cloud Competition 2025 — Showcasing 13 integrated AWS services for AI-powered healthcare.*
