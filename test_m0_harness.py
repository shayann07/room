import json
import tempfile
import unittest
from pathlib import Path

from m0_harness import Room, dry_run_plans, run


class M0HarnessTests(unittest.TestCase):
    def test_event_ids_and_idempotent_ack(self):
        with tempfile.TemporaryDirectory() as d:
            room = Room(Path(d) / "events.json")
            event = room.post("nawaz", "hello", recipients=("claude",))
            duplicate = room.post("nawaz", "hello", recipients=(), idempotency_key="hello:1")
            self.assertEqual(duplicate["id"], 2)
            duplicate_again = room.post("nawaz", "hello", recipients=(), idempotency_key="hello:1")
            self.assertEqual(duplicate_again["id"], duplicate["id"])
            with self.assertRaises(ValueError):
                room.post("nawaz", "changed", recipients=(), idempotency_key="hello:1")
            with self.assertRaises(PermissionError):
                room.post_agent("forged-agent", "not a real participant")
            self.assertEqual(event["id"], 1)
            self.assertEqual(len(room.deliver("claude")), 1)
            room.acknowledge("claude", 1)
            room.acknowledge("claude", 1)
            self.assertEqual(room.outbox["claude"][0]["state"], "acknowledged")

    def test_m0_scenarios_and_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            checks = run(Path(d))
            self.assertTrue(all(v for k, v in checks.items() if k != "idle_wake"))
            self.assertFalse(checks["idle_wake"])
            self.assertTrue((Path(d) / "capability-matrix.json").exists())
            self.assertTrue((Path(d) / "pass-fail.json").exists())
            self.assertTrue((Path(d) / "dry-run-adapter-plans.json").exists())

    def test_rerun_starts_a_fresh_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            first = run(out)
            first_events = json.loads((out / "room-events.json").read_text())
            second = run(out)
            second_events = json.loads((out / "room-events.json").read_text())
            self.assertEqual(first, second)
            self.assertEqual(first_events, second_events)

    def test_dry_run_contains_no_execution_request(self):
        plans = dry_run_plans()
        self.assertEqual({p["participant"] for p in plans}, {"claude", "codex", "antigravity"})
        self.assertTrue(all(p["executed"] is False for p in plans))


if __name__ == "__main__":
    unittest.main()
