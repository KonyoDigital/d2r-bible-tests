#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2821 (#45) — "CLICK A BANKED NAME, SEE THE ACTUAL FRAME FULL-SCREEN."

That is the ticket verbatim, and until now the NAME was inert text. The only route to the proof was
a 15px picture icon beside it that opened the raw JPEG in a NEW BROWSER TAB — and only when the page
was served from the console (:17772/:17771). Off-console it rendered dimmed and did nothing at all.

Meanwhile a real full-screen lightbox has existed in this same file since v741 — `#tvd-frame-lb` /
`window._tvdOpenFrame`, built for "the last frame the AI read" in Session History — and NOTHING in
the routing ledger ever called it. Both halves shipped; they never met. [[the-unjoined-end]]

★ AND IT IS CLICKABLE OFF-CONSOLE TOO, DELIBERATELY. `_tvdOpenFrame` carries its own honest
fallback chain — bridge, then the archived file, then a plain "missing" message. MEASURED
2026-09-09: 739 of 10,318 cited frames no longer resolve to a file. A reader is far better served by
a lightbox that SAYS the proof is gone than by a dimmed icon that silently does nothing.
[[unknown-stays-unknown]]

⚠ THE FIRST CUT CALLED `jsq()` — the forge IIFE's escaper — which is not in this scope at all.
Measured: 0 occurrences before this function. That is a ReferenceError thrown while BUILDING the
row, which would have taken down the whole routing ledger rather than one link. `esc` genuinely is
in scope; `jsq` never was.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import source_window as _sw  # noqa: E402

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _bible():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _code(s):
    """Comments stripped — this file has been fooled by its own prose before."""
    return _sw.strip_js_comments(s)


class TestABankedNameOpensItsProof(unittest.TestCase):

    def setUp(self):
        if not os.path.isfile(BIBLE):
            self.skipTest("bible.html is not on this machine")
        self.src = _bible()
        self.fn = _sw.block(self.src, "function _bankedName(r){", what="the banked-name builder")
        self.code = _code(self.fn)

    def test_the_name_itself_opens_the_lightbox(self):
        """★ THE TICKET. A cursor:zoom-in with no handler looks identical and does nothing."""
        self.assertIn("_tvdOpenFrame", self.code,
                      "the banked name does not call the full-screen lightbox — the only route to "
                      "the proof is still a small icon opening a raw JPEG in another tab")
        self.assertIn("onclick", self.code,
                      "nothing binds a click to the name, so it is decorative")

    def test_it_is_not_gated_on_being_served_from_the_console(self):
        """739 of 10,318 cited frames are already gone; a reader deserves to be TOLD, not shown a
        dimmed icon. The lightbox has its own bridge/archive/missing chain."""
        self.assertNotIn("onConsole", self.code,
                         "the banked name is gated on onConsole again — off-console it would go "
                         "back to being inert, and the lightbox's own honest 'missing' path would "
                         "never be reachable")

    def test_a_row_with_no_frame_is_plain_text_not_a_dead_handle(self):
        """A control that cannot do anything must not look like one. [[unknown-stays-unknown]]"""
        self.assertIn("if (!r.frameId)", self.code,
                      "every row renders as clickable regardless of whether it cites a frame — a "
                      "handle that opens nothing is worse than plain text")

    def test_the_escaper_it_uses_is_actually_IN_SCOPE(self):
        """⚠ THE ONE THAT NEARLY SHIPPED. jsq() belongs to the forge IIFE; calling it here throws
        while BUILDING the row and takes the whole ledger down with it."""
        self.assertEqual(self.code.count("jsq("), 0,
                         "_bankedName calls jsq(), which is not defined in this scope — that is a "
                         "ReferenceError during render, not a broken link")
        head = self.src[:self.src.index("function _bankedName(r){")]
        self.assertNotIn("function jsq(", head,
                         "jsq is now defined before this point; if that is deliberate this law "
                         "must be re-measured rather than deleted")
        self.assertIn("esc(", self.code, "the name is not HTML-escaped at all")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "un-calling the lightbox returns the name to inert text — the ticket's whole subject",
        "file": "bible.html",
        "find": 'var call = "window._tvdOpenFrame && window._tvdOpenFrame(\'"',
        "replace": 'var call = "void 0; //"',
        "matches": 1,
    },
    {
        "why": "dropping the no-frame branch makes every row a handle that opens nothing",
        "file": "bible.html",
        "find": "    if (!r.frameId) return '<b>' + nm + '</b>';",
        "replace": "    if (false) return '<b>' + nm + '</b>';",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
