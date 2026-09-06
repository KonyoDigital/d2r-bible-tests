# -*- coding: utf-8 -*-
"""v2746 — A PANEL THAT CANNOT REACH THE SERVER MUST KEEP ITS CONTENT AND SAY IT IS STALE.

Konyo, 2026-09-06, with a screenshot: *"something within the sessions page also task in theres a big
empty space here im pretty sure there was something here"* — the console's Sessions tab rendered its
right-hand rail correctly and the entire main column, roughly 1080x560, was blank. Minutes later:
*"its working now lol it restarted the console"*. It self-resolved, WHICH MEANS NOBODY MEASURED THE
CAUSE. "It went away" is not "it was fixed". [[unknown-stays-unknown]]

The failure mode is the worst-shaped kind: a panel that renders EMPTY rather than erroring says
"there is nothing here", which is indistinguishable from real emptiness. His own first reading was
"im pretty sure there was something here" — he had to REMEMBER the content to know it was wrong.

=== WHAT WAS MEASURED, AND IT REFUTED THE OBVIOUS HYPOTHESIS ===
The suspicion was a fill that blanks on a failed fetch. It is NOT what these panels do — both main
column panels already implement the correct law, and this file pins that so it cannot regress:

  · control_ui.html `_tzPaint`  — on a dead relay it repaints the LAST RECORDED ZONE with
    `stale: true` rather than blaming the network, and only shows "no rotation available" when
    there is no history to fall back on.
  · control_ui.html `_chronXref` — on a failed crossref it repaints `_chronLastSt`.

An empty region is a claim about the DATA. A stale badge is a claim about the CONNECTION. Only the
second one is ever true when the socket dies, and these two panels get that right today.

⚠⚠ AND THE PROBE THAT LOOKED FOR THE OTHER SUSPECT WAS ITSELF WRONG, TWICE — recorded because the
second error is the one this file now guards against.
`console_ui_two_script_blocks` is a carved scar in this repo (a call across the IIFE boundary is a
dead render — FOUR occurrences, the last an inline `ontoggle` firing during parse), and control_ui.html
had NO gate for it. Measuring it:
  1st error: a bare `name(` regex counted `this.classList.add(...)` as a call to a function named
             `add`, producing three false positives.
  2nd error: `<script` matched an occurrence written INSIDE A JS STRING at line ~14102, so the probe
             reported 3 blocks, built 2 spans, and would have published "0 violations" over an
             incomplete corpus. A zero over an unmeasured corpus is UNKNOWN, not clean.
             ⚠ The comment AT that very line warns of this exact class of error. [[zero-needs-a-denominator]]
TRUE STATE, after fixing the instrument: 2 real script blocks, 0 top-level cross-block calls.
The scar is not live here — and now it is watched, so it cannot become live silently.

⛔ WHAT THIS FILE DOES NOT CLAIM. It does not identify the cause of his blank panel. That remains
UNMEASURED, and the row stays open for it. Deliberate reproduction costs HIS screen (a relaunch
under a window he is using is the very thing that caused it), so it is his call to spend, not mine.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _between(src, start, end):
    """Anchored at BOTH ends — never a fixed src[i:i+N] window, which reads past a region as
    ABSENT and has produced four false findings in this repo. [[source-reading-guard]]"""
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return None if j < 0 else src[i:j + len(end)]


def _real_script_spans(src):
    """Script blocks, EXCLUDING `<script` written inside a JS string or comment.

    ⚠ This function exists because the naive version got it wrong. A `<script'` inside a quoted JS
    string at ~line 14102 was counted as a third block. The tell is the character immediately after
    the tag name: a real tag continues to `>`; the string occurrence does not close on the same
    line. Pair opens to closes instead, and require the pairing to be exact."""
    opens = [m.end() for m in re.finditer(r'<script\b[^>\n]{0,120}>', src)]
    closes = [m.start() for m in re.finditer(r'</script\s*>', src)]
    spans = []
    for a in opens:
        nxt = [c for c in closes if c > a]
        if not nxt:
            continue
        b = nxt[0]
        if spans and a < spans[-1][1]:      # nested match => it was inside a string
            continue
        spans.append((a, b))
    return spans


class ADeadFillKeepsItsContent(unittest.TestCase):

    # ── ⚠ THE GUARD MUST FIND ITS SUBJECTS, or it passes having examined nothing ───────────────
    def test_the_guard_can_find_both_panels_AT_ALL(self):
        for fn in ("function _tzPaint", "function _chronXref"):
            self.assertIn(fn, UI,
                          "%s is gone or renamed — fix this guard before trusting a green from it"
                          % fn)

    # ── ⚠⚠ THE LAW: a dead relay keeps the content ────────────────────────────────────────────
    def test_the_tz_panel_repaints_the_LAST_zone_as_stale(self):
        blk = _between(UI, "function _tzPaint", "function _tzWire")
        self.assertIsNotNone(blk, "could not read _tzPaint")
        self.assertIn("stale: true", blk,
                      "the TZ panel no longer marks a fallen-back read as STALE. Without it the "
                      "panel presents a remembered zone as a live one, which is a worse lie than "
                      "blanking.")
        self.assertIn("histZone", blk,
                      "the TZ panel no longer falls back to the last recorded zone, so a dead "
                      "relay blanks a region that had content — an empty region is a claim about "
                      "the DATA, and the true claim here is about the CONNECTION.")

    def test_the_chronicle_panel_repaints_its_LAST_state(self):
        blk = _between(UI, "async function _chronXref", "function _agoMs")
        self.assertIsNotNone(blk, "could not read _chronXref")
        self.assertIn("_chronLastSt", blk,
                      "the chronicle crossref no longer falls back to its last painted state, so a "
                      "failed fetch leaves the main column empty")

    def test_the_tz_panel_still_reports_a_GENUINE_empty(self):
        """⚠ THE OTHER DIRECTION, and it matters as much. A fix that shows stale content forever
        would hide a real outage. When there is no history to fall back on it must SAY SO."""
        blk = _between(UI, "function _tzPaint", "function _tzWire")
        self.assertIn("no rotation available", blk,
                      "the panel no longer distinguishes 'I have an old reading' from 'I have "
                      "nothing at all' — collapsing those is the same defect facing the other way")

    # ── the carved scar, previously unguarded in this file ────────────────────────────────────
    def test_the_probe_itself_counts_only_REAL_script_blocks(self):
        """⚠ THIS IS THE INSTRUMENT TEST, and it is here because the instrument was wrong. A naive
        `<script` regex matches an occurrence inside a JS STRING at ~line 14102 and reports three
        blocks where there are two. [[feedback-suspect-the-instrument]]"""
        spans = _real_script_spans(UI)
        self.assertEqual(2, len(spans),
                         "expected 2 real script blocks in control_ui.html, found %d. If a block "
                         "was genuinely added, update this number AND re-check the cross-block law "
                         "below — do not just bump it." % len(spans))
        naive = len(re.findall(r'<script\b[^>]*>', UI))
        self.assertGreater(naive, len(spans),
                           "the string-literal decoy at ~14102 is gone; if it was removed that is "
                           "fine, but this test's whole reason for existing changed — read it")

    def test_no_top_level_call_crosses_a_script_block(self):
        """The carved `console_ui_two_script_blocks` scar: a call across the IIFE boundary is a DEAD
        RENDER, and it has happened FOUR times. Nothing guarded control_ui.html for it until now."""
        spans = _real_script_spans(UI)
        defined = {}
        for i, (a, b) in enumerate(spans):
            seg = UI[a:b]
            for pat in (r'^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)',
                        r'^\s*(?:const|var|let)\s+([A-Za-z_$][\w$]*)\s*=',
                        r'window\.([A-Za-z_$][\w$]*)\s*='):
                for m in re.finditer(pat, seg, re.M):
                    defined.setdefault(m.group(1), i)
        kw = {'if', 'for', 'while', 'switch', 'catch', 'return', 'function', 'typeof', 'new'}
        bad = []
        for i, (a, b) in enumerate(spans):
            for m in re.finditer(r'^\s{0,2}([A-Za-z_$][\w$]*)\s*\(', UI[a:b], re.M):
                n = m.group(1)
                if n in kw:
                    continue
                # ⚠ a bare `name(` also matches `obj.method(` — require it NOT be preceded by a dot
                if UI[a:b][max(0, m.start(1) - 1):m.start(1)] == '.':
                    continue
                d = defined.get(n)
                if d is not None and d > i:
                    bad.append((i, n, d))
        self.assertEqual([], bad,
                         "a top-level call reaches a function defined in a LATER script block. That "
                         "is a dead render, and it is this repo's carved two-script-block scar: %r"
                         % bad[:6])


if __name__ == "__main__":
    unittest.main(verbosity=2)
