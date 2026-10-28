# -*- coding: utf-8 -*-
"""REG-2763 (his ruling 2026-10-28: "profiles should carry them") - A PROFILE CARRIES WHAT ITS OWN VAULT READS.

GrokBot's round trip (#230 6467035373) loaded a profile made from his real Mac data into a fresh browser: every store came
back byte-exact and the vault still changed shape (Grief 3x2 -> 2x1, Heart of the Oak 2x1 -> 3x2, a ring gone from the
shared stash), because the vault view also reads the chronicle ledgers - a runeword's base, the set pieces, the found log
- and the profile had left them out on purpose ("the chronicle has its own backup"). He ruled the profile carries them.

So: the chronicle ledgers ride in their own group; a save -> load into another world rebuilds every store, chronicle
included; the load's question names the chronicle when it would change it (this PC's own record is replaced), and a
store of counts says its units (GrokBot: "runeStash: 2 -> 2" while Ber went 5 -> 2). The vault's Undo snapshot leaves
the chronicle OUT - undoing a vault change must never take back a find recorded after it. And one list rules both doors:
every ledger store fleet_mask names is in the profile, and the shadow upload admits every profile store (his order: a
shadow renders the owner's exact data one to one).

Driven on the whole page in node (vault_page_node). RED_PROOF below.
"""
import json
import os
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
import vault_page_node as VPN  # noqa: E402

A = {"d2r_owned": ["Griswold's Edge"], "d2r_muleAssign": {"Griswold's Edge": "uni-weap"},
     "d2r_runeStash": {"Ber": 5, "Jah": 1},
     "d2r_foundLog": {"Harlequin Crest": {"t": 1790000000000}}, "d2r_setPieces": ["Tal Rasha's Guardianship"],
     "d2r_rwMade": {"Grief": "Phase Blade"}, "d2r_grailUnfound": []}

PRELUDE = "localStorage.setItem('d2r_ownerClaim', '*');\n" + "".join(
    "localStorage.setItem(%s, %s);\n" % (json.dumps(k), json.dumps(json.dumps(v))) for k, v in A.items())

BODY = r"""
(async function(){
var W = window;
var keys = []; Object.keys(W._PROFILE_STORES).forEach(function(g){ keys = keys.concat(W._PROFILE_STORES[g]); });
function snap(){ var s = {}; keys.forEach(function(k){ s[k] = W.LSR.getItem(k); }); return s; }
OUT.groups = Object.keys(W._PROFILE_STORES); OUT.keys = keys;
var before = snap(), file = W._vaultProfileBuild();
OUT.fileChron = (JSON.parse(file).groups || {}).chronicle || null;
var u = JSON.parse(W._vaultUndoSnap() || '{}');
OUT.undoKeys = Object.keys(u.stores || {}); OUT.undoGroups = Object.keys(u.groups || {});
// another PC: every profile store says something else
keys.forEach(function(k){ W.LSR.setItem(k, JSON.stringify({ other: k })); });
W.LSR.setItem('d2r_runeStash', JSON.stringify({ Ber: 2 }));
var asked = [];
OUT.load = await W.vaultProfileLoad(file, { confirm: function(m){ asked.push(m); return true; }, noReload: true });
var after = snap();
OUT.differ = keys.filter(function(k){ return before[k] !== after[k]; });
OUT.askChron = asked[0] || '';
// a profile whose chronicle matches this PC: the question says the chronicle is not touched
W.LSR.setItem('d2r_muleAssign', JSON.stringify({}));
W.LSR.setItem('d2r_runeStash', JSON.stringify({ Ber: 1, Jah: 5 }));   // the same 6 runes, moved between names
asked = [];
OUT.load2 = await W.vaultProfileLoad(file, { confirm: function(m){ asked.push(m); return true; }, noReload: true });
OUT.askVault = asked[0] || '';
})().catch(function(e){ OUT.err = String((e && e.stack) || e); });
"""

_PRINT = ("vm.runInThisContext(__BODY, { filename: 'law-body.js' });\n"
          "process.stdout.write('\\n__VAULT_PAGE_NODE_OUT__' + JSON.stringify(OUT) + '\\n');")


