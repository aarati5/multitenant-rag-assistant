import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_answer(query: str, retrieved_docs: list) -> str:
    if not retrieved_docs:
        return "No accessible documents were found relevant to your query. You may not have permission to view this information."

    context = "\n\n".join([f"[{d['id']}] {d['content']}" for d in retrieved_docs])

    system_prompt = """You are an internal company assistant. Answer the user's question using ONLY the context provided below.

Rules:
- Only use information present in the context
- If the context doesn't fully answer the question, say so explicitly
- Cite the document id (e.g., [doc1]) after each claim
"""

    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
        system_instruction=system_prompt
    )

    prompt = f"Context:\n{context}\n\nQuestion: {query}"
    response = model.generate_content(prompt)
    return response.text