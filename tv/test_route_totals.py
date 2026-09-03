"""v2484 — ONE TAB, ONE NUMBER, ON EVERY SURFACE THAT PRINTS IT.

⚠⚠ THE DEFECT, AS HE SAW IT. The heart drew three route sets and each read a different producer:

    tab            chronicle routes   fleet lanes   roster routes
    runeword(s)         105                99            99
    set(s)              135               135           135
    unique(s)           398               403           403

Every number was right. chronicle_routes read a roster ARTIFACT — a file of name strings — while
the other two read the chronicle. Konyo: "sync and match them obivously.. no reason to have this
gap". So all three now quote tv/route_totals.py.

⚠ NO TEST IN THIS FILE MAY NAME 99, 135 OR 403. A gate pinned to a number is the next label that
outlives its referent — and this repo has the scar. These assert the LAWS: that the three agree,
that they all move when the producer moves, that a divergence is said out loud, and that an
unreadable producer is UNKNOWN rather than zero. The rosters and the rulings stay free to change.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

import chronicle_routes as CR  # noqa: E402
import fleet_routes as FR  # noqa: E402
import roster_routes as RR  # noqa: E402
import route_totals as RT  # noqa: E402

KEYS = ("runeword", "set", "unique")


def _rows(mod, tally=None):
    """Every route set's rows, whichever signature it takes. -> [dict]

    ⚠ ALL THREE RETURN A REPORT DICT, NOT A LIST. The first cut iterated the return value directly
    and got the dict's KEYS — strings — which failed with 'str has no attribute get'. A loop over
    the wrong shape that happens not to crash is how a guard silently checks nothing, so this digs
    out `routes` explicitly and refuses anything else.
    """
    try:
        rep = mod.routes(tally) if tally is not None else mod.routes()
    except TypeError:
        rep = mod.routes()
    if isinstance(rep, dict):
        rep = rep.get("routes") or []
    assert isinstance(rep, (list, tuple)), "routes() gave %r, not a list of rows" % type(rep)
    return [r for r in rep if isinstance(r, dict)]


class L1_OneProducer(unittest.TestCase):

    def test_all_three_route_sets_print_the_producers_number(self):
        for key in KEYS:
            want = RT.total(key)
            self.assertIsNotNone(want, "the producer cannot read %r at all" % key)
        for mod, name in ((CR, "chronicle_routes"), (FR, "fleet_routes"), (RR, "roster_routes")):
            for r in _rows(mod):
                k = RT.canonical(r.get("key"))
                if not k:
                    continue
                self.assertEqual(
                    r.get("count"), RT.total(k),
                    "%s prints %r for %r; the producer says %r. Three surfaces reading three "
                    "producers is the defect this file exists for — the panel showed 105/99/99 "
                    "for one tab and every number was right."
                    % (name, r.get("count"), r.get("key"), RT.total(k)))

    def test_the_unit_word_is_the_same_on_every_surface(self):
        """L4 — they count the same thing now, so a different word on one is the old bug in prose."""
        seen = {}
        for mod, name in ((CR, "chronicle_routes"), (FR, "fleet_routes"), (RR, "roster_routes")):
            for r in _rows(mod):
                k = RT.canonical(r.get("key"))
                if not k:
                    continue
                noun = r.get("noun")
                self.assertTrue(
                    noun, "%s sends no unit for %r, so the surface must invent one" % (name, k))
                seen.setdefault(k, {})[name] = noun
        for k, by in seen.items():
            self.assertEqual(
                len(set(by.values())), 1,
                "the surfaces disagree on what %r is counted IN: %r. They print the same number "
                "now, so a different noun is the same defect wearing prose." % (k, by))


class L2_TheProducerMovesAllThree(unittest.TestCase):
    """⚠ THE ONLY TEST HERE THAT CAN PROVE THE JOIN. Equality today could be a coincidence — three
    readers that happen to agree is exactly what SETS looked like before this change, and it was
    not a model to copy. Move the producer and watch all three follow."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rt-bible-")
        self.copy = os.path.join(self.tmp, "bible.html")
        shutil.copyfile(RT.BIBLE, self.copy)
        self._real = RT.BIBLE

    def tearDown(self):
        RT.BIBLE = self._real
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _bump(self, old, new):
        s = io.open(self.copy, encoding="utf-8").read()
        n = s.count(old)
        # PRINT THE MATCH COUNT — a sabotage that matched nothing proves nothing, and this repo
        # has burned a day on exactly that.
        self.assertEqual(n, 1, "the mutation anchor %r matched %d times, so this test would have "
                              "proven nothing" % (old[:50], n))
        io.open(self.copy, "w", encoding="utf-8").write(s.replace(old, new, 1))
        RT.BIBLE = self.copy
        # ⚠ AND DROP THE ROW CACHES. This redirects a module POINTER, which no real edit does — a
        # real edit touches bible.html and moves its mtime, which IS in _source_key(). My first
        # version of this test skipped that and read a cached 99 against a producer saying 106,
        # then blamed the join. The code was right and the instrument was wrong. Clearing the memo
        # keeps this test about the LAW (do the three follow the producer) instead of about the
        # cache, which the next test checks separately. [[feedback-suspect-the-instrument]]
        for mod in (CR, FR, RR):
            memo = getattr(mod, "_MEMO", None)
            if isinstance(memo, dict):
                memo["key"] = None
                memo["val"] = None

    def test_moving_the_runeword_ruling_moves_every_surface(self):
        before = RT.total("runeword")
        self.assertIsNotNone(before)
        import re
        m = re.search(r"var\s+RUNEWORD_CHRONICLE_TOTAL\s*=\s*(\d+)\s*;",
                      io.open(self.copy, encoding="utf-8").read())
        self._bump("var RUNEWORD_CHRONICLE_TOTAL = %s;" % m.group(1),
                   "var RUNEWORD_CHRONICLE_TOTAL = %d;" % (int(m.group(1)) + 7))
        after = RT.total("runeword")
        self.assertEqual(after, before + 7, "the producer did not follow its own declaration")
        for mod, name in ((CR, "chronicle_routes"), (FR, "fleet_routes"), (RR, "roster_routes")):
            for r in _rows(mod):
                if RT.canonical(r.get("key")) == "runeword":
                    self.assertEqual(
                        r.get("count"), after,
                        "%s did not follow the producer — it is still reading its own source, so "
                        "the three agreeing today is a coincidence, not a join" % name)

    def test_an_unreadable_producer_is_UNKNOWN_not_zero(self):
        """L8 — nobody-looked and measured-zero are different facts, all the way to the screen."""
        RT.BIBLE = os.path.join(self.tmp, "does-not-exist.html")
        for key in KEYS:
            self.assertIsNone(
                RT.total(key),
                "%r came back as a number with no source to read. A default here renders as a "
                "total and nothing on screen would say nobody looked." % key)


