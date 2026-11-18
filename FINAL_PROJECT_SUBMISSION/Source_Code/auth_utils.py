"""Session-scoped demo account validation and password hashing helpers."""

import hashlib
import hmac
import re
import secrets
from collections.abc import MutableMapping

PASSWORD_HASH_ITERATIONS = 600_000
_EMAIL_PATTERN = re.compile(
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+",
    re.IGNORECASE,
)

Account = dict[str, str]


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def is_valid_email(email: str) -> bool:
    return _EMAIL_PATTERN.fullmatch(email.strip()) is not None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}"
        f"${salt.hex()}${password_hash.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_text)
        expected_hash = bytes.fromhex(digest_text)
    except (AttributeError, TypeError, ValueError):
        return False
    if (
        iterations != PASSWORD_HASH_ITERATIONS
        or len(salt) != 16
        or len(expected_hash) != hashlib.sha256().digest_size
    ):
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_hash, expected_hash)


def register_account(
    accounts: MutableMapping[str, Account],
    name: str,
    email: str,
    password: str,
) -> str | None:
    normalized_email = normalize_email(email)
    if not name.strip():
        return "Enter your full name."
    if not normalized_email:
        return "Enter your email address."
    if not is_valid_email(normalized_email):
        return "Enter a valid email address."
    if not password:
        return "Enter a password."
    if normalized_email in accounts:
        return "An account with this email is already registered. Please log in."

    accounts[normalized_email] = {
        "name": name.strip(),
        "password_hash": hash_password(password),
    }
    return None


def authenticate_account(
    accounts: MutableMapping[str, Account],
    email: str,
    password: str,
) -> Account | None:
    normalized_email = normalize_email(email)
    if not normalized_email or not password or not is_valid_email(normalized_email):
        return None

    account = accounts.get(normalized_email)
    if account is None or not verify_password(password, account.get("password_hash", "")):
        return None
    return account
