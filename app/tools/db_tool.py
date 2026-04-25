import sqlite3
import os
import re
from app.config.settings import DB_PATH
from app.utils.logger import get_logger

logger = get_logger("db_tool")

SQL_KEYWORDS = {"select", "insert", "update", "delete", "create", "drop", "alter"}


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _is_sql(text: str) -> bool:
    """Returns True if the input looks like a SQL query."""
    first_word = text.strip().split()[0].lower() if text.strip() else ""
    return first_word in SQL_KEYWORDS


def _get_schema() -> str:
    """Reads all table schemas from the SQLite DB and returns as a readable string."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return "No tables exist yet."

        schema_parts = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = cursor.fetchall()
            col_defs = ", ".join([f"{c[1]} ({c[2]})" for c in cols])
            schema_parts.append(f"Table '{table}': {col_defs}")

        conn.close()
        return "\n".join(schema_parts)
    except Exception:
        return "Could not read schema."


def _friendly_error(query: str, raw_error: str) -> str:
    """Converts raw SQLite errors into helpful, human-readable messages."""
    e = raw_error.lower()

    if "no such table" in e:
        table = raw_error.split("no such table:")[-1].strip()
        return (f"❌ Table '{table}' does not exist.\n"
                f"💡 Tip: Create it first — e.g. CREATE TABLE {table} (id INTEGER, name TEXT)")

    if "syntax error" in e:
        if "near \"table\"" in e:
            return (f"❌ 'table' is a reserved SQL keyword and can't be used as a table name.\n"
                    f"💡 Tip: Use your actual table name, e.g. INSERT INTO student VALUES (...)")
        return (f"❌ SQL syntax error: {raw_error}\n"
                f"💡 Tip: Check your query. Example: INSERT INTO student VALUES (1, 'John', 25)")

    if "has" in e and "columns but" in e:
        return (f"❌ Column count mismatch: {raw_error}\n"
                f"💡 Tip: The number of values must match the number of columns in the table.")

    if "unique constraint" in e or "unique" in e:
        return (f"❌ Duplicate entry — a record with this value already exists.\n"
                f"💡 Tip: Use a different primary key or unique value.")

    if "not null constraint" in e:
        return (f"❌ A required field is missing a value.\n"
                f"💡 Tip: Provide values for all NOT NULL columns.")

    if "no such column" in e:
        col = raw_error.split("no such column:")[-1].strip()
        return (f"❌ Column '{col}' does not exist in the table.\n"
                f"💡 Tip: Check column names using SELECT * FROM your_table.")

    return f"❌ Database error: {raw_error}"


async def execute_query(query: str) -> str:
    """
    Accepts either a raw SQL query or a natural language database request.
    If natural language is detected, converts it to SQL using the LLM first.
    Returns a readable string result.
    """
    query = query.strip()

    # ── Natural language → SQL conversion ────────────────────────────────────
    if not _is_sql(query):
        logger.info(f"Natural language detected, converting to SQL: {query}")
        from app.tools.llm_tool import generate_sql
        schema = _get_schema()
        logger.info(f"Schema passed to LLM:\n{schema}")
        query = await generate_sql(query, schema)
        # Strip markdown code fences and sql prefix
        query = re.sub(r"```(?:sql)?", "", query, flags=re.IGNORECASE).strip("`").strip()
        # Take only the first statement if LLM returns multiple lines
        query = query.split(";")[0].strip() + ";"
        query = query.rstrip(";").strip()  # SQLite doesn't need trailing semicolon via cursor.execute
        logger.info(f"Generated SQL: {query}")

    # ── Execute SQL ───────────────────────────────────────────────────────────
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.commit()

        if cursor.description:
            cols = [desc[0] for desc in cursor.description]
            if rows:
                header = " | ".join(cols)
                divider = "-" * len(header)
                body = "\n".join([" | ".join(str(v) for v in row) for row in rows])
                return f"{header}\n{divider}\n{body}"
            else:
                return "Query executed successfully. No rows returned."
        else:
            return "Query executed successfully."

    except Exception as e:
        raw = str(e)
        logger.error(f"DB error: {raw}")
        return _friendly_error(query, raw)
    finally:
        conn.close()
