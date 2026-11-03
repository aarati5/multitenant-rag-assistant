import json
import re
import time

from src.vector_store import search

COLLECTION = "company_chunks"

drop = {int(x) for x in re.findall(r"\d+", open("data/eval_drop.txt", encoding="utf-8").read())}
cands = json.load(open("data/eval_candidates.json", encoding="utf-8"))
EVAL = [c for c in cands if c["n"] not in drop]
json.dump(EVAL, open("data/eval_set_v2.json", "w", encoding="utf-8"), indent=2)


def ranked_docs(question, role):
    chunks = None
    for attempt in range(3):
        try:
            chunks = search(question, role, top_k=10, collection_name=COLLECTION)
            break
        except Exception as e:
            print("   error:", str(e)[:80], "| waiting 30 sec")
            time.sleep(30)
    if chunks is None:
        return None
    ranked = []
    for c in chunks:
        if c["doc_id"] not in ranked:
            ranked.append(c["doc_id"])
    return ranked


def summarize(rows):
    n = len(rows)
    if n == 0:
        return "n=0"
    r1 = sum(r["rank"] == 1 for r in rows)
    r3 = sum(r["rank"] is not None and r["rank"] <= 3 for r in rows)
    mrr = sum((1 / r["rank"]) if r["rank"] else 0 for r in rows) / n
    return f"n={n} | Recall@1 {r1}/{n} = {r1 / n * 100:.0f}% | Recall@3 {r3}/{n} = {r3 / n * 100:.0f}% | MRR {mrr:.2f}"


def main():
    rows = []
    errors = 0
    for c in EVAL:
        ranked = ranked_docs(c["question"], c["asker_role"])
        if ranked is None:
            errors += 1
            continue
        rank = ranked.index(c["doc_id"]) + 1 if c["doc_id"] in ranked else None
        rows.append({**c, "rank": rank, "top3": ranked[:3]})
        time.sleep(0.7)

    json.dump(rows, open("data/eval_v2_results.json", "w", encoding="utf-8"), indent=2)
    print("questions:", len(EVAL), "| evaluated:", len(rows), "| errors:", errors)
    print("ALL           ", summarize(rows))
    print("overlap < 50% ", summarize([r for r in rows if r["overlap"] < 0.5]))
    print("overlap >= 50%", summarize([r for r in rows if r["overlap"] >= 0.5]))
    for r in rows:
        if r["rank"] is None or r["rank"] > 3:
            print(f"MISS #{r['n']:02d} [{r['asker_role']}] expected {r['doc_id']}, got {r['top3']} | {r['question'][:90]}")


if __name__ == "__main__":
    main()