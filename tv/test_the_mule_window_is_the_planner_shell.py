# -*- coding: utf-8 -*-
"""#174 v-A — THE MULE WINDOW IS THE D2PLANNER BUILDER'S SHELL, AT THEIR MEASURED GEOMETRY, AND IT IS A DIALOG.

His words, 2026-09-25: click a mule and a fullscreen window floats over the vault, with the d2planner's EXACT
layout, structure, UI and UX, in OUR theme, over OUR data; Esc goes back to the vault. Their builder was measured
at 2000px wide (DPR 1): a 1350px content column of three columns, LEFT 322 · CENTRE 716 · RIGHT 300, 6px gutters,
and a paper-doll whose ten slots sit at fixed pixel rects on a 30px cell inside a 322x400 EQUIPMENT panel, with the
10x4 inventory under the doll in the same panel.

Two defects this pins, one of each kind:

  · STRUCTURE. The old card was a two-panel in-game replica (stash | inventory+doll) with a doll on a 10x6 grid
    whose slot shapes matched nothing measured. The shell must carry THEIR slot rects exactly — so this law keeps
    its OWN copy of the measured table (the witness) and compares it with what the SHIPPED openMuleCard renders,
    never with the table the page reads (that would compare the code with itself).
  · ESC SENT HIM HOME. The console forwards Esc into the board only for an overlay it recognises —
    `[role="dialog"]:not([hidden])` among its selectors. #vault-detail matched none, so with the console focused
    Esc closed the SHELL and left the mule window up behind it. The window now declares itself a dialog, from the
    markup AND from openMuleCard, and the console's probe still lists that selector (the other end of the join).

And the honesty rule: a locker has no class, no level and nothing equipped, so every stat is UNKNOWN with a reason
— never a 0, which would read as "measured, and zero". [[unknown-stays-unknown]]

  · DRIVEN (node): the SHIPPED vault span — packer, grid, loader, openMuleCard, close, the Esc listener — is cut
    out of bible.html and run over a minimal DOM stub; every assertion reads what it rendered.
  · READ (source): the CSS column widths and panel heights, the static markup's dialog role, and the console's
    Esc probe selector — each anchored on a string that occurs exactly once.
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")

# ── THE WITNESS: their builder, measured at 2000x1300, DPR 1 (spec #174 §1). Slot rects relative to the
#    322x400 EQUIPMENT panel: x, y, w, h. This table is deliberately NOT read from the page. ──
THEIR_SLOTS = {
    "rarm": (16, 65, 60, 120),   # right weapon
    "larm": (247, 65, 60, 120),  # left weapon / shield
    "head": (131, 50, 60, 60),
    "neck": (203, 102, 30, 30),  # amulet
    "tors": (131, 125, 60, 90),  # body armor
    "glov": (15, 199, 60, 60),
    "rrin": (88, 230, 30, 30),
    "belt": (131, 230, 60, 30),
    "lrin": (203, 230, 30, 30),
    "feet": (247, 199, 60, 60),
}
THEIR_COLUMNS = {"left": 322, "centre": 716, "right": 300, "gutter": 6, "column": 1350}
THEIR_HEIGHTS = {            # panel heights, same capture
    ".mp-eq": 400, ".mp-prim": 102, ".mp-merc": 80, ".mp-loot": 88,
    ".mp-cp": 628, ".mp-notes": 206, ".mp-stats": 726, ".mp-set": 84,
}
STAT_GROUPS = ["ATTRIBUTES", "DEFENSES", "RESISTANCES", "WEAPON", "SPELLS", "ADVENTURE"]

CUT_START = "  var _MULE_COPY_CAP = 3;"
CUT_END = "  // v210: live re-pack — any assignment change re-tetrises an OPEN mule card\n"
MARKUP = re.compile(r'<div class="vault-detail" id="vault-detail"([^>]*)></div>')
PROBE_START = "// 2) probe the BOARD inside the iframe for a visible overlay; if one is up, feed it the Esc."
PROBE_END = "// 3) nothing on the board — close the shell."


def _src(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def _vault_span():
    s = _src("bible.html")
    assert s.count(CUT_START) == 1, "the packer anchor is not where this law looks"
    assert s.count(CUT_END) == 1, "the re-pack anchor is not where this law looks"
    i = s.index(CUT_START)
    j = s.index(CUT_END, i)
    return s[i:j]


def _static_attrs():
    s = _src("bible.html")
    hits = MARKUP.findall(s)
    assert len(hits) == 1, "expected ONE #vault-detail element in the markup, found %d" % len(hits)
    attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', hits[0]))
    if re.search(r'(^|\s)hidden(\s|$)', re.sub(r'"[^"]*"', '""', hits[0])):
        attrs["hidden"] = ""
    return attrs


HARNESS = r"""
var LISTEN = {}, WLISTEN = {}, switched = [];
function mkEl(attrs){
  var cls = {}, a = {};
  Object.keys(attrs || {}).forEach(function(k){ a[k] = attrs[k]; });
  return { hidden: Object.prototype.hasOwnProperty.call(a, 'hidden'), innerHTML: '', scrollTop: 0, parentElement: null,
    classList: { add: function(c){ cls[c] = 1; }, remove: function(c){ delete cls[c]; }, contains: function(c){ return !!cls[c]; } },
    setAttribute: function(k, v){ a[k] = String(v); }, getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(a, k) ? a[k] : null; },
    removeAttribute: function(k){ delete a[k]; }, querySelector: function(){ return null; } };
}
var box = mkEl(%(attrs)s);
var body = { appendChild: function(el){ el.parentElement = body; } };
var document = { body: body, documentElement: mkEl({}),
  getElementById: function(id){ return id === 'vault-detail' ? box : null; },
  querySelector: function(sel){ return sel === '.tab.active' ? { dataset: { tab: 'vault' } } : null; },
  querySelectorAll: function(){ return []; },
  addEventListener: function(n, f){ (LISTEN[n] = LISTEN[n] || []).push(f); } };
