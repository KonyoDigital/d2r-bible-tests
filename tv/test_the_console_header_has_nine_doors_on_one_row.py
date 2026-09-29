# -*- coding: utf-8 -*-
"""#41 rank 23 (REG-1537, 2026-09-29) — J10'S TAB COUNT AND ITS SILENT-OVERFLOW RULE, AS A PYTHON LAW THE HEART CAN COUNT.

The heart audit (verified list, rank 23): "J10 lives outside heart2's census, and the gate's why still says '15 cases,
25 red-proofs'." heart2 classifies python gates only, and tv/demo_console.mjs's J10 measures the header strip against
the live console (:17772 on his Mac, the demo on CI) — so the nine doors and the no-silent-scroll rule had no law in
tv/test_*.py, and no RED_PROOF anywhere could say whether a missing door would be seen.

WHAT THIS LAW DRIVES, over the console page (tv/control_ui.html) and the DOM gate (tv/demo_console.mjs) as they are:
  · THE NINE DOORS, IN ORDER: the #head-tabs strip holds exactly nine `.ht` buttons — session · forge · crafts · funi ·
    fsets · tools · chars · vault · tvd — each with a data-tab and a label (.ht-lbl); the 👤 Characters door sits
    between Tools and the Vault (his 2026-09-27 ruling, v3518). HTML comments are stripped first: the strip's own
    comments name tabs in prose.
  · TWO SOURCES MUST AGREE: J10's constant (`if (r.tabs !== N)`) is read out of demo_console.mjs and must equal the
    markup's count. A new tab must move both on purpose; a tab that silently leaves the DOM reads short in both.
  · NO SILENT OVERFLOW: J10's `silent` rule (#66) — `overflow-x: auto|scroll` with `scrollbar-width: none` on
    .head-tabs means a tab that runs out of room is simply NOT THERE. The base-level (outside any @media) .head-tabs
    declarations are folded in source order, last wins, and that pair must not stand.
⚠ WHAT THIS LAW CANNOT DO: the ROW COUNT is a pixel measurement (heights at 900-1920 px) and stays J10's, on the live
console and on CI. This is the static half the census can count and a RED_PROOF can tamper.
RED_PROOF below.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

UI = os.path.join(HERE, "control_ui.html")
DEMO = os.path.join(HERE, "demo_console.mjs")
NAV_START = '<nav class="head-tabs" id="head-tabs">'
DOORS = ["session", "forge", "crafts", "funi", "fsets", "tools", "chars", "vault", "tvd"]


def _read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def _strip_html_comments(s):
    return re.sub(r"<!--.{0,4000}?-->", "", s, flags=re.S)


def strip_of(ui=None):
    """The header strip's markup, comments stripped. -> str"""
    s = ui if ui is not None else _read(UI)
    n = s.count(NAV_START)
    assert n == 1, "the header strip anchor is not unique (%d) — the law would grade the wrong nav" % n
    i = s.index(NAV_START)
    j = s.index("</nav>", i)
    return _strip_html_comments(s[i:j])


def doors_of(nav):
    """-> [(data-tab, has-label)] for every .ht button in the strip, in order"""
    out = []
    for m in re.finditer(r'<button class="ht(?:[^"]*)"([^>]*)>(.*?)</button>', nav, flags=re.S):
        tab = re.search(r'data-tab="([^"]+)"', m.group(1))
        out.append((tab.group(1) if tab else None, 'class="ht-lbl"' in m.group(2)))
    return out


def j10_tab_count(demo=None):
    """J10's own constant, read out of the DOM gate. -> int"""
    s = demo if demo is not None else _read(DEMO)
    hits = re.findall(r"if \(r\.tabs !== (\d+)\)", s)
    assert len(hits) == 1, "J10's tab constant is not where this law looks (%d hits)" % len(hits)
    return int(hits[0])


def base_head_tabs_style(ui=None):
    """The base-level .head-tabs declarations, folded in source order (last wins). -> {prop: value}

    Base-level = a rule at brace depth 0 of a <style> block, so a rule inside @media does not count: the media rules
    tighten gaps at narrow widths and never own the overflow. CSS comments are stripped first (bounded, never a
    DOTALL `.*?` that eats a third of the file — source-reading-guard). A rule whose selector LIST contains
    .head-tabs beside other selectors is not the strip's own rule and is left out.
    """
    s = ui if ui is not None else _read(UI)
    got = {}
    for block in re.findall(r"<style[^>]*>(.*?)</style>", s, flags=re.S):
        css = re.sub(r"/\*.{0,4000}?\*/", "", block, flags=re.S)
        depth, sel, i = 0, [], 0
        while i < len(css):
            c = css[i]
            if c == "{":
                head = "".join(sel).strip()
                sel = []
                j = css.find("}", i + 1)
                if depth == 0 and head == ".head-tabs":
                    body = css[i + 1:j if j >= 0 else len(css)]
                    if "{" not in body:
                        for decl in body.split(";"):
                            if ":" in decl:
                                k, v = decl.split(":", 1)
                                got[k.strip().lower()] = v.strip().lower()
                if depth == 0 and head.startswith("@"):
                    depth += 1           # an @media block: its rules are not base-level
                    i += 1
                    continue
                if depth == 0:
                    i = j + 1 if j >= 0 else len(css)
                    continue
                depth += 1
            elif c == "}":
                depth = max(0, depth - 1)
                sel = []             # a closed block leaves no selector text behind (the first cut carried a nested body into the next head)
            else:
                sel.append(c)
            i += 1
    return got


