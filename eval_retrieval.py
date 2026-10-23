import time
from src.vector_store import search

COLLECTION = "company_chunks"

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
    # deep-fact questions (answer lamba doc ke andar chhupa hai)
    ("hr", "How many business days in advance must casual leave be requested?", "doc1"),
    ("hr", "When is a medical certificate required for sick leave?", "doc1"),
    ("hr", "How are leaves calculated for someone who joins mid-year?", "doc1"),
    ("finance", "What happens to the payment period if an invoice has incorrect billing amounts?", "doc15"),
    ("finance", "What documents are needed before a new vendor's invoice can be processed?", "doc15"),
    ("finance", "Can payment be released without the department head's sign-off?", "doc15"),
]


def doc_ranking(question, role, top_k_chunks=10):
    # chunks laao, phir unique doc ids nikalo (order same rahega)
    chunks = search(question, role, top_k=top_k_chunks, collection_name=COLLECTION)
    ranked = []
    for c in chunks:
        if c["doc_id"] not in ranked:
            ranked.append(c["doc_id"])
    return ranked


def main():
    hit1 = 0
    hit3 = 0
    reciprocal_ranks = []
    misses = []

    for role, question, expected in EVAL_SET:
        ranked = doc_ranking(question, role)
        top3 = ranked[:3]

        if expected in top3:
            rank = top3.index(expected) + 1
            reciprocal_ranks.append(1 / rank)
            hit3 += 1
            if rank == 1:
                hit1 += 1
        else:
            reciprocal_ranks.append(0)
            misses.append((role, question, expected, top3))
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