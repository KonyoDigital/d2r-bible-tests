# -*- coding: utf-8 -*-
"""REG-1939 - THE VAULT'S REGISTERED TOTAL COUNTS EVERY COLUMN IT SHOWS AND NAMES ITS PARTS.

GrokBot (#230 tick 371, FYI 7, "SAME" as 370): "REGISTERED 20 vs 19 owned". Not a contradiction by itself: the
Registered total counts everything read - his v342.20 words, "register the item regardless... distinguished but
still a total amount" - so magic & rare finds and throw-outs sit on top of the chronicle. But nothing on screen
said what the 20 was made of, and the sum left out the "❓ Not recognised" column that v2402 added precisely so
"the total be honest": with one orphan the badge said one less than the columns under it.

The law drives the REAL renderVaultRegistered (lifted from bible.html, its globals stubbed through a scope proxy)
on a fixture vault: 2 muled, 1 orphan, 1 magic find, 1 throw-out. The badge is the sum of every column (5), the
subtitle says "3 chronicle (2 owned . 1 not recognised) . 1 magic & rare . 1 throw-out", and an orphan is counted.
REG-2075 (#286): the chronicle count names how it meets the population line's "owned" - the ❓ names it cannot place.
REG-2097 (GrokBot tick 427 K18b): its 'owned' is the vault pool's own count - the top line's number - and owned
shared-stash goods the pool leaves out (runes, essences) are named beside it, never folded in (20 owned vs 19).
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

START = "  function renderVaultRegistered(){"


def _lift():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        src = fh.read()
    st = src.find(START)
    if st < 0:
        return None
    end = src.find("\n  }\n", st)          # the function closes at its own two-space indent
    if end < 0:
        return None
    return src[st:end + len("\n  }\n")]


HARNESS = r"""
var el = {hidden: true, innerHTML: ''};
var OWNED = %s, POOL = %s, MULED = %s, FINDS = %s, UNK = %s, SHARED = %s;
var stub = {
  document: {getElementById: function(id){ return id === 'vault-registered' ? el : null; },
             addEventListener: function(){}},
  window: {},
  owned: new Set(OWNED), unknownReads: new Set(UNK), magicFinds: FINDS,
  ownedPool: function(){ return POOL; },
  isAggregate: function(){ return false; }, isSharedStash: function(n){ return SHARED.indexOf(n) >= 0; },
  assign: (function(){ var a = {}; MULED.forEach(function(n){ a[n] = 'm1'; }); return a; })(),
  muleById: function(id){ return id === 'm1' ? {name: 'Mule One'} : null; },
  _dedupCanon: function(a){ return a; }, esc: function(s){ return String(s); }, jsArg: function(s){ return String(s); },
  art: function(){ return ''; }, copyCount: function(){ return 1; }, multiTarget: function(){ return 1; },
  _VAL_LABEL: {}, Array: Array, Object: Object, String: String, Number: Number, Math: Math, JSON: JSON,
  Set: Set, encodeURIComponent: encodeURIComponent, location: {protocol: 'http:'}
};
var scope = new Proxy(stub, {
  has: function(t, k){ return k !== 'process'; },
  get: function(t, k){ if (k === Symbol.unscopables) return undefined;
                       if (k in t) return t[k];
                       if (k in globalThis) return globalThis[k];   /* undefined, console, Symbol ... stay real */
                       return function(){ return ''; }; }
});
var fn;
with (scope) { eval(%s); fn = renderVaultRegistered; }
with (scope) { fn(); }
var tot = /<span class="to-ct">(\d+)<\/span>/.exec(el.innerHTML);
var sub = /<span class="to-subt">([^<]*)<\/span>/.exec(el.innerHTML);
var cols = []; var re = /<span class="vrg-col-ct">(\d+)<\/span>/g, m;
while ((m = re.exec(el.innerHTML))) cols.push(+m[1]);
process.stdout.write(JSON.stringify({tot: tot ? +tot[1] : null, sub: sub ? sub[1] : null, cols: cols, hidden: el.hidden}));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class TheRegisteredTotalNamesItsParts(unittest.TestCase):

    def render(self, owned, pool, muled, finds, unk, shared=()):
        fn = _lift()
        self.assertIsNotNone(fn, "renderVaultRegistered is gone from bible.html")
        js = HARNESS % (json.dumps(owned), json.dumps(pool), json.dumps(muled), json.dumps(finds), json.dumps(unk),
                        json.dumps(list(shared)), json.dumps(fn))
        p = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, "the shipped renderer would not run: %s" % p.stderr[-800:])
        return json.loads(p.stdout)

    def test_every_column_is_in_the_total_and_the_split_is_said(self):
        out = self.render(owned=["Shako", "Arachnid Mesh", "Dwarf Star Ring"], pool=["Shako", "Arachnid Mesh"],
                          muled=["Shako", "Arachnid Mesh"], finds={"Jade Grand Charm": {"q": "magic"}},
                          unk=["Gorgon Crossbo"])
        self.assertFalse(out["hidden"], out)
        self.assertEqual(sum(out["cols"]), 5, "the fixture's columns are not what this case assumes: %s" % out)
        self.assertEqual(out["tot"], sum(out["cols"]),
                         "the Registered badge (%s) is not the sum of the columns under it %s - the ❓ orphan is "
                         "left out (REG-1939)" % (out["tot"], out["cols"]))
        self.assertEqual(out["sub"], "3 chronicle (2 owned · 1 ❓ not recognised) · 1 magic &amp; rare · 1 throw-out — everything read, sorted",
                         "the total does not say what it is made of, or how its chronicle meets the top line's 'owned' (REG-2075)")

    def test_with_nothing_but_owned_the_total_is_the_owned(self):
        out = self.render(owned=["Shako", "Arachnid Mesh"], pool=["Shako", "Arachnid Mesh"],
                          muled=["Shako", "Arachnid Mesh"], finds={}, unk=[])
        self.assertEqual(out["tot"], 2)
        self.assertTrue(out["sub"].startswith("2 chronicle · 0 magic"), "no orphan, no bridge to say: %r" % out["sub"])


    def test_owned_is_the_top_lines_count_and_shared_goods_are_named(self):
        """REG-2097 - his vault: 'REGISTERED 21 · 21 chronicle (20 owned · 1 not recognised)' under '19 owned'. The extra
        one was an owned shared-stash good the vault pool leaves out; 'owned' now IS the pool's count."""
        out = self.render(owned=["Shako", "Arachnid Mesh", "Ber Rune", "Dwarf Star Ring"], pool=["Shako", "Arachnid Mesh"],
                          muled=["Shako", "Arachnid Mesh"], finds={}, unk=[], shared=["Ber Rune"])
        self.assertTrue(out["sub"].startswith("4 chronicle (2 owned · 1 shared-stash good (not in the vault's count) · "
                                              "1 ❓ not recognised)"),
                        "the subtitle's 'owned' is not the pool's count the top line prints (REG-2097): %r" % out["sub"])
        out = self.render(owned=["Shako", "Ber Rune"], pool=["Shako"], muled=["Shako"], finds={}, unk=[], shared=["Ber Rune"])
        self.assertTrue(out["sub"].startswith("2 chronicle (1 owned · 1 shared-stash good (not in the vault's count)) · "),
                        "a shared good with no orphan is still named: %r" % out["sub"])


