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

query = st.text_input("Ask a question", placeholder="e.g. What was the quarterly revenue?")

if st.button("Ask") and query.strip():
    try:
        with st.spinner("Searching..."):
            docs = search(query, role, top_k=3)
            log_access(user, role, query, [d["id"] for d in docs])
            answer = generate_answer(query, docs)

        st.subheader("Answer")
        st.write(answer)

        st.subheader("Retrieved documents")
        for d in docs:
            with st.expander(f"{d['id']}  |  access level: {d['role']}"):
                st.write(d["content"])
    except Exception as e:
        st.error(f"Something went wrong (possibly an API rate limit). Try again in a moment.\n\n{e}")

with st.expander("Audit log"):
    logs = load_log()
    if logs:
        st.dataframe(logs[::-1])
    else:
        st.write("No entries yet.")