# -*- coding: utf-8 -*-
"""A STAGE WHOSE EVERY REEL IS HELD MUST NOT RENDER AS A PLAIN COUNT.

⚠⚠ HIS OWN WORDS, LOOKING AT HIS CONSOLE: *"this 8 releasable has been stale for like a week im
pretty sure"*. He was right, and the number was not stale DATA — it was a figure that CANNOT MOVE.
MEASURED on his live console, GET /api/reel_story, 2026-09-14:

    onDisk 12 · banked 4 · releasable 8 · unknown-stage 0
    all 8 at releasable: held=true · holdKind=policy
        why "one of the 8 most recent — kept so a re-sweep always has real footage"
    all 4 at banked:     held=true · holdKind=evidence

`reel_story.TAG_STAGE` maps the `recent` tag onto the `releasable` stage and `POLICY_HOLDS` holds
it there — so that 8 IS the newest-8 floor, counted, pinned at 8 forever. Twelve reels, twelve
holds, and the rail drew plain gold counts under a heading saying each stage counts what gets "no
further" than it. The number was right and the word above it had stopped being true.
[[label-outlived-referent]] [[stale-reading]] [[unknown-stays-unknown]]

⚠ THIS LAW RUNS THE REAL EXPRESSION, IT DOES NOT GREP FOR ONE. A guard that looks for the string
`held` passes the moment someone writes the word in a comment, and passes just as happily when the
branch that emits it can never be reached. The rail builder is extracted between two anchors and
evaluated under node against reel shapes taken from his own console. [[source-reading-guard]]

⚠ AND THE MIRROR ERROR IS GUARDED TOO. Painting a stage as held when ONE of its reels is free is
the same lie pointing the other way: that stage can move, and a "held" badge would send him
looking for a blocker that is not there.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = os.path.join(HERE, "control_ui.html")


def _between(src, start, end):
    """Text between two anchors, BOTH required. A fixed-size window reads a moved region as
    ABSENT, which is how this repo has lost measurements before. [[source-window-shortcut]]"""
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)]


def _rail_source():
    src = io.open(UI, encoding="utf-8").read()
    stages = _between(src, "var _SH_STAGES = [", "];")
    builder = _between(src, "    var _shHeld = {};", "    }).join('');")
    tail = _between(src, "    var _shHeldAll = reels.length > 0",
                    "return !!(r && r.held); });")
    # ⚠⚠ v3119 — THE HEADING IS THE SENTENCE HE READS, AND v3117 NEVER EVALUATED IT. The second
    # eye on v3117: this extract stopped at the `_shHeldAll` ASSIGNMENT, so every assertion read
    # the BOOLEAN and none read the string built from it. Revert the ternary to always say "each
    # stage counts the reels that get no further than it", leave `_shHeldAll` computed, and the
    # whole gate stays green while his console shows the original lie over twelve held reels.
    # Both halves looked wired and the pixels were not in the loop. [[the-unjoined-end]]
    headline = _between(src, "'<div class=\"shs-railh\">where the ' + reels.length",
                        "+   '</div>'")
    return (stages + "\n" + builder + "\n" + tail
            + "\n    var railh = " + headline + ";")


def _run(reels, stages):
    """Evaluate the REAL rail builder AND the heading against these reels. -> {rail, heldAll, railh}"""
    js = """
    var esc = function(x){ return String(x); };
    var reels = %s;
    var stg = %s;
    %s
    console.log(JSON.stringify({rail: rail, heldAll: _shHeldAll, railh: railh}));
    """ % (json.dumps(reels), json.dumps(stages), _rail_source())
    r = subprocess.run([shutil.which("node"), "-e", js],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not evaluate the rail builder — UNKNOWN, not passing: %s"
                             % (r.stderr or "")[:600])
    return json.loads(r.stdout.strip())


#: His live console, 2026-09-14 — every reel held, eight of them by the newest-8 floor.
HIS_LIVE = [
    {"reel": "reel_s_1789330829280_6", "stage": "releasable", "held": True,
     "holdKind": "policy", "why": "one of the 8 most recent — kept so a re-sweep always has real footage"},
] + [
    {"reel": "reel_s_178888%d_5" % i, "stage": "releasable", "held": True,
     "holdKind": "policy", "why": "one of the 8 most recent — kept so a re-sweep always has real footage"}
    for i in range(7)
] + [
    {"reel": "reel_s_178819%d_3" % i, "stage": "banked", "held": True,
     "holdKind": "evidence", "why": "panels were read but never banked"}
    for i in range(4)
]
HIS_STAGES = {"filmed": 0, "triaged": 0, "swept": 0, "banked": 4,
              "vault-done": 0, "releasable": 8, "unknown-stage": 0}


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — this law is UNMEASURED, not passing")
class TestAHeldStageDoesNotReadAsAQueue(unittest.TestCase):

    def test_his_eight_releasable_render_as_HELD_not_as_a_queue(self):
        out = _run(HIS_LIVE, HIS_STAGES)
        rail = out["rail"]
        print("   his 12 reels -> heldAll=%s · 'held' marks=%d"
              % (out["heldAll"], rail.count(">held<")))
        self.assertTrue(out["heldAll"],
                        "every one of his 12 reels is held and the heading still offers to "
                        "explain which get 'no further' — a constant presented as a queue")
        self.assertIn("shs-hk-policy", rail,
                      "the 8 held by the newest-8 floor do not carry the policy tone, so a "
                      "deliberate hold paints the same as a stuck one")
        self.assertIn("shs-hk-evidence", rail,
                      "the 4 held for missing evidence do not carry the evidence tone")
        self.assertEqual(rail.count(">held<"), 2,
                         "expected both populated stages marked held, got %d"
                         % rail.count(">held<"))

    def test_the_reason_reaches_the_title_not_just_the_colour(self):
        out = _run(HIS_LIVE, HIS_STAGES)
        self.assertIn("kept so a re-sweep always has real footage", out["rail"],
                      "the hold REASON never reaches the screen — a colour he has to decode is "
                      "not an explanation, and this sentence already exists in the payload")
        self.assertNotIn("8 reel(s) get no further than releasable", out["rail"],
                         "the queue wording survived on a stage that cannot move")

    def test_ONE_free_reel_means_the_stage_is_not_held(self):
        """⚠ THE MIRROR ERROR. A stage with one free reel CAN move; a held badge there sends him
        looking for a blocker that does not exist."""
        reels = [dict(r) for r in HIS_LIVE]
        reels[0] = dict(reels[0])
        reels[0]["held"] = False
        reels[0]["holdKind"] = None
        out = _run(reels, HIS_STAGES)
        rail = out["rail"]
        print("   one free reel -> heldAll=%s · 'held' marks=%d"
              % (out["heldAll"], rail.count(">held<")))
        self.assertFalse(out["heldAll"], "one reel is free and the heading says none is")
        self.assertEqual(rail.count(">held<"), 1,
                         "releasable has a free reel and still reads as held (%d mark(s))"
                         % rail.count(">held<"))
        self.assertIn("7 of them held", rail,
                      "a partially held stage says nothing about its 7 holds")

    def test_the_HEADING_he_reads_says_nothing_can_move(self):
        """⚠⚠ THE SECOND EYE ON v3117, AND IT IS THIS FILE'S OWN FAILURE MODE. v3117 asserted the
        BOOLEAN `_shHeldAll` and never the sentence built from it. Revert the ternary to always
        emit the queue wording, leave the boolean computed and the per-stage badges alone, and
        every assertion here still passed — while his console showed the original lie over twelve
        held reels. The variable was wired; the pixels were not. [[the-unjoined-end]]"""
        out = _run(HIS_LIVE, HIS_STAGES)
        h = out["railh"]
        print("   heading: %s" % h[:104])
        self.assertIn("none of them is free to move", h,
                      "the heading still offers to explain which reels get 'no further' while "
                      "not one of the twelve can move at all")
        self.assertNotIn("no further", h,
                         "the queue wording survived in the heading: %r" % (h[:140],))

    def test_the_heading_keeps_the_queue_wording_while_a_reel_is_free(self):
        """The mirror: with one reel free the heading must go back to describing a queue, because
        that is what it then is."""
        reels = [dict(r) for r in HIS_LIVE]
        reels[0] = dict(reels[0]); reels[0]["held"] = False; reels[0]["holdKind"] = None
        h = _run(reels, HIS_STAGES)["railh"]
        print("   heading with one free reel: %s" % h[:104])
        self.assertIn("no further", h,
                      "a shelf with a free reel is a queue and the heading no longer says so")
        self.assertNotIn("none of them is free to move", h,
                         "one reel is free and the heading claims none is")

    def test_a_stage_with_no_reels_is_not_held(self):
        """⚠ A ZERO NEEDS A DENOMINATOR. `0 >= 0` is true, and an empty stage marked held would
        be the emptiest possible claim. [[zero-needs-a-denominator]]"""
        out = _run([], {"filmed": 0, "releasable": 0})
        self.assertEqual(out["rail"].count(">held<"), 0,
                         "an empty rail reported a hold it cannot have measured")
        self.assertFalse(out["heldAll"], "no reels at all reported as 'all held'")


RED_PROOF = [
    {
        "why": "the heading goes back to always offering to explain which reels get 'no further' "
               "while not one of the twelve can move — the exact sentence his console showed over "
               "a figure pinned at 8 for a week, and v3117's laws all stayed green through it "
               "because they read the boolean and never the string",
        "file": "control_ui.html",
        "find": "                 +   (_shHeldAll",
        "replace": "                 +   (false",
        "matches": 1,
    },
    {
        "why": "a stage every one of whose reels is held goes back to drawing a plain gold count, "
               "so his 8 RELEASABLE — the newest-8 floor, pinned at 8 forever — reads as a queue "
               "he is waiting on instead of a hold that is working as designed",
        "file": "control_ui.html",
        "find": "      var allHeld = n > 0 && h.n >= n;",
        "replace": "      var allHeld = false;",
        "matches": 1,
    },
    {
        "why": "the hold REASON stops reaching the title, leaving a colour he has to decode — the "
               "sentence is already in the payload and the screen drops it",
        "file": "control_ui.html",
        "find": "              : allHeld ? (n + ' reel(s) reached ' + s[2] + ' and are HELD — '",
        "replace": "              : allHeld ? (n + ' reel(s) reached ' + s[2] + ' (' + (",
        "matches": 1,
    },
    {
        "why": "a majority of holds is treated as all of them, so a stage with a free reel that "
               "CAN move is painted stuck and he goes looking for a blocker that is not there",
        "file": "control_ui.html",
        "find": "      var allHeld = n > 0 && h.n >= n;",
        "replace": "      var allHeld = n > 0 && h.n >= 1;",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
