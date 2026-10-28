# -*- coding: utf-8 -*-
"""#154 (REG-2832, GrokBot's #13 drive, #230 6462208498) - AN EDIT IN THE VAULT PLANNER IS ONE EDIT, FILED ONCE.

GrokBot opened the editor through Add an item (Monarch, Superior) and stepped its sockets. Each step filed the item and
took the previous copy back; the plate flipped NOT IN A LOCKER / SAVED under the cursor; the count only moved on blur.
Measured on the whole page in node, the same drive (pick Monarch, Superior, sockets 1 2 3 4 3 4, Done): every change in
the EDIT tab reached ctx.write and was filed - 3 'planner-take-back' batches (3os, 4os, 3os) went into the removal
journal, a 20-deep ring, for one edit, pushing his real removals out of reach of the undo.

Now a change made in the EDIT tab is held as a draft (ctx.hold), shown as the draft, and filed once when the edit ends:
Done or Esc or the close (vaultPlannerClose -> ctx.flush), or the next pick (ctx.write files the draft first). The pick
itself and a clear still file at once - REG-2536's plate reads that result, untouched. While a draft is held the plate
says Editing, never SAVED or NOT IN A LOCKER. In the planner the Sockets field is live (_cbEditLive on input), which is
safe because nothing is filed until Done. The repaint that keeps the field under the cursor is REG-2833 (Chrome law
test_the_planner_spinner_stays_under_the_cursor, CI proves it). RED_PROOF below.
"""
import io
import json
import os
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
import vault_page_node as VPN  # noqa: E402

PRELUDE = ("Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });\n"
           "localStorage.setItem('d2r_ownerClaim', '*');\n")

BODY = r"""
(function(){
var W = window;
try { W.renderVault(); } catch (e) {} H.flush(60, 3);
function log(){ var l = W.vaultRemovalLog(); return Array.isArray(l) ? l.map(function(b){ return (b.names || []).join(',') + '@' + b.lane; }) : l; }
function plate(){ var h = String((document.getElementById('vault-planner-host') || {}).innerHTML || '');
  var k = /<div class="vp-plate-k">([^<]*)<\/div>/.exec(h), sy = /<div class="vp-plate-say">([^<]*)<\/div>/.exec(h);
  return { k: k ? k[1] : null, say: sy ? sy[1] : null }; }
function filed(){ try { return JSON.parse(W.LSR.getItem('d2r_muleAssign') || '{}'); } catch (e) { return 'UNREADABLE'; } }
function draft(){ var s = W._cbState(), c = s && s.host && s.host.cur ? s.host.cur() : null; return c ? (c.sockets | 0) : null; }
var db = W._cbDb();
function code(name){ return Object.keys(db.b).find(function(c){ return db.b[c][0] === name; }); }
function monarch(){ W._cbChoose('b:' + code('Monarch')); H.flush(60, 3); W._cbQuality('sup'); H.flush(60, 3); }

/* 1 - GrokBot's drive: one edit, sockets stepped six times, then Done */
W.vaultPlannerOpen(''); monarch();
OUT.pickTab = W._cbState().pick && W._cbState().pick.tab;
OUT.steps = [];
[1, 2, 3, 4, 3, 4].forEach(function(n){
  W._cbEdit('sockets', String(n)); H.flush(60, 3);
  OUT.steps.push({ n: n, draft: draft(), plate: plate(), filed: filed(), journal: log().length });
});
W.vaultPlannerClose(); H.flush(60, 3);
OUT.done = { filed: filed(), owned: Array.from(owned), journal: log() };

/* 2 - the live field: an input in the planner moves the draft at once; an empty field is left alone */
W.vaultPlannerOpen(''); monarch();
OUT.live = { took: W._cbEditLive('sockets', { value: '3' }), draft: draft(), empty: W._cbEditLive('sockets', { value: '' }), after: draft(),
             filedDuring: filed() };
/* 3 - the next pick ends the edit: the Monarch draft is filed first, then the new pick */
var ug = db.it.find(function(x){ return x[1] === "Nightwing's Veil" && x[2] === 'u'; });
W._cbPickTab && W._cbPickTab('select');
W._cbChoose(ug[0]); H.flush(60, 3);
OUT.nextPick = { filed: filed(), journal: log().length };
W.vaultPlannerClose(); H.flush(60, 3);

/* 4 - a clear during an edit drops the draft: nothing is filed and nothing is journaled */
var before = JSON.stringify(filed()), jb = log().length;
W.vaultPlannerOpen(''); W._cbChoose('b:' + code('Archon Plate')); H.flush(60, 3); W._cbQuality('sup'); H.flush(60, 3);
W._cbEdit('sockets', '4'); H.flush(60, 3);
var s = W._cbState(); s.host.write(null); H.flush(60, 3);
W.vaultPlannerClose(); H.flush(60, 3);
OUT.cleared = { same: JSON.stringify(filed()) === before, journal: log().length - jb, archon: Object.keys(filed()).filter(function(k){ return /Archon/.test(k); }) };
OUT.outside = W._cbEditLive('sockets', { value: '2' });   /* no planner open: the builder and the mule keep their change event */
OUT.errors = H.errors.slice();
})();
"""


