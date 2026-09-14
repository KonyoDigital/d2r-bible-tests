#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3110 (#58) — THE SHELF SHOWS ONE FLOW STRIP, AND IT NAMES THE ENGINE BEHIND IT.

⚠⚠ THIS REPLACES `test_each_flow_strip_names_its_own_engine`, WHICH WAS A LAW ABOUT A WORLD THAT
NO LONGER EXISTS. That law's own docstring (v2819) states its subject plainly:

    "THE SHELF stacks two 'flow' strips in one overlay, deliberately styled to read as one engine
     ... Both use the word PRINTER and mean different things: in the first it is ONE router station
     holding N reels; in the second it is a seven-step internal pipeline."

Its answer to that duplication was to make each strip NAME ITS SOURCE. Konyo's ruling on 2026-09-14,
looking at the same screen: *"thats like two diffrent sections rendering the same"*, *"pipeline ..
its a third section representing the other two"*, *"i would want it unified only visually
obivously"*. Labelling three sources never stopped three axes from reading as three engines — it
explained the duplication instead of removing it.

So the printer spine is gone from the shelf and THIS law changes shape with it:
  · what SURVIVES — a flow strip must still name its engine, and the tag must be VISIBLE
  · what is RETIRED — the clause requiring a SECOND strip to name a second engine
  · what is NEW — there must be exactly ONE flow strip, so the duplication cannot come back

⚠ A REMOVED SECTION NEEDS A GUARD AGAINST ITS RETURN, or the next version quietly re-adds it and
the ruling has to be made twice. Deleting the red law instead of replacing it would have been the
green that lies. [[regression-guard]] [[label-outlived-referent]]

⚠ THE BACKEND IS UNTOUCHED AND THAT IS THE POINT OF THE SCOPE HE SET: *"the backend must represent
the real real routes and coding of it all"*. `/api/reel_story` still returns `printerStations` and
`printerCounts`, `printer.py` still walks every station, and `river.py`/`reel_router` still own the
nine stations. Only the DRAWING changed.

★ AND THE NEAR-MISS THE OLD LAW CAUGHT IS KEPT, GENERALISED. Its `_srcTag` was once BUILT and never
rendered — "a label living in a variable is the same as no label" — so this refuses ANY source-tag
variable that is never concatenated into markup. [[the-unjoined-end]]
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

UI = os.path.join(HERE, "control_ui.html")


def _ui():
    with io.open(UI, encoding="utf-8") as fh:
        return fh.read()



def _executable(text):
    """control_ui.html with its comments stripped, STRING-AWARE. -> str

    ⚠⚠ WITHOUT COMMENT-STRIPPING, A COMMENT ABOUT THE REMOVED STRIP MAKES THIS LAW RED ON CLEAN
    CODE — the first run after the cut counted `shp-st` once, in a v2587 NOTE explaining a shared
    glyph while the markup was already gone.

    ⚠⚠ AND WITHOUT STRING-AWARENESS THE CURE IS WORSE THAN THE DISEASE, which a cross-family read
    of v3110 caught. A naive stripper treats every `//` as a comment — including the one inside
    `https://` and any inside a quoted string — and an unclosed `/*` makes it discard THE REST OF
    THE FILE. Every `assertEqual(count, 0)` in this law then passes on whatever survived: an
    ABSENCE check against a truncated document is a false negative by construction, and it is
    silent. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

    So quotes are tracked, and an unterminated block comment RAISES rather than truncating.
    """
    out, i, n = [], 0, len(text)
    quote = None
    while i < n:
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:          # escape: take the next char verbatim
                out.append(text[i + 1]); i += 2; continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch; out.append(ch); i += 1; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise AssertionError(
                    "unterminated /* block comment at offset %d — refusing to strip, because "
                    "discarding the rest of the file would make every absence check below pass "
                    "on a document that is not there" % i)
            i = j + 2
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(ch); i += 1
    return "".join(out)


def _orphan_source_tags(code):
    """Source-tag variables assigned and never concatenated into markup. -> [name]

    ⚠ EXTRACTED SO IT CAN BE EXERCISED. Inline, this clause was VACUOUSLY GREEN — there is no
    `*srcTag*` variable in the file today, so it asserted nothing and would only speak the day the
    v2819 bug returned. A check that cannot fail on any input it has ever seen is not yet a check;
    the fixture below plants the orphan and proves it speaks. [[feedback-blind-fixture-green-gate]]
    """
    out = []
    for m in re.finditer(r"var\s+(\w*[sS]rcTag\w*)\s*=", code):
        name = m.group(1)
        used = len(re.findall(r"[+]\s*" + re.escape(name) + r"\b", code)) \
            + len(re.findall(r"\b" + re.escape(name) + r"\s*[+]", code))
        if used == 0:
            out.append(name)
    return out



