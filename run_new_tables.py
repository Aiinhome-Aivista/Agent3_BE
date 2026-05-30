import os
from database.db_connection import get_connection

def run_sql_file(filename):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            with open(filename, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon, but this might be naive if there are semicolons in strings.
            # However, for simple CREATE TABLE statements, it works.
            statements = sql_content.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    print(f"Executing: {stmt[:50]}...")
                    cur.execute(stmt)
        conn.commit()
        print("Success")
    finally:
        conn.close()

if __name__ == "__main__":
    run_sql_file('database/new_tables.sql')
