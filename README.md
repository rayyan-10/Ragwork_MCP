# 🧭 ToolPilot

> **Intelligent Workflow Automation Agent built on Model Context Protocol (MCP)**

ToolPilot is a multi-tool AI agent that accepts natural language queries, automatically selects the right tool, and returns accurate responses — all through a professional Streamlit chat interface connected to a real MCP server over SSE transport.

---

## Overview

Traditional AI assistants are limited to a single capability. ToolPilot solves this by implementing an **agent planner** that reads your query, decides which tool(s) to use, and chains them together automatically. You don't need to know which tool handles what — just ask naturally.

**Example interactions:**
- *"What is reinforcement learning?"* → searches your documents
- *"Create a table named Employee with id, name, salary"* → executes SQL
- *"Summarize the latest AI news"* → web search + summarization
- *"Remember: Python is the best language"* → saves to memory
- *"Show all records in Employee table"* → queries database

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (ui.py)                  │
│              MCP Client over SSE Transport               │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP SSE
                           ▼
┌─────────────────────────────────────────────────────────┐
│              FastMCP Server (port 8000)                  │
│                  app/mcp/server.py                       │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │     Agent Pipeline      │
              │  planner → executor     │
              └────────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼          ▼       ▼       ▼          ▼
   rag_tool   db_tool  memory  file_tool  web_tool
   (FAISS)   (SQLite)  (JSON)   (local)  (DuckDuckGo)
```

**Request flow:**
1. User sends a query from the Streamlit chat
2. MCP client sends it to the FastMCP server via SSE
3. The `agent` tool is invoked on the server
4. Planner (LLM) analyzes the query + conversation history + available docs
5. Executor runs each planned tool step, chaining outputs if needed
6. Result + per-tool status indicators returned to the UI

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
│   │   ├── rag_tool.py       # FAISS vector search over local/uploaded documents
│   │   ├── db_tool.py        # SQLite queries with NL-to-SQL conversion
│   │   ├── memory_tool.py    # Persistent memory stored in JSON
│   │   ├── file_tool.py      # Read/write local files
│   │   ├── summary_tool.py   # LLM-based text summarization
│   │   ├── web_tool.py       # DuckDuckGo web search
│   │   └── llm_tool.py       # LLM API calls (response, RAG answers, SQL generation)
│   ├── utils/
│   │   └── logger.py         # Shared logger factory for all modules
│   └── main.py               # Agent pipeline entry point
├── data/
│   ├── documents/            # Knowledge base — add .txt, .pdf, .docx files here
│   ├── database.db           # SQLite database (auto-created on first use)
│   ├── memory.json           # Persistent memory store (auto-created on first use)
│   └── sample.txt            # Sample file for file_tool testing
├── ui.py                     # Streamlit chat UI (MCP client)
├── requirements.txt          # Python dependencies
├── .env                      # API keys (not committed to git)
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

---

## Setup

### Prerequisites
- Python 3.10 or higher
- A free Groq API key from [console.groq.com](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/toolpilot.git
cd toolpilot
```

### 2. Create and activate virtual environment
```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS / Linux
python -m venv env
source env/bin/activate
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

---

## Running the Application

ToolPilot requires **two terminals** running simultaneously.

### Terminal 1 — Start the MCP Server
```bash
python -m app.mcp.server
```
Expected output:
```
[HH:MM:SS] INFO mcp-server: Starting ToolPilot MCP Server on http://localhost:8000
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Start the Streamlit UI
```bash
streamlit run ui.py --server.fileWatcherType none
```
Then open `http://localhost:8501` in your browser.

> The `--server.fileWatcherType none` flag suppresses harmless warnings from the `transformers` package watcher.

---

## Available Tools

| Tool | Trigger | Description |
|------|---------|-------------|
| `rag_tool` | Knowledge questions, document queries | Semantic search over local/uploaded documents using FAISS. Answers are LLM-generated from retrieved chunks. Long answers are auto-summarized. |
| `db_tool` | Database operations | Accepts natural language or raw SQL. Supports CREATE, INSERT, SELECT, UPDATE, DELETE, table inspection, and existence checks. Uses LLM for NL-to-SQL conversion. |
| `memory_tool` | "Store/remember/save this..." | Saves text entries with timestamp and auto-tag to a persistent JSON memory file. Prevents duplicate entries. |
| `recall_memory` | "Show my memories / what did I store..." | Searches and retrieves previously saved memories by keyword. Use "all" to list everything. |
| `file_tool` | "Read the file / summarize the file" | Reads local text files from the `data/` folder. |
| `summary_tool` | "Summarize this: ..." | Summarizes any provided text into 2–3 concise sentences using the LLM. |
| `web_tool` | "Latest news / current events" | Searches the web via DuckDuckGo Instant Answer API. |

