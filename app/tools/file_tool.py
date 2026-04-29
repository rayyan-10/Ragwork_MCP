"""
file_tool.py
------------
Provides an async function for reading local text files.
Used by the agent when the user explicitly asks to read or summarize a file.
"""
import os


async def read_file(file_path: str) -> str:
    """Read and return the full text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