class TheCacheKeyCoversTheProducersSource(unittest.TestCase):
    """⚠ A CACHE KEYED ON LESS THAN IT READS SERVES A STALE NUMBER AND LOOKS HEALTHY.

    The rows are memoised on `_source_key()`. The counts now come from bible.html, so an edit to
    bible.html MUST move that key — otherwise changing his ruling would leave the panel showing
    the old total until something unrelated was touched. This repo already has that scar: a cache
    whose key omitted one of its inputs.
    """

    def test_bible_html_is_part_of_every_row_cache_key(self):
        import inspect
        for mod, name in ((CR, "chronicle_routes"), (FR, "fleet_routes"), (RR, "roster_routes")):
            fn = getattr(mod, "_source_key", None)
            if fn is None:
                continue          # a module with no cache cannot serve a stale one
            src = inspect.getsource(fn)
            self.assertIn(
                "BIBLE", src,
                "%s memoises its rows but its cache key does not read BIBLE, which is where the "
                "counts now come from. Editing the ruling would not invalidate the cache and the "
                "panel would keep printing the old number." % name)

    def test_touching_bible_moves_the_key(self):
        """⚠ ALL THREE, not just the first. Measured when this was written: chronicle_routes
        followed and fleet_routes and roster_routes did NOT — same lossy `max()` digest, same
        blind spot, and checking only one module would have shipped two of them still broken."""
        for mod, name in ((CR, "chronicle_routes"), (FR, "fleet_routes"), (RR, "roster_routes")):
            fn = getattr(mod, "_source_key", None)
            if fn is None:
                continue
            bib = getattr(mod, "BIBLE", None)
            if not bib or not os.path.isfile(bib):
                continue
            before = fn()
            self.assertIsNotNone(before, "%s: the key is unreadable, so nothing is cached" % name)
            st = os.stat(bib)
            os.utime(bib, (st.st_atime, st.st_mtime + 5))
            try:
                self.assertNotEqual(
                    before, fn(),
                    "%s: touching bible.html did not move the cache key, so a change to his "
                    "ruling would not invalidate the cached rows" % name)
            finally:
                os.utime(bib, (st.st_atime, st.st_mtime))


