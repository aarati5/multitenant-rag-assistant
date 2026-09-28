import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "models/gemini-embedding-001"
COLLECTION_NAME = "company_docs"

# Persistent client — data survives across runs, stored in ./chroma_db folder
client = chromadb.PersistentClient(path="./chroma_db")


def embed_text(text: str, task_type: str = "retrieval_document"):
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type=task_type
    )
    return result["embedding"]


def build_store(documents: list):
    # Rebuild fresh each run so document edits are reflected
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    ids = [d["id"] for d in documents]
    contents = [d["content"] for d in documents]
    metadatas = [{"role": d["role"]} for d in documents]
    embeddings = [embed_text(d["content"]) for d in documents]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=contents,
        metadatas=metadatas
    )
    print(f"Indexed {len(documents)} documents into ChromaDB.")
    return collection


def search(query: str, user_role: str, top_k: int = 2):
    collection = client.get_collection(COLLECTION_NAME)
    query_embedding = embed_text(query, task_type="retrieval_query")

    # ChromaDB filters by role metadata BEFORE similarity ranking —
    # restricted documents are never even considered
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"role": {"$in": [user_role, "all"]}}
    )

    docs = []
    ids = results["ids"][0]
    contents = results["documents"][0]
    metadatas = results["metadatas"][0]
    for i in range(len(ids)):
        docs.append({
            "id": ids[i],
            "content": contents[i],
            "role": metadatas[i]["role"]
        })
    return docs