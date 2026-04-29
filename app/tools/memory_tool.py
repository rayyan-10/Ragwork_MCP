"""
memory_tool.py
--------------
Advanced persistent memory for ToolPilot.
Stores entries with timestamps, auto-tags, and supports keyword-based recall.
Memory is persisted in data/memory.json and survives across sessions.
"""
import json
import os
from datetime import datetime
from app.config.settings import MEMORY_PATH
from app.utils.logger import get_logger

logger = get_logger("memory_tool")

# ── Auto-tagging keywords ─────────────────────────────────────────────────────
_TAG_RULES = {
    "database": ["table", "sql", "insert", "select", "record", "column", "db"],
    "document": ["document", "pdf", "file", "rag", "upload", "text"],
    "web":      ["news", "latest", "search", "web", "internet", "current"],
    "ai":       ["ai", "machine learning", "nlp", "model", "llm", "neural"],
    "general":  [],  # fallback
}


def _auto_tag(content: str) -> str:
    """Assigns a category tag based on content keywords."""
    content_lower = content.lower()
    for tag, keywords in _TAG_RULES.items():
        if any(kw in content_lower for kw in keywords):
            return tag
    return "general"


def _load() -> list[dict]:
    """Loads all memory entries, normalizing any legacy formats."""
    try:
        with open(MEMORY_PATH, "r") as f:
            raw = json.load(f)

        normalized = []
        for i, item in enumerate(raw):
            # Already in new format
            if isinstance(item, dict) and "content" in item and "timestamp" in item:
                normalized.append(item)
            # Old dict with only 'content'
            elif isinstance(item, dict) and "content" in item:
                normalized.append({
                    "id": i + 1,
                    "content": item["content"],
                    "tag": _auto_tag(item["content"]),
                    "timestamp": "legacy"
                })
            # Old dict with 'task' key
            elif isinstance(item, dict) and "task" in item:
                normalized.append({
                    "id": i + 1,
                    "content": item["task"],
                    "tag": _auto_tag(item["task"]),
                    "timestamp": "legacy"
                })
            # Plain string
            elif isinstance(item, str):
                # Skip JSON strings that are error messages or noise
                content = item.strip().strip('"')
                if content and not content.startswith("{"):
                    normalized.append({
                        "id": i + 1,
                        "content": content,
                        "tag": _auto_tag(content),
                        "timestamp": "legacy"
                    })

        return normalized
    except Exception:
        return []


def _save(data: list[dict]) -> None:
    """Persists memory entries to the JSON file."""
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


async def save_memory(entry: str) -> str:
    """
    Saves a new memory entry with timestamp and auto-tag.
    Prevents duplicate entries with identical content.
    """
    try:
        data = _load()

        # Duplicate check — skip if same content already stored
        existing_contents = [m.get("content", "").strip().lower() for m in data if isinstance(m, dict)]
        if entry.strip().lower() in existing_contents:
            return f"ℹ️ Already in memory: \"{entry}\""

        record = {
            "id": len(data) + 1,
            "content": entry,
            "tag": _auto_tag(entry),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        data.append(record)
        _save(data)  # saves normalized data going forward

        logger.info(f"Memory saved [{record['tag']}]: {entry}")
        return f"✅ Saved to memory [{record['tag']}]: \"{entry}\""

    except Exception as e:
        logger.error(f"Memory save error: {str(e)}")
        return f"❌ Memory error: {str(e)}"


async def recall_memory(query: str) -> str:
    """
    Searches memory for entries relevant to the query using keyword matching.
    Returns the top matching entries formatted as a readable list.
    If query is 'all', returns all stored memories.
    """
    try:
        data = _load()

        if not data:
            return "No memories stored yet."

        query_lower = query.strip().lower()

        # Return all memories if asked
        if query_lower in ("all", "everything", "list all", "show all"):
            lines = [
                f"[{m['id']}] ({m.get('tag','general')}) {m['content']}  — {m.get('timestamp','')}"
                for m in data
            ]
            return f"All memories ({len(data)} total):\n" + "\n".join(lines)

        # Keyword search across content and tag
        matches = [
            m for m in data
            if query_lower in m.get("content", "").lower()
            or query_lower in m.get("tag", "").lower()
            or any(word in m.get("content", "").lower() for word in query_lower.split())
        ]

        if not matches:
            return f"No memories found matching \"{query}\"."

        # Return top 5 most recent matches
        matches = matches[-5:]
        lines = [
            f"[{m['id']}] ({m.get('tag','general')}) {m['content']}  — {m.get('timestamp','')}"
            for m in matches
        ]
        return f"Found {len(matches)} memory/memories for \"{query}\":\n" + "\n".join(lines)

    except Exception as e:
        logger.error(f"Memory recall error: {str(e)}")
        return f"❌ Memory recall error: {str(e)}"
