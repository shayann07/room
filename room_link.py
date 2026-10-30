"""Canonical local Room Link protocol primitives.

This is intentionally a small, provider-neutral API. Provider sidecars can
adapt Codex, Claude, or Antigravity to it without making MCP part of Room's
authority model.
"""
from __future__ import annotations

import hashlib
import secrets
import threading
from pathlib import Path

from room_sqlite import SQLiteRoom


class RoomLinkService:
    def __init__(self, db_path: Path, project: str = "default"):
        self.room = SQLiteRoom(db_path)
        self.project = project
        self._tokens: dict[str, str] = {}
        self._lock = threading.RLock()
        self._baton = {"revision": 0, "lead": "nawaz", "charter": "", "assignments": {}}

    def issue_token(self, participant: str) -> str:
        if participant not in {"nawaz", "claude", "codex", "antigravity"}:
            raise PermissionError("unknown participant")
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._tokens[hashlib.sha256(token.encode()).hexdigest()] = participant
        return token

    def _participant(self, token: str) -> str:
        participant = self._tokens.get(hashlib.sha256(token.encode()).hexdigest())
        if not participant:
            raise PermissionError("invalid connector token")
        return participant

    def check_in(self, token: str, cursor: int = 0):
        participant = self._participant(token)
        return {
            "project": self.project,
            "participant": participant,
            "cursor": cursor,
            "baton": dict(self._baton),
            "events": [event for event in self.room.events if event["id"] > cursor],
        }

    def post(self, token: str, text: str, kind: str = "message", idempotency_key: str | None = None):
        participant = self._participant(token)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("non-empty text is required")
        return self.room.post(participant, text, kind, idempotency_key=idempotency_key)

    def claim(self, token: str, assignment: str, baton_revision: int):
        participant = self._participant(token)
        with self._lock:
            if baton_revision != self._baton["revision"]:
                raise ValueError("stale baton revision")
            owner = self._baton["assignments"].get(assignment)
            if owner and owner != participant:
                raise ValueError("assignment already claimed")
            self._baton["assignments"][assignment] = participant
            return {"assignment": assignment, "participant": participant, "baton_revision": baton_revision}

    def revise_baton(self, token: str, charter: str | None = None, lead: str | None = None):
        participant = self._participant(token)
        with self._lock:
            if participant not in {"nawaz", self._baton["lead"]}:
                raise PermissionError("only owner or current lead may revise baton")
            self._baton["revision"] += 1
            if charter is not None:
                self._baton["charter"] = charter
            if lead is not None:
                if lead not in {"claude", "codex", "antigravity"}:
                    raise ValueError("invalid lead")
                self._baton["lead"] = lead
            return dict(self._baton)

    def close(self):
        self.room.close()
