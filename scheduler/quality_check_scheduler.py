"""Quality Check Scheduler - periodically run AI quality checks on new/unchecked datasets.

This scheduler runs every 10 minutes and:
1. Finds datasets without quality scores (quality_score IS NULL)
2. Runs AI-driven quality checks on them
3. Updates the quality_score and pii_categories
4. Creates alerts if quality < 70 or PII detected
"""

import datetime
import threading
import json
# pyrefly: ignore [missing-import]
from apscheduler.schedulers.background import BackgroundScheduler

from database.db_connection import fetch_all, execute, fetch_one
from utils.common import logger
from controllers.monitoring_controller import run_quality_for_dataset
from utils.email_helper import send_alert_email

_scheduler: BackgroundScheduler | None = None
_lock = threading.Lock()


def _process_unchecked_datasets():
    """Find datasets without quality scores and run AI quality checks on them."""
    try:
        # Find datasets that haven't been checked yet (quality_score IS NULL)
        unchecked = fetch_all(
            "SELECT d.* FROM datasets d "
            "WHERE d.quality_score IS NULL "
            "LIMIT 10"  # Process up to 10 per tick to avoid overload
        )

        if not unchecked:
            logger.debug("No unchecked datasets found")
            return

        logger.info("Processing %d unchecked datasets", len(unchecked))

        for dataset in unchecked:
            try:
                dataset_id = dataset["id"]

                # Skip quality checks for datasets without columns (jobs/pipelines/clusters)
                if dataset.get("column_count", 0) == 0:
                    logger.info(
                        "Skipping quality check for schema-less dataset: id=%d, name=%s (type=%s)",
                        dataset_id,
                        dataset["dataset_name"],
                        dataset.get("dataset_type"),
                    )
                    # Set default score for schema-less items
                    execute(
                        "UPDATE datasets SET quality_score=%s WHERE id=%s",
                        (75.0, dataset_id),  # Neutral score for schema-less items
                    )
                    continue

                logger.info(
                    "Running quality checks on dataset: id=%d, name=%s",
                    dataset_id,
                    dataset["dataset_name"],
                )

                # Add connector_type from connector table
                connector = fetch_one(
                    "SELECT type FROM connectors WHERE id=%s",
                    (dataset["connector_id"],),
                )
                dataset["connector_type"] = (
                    connector.get("type") if connector else "unknown"
                )

                # Run AI quality checks via controller
                run_quality_for_dataset(dataset_id)
                
            except Exception as e:
                logger.error("Error processing dataset %d: %s", dataset.get("id"), e)
                continue

    except Exception as e:
        logger.error("Quality check scheduler tick failed: %s", e)


def start():
    """Start the quality check scheduler."""
    global _scheduler
    with _lock:
        if _scheduler is not None:
            return

        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _process_unchecked_datasets,
            "interval",
            minutes=1,  # Run every 1 minute
            id="quality_check_scheduler",
        )
        _scheduler.start()
        logger.info("Quality check scheduler started (1 min interval)")


def stop():
    """Stop the quality check scheduler."""
    global _scheduler
    with _lock:
        if _scheduler:
            _scheduler.shutdown(wait=False)
            _scheduler = None
            logger.info("Quality check scheduler stopped")
