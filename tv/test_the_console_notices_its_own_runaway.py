# -*- coding: utf-8 -*-
"""v2775 — REG-699: HIS CONSOLE BURNED A CORE FOR TWO HOURS AND NOTHING NOTICED BUT HIM.

Measured 2026-09-08 while he was away: pid pinned at 108-109% CPU, `/api/status` returning 0 bytes
at a 25s timeout on every probe, its own log silent for 38 minutes, NO capture running, both child
processes idle — and `/` still serving in 0.69s, so the server was alive with one thread burning a
core while every other thread starved behind the GIL. A freshly booted console on the same code
idles at 0.0% and answers in 0.022s.

⛔ THE CAUSE IS STILL UNKNOWN AND THIS FILE DOES NOT CLAIM OTHERWISE. What it fixes is the part that
actually cost him: **nothing noticed**. He was the detector, twice in one night. And the offending
frame could not be named afterwards because the console had started BEFORE the faulthandler shipped
— the one instrument that would have printed it was not in the running process.

=== ⚠⚠ WHY IT TIMES ITSELF INSTEAD OF POLLING ITS OWN API ===
A watchdog that polls `/api/status` would be [[poll-slower-than-its-interval]] exactly: the thing it
watches for is what makes that poll slow, and a poll slower than its interval saturates the machine
further. This thread sleeps a known interval and measures how long the sleep ACTUALLY took. A loop
that asks for 5s and gets 40s IS the starvation, measured at the source, needing no socket, no lock,
and no cooperation from the wedged thread.

=== ⚠⚠ THE FIRST DESIGN WAS WRONG AND A PROOF RUN IS WHAT SAID SO ===
It fired only on `late AND busy`. Proving it with 12 pure-Python burner threads produced
**cpu = 1.01 core(s) with a tick of 1.1s — NOT LATE AT ALL** — and detected nothing. Pure-Python
loops release the GIL every switch interval (~5ms), so other threads keep being scheduled: "late
tick" cannot see a Python-level spin, and a watchdog built on it would have slept through the very
event it was written for.

That failure is also what finally reconciled his three measurements, which no earlier story did:

    `/` served in 0.69s          ->  the server was NOT globally starved
    `/api/status` died at 25s+   ->  something specific to THAT path was blocked
    the process burned 108% CPU  ->  something was spinning

A thread WAITING on a lock burns 0% CPU, which is why "no lock is involved" looked right — but the
HOLDER can be spinning. **One thread spinning while holding `_lock`** explains all three at once and
is the only shape that does. So the second signal is `_LOCK_WAIT["blocked"]` growth: status reads
that asked for the lock and were refused.

    late alone            -> the Mac slept or swapped. Never a runaway.
    busy alone            -> a chronicle sweep. Legitimate work, and it MUST stay quiet.
    busy + refusals       -> a spinning lock holder. HIS SHAPE.
    busy + late           -> true global starvation (a C-level call holding the GIL). Still caught.

=== ✅ PROVEN END TO END, 2026-09-08 ===
    idle, 5s                                  ->  0 detections
    4 threads burning a core, holding nothing ->  0 detections  ("busy but nothing is refused")
    1 thread spinning WHILE HOLDING the lock  ->  7 detections
    and the dump named it: `line 18 in spin_holding_lock`, 12 thread headers captured.
"""
import io
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

V = CA._runaway_verdict
TICK = CA._RUNAWAY_TICK_S


