# -*- coding: utf-8 -*-
"""v2772 — WHEN THE RESCUE FAILED, KONYO WAS THE FALLBACK. NOW THERE IS ONE RUNG ABOVE IT.

Measured over 196 hours of his own fault journal:

    console-pixels-blank-nothing-else-saw-it        73   the detector works
    console-rescued-by-server                      111   the cure fires
    console-rescue-did-not-restore-painting          4   THE CURE FAILED
    anything stronger after those 4                  0   <- and then nothing happened

=== ⚠⚠ THE EXISTING REFUSAL TO ESCALATE IS CORRECT AND HAS NOT BEEN UNDONE ===
`_console_rescue_loop` carries a deliberate decision, in its own words:

    "This does not retry and does not escalate — a reload that cannot fix a stopped compositor will
     not fix it the second time either, and hammering his window is worse than saying so."

That is right, and retrying the RELOAD is still refused. What changed is that a **relaunch is not a
reload**: it replaces the process rather than re-fetching the page, and MEASURED 2026-09-08 it
restored his blank window TWICE, in ~3 seconds each, after reloads had failed. So the top rung is a
DIFFERENT ACT, not a second helping of the one that already failed.

=== ⛔ WHY THE REFUSALS ARE THE FEATURE, AND WHY THEY ARE TESTED HARDER THAN THE ACT ===
An auto-relaunch loop is far worse than a blank window: it would kill his recordings on repeat and
he would have no way to tell a crash from the cure. So the dangerous states are each driven here —
recording, single failure, cooldown — and the ACT is one line by comparison.

⚠ `recording` is checked FIRST and beats every futile count, however high. A relaunch mid-capture
costs him a reel; a blank window costs him a refresh.

=== ⚠ WHY THIS FILE DRIVES A FUNCTION INSTEAD OF READING THE LOOP ===
The decision was pulled OUT of `_console_rescue_loop` into `_rescue_escalation_decision` precisely so
these laws could call it. A law that greps the loop for `_agent_alive()` is satisfied by the comment
explaining the rule — that exact mistake was made SIX times in one session in this repo, and one of
them left a function defined-and-uncalled behind a green law. The single structural check below
(does the loop CALL it?) is done by PARSING, never by substring. [[source-reading-guard]]
"""
import ast
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

D = CA._rescue_escalation_decision
COOL = CA._RESCUE_ESCALATE_EVERY_S