class L3_DivergenceIsLoud(unittest.TestCase):

    def test_a_lane_that_disagrees_raises_a_flag_naming_BOTH_numbers(self):
        ruled = RT.total("unique")
        self.assertIsNotNone(ruled)
        rows = [{"key": "unique", "boardCount": ruled + 5}]
        flags = RT.disagreements(rows)
        self.assertEqual(len(flags), 1, "a lane read a different number and nothing was said")
        say = flags[0]["say"]
        self.assertIn(str(ruled), say, "the flag does not name the chronicle number")
        self.assertIn(str(ruled + 5), say, "the flag does not name the number the lane read — a "
                                           "divergence that hides the loser is the old bug")

    def test_agreement_raises_nothing(self):
        ruled = RT.total("set")
        self.assertEqual(RT.disagreements([{"key": "set", "boardCount": ruled}]), [])

    def test_a_lane_that_never_read_is_not_a_disagreement(self):
        """None is nobody-looked. Flagging it would teach him to ignore the flag."""
        self.assertEqual(RT.disagreements([{"key": "set", "boardCount": None}]), [])


class TheProducerReadsItsOwnReach(unittest.TestCase):

    def test_the_set_walk_refuses_rather_than_returning_a_short_count(self):
        """⚠ IT ONCE RETURNED 81 INSTEAD OF 135 AND LOOKED ENTIRELY PLAUSIBLE.

        Two of the three set declarations write `pieces:[...]` and the third writes
        `"pieces": [...]`. A bare pattern found 12 arrays, then 7, then ZERO — and returned a
        confident 81. Nothing was broken; the scan had silently stopped seeing one of its three
        inputs. The count was the tell. [[source-reading-guard]]
        """
        s = io.open(RT.BIBLE, encoding="utf-8").read()
        for decl in ("ITEM_SETS", "SET_PIECES_EXTRA", "SET_PIECES_EXTRA2"):
            self.assertIn(decl, s, "%s is gone; the set total is reading fewer inputs than it "
                                   "thinks" % decl)
        import re
        total = RT.set_pieces(s)
        self.assertIsNotNone(total)
        # every declaration must contribute — a source that yields nothing is the 81 defect
        for decl in ("ITEM_SETS", "SET_PIECES_EXTRA", "SET_PIECES_EXTRA2"):
            m = re.search(r"(?:const|var|let)\s+%s\s*=\s*\[" % decl, s)
            blk = RT._balanced(s, m.end() - 1, "[", "]")
            self.assertIsNotNone(blk, "%s never balanced — the walk ran past its own array" % decl)
            arrays = len(re.findall(r"[\"']?pieces[\"']?\s*:\s*\[", blk))
            self.assertGreater(
                arrays, 0,
                "%s contributed ZERO piece arrays. Either it changed shape or the pattern stopped "
                "matching it, and the total is short by however much it holds." % decl)

    def test_a_truncated_source_does_not_yield_a_confident_number(self):
        s = io.open(RT.BIBLE, encoding="utf-8").read()
        i = s.index("const ITEM_SETS")
        self.assertIsNone(
            RT.set_pieces(s[:i + 200]),
            "a source cut off mid-array still produced a count. A walk that does not assert on "
            "its own reach reports the part it happened to see.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
