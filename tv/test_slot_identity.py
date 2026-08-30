#!/usr/bin/env python3
"""Guards for slot identity. His spec, 2026-08-29, turned into things that can go RED.

⚠ EVERY ONE OF THESE ASSERTS A REFUSAL AS WELL AS A PASS. A gate that has only ever been seen say
yes is not a gate — that is this repo's most expensive lesson and it applies to brand-new code
hardest, because nothing has had a chance to catch it yet.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slot_identity as S


BOX = (100.0, 200.0, 500.0, 500.0)          # a 500x500 stash grid at (100,200) -> 50px cells


class TestTheCellIsArithmeticOnPixels(unittest.TestCase):
    def test_corners_and_middle_land_where_a_person_would_say(self):
        self.assertEqual(S.cell_of((100, 200), BOX, "stash")[0], (0, 0))     # top-left
        self.assertEqual(S.cell_of((599, 699), BOX, "stash")[0], (9, 9))     # bottom-right
        self.assertEqual(S.cell_of((375, 475), BOX, "stash")[0], (5, 5))     # middle

    def test_the_inventory_is_a_DIFFERENT_grid_and_the_same_point_is_a_different_cell(self):
        # 10x4 vs 10x10 — if these ever returned the same cell the grid table is not being read.
        st = S.cell_of((375, 475), BOX, "stash")[0]
        inv = S.cell_of((375, 475), BOX, "inventory")[0]
        self.assertEqual(st, (5, 5))
        self.assertEqual(inv, (5, 2))
        self.assertNotEqual(st, inv)

    def test_a_point_OUTSIDE_the_panel_refuses_and_says_so(self):
        cell, why = S.cell_of((50, 200), BOX, "stash")
        self.assertIsNone(cell)
        self.assertIn("OUTSIDE", why)

    def test_a_zero_size_panel_refuses(self):
        cell, why = S.cell_of((100, 200), (100, 200, 0, 0), "stash")
        self.assertIsNone(cell)
        self.assertIn("nothing can be inside it", why)

    def test_an_unknown_container_refuses_rather_than_guessing_a_grid(self):
        cell, why = S.cell_of((375, 475), BOX, "wardrobe")
        self.assertIsNone(cell)
        self.assertIn("unknown container", why)

    def test_the_tab_is_part_of_the_identity(self):
        # the same cell in two stash tabs is two different places, or auto-assembly files them together
        self.assertNotEqual(S.slot_key("stash", 3, 4, tab="personal"),
                            S.slot_key("stash", 3, 4, tab="shared1"))


def _sight(name, reel, frame, slot=None, conf=0.9):
    s = {"name": name, "reel": reel, "frame": frame, "conf": conf}
    if slot:
        s["slot"] = slot
    return s


class TestSlotTagsAreWitnessesTheNameAloneCannotEarn(unittest.TestCase):
    def test_two_looks_agreeing_on_one_cell_earn_same_slot(self):
        ss = [_sight("Shako", "r1", "f1", "stash:c2r3"), _sight("Shako", "r1", "f2", "stash:c2r3")]
        self.assertIn("same-slot", S.slot_tags(ss))

    def test_ONE_placed_look_earns_NOTHING(self):
        # a single look agreeing with itself is not corroboration
        ss = [_sight("Shako", "r1", "f1", "stash:c2r3")]
        self.assertEqual(S.slot_tags(ss), [])

    def test_two_cells_in_ONE_reel_is_a_conflict_and_must_be_visible(self):
        ss = [_sight("Shako", "r1", "f1", "stash:c2r3"), _sight("Shako", "r1", "f2", "stash:c7r1")]
        self.assertIn("slot-conflict", S.slot_tags(ss))
        self.assertNotIn("same-slot", S.slot_tags(ss))

    def test_the_SAME_cell_across_two_reels_is_agreement_not_conflict(self):
        # he did not move it between sessions; that is the ordinary case and must not read as a fault
        ss = [_sight("Shako", "r1", "f1", "stash:c2r3"), _sight("Shako", "r2", "f9", "stash:c2r3")]
        self.assertIn("same-slot", S.slot_tags(ss))
        self.assertNotIn("slot-conflict", S.slot_tags(ss))


class TestUnplacedIsNotZero(unittest.TestCase):
    def test_placed_and_unplaced_are_reported_apart(self):
        ss = [_sight("Shako", "r1", "f1", "stash:c2r3"), _sight("Shako", "r1", "f2")]
        p = S.placement(ss)
        self.assertEqual((p["placed"], p["unplaced"]), (1, 1))

    def test_no_slots_at_all_does_not_read_as_agreement(self):
        p = S.placement([_sight("Shako", "r1", "f1"), _sight("Shako", "r1", "f2")])
        self.assertFalse(p["agreed"])
        self.assertIn("none of them placed it", p["why"])


class TestTheTooltipIsNotWhereTheItemIs(unittest.TestCase):
    """D2R draws the tip ADJACENT to the hovered cell. The rectangle says where the TEXT went, so
    turning it into a cell needs an offset that must be MEASURED, never assumed."""

    RECT = (100, 200, 260, 320)

    def test_an_uncalibrated_offset_REFUSES_instead_of_using_the_corner(self):
        # ⚠ the whole point: a guessed offset would place every item in whichever cell the TEXT
        # covers, confidently and wrongly. Silence is the correct output until it is measured.
        pt, why = S.anchor_from_tooltip_rect(self.RECT)
        self.assertIsNone(pt)
        self.assertIn("OFFSET has been calibrated", why)

    def test_a_calibrated_offset_moves_the_anchor_off_the_tooltip(self):
        pt, why = S.anchor_from_tooltip_rect(self.RECT, "topleft", (-24, 12))
        self.assertEqual(pt, (76.0, 212.0), why)

    def test_a_zero_area_rect_refuses(self):
        pt, why = S.anchor_from_tooltip_rect((100, 200, 100, 200), offset=(5, 5))
        self.assertIsNone(pt)
        self.assertIn("no area", why)

    def test_an_unknown_corner_refuses(self):
        pt, why = S.anchor_from_tooltip_rect(self.RECT, "middle", (1, 1))
        self.assertIsNone(pt)
        self.assertIn("unknown corner", why)

    def test_each_corner_gives_a_DIFFERENT_anchor(self):
        # if these ever collapsed, the corner argument would be decoration
        seen = {S.anchor_from_tooltip_rect(self.RECT, c, (1, 1))[0]
                for c in ("topleft", "topright", "bottomleft", "bottomright")}
        self.assertEqual(len(seen), 4)


class TestTheHumanLaneIsARecheckNotAWitnessCount(unittest.TestCase):
    """His rule: "me/cuzin/user doesnt need to be witnessed.. just needs to be able to read it
    accurately.. so maybe just a double read". So the bar moves from independence to agreement —
    and a disagreement HOLDS, because nothing here can say which read was right."""

    def test_two_agreeing_reads_of_one_frame_pass(self):
        a = _sight("Shako", "r1", "f1", "stash:c2r3")
        b = _sight("Shako", "r1", "f1", "stash:c2r3")
        ok, why = S.double_read_agrees(a, b)
        self.assertTrue(ok, why)

    def test_a_NAME_disagreement_holds(self):
        ok, why = S.double_read_agrees(_sight("Shako", "r1", "f1"), _sight("Shako's", "r1", "f1"))
        self.assertFalse(ok)
        self.assertIn("disagree on the NAME", why)

    def test_a_CELL_disagreement_holds_even_when_the_name_matches(self):
        ok, why = S.double_read_agrees(_sight("Shako", "r1", "f1", "stash:c2r3"),
                                       _sight("Shako", "r1", "f1", "stash:c9r9"))
        self.assertFalse(ok)
        self.assertIn("disagree on the CELL", why)

    def test_two_DIFFERENT_frames_are_not_a_recheck(self):
        # this is the substitution that would quietly turn the human bar back into a witness count
        ok, why = S.double_read_agrees(_sight("Shako", "r1", "f1"), _sight("Shako", "r1", "f2"))
        self.assertFalse(ok)
        self.assertIn("DIFFERENT frames", why)

    def test_one_read_is_not_a_double_read(self):
        v = S.lane_verdict([_sight("Shako", "r1", "f1")], S.LANE_HUMAN,
                           reads_of_same_frame=[_sight("Shako", "r1", "f1")])
        self.assertFalse(v["wouldPass"])
        self.assertIn("not a double read", v["why"])


class TestTheLanesStayApart(unittest.TestCase):
    def test_a_slot_conflict_holds_BOTH_lanes(self):
        ss = [_sight("Shako", "r1", "f1", "stash:c2r3"), _sight("Shako", "r1", "f2", "stash:c7r1")]
        for lane in (S.LANE_HUMAN, S.LANE_SHADOW):
            v = S.lane_verdict(ss, lane, reads_of_same_frame=ss)
            self.assertFalse(v["wouldPass"], "%s passed on a slot conflict" % lane)

    def test_shadow_does_NOT_answer_here_it_defers_to_the_existing_gate(self):
        # ⚠ if this module ever starts returning True for shadow it has silently become a SECOND
        # grounding authority beside chronicle_retro, which is how two gates drift apart.
        v = S.lane_verdict([_sight("Shako", "r1", "f1", "stash:c2r3")], S.LANE_SHADOW)
        self.assertIsNone(v["wouldPass"])
        self.assertIn("chronicle_retro", v["why"])

    def test_this_module_deletes_nothing_and_writes_nothing(self):
        import inspect
        src = inspect.getsource(S)
        for forbidden in ("os.remove", "unlink", "rmtree", "open(", "shutil"):
            self.assertNotIn(forbidden, src,
                             "slot_identity must stay a reader; found %r" % forbidden)


class TestV2319PointOfCellIsTheExactInverse(unittest.TestCase):
    """★ THE HALF MINI(AUTOMATIC) NEEDS: cell -> point, so the machine can hover instead of him.

    Konyo: "is there a way for this to really be automated and for it to pinpoint which items it
    needs to hover itself on? ... i press MINI on air and it does it itself", and then "when i click
    a button called MINI(AUTOMATIC) that alone triggers the HOVER mode".

    cell_of() answers "what did he hover". point_of_cell() answers "what must be hovered". If the
    two ever disagree the automatic pass hovers one cell and files the result under another — and
    a wrong slot is worse than an absent one, which is the rule cell_of already states in its own
    docstring. So the round trip is asserted over EVERY cell of EVERY grid, not a sample.
    """

    def test_the_round_trip_holds_for_every_cell_of_every_grid(self):
        box = (137.0, 211.0, 413.0, 389.0)     # deliberately not round numbers
        for container, (cols, rows) in S.GRIDS.items():
            for c in range(cols):
                for r in range(rows):
                    pt, why = S.point_of_cell(c, r, box, container)
                    self.assertIsNotNone(pt, "%s (%d,%d) refused: %s" % (container, c, r, why))
                    got, w2 = S.cell_of(pt, box, container)
                    self.assertEqual(got, (c, r),
                                     "%s: asked to hover (%d,%d), the point lands in %r — the "
                                     "automatic pass would file the read under the wrong cell"
                                     % (container, c, r, got))

    def test_a_cell_outside_the_grid_is_REFUSED_not_clamped(self):
        pt, why = S.point_of_cell(99, 99, (0.0, 0.0, 100.0, 100.0), "stash")
        self.assertIsNone(pt, "it clamped an impossible cell onto a real one and would hover it")
        self.assertIn("outside", why)

    def test_topleft_and_center_are_different_points_in_the_same_cell(self):
        box = (0.0, 0.0, 100.0, 100.0)
        a, _ = S.point_of_cell(3, 4, box, "stash", where="center")
        b, _ = S.point_of_cell(3, 4, box, "stash", where="topleft")
        self.assertNotEqual(a, b,
                            "the calibration pass needs a point whose CORNER is known; a centre "
                            "hides which corner the tooltip anchored to")
        for p in (a, b):
            self.assertEqual(S.cell_of(p, box, "stash")[0], (3, 4),
                             "a where= variant left the cell it belongs to")

    def test_the_plan_is_in_reading_order_and_deduped(self):
        plan, why = S.hover_plan([(2, 1), (0, 0), (2, 1), (1, 0)],
                                  (0.0, 0.0, 100.0, 100.0), "stash")
        self.assertEqual([(d["col"], d["row"]) for d in plan], [(0, 0), (1, 0), (2, 1)],
                         "not left-to-right, top-to-bottom — a half-finished pass should read as "
                         "a prefix of what he would have done by hand, not a scatter")

    def test_an_unplaceable_cell_is_CARRIED_with_its_reason(self):
        """A short plan must never be mistakable for a short stash."""
        plan, why = S.hover_plan([(0, 0), (99, 99)], (0.0, 0.0, 100.0, 100.0), "stash")
        self.assertEqual(len(plan), 2, "the unplaceable cell was dropped from the plan silently")
        bad = [d for d in plan if d["point"] is None]
        self.assertEqual(len(bad), 1)
        self.assertTrue(bad[0]["why"], "it was carried with no reason attached")


if __name__ == "__main__":
    # REG-044 — this file prints non-ASCII; a non-UTF-8 console would turn its own
    # verdict into a traceback, which is the one place a gate must never be silent.
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    try:
        import console_safe as _cs; _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