def _run_async(body, prelude):
    """vault_page_node's program, its last print made to wait for the body's promise (the profile load awaits its
    question). Refuses when the harness's print line is not there exactly once. -> OUT"""
    prog = VPN.program(body, prelude=prelude)
    if prog.count(_PRINT) != 1:
        raise AssertionError("vault_page_node's print line moved - this law cannot wait for an async body")
    prog = prog.replace(_PRINT, "Promise.resolve(vm.runInThisContext(__BODY, { filename: 'law-body.js' })).then(function(){ "
                                "process.stdout.write('\\n__VAULT_PAGE_NODE_OUT__' + JSON.stringify(OUT) + '\\n'); });")
    r = subprocess.run([VPN.NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=300)
    mark = "__VAULT_PAGE_NODE_OUT__"
    lines = [ln[len(mark):] for ln in (r.stdout or "").splitlines() if ln.startswith(mark)]
    if r.returncode != 0 or len(lines) != 1:
        raise AssertionError("the page did not run in node (exit %s): %s" % (r.returncode, ((r.stdout or "")[-500:] + (r.stderr or "")[-1500:])))
    return json.loads(lines[0])


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AProfileCarriesWhatItsVaultReads(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _run_async(BODY, PRELUDE)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertNotIn("err", self.o, self.o.get("err"))

    def test_the_chronicle_rides_in_its_own_group(self):
        chron = self.o.get("fileChron") or []
        for k in ("d2r_foundLog", "d2r_setPieces", "d2r_rwMade"):
            self.assertIn(k, chron, "the profile leaves out %s, which the vault view reads" % k)

    def test_a_round_trip_rebuilds_every_store_chronicle_included(self):
        self.assertTrue((self.o.get("load") or {}).get("ok"), self.o.get("load"))
        self.assertEqual(self.o.get("differ"), [], "a save -> load did not rebuild these stores: %r" % self.o.get("differ"))

    def test_the_question_names_the_chronicle_and_counts_units(self):
        ask = self.o.get("askChron") or ""
        self.assertIn("your CHRONICLE", ask, "the load replaces his chronicle without saying so: %r" % ask[:400])
        self.assertIn("runeStash: 2 → 6", ask, "a stash line counts keys, not units: %r" % ask[:600])
        v = self.o.get("askVault") or ""
        self.assertIn("the chronicle is not touched", v, "a load that leaves the chronicle alone does not say so: %r" % v[:300])
        # REG-2769 (the second eye on v3825..v3828) - a same-total change names what moved, never "6 -> 6" alone
        self.assertIn("runeStash: 6 \u2192 6 (Ber 1 \u2192 5, Jah 5 \u2192 1)", v,
                      "a stash whose runes moved between names read as unchanged figures: %r" % v[:600])

    def test_undo_never_carries_the_chronicle(self):
        self.assertNotIn("chronicle", self.o.get("undoGroups") or [])
        for k in ("d2r_foundLog", "d2r_setPieces", "d2r_rwMade"):
            self.assertNotIn(k, self.o.get("undoKeys") or [], "an undo would take back a find (%s)" % k)
        self.assertIn("d2r_muleAssign", self.o.get("undoKeys") or [], "PREMISE: the undo snapshot lost the vault")


class OneListRulesBothDoors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run("OUT.keys = []; Object.keys(window._PROFILE_STORES).forEach(function(g){ "
                        "OUT.keys = OUT.keys.concat(window._PROFILE_STORES[g]); });",
                        prelude="localStorage.setItem('d2r_ownerClaim', '*');\n", timeout=300) if VPN.NODE else {}

    @unittest.skipUnless(VPN.NODE, "node is absent - UNMEASURED here, never a pass")
    def test_every_ledger_store_is_in_the_profile(self):
        import fleet_mask as FM
        keys = set(self.o.get("keys") or [])
        miss = sorted(s for spec in FM.LEDGERS.values() for s in spec.get("stores") or [spec["store"]] if s not in keys)
        self.assertEqual(miss, [], "a chronicle ledger store does not travel in a profile: %r" % miss)

    @unittest.skipUnless(VPN.NODE, "node is absent - UNMEASURED here, never a pass")
    def test_the_shadow_admits_every_profile_store(self):
        import console_snapshot as CS
        refused = sorted(k for k in (self.o.get("keys") or []) if not CS.allowed_key(k))
        self.assertEqual(refused, ["d2r_intakeLog", "d2r_intakeSeen"],
                         "the shadow refuses a store a profile carries, so the shadow's vault is not his: %r" % refused)


RED_PROOF = [
    {"why": "REG-2769 - a same-total stash change prints two equal figures and nothing else",
     "file": "bible.html",
     "find": "      + (r.detail ? ' (' + r.detail + ')' : ''); }).join('\\n');   /* REG-2769 */",
     "replace": "      + ''; }).join('\\n');   /* REG-2769 */",
     "matches": 1, "needs": "node"},
    {"why": "REG-2763 - the profile leaves the chronicle out again",
     "file": "bible.html",
     "find": "    chronicle: ['d2r_foundLog','d2r_foundBy','d2r_setPieces','d2r_rwMade','d2r_rwUnmade','d2r_rwProfile','d2r_grailUnfound','d2r_craftMade']\n",
     "replace": "    chronicle: []\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2763 - an undo carries the chronicle and could take back a find",
     "file": "bible.html",
     "find": "    try { var t = window._vaultProfileBuild({ chronicle: false }); return",
     "replace": "    try { var t = window._vaultProfileBuild(); return",
     "matches": 1, "needs": "node"},
    {"why": "REG-2763 - the load replaces his chronicle and says it is not touched",
     "file": "bible.html",
     "find": "      + (chronCh ? ' — ' + chronCh + ' of them your CHRONICLE",
     "replace": "      + (false ? ' — ' + chronCh + ' of them your CHRONICLE",
     "matches": 1, "needs": "node"},
    {"why": "REG-2763 - a stash line counts keys, not units, again",
     "file": "bible.html",
     "find": "      if (ks.length && ks.every(function(k){ return typeof v[k] === 'number' && isFinite(v[k]); })) return",
     "replace": "      if (false) return",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