def _src():
    return io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8").read()


class APlannerEditIsOneEdit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])
        self.assertEqual(self.o["pickTab"], "edit", "PREMISE: the pick did not open the EDIT tab: %r" % self.o["pickTab"])

    def test_nothing_is_filed_or_journaled_while_he_edits(self):
        for st in self.o["steps"]:
            self.assertEqual(st["draft"], st["n"], "the draft did not follow the field: %r" % st)
            self.assertEqual(st["filed"], {}, "an edit step was filed mid-edit: %r" % st)
            self.assertEqual(st["journal"], 0, "an edit step put a copy in the removal journal: %r" % st)

    def test_the_plate_says_editing_never_saved_or_not_in_a_locker(self):
        for st in self.o["steps"]:
            self.assertEqual(st["plate"]["k"], "Editing", "the plate flipped mid-edit: %r" % st)
            self.assertIn("Superior Monarch", st["plate"]["say"] or "", st)
            self.assertIn("Done saves this edit", st["plate"]["say"] or "", st)

    def test_done_files_the_edit_once(self):
        d = self.o["done"]
        self.assertEqual(d["filed"], {"Superior Monarch (4os)": "bases"}, "Done did not file the edit as it ended: %r" % d)
        self.assertEqual(d["owned"], ["Superior Monarch (4os)"], d)
        self.assertEqual(d["journal"], [], "the edit left copies in the removal journal: %r" % d["journal"])

    def test_the_sockets_field_is_live_in_the_planner_only(self):
        lv = self.o["live"]
        self.assertTrue(lv["took"] and lv["draft"] == 3, "typing a count did not move the draft until blur: %r" % lv)
        self.assertFalse(lv["empty"], lv)
        self.assertEqual(lv["after"], 3, "an empty field mid-typing moved the draft: %r" % lv)
        self.assertEqual(lv["filedDuring"], {"Superior Monarch (4os)": "bases"}, "the live field filed: %r" % lv)
        self.assertFalse(self.o["outside"], "the live field acted with no planner open")
        s = _src()
        self.assertEqual(s.count("oninput=\"window._cbEditLive(\\'sockets\\', this)\""), 2, "a Sockets field is not live")

    def test_the_next_pick_files_the_draft_first(self):
        n = self.o["nextPick"]
        self.assertEqual(n["filed"].get("Superior Monarch (3os)"), "bases", "the draft was lost to the next pick: %r" % n)
        self.assertIn("Nightwing's Veil", n["filed"], "the next pick was not filed: %r" % n)
        self.assertEqual(n["journal"], 0, n)

    def test_a_clear_during_an_edit_files_nothing(self):
        c = self.o["cleared"]
        self.assertEqual((c["same"], c["journal"], c["archon"]), (True, 0, []), "a cleared draft was filed or journaled: %r" % c)


RED_PROOF = [
    {"why": "REG-2832 - every EDIT-tab change is filed again (the hold is never taken)",
     "file": "bible.html",
     "find": "      var wr = (st.host.planner && typeof st.host.hold === 'function' && st.pick.tab === 'edit' && _hEnt) ? st.host.hold(_hEnt)\n",
     "replace": "      var wr = (false) ? st.host.hold(_hEnt)\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2832 - Done closes without filing the edit",
     "file": "bible.html",
     "find": "    try { if (_cx && typeof _cx.flush === 'function') _fx = _cx.flush(); } catch (eF) {}\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2832 - the next pick throws the draft away",
     "file": "bible.html",
     "find": "        if (pending && entry) ctx.flush();           /* REG-2832 - the next pick ends the edit: its draft is filed first */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2832 - a clear files the draft before taking it back",
     "file": "bible.html",
     "find": "        if (pending && entry) ctx.flush();",
     "replace": "        if (pending) ctx.flush();",
     "matches": 1, "needs": "node"},
    {"why": "REG-2832 - the plate reads SAVED / NOT IN A LOCKER over a draft",
     "file": "bible.html",
     "find": "_vpPlateHtml(st.host.say, st.host.saved, st.host.pending ? st.host.editSay : '')",
     "replace": "_vpPlateHtml(st.host.say, st.host.saved, '')",
     "matches": 1, "needs": "node"},
    {"why": "REG-2832 - the Sockets field commits only on blur again",
     "file": "bible.html",
     "find": "    if (!(st.host && st.host.planner && st.pick && st.pick.host === 'mule')) return false;\n    var v = el ? el.value : null;\n",
     "replace": "    return false;\n    var v = el ? el.value : null;\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