---

## Document Upload

Upload PDF, DOCX, or TXT files directly from the sidebar in the UI.

- Supported formats: `.pdf`, `.docx`, `.txt`
- Files are saved to `data/documents/`
- The FAISS index is automatically rebuilt after each new upload
- **Duplicate detection**: files with identical content (MD5 hash) are skipped — no re-indexing needed
- The active document name is shown in the sidebar after upload
- After uploading, ask questions naturally: *"What does this document say about X?"*

---

## Database Usage

The `db_tool` understands natural language — no SQL knowledge required:

```
"Create a table named Student with columns id, name, age, grade"
"Add a student: id 1, name Alice, age 20, grade A"
"Show all students"
"How many students are in the table?"
"Is there a table named Employee?"
"List all tables"
"Describe the Student table"
"Delete the student with id 3"
```

Raw SQL also works directly:
```sql
SELECT * FROM Student WHERE age > 18
INSERT INTO Student (id, name, age, grade) VALUES (2, 'Bob', 22, 'B')
```

---

## Memory Usage

Save any information for later reference:

```
"Remember: The project deadline is May 15"
"Store this: Python version 3.12 is being used"
"Save: API rate limit is 30 requests per minute"
```

Retrieve stored memories:

```
"Show all my memories"
"What did I store about Python?"
"List memories"
```

Each memory entry is saved with:
- A unique ID
- Timestamp of when it was stored
- Auto-assigned category tag (`ai`, `database`, `document`, `web`, `general`)
- Duplicate prevention — same content won't be stored twice

> **Note:** `memory_tool` is for saving information. `recall_memory` is for retrieving what you previously saved. If you ask a question like *"What are the types of memory in AI?"* — that is a knowledge question and will be answered from documents via `rag_tool`, not from your stored memories.

---

## Conversation Context

The planner retains the last 3 conversation exchanges (6 messages) as context. This enables:

- *"Store the above answer"* → saves the previous agent response
- *"Summarize what you just said"* → summarizes the last response
- *"Insert the same record again with id 5"* → knows what record was previously discussed

---

## Planner Intelligence

The planner uses a few smart shortcuts before calling the LLM:

- **Summarize fast-path**: if your message ends with "summarize this", "summarize this content", "summarize the above" etc., it immediately routes to `summary_tool` without LLM routing
- **Document awareness**: the planner reads the `data/documents/` folder live on every query, so it knows which documents are available and prefers `rag_tool` for relevant topics
- **DB fast-path**: common DB queries (list tables, describe table, check existence, count records) are handled directly without LLM SQL generation

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq API — Llama 3.1 8B Instant |
| MCP Framework | `mcp[cli]` — FastMCP with SSE transport |
| Vector Search | FAISS (CPU) + sentence-transformers (`all-MiniLM-L6-v2`) |
| Database | SQLite (local, zero-config) |
| UI | Streamlit |
| Server | Uvicorn + Starlette (via FastMCP) |
| PDF Parsing | pypdf |
| DOCX Parsing | python-docx |
| HTTP Client | httpx (async) |
| Web Search | DuckDuckGo Instant Answer API |

---

## Dependencies

```
groq                  # LLM API client
mcp[cli]              # Model Context Protocol SDK with SSE support
faiss-cpu             # Vector similarity search
sentence-transformers # Text embeddings for RAG
python-dotenv         # .env file loading
httpx                 # Async HTTP client for web search
streamlit             # Chat UI
uvicorn               # ASGI server
starlette             # Web framework (used by FastMCP)
pypdf                 # PDF text extraction
python-docx           # DOCX text extraction
```

Install all at once:
```bash
pip install -r requirements.txt
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key for LLM access |

---

## Known Limitations

- `web_tool` uses DuckDuckGo Instant Answers which works well for factual queries but may return limited results for news or trending topics
- RAG accuracy depends on document quality and chunk coverage — very specific factual queries may miss if the answer spans multiple chunks
- The SQLite database is local only — data does not persist across machines
- Memory is stored as a flat JSON file — no querying or filtering capability

---

## Git Setup

```bash
git init
git add .
git commit -m "Initial commit - ToolPilot MCP Agent"
git remote add origin https://github.com/yourusername/toolpilot.git
git branch -M main
git push -u origin main
```

> `.env` and `data/database.db` and `data/memory.json` are excluded via `.gitignore` — they will not be pushed.

---

## License

MIT License — free to use, modify, and distribute.
