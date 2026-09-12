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
        # ⚠⚠ v2958 — assertIs(..., False), NOT assertFalse. THIS IS WHY THE GATE WAS BLIND.
        # `outletReadable` exists to separate False (the store refused — a MEASURED fact) from
        # None (nobody looked). `assertFalse(None)` PASSES, so the one law guarding the unreadable
        # case accepted exactly the value the field was invented to distinguish, and a tamper that
        # replaced the verdict with None sailed straight through it. Demonstrated: assertFalse(None)
        # passes, assertIs(None, False) fails. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
        self.assertIs(rep.get("outletReadable"), False,
                      "the outlet verdict is %r — the router either claims the outlet was readable "
                      "when the store refused, or answers None, which is 'nobody looked' wearing "
                      "'unreadable' clothes" % (rep.get("outletReadable"),))
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
        #: ⚠⚠ v3015 — THIS LAW PINNED A VALUE AND THE VALUE MOVED WITHOUT IT. v2984 armed the
        #: FRAME prune deliberately ("the prune is armed, and the argument against it was about
        #: the other deleter") and did not update this assertion, so the law has been RED at
        #: origin/main ever since — and nothing caught it, because the pre-push runs only
        #: test_agent and test_control, never the full roster. It is almost certainly one of the
        #: four red CI shards measured at e5cc2d26.
        #:
        #: THERE ARE TWO DELETERS AND THIS LAW CONFLATED THEM:
        #:   · `_prune_loop` / `_prune_once` drops DUPLICATE FRAMES inside reels. `_PRUNE_SAFE_TO_RUN`
        #:     gates that one, and it is now True by his decision.
        #:   · `reel_retention.apply_plan` removes WHOLE REELS and is the only writer of a
        #:     TOMBSTONE row. It refuses without an explicit `yes=True`, which is why TOMBSTONE has
        #:     been 0 forever: no automated caller ever releases a reel.
        #:
        #: So the law now pins the STRUCTURE that is actually load-bearing — both deleters still
        #: refuse by default — instead of a boolean that is his to set. Pinning the number would
        #: just go stale again the next time he rules. [[regression-guard]] [[label-outlived-referent]]
        #:
        #: ⚠ PARSED, NEVER GREPPED. The old cut used casrc.find() between two "def " markers, which
        #: silently reads the WRONG function the moment a nested def appears. [[source-reading-guard]]
        import ast as _ast
        import control_app as _ca
        v = getattr(_ca, "_PRUNE_SAFE_TO_RUN", "<absent>")
        self.assertIsInstance(
            v, bool,
            "control_app._PRUNE_SAFE_TO_RUN is %r — the arming lock must be a MEASURED boolean. "
            "Absent or None is 'nobody decided' wearing a decision's clothes." % (v,))

        casrc = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        loop = None
        for _fn in _ast.walk(_ast.parse(casrc)):
            if isinstance(_fn, _ast.FunctionDef) and _fn.name == "_prune_loop":
                loop = _ast.get_source_segment(casrc, _fn) or ""
        self.assertIsNotNone(loop, "_prune_loop is gone — this law inspected nothing")
        self.assertIn("if not _PRUNE_SAFE_TO_RUN:", loop,
                      "the frame prune no longer refuses on its arming lock, so the flag stops "
                      "nothing whatever it is set to")

        #: THE REEL DELETER — the one that writes a tombstone — must keep refusing by default.
        rsrc = io.open(os.path.join(HERE, "reel_retention.py"), encoding="utf-8").read()
        ap = None
        for _fn in _ast.walk(_ast.parse(rsrc)):
            if isinstance(_fn, _ast.FunctionDef) and _fn.name == "apply_plan":
                ap = _fn
        self.assertIsNotNone(ap, "reel_retention.apply_plan is gone — nothing deletes reels, or "
                                 "something else does and this law is no longer watching it")
        _defaults = {a.arg: d for a, d in zip(ap.args.args[-len(ap.args.defaults):],
                                              ap.args.defaults)} if ap.args.defaults else {}
        self.assertIn("yes", _defaults,
                      "apply_plan no longer takes a defaulted `yes` — the reel deleter's refusal "
                      "is the only thing standing between a plan and an irreversible rmtree")
        self.assertIs(getattr(_defaults["yes"], "value", "<not-a-constant>"), False,
                      "apply_plan's `yes` no longer defaults to False, so a caller that forgets "
                      "the flag now DELETES REELS instead of being refused")

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



    def test_the_UNREADABLE_EVIDENCE_path_still_answers_the_outlet(self):
        """⚠⚠ THE PATH CI ACTUALLY TAKES, AND NO LAW REACHED IT — which is why proof [1] measured
        BLIND while eleven laws ran and stayed green.

        `route()` returns EARLY when `_evidence()` cannot be read (`ev is None`): "UNKNOWN, not an
        empty shelf". Every other law here supplies a readable store through `_Stubbed`, so they all
        fall through to the MAIN return and the early one was exercised by nothing. A runner has no
        reels, so this early path is the one the whole repo takes on CI — the single place where a
        confident ROUTED 0 would do the most damage, and the least guarded.

        ⚠ assertIsInstance(bool), not assertTrue/assertFalse: the verdict must be a MEASURED
        boolean either way. None here is "nobody looked" wearing a verdict's clothes, and
        `assertFalse(None)` would wave it through — the exact hole that made this gate blind.
        [[unknown-stays-unknown]]"""
        real = RR._evidence
        try:
            RR._evidence = lambda hist=None: (None, "simulated unreadable evidence")
            rep = RR.route()
        finally:
            RR._evidence = real
        self.assertIn("UNKNOWN", str(rep.get("why") or ""),
                      "the early return did not say the shelf is UNKNOWN rather than empty")
        self.assertIsInstance(rep.get("outletReadable"), bool,
                              "the outlet verdict on the unreadable-evidence path is %r — a walk "
                              "that could not read its evidence still owes a MEASURED yes or no "
                              "about the outlet, never None"
                              % (rep.get("outletReadable"),))
        # ⚠ A `why` IS OWED ONLY WHEN THE ANSWER IS NO. My first cut asserted outletWhy was
        # always non-empty here and it FAILED against correct code: on this run the outlet WAS
        # readable, so there is nothing to explain, and demanding a sentence would have forced a
        # reason for a non-event. The law is "an unreadable outlet must say why", not "every walk
        # must narrate". [[zero-needs-a-denominator]]
        if rep.get("outletReadable") is False:
            self.assertTrue(str(rep.get("outletWhy") or ""),
                            "the outlet could not be read on the path CI takes and nothing says "
                            "why, so its verdict cannot be acted on")

    def test_the_tombstone_pair_with_NOTHING_gradable_is_UNMEASURED_not_zero(self):
        """⚠⚠ THE ZERO THAT SPOKE FOR REELS IT NEVER SAW. v3011's pair skipped every routed reel
        whose extract evidence was gone and published the survivors' count as the verdict.
        MEASURED on his live tree: 20 routed, 16 absent, FOUR graded — reported as "0, agree".

        And the absence is not neutral. Evidence vanishes when the deleter runs, so a reel
        tombstoned ahead of extraction becomes ungradable exactly when the violation completes;
        the pair was structurally green through the terminal state of the pipeline it guards.

        Both directions are pinned here, because "return None" alone would be a different lie:
        nothing gradable must read UNMEASURED, and a reel that IS gradable and clean must still
        read 0. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]"""
        import corroborate as C
        real_r, real_e = RR._routed_by_a_lane, RR._evidence

        def _left_with(routed, ev):
            try:
                RR._routed_by_a_lane = lambda *a, **k: (routed, "")
                RR._evidence = lambda hist=None: (ev, "")
                return C._inv_a_tombstone_is_never_ahead_of_extraction()[4]()
            finally:
                RR._routed_by_a_lane, RR._evidence = real_r, real_e

        nothing = _left_with(["reel_a", "reel_b"], {})
        self.assertIsNone(
            nothing,
            "two reels were routed and NEITHER had surviving evidence, so nothing could be "
            "graded — the pair answered %r instead of UNMEASURED. A zero here claims two reels "
            "were checked and cleared when none was looked at." % (nothing,))

        clean = _left_with(["reel_a"], {"reel_a": {"sealed": True, "worthReading": True}})
        self.assertEqual(
            clean, 0,
            "a routed reel WITH surviving evidence, sealed and worth reading, is a genuine "
            "measured zero — the pair answered %r, so the UNMEASURED guard has swallowed real "
            "coverage as well." % (clean,))

        caught = _left_with(["reel_a"], {"reel_a": {"sealed": False, "worthReading": True}})
        self.assertEqual(
            caught, 1,
            "a worth-reading reel closed out UNSEALED is the violation this pair exists for; "
            "it answered %r." % (caught,))

RED_PROOF = [
    {
        'why': 'v2958 — THE PATH THE STUBBED LAWS ACTUALLY RUN. The existing proof below tampers '
               'the EARLY return (no shelf), but every law here supplies a store through _Stubbed '
               'and falls through to the MAIN return, so that tamper never executed in the laws '
               'that ran — 11 of them stayed green through it and the drill reported BLIND. This '
               'one drops the verdict on the main path, where the laws live.',
        'file': 'reel_router.py',
        'find': 'rep["outletReadable"] = routed is not None',
        'replace': 'rep["outletReadable"] = None',
        'matches': 1,
    },
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
