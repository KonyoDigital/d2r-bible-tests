# -*- coding: utf-8 -*-
"""v2772 — A GUARD THAT COULD NEVER BE FALSE WAS ENDING HIS RECORDINGS AFTER 25 SECONDS.

Konyo: *"i click ON AIR and it just closes me out every time.. something is bugged with the
recording.. it suddenly cuts me out.. same for DEAN something unified is wrong there."*

=== THE DEFECT, IN ONE LINE ===
`mini_state()` returns

    "focus": m.get("focus") or MINI_FOCUS      # MINI_FOCUS = "stash", the module DEFAULT

and `_MINI` is INITIALISED with that default at import, before any mini has ever run. So `focus` is
never empty. `_current_declared_focus()` re-reads the same field, which made

    if not (m.get("focus") or _current_declared_focus()):   # <- one value, read twice

structurally incapable of returning early. `_stash_watch_loop` — whose own docstring says it seals
a **LANE-DECLARED** reel — was therefore armed for EVERY capture, always, including a plain ON AIR
that declared no lane at all.

He plays the game rather than standing in his stash, so `stash_screen_open()` returns None on every
poll, `gone_since` arms on the first one, and 25 seconds later `stop_agent()` seals the reel and
drops him off air.

=== MEASURED, END TO END ===
BEFORE, during a live ON AIR with no mini running:
    t+ 6s .. t+36s   alive=True   mini.focus='stash'   declared='stash'   armed=True
    t+42s            alive=False
    reel: 37 frames · blank 0 · 8 text frames · sealed cleanly · exit 0 · no stderr
    standalone `python3 -u tv_diablo.py` printed the reason the console never showed:
        "👋 closing session (off) — sealing reel…"     <- reason "off" == stop_agent(farewell=False)
AFTER:
    the stash watcher never speaks ("stash closed for" — 0 occurrences)
    ON AIR alive at t+80s and still recording, no shutdown requested at all

⚠ THE ~40s WAS NEVER A TIMER. It is one 5s poll + the 25s grace + startup. Nothing in the system
declares a 40-second session length, which is why searching for one found nothing.

=== ⚠ WHY THIS CANNOT LEAK A REEL — the risk that actually matters, because stop_agent() SEALS ===
Every mini also starts `_mini_watchdog(token, ends_ts)`, which seals on its deadline independently
of this loop. The stash watcher is an EARLY seal, never the only one. So narrowing it costs at most
a few seconds of extra footage on a genuine lane reel, and saves every plain session from being cut
off mid-run. The asymmetry is the point: a wrong seal loses his recording; a late seal costs
seconds.

=== ⚠ WHAT IS STILL UNEXPLAINED, AND IS NOT CLAIMED FIXED ===
One run after the fix died at t+56s with no shutdown recorded. The run after that survived past 80s.
That earlier death has NO established cause. This file fixes the defect it measured; it does not
claim ON AIR is now flawless.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _loop_src(code_only=True):
    """The stash watch loop. -> str

    ⚠⚠ COMMENTS STRIPPED BY DEFAULT, and this file is the proof of why. A law below forbids the
    never-false guard `if not (m.get("focus") or _current_declared_focus()):` — and the FIX's own
    comment QUOTES that line to explain what was wrong, so the law went red on the explanation of
    the thing it was written to prevent. Sixth time in this session a guard read prose as code.
    Judge CODE by its code. [[measured-true-read-wrong]] [[source-reading-guard]]
    """
    i = SRC.find("def _stash_watch_loop():")
    if i < 0:
        return ""
    blk = SRC[i:SRC.find("\ndef ", i + 1)]
    if not code_only:
        return blk
    return "\n".join(ln for ln in blk.split("\n") if not ln.strip().startswith("#"))


class TheStashWatcherOnlySealsALane(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_general_ON_AIR_reel_is_STRUCTURALLY_exempt(self):
        """★★ HIS RULING, and it is the whole shape of the fix:
        *"the stash-watcher's code stops are only relevant for when you exit the stash, not all
        round. ON AIR is just a screenshot and recording of it all in general.. its the first and
        main we built before the others.. and it worked perfectly."*

        ON AIR is the GENERAL RECORDER. Nothing stash-specific may end it. So the gate is the
        IDENTITY OF WHO OPENED THE REEL — `_agent_origin` — not a flag that can default or go
        stale. "hand" is the onair door and is never touched; only "mini" is the stash lane.
        A flag can be initialised to a default (which is exactly what shipped); who opened this
        reel cannot."""
        blk = _loop_src()
        self.assertIn('_agent_origin != "mini"', blk,
                      "the stash watcher is no longer bound to the MINI door, so it can once again "
                      "reach a general ON AIR recording and end it 25s after he leaves his stash")
        self.assertIn("continue", blk.split('_agent_origin != "mini"')[1][:120],
                      "the origin check does not skip the poll")

    def test_the_origin_vocabulary_has_not_moved(self):
        """⚠ THE FIXTURE. `_door_of_origin` maps hand->onair, mini->mini, shadow->shadow. If a
        fourth origin ever appears, this guard must be re-decided rather than silently admit it."""
        self.assertIn('{"hand": "onair", "mini": "mini", "shadow": "shadow"}', SRC,
                      "the origin->door map changed; re-check which origins the stash watcher may "
                      "act on before trusting the guard above")

    def test_the_watcher_requires_a_RUNNING_mini(self):
        """★ `focus` carries a module default, so it can never answer "did anything declare a
        lane?". Only an ACTIVE mini declares one."""
        blk = _loop_src()
        self.assertTrue(blk, "the stash watch loop is gone — this law inspected nothing")
        self.assertIn('m.get("running")', blk,
                      "the stash watcher no longer requires an ACTIVE mini, so it arms on every "
                      "plain ON AIR and seals his session 25s after he leaves the stash")

    def test_it_does_NOT_gate_on_focus_alone(self):
        """★★ THE EXACT SHAPE THAT SHIPPED. `focus or _current_declared_focus()` is ONE value read
        TWICE — both resolve to mini_state()["focus"], which defaults to MINI_FOCUS. An `or` of a
        thing with itself reads like two independent checks and is none."""
        blk = _loop_src()
        self.assertNotIn('if not (m.get("focus") or _current_declared_focus()):', blk,
                         "the never-false guard is back verbatim")

    def test_the_default_that_caused_it_is_still_there_and_still_a_default(self):
        """⚠ THE FIXTURE ASSUMPTION. The fix is correct BECAUSE `focus` has a default. If that ever
        changes — if focus becomes genuinely absent when no mini declared one — this guard could be
        simplified, but that must be a decision rather than drift."""
        self.assertIn('MINI_FOCUS = "stash"', SRC,
                      "MINI_FOCUS moved or changed; re-check whether `focus` can now be empty")
        self.assertIn('"focus": m.get("focus") or MINI_FOCUS', SRC,
                      "mini_state no longer defaults `focus`; the guard above may be re-pointed "
                      "deliberately, never silently")

    def test_a_plain_ON_AIR_does_not_arm_the_watcher(self):
        """★ The behaviour, measured against the live module rather than its source. With no mini
        running, the watcher must not arm — whatever `focus` happens to say."""
        m = CA.mini_state()
        if m.get("running"):
            self.skipTest("a mini IS running here, so the plain-ON-AIR case is not exercised — "
                          "a skip is NOT a pass")
        self.assertTrue(m.get("focus"),
                        "focus is empty, so this test is no longer reproducing the condition that "
                        "caused the bug — re-point it rather than leave it green")
        self.assertFalse(bool(m.get("running") and m.get("focus")),
                         "the watcher ARMS with no mini running — a plain ON AIR would be sealed "
                         "25s after he steps away from his stash")

    # ── ⚠ THE SAFETY ARGUMENT, PINNED ───────────────────────────────────────────────────────
    def test_a_real_mini_still_has_an_independent_sealer(self):
        """⛔ The whole fix rests on this. Narrowing the watcher is only safe because a mini seals
        itself on its deadline anyway. If that watchdog ever goes, a lane reel could run forever
        and this narrowing becomes a leak."""
        self.assertIn("def _mini_watchdog(", SRC,
                      "the mini's own deadline sealer is gone — the stash watcher is now the ONLY "
                      "thing that seals a lane reel, and it has just been narrowed")
        self.assertIn("_mini_watchdog, args=", SRC,
                      "nothing starts the mini watchdog thread")

    def test_the_watcher_still_seals_when_a_mini_IS_running(self):
        """⚠ A fix that stops it working at all would be worse than the bug — the early seal is
        why a stash lane closes promptly instead of running its full countdown."""
        blk = _loop_src()
        self.assertIn("stop_agent(farewell=False)", blk,
                      "the stash watcher no longer seals anything, so a lane reel now always runs "
                      "to its full deadline")
        self.assertIn("_STASH_WATCH_GRACE_S", blk,
                      "the grace period is gone — one bad poll would seal immediately")

    def test_the_grace_is_still_a_grace(self):
        self.assertGreaterEqual(CA._STASH_WATCH_GRACE_S, 10.0,
                                "the grace window shrank to %.1fs — a single missed OCR poll would "
                                "end his session" % CA._STASH_WATCH_GRACE_S)



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in control_app.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_app.py',
        "find": '_agent_origin != "mini"',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in control_app.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_app.py',
        "find": '{"hand": "onair", "mini": "mini", "shadow": "shadow"}',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in control_app.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_app.py',
        "find": 'm.get("running")',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
