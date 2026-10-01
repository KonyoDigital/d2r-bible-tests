# -*- coding: utf-8 -*-
"""REG-1627 — A LANE THAT OWES WORK AND DOES NONE SAYS WHY, IN ITS OWN WORDS.

MEASURED on his Mac 2026-09-30 23:1x (the fleet's river chip "PRINTER 2 - vault lane: owes 3, 3809 read(s) on
record"): the vault lane's status said on, owed 3, stale, last read 36 min earlier - and owedWhy null, skipped {},
retired []. Every vault_autoreel_tick() already returns a named reason (busy, deferred, requeued, retired, "N owed,
none startable") and the loop dropped it. heart-first: "on" is not "working", and the doctor must name the link.

Driven here: _vault_autoread_note records each tick in its own words; _vault_autoread_state says the last tick's
reason whenever reels are owed and it started none, and says nothing when a read started or nothing is owed; the
rescue loop calls the note (read from its AST, the loop being endless). RED_PROOF below.
"""
import ast
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

_WORLD = tempfile.mkdtemp(prefix="owing_lane_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import control_app as ca  # noqa: E402

RED_PROOF = [
    {"why": "REG-1654 - the uptime is read off the wall clock again: an NTP step decides whether the lane is late",
     "file": "control_app.py",
     "find": "    up = max(0, int((time.monotonic() - _BOOT_MONO) if up_s is None else up_s))\n",
     "replace": "    up = max(0, int((time.time() - _BOOT_AT) if up_s is None else up_s))\n", "matches": 1},
    {"why": "REG-1654 - a first tick that is already due is described as still on its way again",
     "file": "control_app.py",
     "find": "    if up < _VAULT_AUTOREAD_EVERY_S:\n",
     "replace": "    if up < 2 * _VAULT_AUTOREAD_EVERY_S:\n", "matches": 1},
    {"why": "REG-1627 - the vault loop drops its tick's reason again: an owing lane is silent",
     "file": "control_app.py",
     "find": "            _vault_autoread_note(_r)        # REG-1627",
     "replace": "            pass                            # REG-1627", "matches": 1},
    {"why": "REG-1627 - the status ignores the last tick: owes 3 and no reason",
     "file": "control_app.py",
     "find": "                                  if (owed and _lt and not _lt.get(\"started\"))\n",
     "replace": "                                  if False\n", "matches": 1},
    {"why": "REG-1646 - an owing lane with no recorded tick says nothing again (null reads as nothing to explain)",
     "file": "control_app.py",
     "find": "                                  else _vault_no_tick_why() if (owed and not _lt) else None)),   # REG-1646\n",
     "replace": "                                  else None)),   # REG-1646\n", "matches": 1},
    {"why": "REG-1646 - a lane silent for ten minutes still reads as 'the first tick is coming'",
     "file": "control_app.py",
     "find": "    if up < 2 * _VAULT_AUTOREAD_EVERY_S:\n",
     "replace": "    if True:\n", "matches": 1},
    {"why": "REG-1646 - a tick that raises leaves no trace again",
     "file": "control_app.py",
     "find": "                _vault_autoread_note({\"ok\": False, \"raised\": True, \"why\": \"the tick raised %s\" % type(_vte).__name__})\n",
     "replace": "                pass\n", "matches": 1},
]

OWED = [{"reel": "reel_s_1_1"}, {"reel": "reel_s_2_2"}, {"reel": "reel_s_3_3"}]


class AnOwingLaneSaysWhyItWaits(unittest.TestCase):
    def setUp(self):
        self._saved = dict(ca._VAULT_AUTOREAD)
        self.addCleanup(lambda: (ca._VAULT_AUTOREAD.clear(), ca._VAULT_AUTOREAD.update(self._saved)))

    def _state(self, owed):
        with mock.patch.object(ca, "_vault_owed_reels", lambda: owed):
            return ca._vault_autoread_state()

    def test_a_busy_tick_is_said_while_reels_are_owed(self):
        n = ca._vault_autoread_note({"ok": False, "busy": True, "why": "a vault sweep is already running"}, now_ms=5)
        self.assertEqual((n["kind"], n["at"]), ("busy", 5))
        st = self._state(OWED)
        self.assertEqual(st["owed"], 3)
        self.assertIn("a vault sweep is already running", st["owedWhy"] or "",
                      "an owing lane that started nothing said nothing: %r" % st.get("owedWhy"))
        self.assertIn("busy", st["owedWhy"])

    def test_none_startable_names_itself(self):
        ca._vault_autoread_note({"ok": True, "read": None, "owed": 3, "why": "3 owed, none startable this tick"})
        self.assertIn("none startable", self._state(OWED)["owedWhy"] or "")

    def test_a_tick_that_started_a_read_owes_no_excuse(self):
        ca._vault_autoread_note({"ok": True, "started": "reel_s_1_1", "owed": 3})
        self.assertIsNone(self._state(OWED)["owedWhy"])

    def test_nothing_owed_says_nothing_and_unknown_stays_unknown(self):
        ca._vault_autoread_note({"ok": False, "busy": True, "why": "a vault sweep is already running"})
        self.assertIsNone(self._state([])["owedWhy"], "a lane that owes nothing was given an excuse")
        self.assertIn("UNKNOWN", self._state(None)["owedWhy"])

    def test_no_recorded_tick_right_after_a_start_says_so(self):
        """REG-1646 - owed, and no tick recorded yet: the first one is up to an interval away, and that is SAID"""
        ca._VAULT_AUTOREAD.pop("lastTick", None)
        with mock.patch.object(ca, "_BOOT_MONO", __import__("time").monotonic() - 10):   # REG-1654
            why = self._state(OWED)["owedWhy"]
        self.assertIsNotNone(why, "an owing lane with no recorded tick said nothing - it reads as nothing to explain")
        self.assertIn("no tick yet", why)

    def test_no_recorded_tick_long_after_a_start_is_a_lane_that_is_not_ticking(self):
        """REG-1646 - past two intervals with nothing recorded, the loop is not ticking: REG-1640's frozen lane"""
        ca._VAULT_AUTOREAD.pop("lastTick", None)
        with mock.patch.object(ca, "_BOOT_MONO", __import__("time").monotonic() - 600):   # REG-1654
            why = self._state(OWED)["owedWhy"]
        self.assertIn("not ticking", why or "")
        self.assertIn("UNKNOWN", why or "")

    def test_a_first_tick_that_is_due_is_not_called_on_time(self):
        """REG-1654 (the v3538 eye) - between one interval and two the first tick is DUE: "the first runs within 45 s"
        said then read a lane that had missed its wake as one still on time"""
        ca._VAULT_AUTOREAD.pop("lastTick", None)
        up = int(ca._VAULT_AUTOREAD_EVERY_S * 1.5)
        with mock.patch.object(ca, "_BOOT_MONO", __import__("time").monotonic() - up):
            why = self._state(OWED)["owedWhy"] or ""
        self.assertIn("was due", why, why)
        self.assertNotIn("within", why, "a due tick was described as still on its way: %r" % why)

    def test_a_wall_clock_step_does_not_move_the_verdict(self):
        """REG-1654 - the loop sleeps on a clock no NTP step moves; so does the question of whether it is late"""
        ca._VAULT_AUTOREAD.pop("lastTick", None)
        import time as _t
        with mock.patch.object(ca, "_BOOT_MONO", _t.monotonic() - 10), \
                mock.patch.object(ca, "_BOOT_AT", _t.time() - 86400):        # the wall clock stepped a day
            why = self._state(OWED)["owedWhy"] or ""
        self.assertIn("no tick yet", why, "a wall-clock step read a lane 10 s old as not ticking: %r" % why)

    def test_a_tick_that_returns_is_recorded_in_its_own_words(self):
        """One real pass of the loop with a tick that RETURNS: its words are recorded. The pass is stopped at the
        next lane's own start (the names feeder), so nothing past the note runs. REG-1646's raise branch also calls
        the note, so "the loop calls it somewhere" can no longer prove this - only the recorded kind can."""
        class _Stop(BaseException):
            pass

        def lane_tick(name, *a, **k):
            if name == "tvd-read-names-feeder":
                raise _Stop()
        ca._VAULT_AUTOREAD.pop("lastTick", None)
        with mock.patch.object(ca.time, "sleep", lambda _s: None), mock.patch.object(ca, "_lane_tick", lane_tick), \
                mock.patch.object(ca, "vault_autoreel_tick",
                                  lambda: {"ok": False, "busy": True, "why": "a vault sweep is already running"}):
            with self.assertRaises(_Stop):
                ca._vault_autoread_loop()
        lt = ca._VAULT_AUTOREAD.get("lastTick") or {}
        self.assertEqual(lt.get("kind"), "busy", "the loop did not record what its tick said: %r" % (lt,))

    def test_a_tick_that_raises_is_recorded_as_raised(self):
        """REG-1646 - the loop's outer swallow used to leave no trace of a raising tick. One real pass of the loop."""
        class _Stop(BaseException):
            pass
        calls = []

        def sleep(_s):
            calls.append(1)
            if len(calls) > 1:
                raise _Stop()

        def boom():
            raise KeyError("x")
        ca._VAULT_AUTOREAD.pop("lastTick", None)
        with mock.patch.object(ca.time, "sleep", sleep), mock.patch.object(ca, "_lane_tick", lambda *a, **k: None), \
                mock.patch.object(ca, "vault_autoreel_tick", boom):
            with self.assertRaises(_Stop):
                ca._vault_autoread_loop()
        lt = ca._VAULT_AUTOREAD.get("lastTick") or {}
        self.assertEqual(lt.get("kind"), "raised", "a tick that raised left no trace: %r" % (lt,))
        self.assertIn("KeyError", lt.get("why") or "")
        self.assertIn("raised", self._state(OWED)["owedWhy"] or "")

    def test_the_loop_records_every_tick(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        loop = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_autoread_loop")
        called = {c.func.id for c in ast.walk(loop) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("_vault_autoread_note", called, "the vault loop no longer records what its tick did")


if __name__ == "__main__":
    unittest.main(verbosity=2)
