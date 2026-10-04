import hashlib
import secrets


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    if not token:
        raise ValueError("session token must not be empty")

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
