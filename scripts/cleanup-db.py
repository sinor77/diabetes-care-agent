"""Clean all DynamoDB tables and create fresh test accounts."""
import boto3
import time

REGION = "ap-southeast-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

# Clear all tables
tables = ["diabetes-care-profiles", "diabetes-care-health-logs", "diabetes-care-referrals"]

for table_name in tables:
    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response.get("Items", [])
    print(f"Deleting {len(items)} items from {table_name}...")
    
    # Get key schema
    desc = table.key_schema
    keys = [k["AttributeName"] for k in desc]
    
    with table.batch_writer() as batch:
        for item in items:
            key = {k: item[k] for k in keys}
            batch.delete_item(Key=key)
    print(f"  ✓ {table_name} cleared")

print("\nCreating test accounts...")

# Create patient account
profiles_table = dynamodb.Table("diabetes-care-profiles")
profiles_table.put_item(Item={
    "email": "patient.test@diabetes.demo",
    "name": "Ahmed Hassan",
    "_role": "patient",
    "verified": True,
    "dtype": "Type 2",
    "age": 52,
    "sex": "male",
    "hba1c": "7.8",
    "goalHba1c": "6.5",
    "bp": "138/88",
    "weight": "89",
    "height": "175",
    "years": "8",
    "meds": "Metformin 1000mg twice daily, Glimepiride 2mg",
    "challenge": "Post-meal spikes, weight management",
    "goal": "Lower HbA1c to 6.5, lose 5kg",
    "glucose": "145",
    "ldl": "135",
    "hdl": "38",
    "triglycerides": "195",
    "egfr": "72",
    "creatinine": "1.2",
    "updated_at": int(time.time()),
})
print("  ✓ Patient account created: patient.test@diabetes.demo")

# Create doctor account
profiles_table.put_item(Item={
    "email": "doctor.test@diabetes.demo",
    "name": "Dr. Sarah Chen",
    "_role": "expert",
    "verified": True,
    "updated_at": int(time.time()),
})
print("  ✓ Doctor account created: doctor.test@diabetes.demo (verified)")

# Create health logs for the patient (simulating past 7 days)
logs_table = dynamodb.Table("diabetes-care-health-logs")
from decimal import Decimal
import random

base_time = int(time.time())
logs_data = [
    {"days_ago": 7, "hba1c": 8.1, "glucose": 165, "weight": 91, "systolic": 142, "diastolic": 90, "ldl": 142, "hdl": 36, "triglycerides": 210, "egfr": 70, "creatinine": 1.3},
    {"days_ago": 5, "hba1c": 8.0, "glucose": 155, "weight": 90.5, "systolic": 140, "diastolic": 89, "ldl": 138, "hdl": 37, "triglycerides": 200, "egfr": 71, "creatinine": 1.25},
    {"days_ago": 3, "hba1c": 7.9, "glucose": 148, "weight": 90, "systolic": 139, "diastolic": 88, "ldl": 136, "hdl": 38, "triglycerides": 198, "egfr": 71, "creatinine": 1.22},
    {"days_ago": 1, "hba1c": 7.8, "glucose": 145, "weight": 89, "systolic": 138, "diastolic": 88, "ldl": 135, "hdl": 38, "triglycerides": 195, "egfr": 72, "creatinine": 1.2},
]

for log in logs_data:
    item = {
        "email": "patient.test@diabetes.demo",
        "timestamp": base_time - (log["days_ago"] * 86400),
    }
    for k, v in log.items():
        if k != "days_ago":
            item[k] = Decimal(str(v))
    logs_table.put_item(Item=item)

print(f"  ✓ Created {len(logs_data)} health log entries (past 7 days)")

# Create a referral from patient to doctor
referrals_table = dynamodb.Table("diabetes-care-referrals")
referrals_table.put_item(Item={
    "doctorEmail": "doctor.test@diabetes.demo",
    "timestamp": base_time - 3600,
    "patientEmail": "patient.test@diabetes.demo",
    "patientName": "Ahmed Hassan",
    "message": "Hi Doctor, my blood sugar has been high lately even with medication. Can you review my recent labs?",
    "insights": "Health Score: 5/10. HbA1c trending down (8.1→7.8) but still above target. LDL high at 135. Kidney function borderline (eGFR 72).",
    "type": "referral",
})
print("  ✓ Created referral from patient to doctor")

print("\n✅ Database cleaned and test accounts ready!")
print("\n  Patient: patient.test@diabetes.demo")
print("  Doctor:  doctor.test@diabetes.demo (verified)")
print("\n  Note: You still need Cognito accounts to sign in.")
print("  Create them via the app's Sign Up flow with these emails.")
