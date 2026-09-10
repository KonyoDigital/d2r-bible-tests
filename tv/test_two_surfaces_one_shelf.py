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
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
