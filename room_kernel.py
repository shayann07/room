"""Deterministic state-to-turn-packet compiler for Room."""
from __future__ import annotations

import hashlib
import json


def compile_packet(*, project: str, revision: int, assignment: dict, charter: str,
                   decisions: list[dict], questions: list[dict], evidence: list[dict]) -> dict:
    payload = {
        "project": project,
        "room_revision": revision,
        "assignment": assignment,
        "charter": charter,
        "binding_decisions": decisions,
        "open_questions": questions,
        "evidence": evidence,
        "required_receipt": ["accepted", "progress", "question", "blocked", "submitted", "stopped"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["packet_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def validate_receipt(receipt: dict, packet: dict, current_epoch: int) -> tuple[bool, str]:
    if receipt.get("packet_hash") != packet["packet_hash"]:
        return False, "packet hash mismatch"
    if receipt.get("assignment_epoch") != current_epoch:
        return False, "stale assignment epoch"
    if receipt.get("status") not in packet["required_receipt"]:
        return False, "unknown receipt status"
    return True, "accepted"
