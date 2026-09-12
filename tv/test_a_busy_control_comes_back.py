#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A CONTROL THAT DISABLES ITSELF MUST COME BACK.

Konyo, 2026-09-11: *"the mouse cursor cool one regressed.. its showing a cancel sign where it
doesnt need to sometimes.. like a CANT CLICK here circle with a line diagonal on it blocked.. but
some of them should be showing that we can click on it"*.

⚠⚠ WHY A STUCK BUTTON SHOWS A CANCEL SIGN AND NOTHING ELSE DOES. control_ui.html paints his custom
hand on EVERY element with `*{cursor:var(--kcur) !important}`. Measured: 82 of the 83
`cursor:pointer` rules lose to it. Only THREE rules are written to survive: `text` for inputs, and
`not-allowed` for `.tzz.tzz-thin` and for `button:disabled, .act:disabled`. So the console has no
surviving way to say "clickable" — but `disabled` still says "forbidden", loudly. A control left
disabled after its work finished is therefore the ONE thing that can produce his cancel sign.

MEASURED 2026-09-11: of the 7 onclick handlers that disable themselves, exactly ONE never
re-enabled on any path — `btn-restore-apply`, not on success, not on ok:false, not in the catch.

⚠ This walks handler BODIES by brace matching, never a line-window: a fixed-size read past the end
of a function reports the rest as absent. [[source-reading-guard]] [[the-unjoined-end]]
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

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
_HANDLER = re.compile(r"\$\(\'([\w-]+)\'\)\.onclick\s*=\s*(?:async\s*)?function\s*\([^)]*\)\s*\{")
_SETS = re.compile(r"\bdisabled\s*=\s*true")
_CLEARS = re.compile(r"\bdisabled\s*=\s*false")
_REEVAL = re.compile(r"\bdisabled\s*=\s*!")


def _code(js):
    """JS with comments blanked — NEVER grade prose. [[source-reading-guard]]

    ⚠⚠ THIS LAW CAUGHT ITSELF DOING IT. The first cut searched raw handler bodies, and
    `test_the_restore_apply_button_re_evaluates` went RED against a correct fix — because the
    comment explaining the fix contains the words "never a bare `disabled = false`". The guard was
    grading the sentence that describes the defect, which is the exact failure this repo has
    recorded nine times. Blanked, not deleted, so offsets and brace depth are preserved.
    """
    js = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), js, flags=re.S)
    return re.sub(r"(?m)//[^\n]*", lambda m: " " * len(m.group(0)), js)


