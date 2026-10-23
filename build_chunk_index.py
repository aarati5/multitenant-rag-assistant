import json
from src.chunker import chunk_documents
from src.vector_store import build_store

docs = json.load(open("data/long_documents.json"))
chunks = chunk_documents(docs)
build_store(chunks, collection_name="company_chunks")