RED_PROOF = [
    {
        "why": "REG-1939 - the ❓ Not recognised column drops out of the total again: the badge says one less than it shows",
        "file": "bible.html",
        "find": "    var _regChron=all.length+orphan.length;\n",
        "replace": "    var _regChron=all.length;\n",
        "matches": 1,
    },
    {
        "why": "REG-1939 - the subtitle stops naming the split, so '20 vs 19 owned' reads as a contradiction again",
        "file": "bible.html",
        "find": "<span class=\"to-subt\">'+_regChron+' chronicle'+((orphan.length||_regShared)?' ('+_regOwned+' owned'+(_regShared?' · '+_regShared+' shared-stash good'+(_regShared===1?'':'s')+' (not in the vault\\'s count)':'')+(orphan.length?' · '+orphan.length+' ❓ not recognised':'')+')':'')+' · '+findNames.length+' magic &amp; rare · '+unkNames.length+' throw-out — everything read, sorted</span>",
        "replace": "<span class=\"to-subt\">chronicle · magic &amp; rare · throw-out — everything read, sorted</span>",
        "matches": 1,
    },
    {
        "why": "REG-2075 - the chronicle count stops saying how it meets the top line's 'owned' (#286: 21 chronicle vs 19 owned)",
        "file": "bible.html",
        "find": "((orphan.length||_regShared)?' ('+_regOwned+' owned'+(_regShared?' · '+_regShared+' shared-stash good'+(_regShared===1?'':'s')+' (not in the vault\\'s count)':'')+(orphan.length?' · '+orphan.length+' ❓ not recognised':'')+')':'')",
        "replace": "''",
        "matches": 1,
    },
    {
        "why": "REG-2097 - the subtitle's 'owned' folds in shared-stash goods the vault pool leaves out (20 owned vs 19)",
        "file": "bible.html",
        "find": "    var _regShared=all.filter(function(n){ return poolM.indexOf(n)<0; }).length, _regOwned=all.length-_regShared;\n",
        "replace": "    var _regShared=0, _regOwned=all.length;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
