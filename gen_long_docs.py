import os, json, time
from dotenv import load_dotenv
import google.generativeai as genai
from src.documents import DOCUMENTS

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-3.6-flash")

LIMIT = 24  

PROMPT = """Expand this short company policy note into a realistic internal document of 400-600 words.
Rules:
- Keep every fact and number from the original EXACTLY the same.
- Add section headings, procedures, exceptions, examples and a short FAQ.
- New details must not contradict the original.
- Plain text only, no markdown symbols.

Original:
{content}"""

out_path = "data/long_documents.json"
result = json.load(open(out_path)) if os.path.exists(out_path) else []
done = {d["id"] for d in result}

for d in DOCUMENTS[:LIMIT]:
    if d["id"] in done:
        continue
    text = None
    for attempt in range(3):
        try:
            text = model.generate_content(PROMPT.format(content=d["content"])).text
            break
        except Exception as e:
            print(d["id"], "error:", e, "| 30 sec wait, retry", attempt + 1)
            time.sleep(30)
    if text is None:
        print(d["id"], "skipped")
        continue
    result.append({"id": d["id"], "role": d["role"], "content": text})
    json.dump(result, open(out_path, "w"), indent=2)
    print(d["id"], len(text.split()), "words")
    time.sleep(15)