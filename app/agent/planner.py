from app.tools.llm_tool import generate_response
import json

async def plan_task(user_input: str, history: list[dict] | None = None):
    # Build recent conversation context (last 3 exchanges)
    context_block = ""
    if history:
        recent = history[-6:]  # last 3 user+agent pairs
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Agent"
            content = str(msg.get("content", ""))[:300]  # cap length
            lines.append(f"{role}: {content}")
        if lines:
            context_block = "Recent conversation:\n" + "\n".join(lines) + "\n\n"

    prompt = f"""
You are an intelligent AI agent planner.

Your job is to analyze the user task and select the most appropriate tool(s).

{context_block}Available tools:
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

2. Use file_tool ONLY when:
   → the user explicitly mentions "file", "read file", or "summarize file"

3. summary_tool should ONLY be used:
   → after file_tool OR after web_tool OR when explicitly asked to summarize
   → NEVER use summary_tool after db_tool
   → NEVER use summary_tool after memory_tool
   → NEVER use summary_tool after rag_tool
   → If the user provides text directly in the message and asks to summarize it,
     use summary_tool with that exact text as input (NOT "previous_output")

4. NEVER pass "previous_output" into rag_tool
   → rag_tool input must always be a clean query (e.g., "AI")

5. Use memory_tool ONLY when storing information

6. Use db_tool ONLY for database-related queries

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