# -*- coding: utf-8 -*-
"""#246 W7 — THE ONE DOOR, WATCHED: the doctor's 'vault provenance' row, and every arm of it seen RED.

heart-first: a thing that works is not finished; a thing that can be seen to work, and shouts when it stops, is.
The one door (window.vaultFile) makes a false filing impossible from here on — and says nothing about the 173
already in his map, or about a door that quietly starts refusing everything. So the console doctor carries a
row that reads the board's own stores (through the ONE board read per tick) and the console's own ledgers:

  1. filings with NO witness row          — must be 0 (his map reads its false vault here, honestly)
  2. MAIN-locked names sitting in a mule   — must be 0 (furniture law · MAIN ledger · a 3-session lane lock)
  3. stash rows that clear TODAY'S gate and are not filed — the witnessed lane that cannot land
  4. the unattended feeder's banked-of-runs, reported beside the verdict, never as it
and it is UNKNOWN — never OK — when the board could not be asked.

WHAT THIS LAW HOLDS: the verdict is a PURE function, driven arm by arm with fixtures (game item names only, never
his store); the row reads the board through the shared read and answers UNKNOWN without it; furniture and
consumables are never reported as "unfiled"; and the row is registered, declared and explained.

#246 review — TWO ANSWERS THE ROW GAVE THAT NOTHING HAD MEASURED:
  · arm 3 counted rows the lane can NEVER file: a shared-stash name (suggestMule's one null; the door answers
    'no-home') and a set piece the lane had filed under its slot-suffixed name. Driven through the REAL
    vaultAccumApply on a copy of his store, the row stayed MISSING for ever and told him to press register —
    advice that cannot work. Those are now reported beside, never as a gap, read from the board's own
    SHARED_STASH_RE and the generated set roster.
  · its OK read "no MAIN item sits in a mule" while his real MAIN ledger locked 0 of 7 tracked rows. With
    filings in the mules and nothing that locks, the row is UNKNOWN; its OK names what locked.
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

import console_doctor as D  # noqa: E402
import corroborate as C  # noqa: E402

TWO = [{"session": "s_a", "frame": "f_a.jpg", "conf": 0.9}, {"session": "s_b", "frame": "f_b.jpg", "conf": 0.85}]
MAGE = [{"session": "s_1", "frame": None, "conf": 0.0}, {"session": "s_2", "frame": "f_2.jpg", "conf": 0.85}]
ROW = {"mule": "uni-armor", "source": "stash"}
NOBODY_LOCKED = (lambda n: (False, ""))


def _v(assign, prov, accum=(), feeder=None, locked=NOBODY_LOCKED):
    return D.vault_provenance_verdict(assign, prov, {}, list(accum) if accum is not None else None,
                                      feeder if feeder is not None else {"runs": 7, "banked": 0}, locked_fn=locked)


class TheVaultProvenanceRowCanGoRed(unittest.TestCase):

    def test_a_clean_vault_is_ok(self):
        st, why, c = _v({"Nagelring": "uni-small"}, {"Nagelring": ROW})
        self.assertEqual(D.OK, st, why)
        self.assertEqual((1, 1, 0, 0), (c["filings"], c["witnessed"], c["unwitnessed"], c["mainInMule"]))

    def test_arm_1_a_filing_with_no_witness_is_red(self):
        st, why, c = _v({"Nagelring": "uni-small", "Windforce": "uni-weap"}, {"Nagelring": ROW})
        self.assertEqual(D.MISSING, st, why)
        self.assertEqual(1, c["unwitnessed"])
        self.assertIn("Windforce", why, "the row does not name the unwitnessed filing")

    def test_arm_2_a_main_item_in_a_mule_is_red(self):
        st, why, c = _v({"Gore Rider": "uni-armor"}, {"Gore Rider": ROW},
                        locked=lambda n: (n == "Gore Rider", "his gear"))
        self.assertEqual(D.MISSING, st, why)
        self.assertEqual(1, c["mainInMule"])
        self.assertIn("Gore Rider in uni-armor", why)

    def test_arm_3_a_gate_passing_stash_row_left_unfiled_is_red(self):
        accum = [{"name": "Nagelring", "lane": "stash", "witnesses": TWO},
                 {"name": "Magefist", "lane": "stash", "witnesses": MAGE},
                 {"name": "Horadric Cube", "lane": "stash", "witnesses": TWO},
                 {"name": "Super Mana Potion", "lane": "stash", "witnesses": TWO},
                 {"name": "Stormshield", "lane": "equipment", "witnesses": TWO}]
        st, why, c = _v({}, {}, accum=accum,
                        locked=lambda n: (n == "Horadric Cube", "furniture"))
        self.assertEqual(D.MISSING, st, why)
        self.assertEqual(1, c["gatePassingUnfiled"], "only Nagelring clears today's gate and is loot in a stash: %s" % why)
        self.assertIn("Nagelring", why)
        for n in ("Magefist", "Horadric Cube", "Super Mana Potion", "Stormshield"):
            self.assertNotIn(n, why, "%s was reported as a stash row waiting to be filed" % n)

    def test_arm_3_never_counts_a_row_no_mule_can_hold(self):
        """#246 review — a shared-stash name has no mule (the door refuses it 'no-home'), and a set piece the lane
        filed under its canonical name IS filed. Neither is a gap; the shared-stash one is reported beside."""
        accum = [{"name": "Cold Rupture", "lane": "stash", "witnesses": TWO},
                 {"name": "Black Cleft", "lane": "stash", "witnesses": TWO},
                 {"name": "Tal Rasha's Horadric Crest", "lane": "stash", "witnesses": TWO},
                 {"name": "Nagelring", "lane": "stash", "witnesses": TWO}]
        filed = {"Tal Rasha's Horadric Crest (helm)": "sets-major"}
        st, why, c = _v(filed, {"Tal Rasha's Horadric Crest (helm)": ROW}, accum=accum)
        self.assertEqual(1, c["gatePassingUnfiled"], "only Nagelring can still be filed by the lane: %s" % why)
        self.assertEqual(2, c["gatePassingNoMule"], "the shared-stash rows were not reported beside: %s" % why)
        self.assertIn("(first: Nagelring)", why)
        self.assertIn("belong in the shared stash", why)
        st2, why2, c2 = _v(filed, {"Tal Rasha's Horadric Crest (helm)": ROW}, accum=accum[:3])
        self.assertEqual(D.OK, st2, "a vault whose only unfiled rows can never be filed read %s: %s" % (st2, why2))
        self.assertNotIn("press register", why2, "the row advises a press that can never file anything: %s" % why2)

    def test_arm_3_a_row_his_reset_held_is_said_beside_never_as_press_register(self):
        """#41 rank 1 — the row told him to press register for 11 stash rows the reset's Wilson plan had just HELD, which
        would undo the hold. A reset-held row is reported beside (held by his reset, the 2-look door would file it),
        never counted as a gap; a row the reset did not hold is still the gap it was."""
        accum = [{"name": "Nagelring", "lane": "stash", "witnesses": TWO},
                 {"name": "Windforce", "lane": "stash", "witnesses": TWO}]
        held = {"Nagelring": "held by your reset at 2026-09-29T07:00:00Z"}
        st, why, c = D.vault_provenance_verdict({}, {}, {}, accum, {"runs": 1, "banked": 0}, locked_fn=NOBODY_LOCKED,
                                                reset_held=held)
        self.assertEqual(D.MISSING, st, "BASELINE: Windforce is still a gap: %s" % why)
        self.assertEqual((1, 1), (c["gatePassingUnfiled"], c["gatePassingResetHeld"]), why)
        self.assertEqual(["Nagelring"], c["gatePassingResetHeldNames"])
        self.assertIn("(first: Windforce)", why)
        self.assertIn("held by your reset", why)
        st2, why2, c2 = D.vault_provenance_verdict({}, {}, {}, accum[:1], {"runs": 1, "banked": 0}, locked_fn=NOBODY_LOCKED,
                                                   reset_held=held)
        self.assertEqual(D.OK, st2, "a vault whose only unfiled row his reset held read %s: %s" % (st2, why2))
        self.assertNotIn("press register", why2, "the row still prompts a press that would undo his reset's hold: %s" % why2)
        self.assertIn("Nagelring", why2)
        st3, why3, c3 = D.vault_provenance_verdict({}, {}, {}, accum[:1], {"runs": 1, "banked": 0}, locked_fn=NOBODY_LOCKED)
        self.assertEqual(D.MISSING, st3, "BASELINE: with no reset receipt the same row is the gap it always was")

    def test_the_row_reads_the_reset_receipt_off_the_same_board_read(self):
        real = D._board_read
        try:
            rec = {"door": "vaultClearHistory", "at": "2026-09-29T07:00:00Z", "heldNames": ["Nagelring"]}
            D._board_read = lambda: {"ok": True, "fullStores": {"d2r_muleAssign": "{}", "d2r_vaultProv": "{}",
                                                                 "d2r_vaultLastReset": json.dumps(rec)}}
            st, why, c = D._vault_provenance_counts()
            self.assertIsInstance(c, dict, why)
            self.assertIsNotNone(c.get("gatePassingResetHeld"), "the counts carry no reset-held figure: %r" % c)
        finally:
            D._board_read = real

    def test_the_reset_hold_joint_is_registered_and_reads_two_records(self):
        """The corroborator's `a-reset-hold-is-not-a-register-prompt`: LEFT the backup lane's snapshot of the reset receipt
        plus the live gate, RIGHT the doctor's own verdict — driven on fixtures, both directions."""
        import tempfile, shutil, os as _os
        names = [b()[0] for b in C.BUILDERS]
        self.assertIn("a-reset-hold-is-not-a-register-prompt", names)
        tmp = tempfile.mkdtemp(prefix="reset-hold-joint-")
        env = {k: _os.environ.get(k) for k in ("TV_VAULT_LEDGER", "TV_LEDGER_BACKUP_DIR")}
        real = D._vault_provenance_counts
        try:
            ledger = _os.path.join(tmp, "vault_accum.json")
            with open(ledger, "w", encoding="utf-8") as fh:
                json.dump({"owned": [{"name": "Nagelring", "lane": "stash", "witnesses": TWO},
                                     {"name": "Windforce", "lane": "stash", "witnesses": TWO}]}, fh)
            bdir = _os.path.join(tmp, "backups")
            _os.makedirs(bdir)
            rec = {"door": "vaultClearHistory", "at": "2026-09-29T07:00:00Z", "heldNames": ["Nagelring"]}
            with open(_os.path.join(bdir, "ledger_2026-09-29_070100.json"), "w", encoding="utf-8") as fh:
                json.dump({"allStores": {"d2r_vaultLastReset": json.dumps(rec), "d2r_muleAssign": "{}"}}, fh)
            _os.environ["TV_VAULT_LEDGER"], _os.environ["TV_LEDGER_BACKUP_DIR"] = ledger, bdir
            inv = [b for b in C.BUILDERS if b()[0] == "a-reset-hold-is-not-a-register-prompt"][0]
            D._vault_provenance_counts = lambda: (D.OK, "", {"gatePassingResetHeld": 1})
            row = C.check_one(inv)
            self.assertEqual(C.AGREE, row["state"], row)
            self.assertEqual((1, 1), (row["left"]["value"], row["right"]["value"]))
            D._vault_provenance_counts = lambda: (D.MISSING, "press register", {"gatePassingResetHeld": 0})
            row2 = C.check_one(inv)
            self.assertEqual(C.DISAGREE, row2["state"], "a doctor that prompted register for a reset-held row was not caught")
            D._vault_provenance_counts = lambda: (D.UNKNOWN, "no console", None)
            self.assertEqual(C.UNKNOWN, C.check_one(inv)["state"])
        finally:
            D._vault_provenance_counts = real
            for k, v in env.items():
                if v is None:
                    _os.environ.pop(k, None)
                else:
                    _os.environ[k] = v
            shutil.rmtree(tmp, ignore_errors=True)

    def test_an_unreadable_route_is_unknown_never_a_gap(self):
        blind = lambda n: (None, n)
        st, why, c = D.vault_provenance_verdict({}, {}, {}, [{"name": "Nagelring", "lane": "stash", "witnesses": TWO}],
                                                {"runs": 1, "banked": 0}, locked_fn=NOBODY_LOCKED, route_fn=blind)
        self.assertEqual((0, 1), (c["gatePassingUnfiled"], c["gatePassingRouteUnknown"]), why)
        self.assertIn("UNKNOWN", why)

    def test_arm_2_ok_is_only_as_wide_as_what_locks(self):
        """#246 review — his real MAIN ledger tracks rows and locks none (each under 3 sightings). Zero locks is not
        zero MAIN items: with filings in the mules the row is UNKNOWN and never says "no MAIN item sits in a mule"."""
        filed = {"Nagelring": "uni-small", "Stormshield": "uni-armor"}
        prov = {"Nagelring": ROW, "Stormshield": ROW}
        for label, ms in (("locks none", {"ok": True, "locked": [], "tracked": 7, "blockedWhy": ""}),
                          ("unreadable", {"ok": False, "locked": None, "why": "the MAIN ledger is unreadable"})):
            st, why, c = D.vault_provenance_verdict(filed, prov, {}, [], {"runs": 1, "banked": 0},
                                                    locked_fn=NOBODY_LOCKED, main_state=ms)
            self.assertEqual(D.UNKNOWN, st, "%s: a MAIN arm that measured nothing read %s: %s" % (label, st, why))
            self.assertNotIn("no MAIN item sits in a mule", why)
            self.assertIn("UNKNOWN", why)
        st, why, c = D.vault_provenance_verdict(filed, prov, {}, [], {"runs": 1, "banked": 0}, locked_fn=NOBODY_LOCKED,
                                                main_state={"ok": True, "locked": [{"name": "Gore Rider"}], "tracked": 7})
        self.assertEqual(D.OK, st, why)
        self.assertIn("locks 1 of 7", why, "the OK does not say what the MAIN arm could see: %s" % why)
        st, why, c = D.vault_provenance_verdict({}, {}, {}, [], {"runs": 1, "banked": 0}, locked_fn=NOBODY_LOCKED,
                                                main_state={"ok": True, "locked": [], "tracked": 7})
        self.assertEqual(D.OK, st, "an empty vault cannot hold a MAIN item: %s" % why)

    def test_arm_4_unknown_is_said_never_counted_as_zero(self):
        st, why, c = _v({}, {}, accum=None, feeder=None)
        self.assertIsNone(c["gatePassingUnfiled"], "an unreadable stash ledger was counted as zero waiting")
        self.assertIn("UNKNOWN", why)
        st2, why2, _c2 = _v({}, {}, feeder={"runs": 12141, "banked": 0})
        self.assertIn("banked 0 row(s) in 12141 run(s)", why2)

    def test_the_row_reads_the_board_through_the_shared_read(self):
        real = D._board_read
        try:
            D._board_read = lambda: None
            self.assertEqual(D.UNKNOWN, D._check_vault_provenance()[0], "no board read answered something other than UNKNOWN")
            D._board_read = lambda: {"ok": True, "fullStores": {
                "d2r_muleAssign": json.dumps({"Nagelring": "uni-small", "Windforce": "uni-weap"}),
                "d2r_vaultProv": json.dumps({"Nagelring": ROW})}}
            st, why = D._check_vault_provenance()
            self.assertEqual(D.MISSING, st, why)
            self.assertIn("Windforce", why)
        finally:
            D._board_read = real

    def test_the_row_is_registered_declared_and_explained(self):
        self.assertIn("vault provenance", dict(D.CHECKS))
        self.assertIn("vault provenance", D.WATCHES)
        self.assertIn("vault provenance", C.NO_JOINT_YET)
        self.assertNotIn("vault provenance", C.COVERED_BY)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 W7 - arm 1 goes blind: a filing with no witness row is never counted",
        "file": "console_doctor.py",
        "find": "    unwitnessed = [n for n in filings if n not in prov]\n",
        "replace": "    unwitnessed = []\n",
        "matches": 1,
    },
    {
        "why": "#246 W7 - arm 2 goes blind: a MAIN-locked name in a mule is never reported",
        "file": "console_doctor.py",
        "find": "        ok, why = locked_fn(n)\n        if ok:\n            in_mule.append((n, h, why))\n",
        "replace": "        ok, why = locked_fn(n)\n",
        "matches": 1,
    },
    {
        "why": "#246 W7 - arm 3 goes blind: a gate-passing stash row left unfiled is never reported",
        "file": "console_doctor.py",
        "find": "        if gv.get(\"pass\"):\n            gate_unfiled.append(nm)\n",
        "replace": "        if False:\n            gate_unfiled.append(nm)\n",
        "matches": 1,
    },
    {
        "why": "#246 review - arm 3 counts a shared-stash row (no mule exists for it) as a gap again",
        "file": "console_doctor.py",
        "find": "        if gv.get(\"pass\") and routable is False:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "#246 review - arm 3 misses a set piece the lane filed under its slot-suffixed name again",
        "file": "console_doctor.py",
        "find": "        if canon in assign:\n            continue",
        "replace": "        if False:\n            continue",
        "matches": 1,
    },
    {
        "why": "#246 review - the OK says 'no MAIN item sits in a mule' again when nothing locks",
        "file": "console_doctor.py",
        "find": "    if main_state is not None and filings and not main_locks and not lane_locks:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#246 W7 - the row is dropped from the doctor's roster, so nothing ever runs it",
        "file": "console_doctor.py",
        "find": "    (\"vault provenance\", _check_vault_provenance),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 1 - a row his reset held is counted as a gap again, so the doctor prompts a press that would undo the hold",
        "file": "console_doctor.py",
        "find": "        if gv.get(\"pass\") and (nm in held_by_reset or canon in held_by_reset):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 1 - the joint's backup side counts every gate-passing row, held or not, so a doctor that prompts register agrees with it",
        "file": "corroborate.py",
        "find": "            if not nm or nm not in held or str(r.get(\"lane\") or \"\").lower() != \"stash\" or nm in (assign or {}):\n",
        "replace": "            if not nm or str(r.get(\"lane\") or \"\").lower() != \"stash\" or nm in (assign or {}):\n",
        "matches": 1,
    },
]
