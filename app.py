import os
import streamlit as st

# On Streamlit Cloud, copy the secret into an env var BEFORE importing src modules
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

from src.documents import DOCUMENTS
from src.vector_store import build_store, search
from src.audit import log_access, load_log
from src.qa_agent import generate_answer

st.set_page_config(page_title="Permission-Aware RAG", page_icon="🔐")


@st.cache_resource
def init_store():
    build_store(DOCUMENTS)
    return True


@st.cache_data(show_spinner=False)
def cached_answer(query: str, doc_ids: tuple, _docs: list):
    # _docs is excluded from the cache key; (query, doc_ids) identify the answer
    return generate_answer(query, _docs)


init_store()

st.title("🔐 Permission-Aware Multi-Tenant RAG")
st.caption(
    "Same question, different role, different documents. "
    "Access control is enforced inside the vector database query, "
    "so restricted documents never reach the LLM."
)

with st.sidebar:
    st.header("Login (demo)")
    user = st.text_input("Name", value="demo-user")
    role = st.selectbox("Role", ["hr", "engineering", "finance"])
    st.info(
        "Role is self-selected for this demo. "
        "In production it would come from authentication."
    )
    st.markdown("**Try this:** ask *'What was the quarterly revenue?'* as hr, then as finance.")
    st.caption(
        "This demo runs on a free API tier with a small daily quota. "
        "If answer generation is unavailable, retrieval and access control still work."
    )

query = st.text_input("Ask a question", placeholder="e.g. What was the quarterly revenue?")

if st.button("Ask") and query.strip():
    # 1. Retrieval + audit: this is the core feature, so show it first
    try:
        docs = search(query, role, top_k=3)
    except Exception as e:
        st.error(f"Search failed (possibly an API rate limit). Please try again shortly.\n\n{e}")
        st.stop()

    log_access(user, role, query, [d["id"] for d in docs])

    # 2. LLM answer: may fail on the free tier, so handle it separately
    st.subheader("Answer")
    try:
        answer = cached_answer(query, tuple(d["id"] for d in docs), docs)
        st.write(answer)
    except Exception:
        st.warning(
            "Answer generation is unavailable right now (free-tier daily limit reached). "
            "The documents your role is allowed to see are shown below."
        )

    st.subheader("Retrieved documents")
    for d in docs:
        with st.expander(f"{d['id']}  |  access level: {d['role']}"):
            st.write(d["content"])

with st.expander("Audit log"):
    logs = load_log()
    if logs:
        st.dataframe(logs[::-1])
    else:
        st.write("No entries yet.")