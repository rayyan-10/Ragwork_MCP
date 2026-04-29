"""
registry.py
-----------
Central tool registry for ToolPilot.
Maps tool names to their async handler functions.
Used by the executor to call the right tool for each plan step.
FastMCP handles schema discovery automatically via @mcp.tool() decorators in server.py.
"""
from app.tools.file_tool import read_file
from app.tools.summary_tool import summarize
from app.tools.rag_tool import search
from app.tools.db_tool import execute_query
from app.tools.memory_tool import save_memory, recall_memory
from app.tools.web_tool import web_search

# Maps tool names (used by planner/executor) to their async handler functions
TOOLS = {
    "file_tool":     read_file,
    "summary_tool":  summarize,
    "rag_tool":      search,
    "db_tool":       execute_query,
    "memory_tool":   save_memory,
    "recall_memory": recall_memory,
    "web_tool":      web_search,
}
