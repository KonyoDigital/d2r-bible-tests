# -*- coding: utf-8 -*-
"""A missing reel_tombstones.json is none yet. A file that will not parse is UNKNOWN.

The loader in printer.py already said "no record yet". The census, the on-disk station,
and river_walk threw that sentence away and printed "could not be read", so a console
that has never retired a reel looked like a broken ledger. control_app's own readers
already kept the two facts apart; this law pins them so they cannot collapse again.

A count of zero is neither of those facts. reels stays None on both the missing path
and the corrupt path.
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


class TestAMissingTombstoneIsNoneYet(unittest.TestCase):

    def test_a_missing_file_stays_none_yet_through_the_census_and_the_walk(self):
        import printer as P
        import river_walk as RW
        missing = os.path.join(HERE, "reel_tombstones.json.not-here-%d" % os.getpid())
        blob, why = P._load_tombstones(missing)
        self.assertIsNone(blob)
        cen = P._tombstone_census(blob, why)
        self.assertFalse(cen.get("ok"))
        self.assertIsNone(cen.get("reels"), "a missing ledger reported a count")
        self.assertIn("no record yet", cen.get("why") or "")
        self.assertNotIn("could not be read", cen.get("why") or "",
                         "a missing file was reported as unreadable: %r" % cen.get("why"))
        said = P._tombstone_unknown_why(why)
        self.assertIn("no record yet", said)
        self.assertNotIn("could not be read", said)
        far = RW._far_end({"tombstoned": cen}, {"counts": {"TOMBSTONE": 0}})
        self.assertIn("no record yet", far.get("why") or "")
        self.assertNotIn("could not be read", far.get("why") or "",
                         "the walk rewrote none yet as unreadable: %r" % far.get("why"))

    def test_a_corrupt_file_stays_unknown_and_is_not_none_yet(self):
        import printer as P
        import river_walk as RW
        fd, path = tempfile.mkstemp(prefix="tomb-corrupt-", suffix=".json")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{")
            blob, why = P._load_tombstones(path)
            self.assertIsNone(blob)
            cen = P._tombstone_census(blob, why)
            self.assertIsNone(cen.get("reels"))
            self.assertIn("could not be read", cen.get("why") or "")
            self.assertNotIn("no record yet", cen.get("why") or "")
            said = P._tombstone_unknown_why(why)
            self.assertIn("could not be read", said)
            self.assertNotIn("no record yet", said)
            far = RW._far_end({"tombstoned": cen}, {})
            self.assertIn("could not be read", far.get("why") or "")
        finally:
            os.unlink(path)

    def test_no_reason_is_still_unreadable_never_none_yet(self):
        """A None blob with no loader sentence is the old UNKNOWN, not a new absence."""
        import printer as P
        cen = P._tombstone_census(None)
        self.assertIsNone(cen.get("reels"))
        self.assertIn("could not be read", cen.get("why") or "")
        self.assertNotIn("no record yet", cen.get("why") or "")

    def test_a_real_record_is_still_a_count(self):
        import printer as P
        cen = P._tombstone_census({"reels": [{"reel": "a", "mb": 1.5}]})
        self.assertTrue(cen.get("ok"))
        self.assertEqual(cen.get("reels"), 1)
        self.assertEqual(cen.get("mb"), 1.5)

    def test_control_app_names_a_missing_ledger_as_none_yet(self):
        import control_app as CA
        import reel_retention as RR
        import unittest.mock as mock
        missing = os.path.join(HERE, "reel_tombstones.json.not-here-%d" % os.getpid())
        mouth = CA.river_mouth(path=missing)
        self.assertFalse(mouth.get("ok"))
        self.assertIsNone(mouth.get("n"), "a missing ledger reported n=%r" % mouth.get("n"))
        self.assertNotIn("could not be read", str(mouth.get("why") or ""))
        self.assertIn("no tombstone ledger", str(mouth.get("why") or ""))
        with mock.patch.object(RR, "_tombstone_path", lambda *a, **k: missing):
            view = CA.tombstone_view()
        self.assertFalse(view.get("ok"))
        self.assertIsNone(view.get("reels"))
        why = str(view.get("why") or "")
        self.assertNotIn("could not be read", why)
        self.assertIn("exists yet", why)

    def test_control_app_names_a_corrupt_ledger_as_unknown(self):
        import control_app as CA
        import reel_retention as RR
        import unittest.mock as mock
        fd, path = tempfile.mkstemp(prefix="tomb-bad-", suffix=".json")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{")
            mouth = CA.river_mouth(path=path)
            self.assertFalse(mouth.get("ok"))
            self.assertIsNone(mouth.get("n"))
            self.assertIn("could not be read", str(mouth.get("why") or ""))
            with mock.patch.object(RR, "_tombstone_path", lambda *a, **k: path):
                view = CA.tombstone_view()
            why = str(view.get("why") or "")
            self.assertIn("UNKNOWN", why)
            self.assertNotIn("exists yet", why)
            self.assertIsNone(view.get("reels"))
        finally:
            os.unlink(path)


RED_PROOF = [
    {
        "why": "treating a missing ledger as present makes none yet read as could not be read",
        "file": "printer.py",
        "find": '    return ("no record yet" in w) or ("no tombstone ledger" in w)\n',
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "dropping the absence branch makes the walk call a missing ledger unreadable",
        "file": "river_walk.py",
        "find": "        if _absent:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "a missing mouth ledger was collapsed back into could not be read",
        "file": "control_app.py",
        "find": '                "why": "there is no tombstone ledger on this venue - retention has no record here, "\n',
        "replace": '                "why": "the tombstone ledger could not be read (missing), "\n',
        "matches": 1,
    },
    {
        "why": "a missing release history was collapsed back into could not be read",
        "file": "control_app.py",
        "find": '        out["why"] = "no tombstone ledger exists yet at %s — measured absent, not empty" % os.path.basename(_p)\n',
        "replace": '        out["why"] = "the tombstone ledger could not be read at %s" % os.path.basename(_p)\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
