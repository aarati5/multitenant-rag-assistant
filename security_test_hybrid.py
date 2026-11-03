import time

from src.documents import DOCUMENTS
from src.hybrid import bm25_search, hybrid_search
from security_test import ADVERSARIAL_QUERIES

ROLE_OF_DOC = {d["id"]: d["role"] for d in DOCUMENTS}
ROLES = ["hr", "engineering", "finance"]


def run(fn):
    for attempt in range(3):
        try:
            return fn()
        except Exception as e:
            print("   error:", str(e)[:80], "| waiting 30 sec")
            time.sleep(30)
    return None


def main():
    checked = {"bm25": 0, "hybrid": 0}
    queries = {"bm25": 0, "hybrid": 0}
    leaks = []
    mismatches = []
    errors = 0

    for role in ROLES:
        for q in ADVERSARIAL_QUERIES:
            for name, fn in (
                ("bm25", lambda: bm25_search(q, role, top_k=10)),
                ("hybrid", lambda: hybrid_search(q, role, top_k=5)),
            ):
                chunks = run(fn)
                if chunks is None:
                    errors += 1
                    continue
                queries[name] += 1
                for c in chunks:
                    checked[name] += 1
                    true_role = ROLE_OF_DOC[c["doc_id"]]
                    if true_role not in (role, "all"):
                        leaks.append((name, role, q, c["id"], true_role))
                    if c["role"] != true_role:
                        mismatches.append((name, c["id"], c["role"], true_role))
            time.sleep(0.7)

    print("\n" + "=" * 60)
    print(f"BM25   queries: {queries['bm25']} | chunks checked: {checked['bm25']}")
    print(f"Hybrid queries: {queries['hybrid']} | chunks checked: {checked['hybrid']}")
    print(f"Cross-role leaks:      {len(leaks)}")
    print(f"Chunk role mismatches: {len(mismatches)}")
    print(f"Errors:                {errors}")
    print("=" * 60)
    for x in leaks:
        print("LEAK:", x)
    for x in mismatches:
        print("MISMATCH:", x)


if __name__ == "__main__":
    main()