def _handlers(src):
    """{id: body} for every $('id').onclick = function(){...}, bodies matched by BRACE DEPTH."""
    out = {}
    for m in _HANDLER.finditer(src):
        start = m.end() - 1
        depth, i = 0, start
        while i < len(src):
            c = src[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out[m.group(1)] = _code(src[start:i + 1])
    return out


class ABusyControlComesBack(unittest.TestCase):

    def test_every_self_disabling_handler_re_enables_on_SOME_path(self):
        """The law. A handler that sets `disabled = true` and has no way back leaves his pointer
        saying forbidden at a control that merely finished."""
        hs = _handlers(UI)
        self.assertTrue(hs, "no onclick handlers parsed — this law examined nothing")
        disabling = {k: v for k, v in hs.items() if _SETS.search(v)}
        self.assertTrue(disabling, "no handler disables itself — the parser found nothing to grade")
        stuck = sorted(k for k, v in disabling.items()
                       if not (_CLEARS.search(v) or _REEVAL.search(v)))
        self.assertEqual([], stuck,
                         "%d of %d self-disabling handlers never re-enable, so after one click "
                         "the pointer says CANNOT CLICK for ever: %r"
                         % (len(stuck), len(disabling), stuck))

    def test_the_restore_apply_button_re_evaluates_rather_than_forcing_true(self):
        """⚠ THE FIX THAT WOULD HAVE BEEN WORSE THAN THE BUG. A bare `disabled = false` here
        re-arms a WRITE: the plan describes names that were MISSING, and once the board has put
        them back it no longer describes the board. Success must CONSUME the plan, and the button
        must re-evaluate from it — a failure re-arms for a retry, a success stays disabled because
        nothing is armed."""
        h = _handlers(UI).get("btn-restore-apply")
        self.assertIsNotNone(h, "the restore-apply handler is gone")
        self.assertIn("__restorePlanned = null", h,
                      "a successful apply does not consume the plan, so the button can be re-armed "
                      "against a plan that no longer describes the board")
        self.assertTrue(_REEVAL.search(h),
                        "the handler forces a boolean instead of re-evaluating from the plan")
        self.assertFalse(_CLEARS.search(h),
                         "a bare `disabled = false` re-arms the write unconditionally")

    def test_the_blanket_cursor_rule_and_its_survivors_are_still_the_reason(self):
        """If the blanket rule ever goes away, this whole law stops being about HIS symptom and
        someone should be told rather than left with a guard whose reason evaporated."""
        # ⚠⚠ v3034 — PIN THE LAW, NOT THE SPELLING. This asserted the literal string
        # `*{cursor:var(--kcur) !important}` and was therefore GREEN through the whole of the
        # regression it was meant to notice: the text was present and his cursor was a plain
        # arrow. What matters is that SOME blanket rule forces the gauntlet on everything.
        # [[regression-guard]]
        self.assertRegex(
            UI, r"\*\{cursor:[^}]+!important\}",
            "the blanket cursor rule is gone — a stuck button may no longer show a cancel sign, "
            "and this law needs re-deriving rather than quietly passing")
        # ⚠⚠ AND IT MAY NOT ROUTE THROUGH var(). Konyo, 2026-09-12: "the cursor mouse custom
        # inside the console again regressed and its a regular mouse cursor" — the second time,
        # v2765 being titled "the gauntlet comes back". `var()` defers validation to
        # COMPUTED-VALUE time, so an image-set this engine cannot resolve makes the declaration
        # invalid-at-computed-value and the property drops to its INITIAL value, `auto`. It does
        # NOT fall back to the plain url() rule above, because the cascade already picked this
        # one. A LITERAL that cannot be parsed is discarded at PARSE time and the url() rule then
        # wins, which is a real fallback rather than an arrow. A WebKit update is enough to flip
        # it, and @supports cannot protect it — a feature query may answer yes while the value
        # still fails to resolve. [[the-unjoined-end]] [[label-outlived-referent]]
        # ⚠ ONLY WHAT THE BROWSER PARSES AS CSS. The first cut of this check searched the whole
        # file and failed on a v2951 JS COMMENT that quotes the rule as prose — a law defeated by
        # a sentence describing it. [[source-reading-guard]]
        import re as _re
        _css = "\n".join(_m.group(1) for _m in
                         _re.finditer(r"<style[^>]*>(.*?)</style>", UI, _re.S | _re.I))
        self.assertIn("cursor:", _css,
                      "no <style> block carries a cursor rule — this law is reading the wrong "
                      "thing, and an empty haystack passes everything")
        for _m in _re.finditer(r"\*\{cursor:([^}]+)!important\}", _css):
            self.assertNotIn(
                "var(", _m.group(1),
                "the blanket cursor rule routes through var(): %r. That converts an unsupported "
                "cursor value into `auto` instead of letting the plain url() rule below take "
                "over, which is exactly how the gauntlet became a plain arrow twice."
                % _m.group(1)[:70])
        self.assertRegex(UI, r"button:disabled,\s*\.act:disabled",
                         "the disabled-cursor rule is gone")


RED_PROOF = [
    {
        "why": "restores the var(--kcur) routing that turned his gauntlet into a plain arrow "
               "twice — the literal is what makes the url() fallback actually reachable",
        "file": "control_ui.html",
        "find": "*{cursor:-webkit-image-set(",
        "replace": "*{cursor:var(--kcur) !important}/*",
        "matches": 1,
    },
    {
        "why": "law: a self-disabling handler must re-enable. Removing the re-evaluation restores "
               "the exact defect he reported - btn-restore-apply stuck disabled after one click, "
               "showing a cancel sign at a control that merely finished.",
        "file": "control_ui.html",
        "find": "      this.disabled = !(_p && _p.missingTotal > 0);",
        "replace": "      /* _HEART2_TAMPERED_ */",
        "matches": 1,
    },
    {
        "why": "law: a successful apply CONSUMES the plan. Without it the button can be re-armed "
               "against a plan that no longer describes the board - a write waiting to happen.",
        "file": "control_ui.html",
        "find": "if (j && j.ok && j.applied) { window.__restorePlanned = null; }",
        "replace": "/* _HEART2_TAMPERED_ */",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
