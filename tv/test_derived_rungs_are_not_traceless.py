# -*- coding: utf-8 -*-
"""v2725 — A RUNG NOTHING CACHES IS NOT A RUNG NOTHING KNOWS.

`one_funnel` printed, for four of its six rungs:

    "no store records this rung, so passing it leaves no trace"

and that sentence was measured FALSE on 2026-09-06. `reel_story.py`'s module docstring names the
decider for every stage — `reel_retention.plan()` for all four — and that decider answers for
EVERY reel on his shelf: onDisk 40, kept 40, and `stageKnown` false for ZERO reels. The state of
every rung was establishable the whole time. What those rungs lack is the DATE of passage.

⚠⚠ THE STING: one_funnel cites [[unknown-stays-unknown]] five times in its own comments, and takes
enormous care to keep ABSENT, UNREADABLE and EMPTY apart (REG-559 was exactly that). It then
collapsed DERIVED into ABSENT — the same error one storey up. A law a module states about its
inputs has to hold for the module's own reasoning too.

=== WHAT THIS PINS, AND THE ONE THAT MATTERS MOST ===
The load-bearing test here is `test_the_derived_rungs_do_NOT_move_passage`. Discovering that four
rungs are observable is a fact that makes a verdict look better, and the honest response to such a
fact is to publish it BESIDE the old verdict rather than inside it. [[t155]] wrote that warning
down before this evidence existed:

    "Reaching the opposite conclusion here, on the same evidence, because it would unblock a row,
     would be exactly the reasoning that makes a conditional authorisation worthless."

So `passage` must stay PARTIAL at 2 of 6 dated rungs no matter what `observability` says, and this
file fails if a future edit lets the good news leak into the strict number.
"""
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

import one_funnel as OF  # noqa: E402


