# -*- coding: utf-8 -*-
"""The board is a BUILD OUTPUT of TASKS.md, so a decision the build cannot read does not survive.

⚠⚠ THE FAILURE THIS EXISTS FOR TOOK ONE AFTERNOON TO APPEAR AND WOULD HAVE LOOKED FINE UNTIL THE
NEXT REFRESH. On 2026-09-03 he retired A6 and put A18/A20 into hibernation. Those decisions were
written into TASKS.md and into the live board by hand — and re-running the deriver the same hour
filed all three straight back into `1 · PENDING`, because `_classify` knew five states and none of
them was "he decided not to". Correct now, silently wrong later, which is worse than wrong now.

Three more defects were found while fixing that, each by a check rather than by reading:

  · the topic index was GLOBAL, so a topic's number kept climbing across stages and VISUAL under
    IN PROGRESS numbered onto the base of YOUR CALL. Latent for as long as the old scheme
    multiplied by 100 and had room to hide it.
  · the stage bases were 1 apart where a stage already held two topics.
  · matching the ruling marker ANYWHERE in the progress line retired A1 — a task in progress that
    merely MENTIONS a scope cut. The count was the tell: two rows in RETIRED, one retired thing.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import board_sync as B  # noqa: E402


class ARulingSurvivesTheDeriver(unittest.TestCase):

    def test_his_two_rulings_have_a_state_at_all(self):
        for state in ("retired", "hibernating"):
            self.assertIn(
                state, B._SEC,
                "%r is not a state the storyline knows, so a task he %s is filed as whatever it "
                "was before — which puts a decision back on the to-do list." % (state, state))

    def test_a_ruling_that_OPENS_the_line_is_read(self):
        self.assertEqual(B._classify("", "⛔ RETIRED — his call, 2026-09-03"), "retired")
        self.assertEqual(B._classify("", "⏸ HIBERNATION — his call, same ruling as A20"), "hibernating")
        self.assertEqual(B._classify("", "RETIRED"), "retired")

    def test_a_ruling_MENTIONED_mid_line_does_not_retire_the_task(self):
        """⚠ THE BUG, EXACTLY. A1 is 1/3 and in progress; its note describes one sub-goal being cut.

        Matching the marker anywhere filed the whole task under RETIRED. A ruling is a statement
        ABOUT this task and is written at the front; a marker mid-sentence is the task TALKING
        about a decision, not carrying one.
        """
        live = "1/3 · v2485 made the heart stop calling work owed. ⛔ SCOPE CUT 2026-09-03: the " \
               "four organs on every surface is OUT. Denominator moved 4 → 3"
        self.assertEqual(
            B._classify("", live), "progress",
            "a task that MENTIONS a scope cut was filed as retired whole — that is a live item "
            "disappearing off the board because of a word inside its own note")
        self.assertEqual(
            B._classify("", "2/4 · going fine, and A20 is in ⏸ HIBERNATION for comparison"),
            "progress")

    def test_the_progress_fraction_still_wins_over_the_header_word(self):
        """The older law this file must not have broken: READY means MAY start, not HAS started."""
        self.assertEqual(B._classify("READY", "3/4 · banked"), "progress")
        self.assertEqual(B._classify("READY", "0/1 · not started"), "pending")


class TheStoryCannotSilentlyMisFile(unittest.TestCase):

    def test_no_stage_can_renumber_a_topic_into_the_next_stage(self):
        rows = B.build()[0]
        self.assertTrue(rows, "BASELINE: no rows derived, so this law is vacuous")
        bases = sorted((o, k) for k, (_t, o, _s) in B._SEC.items())
        by_stage = {}
        for r in rows:
            by_stage.setdefault(r["section"].split(" · ")[0], set()).add(r["sectionOrder"])
        # every row's order must fall inside its OWN stage's span
        span = {}
        for i, (o, k) in enumerate(bases):
            nxt = bases[i + 1][0] if i + 1 < len(bases) else o + 40
            span[B._SEC[k][0]] = (o, nxt)
        for r in rows:
            title = r["section"].rsplit(" · ", 1)[0]
            lo, hi = span[title]
            self.assertTrue(
                lo <= r["sectionOrder"] < hi,
                "%s is in %r but numbered %d, which belongs to another stage (%d..%d). A topic "
                "that overflows its stage renders under the wrong heading and nothing errors."
                % (r["id"], title, r["sectionOrder"], lo, hi))

    def test_every_stage_sorts_above_the_boards_older_sections(self):
        """⚠ v2490 shipped the whole storyline UNREACHABLE underneath the sections it replaced.

        The board still carries pre-storyline sections at 0..11. A stage numbered positively sorts
        below the very rows it exists to organise.
        """
        for k, (title, order, _st) in B._SEC.items():
            self.assertLess(
                order, 0,
                "stage %r (%s) is numbered %d. Anything >= 0 sorts underneath the board's older "
                "sections and the reader never reaches it." % (k, title, order))

    def test_an_unknown_state_is_not_quietly_filed_as_pending(self):
        title, order = B.story_of("a-state-nobody-added-here")
        self.assertIn("does not know", title,
                      "an unrecognised state renders as a normal stage, so a state added to "
                      "_classify and forgotten in SECTIONS joins PENDING and a ruling comes back "
                      "to life")

    def test_the_storyline_reads_pending_then_progress_then_completed(self):
        order = [B._SEC[k][1] for k in ("pending", "progress", "done")]
        self.assertEqual(sorted(order), order,
                         "the stages do not sort pending → in progress → completed: %s" % order)
        self.assertLess(B._SEC["done"][1], B._SEC["hibernating"][1],
                        "HIBERNATING sorts before COMPLETED — a set-aside item reads as live work")

    def test_there_is_exactly_one_table_of_states(self):
        """[[copy-drift]] §1. My first cut of story_of carried its own copy of all seven states —
        a second source, written the same hour as a fix for two sources disagreeing."""
        self.assertFalse(
            hasattr(B, "STORY"),
            "board_sync has a second state table (STORY) beside SECTIONS. Two tables of the same "
            "seven states will disagree, and the board will file a task by whichever one the "
            "caller happened to read.")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
