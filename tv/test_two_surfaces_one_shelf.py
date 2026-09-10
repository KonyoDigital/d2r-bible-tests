"""THE STRIP AND THE SHELF DRAW ONE SHELF, SO THEY MAY NOT PRINT TWO NUMBERS.

⚠⚠ WHY THIS LAW EXISTS, MEASURED ON HIS CONSOLE 2026-09-10 (#58).
`_shelf_visible()` has subtracted the 8 fixture reels from /api/reel_story since v2877, under his
ruling: *"no need to even mention those 8 anywhere visually on the console."* The RIVER STRIP — the
other surface drawn from the same shelf, two panels up the same page — went on counting all 24:

    strip header    the river · 24 reel(s) on the shelf
    the shelf below 16 rows
    INTAKE 6 · PRINTER 2 · CAPTURE 12 · TOMBSTONE 4     (2 · 1 · 4 · 1 of them fixtures)

One shelf, two answers, and nothing on screen saying which was his. That is [[copy-drift]] wearing
the costume this repo keeps re-tailoring: a rule applied at ONE of the places that draws the thing.

⚠ SO THE LAW IS NOT "the strip subtracts 8". It is that the subtraction happens ON THE REPORT, once,
above every figure derived from it — because `shelf`, each lane's `count`, each `byStation` cell and
`reconciles` are all derived from `rep`, and a fix that patched the OUTPUT would be four separate
chances to miss one. Each assertion below names a figure that must move by itself.

⚠ AND THE ROSTER MUST NOT BE FILTERED. roster() decides a reel has CLOSED OUT by its ABSENCE from
the walk, so handing it the filtered report would read all 8 hidden reels as finished — hidden from
the shelf and then announced in TOMBSTONE and in `closed`. Hidden means UNSEEN, never FINISHED.

⚠ NO FOOTAGE, BY CONSTRUCTION. Every reel below is synthetic and roster() is stubbed, so this law
measures the same thing on his Mac and on a CI runner that has no reels at all — the failure mode
[[feedback-blind-fixture-green-gate]] is named for. [[zero-needs-a-denominator]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import river_lanes as RL   # noqa: E402


def _rep(hidden_ids=()):
    """A synthetic router report: 6 reels over four lanes, 2 of them 'fixtures'."""
    reels = [
        {"reel": "reel_keep_a", "station": "STATION"},
        {"reel": "reel_hide_a", "station": "STATION"},
        {"reel": "reel_keep_b", "station": "PRINTER"},
        {"reel": "reel_keep_c", "station": "CAPTURE"},
        {"reel": "reel_hide_b", "station": "CAPTURE"},
        {"reel": "reel_keep_d", "station": "ROUTED"},
    ]
    return {"ok": True, "reels": reels, "shelf": len(reels), "unknown": 0, "why": ""}


class _StubRoster(object):
    """Captures the report roster() was handed, and answers with a readable closure ledger."""

    def __init__(self):
        self.seen = []

    def __call__(self, hist=None, path=None, rep=None):
        self.seen.append(rep)
        return {"ok": True, "rows": [], "closed": 99, "closedReadable": True, "closedWhy": ""}


class TwoSurfacesOneShelf(unittest.TestCase):

    def setUp(self):
        import reel_router
        self._real = reel_router.roster
        self.stub = _StubRoster()
        reel_router.roster = self.stub

    def tearDown(self):
        import reel_router
        reel_router.roster = self._real

    # ── every figure moves, and each one is named separately ─────────────────────────────────
    def test_the_shelf_total_drops_by_exactly_what_was_hidden(self):
        base = RL.lanes(rep=_rep())
        cut = RL.lanes(rep=_rep(), hide={"reel_hide_a", "reel_hide_b"})
        self.assertTrue(base.get("ok") and cut.get("ok"), "the lanes refused to draw at all")
        self.assertEqual(base["shelf"], 6, "the fixture stopped describing the report it is built from")
        self.assertEqual(cut["shelf"], 4,
                         "the strip's own total still counts reels the shelf hides — this is the "
                         "24-over-16 defect exactly")
        self.assertEqual(cut.get("hidden"), 2, "the payload does not say how many it subtracted")

    def test_the_lane_counts_move_with_it(self):
        cut = RL.lanes(rep=_rep(), hide={"reel_hide_a", "reel_hide_b"})
        got = dict((l["name"], l["count"]) for l in cut["lanes"])
        self.assertEqual(got.get("INTAKE"), 1, "INTAKE still counts a hidden reel")
        self.assertEqual(got.get("CAPTURE"), 1, "CAPTURE still counts a hidden reel")
        self.assertEqual(got.get("PRINTER"), 1, "PRINTER lost a reel it should have kept")
        self.assertEqual(got.get("TOMBSTONE"), 1, "TOMBSTONE lost a reel it should have kept")

    def test_the_per_station_cells_move_too(self):
        """The lane count and its byStation breakdown are two figures, not one."""
        cut = RL.lanes(rep=_rep(), hide={"reel_hide_a", "reel_hide_b"})
        by = {}
        for l in cut["lanes"]:
            by.update(l.get("byStation") or {})
        self.assertEqual(by.get("STATION"), 1,
                         "the per-station cell still counts a hidden reel while the lane total "
                         "above it does not — one surface, two numbers, again")
        self.assertEqual(by.get("CAPTURE"), 1, "the CAPTURE cell still counts a hidden reel")

    def test_the_river_still_reconciles_after_the_cut(self):
        """A filter that leaves the lanes not adding up to the shelf has broken the river."""
        cut = RL.lanes(rep=_rep(), hide={"reel_hide_a", "reel_hide_b"})
        total = sum(l["count"] for l in cut["lanes"])
        self.assertEqual(total + cut["unknown"], cut["shelf"],
                         "the lanes and the shelf disagree after hiding: %s + %s != %s"
                         % (total, cut["unknown"], cut["shelf"]))
        self.assertTrue(cut["reconciles"], "reconciles went false on an intact river: %s"
                        % cut.get("why"))

    # ── hidden is not finished ───────────────────────────────────────────────────────────────
    def test_the_closure_roster_is_handed_every_reel(self):
        """roster() reads absence as closure, so a filtered report would resurrect the hidden 8
        as CLOSED OUT — the one place the ruling most obviously forbids."""
        RL.lanes(rep=_rep(), hide={"reel_hide_a", "reel_hide_b"})
        self.assertTrue(self.stub.seen, "roster() was never called, so this law measured nothing")
        got = self.stub.seen[-1]
        ids = {(r or {}).get("reel") for r in ((got or {}).get("reels") or [])}
        self.assertIn("reel_hide_a", ids,
                      "the closure roster was handed the FILTERED report — every hidden reel now "
                      "reads as closed out, and the console would hide them from the shelf and "
                      "then announce them in TOMBSTONE")
        self.assertEqual(len(ids), 6, "the roster saw %d reels, not the whole shelf" % len(ids))

    def test_hiding_does_not_move_the_closed_count(self):
        base = RL.lanes(rep=_rep())
        cut = RL.lanes(rep=_rep(), hide={"reel_hide_a", "reel_hide_b"})
        self.assertEqual(base.get("closed"), cut.get("closed"),
                         "hiding a reel that is ON DISK changed how many reels have CLOSED OUT")

    # ── an unknown filter hides nothing, and says nothing false ──────────────────────────────
    def test_no_filter_means_no_subtraction(self):
        """`hide=None` is 'this console could not establish the set'. It must leave the river
        whole rather than draw a filtered-looking river it never filtered."""
        for empty in (None, set(), frozenset()):
            r = RL.lanes(rep=_rep(), hide=empty)
            self.assertEqual(r["shelf"], 6, "hide=%r subtracted something" % (empty,))
            self.assertEqual(r.get("hidden"), 0,
                             "hide=%r reported a subtraction it did not make" % (empty,))

    # ── the joint: the endpoint must actually pass the set ───────────────────────────────────
    def test_the_river_endpoint_hands_the_hidden_set_to_the_lanes(self):
        """⚠ PARSED, NOT GREPPED. A filter built on both ends and never joined is this repo's most
        repeated defect, and it is invisible to any check that reads prose. [[plumbing-with-no-tap]]
        [[source-reading-guard]]"""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        joined = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not (isinstance(f, ast.Attribute) and f.attr == "lanes"):
                continue
            if any(k.arg == "hide" for k in (node.keywords or [])):
                joined.append(getattr(node, "lineno", 0))
        self.assertTrue(joined,
                        "no call to .lanes(hide=...) anywhere in control_app.py — the hidden set "
                        "is computed and never handed over, so the strip draws every fixture")

    def test_the_hidden_set_is_decided_once_and_refuses_when_it_cannot(self):
        """`shelf_hidden_reels()` must exist, must key on SHELF_HIDDEN_TAGS, and must return None —
        never an empty set — when the plan cannot be read. An empty set is a CLAIM."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "shelf_hidden_reels":
                fn = node
        self.assertIsNotNone(fn, "shelf_hidden_reels() is gone — the two surfaces have no shared "
                                 "authority and are free to drift apart again")
        body = ast.dump(fn)
        self.assertIn("SHELF_HIDDEN_TAGS", body,
                      "shelf_hidden_reels() no longer keys on SHELF_HIDDEN_TAGS, so the strip and "
                      "the shelf can now hide DIFFERENT reels")
        returns_none = any(isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple)
                           and isinstance(n.value.elts[0], ast.Constant)
                           and n.value.elts[0].value is None
                           for n in ast.walk(fn) if isinstance(n, ast.Return)
                           and isinstance(n.value, ast.Tuple) and n.value.elts)
        self.assertTrue(returns_none,
                        "shelf_hidden_reels() has no path returning None — an unreadable plan now "
                        "hands back an empty set, which CLAIMS nothing is hidden")


