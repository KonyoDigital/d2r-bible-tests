# -*- coding: utf-8 -*-
"""v3344 (#81) — THE SHELF SAYS WHAT IS OWED, NOT WHO OWNS IT.

The shelf sentence read, on his live console:

    3 waiting on a lane (vault: 3)

It grouped owed reels by the LANE THAT OWNS them and then printed the word WAITING — a question the
ownership map cannot answer. shelf_driver.py states the split in its own comment:

    OWED_BY      -> WHICH LANE owns this reel   (what the panel reports as waiting)
    READ_CLEARS  -> can a READ clear it         (what the sweeper is allowed to pay for)

`rows-not-banked` is the proof they are different questions. v2878 deliberately kept it OUT of
READ_CLEARS — it is owed a BANK, not a READ; "queuing it spends his money and clears nothing, the
hold does not clear, and the reel is retired as still owed having banked nothing" — so NO lane pass
will ever clear it. The screen filed it under "waiting on a lane" with the other four anyway.

⚠⚠ AND THREE INDEPENDENT PROSE SITES ALREADY SAID SO. Only the rendered sentence disagreed:
  1. control_app.reel_census's own docstring — "panels-never-banked  3  the VAULT still owes a bank"
  2. test_the_shelf_tabs_are_the_real_sessions, three lines above the assertion that pinned the old
     wording — "3 the vault still owes a BANK"
  3. shelf_driver's v2878 note — "what is missing is a durable BANK"
Every author who described this population got it right in prose and shipped a different word to the
screen. [[feedback-comments-vs-code]] with the roles reversed: here the PROSE was correct.

THE ROOT — the tag was READ, used to look up the lane, and then DISCARDED:
    tag  = (_r or {}).get("tag")
    lane = _owed_by[tag]
    out["owedBy"][lane] = ... + 1        # and nothing kept `tag`
so the screen could name WHICH LANE owns a reel and never WHICH OF FIVE CONDITIONS it is in. The
richer fact was in hand at the moment of the write, where keeping it is free.
[[one-to-one-store-for-a-one-to-many-fact]] [[heart-first]] §6

MEASURED on his tree after the fix — the sentence now reads:
    19 reel(s) on disk = 8 he sees + 8 hidden fixture(s) the suite opens by name
                       + 3 still owed (3 panels on film, nothing banked)
⚠ `owedBy` is KEPT. Ownership is a real question and existing laws pin it; this adds the tag beside
it rather than replacing it. And `out["owed"]` still counts all five tags, so the reconciliation
still sums. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import shelf_driver as SD  # noqa: E402


def _code(path):
    with io.open(path, encoding="utf-8") as fh:
        raw = fh.read()
    return "\n".join(re.sub(r"#.*$", "", l) for l in raw.split("\n"))


class TestTheShelfSaysWhatIsOwedNotWhoOwnsIt(unittest.TestCase):

    # ── the wording map ───────────────────────────────────────────────────────────────────────
    def test_every_owed_tag_has_words_of_its_own(self):
        """A tag with no entry falls through to its raw slug on his screen."""
        missing = [t for t in SD.OWED_BY if t not in SD.OWED_SAYS]
        self.assertEqual(
            missing, [],
            "%d owed tag(s) have no wording and would print as a bare slug: %s. OWED_SAYS sits "
            "beside OWED_BY so a tag added to one is obviously missing from the other."
            % (len(missing), ", ".join(missing)))

    def test_a_tag_a_read_cannot_clear_is_not_described_as_waiting_on_a_lane(self):
        """⚠⚠ THE ONE THAT MATTERS, and it is LATENT on his tree — 0 such reels today. A law that
        only checked today's population would pass over the exact case this exists for."""
        cannot = [t for t in SD.OWED_BY if t not in SD.READ_CLEARS]
        self.assertTrue(
            cannot,
            "no owed tag is excluded from READ_CLEARS — this law is vacuous. v2878 put "
            "rows-not-banked outside it deliberately; if that is gone, the distinction this law "
            "pins no longer exists. [[regression-guard]] §5")
        for t in cannot:
            says = SD.OWED_SAYS.get(t, "")
            self.assertNotIn(
                "waiting on a lane", says,
                "%r is owed something NO READ CAN CLEAR, and its wording still says it is waiting "
                "on a lane. That sentence can never come true for it." % t)
            self.assertIn(
                "bank", says.lower(),
                "%r is outside READ_CLEARS because it is owed a BANK rather than a read (v2878), "
                "and its wording does not say so: %r" % (t, says))

    # ── the engine keeps the tag ──────────────────────────────────────────────────────────────
    def test_the_census_keeps_the_tag_not_only_the_lane(self):
        """BEHAVIOURAL, against his real reels."""
        import control_app as ca
        c = ca.reel_census()
        if not c.get("ok"):
            self.skipTest("reel_census could not run here: %s" % (c.get("why") or "no reason"))
        self.assertIn("owedTags", c, "the census no longer carries owedTags, so the screen is back "
                                     "to knowing only which lane owns a reel")
        if c.get("owed"):
            self.assertTrue(
                c["owedTags"],
                "%d reel(s) are owed and owedTags is empty — the tag is being read and thrown away "
                "again, which is the whole defect." % c["owed"])

    def test_the_parts_still_sum(self):
        """⚠ owed must keep counting ALL five tags, or the reconciliation stops adding up and the
        header is dropped entirely — worse than a wrong word."""
        import control_app as ca
        c = ca.reel_census()
        if not c.get("ok"):
            self.skipTest("reel_census could not run here")
        self.assertEqual(
            sum(c["owedTags"].values()), c["owed"],
            "owedTags sums to %d but owed is %d — a per-tag breakdown that does not add up to its "
            "own total is exactly the authoritative-and-wrong number the header refuses to print."
            % (sum(c["owedTags"].values()), c["owed"]))

    def test_the_writer_keeps_the_tag_where_his_footage_is_absent(self):
        """⚠⚠ THE BEHAVIOURAL CASES ABOVE GO QUIET WITHOUT HIS REELS, and that is not hypothetical:
        red-proof 0 came back BLIND with a CORRECT match count of 1. heart2 proves inside a
        safe_copy sandbox which EXCLUDES `frames`, so reel_retention.plan() finds nothing, `owed` is
        0, and `if c.get("owed")` never reaches its assertion. A CI runner is the same — which is
        exactly the population of reds measured on #99. So the writer is pinned STRUCTURALLY here,
        where no footage is needed for the law to mean something.
        [[regression-guard]] §3 (a test that needs his machine runs nowhere else) and §5 (a case
        that cannot fail in the fixture's absence is measuring the fixture)."""
        code = _code(os.path.join(HERE, "control_app.py"))
        self.assertIn(
            'out["owedTags"][str(tag)]', code,
            "the census no longer writes the TAG beside the lane. It is read one line above and "
            "used to look up the lane, so discarding it is free to do and impossible to notice: "
            "the screen goes back to naming WHICH LANE owns a reel and never which of five "
            "conditions it is in. Comments stripped first, because the note explaining this fix "
            "quotes the very expression. [[one-to-one-store-for-a-one-to-many-fact]]")

    # ── one source, and it reaches the screen ─────────────────────────────────────────────────
    def test_the_wording_is_not_hand_copied_into_the_engine(self):
        """[[copy-drift]] — a private copy is how the two disagree the day a tag is added."""
        code = _code(os.path.join(HERE, "control_app.py"))
        self.assertIn(
            "OWED_SAYS", code,
            "control_app no longer reads shelf_driver.OWED_SAYS, so the wording has been copied or "
            "re-invented somewhere it can drift from the map it describes.")

    def test_neither_surface_says_waiting_on_a_lane_any_more(self):
        """The engine and the screen print one sentence; both must have moved."""
        code = _code(os.path.join(HERE, "control_app.py"))
        self.assertNotIn(
            "waiting on a lane", code,
            "the ENGINE still builds the old sentence. Comments are stripped first, because the "
            "note explaining this fix necessarily quotes the banned phrase. [[REG-1070]]")
        ui = _code(os.path.join(HERE, "control_ui.html"))
        self.assertNotIn(
            "' waiting on a lane'", ui,
            "the SCREEN still renders the old sentence, so the engine and the page would disagree "
            "about the same reels. [[the-unjoined-end]]")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "throwing the tag away again leaves the screen naming the owner and never the condition",
        "file": "tv/control_app.py",
        "find": '            out["owedTags"][str(tag)] = out["owedTags"].get(str(tag), 0) + 1',
        "replace": '            pass',
        "matches": 1,
    },
    {
        "why": "restoring the lane sentence puts the READ_CLEARS question back on the OWED_BY map",
        "file": "tv/control_app.py",
        "find": '        _bits.append("%d still owed (%s)" % (out["owed"], ", ".join(_parts)))',
        "replace": '        _bits.append("%d waiting on a lane (%s)" % (out["owed"], ", ".join(_parts)))',
        "matches": 1,
    },
    {
        "why": "wording rows-not-banked as a lane wait promises a sweep that v2878 guarantees never comes",
        "file": "tv/shelf_driver.py",
        "find": '    "rows-not-banked":       "owed a bank, not a read",',
        "replace": '    "rows-not-banked":       "waiting on a lane",',
        "matches": 1,
    },
    {
        "why": "the screen keeping the old sentence makes engine and page disagree about the same reels",
        "file": "tv/control_ui.html",
        "find": "                  if (_ow) bits.push(_ow + ' still owed');",
        "replace": "                  if (_ow) bits.push(_ow + ' waiting on a lane');",
        "matches": 1,
    },
]
