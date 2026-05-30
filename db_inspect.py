import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", 3306)),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", "root123"),
    database=os.getenv("MYSQL_NAME", "enterprise_dq_sentinel"),
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("TABLES:")
        for t in tables:
            table_name = list(t.values())[0]
            print(f"- {table_name}")
            
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print("  Columns:", ", ".join([c['Field'] for c in columns]))
            
            # Print a sample row
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            row = cursor.fetchone()
            print(f"  Sample row: {row}")
        
finally:
    conn.close()