class ThePrinterSpineCountsWhatTheShelfShows(unittest.TestCase):
    """THE THIRD SURFACE. Same shelf, same ruling, found by sweeping for siblings of REG-886.

    ⚠⚠ MEASURED on his shelf 2026-09-10: the printer spine is drawn from `stream()["counts"]`, an
    aggregate over every reel ON DISK, while `_shelf_visible()` had already cut the story's rows to
    16. ALL SEVEN STATIONS read 24 — in 24 · funnel 24 · template 24 · route 24 · extract 24 ·
    out 24 · tombstone "ON DISK 24" — directly beneath the handler's own sentence *"16 of 16
    reel(s) carry the printer's verdicts"*. A denominator and its own label, disagreeing, one line
    apart. [[zero-needs-a-denominator]] [[label-outlived-referent]]
    """

    ROWS = [
        {"reel": "reel_keep_a", "stations": {"in": {"say": "recorder"}, "out": {"say": "UNDECIDED"}}},
        {"reel": "reel_keep_b", "stations": {"in": {"say": "recorder"}, "out": {"say": "UNDECIDED"}}},
        {"reel": "reel_hide_a", "stations": {"in": {"say": "repair"}, "out": {"say": "UNDECIDED"}}},
    ]

    def test_the_counting_rule_has_a_name_the_endpoint_can_call(self):
        """The rule must live in the printer, not be re-tallied by whoever needs a subset."""
        import printer as PR
        self.assertTrue(callable(getattr(PR, "counts_for", None)),
                        "printer.counts_for() is gone — a caller wanting the visible subset must "
                        "now re-implement what a station 'said', which is a second opinion owned "
                        "by the wrong module")

    def test_a_subset_sums_to_the_subset(self):
        import printer as PR
        got = PR.counts_for(self.ROWS[:2], ["in", "out"])
        self.assertEqual(sum(got["in"].values()), 2,
                         "the station column does not sum to the rows it was given")
        self.assertEqual(got["in"], {"recorder": 2},
                         "the hidden reel's verdict is still in the tally: %s" % got["in"])
        self.assertEqual(PR.counts_for(self.ROWS, ["in"])["in"], {"recorder": 2, "repair": 1},
                         "counting every row no longer reproduces the whole-shelf tally")

    def test_a_missing_station_buckets_rather_than_vanishing(self):
        """A dropped row would stop the columns summing to the number of rows — the one property
        every reader of this spine relies on."""
        import printer as PR
        got = PR.counts_for(self.ROWS, ["in", "nosuchstation"])
        self.assertEqual(sum(got["nosuchstation"].values()), len(self.ROWS),
                         "rows vanished from a station they do not carry, so the columns no "
                         "longer sum to the shelf: %s" % got["nosuchstation"])

    def test_stream_itself_counts_with_it(self):
        """One rule, two callers — not one rule and a copy. [[copy-drift]]"""
        src = io.open(os.path.join(HERE, "printer.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        inside_stream = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "stream":
                for n in ast.walk(node):
                    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                            and n.func.id == "counts_for"):
                        inside_stream.append(n)
        self.assertTrue(inside_stream,
                        "stream() no longer calls counts_for() — the walk has gone back to its own "
                        "inline tally, so the spine and the subset are counted by two rules that "
                        "are free to drift apart")

    def test_the_endpoint_counts_only_the_reels_it_is_showing(self):
        """⚠ PARSED, NOT GREPPED. [[source-reading-guard]]"""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        joined = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "counts_for"]
        self.assertTrue(joined,
                        "control_app.py never calls counts_for — printerCounts is back to the "
                        "whole-disk aggregate and the spine counts reels the shelf hides")



