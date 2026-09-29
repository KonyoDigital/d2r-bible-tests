# -*- coding: utf-8 -*-
"""#253 (GrokBot ACT 5854814442, his ask: before Tuesday) — THE EDIT PANEL SHOWS THE BASE, AND THE LOCKER'S CHARACTER
PICKER OPENS.

GROKBOT MEASURED, on v3517:
  (a) the Character Builder's item Edit panel for a white Crowbill printed only "Normal · Crowbill · Required Level 25" -
      no damage, no Strength / Dexterity requirement, no attack speed, no durability - while the HOVER box over the same
      item already computed every one of them (_cbTipEntry + d2Tip). Maxroll's Base Items panel shows them.
  (b) in the mule window, "Character: none bound" was TEXT: clicking it did nothing a user could see.

THE FIX, and what this law drives in node (the SHIPPED code, each piece cut from bible.html by the sibling laws' own
cutters - never re-typed):
  (a) THE BASE'S OWN ROWS ARE ONE FUNCTION, _d2TipBase, which the hover box and BOTH Edit panels (a base's, and a
      unique / set / runeword's) print over the SAME _cbTipEntry. Driven through the builder's own picker:
        · a white Crowbill's Edit panel carries its damage (weapons.txt 14-34), Required Strength 94 / Dexterity 70,
          Durability 26 of 26, Required Level 25 (once - the note no longer repeats it), its "<Class> Class - <Speed>"
          row, and the most sockets it takes AT ITS ITEM LEVEL - the Sockets box's own ceiling (6 at 99, 4 at 20: the
          type's MaxSockets band), never a second count - and every tooltip row it prints is the hover box's row, in
          the box's order, for the same stored entry;
        · a Hel in its socket moves the requirement exactly as the box does (94 / 70 -> 76 / 56, base + trunc(base x
          -20 / 100)) - AT ONCE, through the quiet refresh a socket pick runs (it re-drew only the doll and the stats,
          so the rows sat at 94 / 70 until something else re-drew the tab); ethereal takes 10 off first (84 / 60, with
          Hel 68 / 48), its damage x1.5 floored (21 to 51), its durability said UNKNOWN - each state equal to the box;
        · a runeword (Breath of the Dying on a Crowbill: 76 / 56, its 6 runes as "Sockets: 6") and a LOW-quality base
          (no damage row - the game's code - and the box's UNKNOWN said in the panel, never a silent gap) print the
          same way.
  (b) THE LOCKER'S CHARACTER IS A BUTTON, and the handler it RENDERED opens a list of HIS characters: every build of
      the 👤 Characters tab (asked of that room's own reader, window._charsList - the MAIN one first, marked ★ MAIN from
      d2r_cbMain, the rest newest first) and the MAIN he named (window.mainCharacter, d2r_mainCharacter). The reader
      never sees a character's name, so there is no third source - and none is invented. Pressing a row the list
      RENDERED writes ONE field - that locker's boundChar in d2r_muleRoster - and every other store, and every other
      field of every locker, is byte-identical; Unbind removes that field and nothing else. Opening the list writes
      nothing. A binding is a REFERENCE: a renamed build reads its new name, a deleted one reads UNKNOWN (never "none
      bound" over a binding that exists); an empty store says how to add one (the 👤 Characters tab, + New
      character); an unreadable one is UNKNOWN, never "no characters yet". Esc closes the list before the window.
⚠ WHAT THIS LAW CANNOT SEE: pixels - the panel and the list were not looked at on real pixels here (browser suites run
on GitHub CI, never on his Mac - [[test-venue]]).
RED_PROOF below: every sabotage turns this law red for its own reason.
"""
import io
import json
import os
import re
import sys
import unittest
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_the_character_builder_is_their_builder as CB  # noqa: E402  the builder's harness, one stand-in
import test_the_mule_window_equips_and_says_its_source as EQ  # noqa: E402  the mule window's harness, one cut
from test_the_characters_tab_is_manual_and_separate import _chars_js  # noqa: E402  the Characters room's cutter

NODE = CB.NODE

# ── (a) the Edit panel ───────────────────────────────────────────────────────────────────────────────────────────────
EDIT = r"""
var d = window._cbDb();
function baseCode(n){ var h = null; Object.keys(d.b).forEach(function(c){ if (!h && d.b[c][0] === n && d.b[c][20]) h = c; }); return h; }
function rune(n){ var h = null; Object.keys(d.rwRunes).forEach(function(c){ if (!h && d.rwRunes[c][1] === n + ' Rune') h = c; }); return h; }
function txt(s){ return String(s).replace(/<[^>]+>/g, '').replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'); }
/* the rows of a run of flat <div class="X">..</div> (a row holds spans, never a div) -> {rows: [[class, text]], rest} */
function flat(h){ var out = [], re = /^<div class="([^"]+)"[^>]*>([\s\S]*?)<\/div>/, m; while ((m = re.exec(h))){ out.push([m[1], txt(m[2])]); h = h.slice(m[0].length); } return { rows: out, rest: h }; }
/* the Edit panel's base block, as rendered (the modal, or the string a quiet refresh wrote) -> rows | null (absent) */
function edBase(html){ html = html == null ? MODAL._html : String(html); var i = html.indexOf('id="cb-ed-base"'); if (i < 0) return null;
  var f = flat(html.slice(html.indexOf('>', i) + 1)); return f.rest.indexOf('</div>') === 0 ? f.rows : [['UNPARSED', f.rest.slice(0, 120)]]; }
/* the hover box for what the build now wears in `slot` - the same entry, the build's level and class */
function tipRows(slot){ var b = slots(), e = b.sets[0].slots[slot]; return flat(window.d2Tip(window._cbTipEntry(e, window._cbItem(e.id), b.level, slot, b.cls))).rows; }
function sockMax(){ var h = MODAL._html, j = h.indexOf('id="cb-sockets"'); return j < 0 ? null : +((/max="(\d+)"/.exec(h.slice(j, h.indexOf('>', j))) || [])[1]); }
function mk(cls, lvl){ window.openCharBuilder(); window._cbOpenNew(); window._cbNewCls(cls); window._cbNewLvl(lvl); window._cbNewGo(); }
function whiteCrowbill(){ mk('Sorceress', 90); var c = baseCode('Crowbill'); window._cbOpenPick('slot', 'rarm'); window._cbChoose('b:' + c); window._cbQuality('b'); return c; }
"""


