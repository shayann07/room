import unittest

from room_kernel import compile_packet, validate_receipt


class RoomKernelTests(unittest.TestCase):
    def test_packet_is_deterministic_and_hashed(self):
        kwargs = dict(project="upscaly", revision=3, assignment={"id": "checkout", "scope": "ui"},
                      charter="keep auth", decisions=[], questions=[], evidence=[])
        first = compile_packet(**kwargs)
        second = compile_packet(**kwargs)
        self.assertEqual(first["packet_hash"], second["packet_hash"])

    def test_stale_or_forged_receipts_do_not_advance_work(self):
        packet = compile_packet(project="upscaly", revision=3, assignment={"id": "x"},
                                charter="", decisions=[], questions=[], evidence=[])
        ok, _ = validate_receipt({"packet_hash": packet["packet_hash"], "assignment_epoch": 2, "status": "submitted"}, packet, 3)
        self.assertFalse(ok)
        ok, _ = validate_receipt({"packet_hash": "forged", "assignment_epoch": 3, "status": "submitted"}, packet, 3)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
