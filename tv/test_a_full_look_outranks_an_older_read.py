# -*- coding: utf-8 -*-
"""REG-2892 / REG-2893 (intake design P2, #230 c6473846977 and his Q2) - A FULL LOOK, AND THE READS IT OUTRANKS.

His design: "A full look is a frame that shows a whole container (a stash tab or a mule's full inventory). It is the
container's truth at that capture time. A read older than the container's newest full look can't add, move or remove
anything. It is kept as history. That is how an Oct 6 screenshot stops placing items today."

REG-2892 builds the full look's CONTRACT and its receivers (window._vaultFullLook): it must say complete:true, name its
container (holder, location, a shared page's number), carry its capture time, its session and frame, and list EVERY cell
of the grid once - its item or empty. Anything less is refused in words and stamps nothing. A full look lands in the drain
(_vaultGoneObserve, complete:true - REG-2861's door, in slot_identity's cell keys, a shared page's rows stacked) and in
d2r_vaultFullLooks, the newest look per container (an older one is history and changes nothing), forked per profile.

REG-2893 is his Q2 at the register door: a read whose container has a full look newer than the read - or a read with no
capture time at all - is refused (refused: 'stale') and reaches the ledger as history; it files nothing. A read newer than
the look, a read that names no container, a container never looked at whole, and his hand are untouched.

No reader produces a full look yet (the console names items from hover tooltips only - tv_diablo VAULT_READ_PROMPT); the
producers are the guided sweep (P4) and P2's full-look detection. Whole page in node, fixtures only. RED_PROOF below.
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

HEAD = "Arcanna's Head (helm)"            # REG-2300's own throw-out fixture
T = 1761609600000                          # the full look's capture time
DAY = 86400000


def _prov(holder, loc, cell, n=2):
    return {"kind": "owned", "source": "tv", "seen": n,
            "looks": [{"session": "w%d" % i, "frame": "f%d" % i, "holder": holder, "loc": loc, "cell": cell} for i in range(n)]}


SEED = ("localStorage.setItem('d2r_ownerClaim', '*');"
        "localStorage.setItem('d2r_owned', %s);"
        "localStorage.setItem('d2r_muleAssign', '{}');"
        "localStorage.setItem('d2r_vaultProv', %s);" % (json.dumps(json.dumps([HEAD])),
                                                          json.dumps(json.dumps({HEAD: _prov("MAIN", "stash", "stash:c0r0")}))))

BODY = r"""
(function(){
var W = window, T = %(t)d, DAY = %(day)d, NAME = %(name)s;
function grid(w, h, put){ var c = []; for (var y = 0; y < h; y++) for (var x = 0; x < w; x++){ var k = 'c' + x + 'r' + y; c.push({ cell: k, name: put[k] || null }); } return c; }
function look(sid, at, put, extra){ return Object.assign({ complete: true, container: { holder: 'MAIN', location: 'stash' }, capturedAt: at,
                                                           session: sid, frame: sid + '-f', cells: grid(10, 10, put || {}) }, extra || {}); }
function bag(){ var m = {}; try { (JSON.parse(localStorage.getItem('d2r_vaultRecords') || '{}').records || []).forEach(function(r){ if (r.move) m[r.name] = r.move; }); } catch (e) {} return m; }
W._vaultAutoIntakeSet && W._vaultAutoIntakeSet(false);
W._movePaintBusy = false; W._vaultMovePaint();
OUT.start = bag()[NAME] || null;
/* the contract: every way to fall short is refused, and refused in words */
var short99 = look('x', T); short99.cells = short99.cells.slice(1);
var dup = look('x', T); dup.cells[1] = { cell: 'c0r0', name: null };
var far = look('x', T); far.cells[0] = { cell: 'c10r0', name: null };
OUT.refused = {
  notComplete: W._vaultFullLook(Object.assign(look('x', T), { complete: false })),
  noContainer: W._vaultFullLook(Object.assign(look('x', T), { container: { location: 'stash' } })),
  notAGrid: W._vaultFullLook(Object.assign(look('x', T), { container: { holder: 'MAIN', location: 'equipped' } })),
  sharedNoPage: W._vaultFullLook(Object.assign(look('x', T), { container: { holder: 'SHARED STASH', location: 'shared' } })),
  undated: W._vaultFullLook(Object.assign(look('x', T), { capturedAt: null })),
  noFrame: W._vaultFullLook(Object.assign(look('x', T), { frame: '' })),
  short99: W._vaultFullLook(short99), dup: W._vaultFullLook(dup), far: W._vaultFullLook(far) };
OUT.storeAfterRefusals = localStorage.getItem('d2r_vaultFullLooks');
/* the drain is fed what each full look saw; record its frames */
OUT.frames = []; var _go = W._vaultGoneObserve;
W._vaultGoneObserve = function(f){ OUT.frames.push(JSON.parse(JSON.stringify(f))); return _go.apply(this, arguments); };
/* five full looks of MAIN's stash without the item, each its own session */
for (var i = 1; i <= 5; i++) OUT['l' + i] = W._vaultFullLook(look('g' + i, T + i * 1000, { c5r5: 'Harlequin Crest', c6r5: 'Harlequin Crest' }));
OUT.after5 = bag()[NAME] || null;
OUT.stamp = W._vaultFullLookOf('MAIN', 'stash');
/* an older full look is history: stamps nothing, feeds nothing */
var n0 = OUT.frames.length;
OUT.older = W._vaultFullLook(look('old', T - DAY, {}));
OUT.olderFed = OUT.frames.length - n0;
OUT.stampAfterOlder = W._vaultFullLookOf('MAIN', 'stash');
/* a shared page: its rows stack on the page (REG-2802), so page 1 row 3 is row 13 */
OUT.shared = W._vaultFullLook(Object.assign(look('sh', T, { c2r3: 'Grief' }), { container: { holder: 'SHARED STASH', location: 'shared', page: 1 } }));
OUT.sharedFrame = OUT.frames[OUT.frames.length - 1];
W._vaultGoneObserve = _go;
OUT.forked = !!(W._LP_FORKED && W._LP_FORKED.has('d2r_vaultFullLooks'));
/* REG-2893 - the stale rule, asked directly */
var S = W._vaultFullLookOf('MAIN', 'stash'), FL = S ? S.at : null;
function wit(at, holder, loc){ var l = { session: 'r1', frame: 'r1f', holder: holder || 'MAIN', loc: loc || 'stash', cell: 'stash:c1r1' }; if (at != null) l.at = at; return { lane: 'stash', by: 'tv-live', sessions: [l] }; }
OUT.flAt = FL;
OUT.stale = {
  older: W._vaultStaleRead('Harlequin Crest', wit(new Date(FL - DAY).toISOString())),
  undated: W._vaultStaleRead('Harlequin Crest', wit(null)),
  newer: W._vaultStaleRead('Harlequin Crest', wit(new Date(FL + DAY).toISOString())),
  same: W._vaultStaleRead('Harlequin Crest', wit(new Date(FL).toISOString())),
  noHolder: W._vaultStaleRead('Harlequin Crest', { lane: 'stash', sessions: [{ session: 'r1', frame: 'r1f', at: new Date(FL - DAY).toISOString() }] }),
  neverLooked: W._vaultStaleRead('Harlequin Crest', wit(new Date(FL - DAY).toISOString(), 'MULE-Z')),
  hand: W._vaultStaleRead('Harlequin Crest', { by: 'hand', at: new Date(FL - DAY).toISOString(), where: 'the vault manager' }) };
/* through the register door, with AUTO INTAKE on: the old read files nothing and leaves a ledger row */
W._vaultAutoIntakeSet(true);
var ownedBefore = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
OUT.doorOld = W.tvVaultRegister('Stone of Jordan', wit(new Date(FL - DAY).toISOString()));
OUT.ownedGrew = JSON.parse(localStorage.getItem('d2r_owned') || '[]').filter(function(n){ return ownedBefore.indexOf(n) < 0; });
var log0 = []; try { log0 = JSON.parse(localStorage.getItem('d2r_chronicleInboxLog') || '[]'); } catch (eL0) { log0 = []; }
OUT.staleRow = (Array.isArray(log0) ? log0 : []).filter(function(r){ return r && r.name === 'Stone of Jordan'; })[0] || null;
OUT.doorNew = W.tvVaultRegister('Stone of Jordan', wit(new Date(FL + DAY).toISOString()));
var log = []; try { log = JSON.parse(localStorage.getItem('d2r_chronicleInboxLog') || '[]'); } catch (eL) { log = []; }
OUT.logRows = (Array.isArray(log) ? log : []).filter(function(r){ return r && r.name === 'Stone of Jordan'; }).length;
})();
""" % {"t": T, "day": DAY, "name": json.dumps(HEAD)}


_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AFullLookIsAContract(unittest.TestCase):

    def test_premise_a_row_waits_in_its_first_witnessed_cell(self):
        o = page()
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual(((o["start"] or {}).get("from") or {}).get("cell"), "stash:c0r0", "PREMISE: %r" % o["start"])

    def test_a_look_that_falls_short_is_refused_in_words_and_stamps_nothing(self):
        o = page()
        for k, r in o["refused"].items():
            self.assertFalse(r.get("ok"), "%s was accepted as a full look: %r" % (k, r))
            self.assertTrue(r.get("why"), "%s was refused without a reason" % k)
        self.assertIsNone(o["storeAfterRefusals"], "a refused look stamped the store")

    def test_a_full_look_stamps_its_container_newest_wins(self):
        o = page()
        st = o["stamp"]
        self.assertTrue(o["l5"].get("ok") and o["l5"].get("stamped"), o["l5"])
        self.assertEqual((st["holder"], st["location"], st["at"], st["session"]), ("MAIN", "stash", T + 5000, "g5"), st)
        self.assertEqual((st["items"], st["empty"]), (1, 98), "the stamp miscounted the look: %r" % st)
        self.assertTrue(o["older"].get("older") and not o["older"].get("stamped"), o["older"])
        self.assertEqual(o["olderFed"], 0, "an older full look was fed to the drain")
        self.assertEqual(o["stampAfterOlder"]["at"], T + 5000, "an older full look replaced a newer one")
        self.assertTrue(o["forked"], "d2r_vaultFullLooks is not forked per profile")

    def test_five_full_looks_without_it_drain_its_row(self):
        o = page()
        f = o["frames"][0]
        self.assertIs(f.get("complete"), True)
        self.assertIn({"name": "Harlequin Crest", "cell": "stash:c5r5"}, f["items"])
        self.assertEqual((o["after5"] or {}).get("status"), "closed", "five full looks without it did not drain it: %r" % o["after5"])

    def test_a_shared_page_feeds_its_stacked_cells(self):
        o = page()
        self.assertTrue(o["shared"].get("ok"), o["shared"])
        sf = o["sharedFrame"]
        self.assertEqual((sf["holder"], sf["location"]), ("SHARED STASH", "shared"))
        self.assertIn({"name": "Grief", "cell": "shared:c2r13"}, sf["items"], "page 1 row 3 is not row 13: %r" % sf["items"])


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AReadOlderThanTheFullLookPlacesNothing(unittest.TestCase):

    def test_an_older_or_undated_read_is_stale(self):
        s = page()["stale"]
        for k in ("older", "undated"):
            self.assertEqual((s[k] or {}).get("refused"), "stale", "%s read was allowed to place: %r" % (k, s[k]))
            self.assertTrue(s[k].get("history"))
        self.assertIn("no capture time", s["undated"]["why"])

    def test_a_newer_read_and_the_cases_with_nothing_to_compare_are_untouched(self):
        s = page()["stale"]
        for k in ("newer", "same", "noHolder", "neverLooked", "hand"):
            self.assertIsNone(s[k], "%s read was refused as stale: %r" % (k, s[k]))

    def test_the_register_door_files_nothing_from_an_old_read_and_keeps_it_as_history(self):
        o = page()
        self.assertEqual(o["doorOld"].get("refused"), "stale", "the door filed an old read: %r" % o["doorOld"])
        self.assertNotEqual((o["doorNew"] or {}).get("refused"), "stale", "the door refused a NEWER read as stale: %r" % o["doorNew"])
        self.assertEqual(o["ownedGrew"], [], "the old read still added an item: %r" % o["ownedGrew"])
        row = o["staleRow"] or {}
        self.assertTrue(row, "the stale read left no ledger row - it is not kept as history")
        self.assertIn("seen whole on", json.dumps(row), "the ledger row does not say why the read placed nothing: %r" % row)


RED_PROOF = [
    {"why": "REG-2892 - a look that names 99 of 100 cells is taken as a full look",
     "file": "bible.html",
     "find": "    if (nCells !== W * H) return no(",
     "replace": "    if (false) return no(",
     "matches": 1, "needs": "node"},
    {"why": "REG-2892 - an older full look replaces the newer one",
     "file": "bible.html",
     "find": "    if (curAt != null && curAt > at)\n",
     "replace": "    if (false)\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2892 - a full look reaches the drain as a partial frame, so nothing drains",
     "file": "bible.html",
     "find": "items: items, ground: [], complete: true })\n",
     "replace": "items: items, ground: [] })\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2892 - a shared page's rows are not stacked, so page 1 row 3 reads as page 0 row 3",
     "file": "bible.html",
     "find": "      var y = +m[2] + (loc === 'shared' ? page * H : 0);\n",
     "replace": "      var y = +m[2];\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2892 - the full-look stamp is bare, shared by every profile",
     "file": "bible.html",
     "find": '  "d2r_vaultFullLooks",\n',
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2893 - an older read places again",
     "file": "bible.html",
     "find": "    if (t != null && t >= flAt) return null;\n",
     "replace": "    return null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2893 - an undated read passes as current",
     "file": "bible.html",
     "find": "    if (t != null && t >= flAt) return null;\n",
     "replace": "    if (t == null || t >= flAt) return null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2893 - the register door never asks the stale rule",
     "file": "bible.html",
     "find": "        r = _staleR || _inner.apply(this, _call);   /* REG-2893 */\n",
     "replace": "        r = _inner.apply(this, _call);\n",
     "matches": 1, "needs": "node"},
]


if __name__ == "__main__":
    unittest.main()
