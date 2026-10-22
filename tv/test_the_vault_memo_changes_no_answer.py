# -*- coding: utf-8 -*-
"""V1c (#152 item 4, #111 item 6; REG-2420..REG-2427) - THE VAULT'S SPEED MEMOS CHANGE NO ANSWER.

GrokBot on v3784: the 550-item speed test now finishes, in about 7.5 minutes, because hand adds are QUADRATIC
(30 ms at 50 items, 2.7 s at 600). Measured on the shipped page in node (tv/vault_page_node.py): one hand add at 300
items asked the router about every owned name about 15 times, ran the 398-name fuzzy fold 861 times (64% of the
add), walked the 867-name catalogue for every runeword on every ask, walked every saved move for every war keeper, and
a paint rebuilt every record three times per locker card. _itemCells parsed d2r_plannerMade before it looked at its own
cache (#111 item 6), and artOr parsed it again for every picture. The fix is eight memos (REG-2420..REG-2427):

  * the fuzzy fold's canonical, kept per trimmed name (suggestMule's hop);           REG-2420
  * the war keeper's walk of the saved moves, once per bag;                         REG-2421
  * the planner store, parsed once per stored string for _itemCells and artOr;     REG-2422
  * the catalogue walk of d2rItemLookup, once per name;                             REG-2423
  * one router ask per name per READ PHASE (a phase writes nothing, every write
    ends one) outside renderVault too: the plan of a hand row, a records pass, the
    collect loop before its commit and the unrouted check after it;                 REG-2424
  * the set-piece fold (_spNorm), once per string;                                  REG-2425
  * one records model for the whole shelf (the pass FIND already uses);             REG-2426
  * the ITEMS names in one Set for _vaultKeeps.                                      REG-2427

A memo that changes an answer is a defect wearing a speed-up, so this law is the proof that none does. The SAME fixture
runs twice on the shipped page: as it ships, and with window._vaultMemoOff = true, which turns every one of those memos
off (the path the page took before them). The fixture adds 84 names across every kind (uniques, set pieces ruled keep,
ruled junk and never ruled, runewords, bases, charms, curly apostrophes, misreads, names nothing knows), adds copies past
the war cap, flips two share switches, files and unfiles by hand, locks a name to his MAIN, files three sightings,
turns auto intake on and applies two, writes, changes, corrupts and clears a planner record, runs a drain frame, FIND
and a throw-out keep, and finally grows the catalogue. Every door's answer must be identical, and at eight points so
must every name's router answer, seam, footprint, pack size, picture, war keeper, move homes, catalogue hit, set canon,
twins and planner base, the MOVE TASKS / dock / shelf HTML, the move model, the records, the header and every store.

The comparison must not be vacuous: 50+ records and 50+ move rows, Grief's footprint follows its planner record (2x3,
then 2x4, then the guess again), a misread folds onto the roster, and the grown catalogue is seen by both doors.
The catalogue memos lean on one fact - ITEMS and ITEM_REGISTRY are filled once by the BOSSES build and written nowhere
else - so that is pinned here too. RED_PROOF below: each entry breaks one memo the way memos go wrong (a stale parse, a
wrong key, a lost invalidation, a phase that outlives its write, a shelf pass that never ends), and the answers move.
[[regression-guard]] [[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import io
import json
import os
import re
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

import vault_page_node as VPN  # noqa: E402  (the whole page in node)

CLOCK = "2026-10-22T10:00:00Z"
#: the one comment that quotes the BOSSES build (it is not a writer)
QUOTED_BUILD = "`ITEM_REGISTRY[d.n] = {...}; if (!d.nc) ITEMS.push(ITEM_REGISTRY[d.n])`"
SEED = 7

BODY = r"""
(function(){
function clean(x){
  return JSON.parse(JSON.stringify(x === undefined ? '__undef' : x, function(k, v){
    if (typeof v === 'string') return v.replace(/I·[0-9a-f]+·/g, 'I·*·');
    if (typeof v === 'number' && !isFinite(v)) return 'num:' + String(v);
    if (typeof v === 'function') return 'fn';
    if (v instanceof Set) return { set: Array.from(v) };
    if (v instanceof Map) return { map: Array.from(v.entries()) };
    return v;
  }));
}
function tryv(f){ try { return clean(f()); } catch (e) { return 'THREW: ' + String(e && e.message || e); } }
var PROBE = [
  'Harlequin Crest', 'Harlequin Crest (Shako)', 'Stone of Jordan', 'The Stone of Jordan', 'Arachnid Mesh', "Andariel's Visage",
  "Griffon's Eye", 'Nagelring', 'Gull', 'Annihilus', 'Hellfire Torch', "Gheed's Fortune", 'Rainbow Facet', 'Nokozan Relic',
  'Blackhand Key', "Bartuc's Cut-Throat", 'Death Cleaver', 'Bonehew', 'The Oculus', "Schaefer's Hammer", 'Shaftstop',
  "Nosferatu's Coil", 'Demon Limb', 'Lidless Wall', 'Crescent Moon', 'Wizardspike', 'War Traveler', "Tyrael's Might",
  'Windforce', 'Toothrow', 'Goldwrap', 'Hotspur', 'Atma’s Scarab', "Atma's Scarab", 'Saracen’s Chance',
  "Tal Rasha's Guardianship", "Tal Rasha's Horadric Crest", "Immortal King's Stone Crusher", "Natalya's Totem",
  "Sigon's Guard", "Cathan's Mesh", "Isenhart's Case", "Arcanna's Sign", "Aldur's Advance", "Griswold's Heart",
  "M'avina's Embrace", "Trang-Oul's Claws", "Cow King's Horns", "Horazon's Splendor",
  'Enigma', 'Insight', 'Spirit', 'Grief', 'Call to Arms', 'Breath of the Dying', 'Beast', 'Infinity', 'Heart of the Oak',
  'Chains of Honor', 'Fortitude', 'Hand of Justice', 'Delirium', 'Black', 'Bone',
  'Monarch', 'Archon Plate', 'Phase Blade', 'Shako', 'Colossus Blade', 'Sacred Targe',
  'Amulet of the Viper', 'Ber Rune', "Diablo's Horn", 'Circlet', 'Bone Visor', 'Battlecage', 'Naglring',
  '  Harlequin Crest  ', 'harlequin crest', 'Ring', 'Grand Charm'
];
function probe(tag){
  var o = { tag: tag, n: {} };
  var pool = []; try { pool = Array.from(owned).sort(); } catch (e) {}
  PROBE.forEach(function(n){
    var r = {};
    r.sug = tryv(function(){ return window.suggestMule(n); });
    r.seam = tryv(function(){ return window._vaultSeamHome(n); });
    r.cells = tryv(function(){ return window._itemCells(n); });
    r.size = tryv(function(){ return window.vaultSize(n); });
    r.art = tryv(function(){ return window.artOr(n, 'x', 'sm'); });
    r.keeper = tryv(function(){ return window._vaultWarKeeper(n); });
    r.home0 = tryv(function(){ return window._vaultMoveHome(n, 0); });
    r.home1 = tryv(function(){ return window._vaultMoveHome(n, 1); });
    r.look = tryv(function(){ var x = window.d2rItemLookup(n); return x ? x.n : null; });
    r.canon = tryv(function(){ return window._vfCanon(n); });
    r.isSet = tryv(function(){ return window._vfIsSetPiece(n); });
    r.twins = tryv(function(){ return window._vaultSameItemNames(n, pool); });
    r.made = tryv(function(){ return window._vpMadeBase(n); });
    r.madeOf = tryv(function(){ return window._vpMadeOf(n); });
    o.n[n] = r;
  });
  return o;
}
function stores(){
  var s = {};
  H.RAW.forEach(function(v, k){ s[k.replace(/^I·[0-9a-f]+·/, 'I·*·')] = v.replace(/I·[0-9a-f]+·/g, 'I·*·'); });
  return s;
}
function view(){
  var g = function(id){ var e = document.getElementById(id); return e ? e.innerHTML : null; };
  return clean({ move: g('vault-move-list'), dock: g('vault-dock'), shelf: g('vault-shelf'), eq: g('vault-equipped'),
                 model: window._moveModel ? { tasks: window._moveModel.tasks, unrouted: window._moveModel.unrouted, done: window._moveModel.done } : null,
                 header: tryv(function(){ return window._vaultRecordsHeader(); }),
                 records: tryv(function(){ return window._vaultRecords(); }),
                 dockNames: tryv(function(){ return window._vaultDockNames(); }),
                 owned: Array.from(owned).sort(),
                 warFull: window._vaultWarFull || null, warFullWhy: window._vaultWarFullWhy || null });
}
OUT.steps = [];
function step(tag, f){ var ret = tryv(f); try { H.flush(60, 3); } catch (e) {} OUT.steps.push({ tag: tag, ret: ret }); }
function snap(tag){ OUT.steps.push({ tag: 'probe:' + tag, probe: probe(tag), view: view(), stores: stores() }); }
var HAND = { by: 'hand', at: new Date().toISOString(), where: 'the memo law' };

step('auto-off', function(){ return window._vaultAutoIntakeSet(false); });
PROBE.forEach(function(n){ step('add ' + n, function(){ return window.vaultHandAdd(n); }); });
step('render', function(){ renderVault(); return 1; });
snap('after-adds');
['Arachnid Mesh', 'Arachnid Mesh', 'Arachnid Mesh', 'Arachnid Mesh', 'Arachnid Mesh', 'Harlequin Crest', 'Harlequin Crest',
 'Enigma', 'Enigma', "Tal Rasha's Guardianship", 'Grief', 'Grief', 'Nagelring', 'Nagelring', "Andariel's Visage", "Andariel's Visage"]
  .forEach(function(n, i){ step('copy ' + i + ' ' + n, function(){ return window.vaultHandAdd(n); }); });
step('render2', function(){ renderVault(); return 1; });
snap('after-copies');
step('share mule', function(){ return window._setShareOverride('Harlequin Crest (Shako)', 'mule'); });
step('share shared', function(){ return window._setShareOverride('Insight', 'shared'); });
/* asked at once, with no paint between the switch and the question: a router memo that outlived its phase answers stale */
step('share asked at once', function(){ return { insight: window._vaultSeamHome('Insight'), shako: window._vaultSeamHome('Harlequin Crest (Shako)'),
  insightHome: window._vaultMoveHome('Insight', 0), shakoHome: window._vaultMoveHome('Harlequin Crest (Shako)', 0) }; });
step('file griffon', function(){ return window.vaultFile("Griffon's Eye", HAND, { mule: 'uni-armor' }); });
step('file demon limb', function(){ return window.vaultFile('Demon Limb', HAND, { mule: 'uni-weap' }); });
step('file shaftstop', function(){ return window.vaultFile('Shaftstop', HAND, { mule: 'uni-armor' }); });
step('unassign shaftstop', function(){ return window.vaultUnassign('Shaftstop'); });
step('lane lock', function(){ return window._laneLockNote('Nagelring', 'equipment', ['s1', 's2', 's3']); });
step('lock asked at once', function(){ return { nagel: window._vaultSeamHome('Nagelring'), home: window._vaultMoveHome('Nagelring', 0) }; });
step('seen 1', function(){ return window._ownedAdd('Wizardspike', { source: 'kai-register', by: 'reader', frameId: 'f_101', sessionId: 's_7', loc: 'stash', holder: 'MULE-3', cell: 'stash:c2r3', conf: 0.9 }); });
step('seen 2', function(){ return window._ownedAdd('Arachnid Mesh', { source: 'kai-register', by: 'reader', frameId: 'f_102', sessionId: 's_7', loc: 'shared', holder: 'SHARED STASH', cell: 'shared:c0r0', conf: 0.9 }); });
step('seen main', function(){ return window._ownedAdd('War Traveler', { source: 'kai-register', by: 'reader', frameId: 'f_103', sessionId: 's_8', loc: 'equipment', holder: 'MAIN', cell: null, conf: 0.9 }); });
step('auto-on', function(){ return window._vaultAutoIntakeSet(true); });
step('sight insight', function(){ return window._vaultMoveApplySight('Insight', { holder: 'RUNEWORDS', location: 'stash', cell: 'stash:c0r0', frame: 'f_9' }); });
step('sight mesh', function(){ return window._vaultMoveApplySight('Arachnid Mesh', { holder: 'SHARED STASH', location: 'shared', cell: 'shared:c0r0', frame: 'f_10' }); });
step('auto-off2', function(){ return window._vaultAutoIntakeSet(false); });
step('render3', function(){ renderVault(); return 1; });
snap('after-files');
step('planner grief', function(){ LSR.setItem('d2r_plannerMade', JSON.stringify({ Grief: { id: 'grief', base: '7cr', baseName: 'Phase Blade', q: 'r', affixes: [], eth: false, sockets: 5, rolls: null } })); return 1; });
snap('planner-phase');
step('planner grief colossus', function(){ LSR.setItem('d2r_plannerMade', JSON.stringify({ Grief: { id: 'grief', base: '7gd', baseName: 'Colossus Blade', q: 'r', affixes: [], eth: false, sockets: 5, rolls: null }, Spirit: { id: 'spirit', base: '7cr', baseName: '', q: 'r' } })); return 1; });
snap('planner-colossus');
step('planner garbage', function(){ LSR.setItem('d2r_plannerMade', '{not json'); return 1; });
snap('planner-garbage');
step('planner cleared', function(){ LSR.removeItem('d2r_plannerMade'); return 1; });
snap('planner-cleared');
step('gone', function(){ return window._vaultGoneObserve({ session: 's_9', holder: 'MULE-3', location: 'stash', items: [], ground: [] }); });
step('find soj', function(){ var r = window.vaultFind('soj'); var e = document.getElementById('vault-find-results'); return { r: r, html: e ? e.innerHTML : null }; });
step('find tal', function(){ var r = window.vaultFind('tal'); var e = document.getElementById('vault-find-results'); return { r: r, html: e ? e.innerHTML : null }; });
step('keep throw', function(){ return window._vaultThrowKeep ? window._vaultThrowKeep('Toothrow', 0) : null; });
step('render4', function(){ renderVault(); return 1; });
snap('final');
/* the catalogue grows: a memo that keeps an answer across that is stale */
step('items before', function(){ var x = window.d2rItemLookup('Zzz Memo Law Unique'); return x ? x.n : null; });
step('items before add', function(){ return window.vaultHandAdd('Zzz Memo Law Unique'); });
step('items push', function(){ ITEMS.push({ n: 'Zzz Memo Law Unique', tier: 'u', sources: [] }); return ITEMS.length; });
step('items after', function(){ var x = window.d2rItemLookup('Zzz Memo Law Unique'); return x ? x.n : null; });
step('items after add', function(){ return window.vaultHandAdd('Zzz Memo Law Unique'); });
step('items after sug', function(){ return window.suggestMule('Zzz Memo Law Unique'); });
})();
"""

_RUNS = {}


def _run(memo_off):
    key = "off" if memo_off else "on"
    if key not in _RUNS:
        _RUNS[key] = VPN.run(("window._vaultMemoOff = %s;\n" % ("true" if memo_off else "false")) + BODY,
                             clock=CLOCK, seed=SEED, timeout=900)
    return _RUNS[key]


def differences(a, b, path="", out=None, limit=12):
    """The first `limit` places two answers part. -> [str]"""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if type(a) is not type(b):
        out.append("%s: %r | %r" % (path, str(a)[:160], str(b)[:160]))
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append("%s/%s: only %s" % (path, k, "with the memo" if k in a else "without it"))
            else:
                differences(a[k], b[k], path + "/" + k, out, limit)
            if len(out) >= limit:
                break
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append("%s: %d items | %d items" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            differences(x, y, "%s[%d]" % (path, i), out, limit)
            if len(out) >= limit:
                break
    elif a != b:
        out.append("%s: %r | %r" % (path, str(a)[:200], str(b)[:200]))
    return out


def _snap(out, tag):
    for s in out["steps"]:
        if s.get("tag") == "probe:" + tag:
            return s
    raise AssertionError("the fixture took no %r snapshot" % tag)


def _ret(out, tag):
    for s in out["steps"]:
        if s.get("tag") == tag:
            return s.get("ret")
    raise AssertionError("the fixture has no %r step" % tag)


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheVaultMemoChangesNoAnswer(unittest.TestCase):

    def test_1_the_page_boots_whole_both_ways(self):
        for key, out in (("with the memo", _run(False)), ("without it", _run(True))):
            self.assertEqual(out["__boot"]["errors"], [], "a page script did not run in node (%s): %r" % (key, out["__boot"]))
            self.assertGreater(out["__boot"]["scripts"], 20, "the page's scripts were not found (%s)" % key)

    def test_2_every_answer_is_the_same_with_the_memo_off(self):
        on, off = _run(False), _run(True)
        self.assertEqual(len(on["steps"]), len(off["steps"]), "the two runs did not take the same steps")
        diffs = differences(on["steps"], off["steps"], "steps")
        named = []
        for d in diffs:
            m = re.match(r"steps\[(\d+)\](.*)", d)
            named.append(("%s%s" % (on["steps"][int(m.group(1))]["tag"], m.group(2))) if m else d)
        self.assertEqual(named, [], "a V1c memo changed %s answer(s) - first: \n  %s" % (len(named), "\n  ".join(named)))

    def test_3_the_comparison_is_not_vacuous(self):
        on = _run(False)
        after = _snap(on, "after-copies")
        recs = (after["view"].get("records") or {}).get("records") or []
        tasks = ((after["view"].get("model") or {}).get("tasks")) or []
        self.assertGreaterEqual(len(recs), 50, "the fixture reached only %d records" % len(recs))
        self.assertGreaterEqual(len(tasks), 50, "the fixture painted only %d move rows" % len(tasks))
        self.assertGreater(len(after["view"].get("shelf") or ""), 20000, "the shelf did not paint")
        cells = [(_snap(on, t)["probe"]["n"]["Grief"]["cells"].get("w"), _snap(on, t)["probe"]["n"]["Grief"]["cells"].get("h"),
                  bool(_snap(on, t)["probe"]["n"]["Grief"]["cells"].get("approx")))
                 for t in ("after-files", "planner-phase", "planner-colossus", "planner-garbage", "planner-cleared")]
        self.assertEqual(cells, [(1, 2, True), (2, 3, False), (2, 4, False), (1, 2, True), (1, 2, True)],
                         "Grief's footprint did not follow its planner record: %r" % cells)
        made = [_snap(on, t)["probe"]["n"]["Grief"]["made"] for t in ("planner-phase", "planner-colossus", "planner-cleared")]
        self.assertEqual(made, ["Phase Blade", "Colossus Blade", ""], "Grief's picture base did not follow its record: %r" % made)
        bc = _snap(on, "after-adds")["probe"]["n"]["Battlecage"]["sug"]
        self.assertIn("misread of Rattlecage", str(bc.get("why")), "the fuzzy fold no longer reached the roster: %r" % bc)
        self.assertIsNone(_ret(on, "items before"), "the test name was already in the catalogue")
        self.assertEqual(_ret(on, "items after"), "Zzz Memo Law Unique", "the grown catalogue was not seen by the lookup")
        before, after_add = _ret(on, "items before add"), _ret(on, "items after add")
        self.assertFalse(before.get("ok"), "a name nothing knows was added: %r" % before)
        self.assertTrue(after_add.get("ok"), "the grown catalogue was not seen by the hand door: %r" % after_add)

    def test_4_the_catalogue_has_one_writer(self):
        """d2rItemLookup's memo and _vaultKeeps' name set lean on this: ITEMS and ITEM_REGISTRY are filled by the BOSSES
        build and written nowhere else. A second writer must re-key both memos (the length check covers ITEMS growing,
        never an entry replaced in place)."""
        with io.open(VPN.BIBLE, encoding="utf-8") as fh:
            s = fh.read()
        # one comment quotes the build line in backticks; it is the only quote allowed, and it is counted out by its text
        quoted = s.count(QUOTED_BUILD)
        writes = re.findall(r"(?<![\w.])ITEMS\s*\.\s*(?:push|splice|unshift|pop|shift|sort|reverse|fill|copyWithin)\s*\(", s)
        self.assertEqual(len(writes) - quoted, 1, "ITEMS has %d writers (want the one BOSSES build): %r" % (len(writes) - quoted, writes))
        self.assertEqual(s.count("if (!d.nc) ITEMS.push(ITEM_REGISTRY[d.n]);"), 1, "the BOSSES build is not the ITEMS writer")
        reg = re.findall(r"(?<![\w.])ITEM_REGISTRY\s*\[[^\]]+\]\s*=(?!=)", s)
        self.assertEqual(len(reg) - quoted, 1, "ITEM_REGISTRY has %d writers (want the one BOSSES build): %r" % (len(reg) - quoted, reg))
        self.assertEqual(len(re.findall(r"(?<![\w.])ITEMS\s*\[[^\]]+\]\s*=(?!=)", s)), 0, "an ITEMS entry is written in place")


RED_PROOF = [
    {"why": "REG-2422 - the planner read keeps its parse after the store changed: Grief keeps its Phase Blade footprint and picture",
     "file": "bible.html",
     "find": "      if (!(_vpMadeRO.ok && _vpMadeRO.raw === raw)){",
     "replace": "      if (!_vpMadeRO.ok){",
     "matches": 1, "needs": "node"},
    {"why": "REG-2421 - the keeper index keeps the HIGHEST copy with a shared target, not the lowest",
     "file": "bible.html",
     "find": "      if (cur == null || +p[1] < cur) ix.set(p[0], +p[1]);",
     "replace": "      if (cur == null || +p[1] > cur) ix.set(p[0], +p[1]);",
     "matches": 1, "needs": "node"},
    {"why": "REG-2420 - the fold memo answers every name with the first name's canonical",
     "file": "bible.html",
     "find": "      if (_sugFoldMemo.has(name)) return _sugFoldMemo.get(name);",
     "replace": "      if (_sugFoldMemo.size) return _sugFoldMemo.values().next().value;",
     "matches": 1, "needs": "node"},
    {"why": "REG-2423 - the catalogue memo is not dropped when ITEMS grows",
     "file": "bible.html",
     "find": "    if (!(_ilSig && _ilSig[0] === ITEMS && _ilSig[1] === ITEMS.length && _ilSig[2] === R)){",
     "replace": "    if (!(_ilSig && _ilSig[0] === ITEMS && _ilSig[2] === R)){",
     "matches": 1, "needs": "node"},
    {"why": "REG-2425 - the set-piece fold memo is keyed by the name's length, so two set pieces share one canon",
     "file": "bible.html",
     "find": ("      if (_spNormMemo.has(s)) return _spNormMemo.get(s);\n    }\n"
              "    var b = en ? en(s) : String(s == null ? '' : s).toLowerCase();\n"
              "    var out = b.replace(/[‘’ʼ＇′´‛]/g, \"'\");\n"
              "    if (memo){ if (_spNormMemo.size >= 5000) _spNormMemo.clear(); _spNormMemo.set(s, out); }"),
     "replace": ("      if (_spNormMemo.has(s.length)) return _spNormMemo.get(s.length);\n    }\n"
                 "    var b = en ? en(s) : String(s == null ? '' : s).toLowerCase();\n"
                 "    var out = b.replace(/[‘’ʼ＇′´‛]/g, \"'\");\n"
                 "    if (memo){ if (_spNormMemo.size >= 5000) _spNormMemo.clear(); _spNormMemo.set(s.length, out); }"),
     "matches": 1, "needs": "node"},
    {"why": "REG-2424 - a read phase never ends: its router memo outlives the share switch, the filings and the lane lock",
     "file": "bible.html",
     "find": "    try { return fn(); }\n    finally { window._seamPaint = prev; }\n  }",
     "replace": "    try { return fn(); }\n    finally { }\n  }",
     "matches": 1, "needs": "node"},
    {"why": "REG-2426 - the shelf's records pass never ends: every later records answer is the first paint's model",
     "file": "bible.html",
     "find": "    } finally { window._vrFindPass = _vrShelfOuter || null; } /* V1c the shelf pass ends with the shelf */",
     "replace": "    } finally { } /* V1c the shelf pass ends with the shelf */",
     "matches": 1, "needs": "node"},
    {"why": "REG-2427 - the ITEMS name set is not rebuilt when ITEMS grows: the hand door refuses the grown catalogue",
     "file": "bible.html",
     "find": "    if (!(_vkSig && _vkSig[0] === ITEMS && _vkSig[1] === ITEMS.length)){",
     "replace": "    if (!(_vkSig && _vkSig[0] === ITEMS)){",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
