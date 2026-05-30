from fastapi import APIRouter
from database.db_connection import execute, fetch_one
from utils.jwt_helper import hash_password

router = APIRouter(prefix="/api/system", tags=["system"])

@router.post("/setup_demo")
def setup_demo():
    # 1. Clear existing data and create new tables if needed
    execute("CREATE TABLE IF NOT EXISTS business_rules (id INT AUTO_INCREMENT PRIMARY KEY, dataset_id INT, rule_name VARCHAR(255), rule_logic TEXT, status VARCHAR(50))")
    execute("DELETE FROM business_rules")
    execute("DELETE FROM alerts")
    execute("DELETE FROM monitoring_runs")
    execute("DELETE FROM monitoring_jobs")
    execute("DELETE FROM datasets")
    execute("DELETE FROM connectors")
    execute("DELETE FROM users WHERE username IN ('data_engineer', 'data_steward', 'business_analyst', 'compliance_officer', 'business_user')")

    # 2. Insert Users
    users_to_add = [
        ("data_engineer", "de@example.com", hash_password("pass123"), "admin"),
        ("data_steward", "ds@example.com", hash_password("pass123"), "steward"),
        ("business_analyst", "ba@example.com", hash_password("pass123"), "viewer"),
        ("compliance_officer", "co@example.com", hash_password("pass123"), "viewer"),
        ("business_user", "bu@example.com", hash_password("pass123"), "viewer")
    ]
    for u, e, p, r in users_to_add:
        execute("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)", (u, e, p, r))

    # 3. Insert Connectors
    execute("INSERT INTO connectors (id, name, type, status) VALUES (1, 'MySQL', 'Database', 'Connected')")
    execute("INSERT INTO connectors (id, name, type, status) VALUES (2, 'MSSQL', 'Database', 'Connected')")
    execute("INSERT INTO connectors (id, name, type, status) VALUES (3, 'ADF', 'Pipeline', 'Connected')")
    execute("INSERT INTO connectors (id, name, type, status) VALUES (4, 'Databricks', 'Compute', 'Connected')")

    # 4. Insert Datasets
    execute("INSERT INTO datasets (id, connector_id, dataset_name, pii_percentage) VALUES (100, 1, 'bronze_customers', 5)")
    execute("INSERT INTO datasets (id, connector_id, dataset_name, pii_percentage) VALUES (101, 2, 'bronze_claims', 0)")

    # 5. Insert Alerts
    execute(
        "INSERT INTO alerts (dataset_id, connector_id, title, severity, category, status) VALUES "
        "(101, 4, 'Abnormal Claim Amount Detected: 95 Lakh', 'critical', 'Anomaly', 'open')"
    )
    execute(
        "INSERT INTO alerts (dataset_id, connector_id, title, severity, category, status) VALUES "
        "(100, 4, 'Aadhaar Missing (125 Records)', 'high', 'Data Quality', 'open')"
    )

    # 6. Insert Activity
    execute(
        "INSERT INTO monitoring_runs (connector_id, dataset_id, status, run_type) VALUES "
        "(3, 100, 'success', 'Data Ingestion (MySQL to ADLS)')"
    )

    # 7. Insert Business Rules
    execute("INSERT INTO business_rules (dataset_id, rule_name, rule_logic, status) VALUES (101, 'High Risk Claim', 'Claim > 5 lakh = High Risk', 'pending')")
    execute("INSERT INTO business_rules (dataset_id, rule_name, rule_logic, status) VALUES (101, 'Age Restriction', 'Age < 18 cannot have corporate policy', 'pending')")
    execute("INSERT INTO business_rules (dataset_id, rule_name, rule_logic, status) VALUES (101, 'Fraud Risk', 'Multiple claims within 7 days = Fraud Risk', 'pending')")

    return {"message": "Demo data perfectly seeded into MySQL!"}
