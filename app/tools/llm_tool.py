from groq import Groq
from app.config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

async def generate_response(prompt: str):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def generate_rag_response(query: str, context: list):
    context_text = "\n".join(context)

    prompt = f"""
You are an AI assistant.

Use ONLY the context below to answer the question.

Context:
{context_text}

Question:
{query}

Answer clearly:
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You answer based only on provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

async def generate_sql(natural_language: str, schema_info: str) -> str:
    """
    Converts a natural language database request into a valid SQLite SQL query.
    Returns ONLY the raw SQL string, nothing else.
    """
    prompt = f"""You are a SQLite SQL expert. Convert the user request into a single valid SQLite SQL statement.

Current database schema:
{schema_info}

STRICT RULES:
- Output ONLY the raw SQL. No markdown, no backticks, no explanation, no comments.
- For CREATE TABLE: use INTEGER for numeric columns, TEXT for string columns.
  Example: CREATE TABLE Employee (id INTEGER, name TEXT, age INTEGER, dept TEXT)
- For INSERT: always specify column names explicitly.
  Example: INSERT INTO Employee (id, name, age, dept) VALUES (1, 'John', 25, 'IT')
- For SELECT: use SELECT * FROM tablename unless specific columns are requested.
- For DROP: use DROP TABLE IF EXISTS tablename
- If the user says "with columns id, name, age" → include all those columns in CREATE TABLE.
- Never use reserved words (like "table", "select", "from") as table or column names.
- If the request is incomplete or ambiguous, generate the most reasonable SQL based on context.

User request: {natural_language}

SQL:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a SQL generator. Output only a single raw SQLite SQL statement. No markdown, no backticks, no explanation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()
