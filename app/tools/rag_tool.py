import faiss
import os
import hashlib
import numpy as np
from app.config.settings import DOCS_PATH
from app.utils.logger import get_logger

logger = get_logger("rag_tool")

_model = None
_documents = []
_index = None

# Tracks which folder the current index was built from
_indexed_folder = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _file_hash(filepath: str) -> str:
    """Returns MD5 hash of a file for duplicate detection."""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def extract_text(filepath: str) -> str:
    """Extracts text from .txt, .pdf, or .docx files."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return ""


def _load_documents(folder: str) -> list[str]:
    """Loads all supported documents from a folder."""
    docs = []
    supported = (".txt", ".pdf", ".docx")
    if not os.path.exists(folder):
        raise ValueError(f"Folder not found: {folder}")
    for file in os.listdir(folder):
        if file.lower().endswith(supported):
            text = extract_text(os.path.join(folder, file))
            if text.strip():
                docs.append(text)
    if not docs:
        raise ValueError("No supported documents found in the folder.")
    return docs


def _split_documents(docs: list[str], chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Splits documents into overlapping chunks for better context coverage."""
    chunks = []
    for doc in docs:
        start = 0
        while start < len(doc):
            end = start + chunk_size
            chunk = doc[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap  # overlap keeps context between chunks
    return chunks


def _build_index(chunks: list[str]):
    model = _get_model()
    embeddings = model.encode(chunks)
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index


def _ensure_index():
    global _documents, _index, _indexed_folder
    if _index is None or _indexed_folder != DOCS_PATH:
        raw_docs = _load_documents(DOCS_PATH)
        _documents = _split_documents(raw_docs)
        _index = _build_index(_documents)
        _indexed_folder = DOCS_PATH
        logger.info(f"RAG index built with {len(_documents)} chunks.")


def rebuild_index():
    """Force rebuilds the FAISS index from current documents folder."""
    global _documents, _index, _indexed_folder
    _index = None
    _indexed_folder = None
    _ensure_index()
    logger.info("RAG index rebuilt.")


def save_uploaded_document(filename: str, content: bytes) -> tuple[bool, str]:
    """
    Saves an uploaded document to the docs folder.
    Returns (is_duplicate, message).
    Checks for duplicates by file hash.
    """
    os.makedirs(DOCS_PATH, exist_ok=True)
    dest_path = os.path.join(DOCS_PATH, filename)

    # Write temp to get hash
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    new_hash = hashlib.md5(content).hexdigest()

    # Check all existing files for duplicate content
    for existing_file in os.listdir(DOCS_PATH):
        existing_path = os.path.join(DOCS_PATH, existing_file)
        if os.path.isfile(existing_path):
            if _file_hash(existing_path) == new_hash:
                os.unlink(tmp_path)
                return True, f"'{filename}' already exists in the knowledge base. Using existing document."

    # Not a duplicate — save it
    import shutil
    shutil.move(tmp_path, dest_path)
    return False, f"'{filename}' uploaded successfully."


async def search(query: str, k: int = 5) -> str:
    """
    Searches documents using FAISS vector similarity.
    Retrieves top-k chunks, passes through LLM for a proper answer.
    Auto-summarizes if the answer is long.
    """
    _ensure_index()
    model = _get_model()
    query_vec = model.encode([query])

    # Cap k to available chunks
    actual_k = min(k, len(_documents))
    distances, indices = _index.search(np.array(query_vec), actual_k)
    chunks = [_documents[i] for i in indices[0] if i < len(_documents)]

    from app.tools.llm_tool import generate_rag_response
    answer = await generate_rag_response(query, chunks)

    # Auto-summarize if answer is long (> 800 chars)
    if len(answer) > 800:
        from app.tools.summary_tool import summarize
        logger.info("RAG answer is long, auto-summarizing...")
        answer = await summarize(answer)

    return answer
