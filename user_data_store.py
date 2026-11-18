"""SQLite persistence for authenticated users' career assessment data."""

import json
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import urlsplit

from career_data import (
    CAREERS,
    EDUCATION_OPTIONS,
    EXPERIENCE_OPTIONS,
    FIELD_OPTIONS,
    assessment_interest_options,
    assessment_skill_options,
)
from roadmap_progress import roadmap_phase_entries

DATABASE_PATH = Path(__file__).resolve().parent / ".local_data" / "career_predictor.sqlite3"
SCHEMA_VERSION = 1
PROFILE_FIELDS = frozenset(
    {
        "name",
        "age",
        "education",
        "field",
        "experience",
        "skills",
        "interests",
        "confirmed_skills",
        "confirmed_interests",
    }
)
_CAREERS_BY_ID = {
    career["id"]: career
    for career in CAREERS
    if isinstance(career.get("id"), str) and career["id"].strip()
}
_SKILL_OPTIONS = frozenset(assessment_skill_options())
_INTEREST_OPTIONS = frozenset(assessment_interest_options())


def _validate_identity(issuer: object, subject: object) -> tuple[str, str]:
    if not isinstance(issuer, str) or not isinstance(subject, str):
        raise ValueError("A valid authenticated issuer and subject are required.")

    issuer = issuer.strip()
    subject = subject.strip()
    try:
        parsed_issuer = urlsplit(issuer)
        issuer_hostname = parsed_issuer.hostname
    except ValueError as error:
        raise ValueError("A valid authenticated issuer and subject are required.") from error
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
        raise ValueError("A valid authenticated issuer and subject are required.")
    return issuer, subject


def _validate_profile(profile: object) -> dict[str, object]:
    if not isinstance(profile, Mapping) or set(profile) != PROFILE_FIELDS:
        raise ValueError("The assessment profile has an invalid structure.")

    name = profile["name"]
    age = profile["age"]
    education = profile["education"]
    field = profile["field"]
    experience = profile["experience"]
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        raise ValueError("The assessment profile contains an invalid name.")
    if isinstance(age, bool) or not isinstance(age, int) or not 15 <= age <= 80:
        raise ValueError("The assessment profile contains an invalid age.")
    if education not in EDUCATION_OPTIONS:
        raise ValueError("The assessment profile contains an invalid education level.")
    if field not in FIELD_OPTIONS:
        raise ValueError("The assessment profile contains an invalid field of study.")
    if experience not in EXPERIENCE_OPTIONS:
        raise ValueError("The assessment profile contains an invalid experience level.")

    result: dict[str, object] = {
        "name": name.strip(),
        "age": age,
        "education": education,
        "field": field,
        "experience": experience,
    }
    for field_name, allowed_values in (
        ("skills", _SKILL_OPTIONS),
        ("confirmed_skills", _SKILL_OPTIONS),
        ("interests", _INTEREST_OPTIONS),
        ("confirmed_interests", _INTEREST_OPTIONS),
    ):
        values = profile[field_name]
        if (
            not isinstance(values, (list, tuple))
            or any(not isinstance(value, str) or value not in allowed_values for value in values)
            or len(values) != len(set(values))
        ):
            raise ValueError(f"The assessment profile contains invalid {field_name.replace('_', ' ')}.")
        result[field_name] = list(values)

    if not set(result["confirmed_skills"]).issubset(result["skills"]):
        raise ValueError("Confirmed skills must be selected in the assessment.")
    if not set(result["confirmed_interests"]).issubset(result["interests"]):
        raise ValueError("Confirmed interests must be selected in the assessment.")
    return result


def _validate_career_id(career_id: object) -> str:
    if not isinstance(career_id, str) or career_id not in _CAREERS_BY_ID:
        raise ValueError("The career identifier is not in the career catalog.")
    return career_id


