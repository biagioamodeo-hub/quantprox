import hashlib
import hmac
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    profile: str
    full_name: str
    email: str
    phone: str | None
    preferred_currency: str
    password_hash: str
    password_salt: str


_accounts: dict[str, Account] = {}


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 210_000
    ).hex()


def register_account(
    *,
    profile: str,
    full_name: str,
    email: str,
    phone: str | None,
    preferred_currency: str,
    password: str,
) -> Account:
    normalized_profile = profile.strip().lower()
    if normalized_profile in _accounts:
        raise ValueError("Account already exists.")
    salt = secrets.token_hex(16)
    account = Account(
        profile=normalized_profile,
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip() if phone else None,
        preferred_currency=preferred_currency,
        password_hash=_hash_password(password, salt),
        password_salt=salt,
    )
    _accounts[normalized_profile] = account
    return account


def authenticate_account(profile: str, password: str) -> bool:
    account = _accounts.get(profile.strip().lower())
    if account is None:
        return False
    supplied_hash = _hash_password(password, account.password_salt)
    return hmac.compare_digest(supplied_hash, account.password_hash)


def account_exists(profile: str) -> bool:
    return profile.strip().lower() in _accounts
