# -*- coding: utf-8 -*-
"""THE GROK CHIP MUST PAINT WHEN CLAUDE IS UNMEASURED, AND A CEILING OF 0 MUST NOT LOOK UNMEASURED.

⚠⚠ THE SECOND EYE'S TWO HIGHS ON THE SHIPPED v3099 DIFF, BOTH VERIFIED IN THE FILE BEFORE A LINE
WAS CHANGED. v3099 fixed the PRODUCER — `_meter_lanes` now runs on every return of `_meter_state`,
so `/api/meter` carries `lanes.grok` even on a machine where Claude has never written its ledger.
The consumer was still shut:

    bible.html:52817   if (!known){
    bible.html:52822     return j;          <- bails here
    bible.html:52848   var gl = (j.lanes && j.lanes.grok)   <- the grok paint, never reached

So on exactly the machine v3099 exists for — Grok as primary, Grok as shadow, a fresh checkout,
CI — the payload arrived and the chip was never drawn. **The same unjoined end, one layer down.**
[[the-unjoined-end]] [[plumbing-with-no-tap]]

And the second: `"hourlyMax": _ghm or None` turned a ceiling of **0** into `None`, while the
renderer's `paint()` treats any falsey max as nothing-to-divide-by and writes the same `–` it
writes for an unmeasured lane:

    if (used === null || used === undefined || !max){ ... v.textContent = '-'; return; }

A ceiling of 0 is the circuit that refuses EVERY read — `_budget_ok` returns False outright — and
it is a MEASURED configuration, not an absent value. Off, unknown and switched-off-at-the-budget
are three different facts and two of them were sharing pixels. [[zero-needs-a-denominator]]

⚠ AND A THIRD, WHICH IS MINE AND WHICH NOBODY REPORTED: the early call works ONLY because
`paintGrok` is a hoisted `function` DECLARATION. It is called inside the `!known` branch and
defined below it. Rewrite it as `const paintGrok = () => {}` — the modern habit, and a change any
reviewer would wave through — and the early call throws a TDZ ReferenceError, killing the chip on
the very path this exists to fix, silently, inside a `try`. Pinned here so the shape cannot drift.
"""
import io
import os
import re
import sys
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import control_app as CA          # noqa: E402


def _block(src, opener):
    """The source of the {...} block that `opener` opens, by BRACE MATCHING.

    ⚠ A BRACE WALK, NOT A FIXED WINDOW. `src[i:i+N]` past the end of the region reads as ABSENT,
    which is how a guard comes to describe a guess instead of a file. [[source-window-shortcut]]
    """
    i = src.index(opener)
    j = src.index("{", i)
    depth, k = 0, j
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j:k + 1], j, k
        k += 1
    raise AssertionError("unbalanced braces after %r" % opener)


