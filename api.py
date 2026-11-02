import json
import os
from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field

from src.audit import log_access
from src.auth import create_token, decode_token, hash_password, verify_password
from src.qa_agent import generate_answer
from src.vector_store import load_store_from_file, search

COLLECTION = "company_chunks"
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "gemini-3.8-flash")
VALID_ROLES = {"hr", "engineering", "finance"}

with open("data/users.json", encoding="utf-8") as f:
    USERS = json.load(f)

# Unknown usernames still pay the hashing cost, so login timing does not reveal valid usernames
DUMMY_HASH = hash_password("not-a-real-password")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_store_from_file()
    yield


app = FastAPI(title="Permission-Aware RAG API", lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class AskRequest(BaseModel):
    # extra="forbid": a request that tries to send its own "role" is rejected with 422
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=500)


def current_user(token: str = Depends(oauth2_scheme)) -> dict:
    headers = {"WWW-Authenticate": "Bearer"}
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired", headers=headers)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token", headers=headers)
    username = payload.get("sub")
    role = payload.get("role")
    if username not in USERS or role not in VALID_ROLES:
        raise HTTPException(status_code=401, detail="Invalid token", headers=headers)
    return {"username": username, "role": role}


@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form.username)
    stored = user["password_hash"] if user else DUMMY_HASH
    password_ok = verify_password(form.password, stored)
    if not user or not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_token(form.username, user["role"]), "token_type": "bearer"}


@app.get("/me")
def me(user: dict = Depends(current_user)):
    return user


@app.post("/ask")
def ask(body: AskRequest, user: dict = Depends(current_user)):
    # The role comes from the verified token, never from the request body
    chunks = search(body.query, user["role"], top_k=4, collection_name=COLLECTION)
    log_access(user["username"], user["role"], body.query, [c["id"] for c in chunks])
    try:
        answer = generate_answer(body.query, chunks, model_name=ANSWER_MODEL)
    except Exception:
        answer = None
    return {
        "user": user["username"],
        "role": user["role"],
        "answer": answer,
        "answer_available": answer is not None,
        "chunks": [{"id": c["id"], "doc_id": c["doc_id"], "role": c["role"]} for c in chunks],
    }