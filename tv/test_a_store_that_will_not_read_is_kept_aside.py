# -*- coding: utf-8 -*-
"""#152 items 2-3 (REG-2410) — A SAVED STORE THAT WILL NOT READ IS NAMED, KEPT ASIDE AND NEVER WRITTEN OVER.

GrokBot's sweep (#230, 10-21, cov*.py), retested unchanged on v3784: d2r_owned saved as {"a":1} made the boot line
`let owned = new Set(...)` throw "object is not iterable", so `owned`, `multiKeep` and every name declared after it never
existed - "owned is not defined", the whole Vault dead on every reload. A store that would not PARSE fared no better the
quiet way: _safeJsonParse handed back the default, and the next persist() wrote that default over his bytes.

THE FIX, driven here on the SHIPPED code (window.LSR, ⟦STORE READ⟧, ⟦STORE NOTICE⟧, every boot loader, persist(),
_applyProgress), cut from bible.html by its own anchors and run in node over a stand-in localStorage:
  · every boot loader of a store persist() writes back reads through _storeRead(key, shape): absent is a fresh store,
    a parse failure or the wrong container shape goes to the door's quarantine, and the page runs on the default;
  · the door (window.LSR) copies the exact bytes to <world>d2r_quarantine~<key>~<hash>, reads them back, and from
    then on refuses every write AND remove of that key, whoever calls it - persist() still writes the other stores;
  · release() lets go only while the bytes are kept aside (or no longer in the key), and HIS restore and "Start it
    fresh" are the two doors that ask for it;
  · the notice says each held store on the board in plain words: which store, why, where its bytes are kept, and the
    way out. [[unknown-stays-unknown]] [[heart-first]]
RED_PROOF below; prove with `HEART2_PROVE_WORKERS=1 python3 tv/heart2.py --prove test_a_store_that_will_not_read_is_kept_aside`.
"""
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

import store_door_harness as D  # noqa: E402

BAD = {
    "d2r_owned": '{"a":1}',            # GrokBot's repro: parses, wrong shape - `new Set` threw
    "d2r_wishlist": "GARBAGE {{{",      # will not parse
    "d2r_setPieces": '"text"',          # a string: `new Set("text")` would have read t, e, x
    "d2r_copies": "[1,2]",              # a list where a map belongs: JSON.stringify would drop every key set on it
    "d2r_runeStash": '{"Ber":2}',       # healthy
    "d2r_rwMade": "null",               # the null this page writes for "not seeded yet": absent, never quarantined
}


def _boot(body, seed=None, **kw):
    s = D.src()
    return D.page(D.stage(s) + D.boot(s), body, seed=BAD if seed is None else seed, **kw)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED store door; UNMEASURED, not passing")
