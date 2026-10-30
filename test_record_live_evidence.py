import json
import tempfile
import unittest
from pathlib import Path

from record_live_evidence import record


class LiveEvidenceTests(unittest.TestCase):
    def test_classifies_ack_limit_and_failure_without_launching_tools(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for provider in ("claude", "codex", "antigravity"):
                (root / "results" / provider).mkdir(parents=True)
            (root / "results" / "claude" / "result.json").write_text(json.dumps({"returncode": 1, "ack_text_seen": False, "file_changes": False, "timed_out": False, "structured_json_lines": 2}))
            (root / "results" / "claude" / "stdout.txt").write_text(json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected"}}) + "\n")
            for provider in ("codex", "antigravity"):
                (root / "results" / provider / "result.json").write_text(json.dumps({"returncode": 0, "ack_text_seen": True, "file_changes": False, "timed_out": False, "structured_json_lines": 2}))
                (root / "results" / provider / "stdout.txt").write_text(json.dumps({"type": "result"}) + "\n")
            summary = record(root)
            self.assertEqual({p["status"] for p in summary["providers"]}, {"weekly_limit", "acknowledged"})
            bridge = json.loads((root / "live-bridge-receipts.json").read_text())
            self.assertTrue(all(item["state"] in {"recorded", "ingested_by_local_bridge"} for item in bridge))


if __name__ == "__main__":
    unittest.main()
