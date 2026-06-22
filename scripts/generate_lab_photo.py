"""Generate a realistic lab report photo for the demo."""
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

# Create a clean white lab report
W, H = 800, 1000
img = Image.new('RGB', (W, H), 'white')
draw = ImageDraw.Draw(img)

try:
    font_lg = ImageFont.truetype("arial.ttf", 28)
    font_md = ImageFont.truetype("arial.ttf", 18)
    font_sm = ImageFont.truetype("arial.ttf", 15)
    font_bold = ImageFont.truetype("arialbd.ttf", 18)
except:
    font_lg = ImageFont.load_default()
    font_md = ImageFont.load_default()
    font_sm = ImageFont.load_default()
    font_bold = ImageFont.load_default()

# Header
draw.rectangle([0, 0, W, 70], fill='#16a34a')
draw.text((30, 18), "PATHOLOGY LABORATORY", font=font_lg, fill='white')
draw.text((30, 50), "Hospital Kuala Lumpur — Diagnostic Report", font=font_sm, fill='white')

# Patient info
y = 100
draw.text((30, y), "PATIENT INFORMATION", font=font_bold, fill='#0f172a')
draw.line([(30, y+25), (W-30, y+25)], fill='#cbd5e1', width=1)
y += 40
draw.text((30, y), "Name:", font=font_md, fill='#64748b'); draw.text((180, y), "Ahmed Hassan", font=font_md, fill='#0f172a')
y += 28
draw.text((30, y), "Patient ID:", font=font_md, fill='#64748b'); draw.text((180, y), "PT-2026-04812", font=font_md, fill='#0f172a')
y += 28
draw.text((30, y), "Date of Birth:", font=font_md, fill='#64748b'); draw.text((180, y), "15-Mar-1972 (52y)", font=font_md, fill='#0f172a')
y += 28
draw.text((30, y), "Sample Date:", font=font_md, fill='#64748b'); draw.text((180, y), "20-Jun-2026", font=font_md, fill='#0f172a')
y += 28
draw.text((30, y), "Report Date:", font=font_md, fill='#64748b'); draw.text((180, y), "23-Jun-2026", font=font_md, fill='#0f172a')

# Test results section
y += 50
draw.text((30, y), "TEST RESULTS", font=font_bold, fill='#0f172a')
draw.line([(30, y+25), (W-30, y+25)], fill='#cbd5e1', width=1)
y += 45

# Table header
draw.text((30, y), "Test", font=font_bold, fill='#0f172a')
draw.text((350, y), "Result", font=font_bold, fill='#0f172a')
draw.text((480, y), "Reference", font=font_bold, fill='#0f172a')
draw.text((650, y), "Status", font=font_bold, fill='#0f172a')
y += 22
draw.line([(30, y), (W-30, y)], fill='#94a3b8', width=1)
y += 12

# Glycemic Control header
draw.text((30, y), "GLYCEMIC CONTROL", font=font_sm, fill='#16a34a')
y += 25

results = [
    ("HbA1c (Glycated Hemoglobin)", "7.8 %", "< 6.5%", "HIGH", '#dc2626'),
    ("Fasting Plasma Glucose", "148 mg/dL", "70-100", "HIGH", '#dc2626'),
    ("Post-prandial Glucose (2h)", "215 mg/dL", "< 180", "HIGH", '#dc2626'),
]
for test, val, ref, status, color in results:
    draw.text((30, y), test, font=font_md, fill='#0f172a')
    draw.text((350, y), val, font=font_md, fill='#0f172a')
    draw.text((480, y), ref, font=font_sm, fill='#64748b')
    draw.text((650, y), status, font=font_md, fill=color)
    y += 26

y += 15
draw.text((30, y), "LIPID PANEL", font=font_sm, fill='#16a34a')
y += 25
results = [
    ("Total Cholesterol", "228 mg/dL", "< 200", "HIGH", '#dc2626'),
    ("LDL Cholesterol", "138 mg/dL", "< 100", "HIGH", '#dc2626'),
    ("HDL Cholesterol", "38 mg/dL", "> 40 (M)", "LOW", '#d97706'),
    ("Triglycerides", "195 mg/dL", "< 150", "HIGH", '#dc2626'),
]
for test, val, ref, status, color in results:
    draw.text((30, y), test, font=font_md, fill='#0f172a')
    draw.text((350, y), val, font=font_md, fill='#0f172a')
    draw.text((480, y), ref, font=font_sm, fill='#64748b')
    draw.text((650, y), status, font=font_md, fill=color)
    y += 26

y += 15
draw.text((30, y), "KIDNEY FUNCTION", font=font_sm, fill='#16a34a')
y += 25
results = [
    ("Serum Creatinine", "1.20 mg/dL", "0.7-1.3", "NORMAL", '#16a34a'),
    ("eGFR", "72 mL/min/1.73m²", "> 90", "MILD", '#d97706'),
    ("Urine Microalbumin", "32 mg/g", "< 30", "BORDERLINE", '#d97706'),
]
for test, val, ref, status, color in results:
    draw.text((30, y), test, font=font_md, fill='#0f172a')
    draw.text((350, y), val, font=font_md, fill='#0f172a')
    draw.text((480, y), ref, font=font_sm, fill='#64748b')
    draw.text((650, y), status, font=font_md, fill=color)
    y += 26

# Footer
y = H - 80
draw.line([(30, y), (W-30, y)], fill='#cbd5e1', width=1)
draw.text((30, y+15), "Pathologist: Dr. Lim Wei Jian (MMC: 67890)", font=font_sm, fill='#64748b')
draw.text((30, y+38), "Authorized — Reviewed for clinical interpretation", font=font_sm, fill='#64748b')

# Save
img.save("presentation/demo_lab_report.jpg", quality=85)
print(f"✓ Saved: presentation/demo_lab_report.jpg ({img.size})")

# Also save base64 for direct upload
buf = BytesIO()
img.save(buf, format='JPEG', quality=80)
b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
with open("presentation/demo_lab_report_base64.txt", "w") as f:
    f.write(b64)
print(f"✓ Saved base64: presentation/demo_lab_report_base64.txt ({len(b64)} chars)")
