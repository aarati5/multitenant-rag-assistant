# Permission-Aware Multi-Tenant RAG Assistant

A Retrieval-Augmented Generation system that enforces role-based access control at the retrieval layer — ensuring users can only retrieve and receive answers from documents their role permits, with a full audit trail of every query.

## Problem It Solves

Standard RAG systems retrieve the most semantically relevant chunks regardless of who's asking. In an enterprise setting with mixed HR, Engineering, and Finance data, this creates a serious data leakage risk. This system prevents that by filtering accessible documents by role BEFORE similarity search runs, so restricted content never reaches the LLM in the first place, and every access is logged for compliance.

## How It Works

1. Documents are indexed with role metadata (hr, engineering, finance, or all)
2. Each document is embedded using the Gemini Embedding API and stored in memory
3. When a user submits a query with their role:
   - The system filters to only documents matching their role (or tagged "all")
   - Cosine similarity search runs ONLY on that permitted subset
   - Restricted documents are excluded before the LLM ever sees them
4. Every query is logged with timestamp, user, role, and retrieved document IDs
5. The LLM generates an answer grounded only in the accessible retrieved context, citing document IDs

## Tech Stack

- Language: Python
- LLM: Google Gemini API (gemini-3.8-flash)
- Embeddings: Gemini Embedding API (gemini-embedding-001)
- Core concept: Permission-filtered retrieval + audit logging + grounded generation

## Setup

1. Clone the repo and navigate into it

2. Create a virtual environment:

python -m venv venv
venv\Scripts\activate

3. Install dependencies:

pip install google-generativeai python-dotenv numpy

4. Create a .env file with your Gemini API key:

GEMINI_API_KEY=your_key_here

Get a free key at https://aistudio.google.com/apikey

5. Run the program:

python main.py

## Usage

1. Enter your name and role (hr, engineering, or finance)
2. Ask questions — retrieval is automatically restricted to documents your role can access
3. View the audit log to see every query, who made it, and what was retrieved

## Example (Security Demonstration)

Logged in as: Aarati, role: hr

Query: "What was the quarterly revenue?"
Retrieved documents: [doc2, doc1] (both HR documents; the finance revenue document was never retrieved)
Answer: "The provided context does not contain information about the quarterly revenue."

Query: "What is the leave policy?"
Retrieved documents: [doc1, doc7] (leave policy + company-wide holiday calendar)
Answer: Correctly returned the actual leave policy details.

This demonstrates that cross-role data leakage is prevented by design, not by relying on the LLM to "choose" not to answer.

## Architecture

main.py - CLI loop handling login, questions, and audit log viewing
src/documents.py - sample company documents tagged with role-based access metadata
src/vector_store.py - embeds documents, filters by role BEFORE similarity search, then ranks only accessible documents
src/audit.py - persistent audit log of every query (user, role, query, retrieved document IDs, timestamp)
src/qa_agent.py - generates grounded answers strictly from the permitted retrieved context

## Future Improvements

- Support hierarchical roles (e.g., managers accessing both their team's and their own department's data)
- Move from in-memory storage to a persistent vector database (e.g., ChromaDB) for larger document sets
- Add role-based rate limiting and anomaly detection on the audit log (e.g., flagging unusual access patterns)