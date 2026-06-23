"""Add patient scenario to slide 9."""
lines = open('scripts/make_final_pptx.py', 'r', encoding='utf-8').readlines()
start = next(i for i, l in enumerate(lines) if 'SLIDE 9' in l)
end = next(i for i, l in enumerate(lines) if 'SLIDE 9.5' in l or 'SLIDE 10' in l)

new_slide = '''
# ===== SLIDE 9: IMPACT + SCENARIO =====
s=S(); hdr(s,"Real-World Impact")
T(s,0.5,0.85,12,0.5,"How It Changes One Life",sz=26,b=True,c=TEXT)

# TOP: Patient scenario (the main story)
card(s,0.5,1.4,12.3,2.6,fill=GL,border=GREEN)
T(s,0.7,1.5,11.9,0.35,"Encik Razak, 55 \\u2014 Taxi driver in Petaling Jaya \\u2014 Type 2 diabetes, 6 years",sz=14,b=True,c=GREEN)

T(s,0.7,1.9,5.8,0.3,"\\u274c  BEFORE (no app):",sz=11,b=True,c=RED)
T(s,0.7,2.2,5.8,1.5,"\\u2022 Eats nasi lemak every morning, sugar spikes to 240\\n\\u2022 Doesn't know which foods are safe\\n\\u2022 Next specialist appointment: 4 months away\\n\\u2022 Forgot to take medication twice this week\\n\\u2022 HbA1c stuck at 8.2% for 2 years",sz=10,c=TEXT)

T(s,6.8,1.9,5.8,0.3,"\\u2705  AFTER (with our app):",sz=11,b=True,c=GREEN)
T(s,6.8,2.2,5.8,1.5,"\\u2022 AI Coach: \\u201cHalf rice + extra egg + teh-o kosong\\u201d\\n\\u2022 Uploads lab photo \\u2192 AI flags high LDL instantly\\n\\u2022 Sends data to Dr. Sarah \\u2192 she adjusts plan same day\\n\\u2022 Daily plan reminds medication timing\\n\\u2022 HbA1c drops to 7.4% in 3 months",sz=10,c=TEXT)

T(s,0.7,3.65,11.9,0.3,"Result: Encik Razak avoids kidney complications, saves RM 2,400/year in hospital visits, and feels in control for the first time.",sz=11,b=True,c=TEXT)

# BOTTOM: Pilot + Cost side by side
card(s,0.5,4.2,6.1,2.7)
T(s,0.7,4.3,5.7,0.3,"\\U0001f3e5  Ready to Pilot",sz=12,b=True,c=GREEN)
T(s,0.7,4.65,5.7,0.35,"Klinik Kesihatan Bandar Botanic",sz=14,b=True,c=TEXT)
T(s,0.7,5.05,5.7,0.7,"\\u2022 1,200 diabetes patients on file\\n\\u2022 Endocrinologist visits every 3-4 months\\n\\u2022 Our app fills the 90-day gap",sz=10,c=MUTED)
T(s,0.7,5.9,5.7,0.6,"Backup: MOH Klinik Komuniti, NADI,\\nPersatuan Diabetes Malaysia",sz=9,c=MUTED)

card(s,6.8,4.2,6.1,2.7)
T(s,7.0,4.3,5.7,0.3,"\\U0001f4b0  Cost per User / Month",sz=12,b=True,c=GREEN)
T(s,7.0,4.7,4.0,0.22,"Bedrock (200 chats)",sz=10,c=MUTED)
T(s,11.0,4.7,1.7,0.22,"$0.10",sz=10,c=TEXT,a=PP_ALIGN.RIGHT)
T(s,7.0,4.95,4.0,0.22,"Lambda + API Gateway",sz=10,c=MUTED)
T(s,11.0,4.95,1.7,0.22,"Free tier",sz=10,c=TEXT,a=PP_ALIGN.RIGHT)
T(s,7.0,5.2,4.0,0.22,"DynamoDB (3 tables)",sz=10,c=MUTED)
T(s,11.0,5.2,1.7,0.22,"Free tier",sz=10,c=TEXT,a=PP_ALIGN.RIGHT)
T(s,7.0,5.45,4.0,0.22,"SES + CloudFront + S3",sz=10,c=MUTED)
T(s,11.0,5.45,1.7,0.22,"$0.03",sz=10,c=TEXT,a=PP_ALIGN.RIGHT)

T(s,7.0,5.85,4.0,0.3,"TOTAL",sz=12,b=True,c=TEXT)
T(s,11.0,5.85,1.7,0.3,"$0.13",sz=14,b=True,c=GREEN,a=PP_ALIGN.RIGHT)
T(s,7.0,6.2,5.7,0.4,"Less than half a ringgit per month.\\nSustainable without external funding.",sz=9,c=MUTED)

T(s,0.5,7.0,12.3,0.3,"At 100K users: 50K fewer specialist visits/year \\u2022 RM 240M saved \\u2022 35% fewer complications",sz=10,b=True,c=GREEN,a=PP_ALIGN.CENTER)
sn(s,9)

'''

output = lines[:start] + [new_slide] + lines[end:]
open('scripts/make_final_pptx.py', 'w', encoding='utf-8').writelines(output)
print("Slide 9 updated with patient scenario")
