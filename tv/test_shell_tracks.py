#!/usr/bin/env python3
"""THE TRACK COUNT MUST MATCH THE AREA ROW COUNT.  (v2453)

Konyo, twice, with screenshots of a black panel — then he found the cause himself: "maybe it
because i wasnt full screen."

MEASURED, opening the shelf at each size. Width-driven, not height, so a hard breakpoint:
    920x660 -> stage 464   ·   900x900 -> 0   ·   900x680 -> 0   ·   860x700 -> 0   ·  760x900 -> 0
after the fix:
    900x700 -> 218   ·   860x700 -> 218   ·   1440x900 -> 673 (unchanged)

THE CAUSE. `body.theatre-open .shell` carried FIVE track sizes with `!important`:

    grid-template-rows: auto minmax(0, 1fr) 0 auto auto !important;   /* head stage dash tick foot */

written for the DESKTOP layout. At <=900px the rail stops being a column and stacks in, so the
template has SIX rows — "head" "stage" "dash" "rail" "tick" "foot". Every size then lands one row
short of its area, and the computed track list came out `72px 0px 0px 498px 38px 16px`, matching
NO authored rule. That is what made it look impossible, and it is why two earlier diagnoses were
wrong. The `!important` is also why a higher-specificity counter-rule did nothing.

⚠ THIS GUARD PINS THE LAW, NOT THE NUMBERS: a rule that sizes `.shell`'s rows must declare as many
tracks as the areas template it lands on has rows. A fix that only pinned "six values at <=900px"
would go stale the next time a row is added anywhere. [[regression-guard]] [[d2r-css-last-rule-wins]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")


def _strip_comments(src):
    out, i, n = [], 0, len(src)
    while i < n:
        if src.startswith("/*", i):
            j = src.find("*/", i); i = n if j < 0 else j + 2
        elif src.startswith("<!--", i):
            j = src.find("-->", i); i = n if j < 0 else j + 3
        else:
            out.append(src[i]); i += 1
    return "".join(out)


def _tracks(value):
    """Count top-level track sizes, treating minmax(a,b) / repeat(...) as one."""
    out, depth, cur = [], 0, ""
    for ch in value.replace("!important", "").strip():
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch.isspace() and depth == 0:
            if cur.strip():
                out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


class TestShellTrackCounts(unittest.TestCase):

    def setUp(self):
        self.code = _strip_comments(io.open(UI, encoding="utf-8").read())

    def _blocks(self):
        """-> list of (media, selector, declarations) for every rule touching .shell"""
        out = []
        for m in re.finditer(r"@media([^{]+)\{", self.code):
            start = m.end()
            depth, i = 1, start
            while i < len(self.code) and depth:
                if self.code[i] == "{":
                    depth += 1
                elif self.code[i] == "}":
                    depth -= 1
                i += 1
            body = self.code[start:i]
            for sel, decl in re.findall(r"([^{}]+)\{([^{}]*)\}", body):
                if ".shell" in sel:
                    out.append((m.group(1).strip(), sel.strip(), decl))
        return out

    def test_every_shell_row_rule_declares_as_many_tracks_as_its_areas_have_rows(self):
        """★ THE LAW. A five-value rule meeting a six-row template is how the stage vanished."""
        checked = 0
        for media, sel, decl in self._blocks():
            rows = re.search(r"grid-template-rows\s*:\s*([^;]+)", decl)
            if not rows:
                continue
            # the areas template that applies in this same media block
            areas = None
            for m2, s2, d2 in self._blocks():
                if m2 != media:
                    continue
                a = re.search(r"grid-template-areas\s*:\s*([^;]+)", d2)
                if a:
                    areas = a.group(1)
            if not areas:
                continue
            want = len(re.findall(r'"[^"]*"', areas))
            got = len(_tracks(rows.group(1)))
            checked += 1
            self.assertEqual(
                got, want,
                "in @media%s, `%s` declares %d track size(s) for a %d-row areas template. "
                "Every size then lands one row short of its area — which is exactly how the "
                "theatre stage computed to 0px and he saw a black panel."
                % (media, sel.strip()[:48], got, want))
        self.assertGreater(checked, 0,
                           "this guard compared ZERO rules, so it is measuring nothing. Either the "
                           "media blocks changed shape or .shell no longer sizes its rows")

    def test_the_theatre_open_rule_exists_for_the_narrow_layout(self):
        """Without a narrow-scoped rule, the desktop 5-value !important rule wins at <=900px."""
        narrow = [(m, s, d) for m, s, d in self._blocks()
                  if "900px" in m and "theatre-open" in s and "grid-template-rows" in d]
        self.assertTrue(narrow,
                        "no theatre-open row rule is scoped to the narrow layout, so the desktop "
                        "rule's `!important` wins there and the stage collapses")
        _, _, decl = narrow[0]
        self.assertIn("!important", decl,
                      "the narrow rule has no !important, so it cannot beat the desktop rule that "
                      "does — specificity does not outrank !important")
        val = re.search(r"grid-template-rows\s*:\s*([^;]+)", decl).group(1)
        self.assertRegex(val, r"minmax\(\s*2\d\dpx",
                         "the stage track has no pixel floor, so it can still collapse to nothing "
                         "when its only child is absolutely positioned")


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
