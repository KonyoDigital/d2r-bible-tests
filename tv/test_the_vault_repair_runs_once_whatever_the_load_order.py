# -*- coding: utf-8 -*-
"""#160 (REG-2800) - THE ONE-TIME VAULT REPAIR (v1816) RUNS ONCE AND HIS HAND WINS, WHATEVER ORDER THE LOAD'S WORK LANDS IN.

tests/v1814_vault_routes_by_base_data.spec.ts:212 ("v1816 - the repair runs ONCE, and after it his hand wins") failed on
CI shard 8 of ci/claude-v3826e, first try AND retry, while the same bytes passed elsewhere. The retry's trace shows the
second load logging "[vault] re-routed 1 mis-filed item(s): Homunculus uni-weap->uni-armor" - the repair really ran again -
but on a store that had none of the first load's writes: the first load's last snapshot drew 3 owned items (its seed
cleanse had removed 6), the second load's first snapshot drew all 9 again, and every one-time stamped step of the first load
(provenance backfill, seed cleanse "removed 6", set-piece reconcile, records migrate "persisted 3") ran again. The spec's
init script re-seeds the pre-repair vault whenever its marker is missing, so a store the browser did not carry across the
reload became a new pre-repair vault, and the repair rightly ran on it. The first load had reloaded while the page's
deferred vault work (seed cleanse -> reconcile -> records arm, ~1.5 s after load) was running.

This law runs the same two loads on the whole page in node, with the store carried from the first load to the second and
the spec's init script reproduced, and FORCES each order the CI runner can produce (the console's answer arrives at once,
so the deferred chain runs inside its own timer):
  * the chain, then his hand  (the order of the failing trace);
  * his hand, then the chain  (a fast runner's order).
In both, the repair runs exactly once and his hand survives the second load. Measured while building it: a map written
STRAIGHT INTO STORAGE behind the page's memory (the spec's old "hand") is carried away by the chain's whole-map write
(vaultRemove -> saveA) when the chain lands after it - the reason the spec now files through his own door (vaultAssign) -
and with the one-shot check removed his door is still overruled on the second load, so that door does not blind the law.
It also holds the page's new readiness signal: window._vaultLoadSettled is raised only after the deferred chain's last
step, so a reader that waits on it has nothing of that load still to race.
RED_PROOF below.
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

# the spec's init script, verbatim in effect: what the document was handed, the owner claim, the webdriver spoof, the
# seed only while its marker is absent
INIT = r"""
try { window.__v1816AtStart = { stamp: localStorage.getItem('d2r_vaultRerouteDone'), seeded: localStorage.getItem('__seeded') }; } catch (e) {}
try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
try { Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true }); } catch (e) {}
try {
  if (!localStorage.getItem('__seeded')) {
    localStorage.setItem('d2r_owned', JSON.stringify(["Andariel's Visage", 'Homunculus', "Astreon's Iron Ward", 'Goldwrap', 'Nightsmoke',
      'Blackhand Key', 'Shaftstop', "Titan's Revenge", "Nord's Tenderizer"]));
    localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Homunculus': 'uni-weap', 'Blackhand Key': 'uni-weap' }));
    localStorage.setItem('__seeded', '1');
  }
} catch (e) {}
"""
# what the store held the FIRST time the page raised its settled signal
WATCH = r"""
(function(){
  var v;
  Object.defineProperty(window, '_vaultLoadSettled', { configurable: true,
    get: function(){ return v; },
    set: function(x){ if (v === undefined) window.__settledSaw = { cleanse: !!localStorage.getItem('d2r_seedCleanse'),
                                                                   reconcile: !!localStorage.getItem('d2r_setPieceReconcile') }; v = x; } });
})();
"""
# the console answers at once (the CI stub answers {} in ms): the deferred chain runs inside its own 1.5 s timer
SYNC = ("        Promise.resolve(p).then(run, run);", "        run();", 1)

HAND = "window.vaultAssign('Homunculus', 'uni-weap');"
READ = ("JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}')['Homunculus']")

LOAD1 = r"""
OUT.repaired = %(read)s;
OUT.stamp = window.LSR.getItem('d2r_vaultRerouteDone');
OUT.settledAtBoot = window._vaultLoadSettled === undefined ? null : window._vaultLoadSettled;
if (%(handFirst)s) { %(hand)s OUT.handAt = 'before the chain'; }
OUT.ran = H.flush(600000, 50);
if (!%(handFirst)s) { %(hand)s OUT.handAt = 'after the chain'; }
OUT.settled = !!window._vaultLoadSettled; OUT.saw = window.__settledSaw || null;
OUT.end = %(read)s;
OUT.raw = {}; H.RAW.forEach(function(v, k){ OUT.raw[k] = v; });
"""
LOAD2 = r"""
OUT.atStart = window.__v1816AtStart || null;
OUT.boot = %(read)s;
OUT.ran = H.flush(600000, 50);
OUT.settled = !!window._vaultLoadSettled;
OUT.rerouted = window._vaultReroute || null;
OUT.end = %(read)s;
"""


def _two_loads(hand_first):
    o1 = VPN.run(LOAD1 % {"read": READ, "hand": HAND, "handFirst": "true" if hand_first else "false"},
                 prelude=INIT + WATCH, patches=[SYNC], timeout=300)
    carry = "".join("localStorage.setItem(%s, %s);\n" % (json.dumps(k), json.dumps(v)) for k, v in o1.pop("raw").items())
    o2 = VPN.run(LOAD2 % {"read": READ}, prelude=carry + INIT + WATCH, patches=[SYNC], timeout=300)
    return o1, o2


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class TheRepairRunsOnceWhateverTheLoadOrder(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chain_first = _two_loads(hand_first=False)
        cls.hand_first = _two_loads(hand_first=True)

    def _premise(self, o1, o2):
        self.assertEqual(o1["__boot"]["errors"], [], o1["__boot"])
        self.assertEqual(o2["__boot"]["errors"], [], o2["__boot"])
        self.assertEqual(o1["repaired"], "uni-armor", "PREMISE: the first load's one-time repair did not move it: %r" % o1)
        self.assertTrue(o1["stamp"], "PREMISE: the first load did not stamp the repair: %r" % o1)
        self.assertTrue((o2["atStart"] or {}).get("stamp"), "PREMISE: the second load was not handed the first load's stamp: %r" % o2)
        self.assertEqual(o2["boot"], "uni-weap", "his hand was gone before the second load's repair could have run: %r" % o2)

    def test_the_chain_then_his_hand_the_failing_traces_order(self):
        o1, o2 = self.chain_first
        self._premise(o1, o2)
        self.assertIsNone(o2["rerouted"], "the repair ran a second time on the second load: %r" % o2)
        self.assertEqual(o2["end"], "uni-weap", "his hand lost on the second load: %r" % o2)

    def test_his_hand_then_the_chain_a_fast_runners_order(self):
        o1, o2 = self.hand_first
        self._premise(o1, o2)
        self.assertEqual(o1["end"], "uni-weap", "the deferred chain carried the repaired map back over his hand: %r" % o1)
        self.assertIsNone(o2["rerouted"], "the repair ran a second time on the second load: %r" % o2)
        self.assertEqual(o2["end"], "uni-weap", "his hand lost on the second load: %r" % o2)

    def test_the_page_says_when_its_deferred_vault_work_is_done(self):
        o1, o2 = self.chain_first
        self.assertIsNone(o1["settledAtBoot"], "the settled signal was up before the deferred work ran: %r" % o1)
        self.assertTrue(o1["settled"] and o2["settled"], "the settled signal never rose: %r / %r" % (o1, o2))
        self.assertEqual(o1["saw"], {"cleanse": True, "reconcile": True},
                         "the settled signal rose before the cleanse and the reconcile had stamped: %r" % o1["saw"])


RED_PROOF = [
    {"why": "#160 (REG-2800) - the repair is no longer one-shot: it runs on every load and overrules his hand",
     "file": "bible.html",
     "find": "    var moved = [], skipped = [];\n    try {\n      if (window.LSR.getItem(DONE)) return;\n",
     "replace": "    var moved = [], skipped = [];\n    try {\n",
     "matches": 1, "needs": "node"},
    {"why": "#160 (REG-2800) - the repair never stamps itself done, so the next load repeats it",
     "file": "bible.html",
     "find": "      try { window.LSR.setItem(DONE, String(Date.now())); } catch(e){}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "#160 (REG-2800) - the page never says its deferred vault work is done",
     "file": "bible.html",
     "find": "          try { window._vaultLoadSettled = Date.now(); } catch (eSt) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "#160 (REG-2800) - the settled signal rises before the cleanse runs",
     "file": "bible.html",
     "find": "          try { window._seedCleanse(Object.assign({}, opts, { mainLedger: ml })); } catch (e) {}\n",
     "replace": "          try { window._vaultLoadSettled = Date.now(); } catch (eSt0) {}\n"
                "          try { window._seedCleanse(Object.assign({}, opts, { mainLedger: ml })); } catch (e) {}\n",
     "matches": 1, "needs": "node"},
    {"why": "#160 (REG-2800) - the deferred chain writes the repaired map back over his hand (a filing made after the "
            "repair is forgotten by the page's memory)",
     "file": "bible.html",
     "find": "    var DONE = 'd2r_vaultRerouteDone';\n",
     "replace": "    var DONE = 'd2r_vaultRerouteDone';\n"
                "    window.vaultAssign = (function(orig){ return function(n, m){ var keep = JSON.stringify(assign); var r = orig.apply(this, arguments);"
                " var was = JSON.parse(keep); Object.keys(assign).forEach(function(k){ delete assign[k]; }); Object.keys(was).forEach(function(k){ assign[k] = was[k]; }); return r; }; })(window.vaultAssign);\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
