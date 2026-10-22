# -*- coding: utf-8 -*-
"""REG-2521 FIX ROUND (V1 round 3; the review of REG-2521, major + minor) - THE SOCKET DOORS, THE CELL ✕ AND THE MULE
WINDOW ASK THE HOLD BEFORE ANYTHING IS DROPPED, AND NEVER ANSWER OK OVER A FILING THE DOOR REFUSED.

REG-2521 made vaultFile refuse at its top while a store the vault stands on (VAULT_BASIS) is held, and added Magic & Rare
to that basis. The socket fix walked past the refusal: vaultFixSockets dropped the old label's filing and its witness row
FIRST (owned.delete, delete assign[name], _provDrop), then asked vaultFile to put them back - refused. Reviewer (p3, on
the track head): owned [Grief, Monarch (Larzuk base)], map {Monarch (Larzuk base): bases}, a 2-look stash row on it,
d2r_magicFinds or d2r_copies cut short -> d2r_vaultProv on disk {} (the row gone for good), nothing under 'Monarch (4os)',
the map in memory {Grief:uni-weap}, d2r_owned ["Grief","Monarch (4os)"], status '🔩 Monarch → 4 sockets — fixed'; once the
hold lifts the W6 prune drops the stale old-label filing. A regression from the merge base, where the same click carried
the row across. And vaultSetSockets / vaultKeepAsBase said "registered" / "kept" over a filing vaultFile refused, the cell
✕ (vaultUnassign) demoted the witness row, had its saveA refused and answered {ok:true}, and the mule window said a
vaultFile refusal only for 'hardened' or 'prov-unreadable'.

NOW: the three socket doors ask window._vaultBasisHeld() first and wait, in words, touching nothing; the socket fix
refiles the NEW label before it lets go of the old one, so a refile the door refuses for any reason (a MAIN lock on the
new label) leaves the old label, its filing and its row as they were - said, never "fixed"; the throw-out doors say a
filing the door refused; the ✕ asks the hold, writes the map before it demotes the row, and never answers ok over a
refused saveA; the mule window says a 'held' or 'not-written' refusal too.

WHAT IS DRIVEN: the store door, the boot, the tab sync, the vault module's head and its whole filing block
(store_door_harness), with vaultSetSockets, vaultKeepAsBase, vaultFixSockets, their two helpers and vaultUnassign cut whole
from bible.html; and the mule window's own writer (_mpEqWrite) with the door stood in. In node. RED_PROOF below. A
missing node is the only skip.
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

import store_door_harness as D  # noqa: E402

#: a 2-look stash witness row on the base he is about to fix (game names and invented ids only)
ROW = {"mule": "bases", "holder": "SOCKETED", "source": "stash", "by": "reader", "lane": "stash", "at": "2026-10-01T10:00:00Z",
       "sessions": [{"session": "s_a", "frame": "f_a.jpg", "conf": 0.9}, {"session": "s_b", "frame": "f_b.jpg", "conf": 0.85}],
       "looks": [{"id": "s_a", "conf": 0.9}, {"id": "s_b", "conf": 0.85}]}
OLD, NEW = "Monarch (Larzuk base)", "Monarch (4os)"
MAP = {"Grief": "uni-weap", OLD: "bases"}
PROV = json.dumps({OLD: ROW})
#: every store the vault stands on, made unreadable the ways GrokBot's sweep and the reviews wrote them
HELD = {
    "d2r_owned": '{"a":1}',
    "d2r_muleRoster": "{}",
    "d2r_muleAssign": '{"Grief":"uni-weap"',
    "d2r_copies": '{"Grief":2',
    "d2r_magicFinds": '{"Death Loop":{"q":"rare"',
    "d2r_vaultProv": '{"Monarch (Larzuk base)":{"mule":"bas',
}


def _seed(**more):
    out = {"d2r_owned": json.dumps(["Grief", OLD]), "d2r_muleAssign": json.dumps(MAP), "d2r_vaultProv": PROV,
           "d2r_unknownReads": json.dumps(["Flail", "Monarch"])}
    out.update(more)
    return out


def _pieces(s):
    extra = ("function _ensureSocketBaseEntry(){}\n"
             + D.fn(s, "_socketDoorHeld") + "\n" + D.fn(s, "_socketFiledSay") + "\n"
             + D.window_fn(s, "vaultSetSockets") + "\n" + D.window_fn(s, "vaultKeepAsBase") + "\n"
             + D.window_fn(s, "vaultFixSockets") + "\n" + D.window_fn(s, "vaultUnassign") + "\n"
             + "window.__V = { assign: function(){ return assign; } };\n")
    pre = ("window._vaultResolveName = function(n){ return n; };\nvar EXTRA_ITEMS = {};\n"
           "window._ownedAdd = function(n){ owned.add(n); return { ok: true }; };\n"
           "var FORGOT = []; window._ownedProvForget = function(n){ FORGOT.push(n); return false; };\n")
    return (D.stage(s) + D.boot(s) + D.tab_sync(s) + "\n" + D.VAULT_DOOR_STUBS + pre + "(function(){\n" + D.vault_head(s)
            + "\nfunction muleById(id){ return roster.find(function(m){ return m.id === id; }) || null; }\n"
            + D.say_line(s) + D.vault_door(s) + "\n" + extra + "\n})();\n")


WRITES = ("var WROTE = [], REFUSE = {}; var _set = window.LSR.setItem; window.LSR.setItem = function(k, v){ WROTE.push(k);"
          " if (REFUSE[k]) return false; return _set.call(window.LSR, k, v); };\n")

STATE = r"""
function state(){
  return { owned: RAW['d2r_owned'], map: RAW['d2r_muleAssign'], prov: RAW['d2r_vaultProv'], unknown: RAW['d2r_unknownReads'],
           mem: JSON.parse(JSON.stringify(window.__V.assign())), ownedMem: Array.from(owned).sort() };
}
"""


def _run(body, seed):
    s = D.src()
    return D.page(_pieces(s), WRITES + STATE + body, seed=seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED vault doors; UNMEASURED, not passing")
class TheSocketDoorsWaitForAHeldVault(unittest.TestCase):

    def test_with_every_store_readable_the_socket_fix_carries_the_row_and_the_filing(self):
        """the premise: the doors this law holds shut do work, so the waits below are the hold, not a dead harness"""
        o = _run("OUT.held = window._vaultBasisHeld(); OUT.r = window.vaultFixSockets('" + OLD + "', 4);"
                 "OUT.s = state(); OUT.status = STATUS.slice();", _seed())
        self.assertIsNone(o["held"])
        self.assertTrue(o["r"] and o["r"]["ok"], o["r"])
        prov = json.loads(o["s"]["prov"])
        self.assertEqual(sorted(prov), [NEW], "PREMISE: the row did not move to the new label: %r" % sorted(prov))
        self.assertEqual(prov[NEW]["looks"], ROW["looks"], "PREMISE: the row was not carried verbatim")
        self.assertEqual(json.loads(o["s"]["map"]), {"Grief": "uni-weap", NEW: "bases"})
        self.assertTrue(any("— fixed" in m for m in o["status"]), o["status"])

    def test_while_a_store_the_vault_stands_on_is_held_the_socket_doors_and_the_cell_x_touch_nothing(self):
        body = r"""
