# -*- coding: utf-8 -*-
"""#276 (REG-2052) - FURNITURE HIS MAIN CARRIES, FILED IN A MULE, IS A VAULT INTEGRITY FINDING WITH A SAFE UNFILE.

GrokBot tick 417 on #230 (v3621, K10): a Tome of Identify was a mule TILE in UNI-WEAPONS ("Base item · TV-vaulted ·
physically in your stash · Best-of-the-best") while the lock note above it said MAIN carries it as inventory furniture and
"a MAIN item is never in a mule". REG-2031 stops NEW offers of kit to a mule; this was an OLD filing, and VAULT INTEGRITY
listed only the three SHARED STASH misroutes, so neither "Fix all safe" nor Auto-Sort could clear it.

  * a furniture name (the furniture law: tomes, the Cube, keys, Wirt's Leg) filed in a mule -> kind 'kit-in-mule', fixable;
  * the same name in the SHARED STASH is account storage, not a mule -> no finding; a non-furniture name -> none;
  * the fix unfiles it through vaultUnassign (the door that refuses a HARDENED row) and moves it to no other mule;
  * Auto-Sort applies the same unfile, never over a home his own hand chose.
Drives the SHIPPED _vaultAudit, _vaultAuditApply and the furniture law, cut from bible.html and run in node with the
stores stubbed. A missing node raises; this law does not skip.
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
AUDIT = ("  function _vaultAudit(){\n",
         "\n    return { findings:F, total:F.length, fixable:fixable, review:F.length-fixable };\n  }\n")
APPLY = ("  function _vaultAuditApply(f){\n", "\n    } catch(e){ return false; }\n  }\n")
FURN = ("var _FURNITURE_WORDS = [", "\n  return _FURNITURE_WORDS.some(function(w){ return new RegExp('(^|[^a-z])' + w + '($|[^a-z])').test(low); });\n};\n")
AUTOSORT_UNFILE = ("        if (f.kind === 'kit-in-mule'){   /* #276 - furniture MAIN carries leaves the mule; it is not moved to another one */\n"
                   "          var uu = window.vaultUnassign(f.item);\n")


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:50], s.count(start)))
    i = s.index(start)
    j = s.index(end, i)
    return s[i:j + len(end)]


def _run(assign, apply_kinds=()):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    js = """
var window = {}, UNASSIGNED = [], FILED = [];
%s
var MULES = { "uni-weap": "UNI-WEAPONS", "uni-armor": "UNI-ARMOR", "shared": "SHARED STASH" };
function muleById(id){ return MULES[id] ? { id: id, name: MULES[id] } : null; }
function suggestMule(n){ return { id: "uni-weap", why: "stub" }; }
var assign = %s, owned = new Set(Object.keys(assign)), magicFinds = {}, unknownReads = new Set();
function _muleName(id){ var m = muleById(id); return m ? m.name : id; }
function _vaStoreLabel(k){ return k; }
function _vaIsRW(n){ return false; }
function _vaIsGrailUni(n){ return false; }
function _mfChecker(n){ return null; }
function _vaG3Filled(){ return {}; }
function _vaProvenance(n){ return ''; }
window.vaultUnassign = function(n){ UNASSIGNED.push(n); delete assign[n]; return { ok: true }; };
window.vaultFile = function(n, w, o){ FILED.push([n, o && o.mule]); return { ok: true }; };
%s
%s
var r = _vaultAudit(), applied = [];
r.findings.forEach(function(f){ if (%s.indexOf(f.kind) >= 0) applied.push([f.kind, f.item, _vaultAuditApply(f)]); });
console.log(JSON.stringify({ findings: r.findings.map(function(f){ return [f.kind, f.item, f.fixable, f.to]; }),
                             applied: applied, unassigned: UNASSIGNED, filed: FILED, left: assign }));
""" % (_cut(s, FURN), json.dumps(assign), _cut(s, AUDIT), _cut(s, APPLY), json.dumps(list(apply_kinds)))
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the cut audit did not run in node: %s" % r.stderr[-600:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class FurnitureFiledInAMuleIsAnIntegrityFinding(unittest.TestCase):

    def test_a_tome_in_a_mule_is_a_fixable_kit_finding(self):
        out = _run({"Tome of Identify": "uni-weap", "Horadric Cube": "uni-armor", "Windforce": "uni-weap"})
        kit = sorted(f[1] for f in out["findings"] if f[0] == "kit-in-mule")
        self.assertEqual(kit, ["Horadric Cube", "Tome of Identify"],
                         "furniture filed in a mule is not a finding: %r" % out["findings"])
        self.assertTrue(all(f[2] for f in out["findings"] if f[0] == "kit-in-mule"), "a kit finding is not auto-fixable")
        self.assertNotIn("Windforce", [f[1] for f in out["findings"] if f[0] == "kit-in-mule"],
                         "a non-furniture item was called kit")

    def test_the_shared_stash_is_not_a_mule(self):
        out = _run({"Tome of Identify": "shared"})
        self.assertEqual([f for f in out["findings"] if f[0] == "kit-in-mule"], [],
                         "a tome kept in the shared stash was called a mule filing")

    def test_the_fix_unfiles_and_moves_it_nowhere(self):
        out = _run({"Tome of Identify": "uni-weap"}, apply_kinds=["kit-in-mule"])
        self.assertEqual(out["applied"], [["kit-in-mule", "Tome of Identify", True]], out)
        self.assertEqual(out["unassigned"], ["Tome of Identify"], "the fix did not go through vaultUnassign")
        self.assertEqual(out["filed"], [], "the fix filed the furniture into another mule")
        self.assertNotIn("Tome of Identify", out["left"])

    def test_auto_sort_unfiles_it_too(self):
        s = _src()
        self.assertEqual(s.count(AUTOSORT_UNFILE), 1, "Auto-Sort no longer unfiles furniture its audit names")
        self.assertEqual(s.count("        if (f.kind !== 'misroute' && f.kind !== 'kit-in-mule') return;\n"), 1,
                         "Auto-Sort skips the kit finding again")


RED_PROOF = [
    {"why": "REG-2052 - furniture filed in a mule is no finding again",
     "file": "bible.html",
     "find": "      if (_furn && assign[n] !== 'shared' && assign[n] !== '__throwout' && muleById(assign[n])){\n",
     "replace": "      if (false){\n",
     "matches": 1},
    {"why": "REG-2052 - a tome in the shared stash is called a mule filing",
     "file": "bible.html",
     "find": "      if (_furn && assign[n] !== 'shared' && assign[n] !== '__throwout' && muleById(assign[n])){\n",
     "replace": "      if (_furn && muleById(assign[n])){\n",
     "matches": 1},
    {"why": "REG-2052 - the fix stops unfiling",
     "file": "bible.html",
     "find": "      else if (f.kind==='kit-in-mule'){ var _ku0 = window.vaultUnassign(f.item); if (!_ku0 || !_ku0.ok) return false; }",
     "replace": "      else if (f.kind==='kit-in-mule'){ return false; }",
     "matches": 1},
    {"why": "REG-2052 - Auto-Sort skips the kit finding",
     "file": "bible.html",
     "find": "        if (f.kind !== 'misroute' && f.kind !== 'kit-in-mule') return;\n",
     "replace": "        if (f.kind !== 'misroute') return;\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
