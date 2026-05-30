"""Rule book controller — upload triggers automatic quality scan across all
datasets of the matching connector type. No jobs, no manual triggers."""

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks

from database.db_connection import fetch_all, fetch_one, execute
from middleware.auth_middleware import get_current_user
from utils.common import logger
from utils.vector_helper import add_rule_book_to_index, delete_rule_book_from_index

router = APIRouter(prefix="/api/rule-books", tags=["rulebooks"])


# Connector-type normalization
_TYPE_TO_RULEBOOK = {
    "azure_adf": "ADF", "adf": "ADF",
    "mysql": "MYSQL", "mssql": "MSSQL",
    "databricks": "DATABRICKS", "github": "GITHUB",
}
_RULEBOOK_TO_DB_TYPE = {
    "ADF": "azure_adf", "MYSQL": "mysql", "MSSQL": "mssql",
    "DATABRICKS": "databricks", "GITHUB": "github",
}
_VALID_RULEBOOK_TYPES = {"ADF", "MYSQL", "MSSQL", "DATABRICKS", "GITHUB"}


def normalize_connector_type(ctype: str) -> str:
    if not ctype:
        return ""
    return _TYPE_TO_RULEBOOK.get(ctype.strip().lower(), ctype.strip().upper())


def db_connector_type(rulebook_type: str) -> str:
    """Convert rulebook type (ADF) → DB connector type (azure_adf)."""
    return _RULEBOOK_TO_DB_TYPE.get(rulebook_type.upper(), rulebook_type.lower())


def collection_name(ctype: str) -> str:
    return f"{normalize_connector_type(ctype).lower()}_rulebook"


# ======================================================================
#  UPLOAD — triggers automatic quality scan in background
# ======================================================================
@router.post("/create")
def upload_rulebook(
    background: BackgroundTasks,
    # connector_type: str = Form(...),
    connector_type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    # ctype = normalize_connector_type(connector_type)
    # if ctype not in _VALID_RULEBOOK_TYPES:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Invalid connector type. Use one of: {sorted(_VALID_RULEBOOK_TYPES)}",
    #     )

    # ==========================================================
    # AUTO-DETECT CONNECTOR TYPE FROM FILE CONTENT
    # ==========================================================

    raw = file.file.read()

    try:
        content = raw.decode("utf-8")

    except UnicodeDecodeError:
        content = raw.decode("latin-1", errors="ignore")


    if not connector_type:

        sample = content[:5000].lower()

        if any(x in sample for x in [
            "adf",
            "pipeline",
            "linkedservice",
            "integrationruntime",
            "datafactory"
        ]):
            connector_type = "ADF"

        elif any(x in sample for x in [
            "databricks",
            "delta",
            "notebook",
            "cluster",
            "spark"
        ]):
            connector_type = "DATABRICKS"

        elif any(x in sample for x in [
            "mysql",
            "innodb",
            "varchar",
            "auto_increment"
        ]):
            connector_type = "MYSQL"

        elif any(x in sample for x in [
            "mssql",
            "sql server",
            "nvarchar",
            "dbo."
        ]):
            connector_type = "MSSQL"

        elif any(x in sample for x in [
            "github",
            "workflow",
            "actions",
            ".yml"
        ]):
            connector_type = "GITHUB"

        else:
            connector_type = "MYSQL"  

    ctype = normalize_connector_type(connector_type)

    if ctype not in _VALID_RULEBOOK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid connector type. Use one of: {sorted(_VALID_RULEBOOK_TYPES)}",
        )
    
    if not content.strip():
        raise HTTPException(status_code=400, detail="File content is empty")

    rb_id = execute(
        "INSERT INTO rulebook (connector_type, rulebook_name, rulebook_content, created_at) "
        "VALUES (%s, %s, %s, %s)",
        (ctype, file.filename, content, datetime.datetime.utcnow()),
    )

    # Graph DB Integration (ArangoDB First)
    from utils.graph_helper import graph_db
    from utils.ai_helper import extract_rules_from_rulebook
    try:
        extraction_data = extract_rules_from_rulebook(content)
        summary = extraction_data.get("rulebook_summary", "Rulebook uploaded.")
        graph_db.insert_rulebook(rb_id, file.filename, content, summary)
        
        extracted_rules = extraction_data.get("extracted_rules", [])
        for i, rule in enumerate(extracted_rules):
            rule_id = rule.get("rule_id") or f"R_{rb_id}_{i}"
            rule_text = rule.get("rule_text", "")
            
            if rule_text:
                graph_db.insert_rule(rule_id, rb_id, rule_text)
                
        logger.info("Graph DB insert successful for rulebook %s with %d rules", rb_id, len(extracted_rules))
    except Exception as ge:
        logger.error("Graph DB insert failed for rulebook %s: %s", rb_id, ge)
        # Continuing even if graph fails, as per original logic

    # Index into Vector DB (ChromaDB Second)
    try:
        add_rule_book_to_index(
            text=content, rule_book_id=rb_id, name=file.filename,
            metadata={
                "rulebook_id": rb_id, "connector_type": ctype,
                "uploaded_by": user.get("id") or user.get("user_id"),
                "created_at":  datetime.datetime.utcnow().isoformat(),
            }
        )
        logger.info("Rulebook %s indexed in %s", rb_id, collection_name(ctype))
    except TypeError:
        try:
            add_rule_book_to_index(text=content, rule_book_id=rb_id, name=file.filename,
                                   metadata={"connector_type": ctype, "rulebook_id": rb_id})
        except Exception as e:
            logger.warning("ChromaDB index failed (compat): %s", e)
    except Exception as e:
        logger.exception("ChromaDB index failed — rolling back DB row")
        execute("DELETE FROM rulebook WHERE id=%s", (rb_id,))
        raise HTTPException(status_code=500, detail=f"Index failed: {str(e)[:120]}")

    # AUTO-TRIGGER: scan all datasets of this connector type
    db_type = db_connector_type(ctype)
    from controllers.monitoring_controller import run_quality_for_connector_type
    background.add_task(run_quality_for_connector_type, db_type, rb_id)
    logger.info(
        "Auto-triggered quality scan for connector_type=%s after rulebook %s upload",
        db_type, rb_id,
    )

    rb = fetch_one("SELECT * FROM rulebook WHERE id=%s", (rb_id,))
    return {
        **rb,
        "scan_triggered": True,
        "message": f"Rulebook uploaded. Quality scan started for all {ctype} datasets.",
    }


