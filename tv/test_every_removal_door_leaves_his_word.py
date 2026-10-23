# -*- coding: utf-8 -*-
"""REG-2404 + REG-2405 - EVERY DOOR THAT TAKES A NAME OUT OF OWNED LEAVES HIS WORD ON RECORD (the review of REG-2400/2401,
findings 2 and 3).

REG-2401's verdict reads a frame 'gone' - and vaultIntake reads it again without asking, on every door but the folder -
whenever a name the frame read has left owned with NO REMOVAL ON RECORD (_removedAfter finds no journal row). That is
right for a silent loss and wrong for his own removal, and two of his removal doors wrote no row:
  * toggleOwned's non-grail un-tick (runewords, set pieces, EXTRA_ITEMS, socketed bases) deleted straight out of owned;
  * vaultFixSockets RENAMES a misread label (old out, corrected in) - so a re-read put the misread label back beside the
    fixed one. Reviewer, on the page's real removal predicate: un-tick -> 'gone', socket fix -> 'gone' (gone = the old
    label); card-click and forge consume -> 'removed'.
And REG-2400's doctor made a third door's leftover permanent: the Magic & Rare ✕ (vaultThrowFind) deleted the
magicFinds record only, though since #75 the keeper is ALSO owned. The load-time prune used to sweep that leftover; the
doctor keeps a name no catalogue knows, so a tossed keeper came back as "1 item you own ... a reload never drops what you
own", for good (reviewer: owned still holds 'Death Loop', receipt.kept = ['Death Loop']).

NOW: the un-tick goes through the removal door (lane 'un-tick', keepFiling) exactly as the grail branch does; the
socket fix tells the scan ledger (_intakeSeenRename: the record holds the new name and keeps the old under `as`); the
Magic & Rare ✕ takes the owned name through the door too - the batch carries the Magic & Rare record so the undo is
whole - and a keeper Magic & Rare held alone gets the per-name removal note. The planner's take-back (_vpDrop) only ever
undoes the add its own pick made a moment ago; a pick over an item he already had is never taken back.

WHAT THIS LAW HOLDS - each door is the SHIPPED function cut whole from bible.html (toggleOwned, vaultRemove and the
journal it writes, vaultRestoreLast, vaultUnown, vaultThrowFind, vaultFixSockets, _vpDrop, the page's real removal
predicate _removalIsHisWord / _vaultRemovalNote / _removedAfter, the ⟦INTAKE SEEN VERDICT⟧ block, and for the reload
the whole load-time prune with its owned-load doctor) run in node: a frame reads the name, the door takes it, and the
verdict on that frame is never 'gone'. A missing node raises: this law does not skip. Browser half (CI):
tests/reg2400_reload_keeps_what_he_owns.spec.ts.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")

#: the page's removal predicate and its helpers, cut as they ship
JOURNAL = [
    ("  function _iso(ms){ try { return new Date(ms).toISOString(); }", "\n"),
    ("  function _ms(v){\n    if (typeof v === 'number') return (isFinite(v) && v > 0) ? v : null;", "\n  }\n"),
    ("  function _regName(nm){\n", "\n  }\n"),
    ("  function _bfJson(k, dflt){", "catch (e) { return undefined; } }\n"),
    ("  var _RM_NOT_HIS_WORD = ", "\n"),
    ("  window._removalIsHisWord = function(b){", "\n  };\n"),
    ("  var _RM_AT_KEY = ", "\n"),
    ("  function _rmRead(k, shape, dflt){", "\n  }\n"),
    ("  window._vaultRemovalNote = function(b){", "\n  };\n"),
    ("  window._removedAfterIndex = function(){", "\n  };\n"),
    ("  window._removedAfter = function(name, ts, index){", "\n  };\n"),
]
#: the removal door, its journal and its undo (the same region tv/test_the_removal_door_is_undoable.py cuts)
DOOR = ("  var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n", "  // v342.3 — throw out a Magic & Rare keeper")
UNOWN = ("  window.vaultUnown = function(name){\n", "\n  };\n")
TOSS = ("  window.vaultThrowFind = function(name){\n", "\n  };\n")
FIX = ("  window.vaultFixSockets = function(name, n){\n", "\n  };\n")
VPDROP = ("  function _vpDrop(){\n", "\n  }\n")
VERDICT = ("  /* ⟦INTAKE SEEN VERDICT BEGIN⟧", "  /* ⟦INTAKE SEEN VERDICT END⟧ */\n")
TOGGLE = "function toggleOwned(name, prov) {\n"
#: the load
NORM = ("function _norm(s){", "\n")
SAFE = ("const _safeJsonParse = (raw, fallback) => {", "\n};\n")
RUNEWORDS = ("const RUNEWORDS = [", "\n];\n")
PRUNE = ("(function _v42_sanitizeWishlistOwned() {", "\n  // v659 — GRAIL FOUND-SEED floor")


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair, inclusive_end=True):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end, i + len(start))
    return s[i:j + (len(end) if inclusive_end else 0)]


def _function(s, start):
    """a whole top-level function by brace depth from its own first line"""
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j, depth = s.index("{", i), 0
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i:j + 1]
        j += 1
    raise AssertionError("unbalanced braces cutting %r" % start[:40])


def _run(js):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if r.returncode != 0:
        raise AssertionError("the cut doors did not run in node: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


def _doors(body):
    s = _src()
    js = r"""
