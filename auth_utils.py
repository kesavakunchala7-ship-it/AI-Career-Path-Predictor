"""Streamlit OIDC identity helpers and legacy password hashing utilities."""

import hashlib
import hmac
import re
import secrets
from collections.abc import Mapping, MutableMapping
from urllib.parse import urlsplit

PASSWORD_HASH_ITERATIONS = 600_000
_EMAIL_PATTERN = re.compile(
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+",
    re.IGNORECASE,
)

Account = dict[str, str]


def is_authenticated_user(user_info: Mapping[str, object]) -> bool:
    return user_info.get("is_logged_in") is True


def authenticated_user_name(user_info: Mapping[str, object]) -> str:
    name = user_info.get("name")
    return name.strip() if isinstance(name, str) and name.strip() else "Student"


def authenticated_user_identity(
    user_info: Mapping[str, object],
) -> tuple[str, str] | None:
    if not is_authenticated_user(user_info):
        return None

    issuer = user_info.get("iss")
    subject = user_info.get("sub")
    if not isinstance(issuer, str) or not isinstance(subject, str):
        return None

    issuer = issuer.strip()
    subject = subject.strip()
    try:
        parsed_issuer = urlsplit(issuer)
        issuer_hostname = parsed_issuer.hostname
    except ValueError:
        return None
    if (
        parsed_issuer.scheme != "https"
        or not issuer_hostname
        or parsed_issuer.username is not None
        or parsed_issuer.password is not None
        or parsed_issuer.query
        or parsed_issuer.fragment
        or len(issuer) > 2048
        or not subject
        or len(subject) > 512
    ):
        return None
    return issuer, subject


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
