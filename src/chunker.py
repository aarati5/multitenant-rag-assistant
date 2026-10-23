import json

def chunk_text(text, chunk_words=150, overlap=30):
    words = text.split()
    step = chunk_words - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + chunk_words]))
        if start + chunk_words >= len(words):
            break
    return chunks

def chunk_documents(docs, chunk_words=150, overlap=30):
    out = []
    for d in docs:
        for i, c in enumerate(chunk_text(d["content"], chunk_words, overlap)):
            out.append({
                "id": f'{d["id"]}_c{i}',
                "doc_id": d["id"],
                "role": d["role"],
                "chunk_index": i,
                "content": c,
            })
    return out

if __name__ == "__main__":
    docs = json.load(open("data/long_documents.json"))
    chunks = chunk_documents(docs)
    print("docs:", len(docs), "| chunks:", len(chunks))
    print("roles:", {r: sum(c["role"] == r for c in chunks) for r in ["hr", "engineering", "finance", "all"]})
    print("sample id:", chunks[0]["id"], "| role:", chunks[0]["role"])