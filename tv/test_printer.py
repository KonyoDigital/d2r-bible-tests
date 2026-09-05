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
import contextlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import printer as P   # noqa: E402

#: ⚠⚠ SIX OF THESE MEASURED WHETHER THE MACHINE WAS HIS, NOT WHETHER THE PRINTER WORKS. They called
#: `P.stream()` against the REAL shelf, and the shelf is gitignored — `.gitignore:21` excludes
#: `tv/frames/`, `git ls-files tv/frames` returns **0**, and nothing in `.github/workflows/` sets
#: `TV_HIST`. So on a fresh clone BOTH shelf owners answer with zero rows — `one_start_point` via
#: `tv_diablo.HIST_DIR` (one_start_point.py:134 `if not hist or not os.path.isdir(hist)`), and
#: `reel_river` → `reel_story.story()` → `reel_retention.plan(hist_dir=None)`, which falls back to
#: the hardcoded `HERE/frames/hist` (reel_retention.py:319) and is NOT TV_HIST-overridable — and
#: `printer.py:197` short-circuits to "UNKNOWN, not an empty shelf". MEASURED, not assumed: a copy
#: of `git ls-files tv/` with no `frames/` ran this file to `failures=6, skipped=2` — the same line
#: CI printed, the same six names, the same six messages.
#:
#: ⚠ SO THEY PLANT THEIR OWN SHELF, which is what the eight cases that already passed on CI do
#: (:50, :96, :138, :191, :244). Skipping instead would have turned the gate green while retiring
#: the law — and this repo has lost eight of seventeen named reels to exactly that [[regression-
#: guard]]. A planted shelf keeps every assertion RUNNING, and makes the gate say the same thing on
#: his Mac and on a runner instead of one thing on each.
FIXTURE_REELS = ("reel_s_1_1", "reel_s_1_2")


def _planted_door(reels=FIXTURE_REELS):
    """`one_start_point`'s reading, in its shape, for a shelf that need not exist on disk."""
    return {"ok": True, "state": "ONE_DOOR", "walked": len(reels), "notADirectory": 0,
            "counts": {"recorder": len(reels)},
            "rows": [{"reel": r, "door": "recorder", "why": "planted shelf"} for r in reels],
            "why": "planted shelf"}


def _planted_river(reels=FIXTURE_REELS):
    """`reel_river`'s reading. Carries `stage`+`decider` (the funnel station's field and its extra)
    and `reelAnswer`/`frameAnswer` (the out station's two doors), so no station reads a key the
    fixture forgot and calls the printer wrong for it."""
    return {"ok": True, "state": "WALKED", "gaps": [], "namelessRows": 0, "clean": {},
            "rows": [{"reel": r, "stage": "banked", "decider": "reel_retention",
                      "question": "how far down the river has this reel come?",
                      "reelAnswer": True, "frameAnswer": None} for r in reels],
            "why": "planted shelf"}


def _empty_river():
    """An owner that ANSWERED and had nothing — not one that was never asked. Every key the real
    empty return carries (reel_river.py:105-113), because a shape that changes with the verdict is
    the very thing REG-547/REG-560 exist to catch."""
    return {"ok": True, "state": "WALKED", "rows": [], "gaps": [], "namelessRows": 0,
            "clean": {}, "why": "planted empty"}


@contextlib.contextmanager
def _planted_shelf(river=True, reels=FIXTURE_REELS):
    """Plant the two SHELF owners — the only two `printer.py:197` unions into a shelf — and put the
    real ones back. Every other owner stays REAL, so what these cases measure is still the printer
    quoting owners it did not plant."""
    import one_start_point as OSP
    import reel_river as RR
    real_door, real_river = OSP.start_points, RR.river
    try:
        OSP.start_points = lambda *a, **k: _planted_door(reels)
        RR.river = (lambda *a, **k: _planted_river(reels)) if river \
            else (lambda *a, **k: _empty_river())
        yield
    finally:
        OSP.start_points, RR.river = real_door, real_river


