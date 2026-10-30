"""Local Room lifecycle proof: quota handoff, fencing, and isolated worktrees."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path


class RoomLifecycle:
    def __init__(self, repo: Path):
        self.repo = Path(repo)
        self.room = self.repo / ".room"
        self.room.mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.room / "state.db")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY CHECK(id=1), epoch INTEGER NOT NULL);
            INSERT OR IGNORE INTO meta VALUES (1, 0);
            CREATE TABLE IF NOT EXISTS sessions (agent TEXT PRIMARY KEY, ack_epoch INTEGER NOT NULL, role TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, owner TEXT, intent TEXT, files TEXT, status TEXT NOT NULL, wip_ref TEXT);
            CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, epoch INTEGER, kind TEXT, detail TEXT);
        """)
        for agent, role in (("claude", "LEAD"), ("codex", "CONTRIBUTOR"), ("antigravity", "CONTRIBUTOR")):
            self.db.execute("INSERT OR IGNORE INTO sessions VALUES (?, 0, ?)", (agent, role))
        self.db.commit()

    def epoch(self):
        return self.db.execute("SELECT epoch FROM meta WHERE id=1").fetchone()[0]

    def _bump(self, kind, detail):
        epoch = self.epoch() + 1
        self.db.execute("UPDATE meta SET epoch=? WHERE id=1", (epoch,))
        self.db.execute("INSERT INTO events(epoch, kind, detail) VALUES (?, ?, ?)", (epoch, kind, detail))
        self.db.commit()
        return epoch

    def claim(self, agent, task, intent, files):
        seen = self.db.execute("SELECT ack_epoch FROM sessions WHERE agent=?", (agent,)).fetchone()[0]
        if seen != self.epoch():
            raise RuntimeError("STALE_SESSION")
        row = self.db.execute("SELECT owner,status FROM tasks WHERE id=?", (task,)).fetchone()
        if row and row[1] == "IN_PROGRESS" and row[0] != agent:
            raise RuntimeError("LEASE_HELD")
        self._bump("CLAIM", f"{agent}:{task}:{intent}")
        self.db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, 'IN_PROGRESS', NULL)", (task, agent, intent, files))
        self.db.execute("UPDATE sessions SET ack_epoch=? WHERE agent=?", (self.epoch(), agent))
        self.db.commit()

    def pulse(self, agent):
        return {"agent": agent, "epoch": self.epoch(), "events": self.db.execute("SELECT epoch,kind,detail FROM events ORDER BY epoch").fetchall()}

    def ack(self, agent, epoch):
        if epoch != self.epoch():
            raise RuntimeError("WRONG_EPOCH")
        self.db.execute("UPDATE sessions SET ack_epoch=? WHERE agent=?", (epoch, agent))
        self.db.commit()

    def assert_fresh(self, agent):
        seen = self.db.execute("SELECT ack_epoch FROM sessions WHERE agent=?", (agent,)).fetchone()[0]
        if seen != self.epoch():
            raise RuntimeError("STALE_SESSION")

    def _git(self, *args, env=None, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, env=env, text=True, capture_output=True, check=True).stdout.strip()

    def full_wip_snapshot(self, agent):
        """Capture final dirty tree, including untracked/deleted/binary/mode changes."""
        next_epoch = self.epoch() + 1
        tmp_index = self.room / f"wip-index-{next_epoch}"
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(tmp_index)
        try:
            self._git("read-tree", "HEAD", env=env)
            self._git("add", "-A", env=env)
            tree = self._git("write-tree", env=env)
            parent = self._git("rev-parse", "HEAD")
            commit = subprocess.run(
                ["git", "commit-tree", tree, "-p", parent], cwd=self.repo, env=env,
                input=f"Room WIP snapshot epoch {next_epoch} ({agent})\n", text=True,
                capture_output=True, check=True,
            ).stdout.strip()
            ref = f"refs/room/wip/epoch-{next_epoch}-{agent}"
            self._git("update-ref", ref, commit)
            return ref, commit
        finally:
            tmp_index.unlink(missing_ok=True)

    def limit(self, agent, steward):
        ref, commit = self.full_wip_snapshot(agent)
        epoch = self._bump("LIMIT", f"{agent} quota; steward={steward}; wip={ref}")
        self.db.execute("UPDATE tasks SET status='INTERRUPTED_WIP', owner=NULL, wip_ref=? WHERE owner=? AND status='IN_PROGRESS'", (ref, agent))
        self.db.execute("UPDATE sessions SET role='LEAD_ON_HOLD' WHERE agent=?", (agent,))
        self.db.execute("UPDATE sessions SET role='STEWARD', ack_epoch=? WHERE agent=?", (epoch, steward))
        self.db.commit()
        return ref, commit

    def create_steward_worktree(self, steward, ref, path):
        path = Path(path)
        self._git("worktree", "add", "--detach", str(path), ref)
        return path

    def close(self):
        self.db.close()


def demo():
    with tempfile.TemporaryDirectory(prefix="room-lifecycle-") as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "room@test"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Room Test"], cwd=repo, check=True)
        (repo / "tracked.txt").write_text("base\n")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
        room = RoomLifecycle(repo)
        try:
            room.ack("claude", 0)
            room.claim("claude", "T1", "edit tracked and create new file", "tracked.txt,new.txt")
            (repo / "tracked.txt").write_text("claude partial\n")
            (repo / "new.txt").write_bytes(b"untracked binary\x00")
            ref, _ = room.limit("claude", "codex")
            worktree = room.create_steward_worktree("codex", ref, repo.parent / "codex-worktree")
            room.assert_fresh("claude")
        except RuntimeError as exc:
            if str(exc) != "STALE_SESSION":
                raise
        finally:
            room.close()
        return {"wip_ref": ref, "steward_worktree": str(worktree)}


if __name__ == "__main__":
    print(demo())
