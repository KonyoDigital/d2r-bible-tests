# -*- coding: utf-8 -*-
"""#151 (REG-2742, his ask 2026-10-21) - EVERY FREE-SPACE READ THAT DECIDES SOMETHING COUNTS WHAT macOS FREES ON DEMAND.

"the guards and the sign count purgeable space". macOS answers "how much can an important write use" with the space free
now plus what it frees on demand - the figure Finder shows. MEASURED on his Mac 2026-10-28: 13.19 GB for important usage
against 11.98 GB plain, so the ON AIR floor and the proving lanes refused earlier than macOS would. disk_room.free_bytes is
the one reading now, and every floor reads it: the ON AIR floor, the picture size, the health figure, the console's disk
sign and its doctor, the retention drain, the warden, the river's disk joint and heart2's lane room - so no two of them can
disagree about the same disk (v2006, "one side decides").

A law that replaced shutil.disk_usage is asking about a pretend disk, and the purgeable add-on never touches it - judged
from the function itself, because a copy taken at import was the stub whenever this module was imported late (measured:
the warden read 10.59 GiB under a law's 7 GiB disk). Also here: the disk sign's pass prunes his Grok chats when needed
(REG-2743), and never while he plays. RED_PROOF below.
"""
import collections
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import shutil  # noqa: E402
import disk_room as D  # noqa: E402

GB = 1000 ** 3
DECIDERS = ("tv_diablo.py", "control_app.py", "heart2.py", "river.py", "space_warden.py", "console_doctor.py")


def _usage(free):
    return collections.namedtuple("usage", "total used free")(500 * GB, 400 * GB, int(free))


class FreeBytes(unittest.TestCase):

    def test_BASELINE_the_mac_answers_more_than_the_plain_free(self):
        """Measured on the machine this runs on; elsewhere it is UNMEASURED, never a pass."""
        if sys.platform != "darwin":
            self.skipTest("not macOS - the important-usage figure exists only there (UNMEASURED here)")
        b, kind = D.free_bytes(tempfile.gettempdir())
        self.assertEqual(kind, "important", "macOS did not answer the important-usage figure")
        self.assertGreaterEqual(b, shutil.disk_usage(tempfile.gettempdir()).free)

    def test_the_larger_of_what_macos_says_and_what_is_free_now(self):
        real = shutil.disk_usage(tempfile.gettempdir()).free
        with mock.patch.object(D, "important_bytes", return_value=real + 5 * GB):
            self.assertEqual(D.free_bytes(tempfile.gettempdir()), (real + 5 * GB, "important"))
        with mock.patch.object(D, "important_bytes", return_value=1):
            b, kind = D.free_bytes(tempfile.gettempdir())
            self.assertGreaterEqual(b, real - 64 * 1024 ** 2, "a smaller important figure lowered the plain free")
            self.assertEqual(kind, "important")

    def test_no_answer_is_the_plain_free(self):
        with mock.patch.object(D, "important_bytes", return_value=None):
            self.assertEqual(D.free_bytes(tempfile.gettempdir())[1], "plain")

    def test_a_pretend_disk_is_never_topped_up_with_the_real_ones_purgeable_space(self):
        with mock.patch.object(D, "important_bytes", return_value=99 * GB):
            with mock.patch.object(shutil, "disk_usage", return_value=_usage(7 * GB)):
                self.assertEqual(D.free_bytes("/anything"), (7 * GB, "plain"))
            real = shutil.disk_usage
            shutil.disk_usage = lambda p: _usage(5 * GB)
            try:
                self.assertEqual(D.free_bytes("/anything"), (5 * GB, "plain"))
            finally:
                shutil.disk_usage = real

    def test_off_macos_nothing_is_asked(self):
        with mock.patch.object(sys, "platform", "win32"):
            self.assertIsNone(D.important_bytes(tempfile.gettempdir()))


