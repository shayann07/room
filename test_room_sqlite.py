import multiprocessing
import tempfile
import unittest
from pathlib import Path

from room_sqlite import SQLiteRoom


def worker(db, participant, index):
    room = SQLiteRoom(Path(db))
    try:
        room.post_agent(participant, f"message-{index}", recipients=("nawaz",), idempotency_key=f"message:{index}")
    finally:
        room.close()


class SQLiteRoomTests(unittest.TestCase):
    def test_wal_persistence_idempotency_and_identity(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "room.sqlite3"
            room = SQLiteRoom(path)
            assignment = room.post("nawaz", "Implement checkout", "assignment", ("claude", "codex"), "assignment:1")
            self.assertEqual(room.post("nawaz", "Implement checkout", "assignment", (), "assignment:1")["id"], assignment["id"])
            with self.assertRaises(ValueError):
                room.post("nawaz", "Changed", "assignment", (), "assignment:1")
            with self.assertRaises(PermissionError):
                room.post_agent("forged", "no")
            self.assertEqual(room.conn.execute("PRAGMA journal_mode").fetchone()[0].lower(), "wal")
            room.close()
            reopened = SQLiteRoom(path)
            self.assertEqual(reopened.events[0]["id"], 1)
            self.assertEqual(reopened.outbox["claude"][0]["state"], "queued")
            reopened.close()

    def test_concurrent_processes_do_not_lose_events(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "room.sqlite3"
            initialized = SQLiteRoom(path)
            initialized.close()
            processes = [multiprocessing.Process(target=worker, args=(str(path), participant, index)) for index, participant in enumerate(("claude", "codex", "antigravity"), start=1)]
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=5)
                self.assertEqual(process.exitcode, 0)
            room = SQLiteRoom(path)
            self.assertEqual({event["text"] for event in room.events}, {"message-1", "message-2", "message-3"})
            room.close()


if __name__ == "__main__":
    unittest.main()
