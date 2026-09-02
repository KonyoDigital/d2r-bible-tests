"""A21c — the guard over the roster routes.

⚠ PINS THE LAW, NOT TODAY'S THREE ROSTERS. What must hold is that a catalog whose board getter
is not DEFINED reads DARK, that a MENTION never counts as a definition, that an empty unit word
is not a unit, and that an unknown total never reads as a missing one. [[regression-guard]]
[[unknown-stays-unknown]]
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roster_routes as RR


def _bible():
    import io
    with io.open(RR.BIBLE, encoding="utf-8", errors="replace") as fh:
        return fh.read()


class AMentionIsNotADefinition(unittest.TestCase):

    def test_naming_a_getter_in_prose_does_not_define_it(self):
        """⚠ THE EXACT DEFECT THE FLEET LANES SHIPPED FOR, applied to the roster chain.
        A check that greps for the NAME would have called a missing getter healthy."""
        self.assertFalse(RR._defines("// window._gSetRoster is asked for by the probe",
                                     "_gSetRoster"))
        self.assertFalse(RR._defines("// window._gSetRoster = function(){ return []; }",
                                     "_gSetRoster"))
        self.assertFalse(RR._defines("var x = window._gSetRoster && window._gSetRoster();",
                                     "_gSetRoster"))
        self.assertTrue(RR._defines("window._gSetRoster = function(){ return []; };",
                                    "_gSetRoster"))


class RenamingAGetterTurnsTheLaneDark(unittest.TestCase):
    """⚠ PROVE IT CAN GO RED. A lane that has never been seen red is measuring nothing.

    Sabotage is in MEMORY. Writing bible.html to prove this would steal HIS dirty tree."""

    def test_renaming_the_set_getter_drops_that_route_to_DARK(self):
        src = _bible()
        needle = "window._gSetRoster ="
        n = src.count(needle)
        self.assertGreaterEqual(n, 1,
                                "the sabotage has no assignment to rename — the instrument is "
                                "pointing at a name the board does not use")
        # every assignment, not the first: a second definition left standing would keep the
        # lane FLOWING and the sabotage would be inert. [[source-reading-guard]]
        broken = src.replace(needle, "window._gSetRosterX =")
        self.assertFalse(RR._defines(broken, "_gSetRoster"))
        d = RR.routes(None, bible=broken)
        self.assertTrue(d["ok"], d.get("why"))
        sets = [r for r in d["routes"] if r["key"] == "set"]
        self.assertTrue(sets, "no set route was derived, so the sabotage had nothing to fail")
        self.assertEqual(sets[0]["state"], "DARK", sets[0]["why"])
        self.assertFalse(sets[0]["lanes"]["getter"]["ok"],
                         "renaming the assignment still counted as a definition")

    def test_the_unbroken_copy_does_not_stay_DARK_for_the_same_reason(self):
        """The restore half: if the live tree's set getter is defined, the same call without
        the rename must not report DARK-for-no-getter. Otherwise the sabotage was inert."""
        d = RR.routes(None, bible=_bible())
        sets = [r for r in d["routes"] if r["key"] == "set"]
        self.assertTrue(sets)
        self.assertTrue(sets[0]["lanes"]["getter"]["ok"],
                        "live tree has no set getter either — the rename could not have been "
                        "the thing that went red: %s" % sets[0]["why"])


class AnUnknownTotalIsNotAMissingOne(unittest.TestCase):

    def test_with_no_live_tally_the_total_link_is_UNKNOWN(self):
        d = RR.routes(None)
        for r in d["routes"]:
            self.assertIsNone(r["lanes"]["total"]["ok"],
                              "%s claimed to know about the wire with no live read" % r["key"])

    def test_an_empty_unit_word_is_not_a_unit(self):
        """`{w: ''}` on the surface is the same defect as no unit key at all."""
        ui = "var _DEN = { uniques: {w: 'named'}, sets: {w: 'pieces'}, runewords: {w: ''} };"
        self.assertTrue(RR._unit_stated(ui, "uniques"))
        self.assertTrue(RR._unit_stated(ui, "sets"))
        self.assertFalse(RR._unit_stated(ui, "runewords"))


class TheCorroboratorIsTheSameFunction(unittest.TestCase):

    def test_the_roster_routes_are_judged_by_the_chronicle_corroborator(self):
        import chronicle_routes as CR
        rows = [{"key": "a", "lanes": {k: {"ok": True} for k in RR.LINKS}},
                {"key": "b", "lanes": {k: {"ok": True} for k in RR.LINKS}},
                {"key": "c", "lanes": dict({k: {"ok": True} for k in RR.LINKS},
                                           getter={"ok": False})}]
        flags = CR.corroborate(rows)
        self.assertTrue(any(f["route"] == "c" and f["lane"] == "getter" for f in flags),
                        "the shared corroborator did not flag the lane missing its getter")


class TheRefutableClaimIsMeasured(unittest.TestCase):
    """The brief's claim: at least one roster declared with no getter, or a getter with no unit.

    A true negative is a real result. This test MEASURES; it does not pin today's hits, because
    a test that asserts the current DARK route would go red the day the work lands for the
    wrong reason. [[regression-guard]]
    """

    def test_every_route_speaks_the_hearts_four_words_and_carries_every_link(self):
        d = RR.routes(None)
        self.assertTrue(d.get("ok"), d.get("why"))
        self.assertTrue(d["routes"], "no routes derived — that is UNKNOWN, and it must say so")
        for r in d["routes"]:
            self.assertIn(r["state"], (RR.FLOWING, RR.WATCHED, RR.DARK, RR.UNKNOWN),
                          "a fifth status word defeats the point of one vocabulary")
            for ln in RR.LINKS:
                self.assertIn(ln, r["lanes"], "%s is missing the %s lane" % (r["key"], ln))
            self.assertTrue(r["why"], "%s carries a state with no explanation" % r["key"])

    def test_declared_without_getter_or_getter_without_unit_is_counted_not_hidden(self):
        d = RR.routes({"sets": {"have": 1, "total": 135},
                       "uniques": {"have": 1, "total": 398},
                       "runewords": {"have": 1, "total": 99}})
        missing_getter = [r["key"] for r in d["routes"]
                          if r["lanes"]["declared"]["ok"] and not r["lanes"]["getter"]["ok"]]
        missing_unit = [r["key"] for r in d["routes"]
                        if r["lanes"]["getter"]["ok"] and not r["lanes"]["unit"]["ok"]]
        # the measurement itself must exist; hiding a hit as FLOWING is the false green
        for r in d["routes"]:
            if r["key"] in missing_unit:
                self.assertEqual(r["state"], "WATCHED", r["why"])
            if r["key"] in missing_getter:
                self.assertEqual(r["state"], "DARK", r["why"])
        print("\n  N-1 claim: declared-no-getter=%s getter-no-unit=%s states=%s"
              % (missing_getter, missing_unit,
                 {r["key"]: r["state"] for r in d["routes"]}))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
