import hashlib
import hmac
import secrets


def create_password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return _hash_password(password, salt), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    supplied_hash = _hash_password(password, salt)
    return hmac.compare_digest(supplied_hash, password_hash)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 210_000
    ).hex()