var window = { innerWidth: %(w)d, innerHeight: %(h)d, switchTab: function(t){ switched.push(t); },
  addEventListener: function(n, f){ (WLISTEN[n] = WLISTEN[n] || []).push(f); } };
function setTimeout(f){ f(); } function clearTimeout(){}
var roster = [{ id: 'uni-weap', name: 'UNI-WEAPONS', icon: 'W', note: 'unique melee + caster weapons' },
              { id: 'bases', name: 'SOCKETED', icon: 'S', note: 'socketed bases' },
              { id: 'empty', name: 'EMPTY-ONE', icon: 'E', note: '' }];
function muleById(id){ for (var i = 0; i < roster.length; i++) if (roster[i].id === id) return roster[i]; return null; }
var assign = %(assign)s, SIZES = %(sizes)s;
function vaultSize(n){ return SIZES[n] || [2, 4]; }
function tipOf(){ return null; }
function copyCount(){ return 1; }
function art(n){ return '<i class="a">' + n + '</i>'; }
function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
function jsArg(t){ return String(t).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
function _renderSharedStash(){}
%(span)s
window.openMuleCard(%(mule)s);
var out = { html: box.innerHTML, role: box.getAttribute('role'), modal: box.getAttribute('aria-modal'),
            label: box.getAttribute('aria-label'), hidden: box.hidden, fs: box.classList.contains('vd-fs'),
            on: box.classList.contains('mp-on') };
if (%(page)d >= 0){ window._muleSetPage(%(page)d); out.html2 = box.innerHTML; }
if (%(esc)s){
  (LISTEN.keydown || []).forEach(function(f){ f({ key: 'Escape', target: null, preventDefault: function(){} }); });
  out.after = { hidden: box.hidden, fs: box.classList.contains('vd-fs'), on: box.classList.contains('mp-on'), switched: switched };
}
console.log(JSON.stringify(out));
"""

SMALL = {"Windforce": [2, 4], "Stone of Jordan": [1, 1], "Shako": [2, 2], "Arachnid Mesh": [2, 1]}


def _drive(mule="uni-weap", w=2000, h=1300, assign=None, sizes=None, page=-1, esc=False, attrs=None):
    if assign is None:
        assign = dict((n, "uni-weap") for n in SMALL)
    js = HARNESS % {
        "attrs": json.dumps(_static_attrs() if attrs is None else attrs),
        "w": w, "h": h, "assign": json.dumps(assign), "sizes": json.dumps(sizes or SMALL),
        "span": _vault_span(), "mule": json.dumps(mule), "page": page, "esc": "true" if esc else "false",
    }
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("the shipped mule window would not run - UNKNOWN, not passing: %s" % r.stderr[:600])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _unit(html):
    m = re.search(r'<div class="mp[^"]*" style="--u:([0-9.]+)px"', html)
    assert m, "the window carries no --u unit"
    return float(m.group(1))


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheDollIsTheirs(unittest.TestCase):

    def test_the_ten_slots_sit_at_their_measured_rects(self):
        html = _drive()["html"]
        got = {}
        for m in re.finditer(r'data-slot="(\w+)" style="left:calc\((\d+)\*var\(--u\)\);top:calc\((\d+)\*var\(--u\)\);'
                             r'width:calc\((\d+)\*var\(--u\)\);height:calc\((\d+)\*var\(--u\)\)"', html):
            got[m.group(1)] = tuple(int(x) for x in m.groups()[1:])
        self.assertEqual(len(re.findall(r'class="mp-slot', html)), 10, "the doll does not have ten slots")
        self.assertEqual(got, THEIR_SLOTS, "a doll slot left the rect measured off their builder")

    def test_the_inventory_is_ten_by_four_inside_the_equipment_panel(self):
        html = _drive()["html"]
        eq, prim = html.index('<section class="mp-p mp-eq">'), html.index('<section class="mp-p mp-prim">')
        inv = html.index('<div class="mp-inv">')
        self.assertTrue(eq < inv < prim, "the 10x4 inventory is not under the doll in the EQUIPMENT panel")
        self.assertEqual(html[inv:prim].count('class="vd-cell"'), 40, "the inventory under the doll is not 10x4")
        self.assertIn("onclick=\"window._mpSet('view','stash')\"", html[eq:inv], "EQUIPMENT lost its Stash button")
        self.assertEqual(len(re.findall(r'class="mp-swap', html[eq:inv])), 4, "the I / II weapon-swap tabs are gone")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheThreeColumns(unittest.TestCase):

    def test_the_css_carries_their_column_widths(self):
        s = _src("bible.html")
        c = THEIR_COLUMNS
        self.assertEqual(c["left"] + c["gutter"] + c["centre"], 1044)
        self.assertEqual(1044 + c["gutter"] + c["right"], c["column"])
        self.assertEqual(s.count(".mp{display:grid;grid-template-columns:calc(1044*var(--u)) calc(%d*var(--u));"
                                 "column-gap:calc(%d*var(--u));width:calc(%d*var(--u));"
                                 % (c["right"], c["gutter"], c["column"])), 1, "the outer column split moved")
        self.assertEqual(s.count(".mp-lc{display:grid;grid-template-columns:calc(%d*var(--u)) calc(%d*var(--u));"
                                 "column-gap:calc(%d*var(--u));" % (c["left"], c["centre"], c["gutter"])), 1,
                         "the LEFT | CENTRE split is no longer 322 | 716")

    def test_the_css_carries_their_panel_heights(self):
        s = _src("bible.html")
        for sel, h in THEIR_HEIGHTS.items():
            m = re.findall(r"^" + re.escape(sel) + r"\{height:calc\((\d+)\*var\(--u\)\)", s, re.M)
            self.assertEqual(m, [str(h)], "%s is not the %dpx panel measured off their builder" % (sel, h))

    def test_the_panels_live_in_their_columns_in_their_order(self):
        html = _drive()["html"]
        order = ['<div class="mp-top">', '<section class="mp-p mp-set">', '<div class="mp-left">',
                 '<section class="mp-p mp-eq">', '<section class="mp-p mp-prim">', '<section class="mp-p mp-merc">',
                 '<section class="mp-p mp-loot">', '<section class="mp-p mp-sw">', '<div class="mp-centre">',
                 '<section class="mp-p mp-cp">', '<section class="mp-p mp-notes">', '<div class="mp-right">',
                 '<section class="mp-p mp-auth">', '<section class="mp-p mp-show">', '<section class="mp-p mp-stats">']
        at = []
        for o in order:
            self.assertEqual(html.count(o), 1, "%s is missing or doubled" % o)
            at.append(html.index(o))
        self.assertEqual(at, sorted(at), "a panel left its column or its place in the column")

    def test_one_unit_their_pixels_at_2000_proportions_at_1280_stacked_under_900(self):
        self.assertEqual(_unit(_drive(w=2000, h=1300)["html"]), 1.0, "at 2000 wide the window is not their pixels")
        k = _unit(_drive(w=1280, h=800)["html"])
        self.assertLess(k, 1.0)
        self.assertLessEqual(THEIR_COLUMNS["column"] * k + 48, 1280.01, "at 1280 the three columns scroll sideways")
        self.assertIn('class="mp mp-stack"', _drive(w=800, h=1000)["html"], "under 900 the columns do not stack")

    def test_the_centre_defaults_to_the_stash_with_our_five_tabs(self):
        html = _drive()["html"]
        self.assertIn('<div class="mp-view mp-v-stash">', html, "a locker's centre is not the stash by default")
        st = html.index('<div class="mp-view mp-v-stash">')
        end = html.index('<div class="mp-view mp-v-tree"', st)
        for t in ("Personal", "Shared", "Gems", "Materials", "Runes"):
            self.assertIn(">%s</div>" % t, html[st:end])
        self.assertEqual(html[st:end].count('class="vd-cell vd-red"'), 100, "the centre stash is not 10x10")
        for v in ("stash", "tree", "calc"):
            self.assertEqual(html.count('data-view="%s"' % v), 1)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class EveryEmptyPanelSaysWhy(unittest.TestCase):

    def test_every_stat_is_unknown_with_a_reason(self):
        html = _drive()["html"]
        groups = re.findall(r'<div class="mp-st-g">([A-Z]+)', html)
        self.assertEqual(groups, STAT_GROUPS)
        rows = re.findall(r'<div class="mp-st-r" data-k="[^"]*"><span>([^<]+)</span>'
                          r'<span class="mp-unk" title="UNKNOWN — ([^"]+)">([^<]*)</span></div>', html)
        self.assertEqual(len(rows), html.count('class="mp-st-r"'), "a stat row does not have the UNKNOWN shape")
        self.assertGreaterEqual(len(rows), 20)
        for label, why, val in rows:
            self.assertEqual(val, "UNKNOWN", "%s shows %r - a locker has no measured stat" % (label, val))
            self.assertGreater(len(why.strip()), 10, "%s is UNKNOWN without saying why" % label)
        self.assertEqual(len(re.findall(r'<div class="mp-st-why">[^<]{10,}</div>', html)), len(STAT_GROUPS))

    def test_the_panels_nothing_fills_say_what_would(self):
        html = _drive()["html"]
        for sec in ("mp-prim", "mp-merc", "mp-loot", "mp-sw"):
            i = html.index('<section class="mp-p %s">' % sec)
            body = html[i:html.index("</section>", i)]
            self.assertIn("Nothing fills this yet.", body, sec)
            self.assertRegex(body, r"\((v-[A-E]|not scheduled)[^)]*\)", "%s does not say what would fill it" % sec)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheOldBehaviourSurvives(unittest.TestCase):

    def test_packing_counts_and_the_readouts_the_ci_specs_read(self):
        out = _drive()
        html = out["html"]
        self.assertEqual(html.count('class="vd-cell'), 140, "stash 100 + inventory 40")
        self.assertEqual(html.count('class="vd-grid"'), 2)
        self.assertEqual(html.count('class="vd-item'), len(SMALL))
        self.assertIn('<span class="vd-name">UNI-WEAPONS</span>', html)
        self.assertRegex(html, r'<span class="vd-sub">4 items total')
        self.assertIn(" on this mule</div>", html)
        self.assertIn('class="vd-close" onclick="window.vaultCloseCard()"', html)
        self.assertEqual(html.count('<div class="vd-list">'), 1)
        self.assertTrue(out["fs"] and out["on"] and not out["hidden"])

    def test_an_empty_locker_says_so(self):
        self.assertIn("empty locker", _drive(mule="empty")["html"])

    def test_a_big_locker_spills_onto_mule_tabs_and_pages(self):
        names = ["Base %d" % i for i in range(60)]
        out = _drive(mule="bases", assign=dict((n, "bases") for n in names),
                     sizes=dict((n, [2, 4]) for n in names), page=1)
        html, html2 = out["html"], out["html2"]
        n = int(re.search(r"Mule 1 / (\d+)", html).group(1))
        self.assertGreaterEqual(n, 2)
        self.assertEqual(len(re.findall(r'class="mp-settab(?: on)?" onclick="window._muleSetPage\(\d+\)"', html)), n,
                         "the BUILD SET row does not carry one tab per mule")
        self.assertIn('class="mp-settab on" onclick="window._muleSetPage(0)"', html)
        self.assertIn('class="mp-settab on" onclick="window._muleSetPage(1)"', html2, "paging did not move the tab")
        self.assertIn("Mule 2 / %d" % n, html2)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class EscClosesTheWindowNotTheShell(unittest.TestCase):

    def test_the_markup_declares_a_dialog(self):
        a = _static_attrs()
        self.assertEqual(a.get("role"), "dialog", "the console's Esc probe cannot see #vault-detail")
        self.assertEqual(a.get("aria-modal"), "true")
        self.assertTrue(a.get("aria-label"), "a dialog with no name")
        self.assertIn("hidden", a, "the window must start closed, or the probe would forward every Esc to it")

    def test_opening_declares_the_dialog_even_on_markup_that_lost_it(self):
        out = _drive(attrs={"class": "vault-detail", "id": "vault-detail", "hidden": ""})
        self.assertEqual(out["role"], "dialog")
        self.assertEqual(out["modal"], "true")
        self.assertIn("UNI-WEAPONS", out["label"] or "")

    def test_escape_closes_the_window_and_returns_to_the_vault(self):
        out = _drive(esc=True)
        self.assertEqual(out["after"], {"hidden": True, "fs": False, "on": False, "switched": ["vault"]})

    def test_the_console_probe_still_forwards_to_a_dialog(self):
        ui = _src("tv/control_ui.html")
        self.assertEqual(ui.count(PROBE_START), 1)
        i = ui.index(PROBE_START)
        blk = ui[i:ui.index(PROBE_END, i)]
        self.assertIn("fd.querySelectorAll(", blk)
        self.assertIn(', [role="dialog"]:not([hidden])\');', blk,
                      "the console's Esc probe no longer recognises a dialog, so Esc would close the shell again")
        self.assertIn("w.document.dispatchEvent(new w.KeyboardEvent('keydown', { key:'Escape', bubbles:true }))", blk)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#174 - the mule window's markup is not a dialog, so the console's Esc probe sends him HOME",
        "file": "bible.html",
        "find": '<div class="vault-detail" id="vault-detail" role="dialog" aria-modal="true" '
                'aria-label="Mule window (Esc closes)" hidden></div>',
        "replace": '<div class="vault-detail" id="vault-detail" hidden></div>',
        "matches": 1,
    },
    {
        "why": "#174 - opening the window no longer declares the dialog, so markup that lost it stays invisible",
        "file": "bible.html",
        "find": "    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true');\n",
        "replace": "    box.setAttribute('aria-modal', 'true');\n",
        "matches": 1,
    },
    {
        "why": "#174 - a doll slot drifts off the rect measured on their builder (helm grows to 60x90)",
        "file": "bible.html",
        "find": "    ['head', '⛑',    'helm',               131,  50, 60,  60],\n",
        "replace": "    ['head', '⛑',    'helm',               131,  50, 60,  90],\n",
        "matches": 1,
    },
    {
        "why": "#174 - a locker's stats render a made-up 0 instead of UNKNOWN",
        "file": "bible.html",
        "find": "return '<span class=\"mp-unk\" title=\"UNKNOWN — '+why+'\">UNKNOWN</span>'; };",
        "replace": "return '<span class=\"mp-unk\" title=\"UNKNOWN — '+why+'\">0</span>'; };",
        "matches": 1,
    },
    {
        "why": "#174 - the LEFT column stops being their 322px (proportions lost)",
        "file": "bible.html",
        "find": ".mp-lc{display:grid;grid-template-columns:calc(322*var(--u)) calc(716*var(--u));",
        "replace": ".mp-lc{display:grid;grid-template-columns:calc(360*var(--u)) calc(716*var(--u));",
        "matches": 1,
    },
    {
        "why": "#174 - the 10x4 inventory leaves the EQUIPMENT panel",
        "file": "bible.html",
        "find": "'<div class=\"mp-inv\">' + gridHtml(inv.placed, MULE_INV_W, MULE_INV_H, invCell) + '</div>'",
        "replace": "'<div class=\"mp-inv\"></div>'",
        "matches": 1,
    },
    {
        "why": "#174 - Esc no longer closes the mule window",
        "file": "bible.html",
        "find": "    if (e.key==='Escape' && openMuleId){ window.vaultCloseCard(); }\n",
        "replace": "    if (e.key==='Esc_' && openMuleId){ window.vaultCloseCard(); }\n",
        "matches": 1,
    },
]