class DerivedRungsAreNotTraceless(unittest.TestCase):

    # ── the map is real, not a story about the code ────────────────────────────────────────────
    def test_every_rung_is_either_stored_or_derived(self):
        """A rung with neither is genuinely traceless — and must be declared, not discovered."""
        for rung in OF.WAYPOINT_SOURCES:
            stored = bool(OF.WAYPOINT_SOURCES.get(rung))
            derived = bool(OF.DERIVED_SOURCES.get(rung))
            self.assertTrue(
                stored or derived,
                "rung %r has no store AND no decider. If that is true it is fine, but it must be "
                "TRUE — the four rungs this file exists for were reported that way while "
                "reel_retention.plan() decided every one of them." % rung
            )

    def test_no_rung_is_both(self):
        """A rung answered twice is two sources of truth, and they will disagree. [[copy-drift]]"""
        both = sorted(set(k for k, v in OF.WAYPOINT_SOURCES.items() if v)
                      & set(OF.DERIVED_SOURCES))
        self.assertEqual([], both,
                         "rung(s) %s declare BOTH a cache and a live decider; when they disagree "
                         "nothing says which wins" % both)

    def test_each_decider_actually_EXISTS_AND_IS_CALLABLE(self):
        """⚠ Naming a function that does not exist is how a fix becomes a comment."""
        for rung, src in OF.DERIVED_SOURCES.items():
            self.assertEqual(3, len(src),
                             "%r's decider entry must be (module, function, rule)" % rung)
            mod, fname, rule = src
            try:
                m = __import__(mod)
            except Exception as e:
                self.fail("rung %r names module %r, which will not import (%s). A decider that "
                          "cannot run does not make a rung observable." % (rung, mod, str(e)[:70]))
            fn = getattr(m, fname, None)
            self.assertTrue(callable(fn),
                            "rung %r names %s.%s(), which is not callable — so the claim that this "
                            "rung is decided live is unbacked" % (rung, mod, fname))
            self.assertTrue(str(rule).strip(),
                            "rung %r names a decider but states no RULE, so a reader cannot check "
                            "the claim without leaving the file" % rung)

    def test_the_quoted_rule_is_reel_storys_rule_not_an_invented_one(self):
        """The rules are QUOTED from reel_story. A quote nobody checks is a paraphrase.

        ⚠ Anchored at BOTH ends and matched against the real vocabulary — `TAG_STAGE`'s keys and
        `STAGES` — rather than a fixed window of the docstring. [[source-reading-guard]]
        """
        import reel_story as RS
        vocab = set(RS.TAG_STAGE) | set(RS.STAGES) | {"onDisk"}
        for rung, (_mod, _fn, rule) in OF.DERIVED_SOURCES.items():
            self.assertIn(
                rung, RS.STAGES,
                "rung %r is not one of reel_story.STAGES, so quoting a rule for it is quoting "
                "nothing" % rung
            )
            words = set(w.strip("(),.") for w in str(rule).replace("!=", " ").replace("==", " ").split())
            self.assertTrue(
                words & vocab,
                "rung %r's rule %r names nothing from reel_story's vocabulary (%s...). A rule that "
                "quotes no real tag is prose, and prose cannot be checked."
                % (rung, rule, sorted(vocab)[:4])
            )

    # ── the sentence that was false ────────────────────────────────────────────────────────────
    def test_a_derived_rung_never_says_it_leaves_no_trace(self):
        cover = OF._waypoint_cover(["s_1_1"])
        for rung in OF.DERIVED_SOURCES:
            row = cover.get(rung) or {}
            self.assertIsNotNone(
                row.get("derivedBy"),
                "rung %r has a declared decider but the cover map does not name it, so the funnel "
                "still reports it as storeless-and-therefore-unknown" % rung
            )
            self.assertNotIn(
                "leaves no trace", str(row.get("why") or ""),
                "rung %r still prints the traceless sentence while %s decides it. That sentence "
                "was measured false: plan() answers for every reel on the shelf."
                % (rung, row.get("derivedBy"))
            )

    def test_a_decider_that_cannot_run_is_UNKNOWN_not_zero(self):
        """⚠ The store path learned this as REG-559; the derived path must not relearn it."""
        import reel_story as RS
        orig = RS.story
        try:
            RS.story = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("shelf offline"))
            dec, tot, why = OF._decided_count()
            self.assertIsNone(dec, "a decider that raised returned a COUNT (%r). Nobody looked, so "
                                   "the honest answer is None." % dec)
            self.assertIsNone(tot, "a decider that raised returned a total (%r)" % tot)
            self.assertTrue(why, "it refused without saying why")
        finally:
            RS.story = orig

    # ── ⚠⚠ THE LOAD-BEARING ONE ───────────────────────────────────────────────────────────────
    def test_the_derived_rungs_do_NOT_move_passage(self):
        """`passage` asks whether the HISTORY is dated. Deciding a rung live does not date it.

        This is the test that stops a true discovery from laundering a strict verdict. If four
        rungs being observable is allowed to raise `passage`, then the number that says "his
        pipeline keeps no history" quietly becomes the number that says "his pipeline is fine",
        and no reader would ever know the definition moved under them.
        """
        f = OF.funnel()
        dated = set(f.get("datedRungs") or [])
        leaked = sorted(dated & set(OF.DERIVED_SOURCES))
        self.assertEqual(
            [], leaked,
            "rung(s) %s are counted as DATED while nothing stores a date for them. `passage` "
            "measures recorded history; a live decider proves the present, not the past." % leaked
        )
        for rung in OF.DERIVED_SOURCES:
            row = (f.get("waypoints") or {}).get(rung) or {}
            self.assertIsNone(
                row.get("covered"),
                "rung %r reports store coverage %r while having no store. `covered` is the count "
                "of DATED rows; borrowing the decider's count for it merges the two readings this "
                "change exists to keep apart." % (rung, row.get("covered"))
            )

    # ── the second reading is present on EVERY path (REG-546's law) ───────────────────────────
    def test_observability_is_present_even_when_nothing_was_established(self):
        """⚠⚠ THIS TEST WAS VACUOUS ON ITS FIRST WRITING, AND THE SABOTAGE PASS CAUGHT IT.

        It called `funnel()` on his real tree, which takes the NORMAL return every time — so it
        checked the key on the ONE path that was never in doubt and never once entered the
        `_unknown` early return it claims to be about. Deleting the key from that early return
        left this GREEN. A law aimed at an exceptional path has to force that path.
        [[zero-needs-a-denominator]] — no failures, because no candidates.
        """
        import reel_story as RS
        orig = RS.STAGES
        try:
            RS.STAGES = ()                      # no ladder -> funnel() must take _unknown()
            f = OF.funnel()
            self.assertEqual("UNKNOWN", f.get("passage"),
                             "the ladder was emptied and funnel() still answered %r, so this test "
                             "is not exercising the path it names" % f.get("passage"))
            self.assertIn(
                "observability", f,
                "funnel() gained a key that its own UNKNOWN path does not return — REG-546 "
                "exactly, where a caller breaks on the paths meaning NOTHING WAS ESTABLISHED"
            )
            obs = f["observability"]
            for k in ("state", "seen", "rungCount", "unknown", "dark", "why"):
                self.assertIn(k, obs, "observability is missing %r on the UNKNOWN path" % k)
            self.assertEqual("UNKNOWN", obs["state"],
                             "nothing was established, yet observability claims %r" % obs["state"])
        finally:
            RS.STAGES = orig

        f = OF.funnel()                          # and the normal path still carries it
        self.assertIn("observability", f)
        self.assertIn(f["observability"]["state"], ("OBSERVED", "PARTIAL", "UNKNOWN"))

    def test_one_unmeasurable_rung_makes_the_whole_verdict_UNKNOWN(self):
        """⚠ A rung nobody could read is not a rung measured as absent. [[zero-needs-a-denominator]]"""
        cover = {
            "a": {"store": "x.json", "covered": 3},
            "b": {"store": "y.json", "covered": None, "why": "unreadable"},
        }
        obs = OF._observability(cover)
        self.assertEqual("UNKNOWN", obs["state"],
                         "one unreadable rung produced %r. A fraction computed over evidence "
                         "nobody gathered is a finding with no author." % obs["state"])
        self.assertIn("b", obs["unknown"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