class TheRescueHasATopRung(unittest.TestCase):

    # ── ⛔ THE THREE REFUSALS ────────────────────────────────────────────────────────────────
    def test_it_NEVER_escalates_while_a_reel_is_recording(self):
        """⛔ THE ONE THAT COSTS HIM SOMETHING IRREPLACEABLE. A blank window is a refresh; a
        relaunch mid-capture is footage he cannot get back. This beats ANY futile count."""
        for futile in (2, 3, 50):
            go, why = D(futile, 10_000.0, 0.0, True)
            self.assertFalse(go, "escalated to a relaunch with futile=%d while a reel was "
                                 "RECORDING — that ends his capture to fix a repaint" % futile)
            self.assertIn("recording", why)

    def test_ONE_failure_is_not_a_pattern(self):
        """A single futile rescue can be a race — the pixels sampled before the repaint landed.
        Relaunching his console on one sample is the console being twitchy, not careful."""
        go, why = D(1, 10_000.0, 0.0, False)
        self.assertFalse(go, "one futile rescue triggers a full process relaunch")
        self.assertIn("not a pattern", why)

    def test_the_cooldown_makes_a_RESTART_LOOP_impossible(self):
        """⛔⛔ THE WORST OUTCOME THIS COULD HAVE. If the underlying fault survives a relaunch, the
        futile count keeps climbing and nothing else stops it — so the cooldown, not the counter, is
        what bounds this. Held at the moment it fires, held a second before it expires."""
        self.assertFalse(D(9, 10_000.0, 10_000.0, False)[0],
                         "a second escalation is allowed immediately after the first — his console "
                         "would restart itself in a loop for as long as the fault lasts")
        self.assertFalse(D(9, 10_000.0 + COOL - 1.0, 10_000.0, False)[0],
                         "the cooldown expires early")
        self.assertTrue(D(9, 10_000.0 + COOL + 1.0, 10_000.0, False)[0],
                        "the cooldown never expires, so exactly one escalation is possible per "
                        "process — the rung exists once and then is gone")

    def test_the_cooldown_is_long_enough_to_not_be_a_loop(self):
        """⚠ THE FIXTURE. Every law above holds at ANY cooldown, including 0.5s — which would be a
        restart loop that still passed. The VALUE is the protection, so it is pinned separately."""
        self.assertGreaterEqual(COOL, 300.0,
                                "the escalation cooldown fell to %.0fs — at that spacing a "
                                "persistent fault restarts his console repeatedly" % COOL)

    # ── ✅ AND IT MUST STILL ACTUALLY FIRE ───────────────────────────────────────────────────
    def test_two_futile_rescues_on_an_idle_console_DO_escalate(self):
        """★ The whole point. Guards this careful are one edit away from never firing at all — and
        a top rung that never fires is exactly the state this file was written to end."""
        go, why = D(2, 10_000.0, 0.0, False)
        self.assertTrue(go, "two futile rescues on an idle console still escalate to nothing — "
                            "he remains the fallback, which is the defect")
        self.assertIn("futile", why)

    def test_the_reason_is_always_specific(self):
        """⚠ Every refusal must SAY which one it was, or the journal records 'no escalation' and a
        reader cannot tell a careful hold from a broken check. [[zero-needs-a-denominator]]"""
        for args in ((2, 10_000.0, 0.0, True), (1, 10_000.0, 0.0, False),
                     (9, 10_000.0, 10_000.0, False), (2, 10_000.0, 0.0, False)):
            why = D(*args)[1]
            self.assertTrue(why and len(why) > 12, "an empty reason for %r" % (args,))

    def test_a_missing_or_None_count_does_not_crash_the_rescue_loop(self):
        """⚠ It is read straight out of a dict that may never have been written. An exception here
        is swallowed by the loop, so this would fail SILENTLY and the rung would simply not exist."""
        for bad in (None, 0, "", False):
            self.assertFalse(D(bad, 10_000.0, None, False)[0],
                             "an absent futile count (%r) read as grounds to relaunch" % (bad,))

    # ── ⛔⛔ THE INTERACTION THAT NEARLY SHIPPED ─────────────────────────────────────────────
    def test_a_DEGRADED_aliveness_read_counts_as_RECORDING(self):
        """⛔⛔ TWO CORRECT FIXES BROKE EACH OTHER, and this is the law that holds them apart.

        The same version made `_agent_alive()` non-blocking — refused the lock, it answers from a
        10-second pid cache. During `start_agent` the lock IS held (across the spawn) and that cache
        is still EMPTY, so `_agent_alive()` answers **False while a reel is starting**. The
        escalation gates on exactly that answer. Trusting it would relaunch the process during the
        capture it is forbidden to touch — the one outcome the gates above exist to prevent.

        A refused read is UNKNOWN, and unknown fails safe toward the footage."""
        real = CA._agent_alive
        try:
            # a reader that reports "not alive" while ALSO registering a refusal — precisely the
            # state start_agent produces in the first seconds of a capture
            def _degraded():
                CA._LOCK_WAIT["blocked"] += 1
                return False
            CA._agent_alive = _degraded
            self.assertTrue(CA._recording_or_unknown(),
                            "a DEGRADED aliveness read is being treated as proof that nothing is "
                            "recording — an escalation in that window kills his reel")
        finally:
            CA._agent_alive = real

    def test_a_CONFIDENT_not_alive_read_still_permits_escalation(self):
        """⚠ Fail-safe must not become fail-always. If the answer was confident, an idle console is
        still eligible — otherwise the top rung silently stops existing."""
        real = CA._agent_alive
        try:
            CA._agent_alive = lambda: False           # no refusal registered -> confident
            self.assertFalse(CA._recording_or_unknown(),
                             "a confident 'not recording' is being read as recording, so the "
                             "escalation can never fire at all")
        finally:
            CA._agent_alive = real

    def test_the_escalation_asks_the_FAIL_SAFE_question(self):
        """★★ [[plumbing-with-no-tap]]. The helper above is worthless if the loop still calls
        `_agent_alive()` directly. Parsed, because both names appear in the prose around it."""
        tree = ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "_console_rescue_loop"), None)
        called = {c.func.id for c in ast.walk(fn)
                  if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("_recording_or_unknown", called,
                      "the rescue loop went back to asking `_agent_alive()` directly, so a "
                      "degraded read during a spawn again reads as 'nothing is recording'")

    def test_the_relaunch_refuses_while_anything_is_IN_FLIGHT(self):
        """⛔⛔ FOUND BY CHECKING A COMMENT I HAD WRITTEN, and the comment was wrong.

        It claimed this path "uses the SAME door the manual button uses". It does not: the manual
        `/api/relaunch` keeps a busy list and refuses while a chronicle sweep or vault sweep is
        reading or a mini is recording — and this automatic path had NONE of it. An escalation could
        therefore have replaced the process mid-sweep, from the one caller with nobody watching.

        The flight check must be asked INSIDE the relaunch, at the point of no return, not only when
        the decision was made — a sweep can start in the seconds between."""
        tree = ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "_exec_relaunch_soon"), None)
        self.assertIsNotNone(fn, "_exec_relaunch_soon is gone")
        called = {c.func.id for c in ast.walk(fn)
                  if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("nothing_in_flight", called,
                      "the automatic relaunch no longer asks what is in flight — it can tear the "
                      "process down in the middle of a sweep, with nobody watching")
        # ⚠⚠ AND IT MUST ABANDON ON A REFUSAL. Checked by AST, because the first version of this
        # assertion split the function's TEXT on "nothing_in_flight" and landed in the DOCSTRING
        # ABOVE — which names the helper while explaining the rule. Seventh time in this session a
        # guard read prose as code. Judge code by its tree. [[source-reading-guard]]
        inner = next((n for n in ast.walk(fn) if isinstance(n, ast.FunctionDef)
                      and n.name == "_go"), None)
        self.assertIsNotNone(inner, "the relaunch worker _go is gone")
        guarded = False
        for node in ast.walk(inner):
            if isinstance(node, ast.If) and any(isinstance(b, ast.Return) for b in node.body):
                guarded = True
        self.assertTrue(guarded,
                        "nothing in the relaunch worker returns early — the in-flight check is "
                        "read and then ignored, so the process is replaced anyway")

    # ── ⚠ THE JOIN — PARSED, NEVER GREPPED ──────────────────────────────────────────────────
    def test_the_rescue_loop_actually_CALLS_the_decision(self):
        """★★ [[plumbing-with-no-tap]] — this repo's most repeated defect, and the reason for the
        AST. A substring search for the name is satisfied by the docstring above and by the comment
        inside the loop, so deleting the real call would leave a grep-based law GREEN over dead
        code. That happened to `_chronWaitingJump` in this same session."""
        tree = ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "_console_rescue_loop"), None)
        self.assertIsNotNone(fn, "_console_rescue_loop is gone")
        called = {c.func.id for c in ast.walk(fn)
                  if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        self.assertIn("_rescue_escalation_decision", called,
                      "the rescue loop no longer CALLS the escalation decision — the top rung is "
                      "defined, tested, and unreachable")
        self.assertIn("_exec_relaunch_soon", called,
                      "nothing in the rescue loop performs the escalation it just decided on")

    def test_the_escalation_is_recorded_as_a_fault(self):
        """⚠ An escalation that leaves no trace is a console that restarts for reasons nobody can
        reconstruct afterwards. It must be in the same journal as the rescues it follows."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn('"console-escalating-to-relaunch"', src,
                      "the escalation no longer records a fault row, so a self-restart is "
                      "indistinguishable from a crash in his journal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
