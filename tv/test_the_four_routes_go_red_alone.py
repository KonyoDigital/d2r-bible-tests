# -*- coding: utf-8 -*-
"""v#### — FOUR ROUTES SHARED TWO BUCKETS, AND THE FIELD THAT TOLD THEM APART REACHED NOBODY.

MEASURED 2026-09-08, before any of this:

  · `reel_templates.py:305` built `subTemplate` — "chronicle · uniques", "stash · gems" — and a
    grep for the name across every .py, .html and .js in the tree returned its own definition and
    its own test. NO OTHER READER ANYWHERE. `printer.py` built the TEMPLATE station off `zone`, so
    CHRONICLE stayed ONE bucket for every consumer downstream. The distinction existed, was
    correct, and was thrown away one line after it was made. [[the-unjoined-end]]

  · console_doctor carried fifty rows. The ones touching this territory — `extraction lanes`,
    `vault stores`, `vault proposal`, `read names lane`, `names banked` — are none of them
    per-route. chronicle-sets and chronicle-uniques were indistinguishable to every supervisor in
    the system; inventory and stash shared one "vault" bucket. If exactly ONE route died,
    everything stayed green. That is the defect this file exists for.

⚠⚠ WHY THIS FILE HAS TO SUPPLY ITS OWN INPUT — HIS SHELF CANNOT EXERCISE THE SPLIT.
    reels on the shelf                       49
    in the CHRONICLE zone                     1
    carrying a chronicle ledger               0   (0 of 40 rows; 0 of 1,065 deep journal rows)
So `chronicle · sets` and `chronicle · uniques` are taken by ZERO reels on his machine, and a row
that only ever read his live store would be green — or, honestly, UNKNOWN — for ever and prove
nothing either way. Same shape as `test_chronicle_ledger_refines_the_template`, which says so in
its own docstring: real data, correct code, and no evidence. [[gate-blind-to-unexercised-input]]

WHAT IS PINNED HERE — the LAW, never a count off his shelf:
  1. all four routes resolve when the input exists, and the two chronicle routes are TWO rows
  2. each route can go BROKEN **alone**, leaving the other three untouched
  3. the label (`subTemplate`, the half that reaches a screen) and the census (the half a
     supervisor joins to) must AGREE — the v2709 regression returning is a red route
  4. a route with no data reads UNKNOWN, never OK, at the census AND at the doctor
  5. the census keeps all four keys on the path where nothing was established (REG-546)
  6. the printer's TEMPLATE station actually CARRIES subTemplate and route — the join itself
  7. console_doctor has one row per DECLARED route, so a fifth cannot arrive unwatched
"""
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

import console_doctor as D
import printer as PR
import reel_templates as RT


def _templates_for(specs):
    """The REAL templates() answer for synthetic reels. -> dict

    ⚠ IT DRIVES `templates()` RATHER THAN HAND-BUILDING ROWS, and that is the difference between
    grading the code and grading a fixture. `subTemplate`, `ledgers`, `tabs` and `routes` are all
    computed by the module under test; only the two INPUTS it cannot get here are supplied — the
    journal rows (his ring holds none for these ids) and the segmenter's activity (segmentation
    has its own tests and is not what is being graded). Same patch points, and the same stated
    reason, as test_chronicle_ledger_refines_the_template.
    """
    by_session = {s["sid"]: list(s.get("rows") or []) for s in specs}
    act = {"reel_" + s["sid"]: s.get("activity") for s in specs}
    real_rows, real_segs = RT._journal_rows, RT._segments_for

    def _segs(name, by):
        a = act.get(name)
        return ([{"activity": a}], "") if a else ([], "the fixture gave this reel no activity")

    RT._journal_rows = lambda *a, **k: (by_session, "")
    RT._segments_for = _segs
    try:
        river = {"rows": [{"reel": "reel_" + s["sid"]} for s in specs]}
        out = RT.templates(river=river)
        if not (out or {}).get("rows"):
            raise AssertionError("the synthetic river produced no rows — this measures NOTHING")
        return out
    finally:
        RT._journal_rows, RT._segments_for = real_rows, real_segs


