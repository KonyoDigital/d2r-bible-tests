# -*- coding: utf-8 -*-
"""#230 his done table (REG-2843) - A MOVE TASK TICKS ITSELF ON TWO SESSIONS AT ITS TARGET, BOTH READ AFTER IT OPENED.

A MOVE task verified on ONE sighting at its target cell (_vaultMoveWitness, atTo -> 'verified'), and a full look of the
target (_vaultGoneObserve) closed it at once too. His rule, from the design he approved: a task ticks itself on reads at its
target from 2 DISTINCT SESSIONS (VAULT_WITNESS_MIN; s_1 and its re-look s_1#2 are one, as _vaultLookSessions counts),
each captured AFTER the task opened, with no newer read placing it elsewhere. One such read leaves it open and half-way -
"seen at target once (date)". His own tick closes it at once. A full look of the target container is one session. A read
whose time cannot be told is not after anything, so it does not count. Driven on the whole page in node. RED_PROOF below.
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

BODY = r"""
(function(){
var W = window, OPEN = Date.parse('2026-10-28T10:00:00.000Z'), H1 = 3600e3;
var TO = { holder: 'UNI-ARMOR', location: 'stash', cell: 'stash:c0r0' }, FROM = { holder: 'MAIN', location: 'stash', cell: 'stash:c3r1' };
function task(extra){ var s = { name: 'Shako', status: 'to-move', manual: false, from: FROM, to: TO, evidence: [], opened: OPEN };
  for (var k in (extra || {})) s[k] = extra[k]; return W._vaultMoveTask(s); }
/* a read of session n at place p, captured at OPEN + h hours (h null = a read that carries no time) */
function read(p, n, h, re){ var ms = (h == null) ? null : OPEN + h * H1, sid = 'S' + n + (re ? '#2' : '');
  return { holder: p.holder, location: p.location, cell: p.cell, frame: 'f' + n + (re ? 'b' : ''), at: ms == null ? undefined : new Date(ms).toISOString(),
           sessions: [{ id: sid, frame: 'f' + n + (re ? 'b' : '') }] }; }
function st(t){ return { status: t.status, seen: (t.seen || []).length, half: W._vaultMoveHalfSay(t) }; }
var w = W._vaultMoveWitness;
/* 1 - one session at the target: half-way, still open */
var t1 = w(task(), read(TO, 1, 1));
OUT.one = st(t1);
/* 2 - its own re-look (S1#2) is the same session */
OUT.relook = st(w(t1, read(TO, 1, 2, true)));
/* 3 - a second session: verified */
var t3 = w(t1, read(TO, 2, 3));
OUT.two = st(t3);
/* 4 - reads OLDER than the task's opening do not count, however many */
OUT.older = st(w(w(task(), read(TO, 3, -5)), read(TO, 4, -2)));
/* 5 - a read whose time cannot be told does not count */
OUT.untimed = st(w(w(task(), read(TO, 5, null)), read(TO, 6, null)));
/* 6 - a NEWER read elsewhere reopens it: the half-way read is gone, and a verified task is open again */
OUT.reopenHalf = st(w(t1, read({ holder: 'MULE9', location: 'stash', cell: 'stash:c9r3' }, 7, 4)));
OUT.reopenDone = st(w(t3, read({ holder: 'MULE9', location: 'stash', cell: 'stash:c9r3' }, 8, 5)));
/* 7 - an OLDER read elsewhere changes nothing */
OUT.olderElse = st(w(t3, read({ holder: 'MULE9', location: 'stash', cell: 'stash:c9r3' }, 9, 2)));
/* 8 - his tick closes it at once, and one read at the target confirms it */
OUT.tick = st(w(W._vaultMoveTally(task()), read(TO, 10, 1)));
/* 9 - read once when it was first seen already at home: half-way (one session), not verified */
var h1 = w(task({ from: { holder: null, location: null, cell: null } }), read(TO, 11, 1));
OUT.home = st(h1);
OUT.home2 = st(w(h1, read(TO, 12, 2)));   /* FROM = TO now: a second session there closes it */
/* 10 - the shared session time: a reel id s_<start ms>_<n> dates its read */
var sidMs = OPEN + 2 * H1;
OUT.byId = st(w(w(task(), { holder: TO.holder, location: TO.location, cell: TO.cell, frame: 'g1', sessions: [{ id: 's_' + sidMs + '_1', frame: 'g1' }] }),
                 { holder: TO.holder, location: TO.location, cell: TO.cell, frame: 'g2', sessions: [{ id: 's_' + (sidMs + H1) + '_2', frame: 'g2' }] }));
/* 11 - the list draws the half-way words on the open row */
var html = W._vaultMoveHtml({ locks: [], groups: [{ label: 'MAIN', stash: 'Stash 1', rows: [{ name: 'Shako', copyIx: 0, task: t1, witnesses: 1 }] }] });
OUT.chip = (/<b class="vmv-half"[^>]*>([^<]*)<\/b>/.exec(html) || [])[1] || null;
/* 12 - a full look of the target container is one session (the drain's door), two close it */
var HC = 'Harlequin Crest (Shako)';
OUT.commit = W._vaultMoveCommit([{ name: HC, copyIx: 0, task: task({ name: HC }) }]);
function look(n, h){ return { session: 's_' + (OPEN + h * H1) + '_' + n, at: new Date(OPEN + h * H1).toISOString(), holder: TO.holder, location: TO.location,
                              items: [{ name: HC, cell: TO.cell }], ground: [] }; }
function saved(){ var raw = null; try { raw = JSON.parse(W.LSR.getItem('d2r_vaultRecords') || 'null'); } catch (e) {}
  var r = ((raw && raw.records) || []).filter(function(x){ return x.name === HC && (x.copyIx | 0) === 0; })[0];
  return (r && r.move) ? st(W._vaultMoveTask(r.move)) : null; }
OUT.fullBefore = saved();
W._vaultGoneObserve(look(1, 1)); OUT.full1 = saved();
W._vaultGoneObserve(look(2, 2)); OUT.full2 = saved();
OUT.errors = H.errors.slice();
})();
"""

PRELUDE = ("localStorage.setItem('d2r_ownerClaim', '*'); localStorage.setItem('d2r_vaultAutoIntake', 'on');\n"
           "localStorage.setItem('d2r_owned', %s);\n" % json.dumps(json.dumps(["Harlequin Crest (Shako)"]))
           + "localStorage.setItem('d2r_muleAssign', %s);\n" % json.dumps(json.dumps({"Harlequin Crest (Shako)": "uni-armor"})))


class AMoveClosesOnTwoSessionsAtItsTarget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])

    def test_one_session_is_half_way_and_still_open(self):
        self.assertEqual(self.o["one"], {"status": "to-move", "seen": 1, "half": "seen at target once (2026-10-28)"})
        self.assertEqual(self.o["relook"]["status"], "to-move", "a re-look of the same session closed it: %r" % self.o["relook"])
        self.assertEqual(self.o["relook"]["seen"], 1, self.o["relook"])

    def test_two_sessions_close_it(self):
        self.assertEqual(self.o["two"], {"status": "verified", "seen": 2, "half": ""})

    def test_a_read_from_before_the_task_opened_or_with_no_time_does_not_count(self):
        self.assertEqual(self.o["older"], {"status": "to-move", "seen": 0, "half": ""}, self.o["older"])
        self.assertEqual(self.o["untimed"], {"status": "to-move", "seen": 0, "half": ""}, self.o["untimed"])

    def test_a_newer_read_elsewhere_reopens_it(self):
        self.assertEqual((self.o["reopenHalf"]["status"], self.o["reopenHalf"]["seen"]), ("moved-elsewhere", 0), self.o["reopenHalf"])
        self.assertEqual((self.o["reopenDone"]["status"], self.o["reopenDone"]["seen"]), ("moved-elsewhere", 0), self.o["reopenDone"])

    def test_an_older_read_elsewhere_changes_nothing(self):
        self.assertEqual((self.o["olderElse"]["status"], self.o["olderElse"]["seen"]), ("verified", 2), self.o["olderElse"])

    def test_his_tick_closes_it_at_once(self):
        self.assertEqual(self.o["tick"]["status"], "verified", self.o["tick"])

    def test_first_seen_already_home_is_one_session(self):
        self.assertEqual((self.o["home"]["status"], self.o["home"]["seen"]), ("to-move", 1), self.o["home"])
        self.assertEqual((self.o["home2"]["status"], self.o["home2"]["seen"]), ("verified", 2), self.o["home2"])

    def test_a_reel_id_dates_its_read(self):
        self.assertEqual(self.o["byId"]["status"], "verified", self.o["byId"])

    def test_the_list_says_half_way(self):
        self.assertEqual(self.o["chip"], "seen at target once (2026-10-28)", self.o["chip"])

    def test_a_full_look_is_one_session(self):
        self.assertEqual((self.o["fullBefore"] or {}).get("status"), "to-move", "PREMISE: the task was not saved: %r" % self.o)
        self.assertEqual((self.o["full1"]["status"], self.o["full1"]["seen"]), ("to-move", 1), self.o["full1"])
        self.assertEqual(self.o["full2"]["status"], "verified", self.o["full2"])


RED_PROOF = [
    {"why": "REG-2843 - one sighting at the target verifies the task again",
     "file": "bible.html",
     "find": "      if (t.status === 'moved-manual' || _vaultMoveSeenAtTo(t, reads)) {\n",
     "replace": "      if (true) {\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - an item first read at its home (FROM = TO) is read 'still' at FROM for ever, so it never closes",
     "file": "bible.html",
     "find": "    if (atTo && (!atFrom || _vaultMoveSamePlace(t.from, t.to))) {\n",
     "replace": "    if (atTo && !atFrom) {\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - a re-look of one session counts as a second session",
     "file": "bible.html",
     "find": "      sid = String(sid).split('#')[0];\n      var at = _vmMs(l.at)",
     "replace": "      var at = _vmMs(l.at)",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - a read older than the task's opening counts",
     "file": "bible.html",
     "find": "      if (!r || !r.s || r.at == null || t.opened == null || r.at < t.opened) return;   /* older than its opening, or UNKNOWN */\n",
     "replace": "      if (!r || !r.s || r.at == null) return;   /* older than its opening, or UNKNOWN */\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - a newer read elsewhere leaves its reads at the target standing",
     "file": "bible.html",
     "find": "    if (nt != null && rt != null && rt < nt) return t;\n    delete t.seen;\n",
     "replace": "    if (nt != null && rt != null && rt < nt) return t;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - an older read elsewhere reopens a verified task",
     "file": "bible.html",
     "find": "    if (nt != null && rt != null && rt < nt) return t;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - a full look of the target closes the task at once again",
     "file": "bible.html",
     "find": "        if (next.status === 'moved-manual' || _vaultMoveSeenAtTo(next, [{ s: _fs, at: _fa, frame: frame.frame ? String(frame.frame) : null }])) {\n",
     "replace": "        if (true) {\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - the open row does not say it is half-way",
     "file": "bible.html",
     "find": "        + (hw ? '<b class=\"vmv-half\" title=\"' + esc(hw) + ' - one more session there closes it\">' + esc(hw) + '</b>' : '')   /* REG-2843 half-way */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2843 - a reel id's start time is not read, so a read with no other time never counts",
     "file": "bible.html",
     "find": "      if (at == null && m) at = +m[1];\n      if (!by[sid]",
     "replace": "      if (!by[sid]",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
