from app.tools.file_tool import read_file
from app.tools.summary_tool import summarize
from app.tools.rag_tool import search
from app.tools.db_tool import execute_query
from app.tools.memory_tool import save_memory
from app.tools.web_tool import web_search

# Tool registry — maps tool names (used by planner) to their async functions
TOOLS = {
    "file_tool": read_file,
    "summary_tool": summarize,
    "rag_tool": search,
    "db_tool": execute_query,
    "memory_tool": save_memory,
    "web_tool": web_search,       # ✅ Fixed: was "web_search", planner uses "web_tool"
}

# Tool metadata for MCP schema
TOOL_SCHEMAS = [
    {
        "name": "file_tool",
        "description": "Reads a local text file and returns its content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Relative file path, e.g. data/sample.txt"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "summary_tool",
        "description": "Summarizes a given text into 2-3 concise sentences using an LLM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Text to summarize"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "rag_tool",
        "description": "Retrieves relevant information from local documents using semantic search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Search query, e.g. 'machine learning'"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "db_tool",
        "description": "Executes queries against the Supabase database (users and memories tables).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "SQL-style query, e.g. SELECT * FROM users"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "memory_tool",
        "description": "Saves a piece of information to persistent memory in Supabase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Text to remember, e.g. 'AI is powerful'"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "web_tool",
        "description": "Searches the web for latest information, news, or real-time queries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Search query, e.g. 'latest AI news'"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "agent",
        "description": "Runs the full ToolPilot agent pipeline — planner selects tools and executor runs them automatically.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Natural language query"},
                "history": {"type": "array", "description": "Recent conversation history", "items": {"type": "object"}}
            },
            "required": ["input"]
        }
    },
]
