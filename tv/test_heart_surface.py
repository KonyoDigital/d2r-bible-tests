#!/usr/bin/env python3
"""Guards for ♥ THE HEART as a console SURFACE — the route, and the shell it borrows.

tv/test_heart.py guards the derivation. This guards the parts that were actually wrong on the way
in: a panel that reuses another component's shell inherits its LAYOUT as well as its design, and a
route that fails must fail to UNKNOWN rather than to zero.
"""
import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
UI = os.path.join(HERE, "control_ui.html")
APP = os.path.join(HERE, "control_app.py")


class TestABorrowedShellBringsItsLayout(unittest.TestCase):
    """★ THE ONE THAT ACTUALLY BIT, TWICE IN THIS FILE'S HISTORY.

    `.fx-body` is a two-column grid belonging to the fleet window. #ver-xref reused .fleet-xref /
    .fxr-win to BE the cross-reference window rather than a lookalike, inherited the grid, and had
    to override it — and wrote a warning saying so. v2443 added #heart-ov the same way, three lines
    under that warning, and inherited the same bug: measured at 1440 the diagram was squeezed to its
    640px min-width, THE VALVES were stranded in a right-hand column, and a horizontal scrollbar
    ran under the whole panel.

    So this pins the LAW, not the two panels that exist today: ANY element reusing the fleet shell
    must carry the override. A test naming #heart-ov would go stale the next time someone reuses
    .fleet-xref — which is exactly how this defect arrived the second time.
    [[regression-guard]] [[d2r-css-last-rule-wins]]
    """

    def setUp(self):
        self.src = io.open(UI, encoding="utf-8").read()

    def test_every_panel_reusing_the_fleet_shell_overrides_the_two_column_grid(self):
        borrowers = set(re.findall(r'<div\s+id="([a-z0-9\-]+)"[^>]*class="[^"]*\bfleet-xref\b', self.src))
        # ⚠ THE OWNER IS NOT A BORROWER, and this guard found that on its very first run. The panel
        # whose id IS the shell's class name is the fleet window itself — it AUTHORED the two-column
        # grid and genuinely uses the second column (.fx-drill, 8 uses). Requiring it to override
        # its own layout would be requiring it to break. Discriminating on `id == class` rather than
        # on a hardcoded name keeps this a law: a third borrower is still caught, and if the fleet
        # window is ever renamed the rule follows it instead of going stale. [[regression-guard]]
        borrowers.discard("fleet-xref")
        self.assertTrue(borrowers, "no panel reuses .fleet-xref any more — if that is deliberate "
                                   "this guard is measuring nothing and should be retired, not "
                                   "left to pass vacuously")
        # collect every selector that sets `display: block` on a .fx-body
        overridden = set()
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", self.src):
            if "display" not in body or "block" not in body:
                continue
            if not re.search(r"display\s*:\s*block", body):
                continue
            for part in sel.split(","):
                m = re.search(r"#([a-z0-9\-]+)\s+\.fx-body\s*$", part.strip())
                if m:
                    overridden.add(m.group(1))
        missing = sorted(b for b in borrowers if b not in overridden)
        self.assertEqual(missing, [],
                         "%s reuse(s) the fleet shell without overriding `.fx-body`'s two-column "
                         "grid. Borrowing a component's shell buys its design AND its layout; the "
                         "content will be laid out as grid items side by side, with the later "
                         "sections stranded in a narrow right column." % ", ".join(missing))

    def test_the_heart_carries_a_render_seam_so_the_animation_can_be_proven(self):
        """His console has 0 FLOWING vessels, so the blood animation cannot run on real data. If
        the seam goes, the only way anyone has ever seen it work goes with it."""
        self.assertIn("window._heartRender", self.src,
                      "the render seam is gone. Without it the flow animation, the heartbeat and "
                      "an OPEN padlock can never be rendered on this machine, and an animation "
                      "nobody has seen run is a claim nobody has checked")

    def test_the_widget_sits_in_the_footer_beside_the_version(self):
        """His words: 'a widget HEART on the bottom of the console next to the version... thats
        where it should be located'. A chip that drifts out of the footer is not that."""
        m = re.search(r"<footer>(.*?)</footer>", self.src, re.S)
        self.assertIsNotNone(m, "the footer markup could not be found — this guard cannot answer, "
                                "which is not the same as passing")
        foot = m.group(1)
        self.assertIn('id="heart-chip"', foot, "the heart widget is not in the footer")
        self.assertLess(foot.index('id="foot-ver"'), foot.index('id="heart-chip"'),
                        "the heart widget moved AHEAD of the version stamp; he asked for it "
                        "next to the version, after it")


class TestTheRouteFailsToUnknownNeverToZero(unittest.TestCase):
    """[[unknown-stays-unknown]] — 'nothing runs unwatched' and 'nobody could look' are opposite
    facts, and a heart that renders empty on a broken census claims the safe one."""

    def setUp(self):
        import control_app as C
        self.C = C

    def test_an_unreadable_census_returns_ok_False_with_NO_counts(self):
        import heart as H
        real = H.vessels
        H.vessels = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        self.addCleanup(setattr, H, "vessels", real)
        self.C._HEART_MEMO["v"] = None          # a memo hit would hide the failure entirely
        self.addCleanup(self.C._HEART_MEMO.update, {"t": 0.0, "v": None})
        rep = self.C.heart_state(force=True)
        self.assertFalse(rep["ok"])
        self.assertIsNone(rep["counts"],
                          "a census that could not be taken produced COUNTS. An empty heart and an "
                          "unreadable one look identical on screen and only one of them is safe")
        self.assertIn("boom", rep["why"], "the failure was swallowed — a reason nobody can read is "
                                          "indistinguishable from no failure")

    def test_the_route_is_dispatched_and_calls_heart_state(self):
        """[[the-unjoined-end]] — this repo's most repeated defect is two halves built right and
        never joined. A heart_state() nothing routes to is exactly that."""
        tree = ast.parse(io.open(APP, encoding="utf-8").read())
        found = False
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            for c in node.comparators:
                if isinstance(c, ast.Constant) and c.value == "/api/heart":
                    found = True
        self.assertTrue(found, "/api/heart is not dispatched anywhere in control_app.py")
        self.assertIn("heart_state(force=", io.open(APP, encoding="utf-8").read(),
                      "the route exists but does not reach heart_state()")

    def test_the_memo_is_a_cache_of_a_DERIVATION_and_it_expires(self):
        """A stored picture drifts from the territory; a 45s memo of a derivation does not. If the
        TTL ever became effectively infinite the heart would quietly become a stored diagram."""
        self.assertGreater(self.C._HEART_TTL, 0)
        self.assertLessEqual(self.C._HEART_TTL, 120,
                             "the heart's memo outlives two minutes. It is a cache of a "
                             "derivation, not a stored diagram, and the difference is the TTL")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