def _validate_phase_id(career_id: str, phase_id: object) -> str:
    if not isinstance(phase_id, str):
        raise ValueError("The roadmap phase identifier is invalid.")
    valid_phase_ids = {
        current_phase_id
        for current_phase_id, _ in roadmap_phase_entries(
            _CAREERS_BY_ID[career_id].get("roadmap")
        )
    }
    if phase_id not in valid_phase_ids:
        raise ValueError("The roadmap phase identifier is invalid.")
    return phase_id


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def _database_connection() -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _initialize_schema(connection: sqlite3.Connection) -> None:
    with connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError("The user-data database schema is newer than this application.")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                issuer TEXT NOT NULL,
                subject TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (issuer, subject)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assessment_profiles (
                issuer TEXT NOT NULL,
                subject TEXT NOT NULL,
                profile_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (issuer, subject),
                FOREIGN KEY (issuer, subject)
                    REFERENCES users (issuer, subject)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_careers (
                issuer TEXT NOT NULL,
                subject TEXT NOT NULL,
                career_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                PRIMARY KEY (issuer, subject, career_id),
                FOREIGN KEY (issuer, subject)
                    REFERENCES users (issuer, subject)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS roadmap_progress (
                issuer TEXT NOT NULL,
                subject TEXT NOT NULL,
                career_id TEXT NOT NULL,
                phase_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (issuer, subject, career_id, phase_id),
                FOREIGN KEY (issuer, subject)
                    REFERENCES users (issuer, subject)
                    ON DELETE CASCADE
            )
            """
        )
        if version == 0:
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_user(
    connection: sqlite3.Connection,
    issuer: str,
    subject: str,
) -> None:
    now = _timestamp()
    connection.execute(
        """
        INSERT INTO users (issuer, subject, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (issuer, subject)
        DO UPDATE SET updated_at = excluded.updated_at
        """,
        (issuer, subject, now, now),
    )


def _validated_user(issuer: object, subject: object) -> tuple[str, str]:
    return _validate_identity(issuer, subject)


def load_user_data(issuer: str, subject: str) -> dict[str, object]:
    issuer, subject = _validated_user(issuer, subject)
    with _database_connection() as connection:
        _initialize_schema(connection)
        user = connection.execute(
            "SELECT 1 FROM users WHERE issuer = ? AND subject = ?",
            (issuer, subject),
        ).fetchone()
        if user is None:
            return {"profile": None, "saved_careers": [], "roadmap_progress": {}}

        profile_row = connection.execute(
            """
            SELECT profile_json FROM assessment_profiles
            WHERE issuer = ? AND subject = ?
            """,
            (issuer, subject),
        ).fetchone()
        saved_rows = connection.execute(
            """
            SELECT career_id FROM saved_careers
            WHERE issuer = ? AND subject = ?
            ORDER BY saved_at, career_id
            """,
            (issuer, subject),
        ).fetchall()
        roadmap_rows = connection.execute(
            """
            SELECT career_id, phase_id FROM roadmap_progress
            WHERE issuer = ? AND subject = ?
            ORDER BY career_id, phase_id
            """,
            (issuer, subject),
        ).fetchall()

    profile = None
    if profile_row is not None:
        profile = _validate_profile(json.loads(profile_row["profile_json"]))
    saved_careers = [
        _validate_career_id(row["career_id"])
        for row in saved_rows
    ]
    roadmap: dict[str, list[str]] = {}
    for row in roadmap_rows:
        career_id = _validate_career_id(row["career_id"])
        phase_id = _validate_phase_id(career_id, row["phase_id"])
        roadmap.setdefault(career_id, []).append(phase_id)
    return {
        "profile": profile,
        "saved_careers": saved_careers,
        "roadmap_progress": roadmap,
    }


def save_profile(issuer: str, subject: str, profile: object) -> None:
    issuer, subject = _validated_user(issuer, subject)
    validated_profile = _validate_profile(profile)
    profile_json = json.dumps(
        validated_profile,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    with _database_connection() as connection:
        _initialize_schema(connection)
        _ensure_user(connection, issuer, subject)
        connection.execute(
            """
            INSERT INTO assessment_profiles (issuer, subject, profile_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (issuer, subject)
            DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at
            """,
            (issuer, subject, profile_json, _timestamp()),
        )


def set_saved_career(
    issuer: str,
    subject: str,
    career_id: str,
    saved: bool,
) -> None:
    issuer, subject = _validated_user(issuer, subject)
    career_id = _validate_career_id(career_id)
    if not isinstance(saved, bool):
        raise ValueError("Saved state must be a boolean.")

    with _database_connection() as connection:
        _initialize_schema(connection)
        _ensure_user(connection, issuer, subject)
        if saved:
            connection.execute(
                """
                INSERT INTO saved_careers (issuer, subject, career_id, saved_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (issuer, subject, career_id) DO NOTHING
                """,
                (issuer, subject, career_id, _timestamp()),
            )
        else:
            connection.execute(
                """
                DELETE FROM saved_careers
                WHERE issuer = ? AND subject = ? AND career_id = ?
                """,
                (issuer, subject, career_id),
            )


def set_roadmap_phase(
    issuer: str,
    subject: str,
    career_id: str,
    phase_id: str,
    completed: bool,
) -> None:
    issuer, subject = _validated_user(issuer, subject)
    career_id = _validate_career_id(career_id)
    phase_id = _validate_phase_id(career_id, phase_id)
    if not isinstance(completed, bool):
        raise ValueError("Roadmap completion state must be a boolean.")

    with _database_connection() as connection:
        _initialize_schema(connection)
        _ensure_user(connection, issuer, subject)
        if completed:
            connection.execute(
                """
                INSERT INTO roadmap_progress
                    (issuer, subject, career_id, phase_id, completed_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (issuer, subject, career_id, phase_id)
                DO UPDATE SET completed_at = excluded.completed_at
                """,
                (issuer, subject, career_id, phase_id, _timestamp()),
            )
        else:
            connection.execute(
                """
                DELETE FROM roadmap_progress
                WHERE issuer = ? AND subject = ? AND career_id = ? AND phase_id = ?
                """,
                (issuer, subject, career_id, phase_id),
            )


def delete_user_data(issuer: str, subject: str) -> None:
    issuer, subject = _validated_user(issuer, subject)
    with _database_connection() as connection:
        _initialize_schema(connection)
        connection.execute(
            "DELETE FROM users WHERE issuer = ? AND subject = ?",
            (issuer, subject),
        )
