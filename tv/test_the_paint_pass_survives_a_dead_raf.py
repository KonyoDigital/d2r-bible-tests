# -*- coding: utf-8 -*-
"""THE CURE FOR A STALE COMPOSITE WAS SWITCHED OFF IN THE ONE STATE THAT CAUSES IT.

Konyo, 2026-09-07, with a screenshot of a black room: *"shelf isnt rendering when clicked either"*.

Both shell entry points — `shellHome()` (the TV-D tab) and `showSessions()` — do the pane work
SYNCHRONOUSLY and then repeat it inside `requestAnimationFrame`, commented in the file itself:
*"one more paint tick: WebKit sometimes keeps the last full-viewport composite"*.

⚠⚠ **rAF CALLBACKS DO NOT RUN IN A WINDOW WEBKIT CONSIDERS HIDDEN.** So the second pass — the
actual cure — is dead in exactly the state that produces the stale composite it cures.

MEASURED on his live console while he was looking at the black room, via /api/status:

    hidden true · painting false · frozenBeats 29 · blankStrikes 0 · els 84,514

⚠ AND `hidden` DID NOT MEAN HE WAS NOT LOOKING — he was clicking it. A pywebview window that macOS
reports as OCCLUDED (his Terminal overlapped it) sets visibilityState to hidden while the window is
plainly on screen. The DOM updated correctly on every click — 84,514 elements, intact — and the
pixels never followed. `blankStrikes 0` is why the existing rescue never armed: the window is not
BLANK, it is STALE, and those look different to a paint witness that measures whole-window ink.

=== ⛔ THE TWO FIXES THAT WERE WRONG, AND WHY THEY ARE WORTH RECORDING ===
1. A GLOBAL REPAINT NUDGE on <body> (opacity/transform touch). Rejected on measurement: this page
   has **27 `position: fixed` elements**, and an opacity or transform on an ancestor creates a
   containing block for every one of them — they would reparent for a tick. A full-body reflow over
   84,514 elements is not cheap either.
2. CALLING THE PAIR FROM A `visibilitychange` HANDLER. Rejected on reading the code:
   `_shellRestoreConsole()` removes `shell-open`, so firing it when he returns to the window would
   KICK HIM OUT of whatever board tab he was reading. A fix that loses his place is not a fix.

⇒ So this changes only WHEN the already-trusted pair runs, never what runs.
[[the-unjoined-end]] [[borrowed-surface]] [[console-ui-two-script-blocks]]
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


def _code_only(src):
    """Blank out /* */ and // comments so a law cannot be satisfied by its own prose.
    [[source-reading-guard]]"""
    src = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), src, flags=re.S)
    return re.sub(r"(?m)//[^\n]*", lambda m: " " * len(m.group(0)), src)


CODE = _code_only(UI)


def _fn(name, src=None):
    """A function's source, bounded by the next `function ` at the same indent."""
    s = src if src is not None else CODE
    i = s.find("function %s(" % name)
    if i < 0:
        return None
    j = s.find("\n  function ", i + 1)
    return s[i:j if j > i else i + 4000]


class ThePaintPassSurvivesADeadRaf(unittest.TestCase):

    # ── the law can find its subjects ─────────────────────────────────────────────────────────
    def test_the_guard_can_find_both_shell_entry_points(self):
        """⚠ A law whose subject is renamed passes having examined nothing."""
        for name in ("shellHome", "_shellPaintAgain"):
            self.assertIsNotNone(_fn(name), "%s is gone or renamed — fix this guard before "
                                            "trusting a green from it" % name)

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_the_second_pass_does_not_depend_on_rAF_ALONE(self):
        blk = _fn("_shellPaintAgain")
        self.assertIn("requestAnimationFrame", blk,
                      "the rAF path is gone — it is still the right first choice when it works")
        self.assertIn("setTimeout", blk,
                      "the paint pass depends on requestAnimationFrame ALONE. rAF does not fire in "
                      "a window WebKit thinks is hidden, which is precisely when the composite "
                      "goes stale — the cure would be switched off by the disease.")

    def test_it_runs_the_pair_ONCE_not_twice(self):
        """Both schedulers fire in a visible window. Without a latch the demote/restore pair runs
        twice, which is visible work on an 84,514-element page."""
        blk = _fn("_shellPaintAgain")
        self.assertTrue(re.search(r"\bran\s*=\s*false", blk),
                        "no latch — rAF and the timer would both run the pair")
        self.assertTrue(re.search(r"if\s*\(\s*ran\s*\)\s*return", blk),
                        "the latch is declared but never checked")

    def test_BOTH_call_sites_use_it(self):
        """⚠ One site converted and one left bare is this repo's most repeated defect wearing a
        smaller hat: the bug survives on whichever path was missed."""
        n = len(re.findall(r"_shellPaintAgain\(", CODE))
        self.assertGreaterEqual(n, 3, "expected the helper's definition plus two call sites, "
                                      "found %d occurrence(s)" % n)
        bare = re.findall(r"requestAnimationFrame\(function\(\)\s*\{\s*_shellDemotePane", CODE)
        self.assertEqual([], bare,
                         "a bare requestAnimationFrame still wraps the demote/restore pair, so "
                         "that path still dies in a hidden window")

    # ── ⛔ THE REGRESSION THE FIX MUST NOT BECOME ──────────────────────────────────────────────
    def test_the_pair_is_NOT_called_from_a_visibility_handler(self):
        """`_shellRestoreConsole()` removes `shell-open`. Firing it when he returns to the window
        would drop him out of whatever board tab he was reading — a fix that loses his place."""
        for m in re.finditer(r"visibilitychange[^\n]*\n(?:[^\n]*\n){0,6}", CODE):
            seg = m.group(0)
            self.assertNotIn("_shellRestoreConsole", seg,
                             "the shell restore is wired to visibilitychange, which would kick him "
                             "out of a board tab whenever the window regains focus")

    def test_no_global_body_repaint_nudge_was_introduced(self):
        """This page has 27 position:fixed elements; opacity or transform on body/html creates a
        containing block for all of them."""
        n_fixed = len(re.findall(r"position:\s*fixed", UI))
        self.assertGreater(n_fixed, 10,
                           "expected many fixed elements (found %d) - if this dropped, re-derive "
                           "whether the global-nudge ban still applies" % n_fixed)
        for bad in (r"document\.body\.style\.opacity", r"document\.body\.style\.transform",
                    r"documentElement\.style\.transform"):
            self.assertEqual([], re.findall(bad, CODE),
                             "a global repaint nudge (%s) was introduced; with %d position:fixed "
                             "elements it reparents them for a tick" % (bad, n_fixed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
