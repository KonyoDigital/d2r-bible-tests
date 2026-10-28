# -*- coding: utf-8 -*-
"""Intake design P1 (REG-2817, his ruling Q1-Q4, #230 6473846977) - THE ROSTER UPLOAD'S VAULT SECTION IS THE BOARD'S RECORDS,
DATED BY WHEN THE BOARD HANDED THEM.

The upload's vault section was this console's vault_accum.json - the sweep's evidence ledger, whose own header says it is
"evidence, not truth" - with asOf = that file's mtime, or the moment of publishing when the mtime would not read; its stash
section beside it came from the board's d2r_owned. One upload, two sources, and a date that said when a file was touched.

Now the vault rows come from the copy readout the board hands this console (window._vaultCopyAudit, REG-2760): one row per
locker-homed name (name, locker), asOf = when the board handed it (_COPY_AUDIT receivedAt). A board that has not handed one
since this console started, or handed a readout saying it could not read its records, sends no vault section and says why
on GET /api/vault/copy_audit (rosterVault) - never an empty vault and never "now". The accum ledger is not deleted: the
console's vault routes still read it.

Driven on control_app itself: _roster_vault_from_records over each state of the banked readout, through roster_publish's
vault_read and section_of as the publish lane does; _roster_reads read for the source it builds the vault section from.
RED_PROOF below.
"""
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
import fixture_tmp as _fx  # noqa: E402
_fx.contain()

T = 1793000000000


class TheVaultSectionIsTheBoardsRecords(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as ca
        import roster_publish as rp
        cls.ca, cls.rp = ca, rp

    def setUp(self):
        self.keep = dict(self.ca._COPY_AUDIT)
        self.ca._COPY_AUDIT.update(audit=None, receivedAt=None, who=None, refused=None)

    def tearDown(self):
        self.ca._COPY_AUDIT.clear()
        self.ca._COPY_AUDIT.update(self.keep)

    def _section(self):
        rows, why, as_of = self.ca._roster_vault_from_records()
        got = self.rp.vault_read("ok" if rows is not None else why, rows, as_of)
        return (rows, why, as_of), (self.rp.section_of(got, T + 999999) if got is not None else None)

    def test_nothing_handed_is_no_section_and_says_why(self):
        (rows, why, as_of), sec = self._section()
        self.assertEqual((rows, as_of, sec), (None, None, None), "an unhanded vault became a section")
        self.assertIn("has not handed", why)
        say = self.ca.copy_audit_payload(now_ms=T)["rosterVault"]
        self.assertEqual((say["rows"], say["asOf"]), (None, None))
        self.assertIn("has not handed", say["why"])

    def test_a_handed_readout_is_the_section_dated_by_its_hand_over(self):
        body = {"copyAudit": {"ok": True, "at": T - 5000, "rows": [
            {"name": "Shako", "mule": "uni-armor", "records": 2}, {"name": "Lightsabre", "mule": "uni-weap", "records": 1}]}}
        self.assertEqual(self.ca.accept_handed_copy_audit(body, {"p": "main"}, now_ms=T), (True, None))
        (rows, why, as_of), sec = self._section()
        self.assertEqual(as_of, T, "the section is not dated by when the board handed its records")
        self.assertEqual(sec["asOf"], T)
        self.assertEqual(sec["counts"], 2)
        self.assertEqual(sorted((r["name"], r["locker"]) for r in sec["rows"]), [("Lightsabre", "uni-weap"), ("Shako", "uni-armor")])
        say = self.ca.copy_audit_payload(now_ms=T + 1000)["rosterVault"]
        self.assertEqual((say["rows"], say["asOf"], say["why"]), (2, T, None))

    def test_a_board_that_could_not_read_its_records_sends_none(self):
        self.ca.accept_handed_copy_audit({"copyAudit": {"ok": False, "why": "the vault block is not on this page"}},
                                         {"p": "main"}, now_ms=T)
        (rows, why, as_of), sec = self._section()
        self.assertEqual((rows, sec), (None, None), "a refused readout became an empty vault")
        self.assertIn("could not read its vault records", why)
        self.assertIn("not on this page", why)

    def test_an_empty_locker_set_is_a_measured_zero(self):
        self.ca.accept_handed_copy_audit({"copyAudit": {"ok": True, "at": T, "rows": []}}, {"p": "main"}, now_ms=T)
        (rows, why, as_of), sec = self._section()
        self.assertEqual(sec, {"asOf": T, "counts": 0}, "a board with nothing filed is not a read that found nothing")

    def test_the_publish_lane_builds_it_from_the_records_not_the_accum_file(self):
        src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        reads = src.split("def _roster_reads(", 1)[1].split("\ndef ", 1)[0]
        code = "\n".join(l.split("#", 1)[0] for l in reads.split("\n"))
        self.assertEqual(code.count("rows, why, as_of = _roster_vault_from_records()"), 1)
        self.assertNotIn("VAULT_LEDGER_PATH", code, "the upload's vault section still reads the accum ledger")
        self.assertIn("vault_read(", code)


RED_PROOF = [
    {"why": "REG-2817 - the section is dated by this moment instead of when the board handed its records",
     "file": "tv/control_app.py",
     "find": "    return rows, None, int(at)\n",
     "replace": "    return rows, None, int(time.time() * 1000)\n",
     "matches": 1},
    {"why": "REG-2817 - a board that never handed its records publishes an empty vault",
     "file": "tv/control_app.py",
     "find": "        return None, \"the board has not handed its vault records since this console started\", None\n",
     "replace": "        return [], None, int(time.time() * 1000)\n",
     "matches": 1},
    {"why": "REG-2817 - a refused readout publishes an empty vault",
     "file": "tv/control_app.py",
     "find": "        return None, (\"the board could not read its vault records: \" + str(a.get(\"why\") or \"no reason given\"))[:200], None\n",
     "replace": "        return [], None, int(at)\n",
     "matches": 1},
    {"why": "REG-2817 - the upload's vault section goes back to the accum ledger",
     "file": "tv/control_app.py",
     "find": "    rows, why, as_of = _roster_vault_from_records()\n    if rows is None:\n        _ROSTER_FAIL[\"vault\"] = why\n",
     "replace": "    _acc, _w, _mt = _vault_store_read(VAULT_LEDGER_PATH)\n    rows, why, as_of = _roster_vault_from_records()\n    if rows is None:\n        _ROSTER_FAIL[\"vault\"] = why\n",
     "matches": 1},
    {"why": "REG-2817 - the readout stops saying what the upload's vault section is built from",
     "file": "tv/control_app.py",
     "find": "    return {\"rows\": (len(rows) if rows is not None else None), \"asOf\": as_of, \"why\": why}\n",
     "replace": "    return {\"rows\": (len(rows) if rows is not None else 0), \"asOf\": as_of, \"why\": None}\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