#: One reel per route, each carrying exactly the evidence that route is defined by.
ALL_FOUR = [
    {"sid": "s_T_STASH", "activity": "stash",
     "rows": [{"lane": "deep", "stashTab": "gems", "sessionId": "s_T_STASH"}]},
    {"sid": "s_T_SETS", "activity": "chronicle",
     "rows": [{"lane": "chronicle", "kind": "visit", "ledger": "sets",
               "sessionId": "s_T_SETS"}]},
    {"sid": "s_T_UNIQ", "activity": "chronicle",
     "rows": [{"lane": "deep", "chronicleTab": "uniques", "sessionId": "s_T_UNIQ"}]},
    {"sid": "s_T_INV", "activity": "inventory",
     "rows": [{"lane": "deep", "scene": "inventory", "sessionId": "s_T_INV"}]},
]


def _row(reading, sid):
    for r in reading["rows"]:
        if r["reel"] == "reel_" + sid:
            return r
    raise AssertionError("no row for %s" % sid)


class TheFourRoutesAreFour(unittest.TestCase):
    """Granularity: four routes, four answers, and the chronicle pair is not one bucket."""

    def test_every_declared_route_resolves_when_its_input_exists(self):
        cen = RT.route_census(reading=_templates_for(ALL_FOUR))
        for name, _z, _d in RT.ROUTES:
            self.assertEqual(cen["routes"][name]["state"], "OK",
                             "%s did not resolve on an input built to exercise it: %s"
                             % (name, cen["routes"][name]["why"]))
        self.assertTrue(cen["ok"], cen["why"])
        self.assertEqual(cen["state"], "OK", cen["why"])

    def test_the_two_chronicle_routes_name_DIFFERENT_reels(self):
        """The core of the defect: one zone, two readings, and they were the same row."""
        cen = RT.route_census(reading=_templates_for(ALL_FOUR))
        sets_ = cen["routes"]["chronicle · sets"]
        uniq = cen["routes"]["chronicle · uniques"]
        self.assertEqual(sets_["sample"], ["reel_s_T_SETS"],
                         "the sets route claims %r — the two chronicle routes are still one "
                         "bucket" % (sets_["sample"],))
        self.assertEqual(uniq["sample"], ["reel_s_T_UNIQ"],
                         "the uniques route claims %r" % (uniq["sample"],))
        self.assertEqual((sets_["reels"], uniq["reels"]), (1, 1))
        # and both are in the SAME zone — which is exactly why the zone could never tell them apart
        self.assertEqual(sets_["zone"], uniq["zone"])

    def test_a_reel_that_visited_BOTH_ledgers_is_on_BOTH_routes(self):
        """Not forced to a single winner. A preference nobody expressed is still an invention."""
        reading = _templates_for([
            {"sid": "s_T_BOTH", "activity": "chronicle",
             "rows": [{"lane": "chronicle", "kind": "visit", "ledger": "sets",
                       "sessionId": "s_T_BOTH"},
                      {"lane": "deep", "chronicleTab": "uniques", "sessionId": "s_T_BOTH"}]}])
        row = _row(reading, "s_T_BOTH")
        self.assertEqual(sorted(row["routes"]), ["chronicle · sets", "chronicle · uniques"])
        self.assertIsNone(row["route"],
                          "a reel on two routes reported a single one (%r), which picks a winner "
                          "the data never named" % (row["route"],))


