"""A21c — the guard over the fleet lanes.

⚠ PINS THE LAW, NOT TODAY'S THREE LANES. What must hold is that a lane whose board getter is not
DEFINED reads DARK, that a MENTION never counts as a definition, and that an unknown total never
reads as a missing one. [[regression-guard]] [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_routes as FR


class AMentionIsNotADefinition(unittest.TestCase):

    def test_naming_a_getter_in_prose_does_not_define_it(self):
        """⚠ THE EXACT DEFECT THIS SHIPPED FOR. `_gSetRoster` was named in control_app.py and in
        comments for months while bible.html defined it nowhere, and the total was null on every
        read. A check that greps for the NAME would have called that lane healthy."""
        self.assertFalse(FR._defines("// window._gSetRoster is asked for by the probe", "_gSetRoster"))
        self.assertFalse(FR._defines("var x = window._gSetRoster && window._gSetRoster();", "_gSetRoster"))
        self.assertTrue(FR._defines("window._gSetRoster = function(){ return []; };", "_gSetRoster"))

    def test_every_declared_lane_has_its_getter_defined_on_the_board(self):
        d = FR.routes(None)
        self.assertTrue(d["ok"], d.get("why"))
        for r in d["routes"]:
            self.assertTrue(r["lanes"]["getter"]["ok"],
                            "%s: the board defines no %s, so its denominator can only ever be "
                            "null — %s" % (r["key"], r["lanes"]["getter"]["by"][0], r["why"]))


class AnUnknownTotalIsNotAMissingOne(unittest.TestCase):

    def test_with_no_live_tally_the_total_link_is_UNKNOWN(self):
        """Without a live read nobody can say whether a total reaches the wire. Reporting that as
        a break would cry wolf; reporting it as fine would be the false green."""
        d = FR.routes(None)
        for r in d["routes"]:
            self.assertIsNone(r["lanes"]["total"]["ok"],
                              "%s claimed to know about the wire with no live read" % r["key"])
            self.assertEqual(r["state"], "UNKNOWN", "%s: %s" % (r["key"], r["why"]))

    def test_a_lane_reporting_a_total_but_no_unit_is_WATCHED_not_FLOWING(self):
        """A right number under an unstated unit is exactly what he found on the fleet card."""
        d = FR.routes({"sets": {"have": 1, "total": 135},
                       "uniques": {"have": 1, "total": 398},
                       "runewords": {"have": 1, "total": 99}})
        for r in d["routes"]:
            self.assertIn(r["state"], ("FLOWING", "WATCHED"), r["why"])
            if not r["lanes"]["unit"]["ok"]:
                self.assertEqual(r["state"], "WATCHED", r["why"])

    def test_a_zero_total_is_not_a_total(self):
        d = FR.routes({"sets": {"have": 0, "total": 0},
                       "uniques": {"have": 1, "total": 398},
                       "runewords": {"have": 1, "total": 99}})
        sets = [r for r in d["routes"] if r["key"] == "sets"][0]
        self.assertFalse(sets["lanes"]["total"]["ok"], "a total of 0 was accepted as a denominator")


class TheCorroboratorIsTheSameFunction(unittest.TestCase):

    def test_the_fleet_lanes_are_judged_by_the_chronicle_corroborator(self):
        """Not a copy of the rule — the same code. Two spellings of one rule only ever get fixed
        once, which is how the third twin came to be left running in the first place."""
        import chronicle_routes as CR
        rows = [{"key": "a", "lanes": {k: {"ok": True} for k in FR.LINKS}},
                {"key": "b", "lanes": {k: {"ok": True} for k in FR.LINKS}},
                {"key": "c", "lanes": dict({k: {"ok": True} for k in FR.LINKS},
                                           getter={"ok": False})}]
        flags = CR.corroborate(rows)
        self.assertTrue(any(f["route"] == "c" and f["lane"] == "getter" for f in flags),
                        "the shared corroborator did not flag the lane missing its getter")


if __name__ == "__main__":
    unittest.main(verbosity=2)
