# -*- coding: utf-8 -*-
"""#193 (REG-3052, measured on his Mac 2026-10-29) - AN EVIDENCE REMNANT IS THE DRAIN'S FINISHED WORK, NOT A STUCK REEL.

The Mac's Fleet row said "river stuck" with 25 reels "older than the newest 16 - the drain owes them a tombstone". Measured
read only on his Mac: the drain's own plan() owed nothing (every pass in disk_history: eligible 0, owed 0) - 12 of the 25
were EVIDENCE REMNANTS, reels the drain already released whose cited pictures stay by his §26 ruling (REG-2728's 12), and
the other 13 are held by the plan's own rules. plan() drops remnants before it plans (reel_retention.remnant_reels); the
stuck reader (control_app._river_stuck_for_wire) did not ask that predicate, so it called the drain's finished work its debt,
and its newest-16 window counted remnants where the drain's does not. It now asks the drain's own predicate, before the
window is built. Measured with the fix on his river, read only: 24 stuck reels became 12 - exactly the plan's held set.

Driven: _river_stuck_for_wire on fixture shelves through its own seams, and its production path with the drain's
remnant_reels answering (or failing) - never his river. RED_PROOF below.
"""
import os
import shutil
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
import fixture_tmp as _fx  # noqa: E402
_fx.contain()
import control_app as CA  # noqa: E402
import reel_retention as RR  # noqa: E402

T = 1793000000000
DAY = 86400000
NOW = T + 2 * DAY


def _reel(ms, n):
    return "reel_s_%d_%d" % (ms, n)


NEW = [_reel(T + i * 60000, i) for i in range(1, 17)]       # the newest sixteen
R = _reel(T - 10 * DAY, 900)                                 # an evidence remnant, long released
X = _reel(T - 9 * DAY, 901)                                  # a reel the drain still owes


def _rows(reels, station):
    return [{"reel": r, "station": station, "at": RR._reel_ts(r)} for r in reels]


class ARemnantIsNotAStuckReel(unittest.TestCase):

    def _stuck(self, shelf, rows, remnants):
        return CA._river_stuck_for_wire(NOW, _rows=rows, _shelf=shelf, _fixtures=(), _remnants=remnants)

    def test_a_remnant_past_the_window_is_not_owed_and_an_equal_reel_is(self):
        # the remnant's last stamp is at a LANE's station: out of the window list it would read as "inside" and owed a move
        out = self._stuck(NEW + [R, X], _rows([R], "PRINTER") + _rows([X], "ROUTED") + _rows(NEW, "CAPTURE"), {R})
        self.assertEqual([(e["station"], e["n"]) for e in out], [("ROUTED", 1)],
                         "a released reel's kept pictures were counted as the drain's debt: %r" % out)

    def test_the_window_is_the_drains_window_without_remnants(self):
        newest_remnant = _reel(T + 17 * 60000, 999)
        # CAPTURE waits by design inside the window, so only a reel pushed OUT of it can be owed here
        out = self._stuck(NEW + [newest_remnant], _rows(NEW, "CAPTURE"), {newest_remnant})
        self.assertEqual(out, [], "a remnant took a place in the newest 16 and pushed a kept reel out: %r" % out)

    def test_the_console_asks_the_drains_own_predicate(self):
        d = tempfile.mkdtemp(prefix="remnant_shelf_")
        try:
            for r in NEW + [R, X]:
                os.makedirs(os.path.join(d, r))
            asked = []
            with mock.patch.object(CA, "HIST_DIR", d), \
                    mock.patch.object(CA, "_shelf_reel_names", lambda: list(NEW + [R, X])), \
                    mock.patch.object(RR, "remnant_reels", lambda hist: asked.append(hist) or {R}):
                out = CA._river_stuck_for_wire(NOW, _rows=_rows([R, X], "ROUTED"), _fixtures=())
            self.assertEqual(asked, [d], "the reader did not ask the drain's remnant_reels for this shelf")
            self.assertEqual([(e["station"], e["n"]) for e in out], [("ROUTED", 1)], out)
        finally:
            shutil.rmtree(d, True)

    def test_a_remnant_list_that_cannot_be_read_is_unknown(self):
        d = tempfile.mkdtemp(prefix="remnant_shelf_")
        try:
            for r in NEW + [X]:
                os.makedirs(os.path.join(d, r))

            def boom(hist):
                raise OSError("tombstone unreadable")
            with mock.patch.object(CA, "HIST_DIR", d), \
                    mock.patch.object(CA, "_shelf_reel_names", lambda: list(NEW + [X])), \
                    mock.patch.object(RR, "remnant_reels", boom):
                out = CA._river_stuck_for_wire(NOW, _rows=_rows([X], "ROUTED"), _fixtures=())
            self.assertIsNone(out, "an unreadable remnant list was read as 'nothing finished': %r" % out)
        finally:
            shutil.rmtree(d, True)


RED_PROOF = [
    {"why": "REG-3052 - a remnant past the window is counted as the drain's debt again",
     "file": "tv/control_app.py",
     "find": "        if reel in _pinned or reel in _done or not _on(reel):\n",
     "replace": "        if reel in _pinned or not _on(reel):\n",
     "matches": 1},
    {"why": "REG-3052 - the window counts remnants the drain's window does not",
     "file": "tv/control_app.py",
     "find": "        _names = [n for n in _names if str(n) not in _done]\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3052 - the console stops asking the drain's own remnant predicate",
     "file": "tv/control_app.py",
     "find": "                _remnants = _rr_rem.remnant_reels(HIST_DIR)\n",
     "replace": "                _remnants = ()\n",
     "matches": 1},
    {"why": "REG-3052 - an unreadable remnant list is read as 'nothing finished'",
     "file": "tv/control_app.py",
     "find": "                return None          # cannot tell finished from owed: UNKNOWN, never flowing\n",
     "replace": "                _remnants = ()\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
