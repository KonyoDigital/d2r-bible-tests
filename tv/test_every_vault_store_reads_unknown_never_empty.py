# -*- coding: utf-8 -*-
"""REG-2520 (V1 round 3; #162, #152) - EVERY VAULT STORE IS READ BY ONE RULE: BYTES THAT WILL NOT READ ARE UNKNOWN, NEVER EMPTY.

Round 2's reviews found the REG-2410 defect alive in the stores the vault reads on demand, each through its own
`JSON.parse(raw || '[]')` with `catch -> []`:
  * d2r_intakeSeen (the scan ledger): cut short it read as {} - every screenshot he ever read became 'fresh', the poll
    handed old ones back to the AI 12 at a time, and the next mark wrote bare marks over every record (what each file
    read, lost). Reviewer: pollRead=[old_1,old_2,old_3,new_1], the ledger became {"old_1.jpg":1,...};
  * d2r_vaultRemoved (the removal journal): read as [] and the next removal - every un-tick and every Magic & Rare ✕
    since REG-2404/2405 - wrote [its one batch] over every batch, his undo history with it;
  * d2r_intakeLog (the Recently-registered log): read as [] and journalAdd wrote [this session] over the rest;
and the boot prune read the mule map through _safeJsonParse, so a map cut short was not even quarantined (rv1).

THE ONE RULE (⟦ONE STORE READER⟧, window.LSR.read(k, shape, absent)): nothing saved yet is the caller's empty container
(a measured nothing); bytes that parse to the shape are the value; bytes that will not parse, or of the wrong shape, are
UNKNOWN (null) and the key is QUARANTINED at the door - its bytes kept aside, every write and remove refused, the notice
says which store and why, and the vault is HELD (VAULT_STORES). The boot loaders (_storeRead), the vault module's
roster / mule map load, the scan ledger (seenLedger), the removal journal (_vrRead) and its per-name record (_rmRead),
the Recently-registered log (journal) and the boot prune's read of the mule map all ask it; the module reads the
on-demand stores once as it loads, so a bad store is quarantined before any door is asked.

WHAT THIS LAW HOLDS - the store door, the boot, the notice, the tab sync and the vault module's head and filing block
(tv/store_door_harness.py vault_page), plus the SHIPPED readers cut from bible.html, in node:
  * each of the four on-demand stores, cut short and of the wrong shape: quarantined as the module loads (before any
    reader is asked), its exact bytes kept aside, its reader answers null, the one reader answers null, a write is
    refused and the bytes stay, the notice names it in his words, the vault hold names it, and journalAdd says UNKNOWN;
  * nothing saved, and a store that reads: the reader answers the empty container / the value and nothing is held;
  * the boot prune's read of a mule map cut short quarantines it at that first read, and every owned name stays.
RED_PROOF below. A missing node is the only skip; a node that fails is a failure.
"""
import json
import os
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

import store_door_harness as D  # noqa: E402

#: each on-demand store: its reader (as the law calls it), the one reader's shape, bytes cut short, a wrong shape, a good value
STORES = {
    "d2r_intakeSeen": ("window.__R.seen()", "map",
                       '{"old_1.jpg":{"held":["Shako"],"unr":[],"at":10,"world":"main"},"old_2.jpg":{"he',
                       '["old_1.jpg"]', '{"old_1.jpg":{"held":["Shako"],"unr":[],"at":10,"world":"main"}}'),
    "d2r_vaultRemoved": ("window.__R.vrRead()", "list",
                         '[{"ts":1760000000000,"lane":"hand","names":["Shako"]},{"ts":1760000100000,"lane":"hand","names":["Eni',
                         '{"ts":1}', '[{"ts":1760000000000,"lane":"hand","names":["Shako"],"filed":{}}]'),
    "d2r_vaultRemovedAt": ("window.__R.rmRead('d2r_vaultRemovedAt', 'map', {})", "map",
                           '{"shako":{"at":1760000000000,"lane":"hand"},"enig',
                           '[1,2]', '{"shako":{"at":1760000000000,"lane":"hand"}}'),
    "d2r_intakeLog": ("window.__R.journal()", "list",
                      '[{"ts":1760000000000,"u":"Konyo","items":["Shako"],"pf":[{"f":"a","nw":["Sha',
                      '{"ts":1}', '[{"ts":1760000000000,"u":"Konyo","items":["Shako"],"pf":[]}]'),
}
SAY = {"d2r_intakeSeen": "the scan ledger", "d2r_vaultRemoved": "the removal journal",
       "d2r_vaultRemovedAt": "the per-item record of what you removed", "d2r_intakeLog": "the Recently-registered log"}
