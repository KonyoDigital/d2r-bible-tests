# -*- coding: utf-8 -*-
"""#154 front-run (REG-2840, REG-2841) - HIS HAND ON AN ITEM THE VAULT ALREADY HOLDS: A DOUBT BECOMES A QUESTION.

His words (2026-10-28 19:25), looking at a Vault the reels had filled: "to do my frontrun.. i have to wipe the items and
then do them one by one ... but wont these keep coming back? like we need to have some joineded logic here". Typing a
name he already held made ANOTHER copy (L1), so the Shako the reels read, typed by hand, became two Shakos. Now the two
hand surfaces ask - the add-by-name pick (vaultHandTake) and the planner's pick (the plate) - with each copy named by how
it came and where it is, and "Another copy":
  * "the same item" adds no copy: that copy's looks, history and move stay, and his hand (with the mods he typed) is
    recorded on its witness row - one more witness (window.vaultHandJoin);
  * "another copy" files one, and it carries what he typed;
  * he owns 0 -> a plain add, no question; his typed mods plainly differ from the recorded mods of every copy -> another
    copy, no question (settled when his edit ends - at the pick nothing is typed yet);
  * Done over an unanswered question does not close and files nothing: never a guess.
The doors (vaultHandAdd, vaultPlannerFile) still count what a caller tells them. Driven on the whole page in node, AUTO
on, after a reel read through tvVaultRegister. RED_PROOF below.
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

PRELUDE = ("Object.defineProperty(navigator, 'webdriver', { get: function(){ return true; }, configurable: true });\n"
           "localStorage.setItem('d2r_ownerClaim', '*'); localStorage.setItem('d2r_vaultAutoIntake', 'on');\n")

BODY = r"""
(function(){
var W = window, DB = W._cbDb(), N = "Harlequin Crest (Shako)";
function runeId(n){ var r = DB.sk.find(function(s){ return String(s[1] || '').toLowerCase() === (n + ' rune').toLowerCase() || String(s[1] || '').toLowerCase() === n.toLowerCase(); }); return r ? r[0] : null; }
function plate(){ var h = String((document.getElementById('vault-planner-host') || {}).innerHTML || '');
  var k = /<div class="vp-plate-k">([^<]*)<\/div>/.exec(h); return { k: k ? k[1] : null, choices: (h.match(/vp-plate-choice"/g) || []).length, html: h.slice(0, 0) }; }
function row(){ try { return JSON.parse(W.LSR.getItem('d2r_vaultProv') || '{}')[N] || null; } catch (e) { return 'UNREADABLE'; } }
function hands(){ var r = row(); var a = []; [r, r && r.ownedBy].forEach(function(x){ if (x && Array.isArray(x.hands)) a = a.concat(x.hands); }); return a; }
function journal(){ var l = W.vaultRemovalLog(); return Array.isArray(l) ? l.length : l; }
function moveOf(k){ var raw = null; try { raw = JSON.parse(W.LSR.getItem('d2r_vaultRecords') || 'null'); } catch (e) {}
  var r = ((raw && raw.records) || []).filter(function(x){ return x.name === N && (x.copyIx | 0) === k; })[0]; return r && r.move ? JSON.stringify(r.move) : null; }
var SH = DB.it.find(function(x){ return x[1] === 'Harlequin Crest' && x[2] === 'u'; });
/* 0 - the reels read his Shako */
var cell = { x: 3, y: 2, container: 'stash' };
var rg = W.tvVaultRegister('Harlequin Crest', { by: 'tv-register', lane: 'stash', loc: 'stash', scene: 'stash', holder: 'MULE1', at: '2026-10-27T08:00:00.000Z', cell: cell,
                                                sessions: [{ session: 'r1', frame: 'r1_f', lane: 'stash', conf: 0.9, cell: cell, holder: 'MULE1' }, { session: 'r2', frame: 'r2_f', lane: 'stash', conf: 0.9, cell: cell, holder: 'MULE1' }] });   /* the sweep's own witness shape */
H.flush(60, 3); try { W.renderVault(); } catch (e) {} H.flush(60, 3);
OUT.read = { ok: !!(rg && rg.ok), copies: copyCount(N), looks: ((row() || {}).looks || []).length, choices: W._vaultCopyChoices(N) };
var looks0 = JSON.stringify((row() || {}).looks || []), move0 = moveOf(0);
/* 1 - + Add an item, by name */
W.vaultHandOpen(); W.vaultHandSearch('Harlequin');
var hr = ((W._vhCat && W._vhCat.rows) || []).filter(function(r){ return r.name === 'Harlequin Crest'; })[0];
var a1 = W.vaultHandTake(hr.id);
OUT.byName = { mode: a1 && a1.mode, copies: copyCount(N), say: String((document.getElementById('vault-hand-say') || {}).innerHTML || '') };
var a2 = W.vaultHandTake(hr.id, 0);
OUT.byNameSame = { mode: a2 && a2.mode, copies: copyCount(N), hands: hands().length, looksKept: JSON.stringify((row() || {}).looks || []) === looks0, moveKept: moveOf(0) === move0 };
W.vaultHandClose();
/* 2 - the planner: the pick asks, his runes go on the copy he names */
W.vaultPlannerOpen(''); W._cbChoose(SH[0]); H.flush(60, 3);
OUT.pick = { plate: plate(), copies: copyCount(N) };
W._cbEdit('sockets', '1'); W._cbSocket(0, runeId('Ist')); H.flush(60, 3);
OUT.editing = { plate: plate().k, copies: copyCount(N) };
var ans = W.vaultPlannerAnswer(0); H.flush(60, 3);
var hs = hands(), last = hs[hs.length - 1] || {};
OUT.plannerSame = { mode: ans && ans.mode, copies: copyCount(N), hands: hs.length, lastBy: last.by, lastSocketed: (last.entry && last.entry.socketed) || null,
                    journal: journal(), looksKept: JSON.stringify((row() || {}).looks || []) === looks0, moveKept: moveOf(0) === move0 };
OUT.closed1 = W.vaultPlannerClose() !== false; H.flush(60, 3);
/* 3 - the same runes as copy 0 (Ist) are a real doubt: Done files nothing and does not close; "Another copy" files one carrying them */
W.vaultPlannerOpen(''); W._cbChoose(SH[0]); H.flush(60, 3);
W._cbEdit('sockets', '1'); W._cbSocket(0, runeId('Ist')); H.flush(60, 3);
var c3 = W.vaultPlannerClose(); H.flush(60, 3);
OUT.doneAsked = { closed: c3 !== false, copies: copyCount(N), plate: plate().k };
W.vaultPlannerAnswer('copy'); H.flush(60, 3);
var hs3 = hands(), l3 = hs3[hs3.length - 1] || {};
OUT.another = { copies: copyCount(N), lastCopy: l3.copyIx, lastSocketed: (l3.entry && l3.entry.socketed) || null };
W.vaultPlannerClose(); H.flush(60, 3);
/* 4 - every copy now has recorded mods (Ist on 0, Ist on 1): runes that plainly differ are another copy, no question */
W.vaultPlannerOpen(''); W._cbChoose(SH[0]); H.flush(60, 3);
OUT.pick4 = plate().k;
W._cbEdit('sockets', '1'); W._cbSocket(0, runeId('Lum')); H.flush(60, 3);
var c4 = W.vaultPlannerClose(); H.flush(60, 3);
OUT.differ = { closed: c4 !== false, copies: copyCount(N) };
/* 4b - a bare pick (nothing typed) tells copies apart by nothing: Done asks, even though every copy has recorded mods */
W.vaultPlannerOpen(''); W._cbChoose(SH[0]); H.flush(60, 3);
var c4b = W.vaultPlannerClose(); H.flush(60, 3);
OUT.bare = { closed: c4b !== false, copies: copyCount(N), plate: plate().k };
W.vaultPlannerAnswer(0); H.flush(60, 3); W.vaultPlannerClose(); H.flush(60, 3);
OUT.bareJoined = copyCount(N);
/* 5 - he owns none: a plain add, no question */
var NW = DB.it.find(function(x){ return x[1] === "Nightwing's Veil" && x[2] === 'u'; });
W.vaultPlannerOpen(''); W._cbChoose(NW[0]); H.flush(60, 3);
OUT.plain = { plate: plate().k, owned: owned.has("Nightwing's Veil") };
W.vaultPlannerClose(); H.flush(60, 3);
/* 6 - a new pick over an unanswered question files nothing for the first, and says so */
var AV = DB.it.find(function(x){ return x[1] === "Andariel's Visage" && x[2] === 'u'; });
W.vaultPlannerOpen(''); W._cbChoose(SH[0]); H.flush(60, 3); W._cbPickTab('select'); W._cbChoose(AV[0]); H.flush(60, 3);   /* back to Select, as his tab click does */
OUT.moved = { copies: copyCount(N), say: String(window._cbState().host.say || ''), av: owned.has("Andariel's Visage") };
W.vaultPlannerClose(); H.flush(60, 3);
/* 7 - the question follows the name his edit makes: a 4os Superior Monarch he holds is asked; taken to 3 sockets it is a
   name he does not hold, so the question goes and Done files it */
var MC = Object.keys(DB.b).find(function(c){ return DB.b[c][0] === 'Monarch'; }), M4 = 'Superior Monarch (4os)', M3 = 'Superior Monarch (3os)';
W.vaultPlannerOpen(''); W._cbChoose('b:' + MC); W._cbQuality('sup'); W._cbEdit('sockets', '4'); W.vaultPlannerClose(); H.flush(60, 3);
W.vaultPlannerOpen(''); W._cbChoose('b:' + MC); W._cbQuality('sup'); W._cbEdit('sockets', '4'); H.flush(60, 3);
var c7 = W.vaultPlannerClose(); H.flush(60, 3);
OUT.rename = { asked: c7 === false, plate: plate().k };
W._cbEdit('sockets', '3'); H.flush(60, 3);
OUT.rename.plate3 = plate().k;
OUT.rename.closed = W.vaultPlannerClose() !== false; H.flush(60, 3);
OUT.rename.m4 = copyCount(M4); OUT.rename.m3 = owned.has(M3);
OUT.errors = H.errors.slice();
})();
"""


class AHandEntryOfAnItemAlreadyHereAsks(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted_and_the_reels_read_it(self):
        o = self.o
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual(o["errors"], [])
        r = o["read"]
        self.assertTrue(r["ok"] and r["copies"] == 1 and r["looks"] >= 1, "PREMISE: the reel read did not land: %r" % r)
        self.assertEqual([(c["copyIx"], c["how"]) for c in r["choices"]], [(0, "read")], r)

    def test_typing_its_name_asks_instead_of_making_a_second(self):
        b = self.o["byName"]
        self.assertEqual((b["mode"], b["copies"]), ("ask", 1), "typing a name he holds made another copy: %r" % b)
        self.assertIn("Same item as the one read on 2026-10-27", b["say"], b)
        self.assertIn("Another copy", b["say"], b)

    def test_the_same_item_keeps_its_looks_and_move_and_takes_his_hand(self):
        s = self.o["byNameSame"]
        self.assertEqual((s["mode"], s["copies"], s["hands"]), ("joined", 1, 1), s)
        self.assertTrue(s["looksKept"] and s["moveKept"], "the join touched the copy's looks or move: %r" % s)

    def test_the_planner_pick_asks_and_his_runes_go_on_the_copy_he_names(self):
        p, e, s = self.o["pick"], self.o["editing"], self.o["plannerSame"]
        self.assertEqual((p["plate"]["k"], p["plate"]["choices"], p["copies"]), ("Same item?", 2, 1), p)
        self.assertEqual((e["plate"], e["copies"]), ("Same item?", 1), "an edit under the question filed or lost it: %r" % e)
        self.assertEqual((s["mode"], s["copies"], s["hands"], s["lastBy"]), ("joined", 1, 2, "the Vault planner"), s)
        self.assertEqual(len(s["lastSocketed"] or []), 1, "his runes were not recorded on the copy: %r" % s)
        self.assertEqual(s["journal"], 0, s)
        self.assertTrue(s["looksKept"] and s["moveKept"], s)
        self.assertTrue(self.o["closed1"])

    def test_done_over_an_open_question_files_nothing(self):
        d = self.o["doneAsked"]
        self.assertEqual((d["closed"], d["copies"], d["plate"]), (False, 1, "Same item?"), "Done guessed: %r" % d)

    def test_another_copy_files_one_carrying_his_mods(self):
        a = self.o["another"]
        self.assertEqual((a["copies"], a["lastCopy"]), (2, 1), a)
        self.assertEqual(len(a["lastSocketed"] or []), 1, a)

    def test_mods_that_plainly_differ_from_every_copy_are_another_copy(self):
        self.assertEqual(self.o["pick4"], "Same item?", "the pick decided before his mods were typed")
        d = self.o["differ"]
        self.assertEqual((d["closed"], d["copies"]), (True, 3), "plainly different runes were asked or lost: %r" % d)

    def test_a_bare_pick_is_asked_not_counted(self):
        b = self.o["bare"]
        self.assertEqual((b["closed"], b["copies"], b["plate"]), (False, 3, "Same item?"), "a pick with nothing typed was taken as another copy: %r" % b)
        self.assertEqual(self.o["bareJoined"], 3, "answering 'the same item' added a copy")

    def test_a_new_pick_over_an_open_question_says_the_first_was_not_filed(self):
        m = self.o["moved"]
        self.assertEqual((m["copies"], m["av"]), (3, True), m)
        self.assertIn("nothing was filed for Harlequin Crest (Shako) (its question was not answered)", m["say"], m)

    def test_the_question_follows_the_name_his_edit_makes(self):
        r = self.o["rename"]
        self.assertEqual((r["asked"], r["plate"]), (True, "Same item?"), "PREMISE: a 4os base he holds was not asked: %r" % r)
        self.assertEqual(r["plate3"], "Editing", "an edit to a name he does not hold was still asked by the old name: %r" % r)
        self.assertEqual((r["closed"], r["m4"], r["m3"]), (True, 1, True), r)

    def test_an_item_he_does_not_hold_is_a_plain_add(self):
        p = self.o["plain"]
        self.assertTrue(p["owned"], p)
        self.assertNotEqual(p["plate"], "Same item?", p)


RED_PROOF = [
    {"why": "REG-2840 - typing a name he holds makes a second copy again (the add-by-name window never asks)",
     "file": "bible.html",
     "find": "    if (row && row.name && _ans !== 'copy' && typeof window._vaultJoinAsk === 'function' && typeof _vhPrepare === 'function'){\n",
     "replace": "    if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2841 - the planner's pick of a name he holds files a copy again",
     "file": "bible.html",
     "find": "      if (_jq && _jq.ask) return { ok: true, filed: false, mode: 'ask', name: nm, choices: _jq.choices, why: _jq.why };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2841 - Done closes over an unanswered question",
     "file": "bible.html",
     "find": "    if (_fx && _fx.mode === 'ask'){\n",
     "replace": "    if (false){\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2840 - 'the same item' records no hand on the copy",
     "file": "bible.html",
     "find": "    row.hands = (Array.isArray(row.hands) ? row.hands : []).concat([mark]);\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2840 - mods that plainly differ are still asked",
     "file": "bible.html",
     "find": "      return { ask: false, decision: 'copy', why: 'its mods differ from the recorded mods of every copy here' };\n",
     "replace": "      return { ask: true, choices: ch, why: 'asked' };\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2841 - a bare pick (nothing typed) is taken as plainly different: Done files another copy",
     "file": "bible.html",
     "find": "    var sig = _vaultEntryTyped(entry) ? _vaultEntrySig(entry) : '';\n",
     "replace": "    var sig = entry ? _vaultEntrySig(entry) : '';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2841 - a new pick over an unanswered question drops the first in silence",
     "file": "bible.html",
     "find": "        if (_unans) ctx.say = 'nothing was filed for ' + _unans + ' (its question was not answered) - ' + ctx.say;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2841 - an edit that turns the pick into a name he does not hold is still asked by the old name",
     "file": "bible.html",
     "find": "          if (dq && dq.mode === 'ask'){ ctx.question = { name: dq.name, choices: dq.choices, why: dq.why }; ctx.say = dq.why; return { ok: true, held: true, why: dq.why }; }\n          ctx.question = null;\n",
     "replace": "          return { ok: true, held: true, why: ctx.question.why };\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
