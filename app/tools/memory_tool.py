import json
import os
from app.config.settings import MEMORY_PATH
from app.utils.logger import get_logger

logger = get_logger("memory_tool")


def load_memory() -> list:
    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


async def save_memory(entry: str) -> str:
    """
    Saves a string entry to local JSON memory file.
    """
    try:
        os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
        data = load_memory()
        data.append({"content": entry})
        with open(MEMORY_PATH, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Memory saved: {entry}")
        return f"Memory saved: \"{entry}\""
    except Exception as e:
        logger.error(f"Memory error: {str(e)}")
        return f"Memory error: {str(e)}"
