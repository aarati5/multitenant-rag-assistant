import json
import time

from src.documents import DOCUMENTS
from src.vector_store import search as vector_search
from src.hybrid import bm25_search, hybrid_search, COLLECTION
from eval_hybrid import docs_from, rank_of, vec_pool, summarize, POOL, TOPN

ROLE_OF_DOC = {d["id"]: d["role"] for d in DOCUMENTS}

items = []
for ln, line in enumerate(open("data/keyword_queries.txt", encoding="utf-8"), 1):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 3:
        raise SystemExit(f"line {ln}: expected 'role | query | docN'")
    role, query, doc = parts
    if role not in ("hr", "engineering", "finance"):
        raise SystemExit(f"line {ln}: role must be hr, engineering or finance")
    if doc not in ROLE_OF_DOC:
        raise SystemExit(f"line {ln}: unknown doc id {doc}")
    if ROLE_OF_DOC[doc] not in (role, "all"):
        raise SystemExit(f"line {ln}: role {role} cannot see {doc} (it belongs to {ROLE_OF_DOC[doc]})")
    items.append({"role": role, "query": query, "doc_id": doc})


def main():
    rows = []
    for i, c in enumerate(items, 1):
        pool = vec_pool(c["query"], c["role"])
        if pool is None:
            print("skipped (error):", c["query"])
            continue
        vec = rank_of(docs_from(pool[:TOPN]), c["doc_id"])
        kw = rank_of(docs_from(bm25_search(c["query"], c["role"], top_k=TOPN)), c["doc_id"])
        hy = rank_of(docs_from(hybrid_search(c["query"], c["role"], top_k=TOPN, pool=POOL, vector_results=pool)), c["doc_id"])
        rows.append({**c, "n": i, "vec": vec, "bm25": kw, "hyb": hy})
        time.sleep(0.7)

    json.dump(rows, open("data/eval_keyword_results.json", "w", encoding="utf-8"), indent=2)
    print("queries:", len(items), "| evaluated:", len(rows))
    for label, key in (("vector-only", "vec"), ("BM25-only", "bm25"), ("hybrid (RRF)", "hyb")):
        print(f"{label:13s}", summarize(rows, key))
    print("\nPer query (rank of the correct doc, None = not in top 10 docs):")
    for r in rows:
        print(f"  #{r['n']:02d} vec={r['vec']} bm25={r['bm25']} hybrid={r['hyb']} | {r['role']} | {r['query']} -> {r['doc_id']}")


if __name__ == "__main__":
    main()