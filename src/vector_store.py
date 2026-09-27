import os
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "models/gemini-embedding-001"

_store = []  # in-memory store: list of {id, role, content, embedding}

def embed_text(text: str, task_type: str = "retrieval_document"):
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type=task_type
    )
    return np.array(result["embedding"])

def build_store(documents: list):
    global _store
    _store = []
    for doc in documents:
        embedding = embed_text(doc["content"], task_type="retrieval_document")
        _store.append({
            "id": doc["id"],
            "role": doc["role"],
            "content": doc["content"],
            "embedding": embedding
        })
    print(f"Indexed {len(_store)} documents.")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query: str, user_role: str, top_k: int = 2):
    # STEP 1: Filter by role BEFORE anything reaches similarity search
    accessible_docs = [d for d in _store if d["role"] == user_role or d["role"] == "all"]

    if not accessible_docs:
        return []

    # STEP 2: Embed the query and rank only the accessible documents
    query_embedding = embed_text(query, task_type="retrieval_query")

    scored = []
    for doc in accessible_docs:
        score = cosine_similarity(query_embedding, doc["embedding"])
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = [doc for score, doc in scored[:top_k]]
    return top_results