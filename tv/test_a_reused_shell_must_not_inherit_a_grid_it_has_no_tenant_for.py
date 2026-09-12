# -*- coding: utf-8 -*-
"""HE SAID IT THREE TIMES — "symetric", "+ typography", "its like not aligned" — AND THE CAUSE WAS
A GRID COLUMN RESERVED FOR A PANEL THAT ISN'T THERE.

`.fx-body` is a TWO-column grid: the content, and a `clamp(300px, 32%, 400px)` right rail for the
`.fx-drill` read-trail aside. Three dialogs reuse the `.fleet-xref` shell for its DESIGN and read
top to bottom: `#fleet-xref`, `#ver-xref`, `#heart-ov`. None of them owns a drill — the only
`.fx-drill` in the file is static markup inside the main fleet window, which is not a
`.fleet-xref`. So for all three, that second column is a rail with no tenant, and whatever child
happens to come second gets dropped into it.

Measured at 1080 on #fleet-xref, 2026-09-12: the JS body is `.fx-cols` + `.fx-foot`, exactly two
children, so `.fx-cols` took column one and THE STATS LINE took the drill's column — rendering
`131/135 yours · 131/135 theirs · 129 shared` beside the "you both need" heading and squeezing the
third column to a sliver. That is what he was pointing at, three separate times.

⚠⚠ THIS IS THE THIRD OCCURRENCE, AND THE SECOND ONE LEFT A NOTE SAYING SO. v2384 hit it on
#ver-xref ("VERSIONS and THE FLEET side by side at equal height, with ~300px of dead space").
v2443 hit it on #heart-ov and its own comment reads: *"The warning was already written directly
above and I walked into it anyway."* Both fixes were written as an ID LIST — `#ver-xref
.fx-body, #heart-ov .fx-body` — so each new panel reusing the shell had to be remembered into it,
and #fleet-xref, the ORIGINAL owner of the class, never was.

So this law does not check that three ids are listed. It checks the SHAPE that stops a fourth:
the override must be selected by the CLASS, so membership is automatic. An id list cannot satisfy
it, which is the whole point — the id list is the defect, not the fix. [[the-unjoined-end]]

⚠ It PARSES the stylesheet by brace-matching rather than grepping for the rule text, because a
grep for `display: block` cannot tell a rule that applies from one buried in an unrelated
@media block, and `source-reading-guard` is explicit that a law reading source must parse it.
"""
import io
import os
import re
import sys
import unittest

HERE_ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE_)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")


def _style_text(src):
    """Every <style> block's contents, concatenated. -> str"""
    return "\n".join(m.group(1) for m in re.finditer(r"<style[^>]*>(.*?)</style>", src, re.S | re.I))


def _rules(css):
    """Brace-matched (selector, declarations) pairs, descending into @media. -> list

    A real parse, not a line regex: it tracks depth so a rule inside `@media` is returned with its
    own selector rather than swallowed whole, and so a `{` inside a declaration value cannot end a
    block early.
    """
    out, i, n, sel_start, depth = [], 0, len(css), 0, 0
    stack = []
    while i < n:
        c = css[i]
        if c == "{":
            head = css[sel_start:i].strip()
            if head.startswith("@"):
                stack.append(head)
                depth += 1
                sel_start = i + 1
            else:
                j, d = i + 1, 1
                while j < n and d:
                    if css[j] == "{":
                        d += 1
                    elif css[j] == "}":
                        d -= 1
                    j += 1
                out.append((head, css[i + 1:j - 1]))
                i = j
                sel_start = i
                continue
        elif c == "}":
            if depth:
                stack.pop()
                depth -= 1
            sel_start = i + 1
        i += 1
    return out


def _decl(decls, prop):
    """The last value given for `prop` (last-rule-wins inside a block). -> str|None"""
    val = None
    for part in decls.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            if k.strip().lower() == prop:
                val = v.strip()
    return val


