"""SQLite/WAL Room backend used to validate the authoritative-store boundary."""
from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from m0_harness import AGENT_IDS


class SQLiteRoom:
    def __init__(self, path: Path, initialize: bool = True):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=5, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        try:
            self.conn.execute("PRAGMA busy_timeout=10000")
            if initialize:
                for attempt in range(40):
                    try:
                        self.conn.execute("PRAGMA journal_mode=WAL")
                        break
                    except sqlite3.OperationalError as exc:
                        if "locked" not in str(exc).lower() or attempt == 39:
                            raise
                        time.sleep(0.05)
                self.conn.execute("PRAGMA synchronous=NORMAL")
                self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT NOT NULL,
                    text TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    event_id INTEGER NOT NULL REFERENCES events(id),
                    recipient TEXT NOT NULL,
                    state TEXT NOT NULL,
                    PRIMARY KEY (event_id, recipient)
                );
                """
                )
        except Exception:
            self.conn.close()
            raise

    @property
    def events(self):
        with self.lock:
            rows = self.conn.execute("SELECT id, author, text, kind, idempotency_key FROM events ORDER BY id").fetchall()
            return [{k: row[k] for k in ("id", "author", "text", "kind") if row[k] is not None} | ({"idempotency_key": row["idempotency_key"]} if row["idempotency_key"] is not None else {}) for row in rows]

    @property
    def outbox(self):
        with self.lock:
            rows = self.conn.execute("SELECT event_id, recipient, state FROM outbox ORDER BY event_id, recipient").fetchall()
            result = {}
            for row in rows:
                result.setdefault(row["recipient"], []).append({"event_id": row["event_id"], "state": row["state"]})
            return result

    @property
    def idempotency(self):
        with self.lock:
            rows = self.conn.execute("SELECT idempotency_key, id FROM events WHERE idempotency_key IS NOT NULL").fetchall()
            return {row["idempotency_key"]: row["id"] for row in rows}

    def _event(self, event_id):
        row = self.conn.execute("SELECT id, author, text, kind, idempotency_key FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise KeyError(event_id)
        return {k: row[k] for k in ("id", "author", "text", "kind") if row[k] is not None} | ({"idempotency_key": row["idempotency_key"]} if row["idempotency_key"] is not None else {})

    def post(self, author: str, text: str, kind: str = "message", recipients=(), idempotency_key: str | None = None):
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                if idempotency_key:
                    old = self.conn.execute("SELECT id, author, text, kind FROM events WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
                    if old:
                        if (old["author"], old["text"], old["kind"]) != (author, text, kind):
                            raise ValueError(f"idempotency key reused with different payload: {idempotency_key}")
                        self.conn.execute("COMMIT")
                        return self._event(old["id"])
                cursor = self.conn.execute("INSERT INTO events(author, text, kind, idempotency_key) VALUES (?, ?, ?, ?)", (author, text, kind, idempotency_key))
                event_id = cursor.lastrowid
                self.conn.executemany("INSERT INTO outbox(event_id, recipient, state) VALUES (?, ?, 'queued')", [(event_id, recipient) for recipient in dict.fromkeys(recipients)])
                self.conn.execute("COMMIT")
                return self._event(event_id)
            except Exception:
                self.conn.execute("ROLLBACK")
                raise

    def post_agent(self, participant_id: str, text: str, kind: str = "message", recipients=(), idempotency_key: str | None = None):
        if participant_id not in AGENT_IDS:
            raise PermissionError(f"unknown agent identity: {participant_id}")
        return self.post(participant_id, text, kind, recipients, idempotency_key)

    def deliver(self, participant: str, connected: bool = True):
        if not connected:
            return []
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            self.conn.execute("UPDATE outbox SET state = 'delivered' WHERE recipient = ? AND state = 'queued'", (participant,))
            rows = self.conn.execute("SELECT event_id, state FROM outbox WHERE recipient = ? AND state = 'delivered' ORDER BY event_id", (participant,)).fetchall()
            self.conn.execute("COMMIT")
            return [{"event_id": row["event_id"], "state": row["state"]} for row in rows]

    def acknowledge(self, participant: str, event_id: int):
        with self.lock:
            self.conn.execute("UPDATE outbox SET state = 'acknowledged' WHERE recipient = ? AND event_id = ?", (participant, event_id))

    def close(self):
        self.conn.close()
