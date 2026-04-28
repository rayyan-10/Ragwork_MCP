from app.tools.llm_tool import generate_response
from app.config.settings import DOCS_PATH
import os
import json

def _get_uploaded_docs() -> str:
    """Returns a list of currently available documents in the knowledge base."""
    try:
        files = [f for f in os.listdir(DOCS_PATH)
                 if f.lower().endswith((".txt", ".pdf", ".docx"))]
        if files:
            return "Documents currently in knowledge base: " + ", ".join(files)
    except Exception:
        pass
    return ""

async def plan_task(user_input: str, history: list[dict] | None = None):
    # Build recent conversation context (last 3 exchanges)
    context_block = ""
    if history:
        recent = history[-6:]
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Agent"
            content = str(msg.get("content", ""))[:300]
            lines.append(f"{role}: {content}")
        if lines:
            context_block = "Recent conversation:\n" + "\n".join(lines) + "\n\n"

    # ── Fast-path: if user ends with summarize intent, always use summary_tool ──
    stripped = user_input.strip().lower()
    summarize_triggers = [
        "summarize this", "summarize this content", "summarize the above",
        "summarize it", "give a summary", "make a summary", "summarize this text"
    ]
    for trigger in summarize_triggers:
        if stripped.endswith(trigger) or stripped == trigger:
            # Extract the content before the trigger phrase
            idx = stripped.rfind(trigger)
            content_to_summarize = user_input[:idx].strip()
            if not content_to_summarize:
                content_to_summarize = user_input
            return {
                "steps": [
                    {"tool": "summary_tool", "input": content_to_summarize[:3000]}
                ]
            }

    # Build document awareness block
    docs_block = _get_uploaded_docs()
    if docs_block:
        docs_block = f"{docs_block}\n→ For ANY query about topics that may be covered in these documents, ALWAYS use rag_tool first.\n\n"

    prompt = f"""
You are an intelligent AI agent planner.

Your job is to analyze the user task and select the most appropriate tool(s).

{context_block}{docs_block}Available tools:
- file_tool (reads file, input: file path like "data/sample.txt")
- summary_tool (summarizes text)
- rag_tool (retrieves information from documents)
- db_tool (executes SQL queries)
- memory_tool (stores information)
- web_tool (latest info / internet queries)

Task:
{user_input}

Return ONLY valid JSON.
Do NOT include markdown, backticks, or explanations.

Format:
{{
  "steps": [
    {{"tool": "tool_name", "input": "input_data"}}
  ]
}}

Tool selection rules (STRICT):

1. If the task asks about:
   - definitions (e.g., "what is AI")
   - explanations
   - general concepts
   - known topics

   → ALWAYS use rag_tool ONLY
   → NEVER use web_tool for these

   BUT if the user also says "summarize", "brief", "short", "concise", "in short", "summarized way":
   → use rag_tool THEN summary_tool

2. Use file_tool ONLY when:
   → the user explicitly mentions "file", "read file", or "summarize file"

3. summary_tool should ONLY be used:
   → after file_tool OR after web_tool OR when explicitly asked to summarize
   → NEVER use summary_tool after db_tool
   → NEVER use summary_tool after memory_tool
   → NEVER use summary_tool after rag_tool (rag_tool already summarizes internally)
   → If the user provides text directly in the message and asks to summarize it,
     use summary_tool with that exact text as input (NOT "previous_output")

4. NEVER pass "previous_output" into rag_tool
   → rag_tool input must always be a clean query (e.g., "AI")

5. Use memory_tool ONLY when storing information.
   → If the user says "store this", "remember this", "save this", "store the above", or similar
     WITHOUT providing explicit content, look at the Recent conversation and extract the last
     Agent response as the input to memory_tool.
   → NEVER store the user's instruction itself — store the actual content they are referring to.

6. Use db_tool ONLY for database-related queries.
   → NEVER add web_tool or any other tool after db_tool
   → db_tool is self-contained — one step only
   → Use db_tool for ANY of these:
     - creating, dropping, altering tables
     - inserting, updating, deleting records
     - selecting/querying data
     - checking if a table exists
     - listing all tables
     - asking about database structure or schema
     - any question containing words like "table", "record", "database", "column", "row", "insert", "query"

7. If the task asks about:
   - latest information
   - current events
   - news
   - recent updates
   - real-time or internet-based queries
   → ALWAYS use web_tool ONLY

8. Use web_tool + summary_tool when:
   - the user asks for summarized latest information

General Guidelines:
- Prefer the simplest plan (minimum steps)
- Do NOT invent file names, database tables, or inputs
- Avoid unnecessary chaining
- Use "previous_output" only when chaining outputs between tools

Examples:

Task: summarize the file
{{
  "steps": [
    {{"tool": "file_tool", "input": "data/sample.txt"}},
    {{"tool": "summary_tool", "input": "previous_output"}}
  ]
}}

Task: give me a short summary of the file content
{{
  "steps": [
    {{"tool": "file_tool", "input": "data/sample.txt"}},
    {{"tool": "summary_tool", "input": "previous_output"}}
  ]
}}

Task: what is AI in a summarized way
{{
  "steps": [
    {{"tool": "rag_tool", "input": "AI"}},
    {{"tool": "summary_tool", "input": "previous_output"}}
  ]
}}

Task: is there already a table name as House?
{{
  "steps": [
    {{"tool": "db_tool", "input": "is there already a table name as House?"}}
  ]
}}

Task: what tables exist in the database?
{{
  "steps": [
    {{"tool": "db_tool", "input": "list all tables"}}
  ]
}}

Task: what does the document say about AI
{{
  "steps": [
    {{"tool": "rag_tool", "input": "AI"}}
  ]
}}

Task: explain machine learning from documents
{{
  "steps": [
    {{"tool": "rag_tool", "input": "machine learning"}}
  ]
}}

Task: store this info "AI is powerful"
{{
  "steps": [
    {{"tool": "memory_tool", "input": "AI is powerful"}}
  ]
}}

Task: store this sentence in the memory
(Recent conversation shows Agent said: "Artificial Intelligence involves simulating human intelligence in machines.")
{{
  "steps": [
    {{"tool": "memory_tool", "input": "Artificial Intelligence involves simulating human intelligence in machines."}}
  ]
}}

Task: latest AI news
{{
  "steps": [
    {{"tool": "web_tool", "input": "latest AI news"}}
  ]
}}

Task: summarize latest AI news
{{
  "steps": [
    {{"tool": "web_tool", "input": "latest AI news"}},
    {{"tool": "summary_tool", "input": "previous_output"}}
  ]
}}

Task: "AI is transforming industries." summarize this
{{
  "steps": [
    {{"tool": "summary_tool", "input": "AI is transforming industries."}}
  ]
}}

Task: summarize this text: "Machine learning enables systems to learn from data."
{{
  "steps": [
    {{"tool": "summary_tool", "input": "Machine learning enables systems to learn from data."}}
  ]
}}
"""

    response = await generate_response(prompt)

    try:
        return json.loads(response)

    except Exception as e:
        print("⚠️ Planner output not valid JSON:\n", response)

        # ✅ Safe fallback
        return {
            "steps": [
                {"tool": "rag_tool", "input": user_input}
            ]
        }