class TestAReusedShellMustNotInheritAGridItHasNoTenantFor(unittest.TestCase):

    def setUp(self):
        self.src = io.open(UI, encoding="utf-8").read()
        self.css = _style_text(self.src)
        self.rules = _rules(self.css)
        self.assertTrue(self.rules, "the stylesheet parsed to ZERO rules — the parser is broken, "
                                    "and a law that parses nothing passes everything")

    def test_the_shell_really_does_impose_a_two_column_grid(self):
        """The premise. If .fx-body ever stops being a grid this law is obsolete, and it must say
        so loudly rather than keep passing for a reason that no longer exists."""
        grids = [s for s, d in self.rules
                 if ".fx-body" in s and _decl(d, "grid-template-columns")
                 and len((_decl(d, "grid-template-columns") or "").split()) > 1]
        self.assertTrue(grids,
                        "no rule gives .fx-body a multi-column grid any more, so the rail this law "
                        "guards against no longer exists — DELETE this law rather than trust it")

    def test_no_fleet_xref_panel_owns_a_drill(self):
        """The other half of the premise: the rail is empty for these panels. Proven from the
        markup, because if one of them ever DID gain a drill, blocking its grid would be wrong."""
        panels = re.findall(r'<div[^>]*id="([a-z0-9-]+)"[^>]*class="[^"]*\bfleet-xref\b[^"]*"[^>]*>(.*?)</div>',
                            self.src, re.S)
        self.assertGreaterEqual(len(panels), 3,
                                "expected the three known .fleet-xref dialogs, found %d — the "
                                "markup moved and this law is reading the wrong thing" % len(panels))
        for pid, body in panels:
            self.assertNotIn("fx-drill", body,
                             "#%s now contains an .fx-drill, so it genuinely wants the two-column "
                             "grid and this law's premise no longer holds for it" % pid)

    def test_the_override_is_selected_by_class_so_a_fourth_panel_cannot_be_forgotten(self):
        """THE LAW. Not 'the three ids are listed' — 'membership is automatic'."""
        blockers = [s for s, d in self.rules
                    if ".fx-body" in s and (_decl(d, "display") or "").lower() == "block"]
        self.assertTrue(blockers,
                        "NOTHING overrides the .fx-body grid for the reused shell. The stats line "
                        "lands in the drill's empty rail — this is the v2384/v2443/v3033 defect.")
        by_class = [s for s in blockers if re.search(r"\.fleet-xref\s+\.fx-body", s)]
        self.assertTrue(
            by_class,
            "the override exists but is selected by ID (%s). That is exactly the form that failed "
            "twice: every new panel reusing .fleet-xref must be REMEMBERED into the list, and "
            "#fleet-xref never was. Select it by the class." % "; ".join(blockers)[:200])

    def test_the_column_headers_share_one_floor_so_the_lists_start_level(self):
        """His "its like not aligned". The three titles wrap to different line counts, so with
        `align-items: baseline` and no floor each list began at a different y."""
        hs = [d for s, d in self.rules if re.search(r"\.fx-col-h\s*$", s.strip())]
        self.assertTrue(hs, "no .fx-col-h rule found — the column header lost its own styling")
        self.assertTrue(any(_decl(d, "min-height") for d in hs),
                        "the column header declares no min-height, so a title that wraps to two "
                        "lines pushes its list down while a one-line title's list stays up. That "
                        "is the unevenness he reported as 'its like not aligned'.")


# ⚠ The first tamper does not delete the override — it REVERTS it to the id-list form that shipped
# twice and failed twice. That is the sharpest possible proof: the law must go red on the exact
# code that was considered correct in v2384 and v2443, because listing ids is the defect.
RED_PROOF = [
    {
        "why": "reverts the class-selected override to the ID LIST form of v2384/v2443 — the form "
               "that left #fleet-xref out and put the stats line in the drill's empty rail",
        "file": "control_ui.html",
        "find": ".fleet-xref .fx-body { display: block; }",
        "replace": "#ver-xref .fx-body, #heart-ov .fx-body { display: block; }",
        "matches": 1,
    },
    {
        "why": "removes the column header's height floor, so a two-line title pushes its list down "
               "while a one-line title's list stays up — his 'its like not aligned'",
        "file": "control_ui.html",
        "find": "min-height: 2.65em; text-wrap: balance;",
        "replace": "text-wrap: balance;",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
