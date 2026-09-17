# -*- coding: utf-8 -*-
"""v3285 — THE AUTO LANES ARE ALWAYS ON AND CARRY NO SWITCH.

Konyo, 2026-09-18, looking at the Sessions strip: *"these should be toggled on by default no
option to it"*.

v1975 built these four lanes as real switches, and its doctrine — OFF IS A REAL REFUSAL, not a
hidden button — was CORRECT while OFF was reachable: a pill that says a lane is dark while frames
keep flowing into it is the exact class of lie this board guards against. He has now removed OFF,
which inverts the law rather than relaxing it. Two things must hold, and they are different:

  1. NO ROUTE REACHES OFF — including the route the UI can no longer offer. `d2r_autoLanes` may
     still hold {"runes": false} from a single click months ago, and every reel since would have
     skipped that section silently. Not reading the store is what makes that state UNREACHABLE
     rather than merely un-offered.

  2. THE PILL CARRIES NO CONTROL AFFORDANCE. A track-and-knob that cannot move, or a role=switch
     with no handler, invites a click that does nothing — [[the-unjoined-end]] on a surface.

⚠ THIS LAW STRIPS COMMENTS BEFORE READING (frame_authority._executable_only, which keeps ordinary
string literals). That is load-bearing here and not a nicety: the very code under test carries a
comment reading "No role=switch, no tabindex, no onclick, no knob", so a law that grepped raw
source would read its own commentary and go green — or red — for a reason having nothing to do
with the shipped behaviour. That is REG-1070 exactly. [[presence-law-vs-reachability-law]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

BIBLE = os.path.join(ROOT, "bible.html")


def _between(src, start, end, what):
    """The slice from `start` to the NEXT `end`, with BOTH ends anchored on real bytes.

    A fixed-size window (src[i:i+N]) reads whatever follows the region when the guess is too
    long, and reports an absent string when it is too short. [[source-reading-guard]]
    """
    i = src.find(start)
    if i < 0:
        raise AssertionError("anchor START vanished for %s: %r" % (what, start[:60]))
    j = src.find(end, i + len(start))
    if j < 0:
        raise AssertionError("anchor END vanished for %s: %r" % (what, end[:60]))
    return src[i:j]


class TestTheAutoLanesHaveNoSwitch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = io.open(BIBLE, encoding="utf-8").read()
        # ⚠ ".js", NOT the real path, AND THAT IS NOT A SHORTCUT — it is the codebase's idiom
        # (test_a_name_takes_its_colour_from_its_rarity.py:74 does the same). _executable_only
        # dispatches on the EXTENSION: only .ts/.tsx/.js take the comment-stripping branch, and
        # a path ending .html falls through to the PYTHON branch, where ast.parse() throws and
        # the function returns the source UNSTRIPPED — silently, looking like it worked. The
        # first cut of this law passed BIBLE and went red on its own comment.
        #
        # ⚠⚠ AND THE OBVIOUS FIX — teaching the dispatch about .html — IS THE WRONG ONE.
        # frame_authority:738 uses this same helper to decide which reels are REFERENCED, and
        # v2393 exists precisely because a reel named only in prose must not hold disk. Adding
        # .html there would make every reel id mentioned in a bible.html comment newly eligible
        # for deletion — his real footage, irreversibly. The gap is load-bearing; route around
        # it here rather than widening it there. [[a-gate-can-perturb-what-it-measures]]
        cls.code = _executable_only(raw, ".js")

    def test_the_reader_does_not_consult_the_store(self):
        body = _between(self.code,
                        "window._miniOnAirOn = function(lane){",
                        "window._miniOnAirToggle = function(lane){",
                        "_miniOnAirOn")
        self.assertIn("return true;", body,
                      "the lane reader must answer ON unconditionally — his 2026-09-18 ruling")
        self.assertNotIn("_miniLanes(", body,
                         "reading d2r_autoLanes puts OFF back within reach: a stale {\"runes\":"
                         "false} from an old click would darken that lane on every reel, and "
                         "nothing on the strip would say so")

    def test_the_toggle_writes_nothing(self):
        body = _between(self.code,
                        "window._miniOnAirToggle = function(lane){",
                        "window._miniOnAirPaint = function(){",
                        "_miniOnAirToggle")
        self.assertNotIn("setItem", body,
                         "the toggle is kept BY NAME for its two guarded callers and must be "
                         "inert; a write here re-creates the OFF state from the inside")

    def test_the_pill_carries_no_control_affordance(self):
        body = _between(self.code,
                        "window._miniOnAirHtml = function(lane, what){",
                        "var _MINI_SLOTS = [",
                        "_miniOnAirHtml")
        for token, why in (
            ("onclick", "a handler on a state chip invites a click that changes nothing"),
            ('role="switch"', "role=switch promises a control that is no longer offered"),
            ("tabindex", "a focusable non-control strands keyboard users on a dead stop"),
            ("mini-knob", "a knob that cannot move is a lie about what the surface offers"),
            ("mini-track", "the track exists only to carry the knob"),
        ):
            self.assertNotIn(token, body, "%s must be gone from the pill markup — %s" % (token, why))
        self.assertIn("mini-fixed", body, "the pill must declare itself a fixed state")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "putting the store read back makes a stale {\"runes\":false} darken the lane again",
        "file": "bible.html",
        "find": "  return true;                       // v3285 - never read from the store, by his ruling",
        "replace": "  return _miniLanes()[lane] !== false;",
        "matches": 1,
    },
    {
        "why": "an onclick on the chip re-offers a control he ruled away",
        "file": "bible.html",
        "find": "    + '<span class=\"mini-dot\"></span>'",
        "replace": "    + ' onclick=\"1\"' + '<span class=\"mini-dot\"></span>'",
        "matches": 1,
    },
    {
        "why": "a write inside the inert toggle re-creates OFF from the inside",
        "file": "bible.html",
        "find": "     than a loud one. A no-op that reports the truth. */\n  return true;\n};",
        "replace": "     than a loud one. */\n  window.LSR.setItem(_MINI_LANES_KEY, '{}');\n  return true;\n};",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
