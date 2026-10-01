# -*- coding: utf-8 -*-
"""#145 — THE HEART'S REFRESH NEVER WEDGES, AND WHAT IT SHOWS IS ONE CENSUS.

Three findings from the Grok eyes on #231 (v3544 code seat, v3545 range read), each reproduced on the shipped code first:
  1. A census that never returns held `running` for ever: every later open and every ↻ joined it, waited 4 s and got the
     old memo back - nothing ever started a replacement; only a console restart cleared the slot.
  2. The memo was written in three assignments and read in two loads, so a request could take one census's body with
     another's clock - a just-replaced census shown as ~0 ms old, the signal a reader takes for "fresh".
  3. The panel looked for its status line in the HEADER and put it in the BODY, so every pending answer added another.

Driven through the real control_app.heart_state_now / _heart_refresh_async with heart_state stubbed (never his census),
and the shipped panel source:
  · a census older than _HEART_REFRESH_STUCK_S is abandoned (said in lastError) and a new one is taken; the old one's
    late finish clears nothing (generation); after _HEART_REFRESH_MAX_ABANDONED the console stops and says why;
  · a census younger than the ceiling is still joined, never doubled (REG-1685 stands);
  · the memo's readers read it in ONE look and its writer writes it in ONE write (counted in the bytecode);
  · the status line is found where it is put.
RED_PROOF below.
"""
import dis
import io
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as ca  # noqa: E402

CENSUS = {"ok": True, "counts": {"vessels": 1}, "vessels": [], "locks": []}


class _Server(unittest.TestCase):

    def setUp(self):
        self._memo, self._ref, self._hs = dict(ca._HEART_MEMO), dict(ca._HEART_REFRESH), ca.heart_state
        self._stuck, self._max = ca._HEART_REFRESH_STUCK_S, ca._HEART_REFRESH_MAX_ABANDONED
        ca._HEART_MEMO.update(t=0.0, done=0.0, v=None)
        ca._HEART_REFRESH.update(running=False, startedAt=None, lastTookMs=None, lastError=None, runs=0, gen=0,
                                 abandoned=0)
        self.gates, self.calls = [], 0

        def census(force=False):
            self.calls += 1
            g = threading.Event()
            self.gates.append(g)
            g.wait(10)                       # blocks until the test lets it finish (a stuck walk otherwise)
            ca._heart_memo_store(time.time(), dict(CENSUS))
            return dict(CENSUS)
        ca.heart_state = census
        self.addCleanup(self._restore)

    def _restore(self):
        for g in self.gates:
            g.set()
        time.sleep(0.05)
        ca.heart_state = self._hs
        ca._HEART_REFRESH_STUCK_S, ca._HEART_REFRESH_MAX_ABANDONED = self._stuck, self._max
        ca._HEART_MEMO.clear()
        ca._HEART_MEMO.update(self._memo)
        ca._HEART_REFRESH.clear()
        ca._HEART_REFRESH.update(self._ref)


class ACensusThatNeverReturnsIsReplaced(_Server):

    def test_past_the_ceiling_a_new_census_is_taken_and_said(self):
        ca.heart_state_now(wait_s=0)
        self.assertEqual(self.calls, 1)
        ca._HEART_REFRESH["startedAt"] = time.time() - ca._HEART_REFRESH_STUCK_S - 5     # it has hung that long
        r = ca.heart_state_now(wait_s=0.05)
        self.assertEqual(self.calls, 2, "a census that never came back still held the slot - no replacement started")
        self.assertIn("never came back", r["refresh"]["lastError"] or "", "the abandoned census was not said: %r" % r)
        self.assertEqual(ca._HEART_REFRESH["abandoned"], 1)

    def test_the_abandoned_census_finishing_late_clears_nothing(self):
        ca.heart_state_now(wait_s=0)
        ca._HEART_REFRESH["startedAt"] = time.time() - ca._HEART_REFRESH_STUCK_S - 5
        ca.heart_state_now(wait_s=0)
        self.gates[0].set()                  # the FIRST (abandoned) census finally returns
        time.sleep(0.2)
        self.assertTrue(ca._HEART_REFRESH["running"], "the abandoned census's late finish cleared the new one's flag")

    def test_under_the_ceiling_a_second_ask_joins_never_doubles(self):
        ca.heart_state_now(wait_s=0)
        ca.heart_state_now(wait_s=0.05)
        self.assertEqual(self.calls, 1, "a second census started beside one that is still young (REG-1685)")

    def test_after_the_cap_it_stops_and_says_the_census_hangs(self):
        ca._HEART_REFRESH_MAX_ABANDONED = 1
        ca.heart_state_now(wait_s=0)
        ca._HEART_REFRESH["startedAt"] = time.time() - ca._HEART_REFRESH_STUCK_S - 5
        ca.heart_state_now(wait_s=0)                          # abandons #1, starts #2
        ca._HEART_REFRESH["startedAt"] = time.time() - ca._HEART_REFRESH_STUCK_S - 5
        r = ca.heart_state_now(wait_s=0)
        self.assertEqual(self.calls, 2, "past the cap it went on starting censuses that hang")
        self.assertIn("hung", r["refresh"]["lastError"] or "", r)


