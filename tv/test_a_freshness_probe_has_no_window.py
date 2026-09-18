# -*- coding: utf-8 -*-
"""v3294 — A "DID IT NAVIGATE?" PROBE MUST NOT DEPEND ON WHEN YOU ASK.

`crest_loudness` reloads the page and refuses to score until it can prove the document is NEW —
correctly, because capturing the page the reload was meant to replace is exactly the false reading
the gate exists to prevent.

⚠⚠ ITS PROOF WAS A CLOCK, AND THAT MADE IT A RACE. It sampled `performance.now()` before the
reload and waited for a reading BELOW it, since the clock restarts at ~0 on a real navigation.
**That is only observable for `_before` milliseconds after the navigation.** A page open a long
time gives a large `_before` and an easy test; a page that had just loaded gives a small one, and
the whole window can close between two 0.1s polls.

MEASURED 2026-09-18, back to back, nothing else changing:

    run 1   exit 0 in  6s   "the crest is #151, behind .help-btn"
    run 2   exit 2 in 21s   "no new document within 20s of the reload"

It blocked two pushes on a tree that was fine. **A gate that intermittently cannot measure spends
its credibility on noise**, and the next real UNKNOWN gets waved through as "that flake again".
After the fix: five consecutive runs, 5-6s each, all green.

A MARKER has no window: a new document simply does not carry it, for as long as it takes to look.

⚠ THE REFUSAL IS UNCHANGED AND MUST STAY. A page that genuinely did not navigate is still
UNKNOWN, and still returns 2. This fixed WHEN the probe can see the truth, not WHETHER it insists
on it. [[unknown-stays-unknown]] [[a-gate-can-perturb-what-it-measures]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

from frame_authority import _executable_only  # noqa: E402

SRC = os.path.join(HERE, "crest_loudness.py")


class TestAFreshnessProbeHasNoWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = _executable_only(io.open(SRC, encoding="utf-8").read(), SRC)

    def _loop(self):
        i = self.code.find('t.send("Page.reload")')
        self.assertGreater(i, -1, "the reload vanished")
        j = self.code.find("if _fresh is False", i)
        self.assertGreater(j, i, "the refusal vanished")
        return self.code[i:j]

    def test_the_probe_is_a_marker_not_a_clock(self):
        loop = self._loop()
        self.assertIn("typeof window.__crestGen", loop,
                      "the freshness test no longer asks for a marker a new document cannot have")
        self.assertNotIn("performance.now()", loop,
                         "performance.now() is back in the freshness loop - it is only observable "
                         "for `_before` milliseconds after the navigation, so the probe's "
                         "reliability depends on how long the page happened to be open")

    def test_the_marker_is_set_before_the_reload(self):
        head = self.code[:self.code.find('t.send("Page.reload")')]
        self.assertIn("window.__crestGen", head,
                      "nothing marks the OLD document, so its absence afterwards proves nothing")

    def test_a_page_that_did_not_navigate_is_still_refused(self):
        """The half that must not be softened: this fixed WHEN it can see, not WHETHER it insists."""
        self.assertIn("if _fresh is False", self.code,
                      "the refusal is gone - a gate that scores the page the reload was meant to "
                      "replace is the false reading this whole wait exists to prevent")
        tail = self.code[self.code.find("if _fresh is False"):]
        self.assertIn("return 2", tail[:600],
                      "it no longer returns non-zero, so an unmeasured state would read as a pass")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "putting the clock back restores a probe whose window can close between two polls",
        "file": "tv/crest_loudness.py",
        "find": '                    if t.ev("String(typeof window.__crestGen)").strip() == "undefined":',
        "replace": '                    if float(t.ev("String(performance.now())")) < 1e9:',
        "matches": 1,
    },
    {
        "why": "not marking the old document leaves the absence test proving nothing",
        "file": "tv/crest_loudness.py",
        "find": "            t.ev(\"String(window.__crestGen = 'v3294')\")",
        "replace": "            pass",
        "matches": 1,
    },
    {
        "why": "softening the refusal lets it score the page the reload was meant to replace",
        "file": "tv/crest_loudness.py",
        "find": "        if _fresh is False:",
        "replace": "        if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
