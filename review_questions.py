import json
import re
import statistics

from src.chunker import chunk_documents

STOP = set("""a an and are as at be been but by can could did do does for from had has have how i if in
into is it its may me my of on or our should so than that the their then there these they this to up us
was we were what when where which who whom why will with would you your about after all also any before
between both during each get just more most must no not now only other out over same some such too very
""".split())


def norm(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def content_words(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        if len(w) >= 3 or w.isdigit():
            out.add(norm(w))
    return out


def ngrams(words, n):
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


docs = json.load(open("data/long_documents.json", encoding="utf-8"))
raw = json.load(open("data/eval_questions_raw.json", encoding="utf-8"))
doc_by_id = {d["id"]: d for d in docs}
chunks_by_doc = {}
for c in chunk_documents(docs):
    chunks_by_doc.setdefault(c["doc_id"], []).append(c)

ROLES = ["hr", "engineering", "finance"]
all_i = 0
cands = []
for q in sorted(raw, key=lambda x: int(x["doc_id"][3:])):
    d = doc_by_id[q["doc_id"]]
    if d["role"] == "all":
        asker = ROLES[all_i % 3]  # company-wide docs: rotate the asking role
        all_i += 1
    else:
        asker = d["role"]

    qwords = content_words(q["question"])
    best = 0.0
    for c in chunks_by_doc[q["doc_id"]]:
        if qwords:
            best = max(best, len(qwords & content_words(c["content"])) / len(qwords))

    plain = re.findall(r"[a-z0-9]+", q["question"].lower())
    doc_plain = re.findall(r"[a-z0-9]+", d["content"].lower())
    flags = []
    if ngrams(plain, 4) & ngrams(doc_plain, 4):
        flags.append("COPY4")
    if re.search(r"\b(document|section|policy note|according to)\b", q["question"].lower()):
        flags.append("MENTIONS-DOC")
    if len(plain) < 5:
        flags.append("SHORT")

    cands.append({
        "doc_id": q["doc_id"],
        "asker_role": asker,
        "question": q["question"],
        "overlap": round(best, 2),
        "flags": flags,
    })

for i, c in enumerate(cands, 1):
    c["n"] = i

json.dump(cands, open("data/eval_candidates.json", "w", encoding="utf-8"), indent=2)

with open("data/eval_review.txt", "w", encoding="utf-8") as f:
    for c in cands:
        flag = ("   <<" + ",".join(c["flags"]) + ">>") if c["flags"] else ""
        f.write(f"#{c['n']:02d} [{c['doc_id']} | asker={c['asker_role']} | overlap={int(c['overlap'] * 100)}%] {c['question']}{flag}\n")

ov = [c["overlap"] for c in cands]
q1, q2, q3 = statistics.quantiles(ov, n=4)
print("questions:", len(cands))
print("flagged:", sum(1 for c in cands if c["flags"]), "| COPY4:", sum("COPY4" in c["flags"] for c in cands),
      "| MENTIONS-DOC:", sum("MENTIONS-DOC" in c["flags"] for c in cands), "| SHORT:", sum("SHORT" in c["flags"] for c in cands))
print(f"overlap quartiles: 25%={q1:.2f} median={q2:.2f} 75%={q3:.2f}")
print("overlap <50%:", sum(o < 0.5 for o in ov), "| 50-74%:", sum(0.5 <= o < 0.75 for o in ov), "| >=75%:", sum(o >= 0.75 for o in ov))
print("review file: data/eval_review.txt")