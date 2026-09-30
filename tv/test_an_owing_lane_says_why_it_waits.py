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
    {"why": "REG-1627 - the vault loop drops its tick's reason again: an owing lane is silent",
     "file": "control_app.py",
     "find": "            _vault_autoread_note(_r)        # REG-1627",
     "replace": "            pass                            # REG-1627", "matches": 1},
    {"why": "REG-1627 - the status ignores the last tick: owes 3 and no reason",
     "file": "control_app.py",
     "find": "                                  if (owed and _lt and not _lt.get(\"started\")) else None)),\n",
     "replace": "                                  if False else None)),\n", "matches": 1},
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

    def test_the_loop_records_every_tick(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        loop = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_autoread_loop")
        called = {c.func.id for c in ast.walk(loop) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("_vault_autoread_note", called, "the vault loop no longer records what its tick did")


if __name__ == "__main__":
    unittest.main(verbosity=2)
