# -*- coding: utf-8 -*-
"""#144.9 (REG-2760, his pick 2026-10-28 12:41 IDT via GrokBot #230 6466865161) - A READ-ONLY COPY READOUT.

GrokBot proved on a guest that the locker card draws copies from the copies store (copyCount, through _shelfCopyCount)
while the mule window and FIND pack the vault records (_vaultRecordsForMule): a plate said "5 copies" over two cells.
His own vault records live only in his browser, so no seat could measure his data. He chose a readout: per name filed to
a locker, what the card draws, what the records hold, how many cells FIND names, the copies store's count, and a
mismatch flag - written by nothing, migrating nothing, and readable without touching his profile.

window._vaultCopyAudit() is the board's half (driven here on the whole page in node: a consistent vault reads clean, a
records answer that disagrees with the card is flagged and sorted first, and the readout writes no store). It rides
the board's existing tally hand-over at most every 5 min; the console banks it as handed (accept_handed_copy_audit,
shape-checked, never re-derived) and serves it with its age on GET /api/vault/copy_audit (copy_audit_payload).
RED_PROOF below.
"""
import io
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

PRELUDE = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(["Griswold's Edge", "Lightsabre"]));
localStorage.setItem('d2r_copies', JSON.stringify({"Griswold's Edge": 3}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({"Griswold's Edge": 'uni-weap', "Lightsabre": 'uni-weap'}));
localStorage.setItem('d2r_vaultRecordsMigrate', JSON.stringify({ver: 0, ts: 1793000000000, count: 26}));
"""

BODY = r"""
(function(){
var W = window;
try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); }
H.flush(60, 3);
function snap(){ var o = {}; for (var i = 0; i < localStorage.length; i++){ var k = localStorage.key(i); o[k] = localStorage.getItem(k); } return JSON.stringify(o); }
var before = snap();
try { OUT.clean = W._vaultCopyAudit(); } catch (e) { OUT.cleanErr = String(e && e.message || e); }
var mid = snap();
var real = W._vaultRecordsForMule;
W._vaultRecordsForMule = function(m){ return m === 'uni-weap' ? { "Griswold's Edge": 1, "Lightsabre": 1 } : {}; };
try { OUT.split = W._vaultCopyAudit(); } catch (e) { OUT.splitErr = String(e && e.message || e); }
W._vaultRecordsForMule = real;
OUT.wrote = (before !== mid) || (mid !== snap());
})();
"""


def _row(audit, name):
    return next((r for r in (audit or {}).get("rows") or [] if r.get("name") == name), None)


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - the board's half is UNMEASURED here, never a pass")
class TheBoardSaysWhatEachSideCounts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude=PRELUDE, timeout=300)

    def test_the_page_booted_and_the_readout_ran(self):
        o = self.o
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertNotIn("cleanErr", o, o.get("cleanErr"))
        self.assertTrue((o.get("clean") or {}).get("ok"), "PREMISE: the readout did not answer: %r" % o.get("clean"))

    def test_a_consistent_vault_reads_clean(self):
        c = self.o.get("clean") or {}
        g, l = _row(c, "Griswold's Edge"), _row(c, "Lightsabre")
        self.assertIsNotNone(g, "the x3 item is not in the readout: %r" % c)
        self.assertEqual((g["mule"], g["card"], g["records"], g["find"], g["copies"]), ("uni-weap", 3, 3, 3, 3), g)
        self.assertEqual((l["card"], l["records"], l["find"]), (1, 1, 1), l)
        self.assertEqual((c.get("checked"), c.get("mismatched")), (2, 0), "a consistent vault reads as split: %r" % c)
        self.assertFalse(g["mismatch"] or l["mismatch"])

    def test_records_that_disagree_with_the_card_are_flagged_first(self):
        s = self.o.get("split") or {}
        g = _row(s, "Griswold's Edge")
        self.assertEqual((g["card"], g["records"], g["find"]), (3, 1, 3), "the readout does not say each side's count: %r" % g)
        self.assertTrue(g["mismatch"], "a card drawing 3 over records holding 1 is not flagged: %r" % g)
        self.assertEqual(s.get("mismatched"), 1, s)
        self.assertEqual(s["rows"][0]["name"], "Griswold's Edge", "a mismatched row is not listed first")

    def test_the_readout_says_what_it_covers_and_dates_the_migrate_receipt(self):
        """REG-2779 (GrokBot's v3827 pass) - "checked 9 against migrateCount 26" could not explain itself. An older stamp (ver
        0) is not a source, so the records stay the live derivation and the receipt is read raw."""
        c = self.o.get("clean") or {}
        bk = c.get("recordsByKind") or {}
        self.assertEqual(c.get("recordsTotal"), sum(v for v in bk.values() if isinstance(v, int)),
                         "the records by kind do not add up to the total: %r" % {k: c.get(k) for k in ("recordsTotal", "recordsByKind")})
        self.assertEqual(bk.get("filed"), 4, "today's copy records by kind are not said: %r" % bk)
        self.assertGreaterEqual(c.get("recordsTotal") or 0, sum((r.get("records") or 0) for r in c.get("rows") or []))
        self.assertEqual((c.get("migrateCount"), c.get("migrateAt")), (26, 1793000000000), "the migrate receipt is not dated")

    def test_the_readout_writes_nothing(self):
        self.assertIs(self.o.get("wrote"), False, "reading the copies changed a store")


class TheConsoleBanksItAsHanded(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        cls.ca = ca

    def setUp(self):
        self.keep = dict(self.ca._COPY_AUDIT)
        self.ca._COPY_AUDIT.update(audit=None, receivedAt=None, who=None, refused=None)

    def tearDown(self):
        self.ca._COPY_AUDIT.clear()
        self.ca._COPY_AUDIT.update(self.keep)

    def test_before_any_hand_over_it_says_why_there_is_none(self):
        p = self.ca.copy_audit_payload(now_ms=10)
        self.assertFalse(p["ok"])
        self.assertIsNone(p["ageS"])
        self.assertIn("no board has handed", p["why"])

    def test_a_readout_is_banked_shaped_and_served_with_its_age(self):
        who = {"id": "x", "p": "Konyo", "pfx": ""}
        body = {"copyAudit": {"ok": True, "at": 5, "recordsRead": True, "dirty": False, "migrateCount": 43, "rows": [
            {"name": "Nightwing's Veil", "mule": "uni-armor", "card": 3, "records": 1, "find": 1, "findKind": "filed",
             "copies": 3, "warCap": None, "mismatch": True},
            {"name": "Lightsabre", "mule": "uni-weap", "card": True, "records": -1, "find": 1, "mismatch": "yes"}]}}
        self.assertEqual(self.ca.accept_handed_copy_audit(body, who, now_ms=1000), (True, None))
        p = self.ca.copy_audit_payload(now_ms=61000)
        self.assertTrue(p["ok"], p)
        self.assertEqual((p["ageS"], p["who"], p["audit"]["checked"], p["audit"]["mismatched"]), (60, "Konyo", 2, 1))
        self.assertEqual((p["audit"]["recordsTotal"], p["audit"]["recordsByKind"], p["audit"]["migrateAt"]), (None, None, None),
                         "REG-2779 - a readout that did not say its coverage was banked as if it had")
        body["copyAudit"].update(recordsTotal=7, recordsByKind={"filed": 4, "loose": 3, "x" * 30: 1, "keep": -1}, migrateAt=9)
        self.ca.accept_handed_copy_audit(body, who, now_ms=2000)
        a2 = self.ca.copy_audit_payload(now_ms=3000)["audit"]
        self.assertEqual((a2["recordsTotal"], a2["recordsByKind"], a2["migrateAt"]), (7, {"filed": 4, "loose": 3, "keep": None}, 9),
                         "REG-2779 - the coverage the board said was not banked, or banked unshaped: %r" % a2)
        bad = p["audit"]["rows"][1]
        self.assertEqual((bad["card"], bad["records"], bad["mismatch"]), (None, None, False),
                         "a count that is not a non-negative int, or a flag that is not true, was banked as one: %r" % bad)

    def test_no_readout_in_a_hand_over_is_not_a_refusal(self):
        self.assertEqual(self.ca.accept_handed_copy_audit({"sets": {"have": 1}}, None), (None, None))

    def test_a_board_that_could_not_read_says_so_and_a_malformed_one_is_refused(self):
        self.assertEqual(self.ca.accept_handed_copy_audit({"copyAudit": {"ok": False, "why": "no vault"}}, None, 1),
                         (True, None))
        p = self.ca.copy_audit_payload(now_ms=2)
        self.assertEqual((p["ok"], p["why"]), (False, "no vault"))
        self.assertFalse(self.ca.accept_handed_copy_audit({"copyAudit": {"ok": True, "rows": [{"mule": "x"}]}}, None)[0])
        self.assertFalse(self.ca.accept_handed_copy_audit({"copyAudit": {"ok": True, "rows": [{}] * 4001}}, None)[0])


    def test_a_refused_hand_over_is_served_beside_the_readout_it_did_not_replace(self):
        """REG-2778 (the v3827 second eye) - a refused readout left the older one served alone, as if none came since."""
        good = {"copyAudit": {"ok": True, "at": 5, "rows": [{"name": "Shako", "mule": "uni-armor", "card": 1, "records": 1,
                                                               "find": 1, "mismatch": False}]}}
        self.assertEqual(self.ca.accept_handed_copy_audit(good, None, now_ms=1000), (True, None))
        saved, why = self.ca.accept_handed_copy_audit({"copyAudit": {"ok": True, "rows": [{}] * 4001}}, None, now_ms=31000)
        self.assertFalse(saved)
        p = self.ca.copy_audit_payload(now_ms=61000)
        self.assertEqual((p["ok"], p["ageS"], p["audit"]["checked"]), (True, 60, 1), "the older readout was dropped: %r" % p)
        self.assertEqual(((p.get("refused") or {}).get("ageS"), (p.get("refused") or {}).get("why")), (30, why),
                         "a refused hand-over is not served beside the readout it did not replace: %r" % p)
        self.assertEqual(self.ca.accept_handed_copy_audit(good, None, now_ms=62000), (True, None))
        self.assertIsNone(self.ca.copy_audit_payload(now_ms=63000).get("refused"), "a kept readout still carries an old refusal")

    def test_a_refusal_with_nothing_banked_says_it_was_refused(self):
        self.ca.accept_handed_copy_audit({"copyAudit": {"ok": True, "rows": [{"mule": "x"}]}}, None, now_ms=1000)
        p = self.ca.copy_audit_payload(now_ms=2000)
        self.assertFalse(p["ok"])
        self.assertIn("was refused: a copy readout row has no name", p["why"])


class TheWiringIsWhole(unittest.TestCase):

    def test_the_board_hands_it_over_and_the_console_serves_it(self):
        page = io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8").read()
        app = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertEqual(page.count("_body.copyAudit = (typeof window._vaultCopyAudit === 'function') ? window._vaultCopyAudit()"), 1,
                         "the board's tally hand-over does not carry the copy readout")
        self.assertEqual(app.count("_ca_saved, _ca_why = accept_handed_copy_audit(body, _who)"), 1,
                         "the console's tally door does not bank the copy readout")
        self.assertEqual(app.count('        if path == "/api/vault/copy_audit":\n            # #144.9 (REG-2760)'), 1,
                         "no GET serves the copy readout")
        self.assertEqual(app.count("            self._json(200, copy_audit_payload())\n"), 1)


RED_PROOF = [
    {"why": "REG-2779 - the readout does not say what it covers (no records by kind)",
     "file": "bible.html",
     "find": "        out.recordsTotal = _rs.records.length; out.recordsByKind = _bk;\n",
     "replace": "        out.recordsTotal = null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2779 - the migrate receipt is not dated",
     "file": "bible.html",
     "find": "      out.migrateAt = (_mg && typeof _mg.ts === 'number') ? _mg.ts : null;   /* REG-2779 - the stamp's own date */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2779 - the console drops the coverage the board said",
     "file": "control_app.py",
     "find": "                              \"recordsByKind\": _ca_kinds(a.get(\"recordsByKind\")),\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2778 - a readout this console refuses is forgotten, and the older one is served alone",
     "file": "control_app.py",
     "find": "        _COPY_AUDIT[\"refused\"] = {\"at\": now, \"why\": why, \"who\": _p}\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-2778 - a kept readout still carries the refusal it replaced",
     "file": "control_app.py",
     "find": "                       receivedAt=now, who=_p, refused=None)\n    return True, None\n\n\ndef copy_audit_payload(",
     "replace": "                       receivedAt=now, who=_p)\n    return True, None\n\n\ndef copy_audit_payload(",
     "matches": 1},
    {"why": "REG-2760 - the readout never flags a split",
     "file": "bible.html",
     "find": "                        mismatch: known.some(function(x){ return x !== known[0]; }) });\n",
     "replace": "                        mismatch: false });\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2760 - the readout writes a store while it reads",
     "file": "bible.html",
     "find": "    try { out.dirty = (window.LSR.getItem('d2r_vaultRecordsDirty') != null); } catch (eD) { out.dirty = null; }\n",
     "replace": "    try { window.LSR.setItem('d2r_vaultRecordsDirty', '1'); out.dirty = true; } catch (eD) { out.dirty = null; }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2760 - the readout says the copies store's count where the records' belongs",
     "file": "bible.html",
     "find": "        rec = (span && typeof span === 'object') ? (span[n] | 0) : null;\n",
     "replace": "        rec = (typeof copyCount === 'function') ? copyCount(n) : null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2760 - the console banks a bool as a count",
     "file": "control_app.py",
     "find": "    return v if (isinstance(v, int) and not isinstance(v, bool) and v >= 0) else None\n",
     "replace": "    return v if isinstance(v, int) else None\n",
     "matches": 1},
    {"why": "REG-2760 - the readout is served without its age",
     "file": "control_app.py",
     "find": "    return {\"ok\": bool(a.get(\"ok\")), \"audit\": a, \"receivedAt\": at, \"ageS\": max(0, (now - int(at)) // 1000),\n",
     "replace": "    return {\"ok\": bool(a.get(\"ok\")), \"audit\": a, \"receivedAt\": at, \"ageS\": None,\n",
     "matches": 1},
    {"why": "REG-2760 - the tally hand-over stops carrying the readout",
     "file": "bible.html",
     "find": "              _body.copyAudit = (typeof window._vaultCopyAudit === 'function') ? window._vaultCopyAudit()\n",
     "replace": "              _body.copyAuditOff = (typeof window._vaultCopyAudit === 'function') ? window._vaultCopyAudit()\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