BASE = {"d2r_owned": '["Grief","Harlequin Crest (Shako)"]', "d2r_muleAssign": '{"Grief":"uni-weap"}'}


def _readers(s):
    """the SHIPPED readers of the on-demand stores, cut whole, run in the vault module's scope"""
    return ("var _VR_LOG = 'd2r_vaultRemoved', _VR_RING = 20;\n"
            + D.between(s, "  function _vrRead(){", "  /* the heart and the console read the journal through here", keep_b=False)
            + "var SEEN_KEY = 'd2r_intakeSeen';\n" + D.between(s, "  function seenLedger(){", "\n")
            + "var JOURNAL_KEY='d2r_intakeLog';\n" + D.fn(s, "journal") + "\n" + D.fn(s, "_journalUnknownSay") + "\n"
            + D.fn(s, "journalAdd") + "\n"
            + "window.__R = { seen: seenLedger, vrRead: _vrRead, journal: journal, journalAdd: journalAdd };\n")


def _backfill_readers(s):
    """_rmRead (the journal's per-name record reader) and the _bfJson door it falls back to, as the main script declares them"""
    return D.fn(s, "_rmRead") + "\n" + D.between(s, "  function _bfJson(k, dflt){", "catch (e) { return undefined; } }\n") + \
        "\nwindow.__R.rmRead = _rmRead;\n"


def _run(body, seed):
    s = D.src()
    pieces = D.vault_page(s, _readers(s)) + _backfill_readers(s)
    return D.page(pieces, body, seed=seed)


PROBE = r"""
var K = %(key)s;
var q0 = window.LSR.quarantined(K);                                /* BEFORE any reader is asked */
OUT.qAtLoad = q0 ? { kind: q0.kind, reason: q0.reason, asideOk: q0.asideOk, aside: q0.aside ? RAW[q0.aside] : null } : null;
OUT.reader = %(reader)s;
OUT.oneReader = window.LSR.read(K, %(shape)s, 'ABSENT');
OUT.write = window.LSR.setItem(K, '[]');
OUT.raw = Object.prototype.hasOwnProperty.call(RAW, K) ? RAW[K] : null;
var h = window._vaultHeld(); OUT.held = h ? h.keys : null;
OUT.notice = (document.getElementById('store-quarantine') || {}).innerHTML || '';
OUT.journalAdd = (K === 'd2r_intakeLog') ? window.__R.journalAdd(['Grief'], [{ file: 'shot.jpg', nw: ['Grief'] }]) : null;
OUT.rawAfterAdd = Object.prototype.hasOwnProperty.call(RAW, K) ? RAW[K] : null;
"""


