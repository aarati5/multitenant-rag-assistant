# Permission-Aware Multi-Tenant RAG Assistant

A Retrieval-Augmented Generation system that enforces role-based access control at the retrieval layer, so users can only retrieve and receive answers from documents their role permits, with a full audit trail of every query.

## Problem It Solves

Standard RAG systems retrieve the most semantically relevant chunks regardless of who is asking. In an enterprise setting with mixed HR, Engineering, and Finance data, this creates a serious data leakage risk. This system applies the role filter inside the vector database query itself, so restricted documents are never returned to the application or the LLM, and every access is logged for compliance.

## How It Works

1. 24 documents are indexed with role metadata (hr, engineering, finance, or all)
2. Each document is embedded using the Gemini Embedding API and stored in ChromaDB (persistent vector database)
3. When a user submits a query with their role:
   - ChromaDB runs the similarity search with a metadata filter: role must be the user's role or "all"
   - Restricted documents are never returned, so the LLM never sees them
4. Every query is logged with timestamp, user, role, and retrieved document IDs
5. The LLM generates an answer grounded only in the permitted context, citing document IDs

## Tech Stack

- Language: Python
- LLM: Google Gemini API (gemini-3.8-flash)
- Embeddings: Gemini Embedding API (gemini-embedding-001)
- Vector database: ChromaDB (persistent, with metadata filtering)
- Core concept: Permission-filtered retrieval + audit logging + grounded generation

## Setup

1. Clone the repo and navigate into it

2. Create a virtual environment:

python -m venv venv
venv\Scripts\activate

3. Install dependencies:

pip install google-generativeai python-dotenv chromadb

4. Create a .env file with your Gemini API key:

GEMINI_API_KEY=your_key_here

Get a free key at https://aistudio.google.com/apikey

5. Run the program:

python main.py

## Usage

1. Enter your name and role (hr, engineering, or finance)
2. Ask questions. Retrieval is automatically restricted to documents your role can access
3. View the audit log to see every query, who made it, and what was retrieved

## Example (Security Demonstration)

Same question, two different roles:

Role: hr
Query: "When is the external financial audit conducted?"
Retrieved: [doc2, doc19] (an HR document and a company-wide document; the finance audit document was never returned)
Answer: "There is no information about when the external financial audit is conducted."

Role: finance
Query: "What was the quarterly revenue?"
Retrieved: [doc13, doc17] (both finance documents)
Answer: Q3 revenue was $2.4M, a 15% increase from Q2, citing [doc13].

The same finance question asked by an HR user returned no financial data, because restricted documents are excluded at the database query level rather than relying on the LLM to withhold them.

## Architecture

main.py - CLI loop handling login, questions, and audit log viewing
src/documents.py - 24 sample company documents tagged with role-based access metadata
src/vector_store.py - embeds documents, stores them in ChromaDB, and queries with a role metadata filter
src/audit.py - persistent audit log of every query (user, role, query, retrieved document IDs, timestamp)
src/qa_agent.py - generates grounded answers strictly from the permitted retrieved context

## Limitations and Scaling Considerations

This is a working prototype. Known limitations and how I would address them in production:

- Roles are self-declared at login. Production would integrate real authentication (SSO/OAuth) and derive roles from identity claims, never from user input.
- The index is rebuilt and all documents are re-embedded on every run. This is fine for 24 documents but wasteful at scale; production would embed incrementally and only re-embed changed documents.
- Each document is a single chunk. Real documents need chunking with overlap, and access metadata must be inherited by every chunk.
- Each document has a single role tag. Real organizations need multiple roles per document, hierarchical roles (a manager sees their team's data), and user-level permissions.
- The audit log is a local JSON file. Production would need an append-only, tamper-evident store with retention policies.
- Single-user CLI. A multi-user service would need an API layer, concurrent request handling, and per-user rate limiting.
- No error handling or retries around embedding and LLM API failures.
- Retrieval quality is not formally evaluated. A retrieval test set with recall metrics would be the next step.

## Future Improvements

- Incremental indexing with cached embeddings
- Hierarchical roles and multiple roles per document
- Anomaly detection on the audit log (for example, flagging repeated queries for restricted topics)
- REST API with real authentication