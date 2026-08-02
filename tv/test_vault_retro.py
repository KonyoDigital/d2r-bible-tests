"""v1595 — THE VAULT ACCUMULATOR'S LAWS, proven rather than asserted.

Konyo: *"the vault manager is synced to also slowly analyze and remember especially between and
among sessions ... and slowly also feed the vault manager for throwing out or muling the items read
at the time."*

Accumulating a picture of what he owns ACROSS sessions is a different risk profile from a single
read, and every test here exists because of one specific way it could quietly ruin his stash:

  MERGE-MAX — a later read that sees FEWER items must never subtract. An obstructed or half-scrolled
  stash frame is a NORMAL event, not evidence he threw something away. Get this wrong and the
  accumulator slowly eats his own inventory, one bad frame at a time, while looking like it is
  working.

  THROW-OUT NEEDS MORE EVIDENCE THAN KEEP — there is no un-throw in Diablo. It is the only
  irreversible action in the whole app, so it carries a higher bar and stays a SUGGESTION.

  ORDER MUST NOT MATTER — sessions arrive in whatever order the sweep happens to read reels. If
  merge(a,b) and merge(b,a) can disagree, the ledger depends on disk order, which is not a fact
  about his stash.

  MISSING IS NOT ZERO — a count nobody could read stays unknown, with a reason. An invented zero is
  indistinguishable from "he has none of these", and that is what drives a throw-out.

The workflow that built vault_retro.py left this file unwritten and said so; its own ad-hoc poke
used rows with no `name`/`lane`, which `_rows_of` correctly drops, and it read the empty result as
possible breakage rather than a malformed probe. These tests use the real row shape.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402 — non-ASCII in the failure messages must survive a
                     # non-UTF-8 console; a test that cannot report is not a test.
import vault_retro as v  # noqa: E402
import chronicle_retro as cr  # noqa: E402

LANE = "stash"


def row(name, count=1, lane=LANE, **kw):
    r = {"name": name, "lane": lane, "count": count}
    r.update(kw)
    return r


def count_of(res, name):
    for r in res["owned"]:
        if r["name"] == name:
            return r.get("count")
    return None


class TestMergeMax(unittest.TestCase):
    """Law 1, and the one that can silently destroy his ledger."""

    def test_a_smaller_later_read_never_subtracts(self):
        res = v.merge_vault([row("Ral Rune", 9)], [row("Ral Rune", 3)])
        self.assertEqual(count_of(res, "Ral Rune"), 9,
                         "a later read seeing 3 must NOT lower a held count of 9 — a half-scrolled "
                         "stash frame is normal, not evidence he threw six runes away")

    def test_the_shortfall_is_reported_not_swallowed(self):
        res = v.merge_vault([row("Ral Rune", 9)], [row("Ral Rune", 3)])
        held = [h if isinstance(h, str) else h.get("name") for h in res["held"]]
        self.assertIn("Ral Rune", held,
                      "refusing to subtract is right; refusing SILENTLY is not — the shortfall has "
                      "to be visible or a genuine loss looks identical to an obstructed frame")

    def test_a_larger_later_read_does_raise(self):
        res = v.merge_vault([row("Ral Rune", 9)], [row("Ral Rune", 14)])
        self.assertEqual(count_of(res, "Ral Rune"), 14)
        raised = [x if isinstance(x, str) else x.get("name") for x in res["raised"]]
        self.assertIn("Ral Rune", raised)

    def test_an_item_missing_from_a_later_read_survives(self):
        """Absence is not a claim. He did not throw the Shako away by walking to another tab."""
        res = v.merge_vault([row("Shako", 1), row("Ral Rune", 9)], [row("Ral Rune", 9)])
        self.assertEqual(count_of(res, "Shako"), 1,
                         "an item the second read never saw must survive — absence of evidence is "
                         "not evidence of absence, and this is the exact shape of a scroll position")

    def test_order_cannot_change_the_answer(self):
        a = [row("Ral Rune", 9), row("Shako", 1)]
        b = [row("Ral Rune", 3), row("Ist Rune", 2)]
        one = {r["name"]: r.get("count") for r in v.merge_vault(a, b)["owned"]}
        two = {r["name"]: r.get("count") for r in v.merge_vault(b, a)["owned"]}
        self.assertEqual(one, two,
                         "sessions arrive in whatever order the sweep reads reels; if the fold is "
                         "not order-independent the ledger describes the disk, not his stash")

    def test_lanes_do_not_bleed_into_each_other(self):
        """stash / inventory / equipment are different places. The same item in two of them is two
        rows, not one — merging them would invent items he does not have."""
        res = v.merge_vault([row("Ral Rune", 9, lane="stash")],
                            [row("Ral Rune", 2, lane="inventory")])
        got = sorted((r["name"], r["lane"], r.get("count")) for r in res["owned"])
        self.assertEqual(len(got), 2, "same name in two lanes must stay two rows: %r" % (got,))


class TestThrowOutIsHarderThanKeep(unittest.TestCase):
    """Law 4. There is no un-throw in Diablo."""

    def test_the_throw_bar_is_strictly_higher_than_the_keep_bar(self):
        self.assertGreater(v.THROWOUT_CONF_FLOOR, v.KEEP_CONF_FLOOR,
                           "advising a throw-out must need MORE confidence than advising a keep")
        self.assertGreater(v.THROWOUT_MIN_WITNESSES, v.KEEP_MIN_WITNESSES,
                           "and more witnesses")

    def test_the_keep_bar_is_the_chronicle_bar(self):
        """One calibrated number, not two that drift. The chronicle's floor was tuned on his own
        footage; a second copy would be a second thing to re-tune and only one would get it."""
        self.assertEqual(v.KEEP_CONF_FLOOR, cr.CONF_FLOOR)

    def test_a_throw_out_is_never_automatic(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "vault_retro.py"), encoding="utf-8").read()
        self.assertIn("automatic", src)
        self.assertNotIn("automatic\": True", src.replace("'", '"'),
                         "nothing may mark a throw-out automatic — it is a suggestion, always")


class TestHonestAbsence(unittest.TestCase):
    """Law 5. An invented zero is what drives a wrong throw-out."""

    def test_a_sweep_with_no_reader_refuses_instead_of_returning_empty(self):
        out = v.sweep(["/nonexistent/reel"])
        self.assertFalse(out.get("ok"),
                         "no reader supplied is a REFUSAL, not an empty vault — an empty result "
                         "here reads as 'he owns nothing', which is the input to a throw-out")
        self.assertTrue(str(out.get("why") or "").strip(), "and it must say why")

    def test_rows_without_a_name_or_lane_contribute_nothing(self):
        """The shape that fooled the build agent: a bare {key: {count}} map has no name and no lane,
        so it is not a row and must not become one."""
        res = v.merge_vault({"ral": {"count": 9}}, {"ral": {"count": 3}})
        self.assertEqual(res["owned"], [],
                         "a malformed row must be dropped, never guessed into existence")


class TestReuseNotReimplementation(unittest.TestCase):
    """The accumulator is the chronicle sweep pointed at a different target. Two copies of a
    threshold calibrated on his footage is two things that drift apart, and only one gets re-tuned."""

    def test_it_imports_the_chronicle_primitives_rather_than_copying_them(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "vault_retro.py"), encoding="utf-8").read()
        self.assertIn("chronicle_retro", src)
        for prim in ("still_runs", "jpeg_sig"):
            self.assertNotIn("def %s(" % prim, src,
                             "%s must be IMPORTED from chronicle_retro, not redefined here" % prim)


class TestMiniReelIsFoundable(unittest.TestCase):
    """v1595 — the agent now stamps `mini` into the reel index. Before that, is_mini_reel() could
    never return True on a real reel and the mini-first ordering was unreachable code."""

    def test_a_stamped_index_is_recognised(self):
        self.assertTrue(v.is_mini_reel({"mini": True}),
                        "the stamp the agent writes must be the stamp the sweep looks for")

    def test_an_unstamped_reel_is_not_mini(self):
        self.assertFalse(v.is_mini_reel({"sessionId": "s1", "n": 40}))

    def test_the_agent_actually_writes_that_stamp(self):
        """The other half. A reader that recognises a stamp nobody writes is the dead-seam class."""
        agent = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "tv_diablo.py"), encoding="utf-8").read()
        # v1608 — MATCH THE FACT, NOT THE VARIABLE NAME. This asserted the literal
        # `_idx["mini"] = True`, and when the seal was restructured (the index is now written
        # before the blank pass) the dict was renamed _idx -> _ixdoc. The stamp was still written,
        # byte-identical in meaning, and this test went red on a rename — a false alarm on a
        # healthy change, which is the failure mode that teaches people to delete tests.
        # The dead-seam protection is "something writes a mini flag into the reel index"; that is
        # what is checked now, independent of what the local variable happens to be called.
        import re as _re
        self.assertTrue(_re.search(r'\[\s*["\']mini["\']\s*\]\s*=\s*True', agent),
                        "tv_diablo must stamp the reel with a mini flag, or is_mini_reel can "
                        "never fire on real footage")
        self.assertTrue(_re.search(r'\[\s*["\']focus["\']\s*\]\s*=\s*MINI_FOCUS', agent),
                        "and the FOCUS must be stamped too — v1603's sweep trusts it in place of "
                        "a classify call, so a reel without it silently loses that whole benefit")
        self.assertIn("MINI_MODE", agent)


class TestADeclaredFocusIsTrusted(unittest.TestCase):
    """v1603 — Konyo: "is this finally focused and understanding of the fact that it is reading
    stash/runes/gems/materials and to look out specifically for this".

    Before this, no: `focus` was stamped on the reel and used ONLY to sweep mini reels first
    (is_mini_reel's docstring: "being wrong here costs ordering, never correctness"). Every run
    still paid a classify call to rediscover a fact already on disk — and could still get it wrong,
    which is worse than the cost: a rune tab misread as "inventory" files his runes in the wrong
    lane, and merge-max then makes that permanent.

    Trusting it is the SAME trade chronicle_retro.sweep_frames() has made for the live lane since
    v1527. Cheaper and more accurate at once, because the call it removes is the one that could lie.
    """

    def test_an_ownership_focus_is_taken_from_the_stamp(self):
        self.assertEqual(v._declared_surface({"focus": "runes"}), "runes")
        self.assertEqual(v._declared_surface({"focus": "STASH"}), "stash")

    def test_a_chronicle_focus_is_NOT_this_sweep_s_business(self):
        """chronicle-uniques/sets are real mini focuses, but the chronicle sweep owns them. Claiming
        one here would file grail pages into the vault as though they were a stash tab."""
        self.assertIsNone(v._declared_surface({"focus": "chronicle-uniques"}))
        self.assertIsNone(v._declared_surface({"focus": "chronicle-sets"}))

    def test_an_unknown_focus_is_never_trusted(self):
        """The stamp replaces a paid read, so anything not in the vocabulary must fall through to
        the classifier rather than becoming a lane by assertion."""
        for junk in ("", None, "cube", "belt", "../stash", 7, {"a": 1}):
            self.assertIsNone(v._declared_surface({"focus": junk}), repr(junk))

    def test_a_reel_with_no_focus_behaves_exactly_as_before(self):
        self.assertIsNone(v._declared_surface({}))
        self.assertIsNone(v._declared_surface(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
