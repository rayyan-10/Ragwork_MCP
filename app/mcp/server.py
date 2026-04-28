import asyncio
import json
from mcp.server.fastmcp import FastMCP

from app.mcp.registry import TOOLS, TOOL_SCHEMAS
from app.agent.planner import plan_task
from app.agent.executor import execute
from app.utils.logger import get_logger

logger = get_logger("mcp-server")

# ── FastMCP server instance ───────────────────────────────────────────────────
mcp = FastMCP("toolpilot", host="0.0.0.0", port=8000)


# ── Individual tools ──────────────────────────────────────────────────────────

@mcp.tool()
async def file_tool(input: str) -> str:
    """Reads a local text file and returns its content."""
    return await TOOLS["file_tool"](input)


@mcp.tool()
async def summary_tool(input: str) -> str:
    """Summarizes a given text into 2-3 concise sentences using an LLM."""
    return await TOOLS["summary_tool"](input)


@mcp.tool()
async def rag_tool(input: str) -> str:
    """Retrieves relevant information from local documents using semantic search."""
    return await TOOLS["rag_tool"](input)


@mcp.tool()
async def db_tool(input: str) -> str:
    """Executes natural language or SQL queries against the local SQLite database."""
    return await TOOLS["db_tool"](input)


@mcp.tool()
async def memory_tool(input: str) -> str:
    """Saves a piece of information to persistent local memory."""
    return await TOOLS["memory_tool"](input)


@mcp.tool()
async def web_tool(input: str) -> str:
    """Searches the web for latest information or real-time queries."""
    return await TOOLS["web_tool"](input)


@mcp.tool()
async def upload_document(filename: str, content_b64: str) -> str:
    """
    Uploads a document (PDF, DOCX, TXT) to the knowledge base and rebuilds the RAG index.
    content_b64 must be base64-encoded file bytes.
    Returns status message.
    """
    import base64
    from app.tools.rag_tool import save_uploaded_document, rebuild_index

    try:
        content = base64.b64decode(content_b64)
        is_duplicate, message = save_uploaded_document(filename, content)
        if not is_duplicate:
            rebuild_index()
            return f"✅ {message} Knowledge base updated."
        return f"ℹ️ {message}"
    except Exception as e:
        return f"❌ Upload failed: {str(e)}"


@mcp.tool()
async def agent(input: str, history: str = "[]") -> str:
    """
    Runs the full ToolPilot agent pipeline.
    Planner selects the right tools and executor runs them automatically.
    history should be a JSON string of recent conversation messages.
    """
    try:
        history_list = json.loads(history) if history else []
    except Exception:
        history_list = []

    try:
        plan = await plan_task(input, history=history_list)
        result, tool_statuses = await execute(plan)
        return json.dumps({
            "result": str(result),
            "plan": plan,
            "statuses": tool_statuses
        })
    except Exception as e:
        return json.dumps({
            "result": f"Agent error: {str(e)}",
            "plan": {},
            "statuses": []
        })


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting ToolPilot MCP Server on http://localhost:8000")
    mcp.run(transport="sse")