# ======================================================================
#  LIST — single GET API
# ======================================================================
@router.get("")
def list_rulebooks(user: dict = Depends(get_current_user)):
    return fetch_all(
        "SELECT id, connector_type, rulebook_name, rulebook_content, created_at "
        "FROM rulebook ORDER BY created_at DESC"
    )


# ======================================================================
#  DELETE
# ======================================================================
@router.delete("/{rulebook_id}")
def delete_rulebook(rulebook_id: int, user: dict = Depends(get_current_user)):
    row = fetch_one("SELECT id, connector_type FROM rulebook WHERE id=%s", (rulebook_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Rulebook not found")
    execute("DELETE FROM rulebook WHERE id=%s", (rulebook_id,))
    try:
        delete_rule_book_from_index(rule_book_id=rulebook_id)
    except TypeError:
        try:
            delete_rule_book_from_index(rulebook_id)
        except Exception as e:
            logger.warning("Chroma delete failed: %s", e)
    except Exception as e:
        logger.warning("Chroma delete failed: %s", e)
    return {"status": "success"}


# ======================================================================
#  HELPER — used by monitoring
# ======================================================================
def get_latest_rulebook(connector_type: str) -> Optional[dict]:
    ctype = normalize_connector_type(connector_type)
    return fetch_one(
        "SELECT id, connector_type, rulebook_name, rulebook_content, created_at "
        "FROM rulebook WHERE connector_type=%s "
        "ORDER BY created_at DESC LIMIT 1",
        (ctype,),
    )


# ======================================================================
#  PROPOSED BUSINESS RULES
# ======================================================================
@router.get("/proposed")
def list_proposed_rules(user: dict = Depends(get_current_user)):
    """Fetch all proposed business rules with their connector names and statuses."""
    return fetch_all(
        "SELECT p.*, c.name as connector_name, s.status_name "
        "FROM proposed_business_rules p "
        "LEFT JOIN connectors c ON p.connector_id = c.id "
        "LEFT JOIN status_master s ON p.status_id = s.id "
        "ORDER BY p.created_at DESC"
    )

from pydantic import BaseModel
class ProposedRuleCreate(BaseModel):
    connector_id: int
    rule_text: str
    rule_type: str

@router.post("/proposed")
def create_proposed_rule(
    body: ProposedRuleCreate,
    user: dict = Depends(get_current_user)
):
    """Manually create a new proposed business rule."""
    # Find the industry_type for this connector (either from connector table if it has it, or just use a default/existing)
    row = fetch_one("SELECT industry_type FROM proposed_business_rules WHERE connector_id=%s LIMIT 1", (body.connector_id,))
    industry = row["industry_type"] if row else "Custom"

    execute(
        "INSERT INTO proposed_business_rules (connector_id, industry_type, rule_text, rule_type, status_id) VALUES (%s, %s, %s, %s, 1)",
        (body.connector_id, industry, body.rule_text, body.rule_type)
    )
    return {"status": "success"}

class ProposedRuleUpdate(BaseModel):
    rule_text: str
    status_id: int

@router.put("/proposed/{rule_id}")
def update_proposed_rule(
    rule_id: int, 
    body: ProposedRuleUpdate, 
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Update rule text or status (e.g., approve/reject)."""
    row = fetch_one("SELECT id, connector_id FROM proposed_business_rules WHERE id=%s", (rule_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Proposed rule not found")
    
    execute(
        "UPDATE proposed_business_rules SET rule_text=%s, status_id=%s, updated_at=%s WHERE id=%s",
        (body.rule_text, body.status_id, datetime.datetime.now(datetime.timezone.utc), rule_id)
    )

    # If approved (status_id = 2), automatically trigger the data quality scan for this connector
    if body.status_id == 2:
        from controllers.connector_controller import run_scan
        print(f"========== DEBUG: Rule approved, triggering run_scan for connector {row['connector_id']} ==========")
        background_tasks.add_task(run_scan, row["connector_id"])

    return {"status": "success"}