class AStoreThatWillNotReadIsKeptAside(unittest.TestCase):

    def test_the_shapes_that_bricked_the_page_no_longer_throw(self):
        o = _boot("OUT.owned = owned.size; OUT.wish = wishlist.size; OUT.sp = setPieces.size; OUT.copies = copies;"
                  "OUT.runes = runeStash; OUT.rwMade = rwMade;"
                  "OUT.q = window.LSR.quarantined().map(function(e){ return [e.key, e.reason, e.kind]; });")
        self.assertEqual((o["owned"], o["wish"], o["sp"], o["copies"]), (0, 0, 0, {}),
                         "a quarantined store must run on its empty default in memory: %r" % o)
        self.assertEqual(o["runes"], {"Ber": 2}, "a healthy store beside them must read as it is")
        self.assertIsNone(o["rwMade"], "the null this page writes for 'not seeded yet' is absent, not a quarantine")
        got = {k: why for k, why, _kind in o["q"]}
        self.assertEqual(set(got), {"d2r_owned", "d2r_wishlist", "d2r_setPieces", "d2r_copies"}, o["q"])
        self.assertEqual(got["d2r_owned"], "is not a list (it holds a map)")
        self.assertEqual(got["d2r_wishlist"], "will not parse")
        self.assertEqual(got["d2r_setPieces"], "is not a list (it holds text)")
        self.assertEqual(got["d2r_copies"], "is not a map (it holds a list)")

    def test_kept_aside_byte_for_byte_and_never_written_over(self):
        o = _boot("owned.add('Harlequin Crest (Shako)'); wishlist.add('Grief'); runeStash.Jah = 1; copies.Grief = 2;"
                  "persist();"
                  "OUT.raw = { owned: RAW['d2r_owned'], wish: RAW['d2r_wishlist'], sp: RAW['d2r_setPieces'],"
                  "            copies: RAW['d2r_copies'], runes: RAW['d2r_runeStash'] };"
                  "OUT.aside = aside();"
                  "OUT.set = window.LSR.setItem('d2r_owned', '[]'); OUT.rm = window.LSR.removeItem('d2r_owned');"
                  "OUT.after = RAW['d2r_owned'];"
                  "OUT.refused = window.LSR.quarantined('d2r_owned').refused;"
                  "OUT.slot = window.LSR.quarantined('d2r_owned').aside;")
        for k, key in (("owned", "d2r_owned"), ("wish", "d2r_wishlist"), ("sp", "d2r_setPieces"), ("copies", "d2r_copies")):
            self.assertEqual(o["raw"][k], BAD[key], "persist() wrote over the quarantined %s: %r" % (key, o["raw"]))
        self.assertEqual(json.loads(o["raw"]["runes"]), {"Ber": 2, "Jah": 1},
                         "persist() must still write the stores that DO read (one held store is not all of them)")
        self.assertEqual(sorted(o["aside"].values()), sorted(BAD[k] for k in ("d2r_owned", "d2r_wishlist",
                                                                              "d2r_setPieces", "d2r_copies")),
                         "every quarantined store must be kept aside byte for byte: %r" % o["aside"])
        self.assertTrue(o["slot"].startswith("d2r_quarantine~d2r_owned~"), o["slot"])
        self.assertFalse(o["set"], "a refused write must answer false, so a caller can tell it was not written")
        self.assertFalse(o["rm"], "a remove of a quarantined store must be refused too")
        self.assertEqual(o["after"], BAD["d2r_owned"])
        self.assertGreaterEqual(o["refused"], 3, "persist(), the write and the remove were all refused")

    def test_the_same_bytes_are_not_written_again(self):
        o = D.page(
            D.stage(D.src()),
            r"""
var writes = 0;
var _set = localStorage.setItem;
localStorage.setItem = function(k, v){ if (k === 'd2r_runeStash') writes++; return _set(k, v); };
var same = window.LSR.setItem('d2r_runeStash', '{"Ber":1}');
var again = window.LSR.setItem('d2r_runeStash', '{"Ber":1}');
var changed = window.LSR.setItem('d2r_runeStash', '{"Ber":2}');
window.LSR.quarantine('d2r_wishlist', 'will not parse');
var refused = window.LSR.setItem('d2r_wishlist', 'GARBAGE {{{');
OUT.writes = writes;
OUT.same = same; OUT.again = again; OUT.changed = changed !== false;
OUT.stored = localStorage.getItem('d2r_runeStash');
OUT.refused = refused;
OUT.held = localStorage.getItem('d2r_wishlist');
""",
            seed={"d2r_runeStash": '{"Ber":1}', "d2r_wishlist": "GARBAGE {{{"})
        self.assertEqual(o["writes"], 1, o)
        self.assertTrue(o["same"], o)
        self.assertTrue(o["again"], o)
        self.assertTrue(o["changed"], o)
        self.assertEqual(o["stored"], '{"Ber":2}')
        self.assertFalse(o["refused"], o)
        self.assertEqual(o["held"], "GARBAGE {{{")

    def test_absent_empty_and_healthy_stores_are_not_quarantined(self):
        o = _boot("OUT.q = window.LSR.quarantined().length; OUT.owned = Array.from(owned); OUT.wish = wishlist.size;"
                  "OUT.mk = Object.keys(multiKeep).length > 0;",
                  seed={"d2r_owned": '["Grief"]', "d2r_wishlist": "", "d2r_multiKeep": "null"})
        self.assertEqual(o["q"], 0, "an absent, empty or healthy store must never be quarantined")
        self.assertEqual(o["owned"], ["Grief"])
        self.assertTrue(o["mk"], "a null multiKeep still falls back to the default targets")

    def test_release_only_while_the_bytes_are_kept_aside(self):
        o = _boot("OUT.fresh = window.LSR.release('d2r_wishlist');"
                  "window.LSR.setItem('d2r_wishlist', '[]'); OUT.write = RAW['d2r_wishlist'];"
                  "OUT.kept = aside();",
                  seed={"d2r_wishlist": "GARBAGE {{{"})
        self.assertTrue(o["fresh"]["ok"] and o["fresh"]["released"], o)
        self.assertEqual(o["write"], "[]", "a released store takes writes again")
        self.assertEqual(list(o["kept"].values()), ["GARBAGE {{{"], "the bytes stay kept aside after a release")
        # the aside copy cannot be written (no room): the bytes stay in the key, and release refuses
        s = D.src()
        o = D.page(D.stage(s) + "THROW_ON = /d2r_quarantine~/;\n" + D.boot(s),
                   "OUT.q = window.LSR.quarantined('d2r_owned');"
                   "OUT.rel = window.LSR.release('d2r_owned');"
                   "OUT.still = RAW['d2r_owned'];"
                   "RAW['d2r_owned'] = '[\"X\"]';"
                   "OUT.rel2 = window.LSR.release('d2r_owned');",
                   seed={"d2r_owned": "{bad"})
        self.assertFalse(o["q"]["asideOk"], o["q"])
        self.assertFalse(o["rel"]["ok"], "a store whose bytes are not kept aside must not be let go: %r" % o["rel"])
        self.assertEqual(o["still"], "{bad")
        self.assertTrue(o["rel2"]["ok"], "once the bad bytes are no longer in the key there is nothing to lose")

    def test_a_forked_world_keeps_its_bytes_in_its_own_world(self):
        o = _boot("OUT.q = window.LSR.quarantined('d2r_owned'); OUT.raw = Object.keys(RAW).sort();",
                  seed={"L·d2r_owned": '{"a":1}', "d2r_owned": '["Grief"]'}, profile="ladder")
        self.assertEqual(o["q"]["phys"], "L·d2r_owned")
        self.assertTrue(o["q"]["aside"].startswith("L·d2r_quarantine~d2r_owned~"),
                        "a ladder store's bytes must be kept aside in the ladder world: %r" % o["q"]["aside"])
        self.assertEqual([k for k in o["raw"] if "d2r_quarantine~" in k and not k.startswith("L·")], [],
                         "nothing may be kept aside in another world: %r" % o["raw"])

    def test_the_notice_names_each_store_and_its_way_out(self):
        o = _boot("var el = document.getElementById('store-quarantine');"
                  "OUT.shown = !!el && !el.hidden; OUT.role = el && el.getAttribute('role'); OUT.html = el ? el.innerHTML : '';"
                  "window.LSR.hold('d2r_magicFinds', 'another tab changed it');"
                  "OUT.stale = document.getElementById('store-quarantine').innerHTML;")
        self.assertTrue(o["shown"], "a quarantined store must be said on the board")
        self.assertEqual(o["role"], "alert")
        h = o["html"]
        for key, why in (("d2r_owned", "is not a list (it holds a map)"), ("d2r_wishlist", "will not parse")):
            self.assertIn("<b>%s</b>" % key, h)
            self.assertIn(why, h)
        self.assertIn("what you own", h, "the store is named in his words, not only its key")
        self.assertIn("d2r_quarantine~d2r_owned~", h, "the notice says where the bytes are kept")
        self.assertIn("window._storeStartFresh('d2r_owned')", h, "a store kept aside offers Start it fresh")
        self.assertIn("Backup &amp; Share", h, "the notice names the restore way out")
        self.assertIn("Reload this tab", o["stale"], "a store held behind another tab asks for a reload")
        o = _boot("window._storeQuarantinePaint(); OUT.el = document.getElementById('store-quarantine');",
                  seed={"d2r_owned": '["Grief"]'})
        self.assertIsNone(o["el"], "a clean board shows no notice")

    def test_start_it_fresh_keeps_the_bytes_aside(self):
        o = _boot("window.__ASYNC = true; window._storeStartFresh('d2r_owned', true).then(function(r){"
                  "  OUT.r = r; OUT.key = RAW['d2r_owned'] || null; OUT.kept = aside();"
                  "  OUT.held = !!window.LSR.quarantined('d2r_owned'); done(); });")
        self.assertTrue(o["r"]["ok"], o)
        self.assertIsNone(o["key"], "starting a store fresh empties its key")
        self.assertFalse(o["held"])
        self.assertIn('{"a":1}', o["kept"].values(), "the old bytes stay kept aside")

    def test_a_fresh_roster_waits_for_the_mule_map(self):
        """A fresh roster keeps every mule the map names - it cannot, while the map itself would not read."""
        both = _boot("window.LSR.quarantine('d2r_muleRoster', 'is not a list of mules');"
                     "window.LSR.quarantine('d2r_muleAssign', 'will not parse');"
                     "window._vaultRosterFresh = function(){ return [{ id: 'uni-armor' }]; }; window.__ASYNC = true;"
                     "window._storeStartFresh('d2r_muleRoster', true).then(function(r){ OUT.r = r;"
                     "  OUT.raw = RAW['d2r_muleRoster']; OUT.held = !!window.LSR.quarantined('d2r_muleRoster'); done(); });",
                     seed={"d2r_muleRoster": "{}", "d2r_muleAssign": "{bad"})
        self.assertFalse(both["r"]["ok"])
        self.assertIn("d2r_muleAssign is quarantined too", both["r"]["why"])
        self.assertEqual((both["raw"], both["held"]), ("{}", True), "the roster must stay as it is, held")
        alone = _boot("window.LSR.quarantine('d2r_muleRoster', 'is not a list of mules');"
                      "window._vaultRosterFresh = function(){ return [{ id: 'uni-armor' }]; }; window.__ASYNC = true;"
                      "window._storeStartFresh('d2r_muleRoster', true).then(function(r){ OUT.r = r;"
                      "  OUT.raw = RAW['d2r_muleRoster']; done(); });",
                      seed={"d2r_muleRoster": "{}", "d2r_muleAssign": '{"Grief":"uni-armor"}'})
        self.assertTrue(alone["r"]["ok"], alone)
        self.assertEqual(alone["raw"], '[{"id":"uni-armor"}]', "PREMISE: a roster alone starts fresh with the kept mules")

    def test_every_store_persist_writes_back_is_read_by_shape(self):
        s = D.src()
        persist = D.between(s, "const persist = () => {", "\n};")
        written = set(re.findall(r"LS\.setItem\('(d2r_\w+)', JSON\.stringify\(", persist))
        self.assertGreaterEqual(len(written), 15, "PREMISE: persist()'s JSON stores were not found")
        read = {k for _n, k, _l in D.loaders(s)}
        self.assertEqual(sorted(written - read), [],
                         "a store persist() writes back whole is still read without its shape - one bad value "
                         "there throws or is written over: %s" % sorted(written - read))
        blind = re.findall(r"^let \w+ = .*_safeJsonParse\(LS\.getItem\('(d2r_\w+)'\)", s, re.M)
        self.assertEqual(sorted(set(blind) & written), [],
                         "a boot loader still reads a store persist() writes back with the shape-blind parse")

    def test_a_restore_lets_go_only_what_is_kept_aside(self):
        s = D.src()
        restore = D.fn(s, "_applyProgress")
        pieces = (D.stage(s) + "THROW_ON = /d2r_quarantine~d2r_wishlist/;\n" + D.boot(s)
                  + "var STATUS = []; function _backupStatus(m, k){ STATUS.push([m, k]); }"
                  + " var uiConfirm = function(){ return Promise.resolve(true); };"
                  + " var location = { reload: function(){} };\n" + restore + "\n")
        o = D.page(pieces,
                   "window.__ASYNC = true;"
                   "_applyProgress(JSON.stringify({ data: { d2r_owned: '[\"Shako\"]', d2r_wishlist: '[\"Grief\"]',"
                   " d2r_runeStash: '{\"Ber\":1}' } })).then(function(){"
                   "  OUT.raw = { owned: RAW['d2r_owned'], wish: RAW['d2r_wishlist'], runes: RAW['d2r_runeStash'] };"
                   "  OUT.kept = aside(); OUT.status = STATUS;"
                   "  OUT.held = window.LSR.quarantined().map(function(e){ return e.key; }); done(); });",
                   seed={"d2r_owned": '{"a":1}', "d2r_wishlist": "GARBAGE {{{"})
        self.assertEqual(o["raw"]["owned"], '["Shako"]', "HIS restore is the way out of a quarantine kept aside")
        self.assertEqual(o["raw"]["runes"], '{"Ber":1}')
        self.assertIn('{"a":1}', o["kept"].values(), "the quarantined bytes stay kept aside after the restore")
        self.assertEqual(o["raw"]["wish"], "GARBAGE {{{",
                         "a store whose bytes could not be kept aside must not be written over, even by a restore")
        self.assertEqual(o["held"], ["d2r_wishlist"])
        self.assertIn("d2r_wishlist stayed quarantined", o["status"][-1][0], "the status names the store it kept")


