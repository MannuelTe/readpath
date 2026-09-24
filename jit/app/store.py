"""SQLite persistence for cached answers, sessions, evidence pages, and events."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS queries(
  id INTEGER PRIMARY KEY,
  cache_key TEXT UNIQUE NOT NULL,
  query TEXT NOT NULL,
  answer TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence(
  id INTEGER PRIMARY KEY,
  query_id INTEGER NOT NULL REFERENCES queries(id),
  slug TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at REAL NOT NULL,
  UNIQUE(query_id, slug)
);
CREATE TABLE IF NOT EXISTS sessions(
  session_id TEXT PRIMARY KEY,
  query_id INTEGER NOT NULL REFERENCES queries(id),
  goal TEXT,
  budget TEXT,
  scope TEXT,
  verification_plan TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS contextual_answers(
  id INTEGER PRIMARY KEY,
  query_id INTEGER NOT NULL REFERENCES queries(id),
  context_key TEXT NOT NULL,
  answer TEXT NOT NULL,
  created_at REAL NOT NULL,
  UNIQUE(query_id, context_key)
);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY,
  ts REAL NOT NULL,
  session_id TEXT,
  route TEXT NOT NULL,
  query_id INTEGER,
  details TEXT
);
CREATE INDEX IF NOT EXISTS events_session ON events(session_id, ts);
"""


def normalize_query(query: str) -> str:
    return " ".join(query.casefold().split())


def query_key(query: str) -> str:
    return hashlib.sha256(normalize_query(query).encode("utf-8")).hexdigest()[:16]


def context_key(context: dict[str, str]) -> str:
    packed = json.dumps(context, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()[:16]


class Store:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db_path = Path(self.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def get_query(self, key: str):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM queries WHERE cache_key=?", (key,)
            ).fetchone()

    def save_query(self, key: str, query: str, answer: str):
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO queries(cache_key,query,answer,created_at) VALUES(?,?,?,?)",
                (key, query, answer, time.time()),
            )
            return connection.execute(
                "SELECT * FROM queries WHERE cache_key=?", (key,)
            ).fetchone()

    def save_evidence(self, query_id: int, pages: list[dict[str, str]]) -> None:
        now = time.time()
        with self.connect() as connection:
            connection.executemany(
                "INSERT OR IGNORE INTO evidence(query_id,slug,title,body,created_at) VALUES(?,?,?,?,?)",
                [(query_id, p["slug"], p["title"], p["body"], now) for p in pages],
            )

    def list_evidence(self, query_id: int):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM evidence WHERE query_id=? ORDER BY id", (query_id,)
            ).fetchall()

    def get_evidence(self, key: str, slug: str):
        with self.connect() as connection:
            return connection.execute(
                """SELECT e.*, q.cache_key, q.query, q.answer
                   FROM evidence e JOIN queries q ON q.id=e.query_id
                   WHERE q.cache_key=? AND e.slug=?""",
                (key, slug),
            ).fetchone()

    def save_session(self, session_id: str, query_id: int, context: dict[str, str]) -> None:
        now = time.time()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO sessions(
                     session_id,query_id,goal,budget,scope,verification_plan,created_at,updated_at
                   ) VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(session_id) DO UPDATE SET
                     query_id=excluded.query_id, goal=excluded.goal, budget=excluded.budget,
                     scope=excluded.scope, verification_plan=excluded.verification_plan,
                     updated_at=excluded.updated_at""",
                (
                    session_id,
                    query_id,
                    context.get("goal", ""),
                    context.get("budget", ""),
                    context.get("scope", ""),
                    context.get("verification_plan", ""),
                    now,
                    now,
                ),
            )

    def get_contextual_answer(self, query_id: int, key: str):
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM contextual_answers WHERE query_id=? AND context_key=?",
                (query_id, key),
            ).fetchone()

    def save_contextual_answer(self, query_id: int, key: str, answer: str):
        with self.connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO contextual_answers(query_id,context_key,answer,created_at)
                   VALUES(?,?,?,?)""",
                (query_id, key, answer, time.time()),
            )
            return connection.execute(
                "SELECT * FROM contextual_answers WHERE query_id=? AND context_key=?",
                (query_id, key),
            ).fetchone()

    def log_event(
        self,
        route: str,
        session_id: str | None = None,
        query_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO events(ts,session_id,route,query_id,details) VALUES(?,?,?,?,?)",
                (time.time(), session_id, route, query_id, json.dumps(details or {})),
            )

    def list_events(self, session_id: str | None = None, limit: int = 500) -> list[dict]:
        sql = """SELECT e.id, e.ts, e.session_id, e.route, e.details, q.query, q.cache_key
                 FROM events e LEFT JOIN queries q ON q.id=e.query_id"""
        params: tuple = ()
        if session_id is not None:
            sql += " WHERE e.session_id=?"
            params = (session_id,)
        sql += " ORDER BY e.id DESC LIMIT ?"
        with self.connect() as connection:
            rows = connection.execute(sql, (*params, limit)).fetchall()
        events = [dict(row) | {"details": json.loads(row["details"] or "{}")} for row in rows]
        return events[::-1]

