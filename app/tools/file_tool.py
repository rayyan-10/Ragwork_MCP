import os

async def read_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

async def write_file(file_path: str, content: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return "File written successfully"