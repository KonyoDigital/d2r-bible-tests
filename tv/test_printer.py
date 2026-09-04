# -*- coding: utf-8 -*-
"""THE PRINTER — one reel, in at one door, down one stream, out the other end.

His words: *"3d 4d printer connected to the heart of the console and the reels like we said going
in unified and getting processed and routed out clean on the other end of the stream"*.

⚠⚠ THE PRINTER OWNS NO MEASUREMENT, AND THAT IS THE LAW THIS FILE HOLDS. Seven modules already
answer one question each, every one measured on his own forty reels. If this file re-derived any of
them, a badge and a diagram would eventually disagree on screen about the same reel — the exact
failure [[copy-drift]] §1 names. So every station QUOTES its owner, and these pin that it stays
that way: move an owner's answer and the printer's row must move with it.

⚠⚠ AND THE FAR END IS UNDECIDED, DELIBERATELY. A15's last clause says *clean is a state the
pipeline must be able to ASSERT per reel* and never says WHICH DOOR decides. On his shelf the two
candidates disagree — 12 of 40 by the REEL door, 0 of 15 asked by the FRAME contract — and
conjoining them is exactly the collapse v2312 attempted and WITHDREW (v2314: they answer different
questions at different granularities). A printer that picked one would be answering his question
with my preference and calling it a measurement. It reports BOTH and chooses neither.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import printer as P   # noqa: E402


class EveryStationQuotesItsOwner(unittest.TestCase):

    def test_every_reel_gets_every_station(self):
        """A station missing from a row would read as a reel that did not need it."""
        r = P.stream()
        self.assertTrue(r["ok"], r["why"])
        for row in r["rows"]:
            for st in P.STATIONS:
                self.assertIn(st, row["stations"],
                              "%s has no %r station at all" % (row["reel"], st))
                self.assertTrue(str(row["stations"][st].get("say") or "").strip(),
                                "%s's %r station said nothing" % (row["reel"], st))

    def test_the_IN_station_moves_when_one_start_point_moves(self):
        """⚠ The whole law: the printer must QUOTE, never re-derive. Change the owner's answer and
        the printer's row has to change with it — otherwise it is keeping its own copy."""
        import one_start_point as OSP
        real = OSP.start_points
        try:
            OSP.start_points = lambda *a, **k: {
                "ok": True, "state": "ONE_DOOR", "walked": 1, "counts": {"sentinel": 1},
                "rows": [{"reel": "reel_s_1", "door": "sentinel", "why": "planted"}], "why": "x"}
            r = P.stream("reel_s_1")
            says = [row["stations"]["in"]["say"] for row in r["rows"]]
            self.assertIn("sentinel", says,
                          "the printer did not follow one_start_point, so it keeps its own copy "
                          "of which door a reel entered by: %s" % says)
        finally:
            OSP.start_points = real

    def test_the_ROUTE_station_moves_when_per_reel_routes_moves(self):
        import per_reel_routes as PRR
        real = PRR.routes
        try:
            PRR.routes = lambda *a, **k: {
                "ok": True, "state": "EARNED", "byDecider": {}, "contentRoutes": {},
                "policyRoutes": {}, "distinctContentRoutes": 0, "minDistinct": 2, "walked": 1,
                "rows": [{"reel": "reel_s_1", "tag": "t", "stage": "s",
                          "decidedBy": "sentinel", "why": "planted", "route": "t@s"}], "why": "x"}
            says = [row["stations"]["route"]["say"] for row in P.stream("reel_s_1")["rows"]]
            self.assertIn("sentinel", says,
                          "the printer did not follow per_reel_routes: %s" % says)
        finally:
            PRR.routes = real

    def test_the_OUT_station_reports_BOTH_doors_and_chooses_NEITHER(self):
        """⚠⚠ Choosing is a decision about what *finished* means. It is his, and it gates the prune."""
        r = P.stream()
        for row in r["rows"]:
            out = row["stations"]["out"]
            self.assertEqual(
                out["say"], "UNDECIDED",
                "%s came out of the printer with a CLEAN verdict. A15 never says which door "
                "decides, and conjoining the two is the collapse v2312 withdrew." % row["reel"])
            self.assertIn("reelDoor", out, "the reel door's answer is not even reported")
            self.assertIn("frameDoor", out, "the frame door's answer is not even reported")

    def test_a_STATIONS_shape_does_not_depend_on_its_verdict_either(self):
        """⚠⚠ REG-547 — THE SEVENTH INSTANCE OF ONE CLASS IN A DAY, AND I WROTE IT INSIDE THE FIX
        FOR THE SIXTH. `_station` returned early when the owner had nothing, so the station DROPPED
        its extra keys — `decider`, `route` — on exactly the path where it has nothing to report.
        Measured: funnel carried `['decider','say','why']` normally and `['say','why']` when
        reel_river reported nothing.

        ⚠ The reading-level shape law could not see this: it compares the TOP-LEVEL key sets, and
        this one is nested two levels down. So the law is asked here, per station, at every reel.
        """
        import reel_river as RR
        real = RR.river
        try:
            RR.river = lambda *a, **k: {"ok": True, "rows": [], "gaps": [], "why": "x", "clean": {}}
            silent = P.stream()["rows"]
        finally:
            RR.river = real
        normal = P.stream()["rows"]
        self.assertTrue(silent and normal, "no rows to compare")
        for st in P.STATIONS:
            a = set(silent[0]["stations"][st])
            b = set(normal[0]["stations"][st])
            self.assertEqual(
                sorted(b - a), [],
                "the %r station drops %s when its owner has nothing to report. A shape that "
                "changes with the verdict is not a shape — at the STATION level exactly as at the "
                "reading level." % (st, sorted(b - a)))

    def test_an_owner_that_ANSWERED_WITH_NOTHING_is_UNKNOWN_not_the_word_None(self):
        """⚠⚠ REG-546, from the cold look at v2544, and it is a different case from the one below.
        There the owner did not report the reel at all. HERE the owner reported it and carried no
        value — measured on a door row missing its `door` key, the station printed the literal
        string **"None"**, `counts["in"]` gained a `"None"` bucket that would render on the heart,
        and the row **escaped the unknown tally** because `str(None) != "UNKNOWN"`. So the printer
        said FLOWING over a station that had said nothing.

        ⚠ This guard was MISSING when the fix shipped: the sabotage that restores the defect went
        GREEN, which is how I know the fix was untested rather than well-tested.
        """
        import one_start_point as OSP
        real = OSP.start_points
        try:
            OSP.start_points = lambda *a, **k: {
                "ok": True, "state": "ONE_DOOR", "counts": {}, "walked": 1,
                "rows": [{"reel": "reel_s_1", "why": "this row has no door key"}], "why": "x"}
            r = P.stream("reel_s_1")
            st = r["rows"][0]["stations"]["in"]
            self.assertEqual(
                st["say"], "UNKNOWN",
                "an owner answered with no value and the station said %r — that renders as a "
                "literal 'None' on the heart and is not counted as unknown" % (st["say"],))
            self.assertIn("carried no", st["why"],
                          "the reason does not say WHICH owner had nothing: %r" % st["why"])
            self.assertGreater(r["unknownStations"], 0,
                               "the row escaped the unknown tally, so the printer would report "
                               "FLOWING over a station that said nothing")
            self.assertNotIn("None", r["counts"]["in"],
                             "a 'None' bucket reached the counts: %s" % r["counts"]["in"])
        finally:
            OSP.start_points = real

    def test_a_reel_missing_from_an_owner_is_UNKNOWN_not_dropped(self):
        """⚠ A reel silently absent from a row would shrink the shelf without saying so."""
        import per_reel_routes as PRR
        real = PRR.routes
        try:
            PRR.routes = lambda *a, **k: {"ok": True, "state": "EARNED", "rows": [],
                                          "byDecider": {}, "contentRoutes": {}, "policyRoutes": {},
                                          "distinctContentRoutes": 0, "walked": 0, "why": "x"}
            r = P.stream()
            # ⚠⚠ A LINE THAT LOOKED LIKE AN ASSERTION AND COULD NOT FAIL SHIPPED HERE, caught by
            # the review-after-ship pass on my own v2544 bytes. It read
            #     self.assertEqual(...) if False else None
            # — the `if False` makes the whole expression a no-op, so it never ran while reading
            # exactly like a check. That is the same shape as the tautology REG in test_dom_probe:
            # a guard satisfied by its own text. The real question it meant to ask is below, and it
            # RUNS: an owner reporting nothing must not shrink the shelf.
            self.assertEqual(
                r["walked"], len(P._by_reel(__import__("reel_river").river())),
                "an owner reported no reels and the printer's shelf shrank with it — the union of "
                "the owners is the shelf, so a reel absent from ONE of them must still appear")
            says = set(row["stations"]["route"]["say"] for row in r["rows"])
            self.assertEqual(says, {"UNKNOWN"},
                             "an owner reported nothing and the printer invented a route: %s" % says)
            self.assertEqual(r["state"], "PARTIAL",
                             "every reel has an unanswered station and the printer still says "
                             "FLOWING: %s" % r["why"])
        finally:
            PRR.routes = real

    def test_NO_owner_answering_is_UNKNOWN_not_an_empty_shelf(self):
        import one_start_point as OSP
        import reel_river as RR
        r1, r2 = OSP.start_points, RR.river
        try:
            OSP.start_points = lambda *a, **k: {"ok": False, "rows": [], "state": "UNKNOWN",
                                                "counts": {}, "why": "x"}
            RR.river = lambda *a, **k: {"ok": False, "rows": [], "gaps": [], "why": "x"}
            r = P.stream()
            self.assertEqual(r["state"], "UNKNOWN", r["why"])
            self.assertFalse(r["ok"], "nothing to read answered ok=True")
        finally:
            OSP.start_points, RR.river = r1, r2

    def test_the_EXTRACT_station_says_it_is_a_SHELF_fact_not_a_per_reel_one(self):
        """⚠ printer_reach measured ONE answer about the whole corpus. Printing it on each row
        without saying so would invent forty per-reel measurements nobody took."""
        for row in P.stream()["rows"][:3]:
            self.assertIn("SHELF-WIDE", row["stations"]["extract"]["why"],
                          "a shelf-wide state is printed per reel with nothing saying so")

    def test_it_refuses_nothing_and_deletes_nothing(self):
        """⚠ The prune stays OFF. This routes a reel ON PAPER and says where it came out."""
        import io
        src = io.open(os.path.join(HERE, "printer.py"), encoding="utf-8").read()
        for banned in ("os.remove", "os.unlink", "shutil.rmtree", "os.rmdir", '"w"', "'w'"):
            self.assertNotIn(banned, src,
                             "the printer contains %r — it reports, it does not act" % banned)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
