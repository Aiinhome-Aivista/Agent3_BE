from fastapi import APIRouter
from agents.business_rule_agent import BusinessRuleAgent
from database.db_connection import fetch_all, execute

router = APIRouter(prefix="/business", tags=["Business Analyst"])
business_agent = BusinessRuleAgent()

@router.post("/context/{dataset_id}")
def add_context(dataset_id: int, context: str):
    return {"message": "Add business context", "dataset_id": dataset_id, "context": context}

@router.post("/rules/generate/{dataset_id}")
def generate_rules(dataset_id: int, context: str = ""):
    # Use the AI agent to generate rules
    res = business_agent.generate_rules(dataset_id, context)
    generated_rules = res.get("generated_rules", [])
    
    # Save drafted rules to DB
    for rule in generated_rules:
        execute(
            "INSERT INTO business_rules (dataset_id, rule_name, rule_logic, generated_by_ai, status) VALUES (%s, %s, %s, True, 'draft')",
            (dataset_id, rule["rule_name"], rule["rule_logic"])
        )

    # Fetch them back to return
    rules_db = fetch_all("SELECT * FROM business_rules WHERE dataset_id=%s AND status='draft' ORDER BY id DESC LIMIT %s", (dataset_id, len(generated_rules)))
    
    rules = []
    for r in rules_db:
        rules.append({
            "id": r["id"],
            "rule_name": r["rule_name"],
            "rule_logic": r["rule_logic"],
            "status": r["status"]
        })
    return {
        "status": "success",
        "data": {
            "generated_rules": rules
        }
    }

@router.post("/rules/approve/{rule_id}")
def approve_rules(rule_id: int):
    execute("UPDATE business_rules SET status='active' WHERE id=%s", (rule_id,))
    return {"message": "Rule approved", "rule_id": rule_id, "status": "active"}

@router.post("/rules/reject/{rule_id}")
def reject_rules(rule_id: int):
    execute("UPDATE business_rules SET status='inactive' WHERE id=%s", (rule_id,))
    return {"message": "Rule rejected", "rule_id": rule_id, "status": "inactive"}

@router.post("/validation/run/{dataset_id}")
def run_validation(dataset_id: int):
    # Fetch approved rules for dataset
    approved_rules = fetch_all("SELECT * FROM business_rules WHERE dataset_id=%s AND status='active'", (dataset_id,))
    
    # Execute rules and store results in business_validation_results
    results = []
    for rule in approved_rules:
        # Mocking the execution logic for the demo
        affected = 10 if "Email" in rule["rule_name"] else 5
        risk = "High" if "Risk" in rule["rule_name"] else "Medium"
        
        execute(
            "INSERT INTO business_validation_results (dataset_id, rule_id, rule_name, records_affected, risk_level) VALUES (%s, %s, %s, %s, %s)",
            (dataset_id, rule["id"], rule["rule_name"], affected, risk)
        )
        
        results.append({
            "rule_name": rule["rule_name"],
            "records_affected": affected,
            "risk_level": risk
        })
        
    return {"status": "success", "message": "Business validation executed", "data": results}

@router.get("/validation/results/{dataset_id}")
def get_business_results(dataset_id: int):
    results = fetch_all("SELECT * FROM business_validation_results WHERE dataset_id=%s ORDER BY id DESC", (dataset_id,))
    return {"status": "success", "data": results}
