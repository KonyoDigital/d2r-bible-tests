# -*- coding: utf-8 -*-
"""AN HTML ENTITY HANDED TO AN ESCAPER IS PRINTED AS ITS OWN SOURCE TEXT.

READ OFF HIS SCREEN, 2026-09-16 — the SWEEP box directly under THE FLEET, where the elapsed
figure should be, showed the six literal characters:

    &mdash;

`escC()` replaces `&` with `&amp;`. That is its entire job. So every HTML entity passed through
it comes back out as the text of the entity, and the browser dutifully prints it. Two sites had
it, both in the sweep meter, both written by me:

    escC(took    || '&mdash;')
    escC(elapsed || '&mdash;')

⚠⚠ AND THE OBVIOUS GUARD IS THE WRONG GUARD. A grep for `&mdash;` in this file finds FIVE hits
and only TWO are defects — the other three are concatenated straight into the markup and render
correctly. Same six characters, opposite correctness. A guard that bans the entity would be
wrong three times out of five and would be deleted the first time it blocked a correct line.
[[source-reading-guard]] — the claim is about CODE, so this PARSES rather than greps: it finds
each escaper call, walks to its matching close paren, and asks whether an entity is inside THAT
span. Nothing outside the parentheses can trip it, and a comment cannot satisfy it either.

The fix is always the same: use the CHARACTER. `'\\u2014'` needs no escaping and cannot be
double-escaped by anything downstream. [[label-outlived-referent]]
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

UI = os.path.join(HERE, "control_ui.html")
ESCAPERS = ("escC(", "esc(")
ENTITY = re.compile(r"&[A-Za-z][A-Za-z0-9]{1,9};|&#\d{1,6};")


def _strip_comments(src):
    """block and line comments out, so prose can neither satisfy nor break this."""
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", src)


def _arg_span(src, open_paren):
    """-> the text between `open_paren` and its MATCHING close paren, or '' if unbalanced.

    A depth counter, not a search for the next ')': `escC(String(x) || '&mdash;')` has an inner
    call, and stopping at the first close paren would read only `String(x` and miss the entity
    entirely — the exact shape of the real defect.
    """
    depth, i, n = 0, open_paren, len(src)
    while i < n:
        c = src[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return src[open_paren + 1:i]
        i += 1
    return ""


def _offenders(src):
    code = _strip_comments(src)
    out = []
    for esc in ESCAPERS:
        start = 0
        while True:
            i = code.find(esc, start)
            if i < 0:
                break
            start = i + len(esc)
            # `esc(` also matches the tail of `escC(`; skip that so it is not counted twice
            if esc == "esc(" and i > 0 and code[i - 1] in "Cc":
                continue
            arg = _arg_span(code, i + len(esc) - 1)
            m = ENTITY.search(arg)
            if m:
                line = code.count("\n", 0, i) + 1
                out.append((line, esc.rstrip("("), m.group(0), arg.strip()[:70]))
    return out


class AnEntityInsideAnEscaperIsPrinted(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with io.open(UI, encoding="utf-8") as fh:
            cls.src = fh.read()

    def test_no_escaper_is_handed_an_html_entity(self):
        bad = _offenders(self.src)
        print("   escaper calls scanned for entities: %d offender(s)" % len(bad))
        self.assertEqual([], bad,
                         "an HTML entity is being passed through an escaper, so the page will "
                         "print its source text instead of the character: %r" % (bad[:4],))

    def test_the_parser_actually_finds_one_when_it_is_there(self):
        """[[feedback-blind-fixture-green-gate]] — a scanner never seen find anything is a
        scanner nobody has tested. This is the real defect, verbatim as it shipped."""
        planted = "x = '<span>' + escC(took || '&mdash;') + '</span>';"
        got = _offenders(planted)
        self.assertEqual(1, len(got), "the parser cannot see the defect it exists to find")
        self.assertEqual("&mdash;", got[0][2])

    def test_it_is_NOT_fooled_by_an_entity_OUTSIDE_the_call(self):
        """three of the five real `&mdash;` sites are correct; a guard wrong 3 times in 5 gets
        deleted the first time it blocks a good line."""
        ok = "+ ' onclick=\"window._f(&quot;' + escC(String(m)) + '&quot;)\"'"
        self.assertEqual([], _offenders(ok),
                         "an entity sitting in the surrounding markup was blamed on the escaper")

    def test_it_walks_to_the_MATCHING_paren_not_the_first_one(self):
        """`escC(String(x) || '&mdash;')` — stopping at the first ')' reads `String(x` and the
        entity is never seen."""
        nested = "y = escC(String(took) || '&mdash;');"
        self.assertEqual(1, len(_offenders(nested)),
                         "the argument span stops at the first close paren, so an entity after "
                         "a nested call is invisible")

    def test_a_comment_can_neither_satisfy_nor_break_it(self):
        commented = "/* the elapsed figure said escC(x || '&mdash;') on his screen */\nvar a = 1;"
        self.assertEqual([], _offenders(commented),
                         "prose describing the defect is being reported as the defect")

    def test_the_sweep_meter_uses_the_CHARACTER(self):
        """the two sites that were wrong, pinned by what they should be."""
        code = _strip_comments(self.src)
        self.assertIn("escC(took || '\\u2014')", code,
                      "the sweep meter's cold clock no longer falls back to the em-dash character")
        self.assertIn("escC(elapsed || '\\u2014')", code,
                      "the sweep meter's live clock no longer falls back to the em-dash character")


RED_PROOF = [
    ("control_ui.html", "escC(took || '\\u2014')", "escC(took || '&mdash;')",
     "test_no_escaper_is_handed_an_html_entity"),
    ("control_ui.html", "escC(elapsed || '\\u2014')", "escC(elapsed || '&mdash;')",
     "test_the_sweep_meter_uses_the_CHARACTER"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
