import json
import math
import re
from collections import Counter

from src.vector_store import search as vector_search

COLLECTION = "company_chunks"

STOP = set("a an and are as at be been but by can could did do does for from had has have how i if in into is it its may me my of on or our should so than that the their then there these they this to up us was we were what when where which who whom why will with would you your about after all also any before between both during each get just more most must no not now only other out over same some such too very".split())


def tokenize(text):
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        if len(w) >= 3 or w.isdigit():
            out.append(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


class BM25:
    def __init__(self, texts, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(t) for t in texts]
        self.avgdl = sum(len(d) for d in self.docs) / len(self.docs)
        df = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def scores(self, query):
        q = tokenize(query)
        out = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in q:
                f = tf.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out.append(s)
        return out


_CHUNKS = None
_INDEX = {}


def _load_chunks():
    global _CHUNKS
    if _CHUNKS is None:
        items = json.load(open("data/chunk_embeddings.json", encoding="utf-8"))
        _CHUNKS = [
            {"id": x["id"], "doc_id": x["metadata"]["doc_id"], "role": x["metadata"]["role"], "content": x["content"]}
            for x in items
        ]
    return _CHUNKS


def _bm25_for(role):
    # SECURITY: only chunks this role may see are ever indexed or scored
    if role not in _INDEX:
        permitted = [c for c in _load_chunks() if c["role"] in (role, "all")]
        _INDEX[role] = (permitted, BM25([c["content"] for c in permitted]))
    return _INDEX[role]


def bm25_search(query, role, top_k=20):
    permitted, bm = _bm25_for(role)
    scores = bm.scores(query)
    order = sorted(range(len(permitted)), key=lambda i: scores[i], reverse=True)
    return [permitted[i] for i in order[:top_k] if scores[i] > 0]


def rrf(rankings, k=60):
    fused = {}
    for ranking in rankings:
        for rank, c in enumerate(ranking, 1):
            fused[c["id"]] = fused.get(c["id"], 0.0) + 1.0 / (k + rank)
    return fused


def hybrid_search(query, role, top_k=4, pool=20, vector_results=None):
    vec = vector_results if vector_results is not None else vector_search(
        query, role, top_k=pool, collection_name=COLLECTION)
    kw = bm25_search(query, role, top_k=pool)
    fused = rrf([vec, kw])
    by_id = {c["id"]: c for c in vec + kw}
    ids = sorted(fused, key=fused.get, reverse=True)
    # final guard: never return a chunk outside the caller's role
    return [by_id[i] for i in ids if by_id[i]["role"] in (role, "all")][:top_k]