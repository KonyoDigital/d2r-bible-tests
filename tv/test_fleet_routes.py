"""A21c — the guard over the fleet lanes.

⚠ PINS THE LAW, NOT TODAY'S THREE LANES. What must hold is that a lane whose board getter is not
DEFINED reads DARK, that a MENTION never counts as a definition, and that an unknown total never
reads as a missing one. [[regression-guard]] [[unknown-stays-unknown]]
"""
import io
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


class TheMemoKeyMustSurviveTheRealTally(unittest.TestCase):
    """v2473 — the fleet lanes read UNKNOWN on his console for one line in a CACHE KEY.

    Photographed, not gated: "THE FLEET LANES · UNKNOWN · the fleet lanes could not be derived
    ('bool' object has no attribute 'get')". `routes(tally)` folded every value of the tally with
    `(v or {}).get("total")`, and the tally is an ENVELOPE — measured on his live console, 8 keys
    of which only 3 are lanes; `ok` is a bool, `why` is None, `at` an int, `source`/`profile` str.
    So every real call raised and the panel showed the exception instead of the lanes.

    ⚠ These pin the LAW — a key survives ANY value shape — not the roster of fields, so adding a
    field to the tally tomorrow cannot bring the panel down again. [[regression-guard]]
    """

    def _envelope(self, **over):
        """The shape his console actually hands over, scalars and all."""
        t = {"ok": True, "why": None, "at": 1788415464867, "source": "board-store",
             "profile": "main",
             "sets": {"have": 121, "total": 135},
             "uniques": {"have": 248, "total": 403},
             "runewords": {"have": 0, "total": 99}}
        t.update(over)
        return t

    def test_routes_survives_the_real_envelope(self):
        """The reproduction. RED before the fix with AttributeError, green after."""
        try:
            d = FR.routes(self._envelope())
        except AttributeError as e:
            self.fail("routes() still raises on the real tally shape (%s) — this is the defect "
                      "that printed the exception where the fleet lanes belong" % e)
        self.assertTrue(d.get("ok"), "routes() refused on a well-formed tally: %s" % d.get("why"))
        self.assertTrue(d.get("routes"), "no lanes came back")

    def test_no_value_shape_can_raise_from_the_key(self):
        """A cache key is the last place a crash may come from — it took the whole panel down."""
        exotic = self._envelope(weird=object(), nested=[1, 2], nothing=None, flag=False,
                                num=3.5, blank="")
        try:
            FR._tally_key(exotic)
        except Exception as e:
            self.fail("_tally_key raised on an exotic value (%s: %s). A field added to the tally "
                      "must never be able to take the fleet panel down again."
                      % (type(e).__name__, e))

    def test_the_timestamp_is_excluded_or_the_memo_never_hits(self):
        """`at` moves on every read; folding it in would make every key unique."""
        a = FR._tally_key(self._envelope(at=1))
        b = FR._tally_key(self._envelope(at=999999))
        self.assertEqual(a, b, "the key changes with `at`, so the memo can never hit once — that "
                               "is not a cache, it is overhead")

    def test_the_profile_is_INCLUDED_or_one_account_answers_for_the_other(self):
        """main and ladder are different answers; serving one for the other is the ladder scar."""
        m = FR._tally_key(self._envelope(profile="main"))
        l = FR._tally_key(self._envelope(profile="ladder"))
        self.assertNotEqual(m, l, "the key ignores `profile`, so a ladder read can be served a "
                                  "main-profile answer out of the memo")

    def test_a_changed_lane_total_still_busts_the_key(self):
        """The reason the argument is in the key at all — do not lose it while fixing the crash.

        ⚠ MY FIRST VERSION OF THIS TEST WAS WRONG AND THE FAILURE WAS ITS OWN. It changed `have`
        (121 -> 122) and expected a new key. Measured instead of argued: re-running routes() with
        only `have` changed produces byte-identical output, and with `total` changed produces
        different output. So `have` does not reach the answer and keying on it would only cost
        memo hits. A key must carry exactly the inputs the OUTPUT depends on — no fewer, and no
        more. [[sabotage-is-usually-the-wrong-one]]
        """
        a = FR._tally_key(self._envelope())
        b = FR._tally_key(self._envelope(sets={"have": 121, "total": 999}))
        self.assertNotEqual(a, b, "a changed lane total no longer changes the key")
        same = FR._tally_key(self._envelope(sets={"have": 122, "total": 135}))
        self.assertEqual(a, same,
                         "the key now varies with `have`, which routes() output does not depend "
                         "on — measured identical both ways. That costs every memo hit for nothing")


