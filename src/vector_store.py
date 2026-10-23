import os
import time
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "models/gemini-embedding-001"
COLLECTION_NAME = "company_docs"

# Persistent client - data survives across runs, stored in ./chroma_db folder
client = chromadb.PersistentClient(path="./chroma_db")


def embed_text(text: str, task_type: str = "retrieval_document"):
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type=task_type
    )
    return result["embedding"]


def embed_batch(texts: list, task_type: str = "retrieval_document", batch_size: int = 15):
    # 15 texts har 12 sec mein = ~75 requests/min, free limit (100/min) ke andar
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(4):
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=batch,
                    task_type=task_type
                )
                all_embeddings.extend(result["embedding"])
                break
            except Exception as e:
                print("embed error, 60 sec wait, retry", attempt + 1, "|", str(e)[:80])
                time.sleep(60)
        else:
            raise RuntimeError("embedding failed after 4 retries")
        print(f"embedded {len(all_embeddings)}/{len(texts)}")
        time.sleep(12)
    return all_embeddings


def build_store(documents: list, collection_name: str = COLLECTION_NAME):
    # Rebuild fresh each run so edits are reflected
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

    ids = [d["id"] for d in documents]
    contents = [d["content"] for d in documents]
    metadatas = [
        {
            "role": d["role"],
            "doc_id": d.get("doc_id", d["id"]),
            "chunk_index": d.get("chunk_index", 0),
        }
        for d in documents
    ]
    embeddings = embed_batch(contents)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=contents,
        metadatas=metadatas
    )
    print(f"Indexed {len(documents)} documents into ChromaDB.")
    return collection


def search(query: str, user_role: str, top_k: int = 2, collection_name: str = COLLECTION_NAME):
    collection = client.get_collection(collection_name)
    query_embedding = embed_text(query, task_type="retrieval_query")

    # ChromaDB filters by role metadata BEFORE similarity ranking -
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
            "doc_id": metadatas[i].get("doc_id", ids[i]),
            "content": contents[i],
            "role": metadatas[i]["role"]
        })
    return docs

def load_store_from_file(path: str = "data/chunk_embeddings.json", collection_name: str = "company_chunks"):
    # Saved embeddings se store banao: koi API call nahi, quota nahi lagta
    import json
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)
    items = json.load(open(path, encoding="utf-8"))
    collection.add(
        ids=[x["id"] for x in items],
        embeddings=[x["embedding"] for x in items],
        documents=[x["content"] for x in items],
        metadatas=[x["metadata"] for x in items],
    )
    print(f"Loaded {len(items)} chunks from file (no API calls).")
    return collection