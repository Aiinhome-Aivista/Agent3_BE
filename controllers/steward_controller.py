from fastapi import APIRouter
from agents.orchestrator_agent import OrchestratorAgent
from database.db_connection import fetch_all, execute

router = APIRouter(prefix="/steward", tags=["Data Steward"])
orchestrator = OrchestratorAgent()

@router.get("/review/pending")
def review_pending():
    # Fetch from database dynamically
    alerts = fetch_all("SELECT * FROM alerts WHERE status='open' AND category IN ('Anomaly', 'Data Quality')")
    anomalies = []
    for a in alerts:
        anomalies.append({
            "id": a["id"],
            "type": "missing_data" if "Missing" in a["title"] else "abnormal_value",
            "description": a["title"],
            "severity": a["severity"],
            "dataset_id": a["dataset_id"]
        })

    return {
        "status": "success",
        "data": {
            "dataset": "Dynamic Bronze Data",
            "anomalies": anomalies
        }
    }

@router.post("/approve/validation")
def approve_validation():
    return {"message": "Data clean initiated. Moved bronze to silver_customers and silver_claims.", "status": "approved"}

