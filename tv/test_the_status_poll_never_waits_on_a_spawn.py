# -*- coding: utf-8 -*-
"""v2772 — ON AIR SPUN "LOADING" WHILE THE RECORDING WAS ALREADY RUNNING.

Konyo, 2026-09-08: *"just loading on air and not turning on and OFF AIR is still greyed out"* — and
separately, correctly: *"on air is still just should work regardless."*

=== THE DEFECT ===
`start_agent` holds `_lock` across a **166-line** block that contains `subprocess.Popen()`,
`time.sleep(0.2)` and three `open()` calls. Four functions on the /api/status path — `_agent_alive`,
`_pid_alive`, `_pid_cached`, `_capture_health` — needed that SAME lock for microseconds each (one
`.poll()`). So for the whole duration of a spawn, every status poll queued behind it.

The action always succeeded. `/api/on` returned ok with a pid, the agent came up, the reel recorded.
Only the UI's VIEW of it was wedged, which is why it looked like ON AIR "did nothing" while the
capture was in fact running.

=== ⚠⚠ WHAT THIS FIX DOES **NOT** CLAIM ===
It does NOT explain the other measured wedge: /api/status taking **30-52s during a chronicle sweep
with no agent running at all**. `start_agent` was not executing then, so this cannot be its cause. A
cross-family review on 2026-09-08 was asked to choose between `_lock` and `_PRUNE_LOCK` for that one
and answered **UNKNOWN** — no evidence positively supports either. That question is still open, and
`lockWait` below is the instrument that settles it from his own machine:

    slow /api/status WITH `blocked` climbing  -> `_lock` is the contended one
    slow /api/status WITH `blocked` flat      -> it is NOT `_lock`; look at `_PRUNE_LOCK`

⛔ So this file pins a REAL, INDEPENDENTLY-CONFIRMED defect ("holding a lock across Popen+sleep while
a UI-polled health endpoint needs that lock" — judged a defect on its own merits by a different model
family) and is careful not to be read as closing the sweep question. [[unknown-stays-unknown]]

=== ⚠ WHY A BOUNDED READ IS SAFE HERE ===
Every bounded reader falls back to a source needing no lock — the 10-second pid cache, or the OS. A
refusal costs at most a slightly older answer. A status poll 10s stale is useful; one that never
returns is what he was looking at.
"""
import ast
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

HOLD_S = 3.0


class _HoldsTheLock(object):
    """Hold `_lock` exactly as `start_agent` does across its Popen, then let go."""

    def __enter__(self):
        self._release = threading.Event()
        self._holding = threading.Event()

        def _hold():
            with CA._lock:
                self._holding.set()
                self._release.wait(HOLD_S)
        self._t = threading.Thread(target=_hold, daemon=True)
        self._t.start()
        assert self._holding.wait(2.0), "could not acquire _lock to set the test up"
        return self

    def __exit__(self, *a):
        self._release.set()
        self._t.join(timeout=HOLD_S + 2.0)