RED_PROOF = [
    {
        "why": "removing the report-level filter restores the strip that printed 24 over a shelf "
               "drawing 16",
        "file": "river_lanes.py",
        "find": '            out["hidden"] = len(_drop)',
        "replace": '            out["hidden"] = 0',
        "matches": 1,
    },
    {
        "why": "handing roster() the FILTERED report makes every hidden reel read as closed out — "
               "hidden from the shelf, then announced in TOMBSTONE",
        "file": "river_lanes.py",
        "find": "_ro = _rr2.roster(rep=rep_all)",
        "replace": "_ro = _rr2.roster(rep=rep)",
        "matches": 1,
    },
    {
        "why": "unjoining the endpoint from the filter: the hidden set is still computed, and the "
               "strip goes back to drawing every fixture",
        "file": "control_app.py",
        "find": "_lr = _RL.lanes(hide=_hide)",
        "replace": "_lr = _RL.lanes()",
        "matches": 1,
    },
    {
        "why": "putting the printer spine back on the whole-disk aggregate restores the seven "
               "stations reading 24 beside a shelf of 16",
        "file": "control_app.py",
        "find": "_PR.counts_for(_vis_rows, _p.get(\"stations\"))",
        "replace": "(_p.get(\"counts\") or {})",
        "matches": 1,
    },
    {
        "why": "returning stream() to its own inline tally means the spine and the visible subset "
               "are counted by two rules",
        "file": "printer.py",
        "find": '"rows": rows, "counts": counts_for(rows),',
        "replace": '"rows": rows, "counts": {},',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
