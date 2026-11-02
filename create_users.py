import json
import secrets

from src.auth import hash_password

USERS = [
    ("hr_user", "hr"),
    ("eng_user", "engineering"),
    ("fin_user", "finance"),
]

users = {}
creds = {}
for username, role in USERS:
    password = secrets.token_urlsafe(12)
    users[username] = {"role": role, "password_hash": hash_password(password)}
    creds[username] = password

json.dump(users, open("data/users.json", "w"), indent=2)
json.dump(creds, open("data/demo_credentials.json", "w"), indent=2)

print("created users:", ", ".join(users))
print("hashes -> data/users.json | demo passwords -> data/demo_credentials.json (both gitignored)")