class TestTheShelfShowsOneFlowStrip(unittest.TestCase):

    def setUp(self):
        self.src = _ui()
        self.code = _executable(self.src)

    # ── SURVIVES: the one strip still names its engine ────────────────────────────────────────
    def test_the_river_strip_names_the_router(self):
        head = _sw.between(self.src, 'var H = [\'<div class="shr-head">', "'<div class=\"shr-flow\">'",
                           what="the river strip's header")
        self.assertIn("shr-src", head,
                      "the river strip carries no source tag, so a reader cannot tell which engine "
                      "produced its counts")
        self.assertIn("router", head, "the tag does not name the router as its source")

    def test_the_tag_has_a_style_or_it_is_invisible(self):
        """A tag with no rule is a tag nobody sees — naming the container is not naming the rule.

        ⚠⚠ ASK FOR THE RULE, NOT THE SUBSTRING. The first cut did `assertIn(".shr-src", code)` and
        its red-proof — renaming the selector to `.shr-src-gone` — came back **BLIND**, because
        `.shr-src-gone` CONTAINS `.shr-src`. That is the third time today one spelling of "is this
        string present" has passed through its own defeat. A selector is followed by `{` or `,`;
        anything else is a different selector that merely starts the same way.
        [[sabotage-is-usually-the-wrong-one]] [[source-reading-guard]]
        """
        rules = re.findall(r"\.shr-src\s*[,{]", self.code)
        print("   CSS rules selecting .shr-src exactly: %d" % len(rules))
        self.assertTrue(rules,
                        "no CSS RULE for .shr-src (a bare mention is not a rule), so the source "
                        "tag inherits whatever surrounds it and may not be legible at all")

    # ── NEW: exactly ONE flow strip, so the duplication cannot return ─────────────────────────
    def test_the_printer_spine_does_not_come_back(self):
        """His ruling was that two strips drawing the same route is what confused him. A law that
        only removed it once would let the next version put it back."""
        for token in (".shp-spine", "shp-st", "printerStations"):
            n = self.code.count(token)
            print("   %-16s %d occurrence(s) in control_ui.html" % (token, n))
            self.assertEqual(
                n, 0,
                "the printer spine is drawing on the shelf again (%d x %r) — that is the second "
                "strip whose removal was the whole ruling. The DATA is still served; it is the "
                "SECOND AXIS that may not return." % (n, token))

    def test_only_one_source_tag_is_rendered(self):
        """Two source tags means two strips wearing labels, which is the state he refused."""
        n = self.code.count("shr-src")
        p = self.code.count("shp-head")
        print("   shr-src %d · shp-head %d" % (n, p))
        self.assertEqual(p, 0, "a printer-spine header is back on the shelf")
        self.assertGreaterEqual(n, 1, "the surviving strip lost its source tag entirely")

    # ── SURVIVES, GENERALISED: a tag in a variable is not a tag on the screen ─────────────────
    def test_no_source_tag_is_built_and_left_unrendered(self):
        """★ THE ONE THAT NEARLY SHIPPED WRONG in v2819: `_srcTag` was BUILT and never placed in
        the markup. Generalised so it guards any future spelling rather than that one name."""
        orphans = _orphan_source_tags(self.code)
        print("   source-tag variables built-but-never-rendered: %s" % (orphans or "none"))
        self.assertEqual(orphans, [],
                         "%s is assigned and never concatenated into markup — a label living in a "
                         "variable is the same as no label" % ", ".join(orphans))

    def test_the_orphan_detector_actually_speaks(self):
        """⚠ THE CLAUSE ABOVE IS VACUOUS ON TODAY'S FILE — there is no `*srcTag*` variable at all,
        so it asserts nothing and would first speak the day the bug returns. This plants the exact
        v2819 shape and demands it be named, and plants the fixed shape and demands silence."""
        planted = "var _srcTag = '<span class=\"shr-src\">router</span>';\n_spine = '<b>' + x;"
        fixed = "var _srcTag = '<span class=\"shr-src\">router</span>';\n_spine = '<b>' + _srcTag;"
        print("   planted orphan -> %s · rendered -> %s"
              % (_orphan_source_tags(planted), _orphan_source_tags(fixed) or "none"))
        self.assertEqual(_orphan_source_tags(planted), ["_srcTag"],
                         "the detector did not name a tag that is built and never rendered")
        self.assertEqual(_orphan_source_tags(fixed), [],
                         "the detector names a tag that IS concatenated into markup")

    def test_the_stripper_is_string_aware_and_refuses_truncation(self):
        """⚠⚠ A NAIVE STRIPPER MAKES EVERY ABSENCE CHECK IN THIS LAW A FALSE NEGATIVE. It would
        treat the `//` inside `https://` as a comment, and an unterminated `/*` would discard the
        REST OF THE FILE — after which `assertEqual(count, 0)` passes on a document that is not
        there, silently."""
        kept = _executable('var u = "https://example.com/a"; // dropped')
        self.assertIn("https://example.com/a", kept,
                      "the `//` inside a quoted URL was treated as a comment")
        self.assertNotIn("dropped", kept, "a real // comment survived the strip")
        with self.assertRaises(AssertionError):
            _executable("a /* never closed")
        print("   stripper: URL kept · comment dropped · unterminated /* refused")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "removing the river strip's tag returns it to a count with no engine named — the "
               "surviving half of the original v2819 law",
        "file": "control_ui.html",
        "find": "             + '<span class=\"shr-src\" title=\"4 lanes over reel_router\\u2019s 9 stations, from /api/river\">'",
        "replace": "             + '<span class=\"gone\" title=\"\">'",
        "matches": 1,
    },
    {
        "why": "the printer spine comes back onto the shelf — the second strip drawing the same "
               "route, which is the exact state his ruling removed",
        "file": "control_ui.html",
        "find": "    /* ── 1. the yield bar ─────────────────────────────────────────────────────────────────── */",
        "replace": "    var _back = '<div class=\"shp-spine\"><span class=\"shp-st\">1 IN</span></div>';\n"
                   "    /* ── 1. the yield bar ─────────────────────────────────────────────────────────────────── */",
        "matches": 1,
    },
    {
        "why": "the source tag loses its CSS rule, so it inherits whatever surrounds it and may "
               "not be legible at all",
        "file": "control_ui.html",
        "find": ".shr-src",
        "replace": ".tag-with-no-rule",
        "matches": 2,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
