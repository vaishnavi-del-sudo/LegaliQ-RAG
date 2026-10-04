from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DB_PATH


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                issue TEXT NOT NULL,
                model TEXT NOT NULL,
                language TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(review_id) REFERENCES reviews(id)
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 150_000).hex()


def create_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    salt = os.urandom(16).hex()
    password_hash = _hash_password(password, salt)
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
                (email, password_hash, salt, now_iso()),
            )
        return True, "Account created. You can sign in now."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."


def verify_user(email: str, password: str) -> dict[str, Any] | None:
    email = email.strip().lower()
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row and _hash_password(password, row["salt"]) == row["password_hash"]:
        return dict(row)
    return None


def add_review(user_id: int, title: str, topic: str, issue: str, model: str, language: str, response: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO reviews (user_id, title, topic, issue, model, language, response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, topic, issue, model, language, response, now_iso()),
        )
        review_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO messages (review_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (review_id, "assistant", response, now_iso()),
        )
    return review_id


def add_message(review_id: int, role: str, content: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO messages (review_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (review_id, role, content, now_iso()),
        )


def add_document(user_id: int, filename: str, summary: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO documents (user_id, filename, summary, created_at) VALUES (?, ?, ?, ?)",
            (user_id, filename, summary, now_iso()),
        )
        return int(cur.lastrowid)


def get_reviews(user_id: int, query: str = "") -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM reviews
            WHERE user_id = ? AND (? = '%%' OR title LIKE ? OR topic LIKE ? OR issue LIKE ? OR response LIKE ?)
            ORDER BY created_at DESC
            """,
            (user_id, like, like, like, like, like),
        ).fetchall()
    return [dict(row) for row in rows]


def get_documents(user_id: int, query: str = "") -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM documents
            WHERE user_id = ? AND (? = '%%' OR filename LIKE ? OR summary LIKE ?)
            ORDER BY created_at DESC
            """,
            (user_id, like, like, like),
        ).fetchall()
    return [dict(row) for row in rows]


def get_messages(review_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE review_id = ? ORDER BY id ASC",
            (review_id,),
        ).fetchall()
    return [dict(row) for row in rows]