OUT.held = window._vaultBasisHeld();
var before = state(); WROTE.length = 0;
OUT.fix = window.vaultFixSockets('%(old)s', 4);
OUT.set = window.vaultSetSockets('Monarch', 4);
OUT.keep = window.vaultKeepAsBase('Flail');
OUT.x = window.vaultUnassign('Grief');
OUT.wrote = WROTE.slice(); OUT.after = state(); OUT.before = before; OUT.status = STATUS.slice();
""" % {"old": OLD}
        for key, bad in HELD.items():
            with self.subTest(store=key):
                o = _run(body, _seed(**{key: bad}))
                self.assertTrue(o["held"] and key in o["held"], "PREMISE: %s did not hold the vault: %r" % (key, o["held"]))
                self.assertEqual(o["wrote"], [], "%s held: a door still wrote %r" % (key, o["wrote"]))
                self.assertEqual(o["after"], o["before"], "%s held: a door changed his stores or memory" % key)
                self.assertEqual(json.loads(o["after"]["prov"]) if key != "d2r_vaultProv" else None,
                                 {OLD: ROW} if key != "d2r_vaultProv" else None,
                                 "%s held: the old label's witness row is gone" % key)
                for door in ("set", "keep", "x"):
                    r = o[door]
                    self.assertTrue(isinstance(r, dict) and r.get("ok") is False and r.get("refused") == "held",
                                    "%s held: %s answered %r" % (key, door, r))
                    self.assertIn(key, r.get("why", ""), "%s held: %s's refusal does not name the store" % (key, door))
                said = " | ".join(o["status"])
                self.assertIn("the socket fix waits", said, "%s held: the wait was not said: %r" % (key, o["status"]))
                self.assertIn("stays in its locker", said, "%s held: the cell ✕'s wait was not said" % key)
                self.assertNotIn("— fixed", said, "%s held: the socket fix said 'fixed' with nothing saved" % key)
                self.assertNotIn("registered as a runeword", said, "%s held: 'registered' over a held vault" % key)
                self.assertNotIn("kept UNSOCKETED", said, "%s held: 'kept' over a held vault" % key)

    def test_a_refile_the_door_refuses_leaves_the_old_label_its_filing_and_its_row(self):
        """not the hold: the new label is locked to his MAIN, so the restore refuses - nothing he had may move"""
        o = _run("window._laneLocked = function(n){ return n === '" + NEW + "' ? 'equipment' : ''; };"
                 "OUT.r = window.vaultFixSockets('" + OLD + "', 4); OUT.s = state(); OUT.status = STATUS.slice();"
                 "OUT.forgot = FORGOT.slice();", _seed())
        self.assertFalse(o["r"]["ok"], "a refused refile was answered ok: %r" % o["r"])
        self.assertEqual(o["r"]["refused"], "locked")
        self.assertEqual(json.loads(o["s"]["prov"]), {OLD: ROW}, "the old label's witness row was dropped")
        self.assertEqual(o["s"]["mem"], MAP, "the old label's filing was dropped")
        self.assertEqual(json.loads(o["s"]["map"]), MAP)
        self.assertEqual(o["s"]["ownedMem"], sorted(["Grief", OLD]), "the new label stayed owned / the old one left")
        self.assertEqual(o["forgot"], [NEW], "the receipt this click wrote for the new label was not taken back")
        said = " | ".join(o["status"])
        self.assertIn("the socket fix did not land", said, "the refusal was not said: %r" % o["status"])
        self.assertIn("stays as it was", said)
        self.assertNotIn("— fixed", said)

    def test_the_throw_out_doors_say_a_filing_the_door_refused(self):
        o = _run("window._laneLocked = function(n){ return /^Monarch \\(4os\\)$|^Flail \\(Larzuk base\\)$/.test(n) ? 'equipment' : ''; };"
                 "OUT.set = window.vaultSetSockets('Monarch', 4); OUT.keep = window.vaultKeepAsBase('Flail');"
                 "OUT.status = STATUS.slice();", _seed())
        self.assertEqual((o["set"]["filed"] or {}).get("refused"), "locked", "PREMISE: the door did not refuse: %r" % o["set"])
        said = " | ".join(o["status"])
        self.assertIn("registered as a runeword/craft base · not filed to a mule - Monarch (4os) is locked to your MAIN", said,
                      "the socket count said 'registered' over a refused filing: %r" % o["status"])
        self.assertIn("kept UNSOCKETED", said)
        self.assertIn("· not filed to a mule - Flail (Larzuk base) is locked to your MAIN", said,
                      "keep unsocketed said 'kept' over a refused filing: %r" % o["status"])

    def test_the_cell_x_never_answers_ok_over_a_refused_map_write(self):
        o = _run("REFUSE['d2r_muleAssign'] = true; WROTE.length = 0;"
                 "OUT.x = window.vaultUnassign('" + OLD + "'); OUT.s = state(); OUT.wrote = WROTE.slice();"
                 "OUT.status = STATUS.slice();", _seed())
        self.assertEqual(o["x"].get("refused"), "not-written", "the ✕ answered %r over a refused map write" % o["x"])
        self.assertFalse(o["x"]["ok"])
        self.assertEqual(json.loads(o["s"]["prov"]), {OLD: ROW}, "the witness row was demoted while the map kept the filing")
        self.assertNotIn("d2r_vaultProv", o["wrote"], "the row was written before the map was")
        self.assertTrue(any("was not sent back to the dock" in m for m in o["status"]), o["status"])


MULE_WINDOW = r"""
var window = globalThis, RAW = {};
window.LSR = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
               setItem: function(k, v){ RAW[k] = String(v); return true; }, removeItem: function(k){ delete RAW[k]; },
               quarantined: function(){ return null; }, read: function(k, sh, ab){ var r = RAW[k]; if (r == null) return ab;
                 try { var v = JSON.parse(r); return (v && typeof v === 'object' && !Array.isArray(v)) ? v : null; } catch (e) { return null; } } };