class OneRouteDiesAlone(unittest.TestCase):
    """The whole point of the granularity: it must be possible to tell WHICH route died."""

    def _broken(self, mutate):
        reading = _templates_for(ALL_FOUR)
        mutate(reading)
        return RT.route_census(reading=reading)

    def test_a_dropped_route_reddens_ONLY_that_route(self):
        def mutate(reading):
            r = _row(reading, "s_T_SETS")
            r["routes"] = [x for x in r["routes"] if x != "chronicle · sets"]
        cen = self._broken(mutate)
        self.assertEqual(cen["broken"], ["chronicle · sets"],
                         "exactly one route lost its reel and the census reported %r — a rail "
                         "that cannot say WHICH of four broke is the thing being fixed"
                         % (cen["broken"],))
        for other in ("stash", "chronicle · uniques", "inventory"):
            self.assertEqual(cen["routes"][other]["state"], "OK",
                             "%s went red for a defect in another route: %s"
                             % (other, cen["routes"][other]["why"]))

    def test_each_of_the_four_can_be_the_ONLY_red_one(self):
        """Not one representative case — every route, or three of them are unproven laws."""
        for name, _z, _d in RT.ROUTES:
            def mutate(reading, name=name):
                for r in reading["rows"]:
                    if name in (r.get("routes") or []):
                        r["routes"] = [x for x in r["routes"] if x != name]
            cen = self._broken(mutate)
            self.assertEqual(cen["broken"], [name],
                             "breaking %s reddened %r instead" % (name, cen["broken"]))
            self.assertEqual(cen["state"], "BROKEN")

    def test_the_LABEL_losing_the_ledger_is_a_red_route(self):
        """v2709 REGRESSING IS THE CASE THIS WAS BUILT FOR.

        `subTemplate` is the only half that reaches a screen, and it reached no consumer at all, so
        it falling back to the bare word `chronicle` would have been silent. The census is derived
        from the structured fields; the label is derived beside it; where they meet is the only
        place either can be caught. [[feedback-contradiction-is-the-finding]]
        """
        def mutate(reading):
            _row(reading, "s_T_UNIQ")["subTemplate"] = "chronicle"
        cen = self._broken(mutate)
        self.assertEqual(cen["broken"], ["chronicle · uniques"], cen["why"])
        self.assertIn("does not name the uniques ledger",
                      cen["routes"]["chronicle · uniques"]["why"])

    def test_a_label_pointing_at_the_wrong_zone_is_a_red_route(self):
        def mutate(reading):
            _row(reading, "s_T_STASH")["subTemplate"] = "inventory · gems"
        cen = self._broken(mutate)
        self.assertEqual(cen["broken"], ["stash"], cen["why"])

    def test_a_missing_label_is_a_red_route_not_a_quiet_pass(self):
        def mutate(reading):
            _row(reading, "s_T_INV")["subTemplate"] = None
        cen = self._broken(mutate)
        self.assertEqual(cen["broken"], ["inventory"], cen["why"])


class UnknownIsFirstClass(unittest.TestCase):
    """A route nobody exercised is UNPROVEN. It is never OK, and it is never BROKEN either."""

    def test_a_route_with_no_data_is_UNKNOWN(self):
        cen = RT.route_census(reading=_templates_for([ALL_FOUR[0]]))
        self.assertEqual(cen["routes"]["stash"]["state"], "OK")
        for dark in ("chronicle · sets", "chronicle · uniques", "inventory"):
            self.assertEqual(cen["routes"][dark]["state"], "UNKNOWN",
                             "%s read %s on a shelf that never exercised it"
                             % (dark, cen["routes"][dark]["state"]))
        self.assertEqual(cen["broken"], [])
        self.assertFalse(cen["ok"],
                         "three routes were never exercised and the census called itself ok — "
                         "that is the green that lies")
        self.assertEqual(cen["state"], "PARTIAL")

    def test_a_chronicle_reel_with_NO_ledger_breaks_nothing_and_is_counted(self):
        """His one real chronicle reel is exactly this. Nobody-recorded is not a broken route."""
        cen = RT.route_census(reading=_templates_for([
            {"sid": "s_T_BARE", "activity": "chronicle",
             "rows": [{"lane": "deep", "scene": "chronicle", "sessionId": "s_T_BARE"}]}]))
        for name in ("chronicle · sets", "chronicle · uniques"):
            r = cen["routes"][name]
            self.assertEqual(r["state"], "UNKNOWN", r["why"])
            self.assertEqual(r["inZone"], 1, "the reel vanished from the denominator")
            self.assertEqual(r["unnamed"], 1,
                             "a chronicle reel with no recorded ledger was not counted as one, so "
                             "the zero has no denominator")

    def test_an_unusable_reading_keeps_ALL_FOUR_keys(self):
        """REG-546 — a shape that changes with the verdict is not a shape."""
        cen = RT.route_census(reading={"rows": None, "why": "nobody answered"})
        self.assertEqual(sorted(cen["routes"]), sorted(n for n, _z, _d in RT.ROUTES),
                         "the census SHRANK on the path that means nothing was established")
        for name in cen["routes"]:
            self.assertEqual(cen["routes"][name]["state"], "UNKNOWN")
            self.assertIsNone(cen["routes"][name]["reels"],
                              "an unread census reported a COUNT of reels — 0 and 'nobody looked' "
                              "are opposite facts")
        self.assertFalse(cen["ok"])