class EveryFloorReadsTheOneFigure(unittest.TestCase):

    def test_no_deciding_file_reads_the_plain_disk_any_more(self):
        bad = []
        for f in DECIDERS:
            src = io.open(os.path.join(HERE, f), encoding="utf-8").read()
            code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
            n = code.count(".disk_usage(")
            if n:
                bad.append((f, n))
        self.assertEqual(bad, [], "a floor still reads the plain free space, so two floors can disagree: %r" % bad)

    def test_the_two_local_helpers_are_the_disk_rooms(self):
        for f in ("tv_diablo.py", "control_app.py"):
            src = io.open(os.path.join(HERE, f), encoding="utf-8").read()
            self.assertEqual(src.count("def _disk_free_bytes(path):"), 1, f)
            self.assertEqual(src.count("    return _dr.free_bytes(path)[0]\n"), 1, f)


class TheSignsPassPrunesHisGrokChats(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def test_the_prune_runs_after_a_measurement_and_never_while_he_plays(self):
        ca = self.ca
        calls = []
        with mock.patch.object(ca, "_grok_prune_pass", side_effect=lambda *a, **k: calls.append(1)):
            ca._disk_sign_once(now_ms=1, playing=True, busy_pct=0, candidates=[])
            self.assertEqual(calls, [], "his Grok chats were pruned while he plays")
            ca._disk_sign_once(now_ms=2, playing=False, busy_pct=0, candidates=[])
            self.assertEqual(calls, [1], "the sign's pass never reached the prune")

    def test_a_pass_that_removed_something_is_counted_and_said(self):
        ca = self.ca
        before = dict(ca._GROK_PRUNE)
        try:
            fake = lambda **k: {"need": "over-budget", "removed": [{"id": "x", "bytes": 3 * GB}], "freed": 3 * GB,
                                "failed": 0, "total": 5 * GB, "after": 1 * GB, "say": "needed (over-budget): pruned 1"}
            rec = ca._grok_prune_pass(now_ms=5, _run=fake)
            self.assertEqual((rec["worked"], rec["owed"], rec["lastTs"]), (int(before.get("worked") or 0) + 1, 0, 5))
            self.assertEqual(rec["freedBytes"], int(before.get("freedBytes") or 0) + 3 * GB)
            pay = ca.disk_sign_payload(_free=lambda: 50 * GB)
            self.assertEqual(pay["grokPrune"]["say"], "needed (over-budget): pruned 1")
            idle = lambda **k: {"need": None, "removed": [], "freed": 0, "failed": 0, "total": 3 * GB, "after": 3 * GB,
                                "say": "not needed"}
            rec2 = ca._grok_prune_pass(now_ms=6, _run=idle)
            self.assertEqual(rec2["worked"], rec["worked"], "a pass that removed nothing was counted as work")
            self.assertEqual(rec2["owed"], 1, "a folder still over its budget is not owed")
        finally:
            ca._GROK_PRUNE.clear()
            ca._GROK_PRUNE.update(before)


RED_PROOF = [
    {"why": "REG-2742 - a law's pretend disk is topped up with the real disk's purgeable space",
     "file": "disk_room.py",
     "find": "    if not _disk_usage_is_real():\n        return plain, \"plain\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2742 - a smaller important figure lowers the plain free",
     "file": "disk_room.py",
     "find": "    return max(plain, imp), \"important\"\n",
     "replace": "    return imp, \"important\"\n",
     "matches": 1},
    {"why": "REG-2742 - the picture-size floor reads the plain disk again",
     "file": "tv_diablo.py",
     "find": "        free = _disk_free_bytes(hist_dir) / 1e9\n",
     "replace": "        free = _shp.disk_usage(hist_dir).free / 1e9\n",
     "matches": 1},
    {"why": "REG-2743 - the sign's pass never prunes",
     "file": "control_app.py",
     "find": "    _grok_prune_pass(now)\n    return dict(_DISK_SIGN)\n",
     "replace": "    return dict(_DISK_SIGN)\n",
     "matches": 1},
    {"why": "REG-2743 - a pass that removed nothing is counted as work",
     "file": "control_app.py",
     "find": "    if rec.get(\"removed\"):\n        upd[\"worked\"] = int(_GROK_PRUNE.get(\"worked\") or 0) + 1\n",
     "replace": "    if True:\n        upd[\"worked\"] = int(_GROK_PRUNE.get(\"worked\") or 0) + 1\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