def _edit(body):
    return CB._run(EDIT + body)


def _core(rows):
    """the rows the hover box prints too: all but the panel's own Sockets row and the closing note"""
    return [r for r in rows if not re.match(r"^(Max )?Sockets: ", r[1]) and r[0] != "d2t-note"]


def _run_in(tip, rows):
    """the index where `rows` sit in `tip` as one contiguous run, or -1"""
    for k in range(len(tip) - len(rows) + 1):
        if tip[k:k + len(rows)] == rows:
            return k
    return -1


# ── (b) the locker's character ───────────────────────────────────────────────────────────────────────────────────────
BUILDS = {"b1": {"name": "Konyoress", "cls": "Sorceress", "level": 80, "sets": [], "at": 1},
          "b2": {"name": "Hammerdin", "cls": "Paladin", "level": 91, "sets": [], "at": 5},
          "b3": {"name": "Zapper", "cls": "Sorceress", "level": 60, "sets": [], "at": 3}}
DECLARED = {"name": "Shadowfang", "class": "Assassin", "level": 70, "source": "declared", "at": "2026-09-26T00:00:00Z"}
EQUIP = {"uni-armor": {"setI": {"head": {"name": "Harlequin Crest (Shako)", "source": "manual", "at": "2026-09-26T00:00:00Z"}}}}

BIND = r"""
function ctl(){ var h = box.innerHTML, i = h.indexOf('id="mp-bind"'); if (i < 0) return null;
  var s = h.lastIndexOf('<', i), t = h.slice(s, h.indexOf('>', i) + 1), e = h.indexOf('</' + t.slice(1, t.indexOf(' ')) + '>', i);
  return { tag: t.slice(1, t.indexOf(' ')), state: (/data-state="([^"]*)"/.exec(t) || [])[1] || null, onclick: (/onclick="([^"]*)"/.exec(t) || [])[1] || null,
           title: unesc((/title="([^"]*)"/.exec(t) || [])[1] || ''), text: unesc(h.slice(h.indexOf('>', i) + 1, e).replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim() }; }
/* a button pressed by EVALUATING THE onclick THE WINDOW RENDERED, `this` carrying the attributes it rendered */
function press(onclick, attrs){ var el = { getAttribute: function(k){ return Object.prototype.hasOwnProperty.call(attrs || {}, k) ? attrs[k] : null; } };
  return (new Function('return (' + unesc(onclick).replace(/;\s*$/, '') + ');')).call(el); }
function listHtml(){ var h = box.innerHTML, i = h.indexOf('id="mp-bind-list"'); return i < 0 ? null : h.slice(h.lastIndexOf('<div', i), h.indexOf('</section>', i)); }
function opts(){ var h = listHtml() || '', re = /<button type="button" class="mp-bind-o[^"]*"([^>]*)>([\s\S]*?)<\/button>/g, m, out = [];
  while ((m = re.exec(h))){ var a = m[1];
    out.push({ src: unesc((/data-src="([^"]*)"/.exec(a) || [])[1] || ''), id: unesc((/data-id="([^"]*)"/.exec(a) || [])[1] || ''),
               onclick: (/onclick="([^"]*)"/.exec(a) || [])[1] || null, text: unesc(m[2].replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim() }); }
  return out; }
function pick(src, id){ var o = opts().filter(function(x){ return x.src === src && x.id === id; })[0];
  return o ? press(o.onclick, { 'data-src': o.src, 'data-id': o.id }) : 'NOT OFFERED'; }
function listState(){ var h = listHtml() || '', m = /class="mp-bind-none[^"]*" data-state="([a-z]+)">([\s\S]*?)<\/div>/.exec(h);
  return m ? { state: m[1], text: unesc(m[2].replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim() } : null; }
function snap(){ var o = {}; Object.keys(STORE).sort().forEach(function(k){ o[k] = STORE[k]; }); return o; }
function statsLine(){ return unesc((/<div class="mp-cls"[^>]*>([^<]*)<\/div>/.exec(box.innerHTML) || [0, ''])[1]); }
"""


