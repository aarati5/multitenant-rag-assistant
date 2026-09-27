import json
import os
from datetime import datetime

AUDIT_FILE = "audit_log.json"

def load_log() -> list:
    if not os.path.exists(AUDIT_FILE):
        return []
    with open(AUDIT_FILE, "r") as f:
        return json.load(f)

def log_access(user: str, role: str, query: str, retrieved_doc_ids: list):
    logs = load_log()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "role": role,
        "query": query,
        "retrieved_documents": retrieved_doc_ids
    }
    logs.append(entry)
    with open(AUDIT_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def view_log() -> str:
    logs = load_log()
    if not logs:
        return "No audit entries yet."
    lines = []
    for entry in logs:
        lines.append(
            f"[{entry['timestamp']}] {entry['user']} ({entry['role']}) queried: \"{entry['query']}\" -> retrieved: {entry['retrieved_documents']}"
        )
    return "\n".join(lines)