class ThePrinterCarriesIt(unittest.TestCase):
    """The join itself: subTemplate has to reach the surface that shows the river."""

    def _stream(self, specs):
        reading = _templates_for(specs)
        names = [r["reel"] for r in reading["rows"]]
        src = {
            "river": {"rows": [{"reel": n, "stage": "swept", "decider": "fixture",
                                "question": "fixture", "reelAnswer": False,
                                "frameAnswer": None} for n in names]},
            "door": {"rows": [{"reel": n, "door": "recorder"} for n in names]},
            "routes": {"rows": []},
            "templates": reading,
            "routeCensus": RT.route_census(reading=reading),
            "gap": {"rows": []},
            "reach": {"state": "UNKNOWN", "why": "fixture"},
            "tombstones": {"reels": []},
        }
        real = PR._sources
        PR._sources = lambda: (src, [])
        try:
            return PR.stream()
        finally:
            PR._sources = real

    def test_the_template_station_names_which_chronicle_page_and_which_stash_tab(self):
        out = self._stream(ALL_FOUR)
        got = {r["reel"]: r["stations"]["template"] for r in out["rows"]}
        self.assertEqual(got["reel_s_T_SETS"].get("subTemplate"), "chronicle · sets",
                         "the printer's TEMPLATE station still cannot name which chronicle page "
                         "a reel showed: %r" % (got["reel_s_T_SETS"].get("subTemplate"),))
        self.assertEqual(got["reel_s_T_UNIQ"].get("subTemplate"), "chronicle · uniques")
        self.assertEqual(got["reel_s_T_STASH"].get("subTemplate"), "stash · gems")
        self.assertEqual(got["reel_s_T_SETS"].get("route"), "chronicle · sets")
        self.assertEqual(got["reel_s_T_INV"].get("route"), "inventory")
        # ⚠ AND THE ZONE IS STILL THE VERDICT. Moving `say` to the finer label would re-bucket
        # every number in `counts` underneath a reader who never asked for that.
        self.assertEqual(got["reel_s_T_SETS"].get("say"), "CHRONICLE")

    def test_the_stream_publishes_one_state_per_route(self):
        out = self._stream(ALL_FOUR)
        self.assertEqual(sorted((out.get("routes") or {}).get("routes") or {}),
                         sorted(n for n, _z, _d in RT.ROUTES),
                         "the printer's payload does not carry a state per route")

    def test_the_UNKNOWN_return_still_carries_four_routes(self):
        """REG-546 again, at the payload level: a consumer must not raise on the failure path."""
        real = PR._sources
        PR._sources = lambda: ({}, ["nothing answered"])
        try:
            out = PR.stream()
        finally:
            PR._sources = real
        self.assertFalse(out["ok"])
        self.assertEqual(sorted((out.get("routes") or {}).get("routes") or {}),
                         sorted(n for n, _z, _d in RT.ROUTES))


