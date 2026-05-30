from fastapi import APIRouter
from agents.remediation_agent import RemediationAgent
from database.db_connection import fetch_all, execute

router = APIRouter(prefix="/remediation", tags=["Remediation Workflow"])
remediation_agent = RemediationAgent()

@router.get("/issues/{dataset_id}")
def get_issues(dataset_id: int):
    # Fetch issues that need remediation from ai_quality_results
    issues = fetch_all("SELECT * FROM ai_quality_results WHERE dataset_id=%s ORDER BY id DESC", (dataset_id,))
    return {"status": "success", "data": issues}

@router.post("/suggest/{issue_id}")
def suggest_fix(issue_id: int):
    issue = fetch_all("SELECT * FROM ai_quality_results WHERE id=%s", (issue_id,))
    if not issue:
        return {"status": "error", "message": "Issue not found"}
    
    suggestion = remediation_agent.suggest_fix(issue[0])
    
    # Store the suggested fix in remediation_actions
    action_id = execute(
        "INSERT INTO remediation_actions (alert_id, action_type, suggested_by_ai) VALUES (%s, %s, True)",
        (issue_id, suggestion.get("suggested_fix", "Move Invalid Records to Quarantine"))
    )
    
    return {"status": "success", "data": {"action_id": action_id, "suggestion": suggestion.get("suggested_fix")}}

@router.post("/execute/{action_id}")
def execute_fix(action_id: int):
    # Change status to executed
    execute("UPDATE remediation_actions SET status='executed', executed_at=NOW() WHERE id=%s", (action_id,))
    return {"status": "success", "message": "Remediation fix executed successfully."}
