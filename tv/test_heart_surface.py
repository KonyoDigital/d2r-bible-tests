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


class TestAStampMustSurviveARepaint(unittest.TestCase):
    """★ v2445 — THE DEFECT A COLD CROSS-FAMILY LOOK NAMED AND MY OWN PROBE HAD ALREADY MEASURED.

    v2443 moved the mini-auto padlock INSIDE <b id="miniauto-lbl"> so it would sit inline with the
    words rather than stretching to 147px on its own row. That element is rewritten by
    `_miniPaint` with `lbl.textContent = ...` on EVERY POLL — so the stamp existed for a fraction
    of a second at page load and was then destroyed for ever. On his console the padlock was simply
    ABSENT, on the surface whose entire purpose is making the lock KNOWN.

    The probe had said so: it found THREE .lockchip elements where the markup declares four. I read
    past a count that disagreed with the source. [[feedback-suspect-the-instrument]]

    The law: NO ELEMENT THAT CONTAINS A STAMP MAY BE THE TARGET OF A textContent WRITE. Pinned as a
    rule rather than as "#miniauto-lbl specifically", because the next stamp will be put somewhere
    else by someone who has not read this.
    """

    def setUp(self):
        self.src = io.open(UI, encoding="utf-8").read()
        # ⚠ JUDGE CODE, NOT PROSE. The first run of this guard failed on its OWN comment — the note
        # three lines above `_miniPaint` quotes `lbl.textContent = ...` while explaining the defect,
        # and the regex found it and called it live code. The markup scan needs the HTML comments
        # kept out too, or a commented-out stamp counts as a real one.
        # [[source-reading-guard]] [[feedback-comments-vs-code]]
        self.code = self._strip_comments(self.src)

    @staticmethod
    def _strip_comments(src):
        out, i, n = [], 0, len(src)
        while i < n:
            if src.startswith("<!--", i):
                j = src.find("-->", i)
                i = n if j < 0 else j + 3
            elif src.startswith("/*", i):
                j = src.find("*/", i)
                i = n if j < 0 else j + 2
            elif src.startswith("//", i) and not src.startswith("://", i - 1):
                j = src.find("\n", i)
                i = n if j < 0 else j
            else:
                out.append(src[i])
                i += 1
        return "".join(out)

    def _wrappers(self):
        """Every id whose element CONTAINS a .lockchip. -> list of (ancestor_id, chip_id)

        ⚠ A REAL PARSER, because the hand-rolled version was wrong and said so loudly. Walking
        backwards for "the nearest opening tag with an id, whose closing tag has not appeared yet"
        named ONE element (#ch-search) as the parent of all four chips — a `</span>` counting error
        across 6 MB of nested markup. A guard that misidentifies its own subject reports confident
        nonsense, and would have sent the next reader to rewrite an unrelated element.
        """
        from html.parser import HTMLParser

        class _P(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self, convert_charrefs=True)
                self.stack, self.found = [], []

            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                if "lockchip" in (a.get("class") or "").split() or \
                   re.search(r"\blockchip\b", a.get("class") or ""):
                    chip = a.get("id") or "?"
                    for _t, eid in self.stack:
                        if eid:
                            self.found.append((eid, chip))
                if tag not in ("br", "img", "input", "hr", "meta", "link", "source"):
                    self.stack.append((tag, a.get("id")))

            def handle_endtag(self, tag):
                for idx in range(len(self.stack) - 1, -1, -1):
                    if self.stack[idx][0] == tag:
                        del self.stack[idx:]
                        return

        p = _P()
        p.feed(self.code)
        return sorted(set(p.found))

    def test_no_element_holding_a_stamp_is_rewritten_by_textContent(self):
        wrappers = self._wrappers()
        # PRINT THE MATCH COUNT — a guard that silently matched nothing is a guard that passes for
        # the wrong reason, and this repo has paid for that four times. [[regression-guard]]
        self.assertTrue(wrappers,
                        "this guard found ZERO stamp wrappers, so it is measuring nothing. Either "
                        "every .lockchip was removed or the markup shape changed under the regex")
        bad = []
        for eid, chip in wrappers:
            # `$('id').textContent =` , and `var x = $('id')` followed by `x.textContent =`
            if re.search(r"\$\(\s*['\"]%s['\"]\s*\)\s*\.textContent\s*=" % re.escape(eid), self.code):
                bad.append("%s (holds %s) is written directly" % (eid, chip))
                continue
            for vm in re.finditer(r"var\s+(\w+)\s*=\s*\$\(\s*['\"]%s['\"]\s*\)" % re.escape(eid),
                                  self.code):
                var = vm.group(1)
                # ⚠ SCOPED TO THE FUNCTION BODY, NOT THE WHOLE FILE. `lbl` is an ordinary variable
                # name used in several unrelated handlers here; a file-wide search for
                # `lbl.textContent =` would convict this element of somebody else's write. The
                # window is a heuristic (a function body, not a parsed scope) and it is stated as
                # one — it can still miss a write further down its own function. It cannot invent
                # one belonging to a different function, which is the direction that matters.
                # And it reads self.code: the first two runs of this guard failed on its OWN
                # comment, which quotes `lbl.textContent = ...` while explaining the defect.
                window = self.code[vm.end():vm.end() + 3000]
                if re.search(r"\b%s\s*\.textContent\s*=" % re.escape(var), window):
                    bad.append("%s (holds %s) is written via `%s.textContent =`" % (eid, chip, var))
                    break
        self.assertEqual(bad, [],
                         "a stamp lives inside an element that gets rewritten, so it is destroyed "
                         "on the first repaint and the lock silently stops being shown: %s. Give "
                         "the element a text node of its own and write THAT."
                         % "; ".join(bad))


