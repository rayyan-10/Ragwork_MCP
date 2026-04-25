from app.mcp.registry import TOOLS
from app.utils.logger import get_logger

logger = get_logger("executor")

# Human-readable status messages per tool + result pattern
def _make_status(tool_name: str, tool_input: str, result: str) -> str:
    r = result.lower()
    if tool_name == "db_tool":
        if "error" in r:
            return f"❌ Database error occurred."
        if "create table" in tool_input.lower():
            # extract table name
            parts = tool_input.strip().split()
            tname = parts[2] if len(parts) > 2 else "table"
            return f"✅ Table `{tname}` created successfully."
        if "insert" in tool_input.lower():
            return f"✅ Record inserted successfully."
        if "select" in tool_input.lower():
            rows = [l for l in result.split("\n") if l.strip() and "---" not in l]
            count = max(0, len(rows) - 1)  # subtract header
            return f"✅ Query returned {count} row(s)."
        if "drop" in tool_input.lower():
            return f"✅ Table dropped successfully."
        return f"✅ Query executed successfully."

    if tool_name == "memory_tool":
        if "error" in r:
            return f"❌ Memory save failed."
        return f"✅ Saved to memory."

    if tool_name == "file_tool":
        if "error" in r or "not found" in r:
            return f"❌ File could not be read."
        return f"✅ File read successfully."

    if tool_name == "rag_tool":
        if "error" in r:
            return f"❌ Document search failed."
        return f"✅ Retrieved from documents."

    if tool_name == "web_tool":
        if "error" in r or "no direct results" in r:
            return f"⚠️ Web search returned limited results."
        return f"✅ Web search completed."

    if tool_name == "summary_tool":
        if "error" in r:
            return f"❌ Summarization failed."
        return f"✅ Summary generated."

    return f"✅ {tool_name} completed."


async def execute(plan: dict) -> tuple[str, list[dict]]:
    """
    Executes a plan step by step.
    Returns (final_result, tool_statuses)
    tool_statuses: list of {tool, input, status}
    """
    if not plan.get("steps"):
        return "No steps to execute.", []

    results = []
    previous_output = None
    tool_statuses = []

    for step in plan.get("steps", []):
        tool_name = step.get("tool")
        tool_input = step.get("input")

        logger.info(f"Executing: {tool_name} | Input: {tool_input}")

        if tool_name not in TOOLS:
            msg = f"Unknown tool: {tool_name}"
            logger.warning(msg)
            results.append(msg)
            tool_statuses.append({"tool": tool_name, "input": tool_input, "status": f"❌ Unknown tool: {tool_name}"})
            continue

        tool_func = TOOLS[tool_name]

        if tool_input == "previous_output":
            if previous_output is None:
                return "Error: No previous output available for chaining.", tool_statuses
            tool_input = previous_output

        if isinstance(tool_input, (list, dict)):
            tool_input = str(tool_input)

        try:
            result = await tool_func(tool_input)

            if isinstance(result, list):
                result = "\n".join([str(r) for r in result])

            status = _make_status(tool_name, tool_input, result)
            tool_statuses.append({"tool": tool_name, "input": tool_input, "status": status})

            results.append(result)
            previous_output = result
            logger.info(f"Result from {tool_name}: {str(result)[:100]}")

        except Exception as e:
            error_msg = f"Error in {tool_name}: {str(e)}"
            logger.error(error_msg)
            results.append(error_msg)
            tool_statuses.append({"tool": tool_name, "input": tool_input, "status": f"❌ {error_msg}"})

    return (results[-1] if results else "No result."), tool_statuses
