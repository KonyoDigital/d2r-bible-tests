# -*- coding: utf-8 -*-
"""THE SECOND EYE MUST BE SHOWN CODE THAT COMPILES, NOT CODE THE TRANSPORT BROKE.

`.second_eye.jsonl` is what the SHIP GATE reads: a version may not push until a different model
family has looked at it. So the PAYLOAD BUILDER is part of the gate, and a builder that corrupts
its own input makes every verdict it collects worthless — the findings AND the cleans.

MEASURED 2026-09-16, and it is the reason this file exists. Grok reviewed v3201 and returned a
FATAL finding:

    "the edit inserts a block of explanatory prose directly into the JavaScript source without an
     opening /* ... the resulting string is not syntactically valid JS."

It was reading its input correctly. THE FILE IS FINE — js_syntax_gate.py parses it in a real JS
engine — and the real diff carried 4 added lines with the warning glyph while the payload carried
1. The transport had deleted them.

THE MECHANISM: `_strip_comments` tested each added line against `_JS_COMMENT` INDEPENDENTLY. This
codebase writes block comments as

    /* TITLE - first line
       continuation prose with NO leading asterisk
       ... */

so the opener matched the pattern and was dropped, and every continuation line did NOT match and
was kept. The eye was handed orphaned prose sitting inside executable code — a syntax error the
transport invented.

⚠⚠ THAT WAS NOT A ONE-OFF. It is every multi-line block comment in this repo, on every look this
instrument has ever done, INCLUDING the ones it called clean. An instrument that corrupts its own
input has no verdict worth the name, in either direction.
[[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]

PROVEN BOTH WAYS on the same commit and the same reviewer:
    corrupted payload -> "fatal: not syntactically valid JS"   (a defect that does not exist)
    clean payload     -> "No defects found."
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import second_eye_run as R


def _added(payload):
    """the code the eye is actually shown, with diff markers removed."""
    out = []
    for ln in payload.splitlines():
        if ln.startswith("+++") or ln.startswith("---"):
            continue
        if ln.startswith("+"):
            out.append(ln[1:])
    return "\n".join(out)


# the real comment shape this repo uses, which is what broke
_REPO_STYLE = """diff --git a/x.js b/x.js
@@ -1,3 +1,9 @@
 var a = 1;
+  /* TITLE - the first line of the block
+     a continuation line with no leading asterisk
+     and another one */
+  var b = 2;
 var c = 3;
"""


class TheEyeIsShownValidCode(unittest.TestCase):

    def test_a_block_comment_is_removed_WHOLE(self):
        """the defect, verbatim in the shape that produced it."""
        got = _added(R._strip_comments(_REPO_STYLE))
        self.assertNotIn("a continuation line with no leading asterisk", got,
                         "the comment BODY survived while its opener was dropped — the eye is "
                         "being shown orphaned prose inside code, which is a syntax error the "
                         "transport invented")
        self.assertNotIn("TITLE - the first line", got)

    def test_the_CODE_around_it_survives(self):
        """stripping must not be allowed to eat the thing under review."""
        got = _added(R._strip_comments(_REPO_STYLE))
        self.assertIn("var b = 2;", got,
                      "the code after the block comment was swallowed — trading manufactured "
                      "findings for silently missing code is the worse direction")

    def test_code_sharing_the_CLOSING_line_survives(self):
        d = "diff --git a/x.js b/x.js\n@@ -1 +1,3 @@\n+  /* open\n+     body */ var kept = 1;\n"
        got = _added(R._strip_comments(d))
        self.assertIn("var kept = 1;", got,
                      "real code on the same line as the comment's closer was discarded")

    def test_code_BEFORE_a_trailing_block_comment_survives(self):
        d = "diff --git a/x.js b/x.js\n@@ -1 +1,3 @@\n+  var kept = 2; /* trailing open\n+     body */\n"
        got = _added(R._strip_comments(d))
        self.assertIn("var kept = 2;", got,
                      "code preceding a run-on block comment on the same line was discarded")

    def test_a_single_line_block_comment_does_NOT_start_a_run(self):
        """`/* x */` closes on its own line; treating it as an opener would swallow the file."""
        d = ("diff --git a/x.js b/x.js\n@@ -1 +1,3 @@\n+  /* one liner */\n"
             "+  var after = 3;\n+  var later = 4;\n")
        got = _added(R._strip_comments(d))
        self.assertIn("var after = 3;", got,
                      "a self-closing block comment swallowed everything after it")
        self.assertIn("var later = 4;", got)

    def test_an_unclosed_block_cannot_swallow_the_next_FILE(self):
        """a diff shows hunks: a block can open in one and close where nothing is shown. Without a
        reset at the boundary, one unclosed opener eats the rest of the payload."""
        d = ("diff --git a/x.js b/x.js\n@@ -1 +1,2 @@\n+  /* opened and never closed here\n"
             "diff --git a/y.js b/y.js\n@@ -1 +1,2 @@\n+  var next_file = 5;\n")
        got = _added(R._strip_comments(d))
        self.assertIn("var next_file = 5;", got,
                      "an unclosed block comment in one file suppressed the next file entirely")

    def test_an_unclosed_block_cannot_swallow_the_next_HUNK(self):
        d = ("diff --git a/x.js b/x.js\n@@ -1 +1,2 @@\n+  /* opened, hunk ends\n"
             "@@ -40 +40,2 @@\n+  var next_hunk = 6;\n")
        got = _added(R._strip_comments(d))
        self.assertIn("var next_hunk = 6;", got,
                      "an unclosed block comment suppressed the following hunk")

    def test_python_comments_still_go(self):
        d = "diff --git a/x.py b/x.py\n@@ -1 +1,3 @@\n+# a note\n+x = 1\n"
        got = _added(R._strip_comments(d))
        self.assertNotIn("a note", got)
        self.assertIn("x = 1", got)

    def test_the_real_repo_style_leaves_NO_orphan_prose(self):
        """the end-to-end property, asserted on the shape that actually shipped: after stripping,
        no added line may be a bare sentence — the signature of an orphaned comment body."""
        got = _added(R._strip_comments(_REPO_STYLE))
        for ln in got.splitlines():
            t = ln.strip()
            if not t:
                continue
            self.assertTrue(
                any(ch in t for ch in "=;{}()[]") or t.startswith(("var ", "def ", "class ")),
                "an added line survived that is prose rather than code: %r" % t)


RED_PROOF = [
    # ⚠ THE FIRST TAMPER HERE WAS A NO-OP: `in_block = False` -> `in_block = True and False`
    # evaluates to the SAME VALUE, so the proof ran green and measured nothing. A sabotage that
    # does not change behaviour is not a sabotage. This one restores the HISTORICAL bug — the
    # suppression run never engages, so a block comment's opener is dropped and its body kept,
    # which is exactly what handed a reviewer a fatal finding about code that compiles.
    # [[sabotage-is-usually-the-wrong-one]]
    ("second_eye_run.py", "            if in_block:", "            if False:",
     "test_a_block_comment_is_removed_WHOLE"),
    ("second_eye_run.py", 'if ln.startswith("diff --git") or ln.startswith("@@")',
     'if ln.startswith("diff --gitXX") or ln.startswith("@@XX")',
     "test_an_unclosed_block_cannot_swallow_the_next_FILE"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