def _bind(scenario, store=None, assign=None):
    """the shipped mule window + the Characters room's reader + the MAIN's reader, over the mule law's stand-in DOM"""
    s = EQ._src()
    extra = (_chars_js(s) + "\n"
             + EQ._between(s, "var _MAIN_CHAR_KEY = 'd2r_mainCharacter';", "window.mainCharacterDeclare = function(o){") + "\n")
    return EQ._drive(extra + BIND + scenario, assign=assign if assign is not None else {}, store=store or {})


def _store(builds=BUILDS, main="b1", declared=DECLARED):
    st = {"d2r_muleEquip": json.dumps(EQUIP)}
    if builds is not None:
        st["d2r_charBuilds"] = builds if isinstance(builds, str) else json.dumps(builds)
    if main is not None:
        st["d2r_cbMain"] = main
    if declared is not None:
        st["d2r_mainCharacter"] = json.dumps(declared)
    return st


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheEditPanelShowsTheBase(unittest.TestCase):

    def test_a_white_crowbills_edit_panel_prints_its_base_rows_from_the_tooltip(self):
        out = _edit(r"""
          var crow = whiteCrowbill(); OUT.row = d.b[crow]; OUT.tab = window._cbState().pick.tab;
          OUT.ed = edBase(); OUT.tip = tipRows('rarm'); OUT.sock = sockMax();
          OUT.lvls = (MODAL._html.match(/Required Level/g) || []).length;
          window._cbEdit('ilvl', 20); OUT.ed20 = edBase(); OUT.sock20 = sockMax(); OUT.band = d.ty[d.b[crow][1]][3];
        """)
        b = out["row"]
        self.assertEqual(out["tab"], "edit", "the white Crowbill did not reach its Edit tab")
        self.assertEqual((b[0], b[6], b[7]), ("Crowbill", 94, 70), "the table's Crowbill is not the one the brief measured")
        ed = out["ed"]
        self.assertIsNotNone(ed, "GrokBot's v3517 panel again: the Edit tab carries no base rows at all")
        texts = [t for c, t in ed]
        want = ["One-Hand Damage: %d to %d" % (b[10], b[11]), "Durability: %d of %d" % (b[25], b[25]),
                "Required Dexterity: 70", "Required Strength: 94", "Required Level: %d" % b[5]]
        for w in want:
            self.assertIn(w, texts, "the Edit panel of a white Crowbill does not print %r: %s" % (w, texts))
        self.assertTrue([t for t in texts if re.match(r"^Axe Class - .+ Attack Speed$", t)], "no speed row: %s" % texts)
        # its tooltip rows ARE the hover box's rows, in the box's order, for the same stored entry
        core = _core(ed)
        self.assertGreaterEqual(len(core), 6, "PRINT THE DENOMINATOR: the base block holds %d tooltip rows" % len(core))
        self.assertGreaterEqual(_run_in(out["tip"], core), 0,
                                "the Edit panel's rows are not the hover box's rows:\n  edit %s\n  box  %s" % (core, out["tip"]))
        self.assertEqual(out["lvls"], 1, "Required Level is said %d times on one panel - the note repeats the row" % out["lvls"])
        # the most sockets it takes is the Sockets box's own ceiling, at its item level (the type's MaxSockets band)
        band = out["band"]
        for rows, sock, ilvl in ((ed, out["sock"], 99), (out["ed20"], out["sock20"], 20)):
            cap = min(b[4], band[0] if ilvl <= band[1] else (band[2] if ilvl <= band[3] else band[4]))
            self.assertEqual(sock, cap, "the Sockets box's max at item level %d is %s, the tables say %d" % (ilvl, sock, cap))
            self.assertIn("Max Sockets: %d" % cap, [t for c, t in rows], "item level %d: %s" % (ilvl, rows))
        self.assertNotEqual(out["sock"], out["sock20"], "item level 20 did not move the ceiling - the case measures nothing")

    def test_hel_and_ethereal_move_the_requirement_exactly_as_the_tooltip_does(self):
        out = _edit(r"""
          var crow = whiteCrowbill(), hel = rune('Hel'); OUT.row = d.b[crow];
          OUT.helPct = d.rwRunes[hel][4][0][1][0][0]; OUT.helWords = d.T[d.rwRunes[hel][4][0][0]];
          window._cbEdit('sockets', '1'); OUT.before = edBase();
          var QUIET = []; ELS['cb-ed-base'] = { set outerHTML(v){ QUIET.push(String(v)); } };
          window._cbSocket(0, hel);
          OUT.stored = slots().sets[0].slots.rarm.socketed; OUT.quiet = QUIET.length ? edBase(QUIET[QUIET.length - 1]) : null;
          window._cbPickTab('edit'); OUT.hel = edBase(); OUT.helTip = tipRows('rarm');
          window._cbEdit('eth', true); OUT.both = edBase(); OUT.bothTip = tipRows('rarm');
          window._cbSocket(0, ''); window._cbPickTab('edit'); OUT.eth = edBase(); OUT.ethTip = tipRows('rarm');
        """)
        b, pct = out["row"], out["helPct"]
        self.assertEqual(pct, -20, "Hel's weapon line is not Requirements -20%%: %s %s" % (pct, out["helWords"]))
        self.assertEqual(len(out["stored"]), 1, "the Hel never reached the socket - the case measures nothing")
        rq = lambda v, eth: (v - 10 if eth else v) + int((v - 10 if eth else v) * pct / 100.0)  # noqa: E731
        pre = [t for c, t in out["before"]]
        self.assertIn("Required Strength: 94", pre, "BASELINE: before the Hel the panel must read 94: %s" % pre)
        cases = (("quiet", None, False, True), ("hel", "helTip", False, True), ("both", "bothTip", True, True),
                 ("eth", "ethTip", True, False))
        for key, tipk, eth, hel in cases:
            rows = out[key]
            self.assertIsNotNone(rows, "%s: the base block is gone" % key)
            texts = [t for c, t in rows]
            s_, d_ = (rq(94, eth), rq(70, eth)) if hel else ((84, 60) if eth else (94, 70))
            self.assertIn("Required Strength: %d" % s_, texts, "%s: %s" % (key, texts))
            self.assertIn("Required Dexterity: %d" % d_, texts, "%s: %s" % (key, texts))
            dmg = ("One-Hand Damage: %d to %d" % (b[10] * 3 // 2, b[11] * 3 // 2)) if eth else ("One-Hand Damage: %d to %d" % (b[10], b[11]))
            self.assertIn(dmg, texts, "%s: %s" % (key, texts))
            if eth:
                self.assertTrue([c for c, t in rows if c == "d2t-unk" and t.startswith("Durability: UNKNOWN")],
                                "%s: an ethereal item's durability must be said UNKNOWN: %s" % (key, texts))
            if tipk:
                self.assertGreaterEqual(_run_in(out[tipk], _core(rows)), 0,
                                        "%s: the Edit panel is not the hover box:\n  edit %s\n  box  %s" % (key, _core(rows), out[tipk]))
        self.assertEqual(out["quiet"], out["hel"], "the socket pick's quiet refresh drew other rows than the full Edit tab")
        self.assertEqual((rq(94, False), rq(70, False), rq(94, True), rq(70, True)), (76, 56, 68, 48), "the brief's numbers")

    def test_a_runeword_and_a_low_quality_base_print_the_same_way(self):
        out = _edit(r"""
          mk('Sorceress', 90); var crow = baseCode('Crowbill'), botd = null;
          d.it.forEach(function(x){ if (!botd && x[1] === 'Breath of the Dying') botd = x[0]; });
          window._cbOpenPick('slot', 'rarm'); window._cbChoose(botd); window._cbPickBase(crow);
          if (window._cbState().pick.tab !== 'edit') window._cbPickTab('edit');
          OUT.rw = edBase(); OUT.rwTip = tipRows('rarm'); window._cbClosePick();
          window._cbOpenPick('slot', 'rarm'); window._cbChoose('b:' + crow); window._cbQuality('low');
          OUT.lowTab = window._cbState().pick.tab; OUT.low = edBase(); OUT.lowTip = tipRows('rarm');
        """)
        rw = [t for c, t in out["rw"] or []]
        for w in ("Required Strength: 76", "Required Dexterity: 56", "Sockets: 6"):
            self.assertIn(w, rw, "Breath of the Dying on a Crowbill (Hel inside it): %s" % rw)
        self.assertGreaterEqual(_run_in(out["rwTip"], _core(out["rw"])), 0, "the runeword's Edit panel is not its hover box")
        self.assertEqual(out["lowTab"], "edit")
        low = out["low"] or []
        self.assertFalse([t for c, t in low if "Damage:" in t], "a low-quality base printed a damage the game's code decides")
        unk = [t for c, t in low if c == "d2t-unk" and "low-quality" in t and "UNKNOWN" in t]
        self.assertEqual(len(unk), 1, "the box's UNKNOWN for a low-quality base is not said in the Edit panel: %s" % low)
        self.assertIn(unk[0], [t for c, t in out["lowTip"]], "the panel's UNKNOWN is not the hover box's")
        self.assertGreaterEqual(_run_in(out["lowTip"], [r for r in _core(low) if r[0] != "d2t-unk"]), 0,
                                "the low-quality base's Edit panel is not its hover box")

    def test_a_base_not_on_record_is_unknown_never_zero_sockets(self):
        """#41 rank 11 (2026-09-29) — a runeword whose stored base the database does not carry read "zzz (0 sockets
        max) ▸" in the Base control (_cbMaxSock answers 0 for an unknown code, printed as if measured), and the hover
        box printed NO base line at all. Both now say UNKNOWN with the code, and no number. Measured on the shipped
        code before the fix: the control text was exactly 'zzz (0 sockets max) ▸' and the box had no base row."""
        out = _edit(r"""
          mk('Sorceress', 90); var crow = baseCode('Crowbill'), botd = null, shako = null;
          d.it.forEach(function(x){ if (!botd && x[1] === 'Breath of the Dying') botd = x[0]; if (!shako && x[1] === 'Harlequin Crest') shako = x[0]; });
          function ctl(){ var h = MODAL._html, i = h.indexOf('id="cb-base"'); if (i < 0) i = h.indexOf('aria-label="base (fixed)"'); if (i < 0) return null;
            var s = h.lastIndexOf('<', i), tag = h.slice(s, h.indexOf('>', i) + 1), isBtn = tag.indexOf('<button') === 0;
            var e = h.indexOf(isBtn ? '</button>' : '</select>', i);
            return { text: txt(h.slice(h.indexOf('>', i) + 1, e)), aria: unesc((/aria-label="([^"]*)"/.exec(tag) || [])[1] || ''), tag: isBtn ? 'button' : 'select' }; }
          function unesc(t){ return String(t).replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&'); }
          function rebase(code){ var b = JSON.parse(RAW['d2r_charBuilds']); var k = Object.keys(b)[0]; b[k].sets[0].slots.rarm.base = code; RAW['d2r_charBuilds'] = JSON.stringify(b);
            window._cbClosePick(); window._cbOpenPick('slot', 'rarm'); if (window._cbState().pick.tab !== 'edit') window._cbPickTab('edit'); }
          window._cbOpenPick('slot', 'rarm'); window._cbChoose(botd); window._cbPickBase(crow);
          if (window._cbState().pick.tab !== 'edit') window._cbPickTab('edit');
          OUT.known = ctl(); OUT.knownTip = tipRows('rarm');
          rebase('zzz'); OUT.unk = ctl(); OUT.unkTip = tipRows('rarm');
          rebase(null); OUT.none = ctl();
          /* a unique on a base not on record: the fixed select says the same */
          window._cbClosePick(); window._cbOpenPick('slot', 'head'); window._cbChoose(shako);
          if (window._cbState().pick.tab !== 'edit') window._cbPickTab('edit');
          var b2 = JSON.parse(RAW['d2r_charBuilds']); var k2 = Object.keys(b2)[0]; b2[k2].sets[0].slots.head.base = 'zzz'; RAW['d2r_charBuilds'] = JSON.stringify(b2);
          window._cbClosePick(); window._cbOpenPick('slot', 'head'); if (window._cbState().pick.tab !== 'edit') window._cbPickTab('edit');
          OUT.uniq = ctl();
        """)
        known = out["known"]
        self.assertIsNotNone(known, "BASELINE: the runeword's Edit panel has no Base control")
        self.assertEqual((known["tag"], known["text"]), ("button", "Crowbill (6 sockets max) ▸"),
                         "BASELINE: with the base on record the control must read its name and ceiling: %s" % known)
        self.assertFalse([r for r in out["knownTip"] if r[0] == "d2t-unk" and "base UNKNOWN" in r[1]],
                         "BASELINE: a base on record was said UNKNOWN in the hover box")
        unk = out["unk"]
        self.assertIsNotNone(unk, "the Edit panel lost its Base control over an unrecorded base")
        self.assertEqual(unk["text"], 'base UNKNOWN (not on record: zzz) ▸',
                         "an unrecorded base must read UNKNOWN with its code, no number: %r" % unk["text"])
        for bad in ("sockets max", "(0", "zzz ("):
            self.assertNotIn(bad, unk["text"], "the control still prints a count for a base nobody measured: %r" % unk["text"])
        self.assertIn("base: base UNKNOWN (not on record: zzz)", unk["aria"], "the control's aria-label still says a number: %r" % unk["aria"])
        self.assertNotIn("sockets max", unk["aria"])
        unk_rows = [r for r in out["unkTip"] if r[0] == "d2t-unk" and r[1] == "base UNKNOWN (not on record: zzz)"]
        self.assertEqual(len(unk_rows), 1, "the hover box says nothing about the unrecorded base: %s" % out["unkTip"])
        self.assertEqual(out["unkTip"][0][1], "Breath of the Dying", "the name still leads the box")
        self.assertEqual(out["unkTip"][1], unk_rows[0], "the UNKNOWN base is not in the base line's own place (under the name)")
        self.assertEqual(out["none"]["text"], 'base UNKNOWN (not on record) ▸', "a runeword with no base at all: %r" % out["none"])
        uniq = out["uniq"]
        self.assertEqual((uniq["tag"], uniq["text"]), ("select", "base UNKNOWN (not on record: zzz)"),
                         "a unique's fixed base control prints the bare code over an unrecorded base: %s" % uniq)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheLockersCharacterPickerOpens(unittest.TestCase):

    def test_the_control_opens_his_characters_and_a_bind_writes_only_the_bound_field(self):
        out = _bind(r"""
          window.openMuleCard('uni-armor');
          out.c0 = ctl(); out.statsNone = statsLine(); out.before = snap(); out.rosterBefore = JSON.parse(JSON.stringify(roster));
          press(out.c0.onclick);
          out.opened = !!listHtml(); out.opts = opts(); out.afterOpen = snap();
          out.bound = pick('build', 'b2');
          out.after = snap(); out.rosterAfter = JSON.parse(STORE['d2r_muleRoster'] || 'null');
          out.c2 = ctl(); out.listAfter = !!listHtml(); out.stats = statsLine();
          press(ctl().onclick); out.boundMain = pick('main', 'Shadowfang');
          out.rosterMain = JSON.parse(STORE['d2r_muleRoster']); out.c3 = ctl();
          press(ctl().onclick); out.unbound = pick('', '');
          out.rosterUn = JSON.parse(STORE['d2r_muleRoster']); out.c4 = ctl(); out.final = snap();
        """, store=_store())
        c0 = out["c0"]
        self.assertIsNotNone(c0, "the Locker panel lost its Character row")
        self.assertEqual((c0["tag"], c0["state"], c0["text"]), ("button", "none", "none bound ▾"),
                         "GrokBot's v3517 panel again: 'none bound' is text, not a control: %s" % c0)
        self.assertTrue(c0["onclick"], "the Character control carries no handler")
        self.assertEqual(out["statsNone"], "Character — none bound to this locker")
        self.assertTrue(out["opened"], "pressing the Character control opened nothing a user could see")
        rows = [(o["src"], o["id"]) for o in out["opts"]]
        self.assertEqual(rows, [("build", "b1"), ("build", "b2"), ("build", "b3"), ("main", "Shadowfang")],
                         "his characters, the MAIN build first, the rest newest first, then the MAIN he named: %s" % rows)
        t = [o["text"] for o in out["opts"]]
        self.assertTrue(t[0].startswith("★ MAIN Konyoress") and "Sorceress 80" in t[0], t[0])
        self.assertEqual([x for x in t if "★ MAIN" in x], [t[0]], "only the MAIN build wears the mark: %s" % t)
        self.assertIn("Hammerdin Paladin 91", t[1])
        self.assertIn("Assassin 70", t[3])
        self.assertIn("the MAIN you named", t[3])
        self.assertEqual(out["afterOpen"], out["before"], "OPENING the list wrote a store")
        # the bind: ONE field of ONE locker, and nothing else anywhere
        self.assertIs(out["bound"], True)
        changed = sorted(k for k in set(out["before"]) | set(out["after"]) if out["before"].get(k) != out["after"].get(k))
        self.assertEqual(changed, ["d2r_muleRoster"], "a bind wrote more than the roster: %s" % changed)
        before = dict((m["id"], m) for m in out["rosterBefore"])
        after = dict((m["id"], m) for m in out["rosterAfter"])
        self.assertEqual(sorted(after), sorted(before), "a bind added or dropped a locker")
        for mid in before:
            a = dict(after[mid])
            bc = a.pop("boundChar", None) if mid == "uni-armor" else None
            self.assertEqual(a, before[mid], "a bind changed %s beyond its bound character: %s" % (mid, a))
        bc = after["uni-armor"]["boundChar"]
        self.assertEqual(sorted(bc), ["at", "id", "name", "src"])
        self.assertEqual((bc["src"], bc["id"], bc["name"]), ("build", "b2", "Hammerdin"))
        datetime.strptime(bc["at"][:19], "%Y-%m-%dT%H:%M:%S")
        self.assertEqual((out["c2"]["state"], out["c2"]["text"]), ("build", "Hammerdin ▾"), "the control does not say the bind")
        self.assertFalse(out["listAfter"], "the list stayed open over the bind")
        self.assertEqual(out["stats"], "Character — Hammerdin bound to this locker")
        # the MAIN he named binds by its name; Unbind removes the field and nothing else
        self.assertIs(out["boundMain"], True)
        mb = [m for m in out["rosterMain"] if m["id"] == "uni-armor"][0]["boundChar"]
        self.assertEqual((mb["src"], mb["name"], sorted(mb)), ("main", "Shadowfang", ["at", "name", "src"]))
        self.assertEqual(out["c3"]["text"], "Shadowfang ▾")
        self.assertIs(out["unbound"], True, "the open list of a bound locker carries no Unbind")
        self.assertEqual(out["rosterUn"], out["rosterBefore"], "Unbind left the roster different from before the bind")
        self.assertEqual(out["c4"]["state"], "none")
        for k in ("d2r_charBuilds", "d2r_cbMain", "d2r_mainCharacter", "d2r_muleEquip"):
            self.assertEqual(out["final"].get(k), out["before"].get(k), "binding touched %s" % k)

    def test_no_characters_says_how_to_add_one_and_an_unreadable_store_is_unknown(self):
        empty = _bind(r"""
          window.openMuleCard('uni-armor'); press(ctl().onclick); out.say = listState(); out.opts = opts();
        """, store=_store(builds=None, main=None, declared=None))
        self.assertEqual(empty["opts"], [], "an empty store listed a character")
        self.assertIsNotNone(empty["say"], "an empty store's list says nothing")
        self.assertEqual(empty["say"]["state"], "empty")
        for w in ("No characters yet", "👤 Characters", "+ New character"):
            self.assertIn(w, empty["say"]["text"], "the empty list does not say how to add one: %s" % empty["say"])
        bad = _bind(r"""
          roster[0].boundChar = { src: 'build', id: 'b1', name: 'Konyoress', at: '2026-09-26T00:00:00Z' };
          window.openMuleCard('uni-armor'); out.c = ctl(); press(ctl().onclick); out.say = listState(); out.opts = opts();
          out.html = listHtml();
        """, store=_store(builds='{"b1": {"name": "Konyoress"'))
        self.assertIsNotNone(bad["say"], "an unreadable store's list says nothing")
        self.assertEqual(bad["say"]["state"], "unknown", "an unreadable store read as %s" % bad["say"])
        self.assertIn("UNKNOWN", bad["say"]["text"])
        self.assertNotIn("No characters yet", bad["html"], "an unreadable store said 'No characters yet'")
        self.assertEqual([(o["src"], o["id"]) for o in bad["opts"] if o["src"]], [("main", "Shadowfang")],
                         "the MAIN he named is still listed while the builds are UNKNOWN")
        self.assertEqual((bad["c"]["state"], bad["c"]["text"]), ("unknown", "UNKNOWN ▾"),
                         "a binding over an unreadable store must read UNKNOWN: %s" % bad["c"])
        self.assertIn("Konyoress", bad["c"]["title"])

    def test_a_binding_is_a_reference_a_rename_follows_and_a_deleted_build_is_unknown(self):
        renamed = dict(BUILDS)
        renamed["b2"] = dict(BUILDS["b2"], name="Hammerdin II")
        ren = _bind(r"""
          roster[0].boundChar = { src: 'build', id: 'b2', name: 'Hammerdin', at: '2026-09-26T00:00:00Z' };
          window.openMuleCard('uni-armor'); out.c = ctl(); out.stats = statsLine();
        """, store=_store(builds=renamed))
        self.assertEqual((ren["c"]["state"], ren["c"]["text"]), ("build", "Hammerdin II ▾"),
                         "a renamed build must read its NEW name - the binding is a reference: %s" % ren["c"])
        gone = _bind(r"""
          roster[0].boundChar = { src: 'build', id: 'gone', name: 'Old Sorc', at: '2026-09-26T00:00:00Z' };
          window.openMuleCard('uni-armor'); out.c = ctl(); out.stats = statsLine(); out.roster = JSON.stringify(roster);
        """, store=_store())
        c = gone["c"]
        self.assertEqual((c["state"], c["text"]), ("unknown", "UNKNOWN ▾"), "a deleted build read %s" % c)
        self.assertIn("Old Sorc", c["title"])
        self.assertIn("no longer saved", c["title"])
        self.assertEqual(gone["stats"], "Character — UNKNOWN bound to this locker", "never 'none bound' over a binding")
        self.assertIn('"id":"gone"', gone["roster"], "reading the binding rewrote it")

    def test_esc_closes_the_list_before_the_window(self):
        out = _bind(r"""
          window.openMuleCard('uni-armor'); out.hidden0 = box.hidden; press(ctl().onclick); out.open = !!listHtml();
          fire('keydown', { key: 'Escape' }); out.one = { list: !!listHtml(), hidden: box.hidden };
          fire('keydown', { key: 'Escape' }); out.two = { hidden: box.hidden };
        """, store=_store())
        self.assertEqual((out["hidden0"], out["open"]), (False, True), "BASELINE: the window is up and the list open")
        self.assertEqual(out["one"], {"list": False, "hidden": False}, "the first Esc must close the list, not the window")
        self.assertEqual(out["two"], {"hidden": True}, "the second Esc must close the window")


RED_PROOF = [
    {
        "why": "#253 - GrokBot's v3517 base Edit panel again: 'Normal · Crowbill' and nothing of the base",
        "file": "bible.html",
        "find": "esc(base ? base[0] : e.base) + rq + '</div>'\n      +   _cbEdBaseHtml(tr, e, it)\n",
        "replace": "esc(base ? base[0] : e.base) + rq + '</div>'\n",
        "matches": 1,
    },
    {
        "why": "#253 - the runeword / unique Edit panel prints no base rows",
        "file": "bible.html",
        "find": "(it[2] === 's' && it[7] ? ' · ' + esc(it[7].set) : '') + rq + '</div>'\n      +   _cbEdBaseHtml(tr, e, it)\n",
        "replace": "(it[2] === 's' && it[7] ? ' · ' + esc(it[7].set) : '') + rq + '</div>'\n",
        "matches": 1,
    },
    {
        "why": "#253 - the Edit panel reads a second derivation of the item (its socket and ethereal set aside)",
        "file": "bible.html",
        "find": "    var tr = _cbTipEntry(e, it, clvl, slot, b.cls), rq = _cbEdCannot(tr, clvl);\n    return '<div class=\"cb-ed cb-ed-b\" id=\"cb-ed\">'",
        "replace": "    var tr = _cbTipEntry(Object.assign({}, e, { socketed: [], eth: false }), it, clvl, slot, b.cls), rq = _cbEdCannot(tr, clvl);\n    return '<div class=\"cb-ed cb-ed-b\" id=\"cb-ed\">'",
        "matches": 1,
    },
    {
        "why": "#253 - a Hel picked into the socket leaves the Edit panel at 94 / 70 (the quiet refresh skips the rows)",
        "file": "bible.html",
        "find": "    if (eb && nb != null) eb.outerHTML = nb || '<div id=\"cb-ed-base\" hidden></div>';\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#253 - the base rows lose Required Strength (hover box and Edit panel alike)",
        "file": "bible.html",
        "find": "    if (rq.str) h += one(_cbUi('ItemStats1e', 'Required Strength: %d'), [rv(rq.str)], red(lo(rq.str), at && at.str));\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#253 - the base rows lose the one-hand damage",
        "file": "bible.html",
        "find": "    if (entry.dmg1) h += row(_cbUi('ItemStats1l', 'One-Hand Damage: %d to %d'), [par(entry.dmg1[0], entry.dmg1[1]), par(entry.dmg1[2], entry.dmg1[3])]);\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#253 - Max Sockets is a second count (the base's gemsockets, blind to the item level's band)",
        "file": "bible.html",
        "find": "    var rows = _d2TipBase(tr), sr = _cbSockRange(e, it);\n",
        "replace": "    var rows = _d2TipBase(tr), sr = { lo: 0, hi: (_cbBase(e.base) || [])[4] | 0, why: '' };\n",
        "matches": 1,
    },
    {
        "why": "#253 - what the base rows cannot say (a low-quality base's damage) is silently missing from the Edit panel",
        "file": "bible.html",
        "find": "    (tr.baseUnk || []).forEach(function(l){ rows += '<div class=\"' + (l.cls || 'd2t-unk') + '\">' + esc(l.t) + '</div>'; });\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#253 - the Edit note repeats Required Level beside its row (two answers on one panel)",
        "file": "bible.html",
        "find": "    return (tr.reqs.lvl && clvl != null && tr.reqs.lvl > clvl) ? ' · <span",
        "replace": "    return tr.reqs.lvl ? ' · Required Level ' + tr.reqs.lvl : 0 ? ' · <span",
        "matches": 1,
    },
    {
        "why": "#253 - GrokBot's v3517 locker again: 'Character: none bound' is text that does nothing",
        "file": "bible.html",
        "find": "      +   '<div class=\"mp-bind-r\"><span>Character</span>' + _bind.btn + '</div>'\n",
        "replace": "      +   '<div class=\"mp-bind-r\"><span>Character</span><span>none bound</span></div>'\n",
        "matches": 1,
    },
    {
        "why": "#253 - the list leaves out his builds",
        "file": "bible.html",
        "find": "    else r.rows.forEach(function(x){ out.rows.push({ src: 'build',",
        "replace": "    else [].forEach(function(x){ out.rows.push({ src: 'build',",
        "matches": 1,
    },
    {
        "why": "#253 - the list leaves out the MAIN he named",
        "file": "bible.html",
        "find": "      else out.rows.push({ src: 'main', id: String(mc.name),",
        "replace": "      else [].push({ src: 'main', id: String(mc.name),",
        "matches": 1,
    },
    {
        "why": "#253 - the list forgets which build is the MAIN (the Characters room's reader drops the mark)",
        "file": "bible.html",
        "find": "level: (lvl >= 1 && lvl <= 99) ? (lvl | 0) : null, main: id === mainId };",
        "replace": "level: (lvl >= 1 && lvl <= 99) ? (lvl | 0) : null, main: false };",
        "matches": 1,
    },
    {
        "why": "#253 - a bind also writes the locker's note (more than its bound field)",
        "file": "bible.html",
        "find": "    else delete m.boundChar;\n    try { saveR(); }\n",
        "replace": "    else delete m.boundChar;\n    m.note = String(m.note || '') + ' ';\n    try { saveR(); }\n",
        "matches": 1,
    },
    {
        "why": "#253 - a bind also marks the build as the MAIN (a store that is not the locker's)",
        "file": "bible.html",
        "find": "    _mpBindAt = null; _mpFocusNext = 'bind';\n",
        "replace": "    _mpBindAt = null; _mpFocusNext = 'bind'; if (x && x.src === 'build') window.LSR.setItem('d2r_cbMain', x.id);\n",
        "matches": 1,
    },
    {
        "why": "#253 - the binding shows the name copied at bind time (a renamed build reads its old name)",
        "file": "bible.html",
        "find": "text: (x.main ? '★ ' : '') + x.name, title:",
        "replace": "text: (x.main ? '★ ' : '') + String(bc.name), title:",
        "matches": 1,
    },
    {
        "why": "#253 - a binding to a deleted build reads 'none bound'",
        "file": "bible.html",
        "find": "      return { state: 'unknown', text: 'UNKNOWN', title: 'bound to the build \"' + nm + '\", but '",
        "replace": "      return { state: 'none', text: 'none bound', title: 'bound to the build \"' + nm + '\", but '",
        "matches": 1,
    },
    {
        "why": "#253 - an unreadable builds store reads as 'No characters yet'",
        "file": "bible.html",
        "find": "    if (!r || !r.ok || !Array.isArray(r.rows)){ out.ok = false; out.why = (r && r.why) || 'the builds could not be read'; }\n",
        "replace": "    if (!r || !r.ok || !Array.isArray(r.rows)){ out.ok = true; }\n",
        "matches": 1,
    },
    {
        "why": "#253 - an empty store's list does not say how to add a character",
        "file": "bible.html",
        "find": "    if (L.ok && !L.rows.length)\n      h += '<div class=\"mp-bind-none\" data-state=\"empty\">",
        "replace": "    if (false)\n      h += '<div class=\"mp-bind-none\" data-state=\"empty\">",
        "matches": 1,
    },
    {
        "why": "#253 - Esc closes the whole window over an open bind list",
        "file": "bible.html",
        "find": "    if (e.key !== 'Escape' || !openMuleId || !_mpBindAt || _mpPickAt) return;\n",
        "replace": "    return;\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 11 - the Base control prints the bare code and '(0 sockets max)' for a base not on record",
        "file": "bible.html",
        "find": "                       : 'base UNKNOWN (not on record' + (e.base ? ': ' + esc(String(e.base)) : '') + ')';\n",
        "replace": "                       : esc(String(e.base == null ? '' : e.base)) + ' (' + _cbMaxSock(e.base, e.ilvl) + ' sockets max)';\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 11 - the hover box prints no base line at all over a base not on record",
        "file": "bible.html",
        "find": "    if (!b && !_cbIsBase(it)){ out.base = 'base UNKNOWN (not on record' + (e.base ? ': ' + String(e.base) : '') + ')'; out.baseUnknown = true; }\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 11 - the box's UNKNOWN base line wears the grey base class, not the UNKNOWN class",
        "file": "bible.html",
        "find": "(entry.baseUnknown ? 'd2t-unk' : (entry.baseGrey ? 'd2t-g' : qc))",
        "replace": "(entry.baseGrey ? 'd2t-g' : qc)",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the Edit panel and the bind list were not driven. "
                         "UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