var window = globalThis;
var RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
var LS = window.LSR, SEEN_KEY = 'd2r_intakeSeen';
/* the page's canonical fold, reduced to what these names need (case, curly quotes, a trailing parenthetical) */
var _cnV = function(x){ return String(x||'').replace(/[‘’`]/g, "'").toLowerCase().trim().replace(/\s*\([^)]*\)\s*$/,'').trim(); };
%(journal)s
/* ── the vault's state, stubbed only where the doors touch it ── */
var owned = new Set(), magicFinds = {}, assign = {}, copies = {}, unknownReads = new Set();
var etherealItems = new Set(), superiorBases = new Set(), PROV = {};
function _provAll(){ return PROV; }
function _provDrop(names){ (Array.isArray(names) ? names : [names]).forEach(function(n){ delete PROV[String(n)]; }); }
function _provAsWitness(r){ return r; }
function persistOwned(){ LS.setItem('d2r_owned', JSON.stringify(Array.from(owned))); LS.setItem('d2r_magicFinds', JSON.stringify(magicFinds)); }
function persist(){ persistOwned(); }
function saveA(){} function renderVault(){} function refreshOpenCard(){}
var SAID = []; function status(m){ SAID.push(String(m)); }
window._repaintOwned = function(){};
window._D2R_LEDGER = 'KonyoEndgame'; window.D2R_PROFILE = 'main';
window._ownedAdd = function(n, rec){ var had = owned.has(n); owned.add(n); return { added: !had }; };
window._ownedProvForget = function(n){ if (PROV[n] && PROV[n].kind === 'owned'){ delete PROV[n]; return true; } return false; };
function muleById(id){ return (id === 'bases' || id === 'mule7') ? { id: id, name: id } : null; }
function suggestMule(){ return null; }
window.vaultFile = function(n, w, o){ if (o && o.mule) assign[n] = o.mule; return { ok: true }; };
function findSetPiece(){ return null; }
function _ensureSocketBaseEntry(){}
%(door)s
%(unown)s
%(toss)s
%(fix)s
%(verdict)s
/* ── toggleOwned's world: one grail unique; everything else takes the non-grail branch ── */
var ITEMS = [{ n: 'Harlequin Crest', tier: 'grail' }];
window._gUniqueRoster = function(){ return ['Harlequin Crest']; };
window._UNI_EXTRA = {}; window._GRAIL_SEED = {};
function _gFound(){ return false; } function _gFoundDirty(){}
function renderHero(){} function renderBossCards(){} function renderCalc(){} function renderGrailProgress(){}
function showCelebrate(){} function ownedPool(){ return Array.from(owned); }
var document = { getElementById: function(){ return null; } };
%(toggle)s
/* ── the planner's take-back ── */
var _vpMade = null; function _vpForget(){}
window.vaultUnassign = function(n){ delete assign[n]; return { ok: true }; };
%(vpdrop)s
/* ── a frame reads names; the verdict on it afterwards ── */
var T0 = Date.now();
function readFrame(f, names){
  names.forEach(function(n){ owned.add(n); });
  var seen = JSON.parse(RAW[SEEN_KEY] || '{}');
  _intakeSeenMark(seen, f, { nw: names.slice(), own: [], unr: [], mf: [], err: false }, _intakeSeenAsk());
  RAW[SEEN_KEY] = JSON.stringify(seen);
}
function verdict(f){ return _intakeSeenVerdict(JSON.parse(RAW[SEEN_KEY] || '{}'), f, _intakeSeenAsk()); }
function later(){ var t = Date.now() + 3; while (Date.now() < t) {} }     /* a removal is newer than the read */
function journal(){ return JSON.parse(RAW['d2r_vaultRemoved'] || '[]'); }
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
""" % {"journal": "\n".join(_cut(s, p) for p in JOURNAL), "door": _cut(s, DOOR, inclusive_end=False),
       "unown": _cut(s, UNOWN), "toss": _cut(s, TOSS), "fix": _cut(s, FIX), "verdict": _cut(s, VERDICT),
       "toggle": _function(s, TOGGLE), "vpdrop": _cut(s, VPDROP), "body": body}
    return _run(js)


def _reload(body):
    s = _src()
    js = r"""
var window = globalThis;
var RAW = {}, WARN = [];
console.warn = function(m){ WARN.push(String(m)); };
var LS = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
           setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
window.LSR = LS;
%(norm)s
%(safe)s
%(runewords)s
var SUNDER_CHARMS = [], BASE_CLASS = {};
var ITEM_REGISTRY = { "Harlequin Crest": { n: "Harlequin Crest" } };
var _UNI_EXTRA = {}, _GRAIL_SEED = {}, _EXTRA_ITEM_SET = new Set();
window._gUniqueRoster = function(){ return ["Harlequin Crest"]; };
function findSetPiece(){ return null; }
var wishlist, owned, magicFinds, assign = {}, PROV = {};
function persist(){ LS.setItem('d2r_wishlist', JSON.stringify(Array.from(wishlist))); LS.setItem('d2r_owned', JSON.stringify(Array.from(owned)));
                    LS.setItem('d2r_magicFinds', JSON.stringify(magicFinds)); }
function persistOwned(){ LS.setItem('d2r_owned', JSON.stringify(Array.from(owned))); LS.setItem('d2r_magicFinds', JSON.stringify(magicFinds)); }
function saveA(){} function renderVault(){} function refreshOpenCard(){} function status(){}
window._repaintOwned = function(){};
function _provAll(){ return PROV; } function _provDrop(){}
window._ownedAdd = function(n){ owned.add(n); return { added: true }; };
function muleById(){ return null; }
var _cnV = function(x){ return String(x||'').toLowerCase().trim(); };
%(journal)s
%(door)s
%(toss)s
function El(){ this.hidden = true; this.innerHTML = ''; }
var SLOT = new El();
var document = { getElementById: function(id){ return id === 'vault-owned-kept' ? SLOT : null; } };
/* ONE PAGE LOAD: the stores read the way bible.html reads them, then the shipped prune and its doctor */
function pageLoad(){
  wishlist = new Set(_safeJsonParse(LS.getItem('d2r_wishlist'), []));
  owned = new Set(_safeJsonParse(LS.getItem('d2r_owned'), []));
  magicFinds = _safeJsonParse(LS.getItem('d2r_magicFinds'), {}) || {};
  %(prune)s
}
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
""" % {"norm": _cut(s, NORM), "safe": _cut(s, SAFE), "runewords": _cut(s, RUNEWORDS),
       "journal": "\n".join(_cut(s, p) for p in JOURNAL), "door": _cut(s, DOOR, inclusive_end=False),
       "toss": _cut(s, TOSS), "prune": _cut(s, PRUNE, inclusive_end=False) + "\n})();\n", "body": body}
    return _run(js)


class EveryRemovalDoorLeavesHisWord(unittest.TestCase):

    def test_his_non_grail_untick_is_on_record_so_its_frame_is_never_read_again(self):
        got = _doors(r"""
var F = { name: 'shot_enigma.jpg', lastModified: 1 };
readFrame(F, ['Enigma']); assign['Enigma'] = 'mule7'; PROV['Enigma'] = { kind: 'owned', source: 'intake-read' };
later();
toggleOwned('Enigma');                                   /* his un-tick on the runeword's card (the non-grail branch) */
OUT.owned = owned.has('Enigma'); OUT.v = verdict(F).state;
OUT.batches = journal().map(function(b){ return { lane: b.lane, names: b.names, keepFiling: b.keepFiling }; });
OUT.filing = assign['Enigma'] || null; OUT.receipt = !!PROV['Enigma'];
OUT.noted = (JSON.parse(RAW['d2r_vaultRemovedAt'] || '{}')['enigma'] || {}).lane || null;
OUT.undo = window.vaultRestoreLast(); OUT.back = owned.has('Enigma');
toggleOwned('Socketed Thing (4os)');                    /* a tick of a name he did not hold is an add, never a removal */
OUT.addBatches = journal().length;
""")
        self.assertFalse(got["owned"])
        self.assertEqual(got["v"], "removed", "his non-grail un-tick left no removal on record - its frame reads '%s' "
                                               "and a re-read brings the item back" % got["v"])
        self.assertEqual(got["batches"], [{"lane": "un-tick", "names": ["Enigma"], "keepFiling": True}])
        self.assertEqual(got["filing"], "mule7", "the un-tick deleted a mule filing (his ruling: it never does)")
        self.assertFalse(got["receipt"], "the un-tick left the owned receipt standing (2026-09-28: it takes it)")
        self.assertEqual(got["noted"], "un-tick", "the un-tick is not noted per name - the ring forgets it")
        self.assertEqual(got["undo"]["restored"], 1, "the un-tick is not undoable")
        self.assertTrue(got["back"])
        self.assertEqual(got["addBatches"], 0, "a tick wrote a removal batch")

    def test_his_socket_count_fix_is_his_rename_not_a_loss(self):
        got = _doors(r"""
var F = { name: 'shot_monarch.jpg', lastModified: 1 }, G = { name: 'shot_other.jpg', lastModified: 2 };
readFrame(F, ['Monarch (Larzuk base)', 'Shako']); readFrame(G, ['Grief']);
later();
window.vaultFixSockets('Monarch (Larzuk base)', 4);     /* his fix: the AI missed the sockets */
var v = verdict(F), seen = JSON.parse(RAW[SEEN_KEY]);
OUT.v = v.state; OUT.gone = v.gone; OUT.rec = seen['shot_monarch.jpg']; OUT.other = seen['shot_other.jpg'];
OUT.prev = _intakePrevOf(seen, F);
window.vaultFixSockets('Monarch (4os)', 3);              /* and fixed again: an older rename follows the newest */
seen = JSON.parse(RAW[SEEN_KEY]);
OUT.v2 = verdict(F).state; OUT.rec2 = seen['shot_monarch.jpg'];
RAW[SEEN_KEY] = '{not json';
OUT.unreadable = _intakeSeenRename('Monarch (3os)', 'Monarch (5os)'); OUT.raw = RAW[SEEN_KEY];
SAID.length = 0;
window.vaultFixSockets('Monarch (3os)', 5);             /* his fix while the ledger will not parse */
OUT.fixSaid = SAID.slice(); OUT.raw2 = RAW[SEEN_KEY]; OUT.fixed = owned.has('Monarch (5os)');
""")
        self.assertEqual(got["v"], "seen", "his socket-count fix reads as a loss: the frame is '%s' (gone %r) and a re-read "
                                           "puts the misread label back beside the fixed one" % (got["v"], got["gone"]))
        self.assertEqual(got["rec"]["held"], ["Monarch (4os)", "Shako"], "the record does not hold the renamed item")
        self.assertEqual(got["rec"]["as"], {"Monarch (Larzuk base)": "Monarch (4os)"}, "the record forgot what the frame read")
        self.assertEqual(got["other"]["held"], ["Grief"], "a record that never held the old label was rewritten")
        self.assertNotIn("as", got["other"])
        self.assertEqual(got["prev"], {"Monarch (4os)": 1, "Shako": 1, "Monarch (Larzuk base)": "Monarch (4os)"})
        self.assertEqual(got["v2"], "seen")
        self.assertEqual(got["rec2"]["held"], ["Monarch (3os)", "Shako"])
        self.assertEqual(got["rec2"]["as"], {"Monarch (Larzuk base)": "Monarch (3os)", "Monarch (4os)": "Monarch (3os)"})
        self.assertEqual(got["unreadable"]["renamed"], 0)
        self.assertIn("would not parse", got["unreadable"]["unknown"], "an unreadable ledger was not SAID")
        self.assertEqual(got["raw"], "{not json", "an unreadable scan ledger was written over")
        self.assertTrue(got["fixed"], "an unreadable scan ledger stopped his socket fix")
        self.assertEqual(got["raw2"], "{not json", "his socket fix wrote over an unreadable scan ledger")
        self.assertTrue(any("would not parse" in m and "offered to read again" in m for m in got["fixSaid"]),
                        "the scan ledger's refusal of his rename was not said: %r" % got["fixSaid"])

    def test_the_magic_and_rare_toss_takes_the_owned_name_on_record_and_undoes_whole(self):
        got = _doors(r"""
var F = { name: 'f_1790549355102.jpg', lastModified: 1 };
readFrame(F, ['Death Loop']); magicFinds['Death Loop'] = { q: 'rare', base: 'Ring', mods: ['+1 to All Skills'] };
later();
window.vaultThrowFind('Death Loop');                     /* his ✕ on the MAGIC & RARE row */
OUT.owned = owned.has('Death Loop'); OUT.magic = Object.prototype.hasOwnProperty.call(magicFinds, 'Death Loop');
OUT.v = verdict(F).state;
OUT.batch = journal().map(function(b){ return { lane: b.lane, names: b.names, magic: b.magic || null }; });
OUT.stored = JSON.parse(RAW['d2r_owned']);
OUT.undo = window.vaultRestoreLast();
OUT.backOwned = owned.has('Death Loop'); OUT.backMagic = magicFinds['Death Loop'] || null;
""")
        self.assertFalse(got["owned"], "the ✕ left the keeper's name in owned - the doctor keeps it for ever")
        self.assertFalse(got["magic"])
        self.assertNotIn("Death Loop", got["stored"])
        self.assertEqual(got["v"], "removed", "the toss is not on record: the frame reads '%s'" % got["v"])
        self.assertEqual(len(got["batch"]), 1, "the toss did not go through the removal door")
        self.assertEqual((got["batch"][0]["lane"], got["batch"][0]["names"]), ("card-click", ["Death Loop"]))
        self.assertEqual(got["batch"][0]["magic"], {"Death Loop": {"q": "rare", "base": "Ring", "mods": ["+1 to All Skills"]}},
                         "the batch does not carry the Magic & Rare record - an undo would come back half")
        self.assertEqual(got["undo"]["restored"], 1)
        self.assertTrue(got["backOwned"])
        self.assertEqual(got["backMagic"], {"q": "rare", "base": "Ring", "mods": ["+1 to All Skills"]},
                         "the undo brought the name back without its Magic & Rare record")

    def test_a_keeper_magic_and_rare_held_alone_is_noted_when_he_tosses_it(self):
        got = _doors(r"""
var F = { name: 'shot_charm.jpg', lastModified: 1 };
magicFinds['Sullied Grand Charm of Blight'] = { q: 'magic', base: 'Grand Charm' };
var seen = {}; _intakeSeenMark(seen, F, { nw: [], own: [], unr: [], mf: ['Sullied Grand Charm of Blight'], err: false }, _intakeSeenAsk());
RAW[SEEN_KEY] = JSON.stringify(seen);
OUT.before = verdict(F).state;
later();
window.vaultThrowFind('Sullied Grand Charm of Blight');
OUT.v = verdict(F).state; OUT.batches = journal().length;
OUT.noted = (JSON.parse(RAW['d2r_vaultRemovedAt'] || '{}')['sullied grand charm of blight'] || {}).lane || null;
""")
        self.assertEqual(got["before"], "seen")
        self.assertEqual(got["v"], "removed", "a toss of a Magic & Rare keeper is not on record: the frame reads '%s'"
                         % got["v"])
        self.assertEqual(got["batches"], 0, "a name owned never held got a ring batch (its undo would own it)")
        self.assertEqual(got["noted"], "card-click")

    def test_the_planner_only_takes_back_its_own_fresh_add(self):
        got = _doors(r"""
var F = { name: 'shot_grief.jpg', lastModified: 1 };
readFrame(F, ['Grief']);
_vpMade = { token: 't1', id: 'grief', name: 'Grief', fresh: false, magic: false };   /* a pick over what he already had */
_vpDrop();
OUT.kept = owned.has('Grief'); OUT.v = verdict(F).state;
owned.add('Spirit'); _vpMade = { token: 't2', id: 'spirit', name: 'Spirit', fresh: true, magic: false };   /* its own add */
_vpDrop();
OUT.tookOwn = !owned.has('Spirit'); OUT.vAfter = verdict(F).state;
""")
        self.assertTrue(got["kept"], "the planner took back an item he already had")
        self.assertEqual(got["v"], "seen")
        self.assertTrue(got["tookOwn"], "PREMISE: the planner takes back the add its own pick made")
        self.assertEqual(got["vAfter"], "seen", "taking back the planner's own add touched a frame's item")

    def test_a_tossed_keeper_is_gone_after_a_reload_and_never_kept(self):
        got = _reload(r"""
RAW['d2r_owned'] = JSON.stringify(['Harlequin Crest', 'Death Loop']);
RAW['d2r_magicFinds'] = JSON.stringify({ 'Death Loop': { q: 'rare', base: 'Ring', mods: [] } });
pageLoad();
OUT.load1 = Array.from(owned);
window.vaultThrowFind('Death Loop');
pageLoad();
OUT.load2 = Array.from(owned); OUT.stored = JSON.parse(RAW['d2r_owned']);
OUT.kept = (window._ownedLoadReceipt || {}).kept || null;
window._vaultOwnedKeptPaint(); OUT.panelHidden = SLOT.hidden; OUT.panel = SLOT.innerHTML;
""")
        self.assertIn("Death Loop", got["load1"], "PREMISE: the keeper is owned before the toss")
        self.assertNotIn("Death Loop", got["load2"], "the tossed keeper came back on the reload")
        self.assertNotIn("Death Loop", got["stored"])
        self.assertEqual(got["kept"], [], "the doctor names a tossed keeper as an item he owns: %r" % got["kept"])
        self.assertTrue(got["panelHidden"], "the Vault says he owns what he threw out: %r" % got["panel"])


RED_PROOF = [
    {"why": "REG-2405 - his non-grail un-tick deletes straight out of owned again, with no removal on record",
     "file": "bible.html",
     "find": ("      try { if (typeof window.vaultRemove === 'function') _vrNG = window.vaultRemove([name], { lane: 'un-tick', "
              "quiet: true, keepFiling: true, why: 'un-ticked on its item card' }); } catch(e){ _vrNG = null; }\n"),
     "replace": "",
     "matches": 1},
    {"why": "REG-2405 - his socket-count fix never tells the scan ledger, so his rename reads as a loss",
     "file": "bible.html",
     "find": ("      try { if (typeof window._intakeSeenRename === 'function') _rnS = window._intakeSeenRename(name, newLabel); } "
              "catch(e){ _rnS = { unknown: 'the scan ledger could not take the rename' }; }\n"),
     "replace": "",
     "matches": 1},
    {"why": "REG-2405 - a rename the scan ledger refused is not said (a silent refusal)",
     "file": "bible.html",
     "find": ("             + ((_rnS && _rnS.unknown) ? ' · ' + _rnS.unknown + ' — a screenshot that read the old label may be "
              "offered to read again' : ''));\n"),
     "replace": "             + '');\n",
     "matches": 1},
    {"why": "REG-2405 - the rename keeps the old label in the record's held list",
     "file": "bible.html",
     "find": "        v.held = nh;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2405 - a scan ledger that will not parse is written over by the rename",
     "file": "bible.html",
     "find": "      return { renamed: 0, unknown: 'the scan ledger would not parse - nothing was written over it' };\n",
     "replace": "      { window.LSR.setItem(SEEN_KEY, '{}'); return { renamed: 0 }; }\n",
     "matches": 1},
    {"why": "REG-2404 - the Magic & Rare toss never goes through the removal door (no batch, no undo)",
     "file": "bible.html",
     "find": "owned.has(nm) && typeof window.vaultRemove === 'function'){\n",
     "replace": "false){\n",
     "matches": 1},
    {"why": "REG-2404 - the toss's batch does not carry the Magic & Rare record, so the undo comes back half",
     "file": "bible.html",
     "find": "      if (opts.magic && typeof opts.magic === 'object' && !Array.isArray(opts.magic)) batch.magic = opts.magic;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2404 - the undo does not put the Magic & Rare record back",
     "file": "bible.html",
     "find": "                && !Object.prototype.hasOwnProperty.call(magicFinds, nm)) magicFinds[nm] = last.magic[nm]; } catch(eMg){}\n",
     "replace": "                && false) magicFinds[nm] = last.magic[nm]; } catch(eMg){}\n",
     "matches": 1},
    {"why": "REG-2404 - a keeper Magic & Rare held alone is tossed with nothing on record",
     "file": "bible.html",
     "find": ("              window._vaultRemovalNote({ ts: Date.now(), names: [nm], lane: 'card-click', why: 'thrown out of "
              "Magic & Rare' }); } catch(e){}\n"),
     "replace": "              null; } catch(e){}\n",
     "matches": 1},
    {"why": "REG-2404 - the toss deletes the Magic & Rare record only and leaves the owned name (the doctor keeps it)",
     "file": "bible.html",
     "find": "    var nm = String(name == null ? '' : name), rec = null, r = null;\n",
     "replace": "    var nm = '', rec = null, r = null; try { delete magicFinds[name]; } catch(e){}\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
