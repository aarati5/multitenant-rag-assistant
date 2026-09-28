import time
from src.documents import DOCUMENTS
from src.vector_store import build_store, search

# (asking role, question, expected document id)
EVAL_SET = [
    ("hr", "How many sick days do I get in a year?", "doc1"),
    ("hr", "When do performance appraisals take place?", "doc2"),
    ("hr", "How long does the new joiner induction last?", "doc3"),
    ("hr", "How many weeks of leave does a new mother get?", "doc4"),
    ("hr", "What reward do I get for bringing in a friend who gets hired?", "doc5"),
    ("hr", "How much notice must I give before quitting?", "doc6"),
    ("engineering", "Which days of the week do we release to production?", "doc7"),
    ("engineering", "How do our backend services talk to each other?", "doc8"),
    ("engineering", "How are engineers paid for being on call?", "doc9"),
    ("engineering", "How many approvals does a pull request need?", "doc10"),
    ("engineering", "How quickly must a critical outage be acknowledged?", "doc11"),
    ("engineering", "Which cloud and framework does the company use?", "doc12"),
    ("finance", "How much money did the company make last quarter?", "doc13"),
    ("finance", "What is the limit for claiming travel costs without approval?", "doc14"),
    ("finance", "How many days does it take to pay a supplier invoice?", "doc15"),
    ("finance", "When does the outside auditor review our books?", "doc16"),
    ("finance", "How much cash must the company keep in reserve?", "doc17"),
    ("finance", "When do employees receive their salary?", "doc18"),
    ("hr", "How many days can I work from home?", "doc21"),
    ("engineering", "What should I do about suspicious emails?", "doc22"),
]

def main():
    build_store(DOCUMENTS)

    hit1 = 0
    hit3 = 0
    reciprocal_ranks = []
    misses = []

    for role, question, expected in EVAL_SET:
        results = search(question, role, top_k=3)
        ids = [r["id"] for r in results]

        if expected in ids:
            rank = ids.index(expected) + 1
            reciprocal_ranks.append(1 / rank)
            hit3 += 1
            if rank == 1:
                hit1 += 1
        else:
            reciprocal_ranks.append(0)
            misses.append((role, question, expected, ids))
        time.sleep(0.5)

    n = len(EVAL_SET)
    print("\n" + "=" * 60)
    print(f"Questions evaluated: {n}")
    print(f"Recall@1: {hit1}/{n} = {hit1 / n * 100:.0f}%")
    print(f"Recall@3: {hit3}/{n} = {hit3 / n * 100:.0f}%")
    print(f"MRR:      {sum(reciprocal_ranks) / n:.2f}")
    print("=" * 60)
    for role, q, expected, ids in misses:
        print(f"MISS: [{role}] '{q}' expected {expected}, got {ids}")

if __name__ == "__main__":
    main()