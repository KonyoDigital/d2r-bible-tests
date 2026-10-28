# -*- coding: utf-8 -*-
"""REG-2536 - THE PLANNER'S PLATE SAYS WHAT THE PICK DID: "SAVED INTO THE VAULT" ONLY WHEN THE PICK WAS KEPT.

The V1 round-3 review (reproduced on ed832f3d9, the planner driven through its own open / write / paint doors in node):
the plate picked its headline with /filed to|already filed/ on the pick's SENTENCE, and the door's refusal reads "... is
locked to your MAIN ... so it is never filed to a mule". A 2os Tome and an eth 2os Occult Tome were refused (writeOk
false, nothing on disk) under the headline "Saved into the vault" with the saved class - the plate said the opposite of
what happened. Any MAIN-locked pick did the same. [[unknown-stays-unknown]]

THE RULE: the headline is the pick's RESULT, not a word in its sentence. ctx.write keeps what vaultPlannerFile itself
counts as kept (filed - a copy too - or already filed), and the plate reads that.

Driven on the WHOLE page in node (tv/vault_page_node.py), the planner opened, written and painted through its own doors,
#vault-planner-host read as he sees it, in his world:
  * a pick the door refuses because the name is locked to his MAIN (a 3-session lane lock on "Monarch (4os)") - its
    sentence says "filed to" - reads "Not in a locker yet", never "Saved into the vault";
  * a pick that files (a 4os Monarch to SOCKETED) reads saved; the same pick saved again in that open ("already filed")
    reads saved; a later open's copy reads saved;
  * a plain white that stays unfiled, and a cleared pick, read "Not in a locker yet";
  * the review's own pick, a 2os Warlock Tome: its plate agrees with the disk, and it is filed to SOCKETED (REG-2535).
RED_PROOF below: the sentence regex put back lights the refused pick; the result not kept turns every kept pick to
"Not in a locker yet".
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

import vault_page_node as VPN  # noqa: E402  (the whole page in node)

AUTOMATED = r"""
Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });
location.protocol = 'file:'; location.href = 'file:///spec/bible.html'; location.origin = 'null'; location.host = ''; location.hostname = '';
"""

#: his MAIN carries a 4os Monarch: a lane-lock row seen in 3 separate sessions (his v1985 bar)
LOCKED = r"""
localStorage.setItem('d2r_laneLock', JSON.stringify({ 'Monarch (4os)': { lane: 'equipment', sessions: ['s1', 's2', 's3'] } }));
"""

BODY = r"""
(function(){
var W = window;
function disk(k){ try { return JSON.parse(W.LSR.getItem(k) || 'null'); } catch (e) { return 'UNREADABLE'; } }
function entryOf(name, sockets, eth){
  var d = W._cbDb();
  var code = Object.keys(d.b).find(function(c){ return d.b[c][0] === name; });
  if (!code) throw new Error('no base code for ' + name);
  var e = W._cbEntryFor(W._cbItem('b:' + code));
  e.sockets = sockets; e.eth = !!eth;
  return e;
}
var orig = W._cbHostOpen, CTX = null;
W._cbHostOpen = function(c){ CTX = c; return orig.apply(this, arguments); };
var res = [];
function plate(label, entry, look){
  var w = look ? { ok: true } : CTX.write(entry);   /* `look`: read the plate as the open drew it, no pick written */
  W.vaultPlannerPaint();
  var host = document.getElementById('vault-planner-host');
  var html = host ? host.innerHTML : '';
  var k = /<div class="vp-plate-k">([^<]*)<\/div>/.exec(html);
  var a = disk('d2r_muleAssign') || {};
  res.push({ label: label, writeOk: !!(w && w.ok), say: CTX.say || '', headline: k ? k[1] : null,
             saved: /class="vp-plate vp-plate-saved"/.test(html), wait: /class="vp-plate vp-plate-wait"/.test(html),
             home: a['Monarch (4os)'] || null, tome: a['Tome (2os)'] || null });
}
function open(){ CTX = null; var op = W.vaultPlannerOpen(''); if (!CTX) throw new Error('the planner did not open: ' + JSON.stringify(op)); }
function close(){ W.vaultPlannerClose(); H.flush(60, 3); }
var S_ = __SCENARIO__;
if (S_ === 'locked'){
  open(); plate('locked monarch', entryOf('Monarch', 4, false)); close();
} else {
  open(); plate('opened', null, true);
  plate('monarch', entryOf('Monarch', 4, false));
  plate('monarch again', entryOf('Monarch', 4, false));
  close();
  open(); plate('monarch later', entryOf('Monarch', 4, false)); close();
  /* a clear of a pick that filed nothing (a plain white): the clear of a FILED pick takes it back (_vpDrop) and is
     the undo laws' to grade - here only the plate is read */
  open(); plate('plain white', entryOf('Monarch', 0, false)); plate('cleared', null); close();
  /* the review's own pick: a 2os Warlock Tome (REG-2535) - it files to SOCKETED, or its plate says it was not saved */
  open(); plate('tome', entryOf('Tome', 2, false)); close();
}
OUT.res = res;
OUT.lock = W._laneLocked('Monarch (4os)');
})();
"""

_RUNS = {}


def run(scenario):
    if scenario not in _RUNS:
        pre = AUTOMATED + (LOCKED if scenario == "locked" else "")
        _RUNS[scenario] = VPN.run(BODY.replace("__SCENARIO__", json.dumps(scenario)), prelude=pre, timeout=300)
    return _RUNS[scenario]


def row(o, label):
    for r in o.get("res") or []:
        if r.get("label") == label:
            return r
    raise AssertionError("no plate %r in %r" % (label, o.get("res")))


SAVED, WAIT = "Saved into the vault", "Not in a locker yet"


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ThePlannerPlateSaysWhatThePickDid(unittest.TestCase):

    def test_0_premise_the_page_boots_and_the_lock_holds(self):
        for scenario in ("locked", "kept"):
            o = run(scenario)
            self.assertEqual(o["__boot"]["errors"], [], "%s: a page script did not run in node: %r" % (scenario, o["__boot"]))
        self.assertEqual(run("locked")["lock"], "equipment", "PREMISE: the 3-session lane lock does not hold the 4os Monarch")
        self.assertEqual(run("kept")["lock"], "", "PREMISE: the 4os Monarch is locked in the world where it should file")

    def test_1_a_refused_pick_never_reads_saved(self):
        """the review's shape: a refusal whose sentence says 'never filed to a mule'"""
        r = row(run("locked"), "locked monarch")
        self.assertFalse(r["writeOk"], "PREMISE: the door did not refuse the MAIN-locked pick: %r" % r)
        self.assertIsNone(r["home"], "PREMISE: the locked pick reached the mule map: %r" % r)
        self.assertIn("filed to", r["say"], "PREMISE: the refusal's sentence no longer says 'filed to' - this case would "
                                            "grade no regex: %r" % r)
        self.assertEqual(r["headline"], WAIT, "a refused pick reads as saved: %r" % r)
        self.assertTrue(r["wait"] and not r["saved"], "a refused pick wears the saved plate: %r" % r)

    def test_2_a_kept_pick_reads_saved(self):
        o = run("kept")
        for label in ("monarch", "monarch again", "monarch later"):
            r = row(o, label)
            self.assertTrue(r["writeOk"], r)
            self.assertEqual(r["home"], "bases", "PREMISE: the 4os Monarch is not filed: %r" % r)
            self.assertEqual(r["headline"], SAVED, "%s was kept and the plate does not say so: %r" % (label, r))
            self.assertTrue(r["saved"] and not r["wait"], r)
        self.assertIn("already filed", row(o, "monarch again")["say"], "PREMISE: the second save is not 'already filed'")
        self.assertIn("copy 2", row(o, "monarch later")["say"], "PREMISE: the later open did not count copy 2")

    def test_3_an_unfiled_or_cleared_pick_reads_not_in_a_locker(self):
        o = run("kept")
        for label in ("opened", "cleared", "plain white"):
            r = row(o, label)
            self.assertEqual(r["headline"], WAIT, "%s reads as saved: %r" % (label, r))
            self.assertTrue(r["wait"] and not r["saved"], r)
        self.assertIn("white, superior or low base", row(o, "plain white")["say"], "PREMISE: the plain white was not left unfiled")
        self.assertIn("the pick was cleared", row(o, "cleared")["say"])

    def test_4_a_2os_tome_files_to_socketed_or_its_plate_says_it_was_not_saved(self):
        """the review's law, as it asked for it: the plate agrees with the disk, and (REG-2535) the tome is filed"""
        r = row(run("kept"), "tome")
        self.assertEqual(r["saved"], r["tome"] is not None,
                         "the plate and the disk disagree about the 2os Tome: %r" % r)
        self.assertEqual(r["headline"], SAVED if r["tome"] else WAIT, r)
        self.assertEqual(r["tome"], "bases", "the 2os Tome was not filed to SOCKETED: %r" % r)


RED_PROOF = [
    {"why": "REG-2536 - the plate reads its headline off the sentence again, so a refusal that says 'never filed to a mule' "
            "reads 'Saved into the vault'",
     "file": "bible.html",
     "find": "    saved = (saved === true);\n",
     "replace": "    saved = /filed to|already filed/.test(s);\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2536 - the pick's result is not kept for the plate, so a pick that was kept never says it was saved",
     "file": "bible.html",
     "find": "      ctx.saved = !!(r && r.ok !== false && (r.filed === true || r.mode === 'already'));\n",
     "replace": "      ctx.saved = false;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
