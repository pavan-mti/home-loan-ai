from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


HASH_NAME = "sha256"
ITERATIONS = 390000
SALT_BYTES = 16


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_{HASH_NAME}${ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_text, salt_text, digest_text = stored_hash.split("$")
        if not scheme.startswith("pbkdf2_"):
            return False
        iterations = int(iterations_text)
        salt = _b64decode(salt_text)
        stored_digest = _b64decode(digest_text)
        candidate = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate, stored_digest)
    except Exception:
        return False


def create_token() -> str:
    return secrets.token_urlsafe(32)