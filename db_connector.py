"""
db_connector.py
---------------
Handles all MySQL database interactions:
  - Connecting to mediquery_db
  - Executing approved SELECT queries
  - Returning results as a Pandas DataFrame
  - Basic SQL safety validation before execution
"""

import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# ── Connection ────────────────────────────────────────────────────────────────

def get_connection():
    """
    Create and return a MySQL connection using credentials from .env
    Raises an exception if connection fails.
    """
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
    """
    Quick ping to verify DB is reachable.
    Returns (True, "Connected") or (False, error_message)
    """
    try:
        conn = get_connection()
        conn.close()
        return True, "Connected to mediquery_db successfully."
    except ConnectionError as e:
        return False, str(e)


# ── Safety Validation ─────────────────────────────────────────────────────────

# These keywords must never appear in an executable query
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT",
    "UPDATE", "CREATE", "REPLACE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "SHUTDOWN", "LOAD DATA",
]

def is_safe_query(sql: str) -> tuple[bool, str]:
    """
    Validate that the SQL query is read-only and safe to execute.
    Returns (is_safe: bool, reason: str)
    """
    sql_upper = sql.upper().strip()

    # Must start with SELECT
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."

    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word-boundary style check to avoid false positives
        if f" {keyword} " in f" {sql_upper} ":
            return False, f"Forbidden keyword detected: '{keyword}'"

    # Check for multiple statements (semicolon in middle)
    # Allow trailing semicolon only
    stripped = sql_upper.rstrip(";").strip()
    if ";" in stripped:
        return False, "Multiple SQL statements are not allowed."

    return True, "Query is safe."


# ── Execution ─────────────────────────────────────────────────────────────────

def run_query(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Execute a validated SQL query and return results as a DataFrame.

    Returns:
        (DataFrame, None)        on success
        (None,      error_msg)   on failure
    """
    # Safety check first
    safe, reason = is_safe_query(sql)
    if not safe:
        return None, f"Query blocked by safety validator: {reason}"

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)   # Returns rows as dicts
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            # Query ran fine but returned no rows
            return pd.DataFrame(), None

        df = pd.DataFrame(rows)
        return df, None

    except mysql.connector.Error as e:
        return None, f"MySQL error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


# ── Schema Inspector (used by Schema Viewer tab in UI) ────────────────────────

def get_table_preview(table_name: str, limit: int = 5) -> tuple[pd.DataFrame | None, str | None]:
    """
    Fetch a small preview of any table for the schema viewer.
    """
    # Whitelist table names to prevent injection
    allowed_tables = [
        "patients", "doctors", "departments", "appointments",
        "medical_records", "medications", "prescriptions",
        "billing", "lab_tests",
    ]
    if table_name not in allowed_tables:
        return None, f"Table '{table_name}' is not accessible."

    sql = f"SELECT * FROM {table_name} LIMIT {limit};"
    return run_query(sql)


def get_table_row_counts() -> pd.DataFrame:
    """
    Returns a DataFrame with row counts for all tables.
    Shown in the schema viewer as a summary.
    """
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