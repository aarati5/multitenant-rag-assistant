import json
from src.vector_store import client

col = client.get_collection("company_chunks")
data = col.get(include=["embeddings", "documents", "metadatas"])

out = []
for i in range(len(data["ids"])):
    out.append({
        "id": data["ids"][i],
        "content": data["documents"][i],
        "metadata": data["metadatas"][i],
        "embedding": [round(float(x), 6) for x in data["embeddings"][i]],
    })

json.dump(out, open("data/chunk_embeddings.json", "w"))
print("saved", len(out), "chunks")