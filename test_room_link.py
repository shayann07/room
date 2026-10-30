import tempfile
import unittest
from pathlib import Path

from room_link import RoomLinkService


class RoomLinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = RoomLinkService(Path(self.tmp.name) / "room.sqlite3", "upscaly")
        self.nawaz = self.service.issue_token("nawaz")
        self.codex = self.service.issue_token("codex")
        self.claude = self.service.issue_token("claude")

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def test_check_in_and_authenticated_post(self):
        self.service.post(self.nawaz, "Keep the auth decision", idempotency_key="m1")
        sync = self.service.check_in(self.codex)
        self.assertEqual(sync["participant"], "codex")
        self.assertEqual(sync["events"][0]["text"], "Keep the auth decision")
        with self.assertRaises(PermissionError):
            self.service.post("forged", "pretend to be Claude")

    def test_stale_baton_cannot_claim(self):
        revision = self.service.check_in(self.codex)["baton"]["revision"]
        self.service.revise_baton(self.nawaz, charter="Finish checkout")
        with self.assertRaises(ValueError):
            self.service.claim(self.codex, "checkout-review", revision)

    def test_only_owner_or_lead_revises(self):
        with self.assertRaises(PermissionError):
            self.service.revise_baton(self.codex, charter="hijack")
        self.service.revise_baton(self.nawaz, lead="claude")
        self.service.revise_baton(self.claude, charter="Lead-approved")
        self.assertEqual(self.service.check_in(self.codex)["baton"]["revision"], 2)


if __name__ == "__main__":
    unittest.main()