class TheDoctorWatchesEachOne(unittest.TestCase):
    """A supervisor per route, and each of them able to go red on its own."""

    @staticmethod
    def _fake(states):
        return {"ok": False, "state": "BROKEN", "order": [n for n, _z, _d in RT.ROUTES],
                "broken": [k for k, v in states.items() if v == "BROKEN"],
                "unproven": [k for k, v in states.items() if v == "UNKNOWN"],
                "routes": {k: {"route": k, "state": v, "why": "fixture says %s" % v}
                           for k, v in states.items()},
                "why": "fixture"}

    def _ask(self, name, census):
        real = D._route_read
        D._route_read = lambda: census
        try:
            return dict(D.CHECKS)[name]()
        finally:
            D._route_read = real

    def test_there_is_a_row_for_every_DECLARED_route(self):
        """A fifth route must not be able to arrive unwatched."""
        named = dict(D.CHECKS)
        for name, _z, _d in RT.ROUTES:
            self.assertIn("route " + name, named,
                          "reel_templates declares the %r route and console_doctor has no row "
                          "for it — it would die in silence" % name)

    def test_exactly_one_doctor_row_goes_red(self):
        cen = self._fake({"stash": "OK", "chronicle · sets": "BROKEN",
                          "chronicle · uniques": "OK", "inventory": "OK"})
        got = {n: self._ask("route " + n, cen)[0] for n, _z, _d in RT.ROUTES}
        self.assertEqual(got["chronicle · sets"], D.MISSING, got)
        self.assertEqual([n for n, s in got.items() if s == D.MISSING], ["chronicle · sets"],
                         "one broken route reddened %r" % (got,))

    def test_an_unproven_route_is_UNKNOWN_at_the_rail_too(self):
        cen = self._fake({"stash": "OK", "chronicle · sets": "UNKNOWN",
                          "chronicle · uniques": "UNKNOWN", "inventory": "OK"})
        self.assertEqual(self._ask("route chronicle · sets", cen)[0], D.UNKNOWN)
        self.assertEqual(self._ask("route stash", cen)[0], D.OK)

    def test_a_census_that_will_not_answer_is_UNKNOWN_not_OK(self):
        for dead in ({}, {"ok": False, "routes": {}, "why": "reel_templates would not import"},
                     None):
            st, why = self._ask("route stash", dead)
            self.assertEqual(st, D.UNKNOWN, "a dead census read %s for %r" % (st, dead))
            self.assertTrue(why.strip(), "UNKNOWN with no reason is a blank a reader fills in")

    def test_the_tick_cache_never_outlives_the_tick(self):
        """Four rows, ONE river walk — and a check asked on its own must still read FRESH.

        The cache is scoped to `run()` for the reason written beside `_board_read`: a module-level
        cache with a TTL swallows a test's stub and serves the previous test's answer, which broke
        eight guards at once the first time it was tried. [[feedback-suspect-the-instrument]]
        """
        cached, fresh = {"routes": {"x": {}}, "why": "cached"}, {"routes": {"y": {}}, "why": "fresh"}
        real_once, real_cache = D._route_census_once, dict(D._routes_cache)
        D._route_census_once = lambda: fresh
        try:
            D._routes_cache["active"], D._routes_cache["got"] = True, cached
            self.assertIs(D._route_read(), cached, "the tick was open and the cache was ignored — "
                                                   "four rows would walk the river four times")
            D._routes_cache["active"], D._routes_cache["got"] = False, cached
            self.assertIs(D._route_read(), fresh,
                          "the tick was SHUT and a stale answer was served anyway")
        finally:
            D._route_census_once = real_once
            D._routes_cache.update(real_cache)

    def test_run_OPENS_and_CLOSES_the_tick_cache(self):
        """⚠ ASSERTED OFF THE PARSE TREE, NEVER OFF THE TEXT. `run()` cannot be called here — it
        POSTs to /api/board_ownership, which evaluates JavaScript in the window he is looking at
        [[borrowed-surface]]. So the law is read from the AST, where a comment or a docstring
        mentioning `_routes_cache` cannot satisfy it, and both ends are required: a cache opened
        and never closed leaks one tick's answer into every later call in the process.
        """
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(D))
        top = {n.name: n for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        fn = top.get("run")
        self.assertIsNotNone(fn, "console_doctor has no run()")
        # ⚠⚠ v2815 MOVED THE TWO LINES ONE HOP OUT OF run(), AND THIS LAW LOST ITS SUBJECT.
        # They now live in the `tick_caches()` context manager that run() enters — the mechanism
        # is intact, but a search of run()'s own body returned 0 and the gate had been red since,
        # for code that is correct. So the law FOLLOWS the tick instead of assuming it is inline:
        # run(), plus every module-level function run() calls by bare name — which is exactly what
        # `with tick_caches():` is, a Call in a withitem. The bite is unchanged in both directions:
        # delete either line from tick_caches and the count falls to 1; delete `with tick_caches()`
        # from run() and the reach empties to 0. One hop only, so a cache opened by some function
        # this tick never enters still cannot satisfy it. [[label-outlived-referent]]
        reached = [fn] + [top[n.func.id] for n in ast.walk(fn)
                          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                          and n.func.id in top]
        # ⚠⚠ COUNT ASSIGNMENT *STATEMENTS*, NOT NAME OCCURRENCES — the first cut counted Names,
        # and the close line alone mentions `_routes_cache` twice, so deleting the OPEN left the
        # count at 2 and the sabotage came back GREEN. A law satisfied by a single statement it
        # was written to require two of. [[sabotage-is-usually-the-wrong-one]]
        sets = [n for body in reached for n in ast.walk(body)
                if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "_routes_cache"
                        for t in ast.walk(n))]
        self.assertGreaterEqual(len(sets), 2,
                                "run() does not both open and close the route cache (%d "
                                "assignment(s) found) — four rows would each walk the river, or "
                                "one tick's answer would outlive its tick" % len(sets))

    def test_a_route_that_VANISHED_from_the_census_is_UNKNOWN(self):
        """A check that stopped being reported must never read as a check that passed."""
        cen = self._fake({"stash": "OK"})
        st, why = self._ask("route inventory", cen)
        self.assertEqual(st, D.UNKNOWN)
        self.assertIn("no longer reports", why)


