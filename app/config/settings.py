"""
settings.py
-----------
Central configuration for ToolPilot.
Loads environment variables from .env and defines shared path constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM API key (loaded from .env)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Local storage paths
DB_PATH = "data/database.db"       # SQLite database file
MEMORY_PATH = "data/memory.json"   # Persistent memory store
DOCS_PATH = "data/documents/"      # RAG knowledge base folder
