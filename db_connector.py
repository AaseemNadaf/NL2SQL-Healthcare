import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT",
    "UPDATE", "CREATE", "REPLACE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "SHUTDOWN", "LOAD DATA",
]

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "mediquery_db"),
        )
        return conn
    except mysql.connector.Error as e:
        raise ConnectionError(f"Could not connect to MySQL: {e}")


def test_connection():
    try:
        conn = get_connection()
        conn.close()
        return True, "Connected to mediquery_db successfully."
    except ConnectionError as e:
        return False, str(e)


def is_safe_query(sql: str) -> tuple[bool, str]:
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    for keyword in FORBIDDEN_KEYWORDS:
        if f" {keyword} " in f" {sql_upper} ":
            return False, f"Forbidden keyword detected: '{keyword}'"
    stripped = sql_upper.rstrip(";").strip()
    if ";" in stripped:
        return False, "Multiple SQL statements are not allowed."
    return True, "Query is safe."


def run_query(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    safe, reason = is_safe_query(sql)
    if not safe:
        return None, f"Query blocked: {reason}"
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            return pd.DataFrame(), None
        return pd.DataFrame(rows), None
    except mysql.connector.Error as e:
        return None, f"MySQL error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def get_table_preview(table_name: str, limit: int = 5) -> tuple[pd.DataFrame | None, str | None]:
    allowed_tables = [
        "patients", "doctors", "departments", "appointments",
        "medical_records", "medications", "prescriptions",
        "billing", "lab_tests",
    ]
    if table_name not in allowed_tables:
        return None, f"Table '{table_name}' is not accessible."
    return run_query(f"SELECT * FROM {table_name} LIMIT {limit};")


def get_table_row_counts() -> pd.DataFrame:
    tables = [
        "patients", "doctors", "departments", "appointments",
        "medical_records", "medications", "prescriptions",
        "billing", "lab_tests",
    ]
    counts = []
    for table in tables:
        df, err = run_query(f"SELECT COUNT(*) as count FROM {table};")
        if df is not None and not df.empty:
            counts.append({"Table": table, "Row Count": int(df["count"].iloc[0])})
        else:
            counts.append({"Table": table, "Row Count": "Error"})
    return pd.DataFrame(counts)