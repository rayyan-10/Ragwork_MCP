"""
client.py
---------
MCP client for ToolPilot's Streamlit UI.
Connects to the FastMCP server via SSE and calls tools over the MCP protocol.
Provides synchronous wrappers (run_agent, run_upload) for use in Streamlit.
"""
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = "http://localhost:8000/sse"


async def call_agent(query: str, history: list[dict] | None = None) -> tuple[dict, str, list[dict]]:
    """
    Connects to the ToolPilot MCP server via SSE and calls the 'agent' tool.
    Returns (plan, result, tool_statuses).
    """
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.call_tool("agent", {
                "input": query,
                "history": json.dumps(history or [])
            })

            raw = response.content[0].text
            data = json.loads(raw)
            return data.get("plan", {}), data.get("result", ""), data.get("statuses", [])


def run_agent(query: str, history: list[dict] | None = None) -> tuple[dict, str, list[dict]]:
    """Synchronous wrapper for use in Streamlit."""
    return asyncio.run(call_agent(query, history))


async def call_upload(filename: str, content_b64: str) -> str:
    """Calls the upload_document MCP tool."""
    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.call_tool("upload_document", {
                "filename": filename,
                "content_b64": content_b64
            })
            return response.content[0].text


def run_upload(filename: str, content_b64: str) -> str:
    """Synchronous wrapper for use in Streamlit."""
    return asyncio.run(call_upload(filename, content_b64))
