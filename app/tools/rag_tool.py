import faiss
import os
import numpy as np
from app.config.settings import DOCS_PATH

# ── Lazy globals (populated on first search call) ─────────────────────────────
_model = None
_documents = []
_index = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_documents(folder: str):
    docs = []
    if not os.path.exists(folder):
        raise ValueError(f"Folder not found: {folder}")
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            with open(os.path.join(folder, file), "r", encoding="utf-8") as f:
                docs.append(f.read())
    if not docs:
        raise ValueError("No .txt documents found in the folder!")
    return docs


def _split_documents(docs, chunk_size=200):
    chunks = []
    for doc in docs:
        for i in range(0, len(doc), chunk_size):
            chunks.append(doc[i:i + chunk_size])
    return chunks


def _build_index(documents):
    model = _get_model()
    embeddings = model.encode(documents)
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index


def _ensure_index():
    global _documents, _index
    if _index is None:
        raw_docs = _load_documents(DOCS_PATH)
        _documents = _split_documents(raw_docs)
        _index = _build_index(_documents)


async def search(query: str, k: int = 2) -> str:
    """
    Searches local documents using FAISS vector similarity.
    Returns top matching chunks as a readable string.
    """
    _ensure_index()
    model = _get_model()
    query_vec = model.encode([query])
    distances, indices = _index.search(np.array(query_vec), k)
    results = [_documents[i] for i in indices[0]]
    return "\n\n".join(results)