class EveryStationQuotesItsOwner(unittest.TestCase):

    def test_every_reel_gets_every_station(self):
        """A station missing from a row would read as a reel that did not need it."""
        with _planted_shelf():
            r = P.stream()
        self.assertTrue(r["ok"], r["why"])
        # ⚠ A vacuous walk would pass every assertion below without asking one of them. Stated as
        # CONTAINMENT, not a count: the shelf is a UNION, so on his Mac per_reel_routes adds his
        # 40 real reels to the 2 planted ones and a pinned number would be about his footage
        # rather than about the law. [[regression-guard]]
        walked = set(row["reel"] for row in r["rows"])
        self.assertTrue(set(FIXTURE_REELS) <= walked,
                        "the planted shelf never reached the printer, so the loop below asks "
                        "nothing: %s" % sorted(walked)[:4])
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
        """⚠ Same law as the IN station above. It needs a SHELF as well as a planted owner, because
        `route`'s owner is not one of the two `printer.py:197` unions into one — so with no footage
        the printer never reached the station at all and this read `'sentinel' not found in []`."""
        import per_reel_routes as PRR
        real = PRR.routes
        try:
            PRR.routes = lambda *a, **k: {
                "ok": True, "state": "EARNED", "byDecider": {}, "contentRoutes": {},
                "policyRoutes": {}, "distinctContentRoutes": 0, "minDistinct": 2, "walked": 1,
                "rows": [{"reel": FIXTURE_REELS[0], "tag": "t", "stage": "s",
                          "decidedBy": "sentinel", "why": "planted", "route": "t@s"}], "why": "x"}
            with _planted_shelf():
                says = [row["stations"]["route"]["say"]
                        for row in P.stream(FIXTURE_REELS[0])["rows"]]
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

    def test_a_row_that_names_NO_reel_does_not_become_a_phantom_reel(self):
        """⚠⚠ REG-550. `_by_reel` keyed on `str(r.get("reel") or "")`, so a malformed row from any
        owner joined the shelf **under the empty string** and the printer walked it as a reel —
        every station reporting on nothing, and the shelf one longer than it should be. Found while
        checking a cold review's claim about EMPTY ROWS; the reviewer named the row, not this."""
        import one_start_point as OSP
        real = OSP.start_points
        try:
            OSP.start_points = lambda *a, **k: {
                "ok": True, "state": "ONE_DOOR", "counts": {}, "walked": 2,
                # three ways a row can name no reel, so BOTH drop branches are exercised:
                # a non-dict, an empty dict, and a dict whose `reel` is blank.
                "rows": [None, {}, {"reel": "   "},
                         {"reel": "reel_s_1", "door": "recorder", "why": "w"}], "why": "x"}
            keys, dropped = P._by_reel(OSP.start_points())
            self.assertNotIn("", keys, "a row naming no reel became a reel called '': %s" % keys)
            self.assertEqual(sorted(keys), ["reel_s_1"], keys)
            # ⚠⚠ REG-551, the NINTH instance today: the first cut dropped nameless rows SILENTLY,
            # which is exactly what REG-541 taught me to stop doing in dead_field two hours
            # earlier. A row that vanishes with nothing counting it shrinks the shelf and nothing
            # says so.
            self.assertEqual(dropped, 3,
                             "%d of 3 nameless row(s) were counted — a non-dict, an empty dict and "
                             "a blank `reel` must all be counted, not just the ones the fixture "
                             "happens to hit" % dropped)
            r = P.stream()
            self.assertEqual(r["droppedRows"], 3, "the reading does not carry the drop count: %s"
                             % r.get("droppedRows"))
            self.assertIn("named no reel", r["why"],
                          "the drop is counted but never said out loud: %r" % r["why"])
        finally:
            OSP.start_points = real

    def test_a_row_that_CARRIES_NOTHING_says_so_rather_than_never_reported(self):
        """⚠⚠ THIS TEST WAS WRONG WHEN FIRST WRITTEN AND ITS SABOTAGE CAUGHT IT. It claimed to
        prove that an EMPTY row (`{}`) is distinguished from an absent one — and the sabotage
        restoring `if not row:` went GREEN, because the row it builds carries a `reel` key and is
        therefore not empty.

        Measured after: an empty dict is **UNREACHABLE** from these callers, because `_by_reel`
        drops every row that names no reel. So the branch exists and is defensive only, labelled
        as such in the source, with no test — writing one would mean building a caller that cannot
        exist.

        What IS reachable, and what this now proves: a row that names its reel and carries no
        VALUE for the field must say *carried no <field>*, not *did not report this reel*.
        """
        import reel_river as RR
        realr = RR.river
        try:
            RR.river = lambda *a, **k: {"ok": True, "gaps": [], "why": "x", "clean": {},
                                        "rows": [{"reel": "reel_s_1"}]}
            row = P.stream("reel_s_1")["rows"][0]
            why = row["stations"]["funnel"]["why"]
            self.assertIn("carried no", why,
                          "an owner that ANSWERED with a row carrying no stage was reported as "
                          "not having reported the reel at all: %r" % why)
            self.assertNotIn("did not report", why, why)
        finally:
            RR.river = realr

    def test_a_STATIONS_shape_does_not_depend_on_its_verdict_either(self):
        """⚠⚠ REG-547 — THE SEVENTH INSTANCE OF ONE CLASS IN A DAY, AND I WROTE IT INSIDE THE FIX
        FOR THE SIXTH. `_station` returned early when the owner had nothing, so the station DROPPED
        its extra keys — `decider`, `route` — on exactly the path where it has nothing to report.
        Measured: funnel carried `['decider','say','why']` normally and `['say','why']` when
        reel_river reported nothing.

        ⚠ The reading-level shape law could not see this: it compares the TOP-LEVEL key sets, and
        this one is nested two levels down. So the law is asked here, per station, at every reel.
        """
        # ⚠ BOTH SIDES NEED A SHELF. The comparison used the real one for `normal`, so with no
        # footage both sides were [] and it failed on "no rows to compare" — it was measuring the
        # machine. Planted, the two sides differ in exactly the one variable the law is about:
        # whether reel_river had anything to say about the reel it is asked about.
        with _planted_shelf(river=False):
            silent = dict((r["reel"], r["stations"]) for r in P.stream()["rows"])
        with _planted_shelf(river=True):
            normal = dict((r["reel"], r["stations"]) for r in P.stream()["rows"])
        self.assertTrue(silent and normal, "no rows to compare")
        # ⚠⚠ ADDRESSED BY NAME, NOT BY `rows[0]`, AND THE TWO GUARDS BELOW ARE WHY I KNOW. The
        # shelf is a UNION, so on his Mac per_reel_routes contributes 40 real reels that sort
        # ahead of the fixture — `rows[0]` was one of HIS, which the planted river says nothing
        # about, so its funnel was UNKNOWN on BOTH sides and the loop compared a shape with
        # itself. A comparison whose two sides do not differ cannot go red. [[regression-guard]]
        subject = FIXTURE_REELS[0]
        self.assertIn(subject, silent, "the planted shelf never reached the printer")
        self.assertIn(subject, normal, "the planted shelf never reached the printer")
        self.assertEqual(silent[subject]["funnel"]["say"], "UNKNOWN",
                         "the SILENT side's funnel owner answered, so the two sides do not "
                         "differ and the comparison below is between a shape and itself")
        self.assertNotEqual(normal[subject]["funnel"]["say"], "UNKNOWN",
                            "the NORMAL side's funnel owner said nothing either, so likewise")
        for st in P.STATIONS:
            a = set(silent[subject][st])
            b = set(normal[subject][st])
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
            # ⚠ The shelf is planted so the union below has something to be a union OF — with no
            # footage `says` came back as the empty set and this passed judgement on nothing.
            with _planted_shelf():
                r = P.stream()
                river_reels = P._by_reel(__import__("reel_river").river())[0]
            # ⚠⚠ A LINE THAT LOOKED LIKE AN ASSERTION AND COULD NOT FAIL SHIPPED HERE, caught by
            # the review-after-ship pass on my own v2544 bytes. It read
            #     self.assertEqual(...) if False else None
            # — the `if False` makes the whole expression a no-op, so it never ran while reading
            # exactly like a check. That is the same shape as the tautology REG in test_dom_probe:
            # a guard satisfied by its own text. The real question it meant to ask is below, and it
            # RUNS: an owner reporting nothing must not shrink the shelf.
            self.assertEqual(
                r["walked"], len(river_reels),
                "an owner reported no reels and the printer's shelf shrank with it — the union of "
                "the owners is the shelf, so a reel absent from ONE of them must still appear")
            self.assertTrue(river_reels, "no shelf, so shrinking it would not have shown")
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
        without saying so would invent forty per-reel measurements nobody took.

        ⚠⚠ THIS PINNED THE WORD "SHELF-WIDE" IN `why`, AND v2572 MOVED THE FACT. The station's
        `why`/`say` now carry `extract_gap`'s PER-REEL answer, and printer_reach's shelf-wide one
        rides alongside in `shelfReach`/`shelfWhy` — a better design, and this assertion went red
        for it and stayed red on `main`. **The rule survives the move; the word did not.** So it
        pins the RULE: the shelf-wide answer must be present, must be labelled as being about
        SEALS rather than reels, and must be in a DIFFERENT field from the per-reel answer — which
        is the whole point, since one field holding both is how they got confused before.
        """
        for row in P.stream()["rows"][:3]:
            ex = row["stations"]["extract"]
            self.assertIn("shelfReach", ex, "the shelf-wide answer is not carried at all")
            self.assertIn("SEALS", ex.get("shelfWhy") or "",
                          "the shelf-wide answer is printed per reel with nothing saying it is "
                          "about seals rather than about this reel")
            self.assertNotEqual(
                ex.get("shelfWhy"), ex.get("why"),
                "the per-reel answer and the shelf-wide answer are the same string, so a reader "
                "cannot tell which of the two questions was answered")

    def test_an_EXTRACT_station_whose_owner_will_not_ANSWER_still_gives_a_REASON(self):
        """⚠⚠ REG-576 — UNKNOWN WITH NO REASON, in the station whose job is refusing to invent one.
        `_sources()` already CATCHES an owner that raises and already WRITES DOWN why. Nothing
        handed that sentence to the station, so with printer_reach raising `shelfWhy` rendered as
        *"printer_reach, about SEALS not reels: "* — a label, a colon, and nothing. Reproduced
        across all 40 of his reels. [[the-unjoined-end]]

        ⚠ The STATE was already correct — `shelfReach` reads UNKNOWN and was never permissive — so
        this is about what UNKNOWN SAYS, not what it decides. A blank reason is one a reader fills
        in themselves."""
        import printer_reach as PR
        real = PR.report
        PR.report = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("reach is unmeasurable"))
        try:
            # ⚠ A shelf, so there is a ROW for the raised reason to be missing from. With no
            # footage the printer returned before building one and this proved nothing.
            with _planted_shelf():
                rows = P.stream()["rows"]
        finally:
            PR.report = real
        self.assertTrue(rows, "no reel was walked, so nothing was established")
        for row in rows[:3]:
            ex = row["stations"]["extract"]
            self.assertEqual(ex.get("shelfReach"), "UNKNOWN",
                             "the owner raised and the shelf answer was not UNKNOWN")
            tail = str(ex.get("shelfWhy") or "").split(":", 1)[-1].strip()
            self.assertTrue(tail, "UNKNOWN was reported with an EMPTY reason: %r"
                                  % ex.get("shelfWhy"))
            self.assertIn("unmeasurable", tail,
                          "the reason given is not the one the owner actually gave, so a generic "
                          "sentence stood in for the real failure: %r" % tail)

    def test_it_refuses_nothing_and_deletes_nothing(self):
        """⚠ The prune stays OFF. This routes a reel ON PAPER and says where it came out."""
        import io
        src = io.open(os.path.join(HERE, "printer.py"), encoding="utf-8").read()
        for banned in ("os.remove", "os.unlink", "shutil.rmtree", "os.rmdir", '"w"', "'w'"):
            self.assertNotIn(banned, src,
                             "the printer contains %r — it reports, it does not act" % banned)


class TheSummaryNamesWHICHStationAndWHY(unittest.TestCase):
    """⚠⚠ "14 reel(s) have a station nobody answered" READ AS A PRINTER GAP, AND IT IS AN INPUT GAP.

    Measured on his shelf: all 14 are UNKNOWN at exactly ONE station — TEMPLATE — and every one has
    **ZERO deep journal rows** while carrying 22-2,385 frames on disk and 7-40 SHALLOW rows. They
    were read, and never read DEEPLY. v2604 taught the station to say so; the summary still only
    counted, so **a reader acting on that sentence goes and investigates a river that is working
    perfectly.** [[label-outlived-referent]]"""

    def test_the_summary_names_the_station_and_quotes_its_reason(self):
        rep = P.stream()
        unknown = [r for r in rep["rows"]
                   if any(str(r["stations"][st].get("say")) == "UNKNOWN" for st in P.STATIONS)]
        if not unknown:
            self.skipTest("nothing is UNKNOWN on this shelf, so there is no summary to check")
        why = rep["why"]
        self.assertIn("The unanswered stations are:", why,
                      "the summary counts unanswered stations without naming one: %r" % why[:200])
        # the station it names must be one that is genuinely unknown on a real row
        named = [st for st in P.STATIONS if st.upper() in why]
        self.assertTrue(named, "no station was named: %r" % why[:200])
        for st in named:
            self.assertTrue(
                any(str(r["stations"][st].get("say")) == "UNKNOWN" for r in unknown),
                "the summary named %r, and no reel is UNKNOWN there" % st)

    def test_the_reason_is_the_STATIONS_OWN_why_and_not_invented(self):
        """⚠ A summary that paraphrases is a second copy of a fact — this quotes."""
        rep = P.stream()
        why = rep["why"]
        if "The unanswered stations are:" not in why:
            self.skipTest("nothing unanswered")
        reasons = set()
        for r in rep["rows"]:
            for st in P.STATIONS:
                if str(r["stations"][st].get("say")) == "UNKNOWN":
                    w = str(r["stations"][st].get("why") or "").strip()
                    if w:
                        reasons.add(w[:60])
        self.assertTrue(any(frag in why for frag in reasons),
                        "the summary's reason appears in no station: %r" % why[:200])

    def test_a_fully_answered_shelf_appends_NOTHING(self):
        """⚠ BASELINE — the detail must not be a sentence that is always there. If it appears when
        every station answered, it stops carrying information.

        ⚠ IT READ THE REAL SHELF AND SO IT DECIDED NOTHING ON A RUNNER: with no footage `rep["why"]`
        was "UNKNOWN, not an empty shelf …" and it failed on the second branch. Planted, it lands
        on the SAME branch on every machine — the shelf has stations nobody answered, because only
        the two shelf owners are planted. ⚠ The other branch stays unexercised, exactly as it is on
        his Mac (14 of his 40 reels are UNKNOWN at TEMPLATE), and this fix does not change that."""
        with _planted_shelf():
            rep = P.stream()
        if any(str(r["stations"][st].get("say")) == "UNKNOWN"
               for r in rep["rows"] for st in P.STATIONS):
            # construct the clean case from the real report rather than a fixture
            self.assertIn("The unanswered stations are:", rep["why"])
            return
        self.assertNotIn("The unanswered stations are:", rep["why"])
        self.assertIn("Every station answered", rep["why"])


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
