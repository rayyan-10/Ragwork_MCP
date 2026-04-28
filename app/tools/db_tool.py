import sqlite3
import os
import re
from app.config.settings import DB_PATH
from app.utils.logger import get_logger

logger = get_logger("db_tool")

SQL_KEYWORDS = {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _is_sql(text: str) -> bool:
    """Returns True only if the input is a complete, valid SQL statement."""
    t = text.strip().upper()
    first_word = t.split()[0] if t.split() else ""
    if first_word not in SQL_KEYWORDS:
        return False
    if first_word == "SELECT" and "FROM" not in t:
        return False
    if first_word == "INSERT" and ("INTO" not in t or "VALUES" not in t):
        return False
    if first_word == "CREATE" and "TABLE" not in t:
        return False
    if first_word == "DROP" and "TABLE" not in t:
        return False
    if first_word == "UPDATE" and "SET" not in t:
        return False
    if first_word == "DELETE" and "FROM" not in t:
        return False
    return True


def _get_all_tables() -> list[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def _get_schema() -> str:
    """Returns full schema of all tables as readable string."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        if not tables:
            conn.close()
            return "No tables exist yet."
        parts = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = cursor.fetchall()
            col_defs = ", ".join([f"{c[1]} ({c[2] or 'TEXT'})" for c in cols])
            parts.append(f"Table '{table}': {col_defs}")
        conn.close()
        return "\n".join(parts)
    except Exception:
        return "Could not read schema."


def _format_rows(cursor) -> str:
    """Formats query results as a readable table string."""
    rows = cursor.fetchall()
    if not rows:
        return "No records found."
    cols = [desc[0] for desc in cursor.description]
    col_widths = [max(len(str(col)), max((len(str(row[i])) for row in rows), default=0))
                  for i, col in enumerate(cols)]
    header = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(cols))
    divider = "-+-".join("-" * w for w in col_widths)
    body = "\n".join(
        " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(cols)))
        for row in rows
    )
    return f"{header}\n{divider}\n{body}\n\n({len(rows)} record{'s' if len(rows) != 1 else ''} found)"


def _friendly_error(query: str, raw_error: str) -> str:
    e = raw_error.lower()
    if "no such table" in e:
        table = raw_error.split("no such table:")[-1].strip()
        return (f"❌ Table '{table}' does not exist.\n"
                f"💡 Tip: Create it first — e.g. CREATE TABLE {table} (id INTEGER, name TEXT)")
    if "syntax error" in e:
        return (f"❌ SQL syntax error: {raw_error}\n"
                f"💡 Tip: Check your query format.")
    if "has" in e and "columns but" in e:
        return (f"❌ Column count mismatch: {raw_error}\n"
                f"💡 Tip: Number of values must match number of columns.")
    if "unique constraint" in e:
        return "❌ Duplicate entry — a record with this value already exists."
    if "not null constraint" in e:
        return "❌ A required field is missing a value."
    if "no such column" in e:
        col = raw_error.split("no such column:")[-1].strip()
        return (f"❌ Column '{col}' does not exist.\n"
                f"💡 Tip: Check column names using SELECT * FROM your_table.")
    return f"❌ Database error: {raw_error}"


def _handle_nl_directly(q: str) -> str | None:
    """
    Handles common NL DB queries directly without LLM.
    Returns a string result or None if LLM conversion is needed.
    """
    ql = q.lower().strip().rstrip("?")

    # ── List all tables ───────────────────────────────────────────────────────
    if any(p in ql for p in ["list all tables", "show all tables", "what tables",
                               "all tables", "list tables", "show tables",
                               "tables in database", "tables exist"]):
        tables = _get_all_tables()
        if not tables:
            return "No tables found in the database."
        return "Tables in database:\n" + "\n".join(f"  • {t}" for t in tables)

    # ── Table existence check ─────────────────────────────────────────────────
    if "table" in ql and any(p in ql for p in ["exist", "already", "is there",
                                                 "do we have", "have a table",
                                                 "created", "available"]):
        tables = _get_all_tables()
        # Try to find table name mentioned in query
        for t in tables:
            if t.lower() in ql:
                return f"✅ Yes, table '{t}' exists in the database."
        # Check if any word in query matches a table name (case-insensitive)
        words = re.findall(r'\b\w+\b', q)
        for word in words:
            for t in tables:
                if word.lower() == t.lower():
                    return f"✅ Yes, table '{t}' exists in the database."
        # No match found
        return f"❌ No matching table found. Available tables: {', '.join(tables) if tables else 'none'}"

    # ── Describe / show structure of a table ─────────────────────────────────
    if any(p in ql for p in ["describe", "structure of", "columns in",
                               "schema of", "fields in", "show columns",
                               "what columns", "properties of"]):
        tables = _get_all_tables()
        for t in tables:
            if t.lower() in ql:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({t})")
                    cols = cursor.fetchall()
                    conn.close()
                    if not cols:
                        return f"Table '{t}' exists but has no columns."
                    col_info = "\n".join(
                        f"  • {c[1]} ({c[2] or 'TEXT'})"
                        + (" [NOT NULL]" if c[3] else "")
                        + (" [PK]" if c[5] else "")
                        for c in cols
                    )
                    return f"Structure of table '{t}':\n{col_info}"
                except Exception as ex:
                    return f"Error reading table structure: {str(ex)}"
        return f"Please specify a table name. Available: {', '.join(tables) if tables else 'none'}"

    # ── Show/display/get all records ──────────────────────────────────────────
    if any(p in ql for p in ["show all", "display all", "get all", "fetch all",
                               "show the table", "display the table",
                               "show records", "all records", "all data",
                               "show data", "display data"]):
        tables = _get_all_tables()
        for t in tables:
            if t.lower() in ql:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {t}")
                    result = _format_rows(cursor)
                    conn.close()
                    return result
                except Exception as ex:
                    return f"Error: {str(ex)}"
        # If only one table exists, show it
        if len(tables) == 1:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {tables[0]}")
                result = _format_rows(cursor)
                conn.close()
                return f"Showing table '{tables[0]}':\n{result}"
            except Exception as ex:
                return f"Error: {str(ex)}"
        if tables:
            return f"Please specify which table. Available: {', '.join(tables)}"
        return "No tables found in the database."

    # ── Count records ─────────────────────────────────────────────────────────
    if any(p in ql for p in ["how many", "count", "number of records",
                               "total records", "number of rows"]):
        tables = _get_all_tables()
        for t in tables:
            if t.lower() in ql:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {t}")
                    count = cursor.fetchone()[0]
                    conn.close()
                    return f"Table '{t}' has {count} record{'s' if count != 1 else ''}."
                except Exception as ex:
                    return f"Error: {str(ex)}"

    return None  # Fall through to LLM conversion


async def execute_query(query: str) -> str:
    """
    Accepts natural language or raw SQL.
    Handles all DB-related queries intelligently.
    """
    query = query.strip()

    # ── Try direct NL handling first ──────────────────────────────────────────
    if not _is_sql(query):
        direct = _handle_nl_directly(query)
        if direct is not None:
            return direct

        # Fall through to LLM-based SQL generation
        logger.info(f"Converting to SQL via LLM: {query}")
        from app.tools.llm_tool import generate_sql
        schema = _get_schema()
        sql = await generate_sql(query, schema)
        sql = re.sub(r"```(?:sql)?", "", sql, flags=re.IGNORECASE).strip("`").strip()
        sql = sql.split(";")[0].strip()
        logger.info(f"Generated SQL: {sql}")
        query = sql

    # ── Execute SQL ───────────────────────────────────────────────────────────
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()

        if cursor.description:
            result = _format_rows(cursor)
        else:
            result = "Query executed successfully."

        conn.close()
        return result

    except Exception as e:
        raw = str(e)
        logger.error(f"DB error: {raw}")
        try:
            conn.close()
        except Exception:
            pass
        return _friendly_error(query, raw)