class TestTheGrokChipPaintsOnEveryPath(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(REPO, "bible.html"), encoding="utf-8") as fh:
            self.src = fh.read()

    # ── 1. the chip is painted on the CLAUDE-UNMEASURED path ──────────────────────────────────
    def test_the_grok_chip_is_painted_when_claude_is_unmeasured(self):
        body, _a, end = _block(self.src, "if (!known){")
        n_in = body.count("paintGrok()")
        after = self.src[end:]
        n_after = after.count("paintGrok()")
        print("   paintGrok() inside the !known block: %d · after it: %d" % (n_in, n_after))
        self.assertGreaterEqual(
            n_in, 1,
            "the `if (!known)` branch returns without painting the grok chip, so on a machine "
            "where CLAUDE has never read — the exact case v3099 exists for — /api/meter carries "
            "lanes.grok and the panel draws nothing")
        self.assertGreaterEqual(
            n_after, 1,
            "the grok chip is painted ONLY on the unmeasured path — the normal path lost it")

    # ── 2. and it only works because the declaration HOISTS ───────────────────────────────────
    def test_paintgrok_is_a_hoisted_declaration(self):
        decls = re.findall(r"function\s+paintGrok\s*\(", self.src)
        lex = re.findall(r"(?:const|let|var)\s+paintGrok\s*=", self.src)
        print("   `function paintGrok(` declarations: %d · lexical `paintGrok =`: %d"
              % (len(decls), len(lex)))
        self.assertEqual(
            len(decls), 1,
            "paintGrok must be exactly one hoisted FUNCTION DECLARATION — it is CALLED above the "
            "line it is DEFINED on, and only a declaration is legal there")
        self.assertEqual(
            len(lex), 0,
            "paintGrok is bound with const/let/var: the call inside the `if (!known)` branch runs "
            "BEFORE the binding is initialised and throws a TDZ ReferenceError — inside a try, so "
            "the chip just silently never appears on the one path this was written for")

    # ── 3. the circuit is drawn as a circuit, not as an absence ───────────────────────────────
    def test_a_zero_ceiling_is_not_drawn_like_an_unmeasured_one(self):
        body, _a, _b = _block(self.src, "function paintGrok()")
        self.assertIn("capWindow === 'circuit'", body,
                      "the renderer does not distinguish a ceiling of 0 from an unmeasured lane, "
                      "so `paint()` writes the same '-' for both")
        # and it must actually WRITE something different, not merely test for it
        self.assertTrue(re.search(r"textContent\s*=\s*\(gl\.(hour|day)", body),
                        "the circuit branch tests for the state and paints nothing different")
        print("   circuit branch present in paintGrok, and it writes its own text")

    # ── 4. the server publishes the REAL ceiling, so 0 can reach the screen at all ────────────
    def test_a_zero_ceiling_is_published_as_zero(self):
        import g5_grok_eyes as G5
        h0, d0 = G5._HOURLY_MAX, G5._DAILY_MAX
        try:
            G5._HOURLY_MAX, G5._DAILY_MAX = 0, 200
            lane = (CA._meter_lanes({"hour": 1, "day": 1, "hourlyMax": 4000,
                                     "dailyMax": 20000, "armed": True}) or {}).get("grok") or {}
            print("   with G5._HOURLY_MAX=0 -> hourlyMax=%r atCap=%r capWindow=%r"
                  % (lane.get("hourlyMax"), lane.get("atCap"), lane.get("capWindow")))
            self.assertEqual(lane.get("hourlyMax"), 0,
                             "a ceiling of 0 is published as %r — `or None` erased the difference "
                             "between a configured zero and an unmeasured value, and the bar "
                             "cannot draw what the payload does not carry"
                             % (lane.get("hourlyMax"),))
            self.assertTrue(lane.get("atCap"))
            self.assertEqual(lane.get("capWindow"), "circuit")
        finally:
            G5._HOURLY_MAX, G5._DAILY_MAX = h0, d0


RED_PROOF = [
    {
        "why": "the grok chip stops being painted when Claude is unmeasured — the producer fix in "
               "v3099 reaches /api/meter and the panel still draws nothing, on exactly the "
               "machines where grok is the lane doing the reading",
        "file": "../bible.html",
        "find": "      paintGrok();          /* ⚠ v3100 — CLAUDE unmeasured says NOTHING about the GROK lane */\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "paintGrok becomes a lexical binding, so the call inside the `if (!known)` branch "
               "hits the temporal dead zone and throws — inside a try, so the chip silently never "
               "appears on the path this exists to fix",
        "file": "../bible.html",
        "find": "    function paintGrok(){",
        "replace": "    const paintGrok = function(){",
        "matches": 1,
    },
    {
        "why": "a ceiling of 0 goes back to being published as None, so the circuit that refuses "
               "every read is drawn with the same '-' as a lane nobody has measured",
        "file": "control_app.py",
        "find": '            "hour": _gh, "day": _gd, "hourlyMax": _ghm, "dailyMax": _gdm,',
        "replace": '            "hour": _gh, "day": _gd, "hourlyMax": _ghm or None, "dailyMax": _gdm or None,',
        "matches": 1,
    },
    {
        "why": "the renderer stops naming the circuit, so a 0 ceiling is drawn exactly like an "
               "unmeasured lane again",
        "file": "../bible.html",
        "find": "        var circuit = (gl.capWindow === 'circuit');",
        "replace": "        var circuit = false;",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