class TheConsoleNoticesItsOwnRunaway(unittest.TestCase):

    # ── ⚠⚠ THE SHAPE THAT WAS MEASURED ──────────────────────────────────────────────────────
    def test_late_AND_burning_for_three_ticks_IS_a_runaway(self):
        """★★ His actual numbers: a tick that should take 5s taking 40s while the process uses
        ~1.05 cores. One tick is a hiccup; three consecutive is a state."""
        self.assertFalse(V(40.0, TICK, 1.05, 0)[0], "fires on the FIRST late tick")
        self.assertFalse(V(40.0, TICK, 1.05, 1)[0], "fires on the second")
        hit, streak, why = V(40.0, TICK, 1.05, 2)
        self.assertTrue(hit, "three consecutive late-and-burning ticks do NOT register as a "
                             "runaway — this is the exact state his console sat in for two hours")
        self.assertGreaterEqual(streak, CA._RUNAWAY_NEED)
        self.assertIn("RUNAWAY", why)

    # ── ⛔ THE TWO INNOCENT STATES IT MUST NOT ACCUSE ────────────────────────────────────────
    def test_a_slept_or_swapped_MAC_is_not_a_runaway(self):
        """⛔ A closed lid produces a very late tick with NO cpu. Reporting that as a runaway would
        make the alarm furniture, and furniture is not believed on the day it matters."""
        hit, streak, why = V(120.0, TICK, 0.01, 0)
        self.assertFalse(hit, "a sleeping Mac is being called a runaway")
        self.assertEqual(0, streak, "a sleep is accumulating a streak toward a false detection")
        self.assertIn("not a runaway", why)

    def test_a_legitimate_SWEEP_is_not_a_runaway(self):
        """⛔ A chronicle sweep burns a core ON PURPOSE. It is only pathological when the process
        also stops being scheduled."""
        hit, streak, _ = V(5.2, TICK, 1.10, 0)
        self.assertFalse(hit, "a busy-but-responsive process is being called a runaway — every "
                              "sweep he runs would trip this")
        self.assertEqual(0, streak)

    def test_a_streak_RESETS_on_one_healthy_tick(self):
        """⚠ Otherwise two late ticks an hour apart eventually add up to a false detection."""
        self.assertEqual(2, V(40.0, TICK, 1.05, 1)[1])
        self.assertEqual(0, V(5.1, TICK, 0.02, 2)[1],
                         "a healthy tick does not clear the streak, so unrelated hiccups "
                         "accumulate into a detection that never happened")

    # ── ⚠ UNKNOWN IS NOT A DETECTION ────────────────────────────────────────────────────────
    def test_an_UNMEASURED_tick_never_fires_and_never_accumulates(self):
        """⚠ `resource.getrusage` can fail. A watchdog that escalates on absent evidence is worse
        than one that sleeps through the fault. [[unknown-stays-unknown]]"""
        for args in ((None, TICK, 1.05, 2), (40.0, TICK, None, 2), (None, TICK, None, 2)):
            hit, streak, why = V(*args)
            self.assertFalse(hit, "fired on an unmeasured tick: %r" % (args,))
            self.assertEqual(0, streak, "an unmeasured tick kept the streak alive")
            self.assertIn("not measured", why)

    # ── ⚠⚠ THE SIGNAL THAT ACTUALLY CATCHES HIS FAULT ───────────────────────────────────────
    def test_a_SPINNING_LOCK_HOLDER_is_caught(self):
        """★★ HIS SHAPE. Busy AND refusing status reads, with a perfectly punctual tick — which is
        what the first design missed entirely."""
        self.assertFalse(V(1.1, TICK, 1.01, 0, 7)[0], "fires on the first tick")
        hit, streak, why = V(1.1, TICK, 1.01, 2, 7)
        self.assertTrue(hit, "a thread spinning while holding the status lock is NOT detected — "
                             "this is the exact fault that wedged his console for two hours")
        self.assertIn("SPINNING WHILE HOLDING", why)
        self.assertIn("7", why, "the refusal count is not in the reason, so a reader cannot tell "
                                "a trickle from a flood")

    def test_a_BUSY_SWEEP_WITH_NO_REFUSALS_STAYS_QUIET(self):
        """⛔⛔ THE FALSE POSITIVE THAT WOULD RUIN IT. A chronicle sweep burns a full core on
        purpose. MEASURED in the proof run: 4 threads at 1.00 core(s) with 0 refusals produced 0
        detections. If this ever fires, every sweep he runs dumps 40 thread stacks into his log and
        the alarm becomes furniture."""
        for streak in (0, 5, 50):
            hit, st, why = V(1.0, TICK, 1.00, streak, 0)
            self.assertFalse(hit, "a legitimate sweep is being reported as a runaway")
            self.assertEqual(0, st, "a sweep accumulates a streak toward a false detection")
            self.assertIn("nothing is being refused", why)

    def test_an_ABSENT_refusal_count_does_not_invent_a_detection(self):
        """⚠ `blocked_delta=None` means the lock counter was not read this tick. Unknown must not
        be treated as zero OR as evidence. [[unknown-stays-unknown]]"""
        self.assertFalse(V(1.1, TICK, 1.01, 9, None)[0],
                         "an unmeasured refusal count is being read as refusals")

    # ── ⚠ THE MEASUREMENT SOURCE MUST ACTUALLY WORK ─────────────────────────────────────────
    def test_cpu_seconds_really_moves_under_load(self):
        """★ The verdict is arithmetic on `_cpu_seconds()`. If that returned a constant — or None
        on this platform — every law above would still pass while the watchdog measured nothing.
        [[feedback-blind-fixture-green-gate]]"""
        a = CA._cpu_seconds()
        self.assertIsNotNone(a, "_cpu_seconds() is None on this platform, so the runaway watch "
                                "can never fire here — that is UNMEASURED, not healthy")
        t0 = time.time()
        x = 0
        while time.time() - t0 < 0.6:
            x += 1                      # deliberate busy work
        b = CA._cpu_seconds()
        self.assertGreater(b, a, "_cpu_seconds() did not move across 0.6s of busy work, so the "
                                 "cpu half of the verdict is measuring a constant")

    def test_the_thresholds_are_reachable(self):
        """⚠ A threshold above the ceiling is an absent one. `cpu_frac` is CPU-seconds per
        wall-second, so 1.0 = ONE core — not a fraction of all cores. Set against the wrong
        denominator (0.80 of 8 cores = 6.4) this branch could never run.
        [[feedback-threshold-above-the-ceiling]]"""
        self.assertLessEqual(CA._RUNAWAY_CPU_BUSY, 1.0,
                             "the cpu bar is %.2f — above one core, so a single-threaded runaway "
                             "like the one measured can never reach it" % CA._RUNAWAY_CPU_BUSY)
        self.assertGreaterEqual(CA._RUNAWAY_CPU_BUSY, 0.5,
                                "the cpu bar is so low that ordinary work trips it")
        self.assertGreaterEqual(CA._RUNAWAY_LATE_FACTOR, 2.0,
                                "the lateness factor is under 2x — normal scheduler jitter would "
                                "register as starvation")

    # ── ⚠ FROM THE CROSS-FAMILY REVIEW OF v2774 ─────────────────────────────────────────────
    def test_the_tick_is_measured_on_a_MONOTONIC_clock(self):
        """★ A reviewer named it: this loop's entire signal is "how long did my sleep actually
        take", and `time.time()` can STEP — an NTP correction, or a laptop resuming from suspend.
        A backward step silently loses a tick; a forward step invents starvation. `monotonic()`
        cannot step. Parsed, because the loop legitimately uses `time.time()` elsewhere for a
        wall-clock stamp that a human reads as an age."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find("def _runaway_watch_loop")
        blk = src[i:src.find("\n\ndef ", i + 1)]
        code = "\n".join(l for l in blk.split("\n") if not l.strip().startswith("#"))
        self.assertIn("time.monotonic()", code,
                      "the runaway tick is measured on a steppable clock again — an NTP "
                      "correction or a resume from suspend would fake or hide starvation")
        head = code[:code.find("while True")]
        self.assertNotIn("time.time()", head,
                         "the tick BASELINE is taken from time.time(); the interval must be "
                         "monotonic end to end or the two clocks are being subtracted")

    def test_the_degraded_flag_has_exactly_ONE_reader(self):
        """⛔ THE TRAP THE REVIEW CAUGHT. `_LOCK_TL.degraded` is set by `_lock_briefly` and cleared
        only by its reader — and HTTP request threads are REUSED, so a flag left set survives into
        the next request on that OS thread. That is safe ONLY while there is exactly one reader
        that clears before it looks. A second reader added later, without clearing, would read a
        refusal that belongs to some earlier request on the same thread and report a live capture
        that is not there — which blocks the rescue escalation forever."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        code = "\n".join(l for l in src.split("\n") if not l.strip().startswith("#"))
        readers = code.count("_LOCK_TL.degraded")
        # one write in _lock_briefly, one clear + one read in _recording_or_unknown
        self.assertLessEqual(readers, 3,
                             "`_LOCK_TL.degraded` is now touched %d times in code — a second "
                             "reader was added. Every reader MUST clear it first, or it reports a "
                             "refusal from an earlier request on a reused thread." % readers)
        # ⚠⚠ AST, NOT find(). Written first with two `find()` calls on the function's text, and
        # the DOCSTRING names `_agent_alive()` — so the clear appeared to come after the call it
        # precedes, and the law failed on correct code. Ninth time this session a check read prose
        # as code. Judge order by the tree. [[source-reading-guard]]
        import ast as _ast
        tree = _ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        fn = next((n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)
                   and n.name == "_recording_or_unknown"), None)
        self.assertIsNotNone(fn, "_recording_or_unknown is gone")
        body = fn.body
        if body and isinstance(body[0], _ast.Expr) and isinstance(
                getattr(body[0], "value", None), _ast.Constant):
            body = body[1:]                      # drop the docstring
        clear_at = call_at = None
        for idx, node in enumerate(body):
            for sub in _ast.walk(node):
                if (isinstance(sub, _ast.Attribute) and sub.attr == "degraded"
                        and clear_at is None and isinstance(node, _ast.Assign)):
                    clear_at = idx
                if (isinstance(sub, _ast.Call) and getattr(sub.func, "id", None) == "_agent_alive"
                        and call_at is None):
                    call_at = idx
        self.assertIsNotNone(clear_at, "the reader never clears the flag at all")
        self.assertIsNotNone(call_at, "the reader no longer calls _agent_alive()")
        self.assertLess(clear_at, call_at,
                        "the only reader no longer clears the flag BEFORE the call it is asking "
                        "about, so it can inherit a refusal from a previous request on a reused "
                        "HTTP thread")

    # ── ⚠ THE JOIN ──────────────────────────────────────────────────────────────────────────
    def test_the_watcher_is_ON_THE_ROSTER(self):
        """★★ [[plumbing-with-no-tap]] — this repo's most repeated defect. A watchdog that is never
        started is a watchdog that reports 0 detections forever, which reads exactly like health."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn('("tvd-runaway-watch", _runaway_watch_loop)', src,
                      "the runaway watch is not on the watcher roster, so it never starts")

    def test_it_publishes_its_DENOMINATOR(self):
        """⚠ `detections: 0` out of 0 ticks means the watcher is DEAD and reads identically to all
        clear. [[zero-needs-a-denominator]]"""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn('"ticks": _RUNAWAY["ticks"]', src,
                      "the runaway tick count is never published, so a reader of /api/status "
                      "cannot tell a quiet watcher from a dead one")

    def test_the_detection_DUMPS_before_anything_else(self):
        """⛔ The dump is the entire point — it names the spinning Python frame, the one fact
        nobody has had across two occurrences of REG-699. Recovery without it is how this stayed
        unexplained."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find("def _runaway_watch_loop")
        blk = src[i:src.find("\n\ndef ", i + 1)]
        code = "\n".join(l for l in blk.split("\n") if not l.strip().startswith("#"))
        self.assertIn("dump_traceback", code,
                      "the runaway detection no longer dumps thread stacks, so the next "
                      "occurrence is as unexplainable as the last two")
        self.assertIn("all_threads=True", code,
                      "the dump is not all-threads, so it cannot name the spinning one")


if __name__ == "__main__":
    unittest.main(verbosity=2)
