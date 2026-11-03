import json
import time

from src.vector_store import search as vector_search
from src.hybrid import bm25_search, hybrid_search, COLLECTION

EVAL = json.load(open("data/eval_set_v2.json", encoding="utf-8"))
POOL = 20   # vector chunks fetched once per question
TOPN = 10   # chunks each method contributes to the doc-level ranking


def docs_from(chunks):
    ranked = []
    for c in chunks:
        if c["doc_id"] not in ranked:
            ranked.append(c["doc_id"])
    return ranked


def rank_of(ranked, doc_id):
    return ranked.index(doc_id) + 1 if doc_id in ranked else None


def vec_pool(question, role):
    for attempt in range(3):
        try:
            return vector_search(question, role, top_k=POOL, collection_name=COLLECTION)
        except Exception as e:
            print("   error:", str(e)[:80], "| waiting 30 sec")
            time.sleep(30)
    return None


def summarize(rows, key):
    n = len(rows)
    if n == 0:
        return "n=0"
    r1 = sum(r[key] == 1 for r in rows)
    r3 = sum(r[key] is not None and r[key] <= 3 for r in rows)
    mrr = sum((1 / r[key]) if r[key] else 0 for r in rows) / n
    return f"R@1 {r1}/{n} = {r1 / n * 100:.0f}% | R@3 {r3}/{n} = {r3 / n * 100:.0f}% | MRR {mrr:.2f}"


def main():
    rows = []
    errors = 0
    for c in EVAL:
        pool = vec_pool(c["question"], c["asker_role"])
        if pool is None:
            errors += 1
            continue
        role, q, doc = c["asker_role"], c["question"], c["doc_id"]
        vec_rank = rank_of(docs_from(pool[:TOPN]), doc)
        kw_rank = rank_of(docs_from(bm25_search(q, role, top_k=TOPN)), doc)
        hy_rank = rank_of(docs_from(hybrid_search(q, role, top_k=TOPN, pool=POOL, vector_results=pool)), doc)
        rows.append({**c, "vec": vec_rank, "bm25": kw_rank, "hyb": hy_rank})
        time.sleep(0.7)

    json.dump(rows, open("data/eval_hybrid_results.json", "w", encoding="utf-8"), indent=2)
    print("questions:", len(EVAL), "| evaluated:", len(rows), "| errors:", errors)
    for label, key in (("vector-only", "vec"), ("BM25-only", "bm25"), ("hybrid (RRF)", "hyb")):
        print(f"\n{label}")
        print("  ALL            ", summarize(rows, key))
        print("  overlap < 50%  ", summarize([r for r in rows if r["overlap"] < 0.5], key))
        print("  overlap >= 50% ", summarize([r for r in rows if r["overlap"] >= 0.5], key))

    print("\nQuestions where hybrid rank differs from vector-only rank:")
    changed = [r for r in rows if r["vec"] != r["hyb"]]
    for r in changed:
        print(f"  #{r['n']:02d} vec={r['vec']} bm25={r['bm25']} hybrid={r['hyb']} | {r['question'][:70]}")
    if not changed:
        print("  (none)")


if __name__ == "__main__":
    main()