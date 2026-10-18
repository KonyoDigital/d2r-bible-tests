# -*- coding: utf-8 -*-
"""v3766 board #137 — the GrokBot v3740 retest, re-checked after the records arm.

Exile is a paladin shield, one size, 2x3. Spirit names swords or shields and stays a guess.
A copy past the shared cap is trade stock in GRAIL-DUPES, and a capped cell says its place
in the drawn run, not the owned total on every tile. FIND reads the mule page already in
the cell and opens that page from a button; the row itself still has no click (#79).
Andariel was already mercenary gear. Steel Shade was trade-trash and now rides the same
drawer, unless a mule override wins. A missing picture is the glyph, never a blank string.
The shared-tab overflow note stays the honest one.

The functions are extracted from bible.html and run in node. A missing node raises.
The records seam is not extracted. RED_PROOF below.
[[heart-first]] [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = os.environ.get("NODE") or shutil.which("node")


def _fn(src, name):
    m = re.search(r"\bfunction %s\s*\(" % re.escape(name), src)
    if not m:
        raise AssertionError("could not find function %s in bible.html" % name)
    i = src.index("{", m.start())
    depth, j = 0, i
    while j < len(src):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[m.start():j + 1]
        j += 1
    raise AssertionError("unbalanced braces extracting %s" % name)


def _assigned_fn(src, name):
    m = re.search(r"window\.%s\s*=\s*function\s*\(" % re.escape(name), src)
    if not m:
        raise AssertionError("could not find window.%s" % name)
    i = src.index("{", m.start())
    depth, j = 0, i
    while j < len(src):
        c = src[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[m.start():j + 1]
        j += 1
    raise AssertionError("unbalanced braces extracting window.%s" % name)


def _tip(src, name):
    i = src.find('"%s":{' % name)
    if i < 0:
        raise AssertionError("no runeword tip for %s" % name)
    m = re.search(r'\bb:"([^"]*)"', src[i:i + 5000])
    if not m:
        raise AssertionError("no base on the %s tip" % name)
    return m.group(1)


def _row_open(html):
    i = html.find('<div class="vfr-row"')
    if i < 0:
        return ""
    return html[i:html.find(">", i)]


class TestV3766GrokbotRetest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as fh:
            cls.src = fh.read()
        tips = {n: {"b": _tip(cls.src, n)} for n in ("Exile", "Spirit", "Enigma", "Lore")}
        gear = re.search(r"var MERC_GEAR = \{.*?\n  \};", cls.src, re.S)
        if not gear:
            raise AssertionError("MERC_GEAR did not parse")
        names = [
            "_runewordCells", "_warKey", "mercGearRole", "_mercRoute",
            "_copyCellMark", "_copyFileSay", "_findMuleNav", "_mulePageOnOpen",
            "art", "esc", "jsArg", "_sharedOverflowNote",
        ]
        body = "\n".join(_fn(cls.src, n) for n in names)
        prog = r"""
