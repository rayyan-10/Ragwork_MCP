"""
file_tool.py
------------
Provides async functions for reading and writing local text files.
Used by the agent when the user explicitly asks to read or write a file.
"""
import os


async def read_file(file_path: str) -> str:
    """Read and return the full text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


async def write_file(file_path: str, content: str) -> str:
    """Write content to a local file, overwriting if it exists."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return "File written successfully"