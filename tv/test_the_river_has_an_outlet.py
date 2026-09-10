# -*- coding: utf-8 -*-
"""THE RIVER HAD NO OUTLET: ROUTED WAS UNREACHABLE BECAUSE ONLY THE DELETER COULD WRITE IT.

Konyo: *"when we hit that section pruning/tombstone after its been extracted.. we can start working
and running tests to unlock that.. so the river runs smooth and automized down the river in a loop
like a waterfall from station down to tombstone"* — and *"there is no loop or worry because it gets
eventually tombstoned and deleted and wiped completely. only the data and information gets extracted
before hand."*

MEASURED before the change, on his 40-reel shelf:

    counts     INTAKE 0 · TRIAGE 0 · EMPTY 6 · STATION 7 · PRINTER 11 · JOIN 4 · CAPTURE 12
               ROUTED 0 · TOMBSTONE 0
    unreached  ['INTAKE', 'TRIAGE', 'ROUTED', 'TOMBSTONE']
    _station_of returns 7 of the 9 declared stations. ROUTED and TOMBSTONE are UNREACHABLE.

`river_walk.py` had already written down why, in its own note for ROUTED:

    "the gate is TOMBSTONE, and the ONLY writer of a tombstone row runs inside the deleter
     (`reel_retention.apply_plan` -> `_tombstone`). So a reel cannot be recorded as closed out
     without being removed, and removal is behind the arming lock. That weld is the gap this
     station has been empty for"

**Being finished and being deleted were the same event**, and deletion is behind
`_PRUNE_SAFE_TO_RUN`, which is False and stays False by his explicit instruction. So the river's
only exit was a locked door, and no reel could ever complete the waterfall.

=== WHAT CHANGED ===
ROUTED is the DATA fact — `reel_router.OWES["ROUTED"]` already said "the extraction contract is
satisfied; it may be released with a stamp". TOMBSTONE is the BYTES fact. They are now separable:
`reel_route_lane` writes the first, the deleter still owns the second, and the lock is untouched.

=== ⚠⚠ THE FLAP THIS HAD TO AVOID ===
Routing changes no EVIDENCE, so `_station_of` goes on deriving EMPTY for a routed reel for ever. If
the outlet overlay read observer rows, the observer walk's own output would feed back into it and
the station would oscillate EMPTY -> ROUTED -> EMPTY, appending a transition row to a
never-truncated store on every walk. The overlay reads ACTOR ROWS ONLY, and `river_stamp.run()`
cannot write one. Law `test_an_OBSERVER_row_does_not_move_a_reel` is what holds that.
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

import console_doctor as D  # noqa: E402
import reel_route_lane as LANE  # noqa: E402
import reel_router as RR  # noqa: E402
import river_stamp as ST  # noqa: E402

LSRC = io.open(os.path.join(HERE, "reel_route_lane.py"), encoding="utf-8").read()


#: ⚠ WHY A SKIP AND NOT A FAILURE — and it is NOT a pass either. Found by the post-ship review:
#: these laws walk the LIVE shelf, `tv/hist` is not in the repo, and CI sets no TV_HIST. So they
#: were GREEN ON HIS MAC (40 reels) and RED EVERYWHERE ELSE — the host-machine fixture this repo
#: has a scar for. A shelf with no reels cannot establish anything about where reels sit; it must
#: say so out loud rather than fail as if the code were broken.
#: [[feedback-blind-fixture-green-gate]] [[test-venue]]
_NO_SHELF = ("this shelf holds no reels, so nothing about reel STATIONS could be established here "
             "— a skip is NOT a pass. Run against a shelf (TV_HIST) to exercise these laws.")


def _row(reel, station, kind="actor", by="lane:route", seq=1):
    return {"at": 1788700000000 + seq, "seq": seq, "reel": reel, "station": station,
            "from": None, "by": by, "byKind": kind, "why": "fixture"}


class _Stubbed(object):
    """Swap `river_stamp.rows` for a fixture. ⚠ READ-ONLY — nothing here writes to his store."""

    def __init__(self, rows, ok=True, why=""):
        self.rows = rows
        self.ok = ok
        self.why = why

    def __enter__(self):
        self.real = ST.rows
        ST.rows = lambda path=None: {"ok": self.ok, "rows": self.rows, "why": self.why}
        return self

    def __exit__(self, *a):
        ST.rows = self.real


def _a_reel_at(station):
    """A real reel id currently deriving `station`, or None. ⚠ READ-ONLY."""
    with _Stubbed([]):
        rep = RR.route()
    for r in (rep.get("reels") or []):
        if r.get("station") == station:
            return r.get("reel")
    return None


class TheRiverHasAnOutlet(unittest.TestCase):

    # ── ⚠⚠ THE LAW: ROUTED IS REACHABLE WITHOUT DELETING ANYTHING ───────────────────────────
    def test_an_ACTOR_stamp_puts_a_reel_at_ROUTED(self):
        """★ The whole point. Before this, no input of any kind could make `route()` return ROUTED."""
        reel = _a_reel_at("EMPTY") or _a_reel_at("CAPTURE") or _a_reel_at("STATION")
        if reel is None:
            self.skipTest(_NO_SHELF)
        with _Stubbed([_row(reel, "ROUTED")]):
            rep = RR.route()
        got = [r for r in rep["reels"] if r["reel"] == reel]
        self.assertEqual(1, len(got), "the reel vanished from the walk")
        self.assertEqual("ROUTED", got[0]["station"],
                         "an acting lane closed this reel out and the router still derives %r from "
                         "the footage — ROUTED remains unreachable and no reel can finish the river"
                         % got[0]["station"])
        self.assertEqual(1, rep["counts"]["ROUTED"])
        self.assertNotIn("ROUTED", rep["unreached"])
        self.assertTrue(rep["reconciles"],
                        "the overlay broke the one-reel-one-station invariant")

    # ── ⚠⚠ THE ANTI-FLAP LAW ────────────────────────────────────────────────────────────────
    def test_an_OBSERVER_row_does_not_move_a_reel(self):
        """★ Without this the river oscillates for ever. The observer walk stamps every reel where
        the router says it is; if that fed back into the overlay, a routed reel would derive EMPTY,
        be stamped EMPTY, read as EMPTY, be stamped ROUTED... appending a row to an append-only
        store on every single walk."""
        reel = _a_reel_at("EMPTY") or _a_reel_at("STATION")
        if reel is None:
            self.skipTest(_NO_SHELF)
        with _Stubbed([_row(reel, "ROUTED", kind="observer", by="walk")]):
            rep = RR.route()
        got = [r for r in rep["reels"] if r["reel"] == reel][0]
        self.assertNotEqual("ROUTED", got["station"],
                           "an OBSERVER row moved a reel to ROUTED. A walk did not close anything "
                           "out — it only reported where the router already said the reel was, so "
                           "this is the router reading its own output back in")

    def test_the_LAST_actor_row_wins_so_a_reel_can_be_reopened(self):
        """A first-match read would pin a reel at ROUTED permanently, and no lane could undo it."""
        reel = _a_reel_at("EMPTY") or _a_reel_at("STATION")
        if reel is None:
            self.skipTest(_NO_SHELF)
        with _Stubbed([_row(reel, "ROUTED", seq=1), _row(reel, "STATION", seq=2)]):
            rep = RR.route()
        got = [r for r in rep["reels"] if r["reel"] == reel][0]
        self.assertNotEqual("ROUTED", got["station"],
                           "a later actor row re-opened this reel and the overlay still reports it "
                           "closed out — the outlet is a one-way door with no handle")

    # ── ⚠ AN UNREADABLE STORE IS UNKNOWN, NEVER "NOTHING IS ROUTED" ─────────────────────────
    def test_an_unreadable_stamp_store_is_UNKNOWN_not_zero(self):
        with _Stubbed([], ok=False, why="simulated"):
            rep = RR.route()
        self.assertFalse(rep.get("outletReadable"),
                         "the router claims the outlet was readable when the store refused")
        self.assertTrue(str(rep.get("outletWhy") or ""),
                        "nothing says WHY the outlet could not be read, so ROUTED 0 is a guess "
                        "wearing a count's clothes")

    def test_a_readable_store_says_so(self):
        with _Stubbed([]):
            rep = RR.route()
        # ⚠ THE OUTLET VERDICT IS OWED ON EVERY WALK — that is the subject of this law, and it now
        # holds on a shelf with no reels too (v2881 publishes it on the UNKNOWN return).
        self.assertTrue(rep.get("outletReadable"),
                        "a stubbed, readable store did not produce a readable verdict: %r"
                        % (rep.get("outletWhy"),))
        # ⚠⚠ ROUTED 0 IS A SECOND CLAIM, AND IT NEEDS A WALK. On a runner with no reels the walk is
        # UNKNOWN and `counts` is empty ON PURPOSE — asserting ROUTED == 0 there would demand
        # exactly the confident zero the outlet field exists to prevent, and this file would be
        # forcing the defect it was written to catch. Assert it only where a count was actually
        # taken. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
        if rep.get("counts"):
            self.assertEqual(0, rep["counts"]["ROUTED"])
        else:
            self.assertIn("UNKNOWN", str(rep.get("why") or ""),
                          "no counts were taken and nothing says the walk was UNKNOWN — an empty "
                          "census with no reason is indistinguishable from a shelf that is clear")

    # ── ⚠⚠ THE LANE ROUTES WHAT OWES A ROUTE, AND REFUSES WHAT OWES A STEP FIRST ────────────
    def test_the_lane_agrees_with_the_routers_OWES_table(self):
        """★ Two copies of one rule is how a lane keeps routing a station that stopped owing a
        route. This checks the copy against the original rather than trusting it. [[copy-drift]]"""
        ok, findings = LANE.assert_matches_owes()
        self.assertTrue(ok, "the lane's station table drifted from reel_router.OWES: %r" % findings)

    def test_CAPTURE_is_DECLINED_and_the_refusal_is_PUBLISHED(self):
        """⚠ 12 of his reels sit here. Their OWES is "CAPTURE, then ROUTE" — a step no stamp can
        supply (REG-340: the name is on a character panel the reel does not film). Routing them
        would assert an extraction contract that was never satisfied. A lane that skipped them
        SILENTLY would report "6 routed" on a shelf where 12 reels are permanently stuck."""
        self.assertIn("CAPTURE", LANE.BLOCKED_BY)
        self.assertNotIn("CAPTURE", LANE.ROUTES_FROM)
        with _Stubbed([]):
            p = LANE.plan()
        # ⚠⚠ v2881 — THIS ASSERTED ok BEFORE REACHING THE SKIP THIS FILE ALREADY WROTE FOR IT.
        # `_NO_SHELF` exists three screens up, worded for exactly this case — but the plan REFUSES
        # on a shelf with no reels ("the router did not answer"), so `p["ok"]` was False and the
        # law died one line before its own escape hatch. Found by running the gate inside a
        # `safe_copy` sandbox, which is a truer CI runner than an emptied TV_HIST: the env var left
        # enough of his world behind to keep this green, the sandbox did not.
        # The two structural assertions above still run everywhere — CAPTURE must be in BLOCKED_BY
        # and out of ROUTES_FROM is a fact about the code, and it is what this law most protects.
        # [[feedback-blind-fixture-green-gate]] [[unknown-stays-unknown]]
        if not p["ok"]:
            self.assertTrue(str(p.get("why") or "").strip(),
                            "the lane refused to plan and gave no reason — a refusal with no why "
                            "is indistinguishable from a shelf with nothing to do")
            self.skipTest("%s (the lane refused: %s)" % (_NO_SHELF, str(p.get("why"))[:70]))
        if not (p["route"] or p["declined"]):
            self.skipTest(_NO_SHELF)
        self.assertFalse([x for x in p["route"] if x["from"] == "CAPTURE"],
                         "the lane is routing CAPTURE reels, which owe a capture change first")
        if _a_reel_at("CAPTURE"):
            self.assertTrue(p["declined"],
                            "reels sit at CAPTURE and the plan declined none of them — they are "
                            "being skipped silently, so the count reads as done")
            self.assertTrue(all(x.get("owesFirst") for x in p["declined"]),
                            "a declined reel does not say what it owes first")

    def test_the_lane_refuses_to_stamp_without_a_by(self):
        r = LANE.apply("")
        self.assertFalse(r["ok"])
        self.assertEqual(0, r["routed"])

    # ── ⚠⚠ THE STATION THIS LANE MUST NEVER WRITE ──────────────────────────────────────────
    def test_the_lane_never_writes_TOMBSTONE_and_never_deletes(self):
        """★ His instruction stands: the prune is not armed. This lane writes the DATA fact only;
        the BYTES fact belongs to the deleter, behind the lock.

        ⚠ THIS LAW PARSES; IT DOES NOT GREP. My first cut asserted the string "TOMBSTONE" was
        absent from the file and went RED on the lane's own docstring, which explains the weld it
        undoes and therefore names that station nine times, every one of them correct. Prose is not
        the subject — the `station` argument of every `stamp()` call is. Read comments before
        judging a MEASUREMENT; ignore them when judging CODE. [[measured-true-read-wrong]]
        """
        self.assertEqual("ROUTED", LANE.STATION)
        tree = ast.parse(LSRC)
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and ((isinstance(n.func, ast.Attribute) and n.func.attr == "stamp")
                      or (isinstance(n.func, ast.Name) and n.func.id == "stamp"))]
        self.assertTrue(calls,
                        "no stamp() call was found in the lane at all, so this law inspected "
                        "nothing — an instrument failure, not a pass")
        for c in calls:
            station = c.args[1] if len(c.args) > 1 else None
            for kw in c.keywords:
                if kw.arg == "station":
                    station = kw.value
            self.assertIsNotNone(station, "a stamp() call passes no station")
            self.assertTrue(isinstance(station, ast.Name) and station.id == "STATION",
                            "a stamp() call passes a station that is not the module's STATION "
                            "constant. The lane must write exactly one station, and a literal here "
                            "is how TOMBSTONE would eventually be written by the wrong hand")
        # ⚠ AND THE SAME DEFECT LIVED ONE LINE DOWN. Having fixed the station half to parse, I
        # left this half as a raw substring scan — and it went red on the docstring's quotation of
        # river_walk's own note, `reel_retention.apply_plan -> _tombstone`, which is the very
        # sentence explaining the weld being undone. Fixing one instance and leaving its twin is
        # the thing [[sweep-dont-ask]] exists to stop. Both halves parse now.
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                imported.add(n.module.split(".")[0])
        for banned in ("reel_retention", "shutil", "pathlib", "subprocess"):
            self.assertNotIn(banned, imported,
                             "the route lane IMPORTS %r. It closes reels out; it does not delete "
                             "anything, and deletion stays behind the arming lock" % banned)
        called = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Attribute):
                    called.add(n.func.attr)
                elif isinstance(n.func, ast.Name):
                    called.add(n.func.id)
        for banned in ("remove", "unlink", "rmtree", "rmdir", "apply_plan", "_tombstone"):
            self.assertNotIn(banned, called,
                             "the route lane CALLS %r — a deletion reaching into a lane whose "
                             "whole purpose is to close a reel out WITHOUT removing it" % banned)

    def test_the_prune_lock_is_still_FALSE(self):
        """⚠ Pinned here because this change is the one that makes a tombstone *conceivable*.

        ⚠⚠ IT LIVES IN `control_app`, NOT `reel_retention`. My first cut guessed the latter and
        the law went RED reading `None` — which is the only reason the guess was caught. Had it
        been written as `if not hasattr: skipTest`, it would have reported a clean bill for ever
        while watching an attribute that does not exist. [[feedback-suspect-the-instrument]]

        ⚠ AND MY SECOND GUESS WAS WRONG TOO, which is worth keeping. `reel_retention.py:575`
        carries a scar reading *"because I had checked _PRUNE_SAFE_TO_RUN and not
        retention_may_act()"*, so this law was written to assert BOTH were false. Measured:
        `retention_may_act()` returns **True, "nothing in flight"** — and correctly. It does not
        consult the flag at all. It is a LIVENESS check ("is anything mid-write that deleting would
        corrupt"), the flag is the ARMING lock, and `_prune_loop` ANDs them. Asserting a liveness
        check is False would have pinned "the machine is busy" as a safety property and gone red
        every time the box was idle.

        So the law is the STRUCTURE, not the runtime value: the flag is False, and the loop still
        refuses on it before reaching any deletion. [[feedback-verify-not-proxy]]
        """
        import control_app as _ca
        v = getattr(_ca, "_PRUNE_SAFE_TO_RUN", "<absent>")
        self.assertIs(False, v,
                      "control_app._PRUNE_SAFE_TO_RUN is %r. His instruction is explicit and "
                      "standing: do not arm the prune." % (v,))
        casrc = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = casrc.find("def _prune_loop():")
        self.assertGreater(i, 0, "the prune loop is gone — this law inspected nothing")
        j = casrc.find("\ndef ", i + 1)
        self.assertIn("if not _PRUNE_SAFE_TO_RUN:", casrc[i:j],
                      "the prune loop no longer refuses on the arming lock, so the flag being "
                      "False stops nothing")

    def test_the_lane_stamps_as_an_ACTOR(self):
        """The row must carry a causal claim the lane is entitled to make — and it is the only kind
        the overlay reads, so an observer row here would be invisible AND wrong."""
        self.assertIn("observed=False", LSRC,
                      "the lane does not stamp as an actor, so nothing it writes reaches the outlet")

    # ── ⚠ THE GUARD'S OWN LOOPHOLE, CLOSED WITH THE CHANGE ─────────────────────────────────
    def test_the_retention_guard_now_watches_route_too(self):
        """★ `assert_independent_of_retention`'s docstring warns the coupling could return "one
        function upstream". The overlay put a real station decision into `route()`, which the guard
        was not watching at all."""
        ok, findings = RR.assert_independent_of_retention()
        self.assertTrue(ok, "the retention guard is red: %r" % findings)
        rsrc = io.open(os.path.join(HERE, "reel_router.py"), encoding="utf-8").read()
        i = rsrc.find("def assert_independent_of_retention")
        j = rsrc.find("\ndef ", i + 1)
        self.assertIn("(route, RETENTION_FIELDS", rsrc[i:j],
                      "the guard does not watch `route`, which is now where a station gets its "
                      "final value — the exact place a keep-reason would next try to enter")

    # ── ⚠ FIFO IS INHERITED, NOT RE-SORTED ─────────────────────────────────────────────────
    def test_the_plan_is_FIFO_and_does_not_re_sort(self):
        """His word: *"first in first out FIFO.. that way its optimzed."* `route()` already orders
        oldest-capture-first; a second sort here would be free to drift from it."""
        self.assertNotIn(".sort(", LSRC, "the lane re-sorts instead of inheriting the router's FIFO")
        with _Stubbed([]):
            p = LANE.plan()
        if not p["route"]:
            self.skipTest(_NO_SHELF)
        ms = [x["capturedMs"] for x in p["route"] if x["capturedMs"] is not None]
        self.assertEqual(sorted(ms), ms, "the routable queue is not oldest-first")

    # ── ⚠⚠ THE JOIN TO THE HEART ───────────────────────────────────────────────────────────
    def test_the_doctor_row_is_REGISTERED(self):
        """A check defined and not in CHECKS runs never."""
        self.assertIn("river outlet", dict(D.CHECKS),
                      "the outlet reaches no screen, so a re-welded river would be silent")

    def test_the_doctor_row_reports_the_declined_reels_too(self):
        st, say = dict(D.CHECKS)["river outlet"]()
        self.assertIn(st, (D.OK, D.MISSING, D.UNKNOWN))
        self.assertTrue(say and len(say) > 30, "the row says almost nothing")
        if _a_reel_at("CAPTURE") and st != D.UNKNOWN:
            self.assertIn("CAPTURE", say,
                          "reels are permanently stuck at CAPTURE and the row does not mention "
                          "them, so a shelf with 12 stuck reels can read as done")

    def test_an_unreadable_outlet_grades_UNKNOWN_not_OK(self):
        real = RR.route
        RR.route = lambda hist=None: dict(real(hist), outletReadable=False,
                                          outletWhy="simulated")
        try:
            st, _ = dict(D.CHECKS)["river outlet"]()
        finally:
            RR.route = real
        self.assertEqual(D.UNKNOWN, st,
                         "an unreadable stamp store graded as a measured result — ROUTED 0 was "
                         "reported as a count when nobody could look")



RED_PROOF = [
    {
        'why': 'dropping the outlet verdict on the UNKNOWN path restores the confident ROUTED 0 this gate exists to separate from a real count. ⚠ THE SUCCESS PATH IS THE WRONG ANCHOR: a sandbox has no shelf, so the walk is UNKNOWN and the success line never executes — measured BLIND, it stayed GREEN through its own defeat. Tamper the path the runner actually takes.',
        'file': 'reel_router.py',
        'find': 'rep["outletReadable"] = _r is not None',
        'replace': 'rep["outletReadable"] = None',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
