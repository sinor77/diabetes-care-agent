"""Replace slide 8 with simpler version."""
lines = open('scripts/make_final_pptx.py', 'r', encoding='utf-8').readlines()
start = next(i for i, l in enumerate(lines) if 'SLIDE 8' in l)
end = next(i for i, l in enumerate(lines) if 'SLIDE 9' in l)

new_slide = '''
# ===== SLIDE 8: WHY AI =====
s=S(); hdr(s,"Why AI?")
T(s,0.5,0.85,12,0.5,"Regular App vs Our AI",sz=28,b=True,c=TEXT)
T(s,0.5,1.35,12,0.3,"A form collects data. Our AI understands it.",sz=14,b=True,c=GREEN)

# Simple before/after rows
T(s,0.5,1.9,6,0.35,"\\u274c  Without AI",sz=13,b=True,c=RED)
T(s,6.8,1.9,6,0.35,"\\u2705  With Our AI",sz=13,b=True,c=GREEN)

pairs = [
    ("Patient uploads lab photo\\n\\u2192 Must type values manually","AI reads the photo\\n\\u2192 Extracts all values instantly"),
    ("Sugar was 245 after dinner\\n\\u2192 App stores the number 245","Knows 245 is HIGH for this patient\\n\\u2192 Tells them what to eat next"),
    ("Doctor sees a table of numbers\\n\\u2192 Must interpret alone","AI says: HbA1c dropping but LDL rising\\n\\u2192 Recommend statin discussion"),
    ("Can I eat nasi lemak?\\n\\u2192 Generic PDF advice","Knows their weight, meds, HbA1c\\n\\u2192 Half rice + extra egg + teh-o"),
    ("Risk detection\\n\\u2192 Nothing until next visit (3 months)","Flags: meal gap + medication\\n\\u2192 Hypo risk RIGHT NOW"),
]

y = 2.4
for left, right in pairs:
    card(s,0.5,y,6.1,0.85,fill=RGBColor(0xFE,0xE2,0xE2),border=RED)
    T(s,0.7,y+0.1,5.7,0.7,left,sz=10,c=TEXT)
    card(s,6.8,y,6.1,0.85,fill=GL,border=GREEN)
    T(s,7.0,y+0.1,5.7,0.7,right,sz=10,c=TEXT)
    y += 0.95

T(s,0.5,7.0,12.3,0.3,"Powered by: Amazon Bedrock (Claude 3 Haiku) + Textract + Comprehend Medical + Polly",sz=10,c=MUTED,a=PP_ALIGN.CENTER)
sn(s,8)

'''

output = lines[:start] + [new_slide] + lines[end:]
open('scripts/make_final_pptx.py', 'w', encoding='utf-8').writelines(output)
print("Slide 8 replaced with simpler version")
