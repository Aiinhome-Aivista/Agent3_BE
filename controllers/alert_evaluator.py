import json
from database.db_connection import execute
from utils.common import logger

def evaluate_and_create_alerts(dataset_id: int, ds: dict, quality_score: float, py_result: dict, llm_report: dict):
    # Create alerts if needed
    if quality_score < 85:
        # Quality alert
        severity = py_result.get("severity", "medium")
        alert_title = f"Quality issues on {ds['dataset_name']} (score {quality_score})"
        failed_rules = py_result.get("failed_rules", [])
        summary = llm_report.get("executive_summary", "Check completed")
        alert_msg = f"Score: {quality_score}\nSummary: {summary}\n"
        if failed_rules:
            alert_msg += "Failed Rules: " + "; ".join([f"{r.get('rule_type') or r.get('rule')}: {r.get('reason')}" for r in failed_rules[:3]])

        recs = llm_report.get("recommendations", [])
        recs_str = "\n".join(recs) if isinstance(recs, list) else str(recs)

        try:
            alert_id = execute(
                "INSERT INTO alerts (connector_id, dataset_id, category, severity, title, message, status, ai_recommendation) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    ds["connector_id"],
                    dataset_id,
                    "quality",
                    severity,
                    alert_title,
                    alert_msg,
                    "open",
                    recs_str,
                ),
            )
            logger.info("Created quality alert for dataset %d (ID: %s)", dataset_id, alert_id)
            
            try:
                from utils.graph_helper import graph_db
                graph_db.insert_alert(alert_id, alert_title, alert_msg, dataset_id)
                for r in failed_rules:
                    rule_name = r.get("rule_type") or r.get("rule")
                    if rule_name:
                        graph_db.insert_rule(rule_name, 0, f"Rule: {rule_name}")
                        graph_db.create_edge("VIOLATES", f"Alert/{alert_id}", f"Rule/{rule_name}")
            except Exception as ge:
                logger.error("Graph DB alert insert failed: %s", ge)

            try:
                from utils.escalation_engine import start_incident_escalation
                start_incident_escalation(
                    alert_id=alert_id,
                    category="quality",
                    severity=severity,
                    dataset_id=dataset_id,
                    connector_id=ds["connector_id"]
                )
            except Exception as ne:
                logger.error("Escalation trigger failed for quality alert %s: %s", alert_id, ne)
        except Exception as e:
            logger.warning("Failed to create quality alert: %s", e)

    pii_categories = py_result.get("pii_columns", [])
    # Create PII alert if PII detected
    if pii_categories:
        alert_title = f"PII detected in {ds['dataset_name']}"
        alert_msg = f"Detected PII categories: {', '.join(pii_categories)}"

        recs = llm_report.get("recommendations", [])
        recs_str = "\n".join(recs) if isinstance(recs, list) else str(recs)

        try:
            alert_id = execute(
                "INSERT INTO alerts (connector_id, dataset_id, category, severity, title, message, status, ai_recommendation) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    ds["connector_id"],
                    dataset_id,
                    "pii",
                    "high",
                    alert_title,
                    alert_msg,
                    "open",
                    recs_str,
                ),
            )
            logger.info("Created PII alert for dataset %d (ID: %s)", dataset_id, alert_id)
            
            try:
                from utils.graph_helper import graph_db
                graph_db.insert_alert(alert_id, alert_title, alert_msg, dataset_id)
                for pii_cat in pii_categories:
                    graph_db.insert_rule(pii_cat, 0, f"PII Category: {pii_cat}")
                    graph_db.create_edge("VIOLATES", f"Alert/{alert_id}", f"Rule/{pii_cat}")
            except Exception as ge:
                logger.error("Graph DB PII alert insert failed: %s", ge)

            try:
                from utils.escalation_engine import start_incident_escalation
                start_incident_escalation(
                    alert_id=alert_id,
                    category="pii",
                    severity="high",
                    dataset_id=dataset_id,
                    connector_id=ds["connector_id"]
                )
            except Exception as ne:
                logger.error("Escalation trigger failed for PII alert %s: %s", alert_id, ne)
        except Exception as e:
            logger.warning("Failed to create PII alert: %s", e)
