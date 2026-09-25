# -*- coding: utf-8 -*-
"""REG-1303 — ON WINDOWS THE CONSOLE'S WINDOW WITNESS WAS BLIND, SO A COVERED CONSOLE WAS RELOADED.

window_visibility (on_screen / covered_by) asked only Quartz, so on the ALT (Windows) every answer
was UNKNOWN - and the silence rescue treats UNKNOWN as "go ahead" by design (REG-596). MEASURED
2026-09-25 over SSH on the ALT: 13 `console-rescued-by-server` since 09-20, 7 in one night, each
"silent for 60-84s" with the last beat hidden False / painting True / frozenBeats 0 and
`pixelBlank: Quartz is not importable here`. REG-594's signature (a healthy console covered between
two beats) on the one platform its fix never reached. No sleep was involved (no Kernel-Power
42/107/506/507 that night). MEASURED by the shipped Win32 walk, run in his session on the ALT the same
day: the 1280x720 console listed on screen and "Boosteroid (100.0%) is on top of it" - the cloud-gaming
window he plays through.

The Windows witness lists top-level windows front to back and feeds the SAME rows to the SAME
arithmetic (layer rule, union, 95% bar). These cases drive it through a fake window list shaped
exactly like the real one, and drive the SHIPPED silence branch of ui_rescue_due through it.

  · DRIVEN: Citrix covering it -> covered, named; the always-on-top taskbar -> not an occluder;
    half covered -> not covered; two windows tiling it -> covered (the union); minimized ->
    covered and not on screen; a list that cannot be read -> UNKNOWN, never "covered".
  · DRIVEN (control_app.ui_rescue_due, the silence branch, witness chosen as on the ALT - no
    Quartz): a silent console under Citrix is NOT reloaded; a silent visible one still IS.
RED_PROOF below.
"""
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import window_visibility as WV  # noqa: E402

ME = 4242


def _row(pid, name, x, y, w, h, top=False, iconic=False, ex=0, cloaked=0):
    """Built by the SHIPPED per-window rule, exactly as the Win32 walk builds each row."""
    return WV._win_row(pid, name, (x, y, x + w, y + h), ex | (WV.WS_EX_TOPMOST if top else 0),
                       iconic, cloaked)


class _Fake(object):
    def __init__(self, rows=None, boom=False):
        self._rows, self._boom = rows or [], boom

    def rows(self):
        if self._boom:
            raise OSError("EnumWindows refused")
        return list(self._rows)


CONSOLE = _row(ME, "TV DIABLO", 100, 100, 1280, 720)
TASKBAR = _row(9, "", 0, 0, 1920, 1080, top=True)          # always-on-top, spans everything


class TheWindowsWitness(unittest.TestCase):

    def test_citrix_over_the_console_is_a_covering(self):
        w = _Fake([TASKBAR, _row(77, "Citrix Workspace", 0, 0, 1920, 1080), CONSOLE])
        cov, why = WV.covered_by(pid=ME, win=w)
        self.assertTrue(cov, "a console under Citrix read as visible: %r" % (why,))
        self.assertIn("Citrix", why)

    def test_the_always_on_top_taskbar_is_not_an_occluder(self):
        cov, why = WV.covered_by(pid=ME, win=_Fake([TASKBAR, CONSOLE]))
        self.assertEqual(cov, [], "system chrome was counted as covering his console: %r" % (why,))
        self.assertIs(WV.on_screen(pid=ME, win=_Fake([TASKBAR, CONSOLE]))[0], True)

    def test_half_covered_is_still_visible(self):
        cov, _ = WV.covered_by(pid=ME, win=_Fake([_row(77, "Notepad", 100, 100, 640, 720), CONSOLE]))
        self.assertEqual(cov, [])

    def test_two_windows_that_tile_it_cover_it(self):
        w = _Fake([_row(77, "Citrix Workspace", 0, 0, 740, 1080), _row(78, "Chrome", 740, 0, 1180, 1080),
                   CONSOLE])
        cov, _ = WV.covered_by(pid=ME, win=w)
        self.assertEqual(len(cov or []), 2, "the union of two tiling windows was not counted: %r" % (cov,))

    def test_a_minimized_console_is_hidden_completely(self):
        w = _Fake([TASKBAR, _row(ME, "TV DIABLO", -32000, -32000, 160, 28, iconic=True)])
        cov, why = WV.covered_by(pid=ME, win=w)
        self.assertEqual(cov, ["minimized (100.0%)"], why)
        self.assertIs(WV.on_screen(pid=ME, win=w)[0], False)

    def test_cloaked_and_click_through_windows_cover_nothing(self):
        self.assertIsNone(_row(77, "Citrix Workspace", 0, 0, 1920, 1080, cloaked=1),
                          "a window on another virtual desktop was listed as covering him")
        self.assertIsNone(_row(78, "GeForce Overlay", 0, 0, 1920, 1080, ex=WV.WS_EX_TRANSPARENT),
                          "a click-through overlay was listed as covering him")

    def test_windows_selects_the_win32_witness(self):
        """The platform switch itself: on win32 the witness is _Win32, elsewhere none (Quartz)."""
        keep = sys.platform
        try:
            sys.platform = "win32"
            self.assertIsInstance(WV._win(), WV._Win32, "Windows still gets no window witness")
            sys.platform = "darwin"
            self.assertIsNone(WV._win())
        finally:
            sys.platform = keep

    def test_an_unreadable_list_is_unknown_never_covered(self):
        cov, why = WV.covered_by(pid=ME, win=_Fake(boom=True))
        self.assertIsNone(cov, "an unreadable window list was read as an answer: %r" % (why,))
        self.assertIsNone(WV.on_screen(pid=ME, win=_Fake(boom=True))[0])


