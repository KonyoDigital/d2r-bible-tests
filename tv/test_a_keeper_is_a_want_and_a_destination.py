# -*- coding: utf-8 -*-
"""REG-2900 (#149.2, GrokBot's GB-L Advanced-drawer pass, ACT 2) - A KEEPER IS {want, dest}, NOT A BARE NUMBER.

GrokBot's read-only audit: d2r_multiKeep was {name: wantCount}. A keeper could say how many copies he wants and never
where they go, and the router never read it. Each keeper is now {want, dest} (dest 'auto' | 'shared' | 'war' |
'mule:<id>'), and a store of plain numbers is migrated once, at load:

  * every number becomes {want, dest:'auto'} and the store is written back in the new shape; a keeper already
    {want, dest} keeps its dest;
  * a second load finds nothing to turn (idempotent);
  * a shadow never writes (read only), and a store that would not read is never written over (kept aside, the page
    runs on the default keepers);
  * every reader reads both shapes (a number still arrives from another tab on an older build, a backup, a seed);
  * a writer keeps the dest: a WANT step moves the want and nothing else;
  * the default keepers are fresh objects, never the live map's own (a writer that edited one in place would edit the
    defaults every later reset reads).

Driven on the whole page in node (vault_page_node), fixtures only. RED_PROOF below.
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

import vault_page_node as VPN  # noqa: E402

HC = "Harlequin Crest"


def _seed(mk):
    s = "localStorage.setItem('d2r_ownerClaim', '*');\n"
    if mk is not None:
        s += "localStorage.setItem('d2r_multiKeep', %s);\n" % json.dumps(mk if isinstance(mk, str) else json.dumps(mk))
    return s


BODY = r"""
(function(){
var W = window;
function disk(){ var k = Array.from(H.RAW.keys()).filter(function(x){ return /(^|[^A-Za-z])d2r_multiKeep$/.test(x); })[0];
  return k ? H.RAW.get(k) : null; }
function sets(){ var n = 0; Object.keys(H.ls.byKeySet).forEach(function(x){ if (/(^|[^A-Za-z])d2r_multiKeep$/.test(x)) n += H.ls.byKeySet[x]; }); return n; }
OUT.boot = W._multiKeepShaped || null;
OUT.bootSets = sets();
OUT.disk = disk();
OUT.mem = JSON.parse(JSON.stringify(multiKeep));
__CASE__
})();
"""


def _run(mk, case=""):
    out = VPN.run(BODY.replace("__CASE__", case), prelude=_seed(mk), timeout=300)
    errs = (out.get("__boot") or {}).get("errors") or []
    if errs:
        raise AssertionError("the page did not boot clean in node: %r" % errs[:3])
    return out


class AKeeperIsAWantAndADestination(unittest.TestCase):

    def test_numbers_become_want_and_dest_and_are_written_back(self):
        o = _run({"Grief": 3, "Gore Rider": 2, "Stormshield": {"want": 2, "dest": "war"}})
        self.assertTrue(o["boot"] and o["boot"].get("ran"), "the load did not migrate a store of numbers: %r" % o["boot"])
        self.assertEqual(sorted(o["boot"]["turned"]), ["Gore Rider", "Grief"])
        want = {"Grief": {"want": 3, "dest": "auto"}, "Gore Rider": {"want": 2, "dest": "auto"},
                "Stormshield": {"want": 2, "dest": "war"}}
        self.assertEqual(o["mem"], want)
        self.assertEqual(json.loads(o["disk"]), want, "the store was not written back in the new shape: %r" % o["disk"])

    def test_a_second_load_turns_nothing(self):
        o = _run({"Grief": {"want": 3, "dest": "auto"}, "Stormshield": {"want": 2, "dest": "mule:uni-armor"}})
        self.assertFalse(o["boot"].get("ran"), "a store already {want, dest} was migrated again: %r" % o["boot"])
        self.assertTrue(o["boot"].get("done"), o["boot"])
        self.assertEqual(o["bootSets"], 1, "a load of a migrated store wrote it again (1 is the fixture's own seed)")
        self.assertEqual(o["mem"]["Stormshield"], {"want": 2, "dest": "mule:uni-armor"})

    def test_nothing_saved_is_the_default_keepers_unwritten(self):
        o = _run(None)
        self.assertTrue(o["boot"].get("done") and not o["boot"].get("ran"), o["boot"])
        self.assertIsNone(o["disk"], "a fresh board wrote its default keepers at load")
        self.assertEqual(o["mem"]["Andariel's Visage"], {"want": 5, "dest": "auto"})

    def test_a_shadow_never_writes(self):
        o = _run({"Grief": {"want": 3, "dest": "auto"}},
                 "multiKeep['Raven Frost'] = 4; window._tvdShadow = { owner: 'the other PC' };"
                 "OUT.r = window._multiKeepShape(); OUT.after = JSON.parse(JSON.stringify(multiKeep['Raven Frost']));"
                 "OUT.disk2 = disk(); window._tvdShadow = null;")
        self.assertFalse(o["r"].get("ran"), "the migration ran in a shadow: %r" % o["r"])
        self.assertIn("shadow", o["r"].get("why", ""))
        self.assertEqual(o["after"], 4, "a shadow turned a keeper in memory")
        self.assertEqual(json.loads(o["disk2"]), {"Grief": {"want": 3, "dest": "auto"}}, "a shadow wrote the store")

    def test_a_store_that_would_not_read_is_never_written_over(self):
        o = _run("[3]")
        self.assertFalse(o["boot"].get("ran"), o["boot"])
        self.assertIn("would not read", o["boot"].get("why", ""), "the migration did not say why it left the store: %r" % o["boot"])
        self.assertEqual(o["bootSets"], 1, "a store that would not read was written over at load (1 is the fixture's own seed)")
        self.assertEqual(o["mem"]["Andariel's Visage"], {"want": 5, "dest": "auto"}, "the page did not run on the default keepers")

    def test_every_reader_reads_both_shapes(self):
        o = _run({"Grief": {"want": 3, "dest": "war"}},
                 "multiKeep['Gore Rider'] = 4;"
                 "OUT.t = [multiTarget('Grief'), multiTarget('Gore Rider'), multiTarget('Nobody')];"
                 "OUT.d = [_mkDest('Grief'), _mkDest('Gore Rider'), _mkDest('Nobody')];"
                 "renderMultiKeep(); var el = document.getElementById('vault-multikeep');"
                 "OUT.html = el ? String(el.innerHTML) : '';")
        self.assertEqual(o["t"], [3, 4, 1])
        self.assertEqual(o["d"], ["war", "auto", "auto"])
        self.assertIn('data-mk="Grief"', o["html"], "a {want, dest} keeper is not listed on the Keepers panel")
        self.assertIn('data-mk="Gore Rider"', o["html"], "a plain-number keeper is not listed on the Keepers panel")

    def test_a_want_step_keeps_the_destination(self):
        o = _run({HC: {"want": 3, "dest": "war"}},
                 "W.vaultTargetBump('%s', 1); OUT.up = JSON.parse(JSON.stringify(multiKeep['%s']));"
                 "OUT.diskUp = JSON.parse(disk())['%s'];"
                 "W.vaultTargetBump('%s', -3); OUT.gone = !Object.prototype.hasOwnProperty.call(multiKeep, '%s');"
                 % (HC, HC, HC, HC, HC))
        self.assertEqual(o["up"], {"want": 4, "dest": "war"}, "a WANT step lost the destination: %r" % o["up"])
        self.assertEqual(o["diskUp"], {"want": 4, "dest": "war"})
        self.assertTrue(o["gone"], "a want below two must remove the keeper, as before")

    def test_the_default_keepers_are_their_own_objects(self):
        o = _run(None, "OUT.same = multiKeep['Raven Frost'] === MULTI_KEEP_DEFAULT['Raven Frost'];"
                       "OUT.absentSame = (function(){ var a = _mkShaped(MULTI_KEEP_DEFAULT); return a['Raven Frost'] === MULTI_KEEP_DEFAULT['Raven Frost']; })();")
        self.assertFalse(o["same"], "the live keepers share their objects with MULTI_KEEP_DEFAULT")
        self.assertFalse(o["absentSame"], "a copy of the default keepers shares its objects")


RED_PROOF = [
    {"why": "REG-2900 - the load turns the numbers in memory and never writes the store in the new shape",
     "file": "bible.html",
     "find": "  try { w = window.LSR.setItem('d2r_multiKeep', JSON.stringify(multiKeep)); } catch (eW) { w = false; }\n",
     "replace": "  w = true;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2900 - the migration runs in a shadow",
     "file": "bible.html",
     "find": "  if (window._tvdShadow) return { ran: false, why: 'a shadow is read only' };\n  var held = null;\n",
     "replace": "  var held = null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2900 - a store that would not read is not named as the reason the migration left it",
     "file": "bible.html",
     "find": "  if (held) return { ran: false, why: 'the keeper store would not read - its bytes are kept aside and nothing is written over them' };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2900 - a store already {want, dest} is migrated again on every load",
     "file": "bible.html",
     "find": "  if (!turned.length) return { ran: false, done: true, why: 'every keeper is {want, dest} already' };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2900 - a WANT step drops the destination",
     "file": "bible.html",
     "find": "function _mkSetWant(n, w){ multiKeep[n] = { want: w, dest: _mkDest(n) }; }",
     "replace": "function _mkSetWant(n, w){ multiKeep[n] = { want: w, dest: 'auto' }; }",
     "matches": 1, "needs": "node"},
    {"why": "REG-2900 - a reader reads only the old number shape",
     "file": "bible.html",
     "find": "  return (v && typeof v === 'object' && typeof v.want === 'number') ? v.want : 0;\n",
     "replace": "  return 0;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2900 - a copy of the keepers hands out the same objects",
     "file": "bible.html",
     "find": "    else if (v && typeof v === 'object') o[n] = { want: v.want, dest: (typeof v.dest === 'string' && v.dest) ? v.dest : 'auto' };\n",
     "replace": "    else if (v && typeof v === 'object') o[n] = v;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