class TheStatusPollNeverWaitsOnASpawn(unittest.TestCase):

    # ── ⚠⚠ THE LAW, MEASURED ────────────────────────────────────────────────────────────────
    def test_agent_alive_answers_while_the_lock_is_held(self):
        """★★ THE WHOLE BUG, REPRODUCED. With `_lock` held — which is what a spawn does for 166
        lines — `_agent_alive()` must still answer promptly. Before the fix this call took as long
        as the holder held it, and his UI spun for exactly that long."""
        with _HoldsTheLock():
            t0 = time.time()
            CA._agent_alive()
            dt = time.time() - t0
        self.assertLess(dt, HOLD_S - 0.5,
                        "_agent_alive() waited %.2fs for a lock held by a spawn — the status poll "
                        "is blocked for the whole of start_agent, so ON AIR shows 'loading' while "
                        "the recording is already running" % dt)

    def test_pid_cached_answers_while_the_lock_is_held(self):
        with _HoldsTheLock():
            t0 = time.time()
            CA._pid_cached()
            dt = time.time() - t0
        self.assertLess(dt, HOLD_S - 0.5,
                        "_pid_cached() blocked for %.2fs behind the lock" % dt)

    def test_pid_alive_answers_while_the_lock_is_held(self):
        with _HoldsTheLock():
            t0 = time.time()
            CA._pid_alive(os.getpid())
            dt = time.time() - t0
        self.assertLess(dt, HOLD_S - 0.5,
                        "_pid_alive() blocked for %.2fs behind the lock" % dt)

    def test_the_wait_is_bounded_and_SHORT(self):
        """⚠ THE FIXTURE. Every law above passes at ANY finite timeout, including 60s. The VALUE is
        the protection — he polls roughly once a second, so the budget must sit well under that."""
        self.assertGreater(CA._STATE_READ_WAIT_S, 0.0, "the bound was removed")
        self.assertLessEqual(CA._STATE_READ_WAIT_S, 1.0,
                             "a status read may now wait %.2fs — longer than his poll interval, so "
                             "polls stack up and the UI stalls again" % CA._STATE_READ_WAIT_S)

    # ── ⚠ THE INSTRUMENT, WHICH IS HALF THE POINT ───────────────────────────────────────────
    def test_a_refused_read_is_COUNTED(self):
        """★ The open sweep question is settled by this counter or not at all. A bounded read that
        silently degrades is worse than the block it replaced — it would hide the contention that is
        still unexplained."""
        before = CA._LOCK_WAIT["blocked"]
        with _HoldsTheLock():
            CA._agent_alive()
        self.assertGreater(CA._LOCK_WAIT["blocked"], before,
                           "a status read was refused the lock and NOTHING recorded it — the "
                           "contention is now invisible instead of merely slow")
        # ⚠ MEASURED, and it corrects an assumption this test was first written with: the refusal
        # CASCADES. `_agent_alive` is refused, falls through to `_pid_cached`, and that is refused
        # too — so `last` names the FINAL reader in the chain, not the first. That is correct and
        # is exactly the designed degradation: the chain ends at the 10-second pid cache, which
        # needs no lock, so it always terminates in an answer.
        self.assertIn(CA._LOCK_WAIT["last"],
                      ("agent_alive", "pid_cached", "pid_alive", "capture_health"),
                      "the refusal does not say WHICH reader was blocked")
        self.assertGreaterEqual(CA._LOCK_WAIT["blocked"] - before, 2,
                                "only one refusal recorded — `_agent_alive` should have been "
                                "refused AND its `_pid_cached` fallback too; if the chain now "
                                "stops early, a reader is blocking somewhere this test cannot see")

    def test_blocked_is_published_WITH_its_denominator(self):
        """⚠ `blocked: 0` is meaningless alone — it reads identically whether nothing was ever
        contended or nothing was ever read. [[zero-needs-a-denominator]]"""
        self.assertIn("reads", CA._LOCK_WAIT,
                      "the refusal counter has no denominator")
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn('"reads": _LOCK_WAIT["reads"]', src,
                      "the denominator is counted but never published, so a reader of /api/status "
                      "sees a bare 0 and cannot tell quiet from unmeasured")

    # ── ⛔ THE ROOT CAUSE IS STILL THERE, AND MUST STAY VISIBLE ──────────────────────────────
    def test_start_agent_still_holds_the_lock_across_its_spawn(self):
        """⛔ THIS TEST ASSERTS THE BUG IS STILL PRESENT, ON PURPOSE — and must be deleted, not
        'fixed', the day someone narrows `start_agent`.

        The readers were made bounded because that is surgical and provably safe. Narrowing a
        166-line critical section containing a process spawn is NOT safe to do unattended — get it
        wrong and two ON AIR presses race into a double capture. So the root cause is documented and
        left, and this law makes sure that decision stays a DECISION rather than being forgotten. If
        it ever goes red, someone narrowed the block and this file should be re-read, not patched.
        """
        tree = ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "start_agent"), None)
        self.assertIsNotNone(fn, "start_agent is gone")
        widest = 0
        for n in ast.walk(fn):
            if isinstance(n, ast.With) and any(
                    getattr(i.context_expr, "id", None) == "_lock" for i in n.items):
                widest = max(widest, (n.end_lineno or n.lineno) - n.lineno)
        self.assertGreater(widest, 50,
                           "start_agent's lock block is now %d lines — if it was narrowed "
                           "deliberately, DELETE this law and its note; the bounded readers stay "
                           "useful either way" % widest)



if __name__ == "__main__":
    unittest.main(verbosity=2)
