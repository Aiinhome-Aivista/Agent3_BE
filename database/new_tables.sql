-- ========================================================
-- NEW TABLES FOR ENTERPRISE AI DATA QUALITY PLATFORM
-- ========================================================

-- 1. quarantine_records
CREATE TABLE IF NOT EXISTS quarantine_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    record_data JSON NOT NULL,
    violation_reason TEXT,
    quarantine_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'remediated', 'rejected') DEFAULT 'pending',
    remediated_by VARCHAR(255),
    remediated_at DATETIME
);

-- 2. remediation_actions
CREATE TABLE IF NOT EXISTS remediation_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_id INT NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_details JSON,
    suggested_by_ai BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    status ENUM('pending', 'approved', 'executed', 'failed') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    executed_at DATETIME
);

-- 3. business_context
CREATE TABLE IF NOT EXISTS business_context (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    domain VARCHAR(100) NOT NULL,
    business_description TEXT,
    criticality ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    owner_email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. business_rules
CREATE TABLE IF NOT EXISTS business_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_description TEXT,
    rule_logic JSON NOT NULL,
    generated_by_ai BOOLEAN DEFAULT FALSE,
    status ENUM('draft', 'active', 'inactive') DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. business_rule_approvals
CREATE TABLE IF NOT EXISTS business_rule_approvals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    approver_email VARCHAR(255) NOT NULL,
    approval_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    comments TEXT,
    approval_date DATETIME
);

-- 6. dataset_trust_scores
CREATE TABLE IF NOT EXISTS dataset_trust_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    trust_score DECIMAL(5,2) NOT NULL,
    quality_score DECIMAL(5,2),
    freshness_score DECIMAL(5,2),
    compliance_score DECIMAL(5,2),
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. pii_scan_results
CREATE TABLE IF NOT EXISTS pii_scan_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    pii_type VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,2),
    scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_masked BOOLEAN DEFAULT FALSE
);

-- 8. governance_audit_logs
CREATE TABLE IF NOT EXISTS governance_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(100) NOT NULL,
    actor_email VARCHAR(255) NOT NULL,
    target_resource VARCHAR(255),
    target_resource_id VARCHAR(100),
    action_details JSON,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 9. lineage_relationships
CREATE TABLE IF NOT EXISTS lineage_relationships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_entity_type VARCHAR(100) NOT NULL,
    source_entity_id VARCHAR(100) NOT NULL,
    target_entity_type VARCHAR(100) NOT NULL,
    target_entity_id VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 10. graph_sync_logs
CREATE TABLE IF NOT EXISTS graph_sync_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sync_status ENUM('success', 'failed', 'in_progress') DEFAULT 'in_progress',
    records_synced INT DEFAULT 0,
    error_message TEXT,
    sync_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    sync_end DATETIME
);

-- 11. watermark_tracking
CREATE TABLE IF NOT EXISTS watermark_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    dataset_id INT,
    last_processed_watermark VARCHAR(255) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 12. curated_dataset_registry
CREATE TABLE IF NOT EXISTS curated_dataset_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    certification_level ENUM('bronze', 'silver', 'gold') DEFAULT 'bronze',
    certified_by VARCHAR(255),
    certification_date DATETIME,
    business_glossary_link VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 13. ai_quality_results
CREATE TABLE IF NOT EXISTS ai_quality_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    affected_records INT DEFAULT 0,
    recommendation TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 14. business_validation_results
CREATE TABLE IF NOT EXISTS business_validation_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    rule_id INT NOT NULL,
    rule_name VARCHAR(255),
    records_affected INT DEFAULT 0,
    risk_level VARCHAR(50),
    execution_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
