# 🧭 ToolPilot

**Intelligent Workflow Automation Agent built on Model Context Protocol (MCP)**

ToolPilot accepts natural language queries, automatically selects the right tool, and returns accurate responses — all through a professional Streamlit chat interface connected to a real MCP server.

---

## Project Structure

```
TOOL_PILOT/
├── app/
│   ├── agent/
│   │   ├── planner.py        # LLM-based task planner — decides which tools to use
│   │   └── executor.py       # Executes the plan step by step, handles tool chaining
│   ├── config/
│   │   └── settings.py       # Environment variables and path constants
│   ├── mcp/
│   │   ├── server.py         # FastMCP server — exposes tools via SSE transport
│   │   ├── client.py         # MCP client — connects Streamlit UI to the server
│   │   └── registry.py       # Tool registry and MCP-compliant tool schemas
│   ├── tools/
│   │   ├── rag_tool.py       # FAISS vector search over local documents
│   │   ├── db_tool.py        # SQLite queries with NL-to-SQL conversion
│   │   ├── memory_tool.py    # Persistent memory stored in JSON
│   │   ├── file_tool.py      # Read/write local files
│   │   ├── summary_tool.py   # LLM-based text summarization
│   │   ├── web_tool.py       # DuckDuckGo web search
│   │   └── llm_tool.py       # Groq LLM API calls (response, RAG, SQL generation)
│   ├── utils/
│   │   └── logger.py         # Shared logger factory
│   └── main.py               # Agent pipeline entry point
├── data/
│   ├── documents/            # Knowledge base — add .txt, .pdf, .docx files here
│   ├── database.db           # SQLite database (auto-created)
│   ├── memory.json           # Persistent memory store (auto-created)
│   └── sample.txt            # Sample file for file_tool testing
├── ui.py                     # Streamlit chat UI (MCP client)
├── requirements.txt          # Python dependencies
└── .env                      # API keys (not committed to git)
```

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/toolpilot.git
cd toolpilot
```

### 2. Create and activate virtual environment
```bash
python -m venv env
env\Scripts\activate        # Windows
source env/bin/activate     # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```
Get your free Groq API key at [console.groq.com](https://console.groq.com)

---

## Running the Application

ToolPilot requires two processes running simultaneously.

### Terminal 1 — Start the MCP Server
```bash
python -m app.mcp.server
```
Server starts at `http://localhost:8000`

### Terminal 2 — Start the Streamlit UI
```bash
streamlit run ui.py --server.fileWatcherType none
```
UI opens at `http://localhost:8501`

---

## How It Works

```
User Query (natural language)
        ↓
   MCP Client (ui.py)
        ↓  SSE over HTTP
   MCP Server (server.py)
        ↓
   Planner (LLM decides tools)
        ↓
   Executor (runs tools in order)
        ↓
   Tool (rag_tool / db_tool / etc.)
        ↓
   Result → back to UI
```

1. User types a query in the Streamlit chat
2. The MCP client sends it to the FastMCP server via SSE
3. The planner (LLM) analyzes the query and selects the appropriate tool(s)
4. The executor runs each tool step, chaining outputs if needed
5. The result is returned to the UI with tool status indicators

---

## Available Tools

| Tool | Description | Example Query |
|------|-------------|---------------|
| `rag_tool` | Semantic search over uploaded documents | "What is machine learning?" |
| `db_tool` | Natural language SQLite queries | "Create a table named Student with id, name, age" |
| `memory_tool` | Save information to persistent memory | "Remember: Python is great" |
| `file_tool` | Read local text files | "Read the sample file" |
| `summary_tool` | Summarize any text | "Summarize this: ..." |
| `web_tool` | DuckDuckGo web search | "Latest AI news" |

---

## Document Upload

Upload PDF, DOCX, or TXT files directly from the sidebar. The RAG tool will automatically index the content and answer questions from it. Duplicate files (same content) are detected by MD5 hash and skipped.

---

## Database Usage

The `db_tool` supports natural language — no SQL knowledge required:
- "Create a table named Employee with columns id, name, salary"
- "Add a new employee: John, age 28, salary 50000"
- "Show all employees"
- "Is there a table named Student?"
- "List all tables"

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]` | Model Context Protocol SDK |
| `groq` | LLM API (Llama 3.1) |
| `faiss-cpu` | Vector similarity search |
| `sentence-transformers` | Text embeddings for RAG |
| `streamlit` | Chat UI |
| `uvicorn` + `starlette` | ASGI server for MCP SSE |
| `pypdf` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `httpx` | Async HTTP client |
| `python-dotenv` | Environment variable loading |
