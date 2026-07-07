"""SQLite persistence for SmartSeg authentication and analysis history."""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(os.getenv("SMARTSEG_DB_PATH", "./api_data/smartseg.db"))
DEFAULT_EMAIL = os.getenv("SMARTSEG_AUTH_EMAIL", "analyst@ooredoo.com").lower()
DEFAULT_PASSWORD = os.getenv("SMARTSEG_AUTH_PASSWORD", "SmartSeg2026!")
DEFAULT_ROLE = "Marketing Analyst"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    password_salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt.encode("utf-8"),
        120_000,
    ).hex()
    return password_salt, password_hash


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, candidate_hash = hash_password(password, salt)
    return hmac.compare_digest(candidate_hash, password_hash)


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                dataset_name TEXT,
                algorithm TEXT,
                n_clusters INTEGER,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (DEFAULT_EMAIL,),
        ).fetchone()

        if existing is None:
            salt, password_hash = hash_password(DEFAULT_PASSWORD)
            connection.execute(
                """
                INSERT INTO users (email, password_hash, password_salt, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    DEFAULT_EMAIL,
                    password_hash,
                    salt,
                    DEFAULT_ROLE,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, email, password_hash, password_salt, role FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, email, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def save_analysis(
    *,
    user_id: int,
    title: str,
    dataset_name: Optional[str],
    algorithm: Optional[str],
    n_clusters: Optional[int],
    result: dict[str, Any],
) -> sqlite3.Row:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses
                (user_id, title, dataset_name, algorithm, n_clusters, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                dataset_name,
                algorithm,
                n_clusters,
                json.dumps(result),
                created_at,
            ),
        )
        return connection.execute(
            """
            SELECT id, title, dataset_name, algorithm, n_clusters, created_at
            FROM analyses
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()


def list_analyses(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, title, dataset_name, algorithm, n_clusters, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (user_id,),
        ).fetchall()


def get_analysis(user_id: int, analysis_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, title, dataset_name, algorithm, n_clusters, result_json, created_at
            FROM analyses
            WHERE user_id = ? AND id = ?
            """,
            (user_id, analysis_id),
        ).fetchone()
