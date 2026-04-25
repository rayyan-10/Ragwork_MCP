import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

from app.mcp.registry import TOOLS, TOOL_SCHEMAS
from app.agent.planner import plan_task
from app.agent.executor import execute

# Initialize MCP server
app = Server("toolpilot")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """MCP tool discovery — returns all tools with schemas."""
    return [
        Tool(
            name=schema["name"],
            description=schema["description"],
            inputSchema=schema["inputSchema"]
        )
        for schema in TOOL_SCHEMAS
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """MCP tool execution — calls a single tool directly."""
    if name not in TOOLS:
        return [TextContent(type="text", text=f"Error: Tool '{name}' not found.")]

    tool_input = arguments.get("input", "")

    try:
        result = await TOOLS[name](tool_input)
        # Normalize result to string
        if isinstance(result, list):
            result = "\n".join([str(r) for r in result])
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]


async def run_agent_query(query: str) -> str:
    """Helper to run full planner + executor pipeline."""
    plan = await plan_task(query)
    result = await execute(plan)
    if isinstance(result, list):
        result = "\n".join([str(r) for r in result])
    return str(result)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
