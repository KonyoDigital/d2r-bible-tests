# -*- coding: utf-8 -*-
"""#152 slice 1 — A JOIN THE ENGINE RULED NOT_A_HOLDING IS NOT LEFT AT THE JOIN.

extract_gap already says that reel owes nothing: the names were read, and none of them
can become a holding. The route lane only moved EMPTY. That reel sat at JOIN for good,
one step short of ROUTED, while a reel with nothing in it was closed out.

  · DRIVEN: a JOIN reel carrying the engine's own NOT_A_HOLDING token is routed, and
    the stamp cites that token. It is not filed as declined.
  · DRIVEN: RECOVERABLE stays. A missing verdict stays. A word this station does not
    know stays. None of those is a route and none of them is a silent decline.
  · DRIVEN: CAPTURE is still declined, and it is not routed. EMPTY is still routed.
  · DRIVEN: a token that could not be read routes none of the JOIN reels.
Nothing here stamps a reel, deletes one, or reads his shelf. RED_PROOF below.
[[unknown-stays-unknown]] [[copy-drift]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import extract_gap as EG  # noqa: E402
import reel_route_lane as LANE  # noqa: E402
import reel_router as RR  # noqa: E402
import river_stamp as ST  # noqa: E402


_NOTHING = "reel_s_1500000000106_16"
_RECOVER = "reel_s_1500000000107_17"
_UNSAID = "reel_s_1500000000108_18"
_OTHER = "reel_s_1500000000109_19"
_EMPTY = "reel_s_1500000000101_11"
_CAPTURE = "reel_s_1500000000103_13"


def _shelf():
    return {
        _EMPTY: {"sealed": False, "names": 0, "surveyed": True, "worthReading": False},
        _CAPTURE: {"sealed": True, "names": 0, "surveyed": True, "worthReading": True},
        _NOTHING: {"sealed": True, "names": 45, "surveyed": True, "worthReading": True,
                   "extractSay": EG.NOT_A_HOLDING},
        _RECOVER: {"sealed": True, "names": 2, "surveyed": True, "worthReading": True,
                   "extractSay": "RECOVERABLE"},
        _UNSAID: {"sealed": True, "names": 1, "surveyed": True, "worthReading": True},
        _OTHER: {"sealed": True, "names": 3, "surveyed": True, "worthReading": True,
                 "extractSay": "NO_NAMES"},
    }


class AJoinThatOwesNothingIsRouted(unittest.TestCase):

    def setUp(self):
        self._ev = RR._evidence
        self._rows = ST.rows
        shelf = _shelf()
        RR._evidence = lambda hist=None: ({k: dict(v) for k, v in shelf.items()}, "the law's shelf")
        ST.rows = lambda path=None: {"ok": True, "rows": [], "why": ""}
        self.addCleanup(self._restore)

    def _restore(self):
        RR._evidence = self._ev
        ST.rows = self._rows

    def _plan(self):
        got = LANE.plan()
        self.assertTrue(got.get("ok"), got.get("why"))
        return got

    def _ids(self, rows):
        return [r.get("reel") for r in rows]

    def test_a_join_ruled_nothing_is_routed_and_cites_the_engine(self):
        got = self._plan()
        hit = [r for r in got["route"] if r.get("reel") == _NOTHING]
        self.assertEqual(len(hit), 1, got)
        self.assertEqual(hit[0].get("from"), "JOIN")
        self.assertIn(EG.NOT_A_HOLDING, hit[0].get("why") or "")
        self.assertNotIn(_NOTHING, self._ids(got["declined"]))
        self.assertNotIn("character panel", hit[0].get("why") or "")

    def test_a_join_that_still_owes_a_join_is_not_this_lane(self):
        got = self._plan()
        seen = self._ids(got["route"]) + self._ids(got["declined"])
        for reel in (_RECOVER, _UNSAID, _OTHER):
            self.assertNotIn(reel, seen, "%s was taken by the route lane: %r" % (reel, got))

    def test_capture_stays_declined_and_empty_stays_routed(self):
        got = self._plan()
        self.assertIn(_EMPTY, self._ids(got["route"]))
        self.assertNotIn(_EMPTY, self._ids(got["declined"]))
        cap = [r for r in got["declined"] if r.get("reel") == _CAPTURE]
        self.assertEqual(len(cap), 1, got)
        self.assertTrue(cap[0].get("owesFirst"))
        self.assertFalse([r for r in got["route"] if r.get("from") == "CAPTURE"])

    def test_an_unreadable_token_routes_no_join(self):
        real = LANE._nothing_owed_say
        LANE._nothing_owed_say = lambda: None
        try:
            got = self._plan()
        finally:
            LANE._nothing_owed_say = real
        self.assertNotIn(_NOTHING, self._ids(got["route"]),
                         "the engine's token could not be read, and the join was routed anyway")
        self.assertIn(_EMPTY, self._ids(got["route"]),
                      "a missing token also stopped the empty reels, which do not ask it")


RED_PROOF = [
    {"why": "REG-1782 - the join the engine ruled nothing is left at JOIN again",
     "file": "reel_route_lane.py",
     "find": "        _ruled = _hold if (st == \"JOIN\" and _hold is not None\n"
             "                           and r.get(\"extractSay\") == _hold) else None\n",
     "replace": "        _ruled = None\n",
     "matches": 1},
    {"why": "REG-1782 - a token that could not be read is filled in, and the join is routed on a guess",
     "file": "reel_route_lane.py",
     "find": "    _hold = _nothing_owed_say()\n",
     "replace": "    _hold = _nothing_owed_say() or \"NOT_A_HOLDING\"\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