class TheConsoleHeaderHasNineDoorsOnOneRow(unittest.TestCase):

    def test_the_strip_holds_the_nine_doors_in_order_each_with_a_label(self):
        doors = doors_of(strip_of())
        self.assertEqual(DOORS, [d[0] for d in doors], "the header strip's doors moved: %r" % [d[0] for d in doors])
        self.assertTrue(all(d[1] for d in doors), "a door has no .ht-lbl label: %r" % [d for d in doors if not d[1]])
        self.assertEqual(DOORS.index("tools") + 1, DOORS.index("chars"), "👤 Characters does not follow Tools")
        self.assertEqual(DOORS.index("chars") + 1, DOORS.index("vault"), "the Vault does not follow 👤 Characters")

    def test_the_dom_gate_and_the_markup_agree_on_the_count(self):
        self.assertEqual(len(doors_of(strip_of())), j10_tab_count(),
                         "demo_console.mjs J10 counts a different number of tabs than the markup holds")

    def test_the_strips_own_comments_are_not_doors(self):
        """the v2092 comment inside the nav names 'session · forge · funi · fsets · tools · tvd' in prose"""
        raw = _read(UI)
        i = raw.index(NAV_START)
        self.assertIn("<!--", raw[i:raw.index("</nav>", i)], "the fixture premise is gone: the nav carries no comment")
        planted = raw.replace(NAV_START, NAV_START + '<!-- <button class="ht" type="button" data-tab="ghost"><span class="ht-lbl">Ghost</span></button> -->', 1)
        self.assertEqual(len(DOORS), len(doors_of(strip_of(planted))), "a commented-out button was counted as a door")

    def test_no_silent_overflow_on_the_strip(self):
        got = base_head_tabs_style()
        self.assertIn("overflow-x", got, "the strip declares no base-level overflow-x — the rule this law grades is gone")
        self.assertIn("scrollbar-width", got, "the strip declares no base-level scrollbar-width")
        silent = got["overflow-x"] in ("auto", "scroll") and got["scrollbar-width"] == "none"
        self.assertFalse(silent, "overflow-x:%s with scrollbar-width:none — a tab that runs out of room vanishes silently (#66)"
                         % got["overflow-x"])

    def test_the_style_fold_is_driven_both_ways(self):
        """the fold must SEE the silent pair when it stands, take the LAST base rule, and ignore @media rules"""
        ui = ('<style>.head-tabs { overflow-x: auto; scrollbar-width: none; }\n'
              '@media (max-width: 900px){ .head-tabs { overflow-x: visible; } }\n'
              '/* .head-tabs { overflow-x: visible; } */</style>')
        got = base_head_tabs_style(ui)
        self.assertEqual({"overflow-x": "auto", "scrollbar-width": "none"}, got)
        ui2 = ui.replace("</style>", ".head-tabs { flex-wrap: wrap; overflow-x: visible; }</style>")
        self.assertEqual("visible", base_head_tabs_style(ui2)["overflow-x"], "the later base rule did not win")
        ui3 = '<style>.topbar .head-tabs, .x { overflow-x: auto; }</style>'
        self.assertEqual({}, base_head_tabs_style(ui3), "a selector list that is not the strip's own rule was folded")

    def test_the_door_parser_is_driven_both_ways(self):
        nav = NAV_START + '<button class="ht" type="button" data-tab="a"><span class="ht-lbl">A</span></button>' \
              '<button class="ht ht-icon" type="button" data-tab="b" title="B"><span class="ht-emo">x</span><span class="ht-lbl">B</span></button>' \
              '<button class="ht" type="button" data-tab="c">no label</button></nav>'
        self.assertEqual([("a", True), ("b", True), ("c", False)], doors_of(strip_of(nav)))
        self.assertEqual(7, j10_tab_count("if (r.tabs !== 7) bad.push('x');"))


RED_PROOF = [
    {
        "why": "#41 rank 23 - the Crafts door leaves the strip: eight doors, and the DOM gate's 9 disagrees with the markup",
        "file": "control_ui.html",
        "find": '          <button class="ht" type="button" data-tab="crafts"><img class="ht-i" src="/art/logo_cube.png" alt="" onerror="this.remove()"> <span class="ht-lbl">Crafts</span></button>\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 23 - the v2099 wrap rule stops overriding the silent scroll: overflow-x auto + scrollbar-width none stands again (#66)",
        "file": "control_ui.html",
        "find": "  .head-tabs { flex-wrap: wrap; row-gap: 6px; overflow-x: visible; }\n",
        "replace": "  .head-tabs { flex-wrap: wrap; row-gap: 6px; }\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 23 - J10 is told to expect eight tabs while the strip holds nine: the two sources part",
        "file": "demo_console.mjs",
        "find": "if (r.tabs !== 9) bad.push(",
        "replace": "if (r.tabs !== 8) bad.push(",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