RED_PROOF = [
    {
        'why': 'The line is the ONLY place in the tree where `route_census` catches a reel that carries a route\'s evidence and did not come out on that route — the "the join dropped" arm of the three-state verdict. It is real executable code inside the per-route loop, not a comment and not a message string, and it is not shared with the other side of any comparison: the census derives BROKEN from `r["routes"]` here, while the corroborating label check `_label_agrees` reads `subTemplate` further down and is untouched, so the two halves cannot both move together. It is also not the ROUTES tuple — that IS the shared constant this file\'s tests iterate on both sides, and editing it would have shrunk expectation and answer together. With the arm removed, a route whose reel was un-routed simply produces an empty `took` list and falls through to UNKNOWN, so the census reports `broken == []` instead of naming which of the four died — exactly the defect the file exists for ("a rail that cannot say WHICH of four broke"). Anchor counted 1 in reel_templates.py and 1 tree-wide across every .py/.html/.js, so replace-all and replace-one are the same experiment.  MEASURED: untampered OK; tampered (all 1 match(es)) FAILED (failures=2); reddened law test_a_dropped_route_reddens_ONLY_that_route; that law ALONE FAILED (failures=1) — `python3 -m unittest test_the_four_routes_go_red_alone.OneRouteDiesAlone.test_a_dropped_route_redd.',
        'file': 'reel_templates.py',
        'find': 'if name not in (r.get("routes") or []):',
        'replace': 'if False:',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
