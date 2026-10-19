"""v3773 - opening the vault on his store spent 148 ms self in findSetPiece: every call re-normed
all 135 set pieces. It now keeps a normed index per set-table shape. In node, on the real
functions: every piece (plain, slot-suffixed, odd quotes) resolves to the same answer the old scan
gave, an unknown name is null, 300 lookups norm the table once, and a table that grows is re-read.
Each RED_PROOF changes what the page does.
"""
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _read():
    with open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        return fh.read()


def _fn(bible, head):
    i = bible.find(head)
    if i < 0:
        return None
    j = bible.find("\n}\n", i)
    return bible[i:j + 2]


def problems(bible):
    parts = []
    for head in ("function _norm(s){", "function __allSets(){", "function __pieceBase(pc){",
                 "function __pieceSlot(pc){", "function findSetPiece(name){"):
        if head == "function findSetPiece(name){":
            f = _fn(bible, head)
        else:
            i = bible.find(head)
            f = bible[i:bible.find("\n", i)] if i >= 0 else None
        if not f:
            return ["missing %s" % head]
        parts.append(f)
    prog = r"""
var ITEM_SETS = [{name:'Odd', pieces:["Foo Amulet (ring)"]}, {name:'Tal Rasha', pieces:["Tal Rasha's Adjudication (amulet)","Tal Rasha's Guardianship (armor)"]},
                 {name:'Dupe', pieces:["Twin Piece (ring)","Other (helm)"]}];
var SET_PIECES_EXTRA = [{name:'Later', pieces:["Twin Piece (amulet)","Shut Up (belt)","Foo (ring)"]}];
var SET_PIECES_EXTRA2 = [];
""" + "\n".join(parts) + r"""
var _n = _norm, calls = 0; _norm = function(s){ calls++; return _n(s); };
function ref(name){ var q=_n(name), qs=_n(String(name).replace(/\s*\([^)]*\)\s*$/,'')), S=__allSets();
  for (var i=0;i<S.length;i++){ var ps=S[i].pieces||[]; for (var k=0;k<ps.length;k++){ var pb=_n(__pieceBase(ps[k]));
    if (pb===q||(qs&&pb===qs)) return S[i].name+'|'+ps[k]+'|'+__pieceSlot(ps[k]); } } return null; }
function got(name){ var r=findSetPiece(name); return r ? r.set.name+'|'+r.piece+'|'+r.slot+(r.base===__pieceBase(r.piece)?'':'!base') : null; }
var names = ["Tal Rasha's Adjudication","tal rasha\u2019s adjudication (amulet)","Twin Piece","Twin Piece (amulet)","Shut Up",
             "Shut Up (belt)","Nobody","", "Other (helm)", "  other  ", "Foo (amulet)", "Foo"];
var mism = [];
names.forEach(function(n){ var a=ref(n), b=n?got(n):findSetPiece(n); if (a!==b && !(a===null&&b===null)) mism.push([n,a,b]); });
if (got("Foo (amulet)") !== "Odd|Foo Amulet (ring)|ring") mism.push(["Foo (amulet)", "Odd|Foo Amulet (ring)|ring", got("Foo (amulet)")]);
calls = 0; for (var t=0;t<300;t++) findSetPiece("Twin Piece");
var many = calls;
SET_PIECES_EXTRA.push({name:'New', pieces:["Fresh One (ring)"]});
var grown = got("Fresh One");
console.log(JSON.stringify({mism:mism, many:many, grown:grown}));
"""
    try:
        r = subprocess.run(["node", "-"], input=prog, capture_output=True, text=True, timeout=60)
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        return ["node run failed: %s" % e]
    bad = []
    for m in out["mism"]:
        bad.append("lookup differs from the table scan: %s" % (m,))
    if out["many"] > 300 * 3:
        bad.append("300 lookups normed %d strings: the table is re-normed per call" % out["many"])
    if out["grown"] != "New|Fresh One (ring)|ring":
        bad.append("a set table that grew is not re-read: %s" % out["grown"])
    return bad


class TestSetPieceLookupStaysCheap(unittest.TestCase):
    def test_01_same_answers_and_one_index(self):
        bad = problems(_read())
        self.assertEqual(bad, [], bad)

    def test_02_distinct_attacks_clear_the_wilson_bar(self):
        from confidence import wilson_lower
        n = len(RED_PROOF)
        self.assertGreaterEqual(n, 10)
        self.assertGreaterEqual(wilson_lower(n, n), 0.722)


RED_PROOF = [
    {"why": "The index is thrown away every call.", "file": "bible.html",
     "find": "    findSetPiece._ix=ix;\n", "replace": "    findSetPiece._ix=null;\n", "matches": 1},
    {"why": "The index never notices a grown table.", "file": "bible.html",
     "find": "  if(!ix || ix.sig!==sig){", "replace": "  if(!ix){", "matches": 1},
    {"why": "A later duplicate piece overwrites the first in table order.", "file": "bible.html",
     "find": "        if(!Object.prototype.hasOwnProperty.call(ix.at,pb)) ix.at[pb]=[i,k];",
     "replace": "        ix.at[pb]=[i,k];", "matches": 1},
    {"why": "The slot-stripped name is no longer tried.", "file": "bible.html",
     "find": "  var b=(qStripped && Object.prototype.hasOwnProperty.call(ix.at,qStripped))?ix.at[qStripped]:null;",
     "replace": "  var b=null;", "matches": 1},
    {"why": "The plain name is no longer tried.", "file": "bible.html",
     "find": "  var a=Object.prototype.hasOwnProperty.call(ix.at,q)?ix.at[q]:null;",
     "replace": "  var a=null;", "matches": 1},
    {"why": "When both hit, the later piece wins.", "file": "bible.html",
     "find": "((a[0]<b[0]||(a[0]===b[0]&&a[1]<=b[1]))?a:b)", "replace": "b", "matches": 1},
    {"why": "The returned slot is the piece name.", "file": "bible.html",
     "find": "base:__pieceBase(pc), slot:__pieceSlot(pc)};", "replace": "base:__pieceBase(pc), slot:pc};", "matches": 1},
    {"why": "The returned base is the raw piece.", "file": "bible.html",
     "find": "piece:pc, base:__pieceBase(pc),", "replace": "piece:pc, base:pc,", "matches": 1},
    {"why": "The index keys are not normed.", "file": "bible.html",
     "find": "        var pb=_norm(__pieceBase(ps[k]));\n        if(!Object",
     "replace": "        var pb=__pieceBase(ps[k]);\n        if(!Object", "matches": 1},
    {"why": "An unknown name answers the first piece instead of null.", "file": "bible.html",
     "find": "  if(!h) return null;\n  var pc=sets[h[0]]", "replace": "  if(!h) h=[0,0];\n  var pc=sets[h[0]]", "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