class TestADoorMayNotFailInSilence(unittest.TestCase):
    """★ v2446 — HE FOUND THIS ONE ON HIS OWN SCREEN, and the console had nothing to say about it.

    "now the theatre mode/shelf mode is swallowed i cant see it rendering when i click on it...
    but its like swallowed." Then: "hook that to the heart of the console so it doesnt regress in
    the future either."

    THE DEFECT: the Shelf handler was `if (!TH.open) { await thOpen(); }` with no catch, followed by
    `try { thShelf(true); } catch(e){}`. A REJECTED thOpen() throws straight out of the async
    handler, so thShelf never runs — the stage is left open and empty and NOTHING anywhere says so.
    He photographed a black rectangle.

    ⚠ AND THE CHANNEL TO SAY IT ALREADY EXISTED. ui_fault_record's own docstring reads: "THE
    CONSOLE HAD NO WAY TO SAY IT WAS BROKEN. He found the black-screen stage himself, twice, and
    reported it with screenshots; nothing in the tree knew." That was v2228. This is the third
    time, on the same surface, through a door nobody wired to it.
    """

    def setUp(self):
        self.code = TestAStampMustSurviveARepaint._strip_comments(
            io.open(UI, encoding="utf-8").read())

    def test_the_shelf_door_catches_a_refused_stage(self):
        m = re.search(r"_bshelf\.onclick\s*=\s*async function\s*\([^)]*\)\s*\{(.{0,1400}?)\n  \};",
                      self.code, re.S)
        self.assertIsNotNone(m, "the Shelf handler could not be found — this guard cannot answer, "
                                "which is not the same as passing")
        body = m.group(1)
        self.assertIn("await thOpen()", body, "the handler no longer opens the stage — if that is "
                                              "deliberate this guard is measuring nothing")
        # the await must sit inside a try, and the shelf must still be attempted afterwards
        awaits = body.index("await thOpen()")
        before = body[:awaits]
        self.assertRegex(before[-120:], r"try\s*\{",
                         "`await thOpen()` is not inside a try. A rejected stage throws out of the "
                         "handler and thShelf() never runs, leaving an open black stage and total "
                         "silence — which is exactly what he photographed")
        self.assertLess(body.index("thShelf(true)"), len(body),
                        "the shelf is never attempted")
        self.assertIn("_shelfRefused", body,
                      "nothing reports the refusal. A door that fails silently is worse than one "
                      "that is missing: he cannot tell it from a mis-click")

    def test_the_refusal_reaches_the_console_fault_channel(self):
        """[[the-unjoined-end]] — a reporter with no route is plumbing with no tap."""
        m = re.search(r"function _shelfRefused\b(.{0,1800}?)\n  \}", self.code, re.S)
        self.assertIsNotNone(m, "_shelfRefused is gone")
        body = m.group(1)
        self.assertIn("/api/ui_fault", body, "the refusal never reaches the fault channel")
        self.assertIn("kind", body, "the route REJECTS a fault that does not name its kind (400), "
                                    "so a payload without one is a report nobody ever hears")
        # ⚠ AND IT MUST SAY IT SOMEWHERE VISIBLE WHEN THE STAGE IS NOT. #th-shelfov lives INSIDE
        # #theatre, which is display:none while the theatre is shut — so in the exact case this
        # handler exists for (thOpen rejected, the theatre never came up) the panel message renders
        # into a ZERO-HEIGHT box and he sees nothing. Measured: overlay height 0, full text inside.
        self.assertIn("toast(", body,
                      "the refusal only writes into #th-shelfov, which is inside #theatre and has "
                      "no layout box while the theatre is shut. A message that is only visible "
                      "when the thing works is not an error message")

    def test_the_refusal_handler_is_reachable_so_it_can_be_PROVEN(self):
        """It had never run. Two attempts to reach it failed as instrument errors — overriding
        thOpen only proved the shelf still renders, and overriding thShelf from outside never took
        because it is a closure binding. A refusal handler nobody has watched refuse is a guess."""
        self.assertIn("window._shelfRefused", self.code,
                      "the seam is gone, and with it the only way anything has ever executed this "
                      "handler")

    def test_the_close_control_appears_when_there_is_something_to_close(self):
        """v2443 hid #btn-sim so the Shelf could be the single door. Its handler begins
        `if (TH.open) { thClose(); return; }` and its label becomes "Close Theatre" once open — so
        hiding it unconditionally deleted the way OUT, not a duplicate way in. He said so:
        "it use to say close theatre mode after i click theatre mode"."""
        self.assertRegex(self.code, r"\$\('btn-sim'\)\.hidden\s*=\s*!\s*thOpenNow",
                         "#btn-sim is not tied to whether the theatre is open, so either it is "
                         "always visible (two doors, which he asked me to stop) or always hidden "
                         "(no way to close the theatre, which is how this broke)")


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