def _global_loads(fn, name):
    return sum(1 for ins in dis.get_instructions(fn) if ins.opname == "LOAD_GLOBAL" and ins.argval == name)


class TheMemoIsOneCensus(unittest.TestCase):

    def test_each_reader_takes_one_look(self):
        for fn in (ca._heart_memo_hit, ca._heart_memo_last):
            self.assertEqual(_global_loads(fn, "_HEART_MEMO"), 1,
                             "%s reads the memo in more than one look - body and clock can come from two censuses"
                             % fn.__name__)

    def test_the_writer_writes_once(self):
        stores = [i for i in dis.get_instructions(ca._heart_memo_store) if i.opname == "STORE_SUBSCR"]
        self.assertEqual(stores, [], "the memo is written in several steps again")
        self.assertIn("update", ca._heart_memo_store.__code__.co_names)

    def test_the_shown_age_is_still_from_when_the_reading_began(self):
        now = time.time()
        ca_memo = dict(ca._HEART_MEMO)
        try:
            ca._heart_memo_store(now - 30, dict(CENSUS))
            shown = ca._heart_memo_last(now)
            self.assertGreaterEqual(shown["ageMs"], 29000, "the age is the landing's, hiding the reading (REG-1229)")
        finally:
            ca._HEART_MEMO.clear()
            ca._HEART_MEMO.update(ca_memo)


class TheStatusLineIsFoundWhereItIsPut(unittest.TestCase):

    def test_it_is_looked_for_in_the_panel_not_the_header(self):
        src = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
        i = src.index("  function _hrtStatus(ov, d){")
        body = src[i:src.index("\n  function ", i + 10)]
        self.assertEqual(body.count("var el = ov.querySelector('#hrt-age');"), 1,
                         "the status line is looked for where it is not put - each pending answer adds one")
        self.assertIn("body.insertBefore(el, body.firstChild)", body, "PREMISE: the line is no longer put in the body")


RED_PROOF = [
    {"why": "#145 - a census that never returns holds the slot for ever (no ceiling)",
     "file": "control_app.py",
     "find": "            if age < _HEART_REFRESH_STUCK_S or gave_up:\n",
     "replace": "            if True:\n",
     "matches": 1},
    {"why": "#145 - an abandoned census's late finish clears the new census's flag",
     "file": "control_app.py",
     "find": "                if _HEART_REFRESH.get(\"gen\") == gen:      # #145 - an abandoned census's late finish clears nothing\n",
     "replace": "                if True:\n",
     "matches": 1},
    {"why": "#145 - past the cap it goes on starting censuses that hang",
     "file": "control_app.py",
     "find": "            gave_up = int(_HEART_REFRESH.get(\"abandoned\") or 0) >= _HEART_REFRESH_MAX_ABANDONED\n",
     "replace": "            gave_up = False\n",
     "matches": 1},
    {"why": "#145 - the fast read takes the body and the clock in two looks again",
     "file": "control_app.py",
     "find": "    shown[\"ageMs\"] = int((now - float(m[\"t\"])) * 1000)     # its honest age, from when its reading began\n",
     "replace": "    shown[\"ageMs\"] = int((now - float(_HEART_MEMO[\"t\"])) * 1000)     # its honest age, from when its reading began\n",
     "matches": 1},
    {"why": "#145 - the status line is looked for in the header again",
     "file": "control_ui.html",
     "find": "    var el = ov.querySelector('#hrt-age');",
     "replace": "    var el = head.querySelector('#hrt-age');",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