window._storeHeldWhy = function(){ return null; };
function muleById(id){ return { id: id, name: id.toUpperCase() }; }
var SAID = []; window._vaultLockSay = function(n, m, loud){ SAID.push(String(m)); };
var DOOR = %(door)s;
window.vaultFile = function(n, w, o){ return DOOR; };
%(slots)s
%(all)s
%(why)s
%(generic)s
%(write)s
try { _mpEqWrite({ 'uni-armor': { setI: { head: { name: 'Harlequin Crest (Shako)', source: 'manual', at: '2026-10-22T10:00:00Z' } } } }); } catch (e) { SAID.push('threw: ' + e.message); }
process.stdout.write(JSON.stringify({ said: SAID, raw: RAW['d2r_muleEquip'] || null }));
"""


def _block(s, start, end_line):
    if s.count(start) != 1:
        raise AssertionError("%r matched %d times - the anchor moved" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end_line, i)
    return s[i:s.index("\n", j) + 1]


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED mule window writer; UNMEASURED, not passing")
class TheMuleWindowSaysAHeldVault(unittest.TestCase):

    def _drive(self, door):
        s = D.src()
        prog = MULE_WINDOW % {"door": json.dumps(door),
                              "slots": _block(s, "  var MP_SLOT_WEARS = { head: ['helm']", "  var MP_CB_FIELDS = ["),
                              "all": D.fn(s, "_mpEqAll"), "why": D.fn(s, "_mpEqHeldWhy"),
                              "generic": D.fn(s, "_mpIsGenericCopy"), "write": D.fn(s, "_mpEqWrite")}
        r = subprocess.run([D.NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped mule window writer would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
        return json.loads(r.stdout)

    def test_a_placement_the_held_vault_did_not_file_is_said(self):
        for refused in ("held", "not-written"):
            with self.subTest(refused=refused):
                o = self._drive({"ok": False, "refused": refused,
                                 "why": "Harlequin Crest (Shako) was not filed - the vault is held - d2r_copies will not parse"})
                self.assertIsNotNone(o["raw"], "PREMISE: the placement itself was not saved")
                self.assertEqual(len(o["said"]), 1, "a %s refusal of the filing was not said: %r" % (refused, o["said"]))
                self.assertIn("d2r_copies will not parse", o["said"][0])
                self.assertIn("the vault did not file it there", o["said"][0])
        ok = self._drive({"ok": True, "mode": "filed", "mule": "uni-armor"})
        self.assertEqual(ok["said"], [], "PREMISE: a filing that landed was said as a refusal")


RED_PROOF = [
    {"why": "REG-2521 fix round - the socket fix no longer asks the hold (it drops the old label's row and filing, then "
            "vaultFile refuses: the row is gone for good and the status says 'fixed')",
     "file": "bible.html", "matches": 1,
     "find": "      if (_bhFix){ status('⚠ the socket fix waits - ' + _bhFix + ' (see the notice at the top)'); return { ok: false, refused: 'held', why: _bhFix }; }\n",
     "replace": ""},
    {"why": "REG-2521 fix round - a refile the door refuses no longer puts back what the click took (the old label's row "
            "and filing dropped)",
     "file": "bible.html", "matches": 1,
     "find": "      if (_rfF && !_rfF.ok){\n",
     "replace": "      if (false){\n"},
    {"why": "REG-2521 fix round - the throw-out review's socket doors no longer ask the hold",
     "file": "bible.html", "matches": 1,
     "find": "  function _socketDoorHeld(){\n    var why = (typeof window._vaultBasisHeld === 'function') ? window._vaultBasisHeld() : null;\n",
     "replace": "  function _socketDoorHeld(){\n    var why = null;\n"},
    {"why": "REG-2521 fix round - the throw-out doors say 'registered' / 'kept' over a filing the door refused",
     "file": "bible.html", "matches": 1,
     "find": "    return (vf && !vf.ok) ? ' · not filed to a mule - '",
     "replace": "    return false ? ' · not filed to a mule - '"},
    {"why": "REG-2521 fix round - the cell ✕ no longer asks the hold (demotes the row, saveA refused, answers ok)",
     "file": "bible.html", "matches": 1,
     "find": "    if (_bhU){\n      var whyH",
     "replace": "    if (false){\n      var whyH"},
    {"why": "REG-2521 fix round - the cell ✕ answers ok over a refused map write and demotes the row anyway",
     "file": "bible.html", "matches": 1,
     "find": "    if (!_okU){\n      if (_prevU !== undefined) assign[name] = _prevU;",
     "replace": "    saveA(); if (false){\n      if (_prevU !== undefined) assign[name] = _prevU;"},
    {"why": "REG-2521 fix round - the mule window says a vaultFile refusal only for 'hardened' / 'prov-unreadable' again",
     "file": "bible.html", "matches": 1,
     "find": "            else if (_vfM && !_vfM.ok && (_vfM.refused === 'held' || _vfM.refused === 'not-written') && window._vaultLockSay)\n",
     "replace": "            else if (false)\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