class TheSilenceRescueUsesIt(unittest.TestCase):
    """The shipped branch, with the witness selected exactly as on the ALT: Quartz absent."""

    def setUp(self):
        import control_app as ca
        self.ca = ca
        keep_b, keep_r = dict(ca._UI_BEAT), dict(ca._UI_RESCUE)
        keep_q, keep_w, keep_pid = WV._quartz, WV._win, os.getpid

        def _restore():
            ca._UI_BEAT.clear(); ca._UI_BEAT.update(keep_b)
            ca._UI_RESCUE.clear(); ca._UI_RESCUE.update(keep_r)
            WV._quartz, WV._win = keep_q, keep_w
        self.addCleanup(_restore)
        WV._quartz = lambda: None
        age = 70.0                                      # the ALT's measured 60-84 s silences
        ca._UI_BEAT.update({"n": 9, "mono": time.monotonic() - age, "t": time.time() - age,
                            "hidden": False, "els": 917, "elsNow": 917,
                            "blankStrikes": 0, "frozenBeats": 0})
        ca._UI_RESCUE["last"] = 0.0
        ca._UI_RESCUE["futile"] = 0

    def _world(self, rows):
        me = os.getpid()
        fixed = [dict(r, kCGWindowOwnerPID=(me if r["kCGWindowOwnerPID"] == ME else r["kCGWindowOwnerPID"]))
                 for r in rows]
        WV._win = lambda: _Fake(fixed)

    def test_a_silent_console_under_citrix_is_not_reloaded(self):
        self._world([TASKBAR, _row(77, "Citrix Workspace", 0, 0, 1920, 1080), CONSOLE])
        due, why = self.ca.ui_rescue_due(now=time.time())
        self.assertFalse(due, "the ALT's covered console was reloaded under him again: %s" % why)
        self.assertIn("Citrix", why)

    def test_a_silent_visible_console_is_still_rescued(self):
        """THE BASELINE: a genuinely wedged page on a window he can see must still be reloaded."""
        self._world([TASKBAR, CONSOLE])
        due, why = self.ca.ui_rescue_due(now=time.time())
        self.assertTrue(due, "a visible silent console stopped being rescued: %s" % why)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1303 - the witness is Quartz-only again: on the ALT a covered console reads UNKNOWN and is reloaded",
        "file": "window_visibility.py",
        "find": "    return _Win32() if _sys.platform == \"win32\" else None\n",
        "replace": "    return None\n",
        "matches": 1,
    },
    {
        "why": "REG-1303 - the always-on-top taskbar counts as an occluder: every Windows console reads covered and the rescue never fires",
        "file": "window_visibility.py",
        "find": "            \"kCGWindowLayer\": 1 if (int(exstyle) & WS_EX_TOPMOST) else 0,\n",
        "replace": "            \"kCGWindowLayer\": 0,\n",
        "matches": 1,
    },
    {
        "why": "REG-1303 - a minimized console is 'not listed' again, UNKNOWN instead of hidden, and gets reloaded",
        "file": "window_visibility.py",
        "find": "            return [\"minimized (100.0%)\"], \"his console is minimized, so he cannot see it\"\n",
        "replace": "            return None, \"no window of his was listed to compare against\"\n",
        "matches": 1,
    },
    {
        "why": "REG-1303 - a cloaked or click-through window is listed as covering him, so a console he CAN see is left to rot",
        "file": "window_visibility.py",
        "find": "    if cloaked or (int(exstyle) & WS_EX_TRANSPARENT):\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1,
    },
]
