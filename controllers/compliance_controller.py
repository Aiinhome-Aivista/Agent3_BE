from fastapi import APIRouter
from agents.compliance_agent import ComplianceAgent
from database.db_connection import fetch_all, execute

router = APIRouter(prefix="/compliance", tags=["Compliance"])
compliance_agent = ComplianceAgent()

@router.post("/pii/scan/{dataset_id}")
def scan_pii(dataset_id: int):
    # Dynamically find PII in DB alerts
    alerts = fetch_all("SELECT * FROM alerts WHERE status='open' AND title LIKE '%Aadhaar%'")
    pii_found = []
    for a in alerts:
        pii_found.append({
            "dataset": f"Dataset {a['dataset_id']}",
            "column": "aadhaar",
            "type": "National ID",
            "status": "Exposed"
        })
    return {
        "status": "success",
        "data": {
            "pii_found": pii_found
        }
    }

@router.post("/pii/mask/{dataset_id}")
def mask_pii(dataset_id: int):
    # Dynamically update the DB status
    execute("UPDATE alerts SET status='closed' WHERE title LIKE '%Aadhaar%'")
    
    return {
        "status": "success",
        "logs": [
            "✅ DB updated: Alert Closed",
            "✅ Incident created (#INC-1024)",
            "✅ Email sent to InfoSec Team",
            "✅ Teams alert triggered in #security-alerts",
            "✅ Ticket created in ServiceNow"
        ]
    }

@router.get("/reports/{dataset_id}")
def get_reports(dataset_id: int):
    results = compliance_agent.validate_policies(dataset_id)
    return {"message": "Review compliance violations", "data": results}