var window = globalThis;
var artOr;
var _SHARED_COPY_CAP = 2;
var RUNEWORD_TIP = %s;
function findRuneword(name){ return Object.prototype.hasOwnProperty.call(RUNEWORD_TIP, name) ? name : null; }
%s
function ownedPool(){ return ['Exile']; }
var magicFinds = null;
function _vaultFindMatches(pool, q){
  return pool.filter(function(n){ return String(n).toLowerCase().indexOf(q) >= 0; });
}
function _vfCanon(n){ return n; }
function _vaultFindHome(){
  return { kind:'filed', mule:'uni-armor', muleName:'Armor', cell:'Mule 2 · Personal stash · col 1', why:'' };
}
var document = { getElementById: function(){ return null; } };
function mountFind(){
  var box = { hidden: true, innerHTML: '' };
  document.getElementById = function(id){ return id === 'vault-find-results' ? box : null; };
  return box;
}
%s
var CURLY = "Andariel\u2019s Visage";
var out = {
  exile: _runewordCells('Exile'),
  spirit: _runewordCells('Spirit'),
  enigma: _runewordCells('Enigma'),
  lore: _runewordCells('Lore'),
  plain: _runewordCells('Nagelring'),
  tips: RUNEWORD_TIP,
  steel: _mercRoute('Steel Shade', null),
  steelMule: _mercRoute('Steel Shade', 'mule'),
  andariel: _mercRoute("Andariel's Visage", null),
  andarielCurly: _mercRoute(CURLY, null),
  guillaume: _mercRoute("Guillaume's Face", null),
  shaft: _mercRoute('Shaftstop', null),
  mark: _copyCellMark(7, 2, 0),
  markOne: _copyCellMark(1, 1, 0),
  say4: _copyFileSay('Exile', 4, 'shared'),
  say2: _copyFileSay('Exile', 2, 'shared'),
  sayRw: _copyFileSay('Exile', 4, 'runewords'),
  nav: _findMuleNav('Mule 2 · Personal stash · col 1'),
  navNone: _findMuleNav('Personal stash · col 1'),
  pagePending: _mulePageOnOpen('uni-armor', null, { mule:'uni-armor', page:1 }),
  pageSame: _mulePageOnOpen('uni-armor', 'uni-armor', null),
  pageSwitch: _mulePageOnOpen('uni-armor', 'uni-weap', { mule:'shared', page:3 }),
  artMiss: art('Exile'),
  artThrow: (function(){ var boom = function(){ throw new Error('art'); }; var prev = artOr; artOr = boom; try { return art('Exile'); } finally { artOr = prev; } })(),
  artHit: (function(){ artOr = function(){ return '<img class="d2art-img" src="art/exile.png" alt="">'; }; return art('Exile'); })(),
  note: _sharedOverflowNote([{n:'Exile'}]),
  noteEmpty: _sharedOverflowNote([])
};
var box = mountFind();
window.vaultFind('exile');
out.find = box.innerHTML;
process.stdout.write(JSON.stringify(out));
""" % (json.dumps(tips), gear.group(0), body + "\n" + _assigned_fn(cls.src, "vaultFind"))
        p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            raise AssertionError((p.stderr or p.stdout)[-2000:])
        cls.f = json.loads(p.stdout)

    def test_exile_packs_as_a_paladin_shield_and_spirit_stays_a_guess(self):
        ex, sp, en, lo = self.f["exile"], self.f["spirit"], self.f["enigma"], self.f["lore"]
        self.assertEqual(self.f["tips"]["Exile"]["b"], "4 socket Paladin Shields")
        self.assertEqual(self.f["tips"]["Spirit"]["b"], "4 socket Swords or Shields")
        self.assertEqual([ex["w"], ex["h"]], [2, 3], ex)
        self.assertNotIn("approx", ex)
        self.assertTrue(sp.get("approx"), sp)
        self.assertEqual([sp["w"], sp["h"]], [1, 2], sp)
        self.assertEqual([en["w"], en["h"]], [2, 3], en)
        self.assertNotIn("approx", en)
        self.assertEqual([lo["w"], lo["h"]], [2, 2], lo)
        self.assertIsNone(self.f["plain"])
        self.assertEqual(self.src.count(
            "var _rwSized = (typeof _runewordCells === 'function') ? _runewordCells(name) : null;"), 1)

    def test_steel_shade_routes_with_andariel_unless_a_mule_override_wins(self):
        for key in ("steel", "andariel", "andarielCurly", "guillaume"):
            row = self.f[key]
            self.assertEqual(row["id"], "shared", row)
            self.assertRegex(row["why"], r"mercenary")
        self.assertIsNone(self.f["steelMule"])
        self.assertIsNone(self.f["shaft"])
        call = self.src.find("var _mercHit = _mercRoute(name, _ov);")
        trash = self.src.find("if (_tv === 'trash')")
        self.assertGreater(call, 0)
        self.assertGreater(trash, call)

    def test_a_capped_cell_does_not_print_the_owned_total_on_every_tile(self):
        mark = self.f["mark"]
        self.assertEqual(mark["badge"], "1/2", mark)
        self.assertNotIn("7", mark["badge"])
        self.assertIn("copy 1 of 2", mark["title"])
        self.assertIn("7 owned", mark["title"])
        self.assertEqual(self.f["markOne"]["badge"], "")
        self.assertEqual(self.src.count("var _mark = _copyCellMark(_cc, _drawN[n] || 1, _ix);"), 1)

    def test_a_copy_past_the_shared_cap_says_trade_stock(self):
        self.assertIn("GRAIL-DUPES", self.f["say4"])
        self.assertNotIn("filed to shared", self.f["say4"])
        self.assertIn("filed to shared", self.f["say2"])
        self.assertIn("filed to runewords", self.f["sayRw"])
        self.assertEqual(self.src.count("why: _copyFileSay(nm, copies[nm], assign[nm])"), 1)

    def test_find_names_the_mule_page_without_a_row_click(self):
        nav = self.f["nav"]
        self.assertEqual(nav["page"], 2)
        self.assertEqual(nav["index"], 1)
        self.assertIsNone(self.f["navNone"])
        html = self.f["find"]
        self.assertIn("vd-mule-nav", html)
        self.assertIn("_muleOpenAt", html)
        self.assertIn("Mule 2", html)
        opened = _row_open(html)
        self.assertTrue(opened.startswith('<div class="vfr-row"'), opened)
        self.assertNotIn("onclick", opened)
        self.assertEqual(self.f["pagePending"], 1)
        self.assertIsNone(self.f["pageSame"])
        self.assertEqual(self.f["pageSwitch"], 0)
        self.assertEqual(self.src.count(
            "var _navPg = _mulePageOnOpen(muleId, openMuleId, _pendingNav);"), 1)
        switch = [ln for ln in self.src.splitlines() if "_mulePageOnOpen" in ln and "_mpStab = 'personal'" in ln]
        self.assertEqual(len(switch), 1, switch)
        self.assertNotIn("_mulePage = 0", switch[0])

    def test_a_missing_picture_is_the_glyph_and_the_overflow_note_stays_honest(self):
        for key in ("artMiss", "artThrow"):
            self.assertIn("d2art-fallback", self.f[key])
            self.assertNotEqual(self.f[key], "")
        self.assertIn("d2art-img", self.f["artHit"])
        self.assertNotIn("d2art-fallback", self.f["artHit"])
        self.assertIn("Exile", self.f["note"])
        self.assertIn("100", self.f["note"])
        self.assertNotIn("preview", self.f["note"])
        self.assertEqual(self.f["noteEmpty"], "")

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("grokbot retest: %d distinct attacks, wilson %.4f vs vault.apply bar %.3f; "
               "kinds sabotage %.2f vs %.2f" % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(n, 10, msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar,
                        "one sabotage family must not read as enough to open the write door")


RED_PROOF = [
    {
        "why": "Exile is a paladin shield. Dropping that class puts it back on the 1x2 guess.",
        "file": "bible.html",
        "find": "  if (/^\\d+\\s+socket\\s+paladin shields$/.test(_rwb)) return {w:2, h:3};\n",
        "replace": "  /* paladin shield size removed */\n",
        "matches": 1,
    },
    {
        "why": "Spirit names swords or shields. Sizing every shield as 2x3 states a size the tip does not.",
        "file": "bible.html",
        "find": "  if (/^\\d+\\s+socket\\s+paladin shields$/.test(_rwb)) return {w:2, h:3};\n",
        "replace": "  if (/^\\d+\\s+socket\\s+.*shields$/.test(_rwb)) return {w:2, h:3};\n",
        "matches": 1,
    },
    {
        "why": "The item sizer has to ask the class rule. A rule nobody calls leaves Exile a guess.",
        "file": "bible.html",
        "find": "        var _rwSized = (typeof _runewordCells === 'function') ? _runewordCells(name) : null;\n",
        "replace": "        var _rwSized = null;\n",
        "matches": 1,
    },
    {
        "why": "Steel Shade is mercenary gear. Removing the seed throws it out as trade-trash again.",
        "file": "bible.html",
        "find": "    \"steel shade\":         'merc helm - fire absorb, the barb and Act 2 merc helm'\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "Andariel already routes shared. Dropping the seed unpins the merc drawer.",
        "file": "bible.html",
        "find": "    \"andariel's visage\":   'merc helm - IAS + poison, the classic Act 2 merc face',\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "A mule override still wins. Ignoring it files a forced mule item into the shared stash.",
        "file": "bible.html",
        "find": "    if (role && ov !== 'mule') return {id:'shared', why:'mercenary gear: ' + role + ' - in the shared stash, where every character can reach it'};\n",
        "replace": "    if (role) return {id:'shared', why:'mercenary gear: ' + role + ' - in the shared stash, where every character can reach it'};\n",
        "matches": 1,
    },
    {
        "why": "suggestMule has to pass the override. A null override files Steel Shade shared even when he forced a mule.",
        "file": "bible.html",
        "find": "    var _mercHit = _mercRoute(name, _ov);\n",
        "replace": "    var _mercHit = _mercRoute(name, null);\n",
        "matches": 1,
    },
    {
        "why": "The badge is this cell's place in the drawn run. Printing the owned total on every cell multiplies the count.",
        "file": "bible.html",
        "find": "    var badge = (drawn > 1) ? ((index + 1) + '/' + drawn) : '';\n",
        "replace": "    var badge = (owned > 1) ? ('\\u00d7' + owned) : '';\n",
        "matches": 1,
    },
    {
        "why": "The locker cell has to ask the mark. The old times-owned badge is the inflation.",
        "file": "bible.html",
        "find": "        var _mark = _copyCellMark(_cc, _drawN[n] || 1, _ix);\n",
        "replace": "        var _mark = { badge: (_cc > 1) ? ('\\u00d7' + _cc) : '', title: '' };\n",
        "matches": 1,
    },
    {
        "why": "Copy 4 of a shared item is trade stock. Saying it was filed to shared puts it on the tab that keeps 2.",
        "file": "bible.html",
        "find": "    if (String(home) === 'shared' && n > cap)\n      return name + ' — copy ' + n + ' is trade stock in GRAIL-DUPES (the shared stash keeps ' + cap + ')';\n",
        "replace": "    /* shared cap message removed */\n",
        "matches": 1,
    },
    {
        "why": "The planner has to ask that sentence. The old concatenation says filed to shared for every copy.",
        "file": "bible.html",
        "find": "            why: _copyFileSay(nm, copies[nm], assign[nm]) };\n",
        "replace": "            why: nm + ' \\u2014 copy ' + copies[nm] + ' filed to ' + assign[nm] };\n",
        "matches": 1,
    },
    {
        "why": "FIND reads the mule page out of the cell. A nav that always returns null never names it.",
        "file": "bible.html",
        "find": "    var m = /Mule\\s+(\\d+)/.exec(String(cell || ''));\n",
        "replace": "    var m = null;\n",
        "matches": 1,
    },
    {
        "why": "The row has to ask that nav. A null nav leaves the page in the cell and no button.",
        "file": "bible.html",
        "find": "      var _fnav = (w && w.cell && mid) ? _findMuleNav(w.cell) : null;\n",
        "replace": "      var _fnav = null;\n",
        "matches": 1,
    },
    {
        "why": "Opening the locker from FIND keeps the named page. Always returning 0 drops a re-render back to mule 1.",
        "file": "bible.html",
        "find": "    if (pending && pending.mule === muleId && (pending.page | 0) >= 0) return pending.page | 0;\n    if (muleId !== currentId) return 0;\n    return null;\n",
        "replace": "    return 0;\n",
        "matches": 1,
    },
    {
        "why": "openMuleCard has to ask that page law. Hardcoding 0 forgets the mule FIND named.",
        "file": "bible.html",
        "find": "    var _navPg = _mulePageOnOpen(muleId, openMuleId, _pendingNav);\n",
        "replace": "    var _navPg = 0;\n",
        "matches": 1,
    },
    {
        "why": "A missing picture is the glyph. Returning a blank string is the empty art on reload.",
        "file": "bible.html",
        "find": "return '<span class=\"d2art-fallback\">' + glyph + '</span>';",
        "replace": "return '';",
        "matches": 1,
    },
    {
        "why": "The shared overflow note names the real tab. Calling it a preview says the stash is bigger than it is.",
        "file": "bible.html",
        "find": "      + ' will not fit on this shared tab</strong> — a shared tab is 10×10 = 100 cells and this one is full. '\n",
        "replace": "      + ' will not fit this 10x10 preview</strong> — a shared tab is 10×10 = 100 cells and this one is full. '\n",
        "matches": 1,
    },
    {
        "why": "Shaftstop is not mercenary gear. Seeding it would route a budget armor into the shared stash.",
        "file": "bible.html",
        "find": "    \"steel shade\":         'merc helm - fire absorb, the barb and Act 2 merc helm'\n  };\n",
        "replace": "    \"steel shade\":         'merc helm - fire absorb, the barb and Act 2 merc helm',\n    \"shaftstop\":           'budget armor - a control that must stay off this list'\n  };\n",
        "matches": 1,
    },
    {
        "why": "The FIND row stays on the vault. A row click opens the locker and leaves the finder, which #79 dropped.",
        "file": "bible.html",
        "find": "      return '<div class=\"vfr-row\" title=\"'+esc(n)+'\">'\n",
        "replace": "      return '<div class=\"vfr-row\" onclick=\"window.openMuleCard(\\''+jsArg(mid)+'\\')\" title=\"'+esc(n)+'\">'\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
