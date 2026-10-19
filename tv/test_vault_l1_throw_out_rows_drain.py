# -*- coding: utf-8 -*-
"""Vault L1 - a junk route is a THROW OUT row in MOVE TASKS, and every row drains on direct proof only.

Elad, 2026-10-20, at his live Vault: throw-out suggestions leave the Unsorted Dock. They are THROW OUT rows next to
the moves, target NOWHERE, one plain reason ("set never ruled"), Keep / Junk inline. Keep turns the row into a normal
move. The dock keeps only items with no route. A hand-added unruled set piece stays kept and routed (his ruling), so
it is never a THROW OUT row.

The drain (same pipeline, closed by sighting):
  - a move seen in its TARGET cell closes at once;
  - a row whose item is missing from its first-witnessed cell closes only after 5 reel sessions in which a frame
    actually SHOWED that cell without the item; a session whose frames never show that container counts nothing;
  - a re-sighting at that cell resets the count; the row says "gone k/5";
  - a throw-out whose item already left its cell and is then read as a dropped-item label on the ground closes at once.
Driven on the SHIPPED page through window._vaultGoneObserve. NO CHROME = a declared skip. RED_PROOF below.
[[regression-guard]] [[unknown-stays-unknown]]
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402

_B = {}
HEAD = "Arcanna's Head (helm)"     # screenshot-seen, the rules default it to junk (set never ruled)
SHAKO = "Harlequin Crest (Shako)"  # screenshot-seen, routed to the shared stash
SOJ = "The Stone of Jordan"        # seen on the equipment
SIGN = "Arcanna's Sign"            # hand-added unruled set piece: kept and routed


def _prov(holder, loc, cell, n=2):
    return {"kind": "owned", "source": "tv", "seen": n,
            "looks": [{"session": "w%d" % i, "frame": "f%d" % i, "holder": holder, "loc": loc, "cell": cell} for i in range(n)]}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def world():
    board().seed({"d2r_owned": [HEAD, SHAKO, SOJ], "d2r_muleAssign": {}, "d2r_vaultRecords": None,
                  "d2r_vaultProv": {HEAD: _prov("MAIN", "stash", "c0r0"), SHAKO: _prov("MAIN", "stash", "c4r0"),
                                    SOJ: _prov("MAIN", "equipment", "c0r0")}})
    return board().run("window._vaultAutoIntakeSet(false); window.vaultHandAdd(%s); window.switchTab('vault');"
                       "window._vaultMovePaint(); OUT.ok = 1;" % json.dumps(SIGN))


READ = r"""
function bag(){ var m = {}; try { (JSON.parse(LSR.getItem('d2r_vaultRecords') || '{}').records || []).forEach(function(r){ if (r.move) m[r.name] = r.move; }); } catch (e) {} return m; }
function row(nm){ var l = document.getElementById('vault-move-list'); return l ? l.querySelector('.vmv-row[data-name="' + nm.replace(/"/g, '\\"') + '"]') : null; }
function obs(f){ return window._vaultGoneObserve(f); }
"""


def frame(session, holder="MAIN", location="stash", items=(), ground=()):
    return json.dumps({"session": session, "holder": holder, "location": location,
                       "items": [{"name": n, "cell": c} for n, c in items], "ground": list(ground)})


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class ThrowOutRows(unittest.TestCase):

    def test_a_junk_route_is_a_throw_out_row_not_a_dock_chip(self):
        world()
        o = board().run(READ + "var r = row(%s); OUT.has = !!r; OUT.kind = r && r.getAttribute('data-kind');"
                        "OUT.text = r ? r.textContent : ''; OUT.keep = !!(r && r.querySelector('.vmv-keep'));"
                        "OUT.junk = !!(r && r.querySelector('.vmv-junk')); OUT.dock = window._vaultDockNames();"
                        "OUT.org = (document.getElementById('vault-organize') || {}).textContent || '';"
                        "OUT.list = document.getElementById('vault-move-list').textContent;" % json.dumps(HEAD))
        self.assertTrue(o["has"], "no THROW OUT row for the screenshot-seen junk item")
        self.assertEqual(o["kind"], "throw")
        self.assertIn("NOWHERE", o["text"])
        self.assertIn("set never ruled", o["text"])
        self.assertNotIn("by DEFAULT", o["list"], "the wordy throw-out advice is back in MOVE TASKS")
        self.assertTrue(o["keep"] and o["junk"], "Keep / Junk are not inline on the row")
        self.assertNotIn(HEAD, o["dock"] or [], "the junk item still sits in the Unsorted Dock")
        self.assertNotIn("throw-out advice", o["org"], "the organizer still prints throw-out advice")

    def test_his_hand_added_unruled_set_piece_is_never_a_throw_out_row(self):
        world()
        o = board().run(READ + "var r = row(\"Arcanna's Sign (amulet)\"); OUT.kind = r && r.getAttribute('data-kind');"
                        "OUT.to = (bag()[\"Arcanna's Sign (amulet)\"] || {}).to;")
        self.assertIsNone(o["kind"], "his hand add became a THROW OUT row")
        self.assertEqual((o["to"] or {}).get("holder"), "SETS-REST")

    def test_keep_turns_the_row_into_a_normal_move(self):
        world()
        o = board().run(READ + "window._vaultThrowKeep(%s, 0); var m = bag()[%s]; OUT.m = m; var r = row(%s);"
                        "OUT.kind = r && r.getAttribute('data-kind'); OUT.status = r && r.getAttribute('data-status');"
                        % (json.dumps(HEAD), json.dumps(HEAD), json.dumps(HEAD)))
        self.assertNotEqual(o["m"].get("kind"), "throw", o["m"])
        self.assertTrue(o["m"].get("kept"), o["m"])
        self.assertTrue(o["m"]["to"]["cell"], "Keep left no target cell: %r" % o["m"])
        self.assertIsNone(o["kind"])
        self.assertEqual(o["status"], "to-move")

    def test_junk_confirms_and_the_row_stays_until_drained(self):
        world()
        o = board().run(READ + "window._vaultThrowJunk(%s, 0); OUT.m = bag()[%s]; var r = row(%s); OUT.j = r && r.getAttribute('data-junk');"
                        % (json.dumps(HEAD), json.dumps(HEAD), json.dumps(HEAD)))
        self.assertTrue(o["m"].get("junk"))
        self.assertEqual(o["j"], "1")


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class TheDrain(unittest.TestCase):

    def test_five_sessions_of_direct_proof_close_a_throw_out_with_progress(self):
        world()
        js = READ
        for i in range(1, 5):
            js += "obs(%s);" % frame("s%d" % i)
        js += "var r = row(%s); OUT.say4 = r ? r.textContent : null; OUT.m4 = bag()[%s];" % (json.dumps(HEAD), json.dumps(HEAD))
        js += "obs(%s); OUT.m4b = bag()[%s];" % (frame("s4"), json.dumps(HEAD))  # same session again: still 4
        js += "obs(%s); OUT.m5 = bag()[%s]; OUT.row5 = !!row(%s);" % (frame("s5"), json.dumps(HEAD), json.dumps(HEAD))
        o = board().run(js)
        self.assertIn("gone 4/5", o["say4"] or "", "the row does not show its drain progress")
        self.assertEqual(o["m4"]["status"], "to-move")
        self.assertEqual(len(o["m4b"]["gone"]), 4, "one session counted twice")
        self.assertEqual(o["m5"]["status"], "closed", o["m5"])
        self.assertFalse(o["row5"], "a drained row is still on the list")

    def test_container_not_shown_so_no_count(self):
        world()
        js = READ
        for i in range(1, 9):
            js += "obs(%s);" % frame("x%d" % i, holder="SOME-MULE")       # another container entirely
            js += "obs(%s);" % frame("y%d" % i, location="inventory")    # same holder, other container
        js += "OUT.m = bag()[%s];" % json.dumps(HEAD)
        o = board().run(js)
        self.assertEqual(o["m"].get("gone"), None, "a session that never showed the cell was counted: %r" % o["m"])
        self.assertEqual(o["m"]["status"], "to-move")

    def test_a_re_sighting_resets_the_count(self):
        world()
        js = READ
        for i in range(1, 5):
            js += "obs(%s);" % frame("s%d" % i)
        js += "obs(%s);" % frame("s5", items=[(HEAD, "c0r0")])
        js += "OUT.m = bag()[%s];" % json.dumps(HEAD)
        o = board().run(js)
        self.assertEqual(o["m"].get("gone"), None, o["m"])
        self.assertEqual(o["m"]["status"], "to-move")

    def test_seen_on_the_ground_after_leaving_closes_a_throw_out_at_once(self):
        world()
        js = READ
        js += "obs(%s); OUT.before = bag()[%s].status;" % (frame("g0", holder="ELSEWHERE", ground=[HEAD]), json.dumps(HEAD))
        js += "obs(%s); obs(%s); OUT.m = bag()[%s];" % (frame("g1"), frame("g2", holder="ELSEWHERE", location="ground", ground=[HEAD]), json.dumps(HEAD))
        o = board().run(js)
        self.assertEqual(o["before"], "to-move", "a ground label before the item left its cell closed the row")
        self.assertEqual(o["m"]["status"], "closed")
        self.assertEqual(o["m"].get("closedBy"), "seen on the ground")

    def test_a_move_seen_at_its_target_closes_at_once(self):
        world()
        o = board().run(READ + "var t = bag()[%s].to; OUT.to = t; obs({ session: 'm1', holder: t.holder, location: t.location,"
                        " items: [{ name: %s, cell: t.cell }] }); OUT.m = bag()[%s];"
                        % (json.dumps(SHAKO), json.dumps(SHAKO), json.dumps(SHAKO)))
        self.assertEqual(o["m"]["status"], "verified", o)

    def test_a_vanished_move_drains_after_five_sessions(self):
        world()
        js = READ
        for i in range(1, 6):
            js += "obs(%s);" % frame("v%d" % i, items=[(HEAD, "c0r0")])  # HEAD still there, SHAKO gone from c4r0
            if i == 2:
                js += "var r = row(%s); OUT.say2 = r ? r.textContent : null;" % json.dumps(SHAKO)
        js += "OUT.m = bag()[%s]; OUT.h = bag()[%s];" % (json.dumps(SHAKO), json.dumps(HEAD))
        o = board().run(js)
        self.assertIn("gone 2/5", o["say2"] or "")
        self.assertEqual(o["m"]["status"], "closed", o["m"])
        self.assertEqual(o["h"].get("gone"), None, "the item still in its cell was counted gone")

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("vault L1 throw-out + drain: %d distinct attacks, wilson %.4f vs bar %.3f; kinds %.2f vs %.2f"
               % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar, msg)


RED_PROOF = [
    {"why": "A junk route goes back to the dock instead of a THROW OUT row.",
     "file": "bible.html",
     "find": "? _vaultThrowTask(r, stored) : null;\n",
     "replace": "? null : null;\n",
     "matches": 1},
    {"why": "The row loses its plain reason and prints the wordy DEFAULT advice.",
     "file": "bible.html",
     "find": "    if (/never ruled/i.test(w)) return /\\(set\\)/i.test(w) ? 'set never ruled' : 'never ruled';\n",
     "replace": "    if (/never ruled/i.test(w)) return w;\n",
     "matches": 1},
    {"why": "The dock keeps a junk-routed item as a chip.",
     "file": "bible.html",
     "find": "if (_sgD && _sgD.id === '__throwout') return false; } catch (eSgD) {}",
     "replace": "if (false) return false; } catch (eSgD) {}",
     "matches": 1},
    {"why": "Keep stays a THROW OUT row.",
     "file": "bible.html",
     "find": "if (sg.id === '__throwout' && typeof window._vaultKeptByHim === 'function' && window._vaultKeptByHim(name)) {",
     "replace": "if (sg.id === '__throwout' && typeof window._vaultKeptByHim === 'function' && false) {",
     "matches": 1},
    {"why": "A hand-added unruled set piece becomes a THROW OUT row (his ruling: kept and routed).",
     "file": "bible.html",
     "find": "window._vaultHandTyped(name) && typeof muleById === 'function' && muleById('sets-rest'))",
     "replace": "false)",
     "matches": 1},
    {"why": "A frame that never showed the container counts a session.",
     "file": "bible.html",
     "find": "      } else if (shows(t.from)) {\n",
     "replace": "      } else if (t.from && t.from.cell != null) {\n",
     "matches": 1},
    {"why": "A re-sighting no longer resets the count.",
     "file": "bible.html",
     "find": "        if (here(name, t.from.cell)) { if (t.gone || t.left) { next = _vaultMoveTask(t); delete next.gone; delete next.left; } }\n",
     "replace": "        if (here(name, t.from.cell)) { }\n",
     "matches": 1},
    {"why": "The row closes after one missing frame instead of five sessions.",
     "file": "bible.html",
     "find": "  var VAULT_GONE_SESSIONS = 5;\n",
     "replace": "  var VAULT_GONE_SESSIONS = 1;\n",
     "matches": 1},
    {"why": "The same session counts twice.",
     "file": "bible.html",
     "find": "var g = (next.gone || []).slice(); if (g.indexOf(sid) < 0) g.push(sid); next.gone = g;",
     "replace": "var g = (next.gone || []).slice(); g.push(sid + g.length); next.gone = g;",
     "matches": 1},
    {"why": "A ground label closes a throw-out before the item left its cell.",
     "file": "bible.html",
     "find": "if (cur.kind === 'throw' && cur.status !== 'closed' && cur.left && ground.indexOf(name) >= 0) {",
     "replace": "if (cur.kind === 'throw' && cur.status !== 'closed' && ground.indexOf(name) >= 0) {",
     "matches": 1},
    {"why": "A move seen at its target no longer closes at once.",
     "file": "bible.html",
     "find": "      if (t.kind !== 'throw' && shows(t.to) && here(name, t.to.cell)) {\n",
     "replace": "      if (false) {\n",
     "matches": 1},
    {"why": "The row hides its drain progress.",
     "file": "bible.html",
     "find": "    return n ? ('gone ' + n + '/' + VAULT_GONE_SESSIONS) : '';\n",
     "replace": "    return '';\n",
     "matches": 1},
    {"why": "Keep/Junk buttons leave the THROW OUT row.",
     "file": "bible.html",
     "find": "             : '<button type=\"button\" class=\"vault-btn vmv-keep\"",
     "replace": "             : '<span hidden class=\"x-keep\"",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
