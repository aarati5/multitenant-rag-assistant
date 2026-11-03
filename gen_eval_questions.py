import os
import json
import time
import re

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-3.6-flash")

docs = json.load(open("data/long_documents.json", encoding="utf-8"))
out_path = "data/eval_questions_raw.json"
result = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else []
done = {r["doc_id"] for r in result}

PROMPT = """You write test questions for a retrieval system.
For EACH document below, write 4 questions that a real employee might ask, where the answer is a specific detail in the BODY of that document (a number, condition, exception, deadline, step or example).
Rules:
- Do NOT use the FAQ section as the source.
- Use different vocabulary from the document: do not copy any phrase of 3 or more words.
- Each question must make sense on its own and must not mention the document, its id or its title.
- Return ONLY JSON: a list of objects like {"doc_id": "doc1", "question": "..."}.

"""

BATCH = 6
FENCE = "`" * 3

for i in range(0, len(docs), BATCH):
    group = docs[i:i + BATCH]
    ids = [d["id"] for d in group]
    if all(x in done for x in ids):
        continue
    prompt = PROMPT + "\n\n".join(f"=== {d['id']} ===\n{d['content']}" for d in group)

    items = None
    for attempt in range(3):
        try:
            text = model.generate_content(prompt, request_options={"timeout": 120}).text
            text = text.replace(FENCE + "json", "").replace(FENCE, "")
            start, end = text.find("["), text.rfind("]")
            items = json.loads(text[start:end + 1])
            break
        except Exception as e:
            print("error:", str(e)[:100], "| waiting 60 sec, retry", attempt + 1)
            time.sleep(60)
    if items is None:
        print("skipped batch", ids)
        continue

    kept = [x for x in items if x.get("doc_id") in ids and str(x.get("question", "")).strip()]
    result.extend({"doc_id": x["doc_id"], "question": x["question"].strip()} for x in kept)
    json.dump(result, open(out_path, "w", encoding="utf-8"), indent=2)
    print("batch", ids[0], "to", ids[-1], "->", len(kept), "questions")
    time.sleep(15)

print("total questions:", len(result))