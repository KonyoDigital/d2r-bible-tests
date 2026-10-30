# -*- coding: utf-8 -*-
"""v3847 - EVERY OVERLAY CLOSES THE SAME WAY (Elad 2026-10-30 14:24/14:27/14:28).

Esc closes the topmost overlay only (the one whose x is not covered), a click outside the overlay closes it,
its x closes it, and Esc with nothing open does nothing.  One contract block does this in the console and in
the board; the copies must stay identical, and every overlay x in either file must be one the contract knows.
Measured by hand in a box headless render (no window on the Mac): forensics, theatre, the Mirror key and the
help sheet all close on Esc, outside click and x; Esc on the Mirror key over the heart closes the key only.
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UI = open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
BIBLE = open(os.path.join(ROOT, "bible.html"), encoding="utf-8").read()
BLOCK = re.compile(r"/\* OVERLAY-CONTRACT v3847.*?/\* /OVERLAY-CONTRACT \*/", re.S)
# x buttons that are not overlays: a banner, a status bar, chips inside a cell or a form
NOT_OVERLAYS = {"fb-x", "rs-x", "vm-cell-x", "cb-mod-x", "cb-grp-x", "mp-pick-x", "mp-bind-x", "vault-find-x",
                "eh-x", "sfp-x", "help-close", "aid-close-btn", "gic-close-btn", "aib-close"}


def _x_classes(src):
    out = set()
    for m in re.finditer(r"<button[^>]*class=\\?[\"']([^\"'\\]+)\\?[\"'][^>]*>\s*([\u00d7\u2715\u2716])", src):
        for c in m.group(1).split():
            if re.search(r"(-x|close|close-btn)$", c):
                out.add(c)
    return out


class EveryOverlayClosesTheSameWay(unittest.TestCase):
    def test_one_contract_in_both_files(self):
        a, b = BLOCK.findall(UI), BLOCK.findall(BIBLE)
        self.assertEqual(len(a), 1, "console must carry the overlay contract once")
        self.assertEqual(len(b), 1, "board must carry the overlay contract once")
        self.assertEqual(a[0], b[0], "the two copies of the overlay contract drifted")

    def test_esc_and_outside_click_close_the_topmost(self):
        c = BLOCK.findall(UI)[0]
        self.assertIn("addEventListener('keydown'", c)
        self.assertIn("e.key !== 'Escape'", c)
        self.assertIn("elementFromPoint", c, "topmost must be the overlay whose x is uncovered")
        self.assertIn("addEventListener('pointerdown'", c)
        self.assertIn("!top.box.contains(e.target)", c)
        self.assertIn("if (!top) return;", c, "Esc with nothing open must do nothing")
        self.assertNotIn("/api/window", c)

    def test_every_overlay_x_is_known_to_the_contract(self):
        sel = re.search(r"var X_SEL = (.*?);\n", BLOCK.findall(UI)[0], re.S).group(1)
        known = set(re.findall(r"\.([a-z0-9-]+)", sel))
        for name, src in (("control_ui.html", UI), ("bible.html", BIBLE)):
            missing = sorted(_x_classes(src) - known - NOT_OVERLAYS)
            self.assertEqual(missing, [], "%s has overlay x buttons the contract does not close: %s" % (name, missing))

    def test_the_help_sheet_has_a_top_right_x(self):
        self.assertRegex(BIBLE, r'<div class="help-content">\s*<button type="button" class="help-x"')

    def test_buttons_glow_and_ease_but_respect_reduced_motion(self):
        for src in (UI, BIBLE):
            css = re.search(r"/\* OVERLAY-X v3847.*?/\* /OVERLAY-X \*/", src, re.S)
            self.assertIsNotNone(css)
            self.assertIn(":hover", css.group(0))
            self.assertIn("transition:", css.group(0))
            self.assertIn("prefers-reduced-motion", css.group(0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
