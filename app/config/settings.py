import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DB_PATH = "data/database.db"
MEMORY_PATH = "data/memory.json"
DOCS_PATH = "data/documents/"
