# -*- coding: utf-8 -*-
"""v2770 — THE RIVER HAD AN OUTLET AND NOTHING DRIVING IT.

Konyo: *"so the river runs smooth and automized down the river in a loop like a waterfall from
station down to tombstone"*, and *"it just flows and eats session reels regardless of the route it
come from initially"*.

MEASURED, and found by the post-ship review of v2764 rather than by me: `reel_route_lane.apply()`
was referenced by NOTHING — its own `main()` and its own test. `console_doctor` called `plan()`,
which reads. No tick, timer, loop or route invoked the lane. **The six reels closed out in v2764
were moved by hand.**

So the moment retro_triage classified a new reel as EMPTY, the `river outlet` row would return
MISSING — "N of M reel(s) can be closed out RIGHT NOW and have not been" — and stay there
indefinitely, because nothing anywhere could clear it. The river's DIAGNOSIS flowed. The river did
not. [[plumbing-with-no-tap]] [[the-unjoined-end]]

=== ⚠⚠ WHY THE LANE ACTS *BEFORE* THE WALK, AND WHY THAT IS NOT A PREFERENCE ===
The lane writes ACTOR rows; `reel_router.route()`'s outlet overlay reads them; the observer walk
then finds those reels already at ROUTED and writes nothing. Reversed, the walk would derive EMPTY
from the evidence, stamp it, and the lane would move the reel back — two rows per tick, for ever,
into a journal that is append-only and never correctable.

v2769's guard makes that contradiction UNWRITABLE rather than merely unlikely (an observer may not
overwrite a standing actor row). The ordering is what makes the walk a silent no-op instead of a
refusal on every single tick.

=== ⚠ WHAT THE DRIVER MAY NOT DO ===
It rides the TRIAGE tick, never the retention pass — the same rule the river walk already follows,
because that one deletes. It writes ROUTED and only ROUTED. TOMBSTONE stays with the deleter,
behind `_PRUNE_SAFE_TO_RUN`, which is False and stays False.
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

import console_doctor as D  # noqa: E402
import reel_route_lane as LANE  # noqa: E402
import river_stamp as ST  # noqa: E402

APP = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _loop_body(code_only=True):
    """The triage loop's source. -> str

    ⚠⚠ COMMENTS STRIPPED BY DEFAULT, AND THAT IS NOT TIDINESS. Every law below asks whether the
    loop DOES something. The loop's own comment block explains the defect being fixed and therefore
    contains the literal text `reel_route_lane.apply()` — so a law asserting ".apply(" is present
    was satisfied by the PROSE, and a sabotage that removed the real call stayed GREEN. That is the
    fifth time in this session a guard read comments as code. Judge CODE by its code.
    [[measured-true-read-wrong]] [[source-reading-guard]]
    """
    i = APP.find("def _retro_triage_loop(")
    if i < 0:
        return ""
    j = APP.find("\ndef ", i + 1)
    body = APP[i:j if j > i else len(APP)]
    if not code_only:
        return body
    return "\n".join(ln.split("#", 1)[0] if ln.strip().startswith("#") else ln
                      for ln in body.split("\n"))


class TheRiverHasADriver(unittest.TestCase):

    # ── ⚠⚠ THE JOIN ─────────────────────────────────────────────────────────────────────────
    def test_something_actually_CALLS_the_lane(self):
        """★ THE WHOLE POINT. Built and not called is this repo's most repeated defect, and v2764
        shipped exactly that: an outlet with no driver."""
        body = _loop_body()
        self.assertTrue(body, "the triage loop is gone — this law inspected nothing")
        self.assertIn("import reel_route_lane", body,
                      "no loop drives the route lane, so the river only moves when a person types "
                      "a CLI command and the outlet row can never clear itself")
        self.assertIn("_rrl.apply(", body,
                      "the loop imports the lane but never lets it ACT — plan() only reads, so the "
                      "outlet stays exactly as unreachable as it was before it had a driver")

    def test_the_lane_ACTS_BEFORE_the_walk_OBSERVES(self):
        """★★ ORDER IS CORRECTNESS HERE, not taste. Walk-then-lane writes two rows per tick for
        ever into an append-only store: the walk derives EMPTY from evidence the lane is about to
        supersede. v2769's guard makes that unwritable; this ordering makes it a silent no-op."""
        body = _loop_body()
        # ⚠ COMPARE THE CALLS, NOT THE MODULE NAMES. My first cut compared find("reel_route_lane")
        # against find("river_stamp") and failed: the loop's own PROSE mentions river_stamp ~1000
        # chars before either call, so it "proved" the walk ran first. A guard that greps source
        # must match executable text, not the comments explaining it. [[source-reading-guard]]
        lane = body.find("_rrl.apply(")
        walk = body.find("_rvs.run(")
        self.assertGreater(lane, 0, "the lane is not driven at all")
        self.assertGreater(walk, 0, "the river walk is gone from the loop")
        self.assertLess(lane, walk,
                        "the observer WALK runs before the acting LANE. The walk would stamp the "
                        "station the lane is about to change, and every tick would cost a "
                        "transition row in a journal that is never trimmed")

    def test_the_driver_publishes_what_it_did(self):
        import control_app as CA
        rec = getattr(CA, "_ROUTE_LANE", None)
        self.assertIsInstance(rec, dict, "nothing records what the driver did, so the console "
                                         "cannot tell a lane that ran from one that never has")
        for k in ("at", "runs", "ok", "routed", "already", "refused", "declined", "why"):
            self.assertIn(k, rec, "the driver record has no %r" % k)

    def test_the_declined_count_is_carried(self):
        """⚠ 12 reels sit at CAPTURE owing a capture change no lane can supply. A driver reporting
        only what it MOVED reads as done on a shelf where they are permanently stuck."""
        import control_app as CA
        self.assertIn("declined", getattr(CA, "_ROUTE_LANE", {}))
        # ⚠ MATCH THE FIELD, NOT ONE SPELLING OF THE ASSIGNMENT. This pinned
        # `_ROUTE_LANE["declined"]` and went red when the record moved to an atomic dict-literal
        # swap that carries the same field. PIN THE LAW, NOT THE LITERAL. [[regression-guard]]
        body = _loop_body()
        i = body.find("_rrl.apply(")
        j = body.find("_rvs.run(", i)
        self.assertIn('"declined"', body[i:j],
                      "the loop drops the declined count, so the honest other half — the reels "
                      "that owe a step no lane can supply — never reaches the console")

    # ── ⚠ IT MUST NOT BREAK THE LOOP, AND MUST NOT WRITE ON A QUIET RIVER ───────────────────
    def test_a_RAISING_lane_does_not_take_the_loop_down(self):
        body = _loop_body()
        # ⚠ ANCHORED AT BOTH ENDS, NEVER A FIXED WINDOW. My first cut read body[i-400:i+1400] and
        # went red because the comment above the call is longer than the window — so the guard
        # measured my guess about the file's shape rather than the file. [[source-reading-guard]]
        i = body.find("_rrl.apply(")
        self.assertGreater(i, 0, "the lane call is gone")
        j = body.find("_rvs.run(", i)
        self.assertGreater(j, i, "the walk no longer follows the lane")
        seg = body[i:j]
        self.assertIn("except Exception", seg,
                      "the driver is unguarded, so one bad tick kills the triage loop that also "
                      "carries the survey and the river walk")
        self.assertIn("ok=False", seg,
                      "a failed driver tick leaves the record looking like a successful one")

    def test_a_FAILING_tick_still_counts_as_a_RUN(self):
        """★★ FOUND BY THE SECOND EYE on v2770, and it was a real bug. The first cut set at/ok/why
        on failure and left `runs` at 0 — so the doctor row, which branches on `runs == 0`,
        reported "the route lane HAS NEVER RUN" for a lane that ran every tick and failed every
        time. A DEAD LOOP and a FAILING LOOP are different findings and must not share a sentence:
        one means the wiring broke, the other means the lane is broken. [[zero-needs-a-denominator]]
        """
        body = _loop_body()
        i = body.find("_rrl.apply(")
        j = body.find("_rvs.run(", i)
        seg = body[i:j]
        k = seg.find("except Exception")
        self.assertGreater(k, 0, "the driver has no failure path")
        self.assertIn("runs=", seg[k:],
                      "the failure path does not record that a run HAPPENED, so a lane failing on "
                      "every tick is reported as one that has never run")

    def test_the_record_is_swapped_ATOMICALLY_not_mutated_field_by_field(self):
        """★ RAISED BY THE SECOND EYE: the doctor reads this dict from another thread and could see
        it half-written — `runs` incremented while `ok` still held the previous tick's value. A
        rebind is atomic; eight separate writes are eight chances to be read mid-flight."""
        body = _loop_body()
        i = body.find("_rrl.apply(")
        j = body.find("_rvs.run(", i)
        seg = body[i:j]
        self.assertIn('globals()["_ROUTE_LANE"] = _nxt', seg,
                      "the driver record is not swapped in one assignment")
        self.assertNotIn('_ROUTE_LANE["routed"] =', seg,
                         "the record is still being mutated field by field, so a reader can catch "
                         "it half-updated")

    def test_the_unattended_writer_has_a_PER_TICK_CEILING(self):
        """★ RAISED BY THE SECOND EYE: "an actor that mutates state should not be driven by a blind
        timer; one incorrect selection rule can stamp an unbounded number of reels." The lane is
        narrow by construction and a wrong stamp IS recoverable — a later actor row supersedes it —
        but recoverable is not bounded. A cap turns a bad rule into a slow visible drip instead of
        one sweep across the whole shelf; the remainder is taken on the next tick."""
        body = _loop_body()
        i = body.find("_rrl.apply(")
        j = body.find("_rvs.run(", i)
        seg = body[i:j]
        self.assertIn("limit=", seg,
                      "the timer-driven lane runs with NO ceiling, so a wrong selection rule "
                      "stamps the entire shelf in a single unattended tick")
        import re as _re
        m = _re.search(r"_ROUTE_LANE_MAX_PER_TICK\s*=\s*(\d+)", body)
        self.assertIsNotNone(m, "the ceiling is not a named constant")
        self.assertLessEqual(int(m.group(1)), 25,
                             "the per-tick ceiling is %s — high enough that a bad rule sweeps the "
                             "shelf before anyone looks" % m.group(1))

    def test_a_quiet_river_costs_ZERO_rows(self):
        """★ The driver runs on a short tick. If a no-op tick wrote anything, an append-only
        journal would grow for ever on an idle machine."""
        before = len(ST.rows().get("rows") or [])
        r = LANE.apply(by="test:quiet-river")
        self.assertTrue(r["ok"], r["why"])
        after = len(ST.rows().get("rows") or [])
        self.assertEqual(before + (r["routed"] or 0), after,
                         "the lane wrote %d row(s) while reporting %d routed — a tick is writing "
                         "rows it does not account for" % (after - before, r["routed"]))

    # ── ⛔ THE LINE THE DRIVER MAY NOT CROSS ────────────────────────────────────────────────
    def test_the_driver_rides_the_TRIAGE_tick_never_the_deleter(self):
        """⛔ The river walk already follows this rule because the retention pass DELETES. A driver
        that closes reels out must not ride the pass that removes them."""
        body = _loop_body()
        self.assertIn("reel_route_lane", body)
        for banned in ("reel_retention", "apply_plan", "_tombstone", "prune_once"):
            self.assertNotIn(banned, body,
                             "the triage loop now reaches for %r — the driver has been put on the "
                             "pass that deletes" % banned)

    def test_the_prune_lock_is_STILL_false(self):
        import control_app as CA
        self.assertIs(False, getattr(CA, "_PRUNE_SAFE_TO_RUN", "<absent>"),
                      "the arming lock moved. His instruction is standing: do not arm the prune.")

    # ── ⚠⚠ THE HEART ────────────────────────────────────────────────────────────────────────
    def test_the_doctor_separates_A_DEAD_DRIVER_from_A_BUSY_ONE(self):
        """★ Until v2770 the row could say "they have not been closed out" but never WHY, and the
        answer was "because no code anywhere runs the lane". A waiting queue means two different
        things now, and one of them is a dead loop."""
        i = APP.find("def _check_the_river_has_an_outlet")
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        i = src.find("def _check_the_river_has_an_outlet")
        blk = src[i:src.find("\ndef ", i + 1)]
        self.assertIn("_ROUTE_LANE", blk, "the outlet row does not ask the driver anything")
        self.assertIn("HAS NEVER RUN", blk,
                      "a driver that has never run is reported with the same sentence as one that "
                      "ran a second ago — a dead loop reading as a busy one")

    def test_the_row_still_answers(self):
        st, say = dict(D.CHECKS)["river outlet"]()
        self.assertIn(st, (D.OK, D.MISSING, D.UNKNOWN))
        self.assertTrue(say and len(say) > 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