RED_PROOF = [
    {"why": "REG-2410 - the door writes over a quarantined store again (persist() put the empty default over his bytes)",
     "file": "bible.html", "matches": 1,
     "find": "      if (_QUAR[k]) return _qRefuse(String(k), 'write');\n",
     "replace": ""},
    {"why": "REG-2410 - a quarantined store's remove is no longer refused",
     "file": "bible.html", "matches": 1,
     "find": "    removeItem: function(k){ if (window._tvdShadow) return; if (_QUAR[k]) return _qRefuse(String(k), 'remove'); return RAW.removeItem(key(k)); },",
     "replace": "    removeItem: function(k){ if (window._tvdShadow) return; return RAW.removeItem(key(k)); },"},
    {"why": "REG-2410 - the bytes are no longer copied aside (a later release would lose them)",
     "file": "bible.html", "matches": 1,
     "find": "        if (RAW.getItem(slot) !== raw) RAW.setItem(slot, raw);\n",
     "replace": ""},
    {"why": "REG-2410 - a list store of the wrong shape reaches `new Set(...)` again (d2r_owned {\"a\":1} bricked the page)",
     "file": "bible.html", "matches": 1,
     "find": "    if (shape === 'list') return Array.isArray(v) ? null : 'is not a list (it holds ' + _qWhat(v) + ')';\n",
     "replace": "    if (shape === 'list') return null;\n"},
    {"why": "REG-2410 - d2r_owned is read by the shape-blind parse again",
     "file": "bible.html", "matches": 1,
     "find": "let owned = new Set(_storeRead('list', []).getItem('d2r_owned'));",
     "replace": "let owned = new Set(_safeJsonParse(LS.getItem('d2r_owned'), []));"},
    {"why": "REG-2410 - release lets go of bytes that are not kept aside",
     "file": "bible.html", "matches": 1,
     "find": "      if (again != null && (ent.hash == null || _qHash(String(again)) === ent.hash))\n",
     "replace": "      if (false)\n"},
    {"why": "REG-2410 - the notice is never shown (a held store is silent on the board)",
     "file": "bible.html", "matches": 1,
     "find": "    el.innerHTML = window._storeQuarantineHtml(list);\n    el.hidden = false;\n",
     "replace": "    el.hidden = true;\n"},
    {"why": "REG-2410 - the roster starts fresh while the mule map is quarantined too (a later restore of the map loses filings)",
     "file": "bible.html", "matches": 1,
     "find": "  if (k === 'd2r_muleRoster' && window.LSR.quarantined('d2r_muleAssign'))\n",
     "replace": "  if (false)\n"},
    {"why": "REG-2410 - his restore no longer lets go of a quarantine (the snapshot cannot land)",
     "file": "bible.html", "matches": 1,
     "find": "        const _rl = window.LSR.release(k);\n        if (!_rl || !_rl.ok) { _keptHeld.push(k); return; }\n",
     "replace": "        _keptHeld.push(k); return;\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
