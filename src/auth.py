import os
import time
import hmac
import hashlib
import secrets

import jwt
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = "HS256"
TOKEN_MINUTES = 30
ITERATIONS = 200_000


def _secret() -> str:
    s = os.getenv("JWT_SECRET")
    if not s or len(s) < 32:
        raise RuntimeError("JWT_SECRET is missing or too short (need 32+ characters)")
    return s


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, dk_hex = stored.split("$")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS)
    return hmac.compare_digest(dk.hex(), dk_hex)


def create_token(username: str, role: str) -> str:
    now = int(time.time())
    payload = {"sub": username, "role": role, "iat": now, "exp": now + TOKEN_MINUTES * 60}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    # Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on bad tokens
    return jwt.decode(token, _secret(), algorithms=[ALGORITHM])