def _run_hrt_chron():
    """Render _hrtChron's ERROR branch for both callers. -> {"chronicle": html, "fleet": html}

    ⚠ IT RUNS THE FUNCTION. The assertion this replaces checked that the token `SUBJ` appeared
    somewhere in the source, which `var SUBJ = TT;` satisfies while the hardcoded "the chronicles"
    is restored — the v2472 review reproduced exactly that, green, with THE FLEET LANES shipping
    the photographed defect. A token existing is not a token being used.
    """
    import json as _json
    import re as _re
    import shutil as _shutil
    import subprocess as _subprocess
    import tempfile as _tempfile
    node = _shutil.which("node")
    if not node:
        raise unittest.SkipTest("node is not installed, so the renderer could not be RUN — that "
                                "is UNKNOWN, not a pass")
    ui = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html"),
                 encoding="utf-8").read()

    def _fn(name):
        i = ui.index("function %s(" % name)
        j, depth, seen = ui.index("{", i), 0, False
        k = j
        while k < len(ui):
            if ui[k] == "{":
                depth += 1
                seen = True
            elif ui[k] == "}":
                depth -= 1
                if seen and depth == 0:
                    return ui[i:k + 1]
            k += 1
        raise AssertionError("could not bound function %s" % name)

    js = _fn("_hrtEsc") + "\n" + _fn("_hrtChron") + """
    var bad = {ok:false, why:'the wire said nothing'};
    console.log(JSON.stringify({
      chronicle: _hrtChron(bad),
      fleet:     _hrtChron(bad, 'The fleet lanes', ' reported as the total')
    }));
    """
    with _tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(js)
        path = fh.name
    try:
        out = _subprocess.check_output([node, path], stderr=_subprocess.STDOUT, timeout=60)
        return _json.loads(out.decode("utf-8", "replace"))
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


class TheSharedRendererTakesEveryWordFromItsCaller(unittest.TestCase):
    """v2473 — the FLEET section printed a row called "the chronicles"."""

    def test_the_error_branch_does_not_hardcode_one_surfaces_noun(self):
        import os as _os
        ui = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "control_ui.html")
        src = io.open(ui, encoding="utf-8").read()
        i = src.find("function _hrtChron(")
        self.assertGreater(i, 0, "_hrtChron is gone; this guard needs re-deriving")
        # the ERROR branch only — bounded by the next `var rows =`, not a character window
        j = src.find("var rows = cc.routes", i)
        self.assertGreater(j, i, "could not find the end of the error branch")
        branch = src[i:j]
        # ⚠⚠ `assertIn("SUBJ", branch)` PASSED ON THE DEFECT. The v2472 review reproduced it:
        # restore the hardcoded "the chronicles" while leaving `var SUBJ = TT;` declared and
        # UNUSED, and this file reported "Ran 12 tests ... OK" while THE FLEET LANES shipped a row
        # headed "the chronicles" — the photographed v2473 defect. A token existing is not a token
        # being used. So the renderer is RUN, for both of its callers, and judged on what it
        # produces. [[source-reading-guard]]
        self.assertNotIn(
            "'the chronicles'", branch,
            "the shared renderer's error branch names one caller's subject. It is used by BOTH "
            "the chronicle routes and the fleet lanes, so the one moment it has something to "
            "report it reports it under the wrong surface's name.")
        rendered = _run_hrt_chron()
        self.assertIn(
            "fleet lanes", rendered["fleet"].lower(),
            "the FLEET error row does not name the fleet. Rendered: %s"
            % rendered["fleet"][:200])
        self.assertNotIn(
            "chronicle", rendered["fleet"].lower(),
            "the FLEET error row still says 'chronicle' — that is the other caller's subject, and "
            "it is the exact row he photographed. Rendered: %s" % rendered["fleet"][:200])
        self.assertIn(
            "chronicle", rendered["chronicle"].lower(),
            "the CHRONICLE error row no longer names the chronicles either — the fix swapped one "
            "wrong subject for another. Rendered: %s" % rendered["chronicle"][:200])


if __name__ == "__main__":
    try:                       # cp1255 cannot encode the ⚠ these tests print
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
