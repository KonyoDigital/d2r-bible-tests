"""v1578 — the Terror Zone panel: every zone the game can serve has a face and a verdict.

Konyo: "the TZ with the HD art isnt rendering properly i want it HD diablo ii extracted from the
game like it should be.. and make it bigger! i said flagship style and i want it to be seen on the
top" and "some of them should be greyed out (worthless zones) compared to good ones that need to be
emphasized. make sure theres a distinguished difference between them".

Three things were wrong and only one of them was the art:

1. THE ART WAS NOT FROM THE GAME. The 13 act graphics came from diablo2.io in v231. They covered
   13 of the 67 zones the rotation serves, and on the rotation live when he reported it the match
   rate was ZERO. The art is now extracted from his own D2R install (CASC -> .texture -> BC3).

2. THE OXFORD COMMA. The splitter tried `,\\s*` before `\\s+and\\s+`, so "Lost City, Valley of
   Snakes, and Claw Viper Temple" produced a chip labelled literally "and Claw Viper Temple" —
   which then missed every art and density lookup too, because levels.txt has no such level.

3. NOTHING DISTINGUISHED A GOOD ZONE FROM A DEAD ONE. Every zone rendered identically.

These tests guard the DATA behind all three. The RENDERING is proven separately, in a real browser,
by journey J9 in tv/demo_console.mjs — it stubs a rotation chosen to exercise every case at once
(a dense prime, a boss-prime that density alone would have greyed, two thin Act 1 zones) and asserts
on computed style, not on markup. This file guards the facts that rendering depends on, because a
wrong number rendered beautifully is worse than a right number rendered plainly.
"""

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402 — the failure messages carry non-ASCII (arrows, the
                     # em dash, Nihlathak); without this they die on a non-UTF-8 console
                     # instead of reporting, which is the one moment they must not.

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
UI = os.path.join(HERE, "control_ui.html")


def _strip_comments(src):
    """v1801 — GUARDS MUST READ CODE, NOT PROSE. Three separate assertions in this ship matched
    their own explanatory comments: a comment that says "the padlock was removed" contains the word
    padlock, so a grep for it passes forever while the feature is gone — or fails forever while it
    is. This repo has a carved scar for exactly that ([[feedback-comments-vs-code]]) and it still
    caught me three times in one session, because writing a good comment about a removal is the
    very act that plants the false match."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)      # css + js block comments
    return re.sub(r"^\s*//.*$", "", src, flags=re.M)      # js line comments


def _tz_info():
    src = open(UI, encoding="utf-8").read()
    m = re.search(r"var TZ_INFO = (\{.*?\});", src, re.S)
    assert m, "TZ_INFO table is gone from control_ui.html"
    return json.loads(m.group(1)), src


# v1610 — ART THAT IS KNOWN BAD, NAMED RATHER THAN TOLERATED SILENTLY.
# An exception you have to write a sentence for is a debt on the books. An exception with no
# entry here is a bug nobody can see — which is exactly how a flat grey tile shipped and stayed.
# v1611 — act3-spider was extracted properly from the game and the entry is GONE, which is the
# only correct end state for this table. An exception that outlives its bug is a lie with a
# comment on it, and test_no_exception_outlives_its_file exists to make sure that never happens.
KNOWN_FLAT_ART = {}


class TestTZArtCoverage(unittest.TestCase):
    def test_every_zone_has_den_lvl_and_an_art_key(self):
        info, _ = _tz_info()
        self.assertGreaterEqual(len(info), 60, "the rotation serves ~67 zones")
        for zone, row in info.items():
            self.assertEqual(len(row), 3, "%s: expected [den, lvl, artKey]" % zone)
            den, lvl, art = row
            self.assertIsInstance(den, int)
            self.assertTrue(60 <= lvl <= 99, "%s: implausible area level %r" % (zone, lvl))
            self.assertTrue(art, "%s has no art key" % zone)

    def test_every_art_key_is_a_file_that_exists(self):
        """The v1569 failure mode was a name match that resolved to nothing. A key with no file is
        a broken image on his TV, and the browser reports it to nobody."""
        info, _ = _tz_info()
        missing = sorted({
            row[2] for row in info.values()
            if not os.path.isfile(os.path.join(REPO, "art", "tz_%s.jpg" % row[2]))
        })
        self.assertEqual(missing, [], "art keys with no file in art/: %s" % missing)

    def test_the_art_is_real_images_not_placeholders(self):
        """v497 taught this repo that ~487 base_*.png were one identical corrupt placeholder. A
        size check is cheap and catches a whole extraction going wrong at once."""
        info, _ = _tz_info()
        keys = sorted({row[2] for row in info.values()})
        sizes = {}
        for k in keys:
            p = os.path.join(REPO, "art", "tz_%s.jpg" % k)
            n = os.path.getsize(p)
            self.assertGreater(n, 5000, "tz_%s.jpg is only %d bytes — suspect a failed decode" % (k, n))
            # v1610 — BYTES CANNOT SEE A BLANK IMAGE. tz_act3-spider.jpg was a flat grey tile that
            # sailed through this floor at 7,779 bytes: a featureless JPEG compresses small but not
            # THAT small, so the size check said "fine" while Spider Forest and Spider Cavern both
            # rendered as empty boxes in the panel. Konyo found it by looking, which is the one
            # thing a gate is supposed to make unnecessary.
            #
            # Pixel VARIANCE is the property that actually distinguishes art from a placeholder.
            # Measured across the 22 healthy tiles: stdev 14.0 - 42.7. The blank one: 2.8. A floor
            # of 8 sits far below every real tile and far above the failure, so it cannot fire on a
            # legitimately dark or low-contrast extraction.
            try:
                from PIL import Image, ImageStat
                _st = ImageStat.Stat(Image.open(p).convert("L"))
                if k in KNOWN_FLAT_ART:
                    continue        # named, reasoned, and re-checked by the test below
                self.assertGreater(
                    _st.stddev[0], 8.0,
                    "tz_%s.jpg has pixel stdev %.1f — that is a FLAT image, not art. Every real "
                    "tile measures 14-43. It will render as an empty grey box for every zone that "
                    "uses this key, and the byte-size floor above cannot catch it." % (k, _st.stddev[0]))
            except ImportError:
                pass          # no Pillow in this env — the size floor above still applies
            sizes.setdefault(n, []).append(k)
        dupes = {n: v for n, v in sizes.items() if len(v) > 1}
        self.assertEqual(dupes, {}, "byte-identical art files = the v497 placeholder bug: %s" % dupes)

    def test_the_live_rotation_vocabulary_is_covered(self):
        """The zones D2R actually served in the relay history, spelled the way it spells them."""
        info, _ = _tz_info()
        for z in ["Lost City", "Valley of Snakes", "Claw Viper Temple", "Glacial Trail",
                  "Drifter Cavern", "Travincal", "The Pit", "Worldstone Keep", "Blood Moor",
                  "Halls of Anguish", "Nihlathak's Temple", "Tal Rasha's Tombs", "Moo Moo Farm"]:
            self.assertIn(z, info, "%s is served by the rotation and has no entry" % z)


class TestTZTiering(unittest.TestCase):
    """The grey-out has to be DEFENSIBLE. Dimming a zone is advice, and wrong advice printed in
    confident type is worse than no advice."""

    def _tier(self, name, info, notable):
        den, lvl = info[name][0], info[name][1]
        if name in notable:
            return "prime"
        if not den:
            return "good"
        s = (den / 2200) * 0.85 + max(0, (lvl - 67) / 18) * 0.15
        return "prime" if s >= 0.5 else ("good" if s >= 0.28 else "thin")

    def _notable(self, src):
        m = re.search(r"var TZ_NOTABLE = \{(.*?)\};", src, re.S)
        assert m
        return set(re.findall(r"'((?:[^'\\]|\\.)*)'\s*:", m.group(1)))

    def test_travincal_is_never_greyed_out(self):
        """THE CASE THAT PROVES THE OVERRIDE IS NEEDED. Travincal has density 325 — among the
        lowest in the game — and is still a destination, because the Council is there. A purely
        density-driven ranking greys it out, and that is bad advice, not a cosmetic slip."""
        info, src = _tz_info()
        notable = self._notable(src)
        self.assertLess(info["Travincal"][0], 400, "if Travincal got dense, this test is stale")
        self.assertIn("Travincal", {n.replace("\\'", "'") for n in notable})
        self.assertEqual(self._tier("Travincal", info, {n.replace("\\'", "'") for n in notable}), "prime")

    def test_a_zero_density_row_is_missing_data_not_a_thin_zone(self):
        """Nihlathak's Temple carries MonDen(H)=0 in levels.txt because it is an entrance. Greying
        it would be the panel presenting an absent number as a low one."""
        info, src = _tz_info()
        notable = {n.replace("\\'", "'") for n in self._notable(src)}
        zero = [z for z, r in info.items() if r[0] == 0]
        self.assertTrue(zero, "expected at least one zero-density row")
        for z in zero:
            self.assertNotEqual(self._tier(z, info, notable), "thin",
                                "%s has NO density on record — that is missing data" % z)

    def test_the_tiers_actually_separate(self):
        """A ranking where everything lands in one bucket distinguishes nothing. He asked for a
        DISTINGUISHED difference; this is the check that there is one."""
        info, src = _tz_info()
        notable = {n.replace("\\'", "'") for n in self._notable(src)}
        tiers = [self._tier(z, info, notable) for z in info]
        for t in ("prime", "good", "thin"):
            self.assertGreaterEqual(tiers.count(t), 5,
                                    "only %d zones are %r — the tiering is not separating"
                                    % (tiers.count(t), t))

    def test_the_weakest_act1_zones_are_the_ones_greyed(self):
        """Sanity on direction: Blood Moor must never outrank Stony Tomb."""
        info, src = _tz_info()
        notable = {n.replace("\\'", "'") for n in self._notable(src)}
        self.assertEqual(self._tier("Blood Moor", info, notable), "thin")
        self.assertEqual(self._tier("Stony Tomb", info, notable), "prime")


class TestTZSplitter(unittest.TestCase):
    def test_the_and_stripper_is_present(self):
        """The regex fix, pinned at the source. The behaviour is proven in the browser spec; this
        catches someone 'simplifying' the two-step split back into the one-step version."""
        _, src = _tz_info()
        self.assertIn("replace(/^and\\s+/i, '')", src,
                      "the leading-'and' strip is gone — three-zone rotations will render a chip "
                      "labelled 'and <Zone>' again")

class TestBoardConsoleAgree(unittest.TestCase):
    """v1579 — the board and the console must tell Konyo the SAME thing about the same zone.

    TZ_INFO is duplicated into bible.html because the board is a single file that has to work from
    file:// with no server and no build step. Duplication that nobody checks is just a slower way of
    disagreeing, so this is the check: the two tables must be identical, and both surfaces must
    apply the same tier thresholds. If they ever drift, the push fails instead of Konyo finding two
    different verdicts for the same hour on two screens.
    """

    def _board(self):
        src = open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        m = re.search(r"var TZ_INFO = (\{.*?\});", src, re.S)
        self.assertTrue(m, "bible.html has no TZ_INFO — the board tracker lost its data")
        return json.loads(m.group(1)), src

    def test_the_two_tables_are_identical(self):
        console, _ = _tz_info()
        board, _ = self._board()
        self.assertEqual(board, console,
                         "bible.html and tv/control_ui.html disagree about the zones — one surface "
                         "would show art/density the other does not")

    def test_both_surfaces_use_the_same_thresholds(self):
        _, ui = _tz_info()
        _, board = self._board()
        for needle in ("(den / 2200) * 0.85", "0.5", "0.28"):
            self.assertIn(needle.replace(" ", ""), ui.replace(" ", ""),
                          "console lost the %r threshold" % needle)
        for needle in ("(den/2200)*0.85", "0.5", "0.28"):
            self.assertIn(needle.replace(" ", ""), board.replace(" ", ""),
                          "board lost the %r threshold" % needle)

    def test_both_surfaces_normalise_the_apostrophe(self):
        """Four zones carry an apostrophe and the names arrive as text from a web feed. A curly
        U+2019 misses the table, and the miss is SILENT — an emoji with no numbers reads as "we
        have nothing on this zone" rather than "the lookup failed". Found by my own test passing
        the curly form and getting tier 'unknown' back."""
        _, ui = _tz_info()
        _, board = self._board()
        for name, src in (("console", ui), ("board", board)):
            self.assertIn("\\u2019", src,
                          "%s does not normalise the typographic apostrophe" % name)

    def test_the_board_splits_the_rotation_into_zones(self):
        """The board used to hand the WHOLE rotation string to one card as if it were one zone."""
        _, board = self._board()
        self.assertIn("function tzSplitZones", board)
        self.assertIn("tzZonesHtml(data.current)", board,
                      "renderTzTracker must render the rotation as a LIST, not as one name")
        # Strip /* */ comments before the NEGATIVE check. The comment that explains this very bug
        # quotes the old call verbatim, so a naive assertNotIn matches the documentation and fails
        # on correct code — the same trap v1533 hit when its guard flagged its own docstring.
        code = re.sub(r"/\*.*?\*/", "", board, flags=re.S)
        self.assertNotIn("tzZoneRowHtml(data.current)", code,
                         "the single-card renderer is back — a three-zone hour will show one card")

class TestRotationCadence(unittest.TestCase):
    """v1581 — the countdown must match how often the zone actually turns.

    v1567 wrote "terror zones turn hourly" and counted to the top of the hour. The board's own
    tracker tab said "~30 MIN" for the next slot, so the two surfaces contradicted each other and
    only one could be right. The FEED settles it: its slots land on :00 and :30 with nothing in
    between, and across 93 adjacent half-hour pairs the zone changed in 90 of them. Hourly rotation
    would repeat about half of those; 3 of 93 is 3%.

    This was not cosmetic. At 15:09 the panel read 50:46 when the zone turned in 20 minutes — the
    number Konyo uses to decide whether there is time to start a run, overstating the window by up
    to half an hour.
    """

    def test_the_console_counts_to_the_half_hour(self):
        _, ui = _tz_info()
        self.assertIn("var SLOT_S = 1800", ui, "the slot length must be half an hour")
        self.assertNotIn("3600 - (now.getMinutes() * 60", ui,
                         "the hourly countdown is back — it overstates the window by up to 30 min")
        self.assertIn("(now.getMinutes() % 30)", ui)

    def test_the_label_does_not_promise_the_hour(self):
        _, ui = _tz_info()
        self.assertIn("on the hour and the half hour", ui,
                      "the clock label still claims an hourly turn")

    def test_the_two_surfaces_agree_on_cadence(self):
        """The board said 30 minutes while the console said 60. Whichever is right, they must not
        disagree — two screens showing different answers is worse than one wrong answer."""
        src = open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        self.assertIn("~30 MIN", src, "the board's next-slot label lost its cadence")
        _, ui = _tz_info()
        self.assertNotIn("turn hourly), ", ui.replace("\n", " "))

class TestHistoryRanking(unittest.TestCase):
    """v1584 — the 48-hour log ranks its windows, and by the RIGHT zone.

    Every past window rendered identically unless it happened to contain one of fourteen hardcoded
    bosses, so a Stony Tomb hour (density 2200) and a Blood Moor hour (520) were the same row, and
    the summary could read "0 huntable" over two days of excellent tomb rotations.

    A window is judged by its BEST zone — the one you would actually have gone to. An AVERAGE would
    let a bad window that happened to include one good area look mediocre instead of worth running,
    and would let a good one be dragged down by filler it shares the hour with.
    """

    def _board(self):
        return open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()

    def test_the_log_splits_and_ranks_by_the_best_zone(self):
        src = self._board()
        self.assertIn("tzSplitZones(h.zone)", src, "the log must split the rotation, not match the string")
        self.assertIn("ORDER[b2.t.tier]", src, "windows must be ordered by tier")
        self.assertIn("tzt-h-", src, "rows must carry their tier")

    def test_the_summary_counts_prime_not_the_boss_list(self):
        src = self._board()
        self.assertIn("worth running", src)
        self.assertNotIn("' huntable'", src,
                         "the old count is back — it reports 0 for a log full of density-2200 hours")

    def test_a_zero_density_window_is_not_dimmed(self):
        """Same rule as the live cards: no density on record is MISSING DATA, not a thin window."""
        src = self._board()
        self.assertIn("if (!den) return { tier:'good'", src.replace(" ", " "),
                      "tzTier must still treat den 0 as good, which keeps its log row lit")

class TestTierSeparation(unittest.TestCase):
    """v1585 — three tiers must have THREE treatments, and a sparse zone must not be rescued by its
    base level.

    Konyo, looking at Outer Steppes and Plains of Despair at full brightness: "when its a real
    terror zone is emphasized correct? like these dont look greyed out... i want a distinguished
    difference between the real tz zones worth farming compared to the not."

    He was right, and the cause was measurable: 38 of the 67 zones were 'good', and 'good' rendered
    exactly like PRIME minus a badge. 57% of the rotation looked emphasised, which means nothing
    did. The middle tier now reads as middle.

    And the level term was rescuing sparse zones. Burial Grounds and Blood Moor are BOTH density
    520; only their base level (80 vs 67) separated them — the exact number a terror zone overrides
    by lifting monsters to the player's level. A density floor settles it.
    """

    def _tier(self, z, info, notable):
        den, lvl = info[z][0], info[z][1]
        if z in notable:
            return "prime"
        if not den:
            return "good"
        if den < 600:
            return "thin"
        s = (den / 2200) * 0.85 + max(0, (lvl - 67) / 18) * 0.15
        return "prime" if s >= 0.5 else ("good" if s >= 0.28 else "thin")

    def _notable(self, src):
        m = re.search(r"var TZ_NOTABLE = \{(.*?)\};", src, re.S)
        return {n.replace("\\'", "'") for n in re.findall(r"'((?:[^'\\]|\\.)*)'\s*:", m.group(1))}

    def test_two_zones_at_the_same_density_get_the_same_verdict(self):
        info, src = _tz_info()
        notable = self._notable(src)
        self.assertEqual(info["Burial Grounds"][0], info["Blood Moor"][0],
                         "if these stop sharing a density this test is stale")
        self.assertEqual(self._tier("Burial Grounds", info, notable),
                         self._tier("Blood Moor", info, notable),
                         "same density, different verdict — the base level is deciding, and a "
                         "terror zone overrides exactly that")

    def test_the_density_floor_is_in_both_surfaces(self):
        _, ui = _tz_info()
        board = open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        self.assertIn("den < 600", ui, "console lost the density floor")
        self.assertIn("den < 600", board, "board lost the density floor")

    def test_the_middle_tier_is_visually_distinct_from_prime(self):
        """The whole complaint. 'good' must not render like PRIME minus a badge."""
        _, ui = _tz_info()
        board = open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        self.assertIn(".tzz-good", ui, "the console has no middle-tier treatment")
        self.assertIn("tzt-t-good{", board, "the board has no middle-tier treatment")
        for name, src in (("console", ui), ("board", board)):
            self.assertIn("saturate(.5", src.replace("0.5", ".5"),
                          "%s: the middle tier is not desaturated" % name)

    def test_prime_is_not_the_majority(self):
        """If most of the rotation is emphasised, nothing is."""
        info, src = _tz_info()
        notable = self._notable(src)
        tiers = [self._tier(z, info, notable) for z in info]
        self.assertLess(tiers.count("prime"), len(tiers) * 0.45,
                        "PRIME has grown to most of the map — emphasis that common is not emphasis")
        self.assertGreaterEqual(tiers.count("thin"), 10,
                                "almost nothing dims; the weak zones should be visibly weak")

    def test_an_unpublished_next_window_says_so(self):
        """The upstream really returns next:"" for part of every slot. "(unknown)" was true and read
        like a broken panel."""
        _, ui = _tz_info()
        board = open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        self.assertIn("not published yet", ui, "console still says (unknown) for an absent next")
        self.assertIn("not published yet", board, "board still says (unknown) for an absent next")

class TestPanelAlignmentAndPolling(unittest.TestCase):
    """v1586-87 — three things Konyo saw that the panel should have said or done itself.

    "why are they not aligned? the next and live?" — auto-fit sized each row to its OWN item count,
    so a 2-zone LIVE NOW made two 50% columns while a 3-zone UP NEXT made three 33% ones and no card
    lined up with the card above it. Both rows share one column count now.

    "the LIVE NOW is rendering two of the separted tz zones?? maybe theres a mistake here?" — there
    is no mistake, and that is exactly why it had to change. A terror zone in D2R is a GROUP of
    connected areas terrorised together for one window: across the last 95 windows of his own feed,
    30 had one area, 43 had two, 21 had three and one had four. Two cards side by side with nothing
    saying they are concurrent reads like the half hour split in two.

    "i want it to be greyed out really.. so its known" — THIN is now full grayscale at .3, so it
    never has to be compared against a neighbour to be recognised.
    """

    def test_both_rows_share_one_column_count(self):
        _, ui = _tz_info()
        self.assertIn("--tz-cols", ui, "the shared column count is gone")
        self.assertIn("repeat(var(--tz-cols", ui)
        self.assertIn("Math.max(1, _count(d.current), _count(d.next))", ui,
                      "the column count must span BOTH rows or they cannot align")

    def test_a_multi_zone_window_says_the_zones_are_concurrent(self):
        _, ui = _tz_info()
        board = open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
        self.assertIn("terrorised together", ui, "console does not say the zones are simultaneous")
        self.assertIn("terrorised together", board, "board does not say the zones are simultaneous")

    def test_thin_is_unmistakable_not_merely_dimmer(self):
        _, ui = _tz_info()
        self.assertIn("grayscale(1)", ui, "THIN is not fully desaturated")
        m = re.search(r"\.tzz-thin \{ opacity: ([\d.]+)", ui)
        self.assertTrue(m, "the THIN opacity rule is gone")
        thin = float(m.group(1))
        g = re.search(r"\.tzz-good \{ opacity: ([\d.]+)", ui)
        good = float(g.group(1))
        self.assertLess(thin, good - 0.3,
                        "THIN (%.2f) is not far enough below FINE (%.2f) to be read without "
                        "comparing them" % (thin, good))

    def test_the_lean_in_is_actually_re_armed(self):
        """v1586 shipped this DEAD: _tzNextMissing was set inside the fetch, but _tzSchedule() only
        ran once at wire time, so it read the flag before any fetch had set it and the cadence
        stayed 120s forever. Its own test caught it — two fetches before, two after 63 seconds.
        Same shape as the v1570 redo: a slot written, read and cleared, with nothing re-arming."""
        _, ui = _tz_info()
        self.assertIn("if (wasMissing !== _tzNextMissing", ui,
                      "nothing re-schedules when the cadence changes — the lean-in is dead again")
        self.assertIn("_tzNextMissing ? 60000 : 120000", ui)

class TestLockedVsRoutable(unittest.TestCase):
    """v1588 — the verdict is an AFFORDANCE, not a paragraph.

    v1580 answered "why is this dimmed" with a standfirst that spelled the ranking out. Konyo:
    "i dont want this desription here.. no description needed for it.. should be visually logicaly
    and visually rendering this in greyed out and like not clickable even so its locked kinda
    feeling.. and for the real TZ ZONEs clickable and routable."

    He is right that a panel explaining itself in prose is a panel whose visuals are not doing the
    work. A zone worth the window is a button — pointer, lift, and it routes to the tracker. A thin
    one has no handler at all, a not-allowed cursor and a padlock. He meets the difference with the
    mouse before he reads anything, and the numbers stay on every card so the basis is still there
    without the lecture.
    """

    def test_the_explanatory_standfirst_is_gone(self):
        _, ui = _tz_info()
        self.assertNotIn('class="tz-standfirst"', ui,
                         "the prose legend is back — the treatment should be carrying this")

    def test_every_zone_routes_and_thin_still_reads_thin(self):
        """v1801 — INVERTED, deliberately, and the old assertion is described rather than deleted.

        v1588 made a thin zone inert (no handler, aria-disabled, a padlock) and this pinned it.
        That held while 15 of 66 zones were thin. v1801 drops the level term from both tzTiers —
        v1585 had already diagnosed it as meaningless, since terror lifts any TZ area to mlvl 96 —
        which takes thin to 40 of 66. Konyo, asked directly, chose greyed-and-cancelled but still
        clickable: a lock over most of the map punishes him for a ranking instead of reporting one.

        So what must survive is the VERDICT (the grey, the tag, the wording) and what must go is
        the DEAD HANDLER. Both halves are asserted, because the easy way to get this wrong is to
        unlock the card and let it stop looking thin."""
        _, ui = _tz_info()
        code = _strip_comments(ui)
        self.assertFalse("var dead = (t.tier === 'thin')" in code,
                         "the inert branch is back — thin zones stopped routing")
        self.assertFalse(".tzz-locked { cursor: not-allowed" in code,
                         "the lock styling returned with no emitter, or the lock itself did")
        self.assertIn("window._tzRoute()", ui, "a card must route somewhere")
        self.assertIn("window._tzRoute = function", ui, "the router the cards call must EXIST — a "
                      "handler with no function behind it is the v1570 shape again")
        # the verdict is untouched: thin is still greyed to .3 and fully desaturated
        self.assertIn(".tzz-thin { opacity: .3", ui, "thin stopped being greyed")
        self.assertIn("grayscale(1)", ui, "thin stopped being desaturated")

    def test_the_board_unlocks_its_thin_zones_the_same_way(self):
        """The ranking is one fact; which file renders it is not a reason for two answers. The board
        kept its padlock for a few minutes after the console lost one, which is [[copy-drift]]."""
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8") as fh:
            board = _strip_comments(fh.read())
        # assertFalse, not assertNotIn: assertNotIn prints the whole 5MB container on failure.
        self.assertFalse("tzt-locked" in board, "the board still locks what the console now routes")
        self.assertFalse(".tzt-lock{" in board, "the padlock styling outlived its emitter")

    def test_both_surfaces_rank_a_zone_the_same_way(self):
        """THE ONE THAT MATTERS. bible.html and tv/control_ui.html each carry their own tzTier over
        one shared TZ_INFO. v1801 removed the level term from the console first, and for a few
        minutes Ancient's Way (den 650, lvl 82) scored 0.376 GOOD on the board and 0.251 THIN in
        the console — same rotation, two verdicts, two screens he reads. Pinned as: NEITHER
        formula may consult the level."""
        with open(os.path.join(REPO, "bible.html"), encoding="utf-8") as fh:
            board = fh.read()
        _, ui = _tz_info()
        self.assertIn("const s = (den/2200)*0.85;", board,
                      "the board's tier formula changed shape — re-check it against the console's")
        self.assertIn("var s = (den / 2200) * 0.85;", ui,
                      "the console's tier formula changed shape — re-check it against the board's")
        for src, who in ((board, "board"), (ui, "console")):
            i = src.find("(den/2200)*0.85;") if who == "board" else src.find("(den / 2200) * 0.85;")
            self.assertNotIn("lvl - 67", src[i:i + 200], "%s reintroduced the level term" % who)
            self.assertNotIn("lvl-67", src[i:i + 200], "%s reintroduced the level term" % who)

class TestSessionsOnly(unittest.TestCase):
    """v1589 — the rotation card lives in ONE place. Konyo: "remove it completely from TV-D tab..
    i want it only in sessions". It was rendering 419px tall in the cockpit too, where the job is
    the live feed and a rotation clock is someone else's business."""

    def test_hidden_outside_the_sessions_view(self):
        _, ui = _tz_info()
        self.assertIn(".hd-tz { display: none; }", ui, "the card is visible everywhere again")
        self.assertIn('body[data-view="sessions"] .hd-tz { display: block;', ui)

    def test_it_does_not_poll_while_off_screen(self):
        """Polling for a panel nobody can see is the background chatter he has complained about."""
        _, ui = _tz_info()
        self.assertIn("if (_tzOnScreen()) _tzFetch();", ui, "the off-screen guard is gone")
        self.assertIn("function _tzOnScreen()", ui, "the guard calls a function that must EXIST")

    def test_entering_sessions_refreshes_it(self):
        """It stops polling off screen, so without this he would open Sessions to whatever was true
        when he last looked."""
        _, ui = _tz_info()
        self.assertIn("window._tzRefresh = function", ui,
                      "the refresh the view-switch calls must exist — a call with no function "
                      "behind it is the v1570 shape again")
        self.assertIn("window._tzRefresh()", ui, "showSessions must actually call it")


class TestKnownBadArtStaysNamedAndSmall(unittest.TestCase):
    """An exception list is only honest while it is short and every entry says why.

    This is the half that makes KNOWN_FLAT_ART a debt rather than a hiding place: it fails if the
    list grows past a couple of entries, if an entry has no real reason written against it, or if
    an entry names a key that no longer exists (a stale excuse outliving its bug).
    """

    def test_every_exception_carries_a_real_reason(self):
        for k, why in KNOWN_FLAT_ART.items():
            self.assertGreater(len(str(why).strip()), 80,
                               "%s is excused with no explanation — say what is wrong and how to "
                               "fix it, or fix it" % k)
            self.assertIn("TO FIX", str(why),
                          "%s must say how to fix it, or it is not a debt, it is a shrug" % k)

    def test_the_list_does_not_become_a_dumping_ground(self):
        self.assertLessEqual(len(KNOWN_FLAT_ART), 2,
                             "more than two tiles excused at once means the extraction pass broke, "
                             "not that individual files are unlucky: %s" % sorted(KNOWN_FLAT_ART))

    def test_no_exception_outlives_its_file(self):
        info, _ = _tz_info()
        keys = {row[2] for row in info.values()}
        for k in KNOWN_FLAT_ART:
            self.assertIn(k, keys,
                          "%s is excused but no zone uses that art key any more — delete the "
                          "exception" % k)

class TestHandReplacedIconsAreNotReExtracted(unittest.TestCase):
    """v1751 — the extractor must not overwrite the six icons v1671 replaced by hand.

    v1671 swapped all six ui_tab_*.png in place and said so: "a PURE FILE SWAP... zero code
    touched." Zero code touched left extract_ui_icons.py still pointing every tab_* role at the
    quest medallion it was originally pulled from, ending in an unconditional im.save(out). A full
    re-run to add ONE new icon would have reverted all six, and nothing would have said so: the
    ui_icons gate runs `--check`, which tests only that a file EXISTS, and a reverted file exists.

    Found by asking a different model family what the pictures DEPICT, with no hint. It said "an
    off-white circle/ring" and "a green square with a blocky pattern" where the code claimed The
    Seven Tombs and The Golden Bird. [[label-outlived-referent]]
    """

    def setUp(self):
        sys.path.insert(0, HERE)
        import extract_ui_icons
        self.X = extract_ui_icons

    def test_every_superseded_role_is_refused_by_the_extractor(self):
        refused = set(self.X.ICONS) - set(self.X.roles_to_extract())
        self.assertEqual(refused, set(self.X.SUPERSEDED),
                         "the write loop no longer refuses exactly the hand-replaced icons")
        # non-vacuity: a SUPERSEDED that named nothing would pass the line above trivially
        self.assertEqual(len(self.X.SUPERSEDED), 6,
                         "v1671 replaced six icons; SUPERSEDED names %d" % len(self.X.SUPERSEDED))

    def test_a_superseded_name_that_is_not_an_icons_role_is_a_typo_not_a_guard(self):
        """A role spelled wrong here refuses nothing and reads exactly like protection."""
        stray = sorted(set(self.X.SUPERSEDED) - set(self.X.ICONS))
        self.assertEqual(stray, [],
                         "SUPERSEDED names roles ICONS does not have, so they guard nothing: %s"
                         % ", ".join(stray))

    def test_the_refused_icons_are_actually_on_disk(self):
        """Refusing to re-pull a file only helps while the file is there to keep."""
        art = os.path.join(os.path.dirname(HERE), "art")
        for role in sorted(self.X.SUPERSEDED):
            p = os.path.join(art, "ui_%s.png" % role)
            self.assertTrue(os.path.exists(p) and os.path.getsize(p) > 200,
                            "%s is refused by the extractor but is missing from art/" % role)


if __name__ == "__main__":
    unittest.main(verbosity=2)
