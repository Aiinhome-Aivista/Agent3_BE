"""Orchestrator Agent - Controls the workflow and triggers other agents."""

import logging
from agents.validation_agent import ValidationAgent
from agents.anomaly_agent import AnomalyAgent
from agents.compliance_agent import ComplianceAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self):
        self.validation = ValidationAgent()
        self.anomaly = AnomalyAgent()
        self.compliance = ComplianceAgent()

    def start_pipeline(self, dataset_id: int):
        """Starts the AI governance pipeline for a given dataset."""
        logger.info(f"Starting pipeline for dataset {dataset_id}")
        
        # 1. Technical Validation
        val_results = {
            "nulls": self.validation.run_null_checks(dataset_id),
            "duplicates": self.validation.run_duplicate_checks(dataset_id),
            "schema": self.validation.run_schema_checks(dataset_id)
        }
        
        # 2. Anomaly Detection
        anom_results = {
            "outliers": self.anomaly.detect_outliers(dataset_id),
            "trend": self.anomaly.detect_trend_shift(dataset_id)
        }
        
        # 3. Compliance Scan
        comp_results = {
            "pii": self.compliance.detect_pii(dataset_id)
        }
        
        return {
            "status": "success",
            "dataset_id": dataset_id,
            "validation": val_results,
            "anomalies": anom_results,
            "compliance": comp_results
        }

    def assign_agent(self, agent_name: str, payload: dict):
        """Assigns a task to a specific agent."""
        logger.info(f"Assigning task to {agent_name} with payload {payload}")
        return {"assigned_to": agent_name, "status": "processing"}

    def collect_results(self):
        """Collects results from all agents and finalizes the run."""
        logger.info("Collecting agent results...")
        return {"status": "results_collected"}
