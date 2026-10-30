import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from live_smoke_runner import PROMPT, command_for, main


class LiveSmokeRunnerTests(unittest.TestCase):
    def test_commands_are_bounded_and_do_not_bypass_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            workdir = Path(d)
            for provider in ("claude", "codex", "antigravity"):
                command = command_for(provider, workdir)
                self.assertTrue(any("ROOM_M0_ACK" in arg for arg in command))
                self.assertNotIn("--dangerously-skip-permissions", command)
                self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
                self.assertNotIn("--dangerously-skip-permissions", command)

    def test_confirmation_gate_rejects_wrong_token(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--confirm", "NO", "--provider", "claude"])


if __name__ == "__main__":
    unittest.main()