def _probe(key, raw):
    reader, shape = STORES[key][0], STORES[key][1]
    seed = dict(BASE)
    if raw is not None:
        seed[key] = raw
    return _run(PROBE % {"key": json.dumps(key), "reader": reader, "shape": json.dumps(shape)}, seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED readers; UNMEASURED, not passing")
class EveryVaultStoreReadsUnknownNeverEmpty(unittest.TestCase):

    def _assert_unknown(self, key, raw, label):
        o = _probe(key, raw)
        self.assertIsNotNone(o["qAtLoad"], "%s %s: not quarantined as the module loaded - the first to find it would be "
                                           "the write that goes over it" % (key, label))
        self.assertEqual(o["qAtLoad"]["kind"], "quarantine")
        self.assertTrue(o["qAtLoad"]["asideOk"], "%s %s: the bytes were not kept aside" % (key, label))
        self.assertEqual(o["qAtLoad"]["aside"], raw, "%s %s: the slot aside does not hold the exact bytes" % (key, label))
        self.assertIsNone(o["reader"], "%s %s: the shipped reader read UNKNOWN bytes as %r" % (key, label, o["reader"]))
        self.assertIsNone(o["oneReader"], "%s %s: the one reader answered %r" % (key, label, o["oneReader"]))
        self.assertFalse(o["write"], "%s %s: a write over the UNKNOWN store was let through" % (key, label))
        self.assertEqual(o["raw"], raw, "%s %s: the bytes were written over" % (key, label))
        self.assertIsNotNone(o["held"], "%s %s: the vault is not held" % (key, label))
        self.assertIn(key, o["held"], "%s %s: the hold does not name the store" % (key, label))
        self.assertIn('data-store="%s"' % key, o["notice"], "%s %s: not on the board" % (key, label))
        self.assertIn(SAY[key], o["notice"], "%s %s: the notice does not say what the store is" % (key, label))
        if key == "d2r_intakeLog":
            self.assertIs(o["journalAdd"], False, "journalAdd wrote over an UNKNOWN log, or did not say it could not")
            self.assertEqual(o["rawAfterAdd"], raw)
        return o

    def test_bytes_cut_short_are_unknown_kept_aside_held_and_said(self):
        for key in STORES:
            with self.subTest(store=key):
                self._assert_unknown(key, STORES[key][2], "cut short")

    def test_a_store_of_the_wrong_shape_is_unknown_too(self):
        for key in STORES:
            with self.subTest(store=key):
                self._assert_unknown(key, STORES[key][3], "of the wrong shape")

    def test_nothing_saved_reads_as_the_empty_container_and_a_good_store_reads(self):
        empty = {"map": {}, "list": []}
        for key in STORES:
            with self.subTest(store=key, saved="nothing"):
                o = _probe(key, None)
                self.assertIsNone(o["qAtLoad"], "%s: nothing saved was quarantined" % key)
                self.assertEqual(o["reader"], empty[STORES[key][1]], "%s: nothing saved did not read as a measured nothing" % key)
                self.assertEqual(o["oneReader"], "ABSENT")
                self.assertIsNone(o["held"], "%s: nothing saved held the vault" % key)
            with self.subTest(store=key, saved="good"):
                o = _probe(key, STORES[key][4])
                self.assertIsNone(o["qAtLoad"], "%s: a store that reads was quarantined" % key)
                self.assertEqual(o["reader"], json.loads(STORES[key][4]), "%s: a store that reads did not read" % key)
                self.assertIsNone(o["held"])

    def test_the_boot_prune_quarantines_a_mule_map_cut_short_at_its_first_read(self):
        s = D.src()
        norm = D.between(s, "function _norm(s){", "\n")
        safe = D.between(s, "const _safeJsonParse = (raw, fallback) => {", "\n};\n")
        rws = D.between(s, "const RUNEWORDS = [", "\n];\n")
        prune = D.between(s, "(function _v42_sanitizeWishlistOwned() {", "\n  // v659 — GRAIL FOUND-SEED floor", keep_b=False)
        pieces = D.stage(s) + "var LS = window.LSR;\n" + norm + "\n" + safe + "\n" + rws + r"""
var SUNDER_CHARMS = [], BASE_CLASS = {};
var ITEM_REGISTRY = { "Harlequin Crest": { n: "Harlequin Crest" } };
var _UNI_EXTRA = {}, _GRAIL_SEED = {}, _EXTRA_ITEM_SET = new Set();
window._gUniqueRoster = function(){ return ["Harlequin Crest"]; };
function findSetPiece(){ return null; }
var wishlist = new Set(), owned = new Set(JSON.parse(RAW['d2r_owned'])), magicFinds = {};
function persist(){ LS.setItem('d2r_owned', JSON.stringify(Array.from(owned))); }
""" + prune + "\n})();\n"
        cut = '{"Wraith Grasp":"magic-rare","Havoc Fin'
        o = D.page(pieces, "var q = window.LSR.quarantined('d2r_muleAssign');"
                           "OUT.q = q ? { reason: q.reason, aside: q.aside ? RAW[q.aside] : null } : null;"
                           "OUT.map = RAW['d2r_muleAssign']; OUT.owned = JSON.parse(RAW['d2r_owned']);",
                   seed={"d2r_owned": '["Wraith Grasp","Havoc Finger","Harlequin Crest"]', "d2r_muleAssign": cut})
        self.assertEqual(o["q"], {"reason": "will not parse", "aside": cut},
                         "the boot prune read a mule map cut short without quarantining it (read as {})")
        self.assertEqual(o["map"], cut, "the mule map's bytes were written over")
        self.assertEqual(sorted(o["owned"]), ["Harlequin Crest", "Havoc Finger", "Wraith Grasp"],
                         "the load dropped an owned name while the mule map would not read")


RED_PROOF = [
    {"why": "REG-2520 - the scan ledger reads bytes that will not parse as {} again (every screenshot 'fresh', marks "
            "written over every record)",
     "file": "bible.html", "matches": 1,
     "find": "  function seenLedger(){ var D = window.LSR; if (D && typeof D.read === 'function') return D.read(SEEN_KEY, 'map', {});",
     "replace": "  function seenLedger(){ try { return JSON.parse(window.LSR.getItem(SEEN_KEY)||'{}'); } catch(e){ return {}; } var D = window.LSR;"},
    {"why": "REG-2520 - the removal journal reads bytes that will not parse as [] again (the next removal writes over "
            "his undo history)",
     "file": "bible.html", "matches": 1,
     "find": "    if (D && typeof D.read === 'function') return D.read(_VR_LOG, 'list', []);\n",
     "replace": "    try { var _a0 = JSON.parse(D.getItem(_VR_LOG) || '[]'); return Array.isArray(_a0) ? _a0 : []; } catch(e0){ return []; }\n"},
    {"why": "REG-2520 - the Recently-registered log reads bytes that will not parse as [] again",
     "file": "bible.html", "matches": 1,
     "find": "    if (D && typeof D.read === 'function') return D.read(JOURNAL_KEY, 'list', []);\n",
     "replace": "    try { var _j0 = JSON.parse(D.getItem(JOURNAL_KEY) || '[]'); return Array.isArray(_j0) ? _j0 : []; } catch(e0){ return []; }\n"},
    {"why": "REG-2520 - the per-name removal record reads bytes that will not parse as {} again",
     "file": "bible.html", "matches": 1,
     "find": "  function _rmRead(k, shape, dflt){\n",
     "replace": "  function _rmRead(k, shape, dflt){\n    try { var _x = JSON.parse(window.LSR.getItem(k) || 'null'); return _x == null ? dflt : _x; } catch (eX) { return dflt; }\n"},
    {"why": "REG-2520 - the module no longer reads the on-demand stores as it loads (a bad store is first found by the "
            "write that goes over it)",
     "file": "bible.html", "matches": 1,
     "find": "    try { if (window.LSR && typeof window.LSR.read === 'function') window.LSR.read(k, VAULT_STORE_SHAPE[k], null); } catch (eVr) {}\n",
     "replace": ""},
    {"why": "REG-2520 - the one reader reads bytes that will not parse as the absent value",
     "file": "bible.html", "matches": 1,
     "find": "    try { v = JSON.parse(raw); } catch(eP){ quarantine(k, 'will not parse'); return null; }\n",
     "replace": "    try { v = JSON.parse(raw); } catch(eP){ return absent; }\n"},
    {"why": "REG-2520 - the one reader lets a store of the wrong shape through as the absent value",
     "file": "bible.html", "matches": 1,
     "find": "    if (why){ quarantine(k, why); return null; }\n",
     "replace": "    if (why){ return absent; }\n"},
    {"why": "REG-2520 - the vault hold does not cover the stores it reads on demand",
     "file": "bible.html", "matches": 1,
     "find": "  var VAULT_STORES = VAULT_BASIS.concat(Object.keys({ d2r_vaultRecords: 1, d2r_vaultRemoved: 1, d2r_vaultRemovedAt: 1,\n"
             "                                                       d2r_intakeSeen: 1, d2r_intakeLog: 1 }));\n",
     "replace": "  var VAULT_STORES = VAULT_BASIS.concat(Object.keys({ d2r_vaultRecords: 1 }));\n"},
    {"why": "REG-2520 - the notice names the scan ledger with no words he knows",
     "file": "bible.html", "matches": 1,
     "find": "  d2r_intakeSeen: 'the scan ledger - which screenshots were read, and what each read',\n",
     "replace": "  d2r_intakeSeenX: '',\n"},
    {"why": "REG-2520 - journalAdd writes this session over a log it could not read",
     "file": "bible.html", "matches": 1,
     "find": "    if (j === null) return false;   /* REG-2520 — UNKNOWN: nothing is written over it; the caller says so */\n",
     "replace": "    if (j === null) j = [];\n"},
    {"why": "REG-2520 (rv1) - the boot prune reads a mule map cut short as {} and never quarantines it",
     "file": "bible.html", "matches": 1,
     "find": "  var _maKeep = ((window.LSR && typeof window.LSR.read === 'function') ? window.LSR.read('d2r_muleAssign', 'map', {})\n",
     "replace": "  var _maKeep = ((false) ? null\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
