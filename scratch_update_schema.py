from database.db_connection import execute
try:
    execute("ALTER TABLE connectors ADD COLUMN industry_context TEXT")
    print("Added industry_context to connectors")
except Exception as e:
    print("Error altering connectors:", e)

try:
    execute("ALTER TABLE proposed_business_rules MODIFY COLUMN industry_type TEXT")
    print("Modified industry_type in proposed_business_rules")
except Exception as e:
    print("Error modifying proposed_business_rules:", e)
