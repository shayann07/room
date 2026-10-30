import subprocess
import tempfile
import unittest
from pathlib import Path

from room_lifecycle import RoomLifecycle


class RoomLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="room-test-")
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        run = lambda *args: subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, text=True)
        run("init", "-q")
        run("config", "user.email", "room@test")
        run("config", "user.name", "Room Test")
        (self.repo / "tracked.txt").write_text("base\n")
        run("add", ".")
        run("commit", "-qm", "base")
        self.room = RoomLifecycle(self.repo)
        self.room.ack("claude", 0)

    def tearDown(self):
        self.room.close()
        self.tmp.cleanup()

    def test_quota_handoff_captures_complete_wip_and_isolates_steward(self):
        self.room.claim("claude", "T1", "implement upload retry", "tracked.txt,new.txt,delete.txt")
        (self.repo / "tracked.txt").write_text("tracked edit\n")
        (self.repo / "new.txt").write_bytes(b"new\x00binary")
        (self.repo / "delete.txt").write_text("remove\n")
        subprocess.run(["git", "add", "delete.txt"], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "delete.txt").unlink()

        ref, _ = self.room.limit("claude", "codex")
        self.assertTrue((self.repo / "tracked.txt").exists(), "handoff must not clean working tree")
        self.assertIn("tracked edit", subprocess.run(["git", "show", f"{ref}:tracked.txt"], cwd=self.repo, text=True, capture_output=True, check=True).stdout)
        self.assertIn("new", subprocess.run(["git", "show", f"{ref}:new.txt"], cwd=self.repo, text=True, capture_output=True, check=True).stdout)
        self.assertNotEqual(subprocess.run(["git", "cat-file", "-e", f"{ref}:delete.txt"], cwd=self.repo).returncode, 0)

        steward = Path(self.tmp.name) / "codex-worktree"
        self.room.create_steward_worktree("codex", ref, steward)
        self.assertEqual((steward / "tracked.txt").read_text(), "tracked edit\n")
        self.assertTrue((steward / "new.txt").exists())

    def test_stale_claude_is_fenced_until_pulse_and_ack(self):
        self.room.claim("claude", "T1", "edit", "tracked.txt")
        self.room.limit("claude", "codex")
        with self.assertRaisesRegex(RuntimeError, "STALE_SESSION"):
            self.room.assert_fresh("claude")
        current = self.room.pulse("claude")["epoch"]
        self.room.ack("claude", current)
        self.room.assert_fresh("claude")


if __name__ == "__main__":
    unittest.main()
