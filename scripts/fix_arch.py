"""Replace slide 4 architecture with clean step-by-step version."""
lines = open('scripts/make_final_pptx.py', 'r', encoding='utf-8').readlines()

# Find boundaries
start = next(i for i, l in enumerate(lines) if 'SLIDE 4' in l)
end = next(i for i, l in enumerate(lines) if 'SLIDE 5' in l)

new_arch = '''
# ===== SLIDE 4: ARCHITECTURE (Step by Step) =====
s=S(); hdr(s,"System Architecture")
T(s,0.5,0.85,12,0.5,"How It Works \\u2014 Step by Step",sz=26,b=True,c=TEXT)

# STEP 1
T(s,0.3,1.5,0.9,0.5,"STEP 1\\nUsers",sz=8,b=True,c=MUTED)
box(s,1.2,1.5,3.3,0.5,"Patient App\\nProfile \\u00b7 AI Tools \\u00b7 Send to Dr",GREEN,GL)
box(s,4.7,1.5,3.3,0.5,"Doctor Dashboard\\nCharts \\u00b7 Alerts \\u00b7 Reports",BLUE,RGBColor(0xDB,0xEA,0xFE))
box(s,8.2,1.5,3.3,0.5,"Admin Panel\\nVerify Doctors \\u00b7 Users",PURPLE,RGBColor(0xF3,0xE8,0xFF))

T(s,6.2,2.05,1,0.3,"\\u25bc",sz=14,c=MUTED,a=PP_ALIGN.CENTER)

# STEP 2
T(s,0.3,2.35,0.9,0.5,"STEP 2\\nDelivery",sz=8,b=True,c=MUTED)
box(s,1.2,2.35,10.3,0.45,"Amazon CloudFront (HTTPS CDN) + Amazon S3 (Website Hosting)",CYAN)

T(s,6.2,2.85,1,0.3,"\\u25bc",sz=14,c=MUTED,a=PP_ALIGN.CENTER)

# STEP 3
T(s,0.3,3.1,0.9,0.5,"STEP 3\\nAuth+API",sz=8,b=True,c=MUTED)
box(s,1.2,3.1,4.5,0.5,"Amazon Cognito\\nLogin \\u00b7 Role: Patient or Doctor",PURPLE,RGBColor(0xF3,0xE8,0xFF))
T(s,5.85,3.32,0.5,0.3,"\\u2192",sz=14,c=MUTED,a=PP_ALIGN.CENTER)
box(s,6.2,3.1,5.3,0.5,"API Gateway + Lambda\\n14 endpoints \\u00b7 Python 3.13",GREEN,GL)

T(s,8.8,3.65,1,0.3,"\\u25bc",sz=14,c=MUTED,a=PP_ALIGN.CENTER)

# STEP 4
T(s,0.3,3.95,0.9,0.5,"STEP 4\\nCore AI\\n& Data",sz=8,b=True,c=MUTED)
box(s,1.2,3.9,2.85,0.75,"Amazon Bedrock\\n(Claude 3 Haiku)\\nChat \\u00b7 Meal \\u00b7 Risk\\nPlan \\u00b7 Lab \\u00b7 Coach",ORANGE,RGBColor(0xFF,0xED,0xD5))
box(s,4.25,3.9,2.85,0.75,"Amazon DynamoDB\\n(3 Tables)\\nProfiles \\u00b7 Logs\\nReferrals",BLUE,RGBColor(0xDB,0xEA,0xFE))
box(s,7.3,3.9,2.5,0.75,"Textract + Comprehend\\nMedical\\nReads lab photos\\nExtracts meds",PURPLE,RGBColor(0xF3,0xE8,0xFF))
box(s,10.0,3.9,2.5,0.75,"Amazon Polly\\n(Text-to-Speech)\\nReads results\\naloud",PINK,RGBColor(0xFC,0xE7,0xF3))

T(s,6.2,4.7,1,0.3,"\\u25bc",sz=14,c=MUTED,a=PP_ALIGN.CENTER)

# STEP 5
T(s,0.3,5.0,0.9,0.5,"STEP 5\\nOutput",sz=8,b=True,c=MUTED)
box(s,1.2,4.95,2.85,0.55,"Amazon SES\\nEmail reports\\nto patient inbox",GREEN,GL)
box(s,4.25,4.95,2.85,0.55,"EventBridge\\nAlerts when HbA1c>9%\\nor glucose>300",AMBER,RGBColor(0xFE,0xF3,0xC7))
box(s,7.3,4.95,2.5,0.55,"Step Functions\\nPipeline: Meal\\u2192Lab\\u2192Risk\\u2192Plan",AMBER,RGBColor(0xFE,0xF3,0xC7))
box(s,10.0,4.95,2.5,0.55,"CloudWatch\\nMonitor API calls\\nLatency + Errors",RED,RGBColor(0xFE,0xE2,0xE2))

# Data flow summary
card(s,0.5,5.75,12.3,1.4,fill=GL,border=GREEN)
T(s,0.7,5.85,11.9,0.25,"Data Flow:",sz=10,b=True,c=GREEN)
T(s,0.7,6.1,11.9,1.0,"1. Patient signs in (Cognito) \\u2192 saves profile (DynamoDB) \\u2192 each save logs a time-stamped health metric\\n2. Patient uploads lab photo \\u2192 Textract reads it \\u2192 Bedrock interprets values \\u2192 saved\\n3. Patient selects data to share (checkboxes) \\u2192 sends referral to Doctor (DynamoDB)\\n4. Doctor signs in \\u2192 sees referred patients \\u2192 charts render from health-logs \\u2192 AI analyzes trends\\n5. Doctor writes notes \\u2192 report sent back to patient (DynamoDB + SES)",sz=9,c=TEXT)
sn(s,4)

'''

# Rebuild file
output = lines[:start] + [new_arch] + lines[end:]
open('scripts/make_final_pptx.py', 'w', encoding='utf-8').writelines(output)
print("Done - architecture slide replaced")
