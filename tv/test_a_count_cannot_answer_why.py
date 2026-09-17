# -*- coding: utf-8 -*-
"""A COUNT CANNOT ANSWER "WHY", AND HE HAS ASKED THREE TIMES.

*"vault again is inporperly routing and stashing and vaulting 200+ items.. when it should be alot
less based on what we already established?"* — and later, at a screenshot of the Vault: *"stlll the
vault"*.

Every previous answer was a number. `vault_population()` decomposes it instead. MEASURED on his
board, 2026-09-17:

    owned 222 · filed to a locker 173 · setPieces 133

    uni-armor 68 · uni-weap 64 · sets-major 10 · sets-rest 9
    uni-small  9 · runewords 5 · shared      7 · __keep    1
    UNFILED   49

    of the 222 owned, 50 are ALSO in d2r_setPieces · 172 are not
    of the 49 unfiled, 31 are set pieces          · 18 are not

**172 is exactly his pre-wipe owned count.** So the 222 is 172 possessions plus 50 set pieces the
board also files as physical — one item in two stores, which is the board's own design (possession
versus the set chronicle) and not corruption. What makes the vault LOOK inflated is that 49 of them
are filed nowhere and land in the dock.

⚠ The locker figures match his screenshot exactly — uni-armor 68, uni-weap 64, sets-major 10,
sets-rest 9, uni-small 9, runewords 5. That correspondence is what makes this a reading of HIS
vault and not of a fixture. [[zero-needs-a-denominator]]
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

import control_app as CA


def _board(owned, assign, sets):
    return {"ok": True, "fullStores": {
        "d2r_owned": json.dumps(owned),
        "d2r_muleAssign": json.dumps(assign),
        "d2r_setPieces": json.dumps(sets)}}


class TestACountCannotAnswerWhy(unittest.TestCase):

    # ── THE DECOMPOSITION ────────────────────────────────────────────────────────────────────
    def test_it_splits_owned_into_set_pieces_and_the_rest(self):
        r = CA.vault_population(board=_board(
            ["Shako", "Tal's Mask", "Tal's Armor", "Potion"],
            {"Shako": "uni-armor", "Tal's Mask": "sets-major"},
            ["Tal's Mask", "Tal's Armor"]))
        self.assertTrue(r.get("ok"), r.get("why"))
        self.assertEqual(r["owned"], 4)
        self.assertEqual(r["alsoSetPiece"], 2, "the set-piece overlap is wrong: %r" % r)
        self.assertEqual(r["notSetPiece"], 2)
        self.assertEqual(r["alsoSetPiece"] + r["notSetPiece"], r["owned"],
                         "the two halves do not add back to the whole, so one name is being "
                         "counted twice or lost: %r" % r)

    def test_every_owned_name_lands_in_exactly_one_locker_bucket(self):
        """★ The byLocker figures are what he reads off the screen — they must total the owned."""
        r = CA.vault_population(board=_board(
            ["a", "b", "c", "d", "e"],
            {"a": "uni-armor", "b": "uni-armor", "c": "sets-rest"},
            []))
        self.assertEqual(sum(r["byLocker"].values()), r["owned"],
                         "the locker buckets do not sum to the owned count, so a name is in two "
                         "buckets or none: %r" % r["byLocker"])
        self.assertEqual(r["byLocker"].get("uni-armor"), 2)
        self.assertEqual(r["unfiled"], 2, "an unfiled name was not counted as unfiled")

    def test_the_unfiled_are_split_by_whether_they_are_set_pieces(self):
        r = CA.vault_population(board=_board(
            ["s1", "s2", "x"], {}, ["s1", "s2"]))
        self.assertEqual(r["unfiled"], 3)
        self.assertEqual(r["unfiledSetPieces"], 2,
                         "the unfiled split is wrong — 31 of his 49 are set pieces and that is "
                         "the half that explains the dock: %r" % r)
        self.assertEqual(r["unfiledOther"], ["x"])

    # ── UNKNOWN IS NOT EMPTY ────────────────────────────────────────────────────────────────
    def test_a_board_that_cannot_be_asked_is_UNKNOWN(self):
        r = CA.vault_population(board={"ok": False, "why": "no window"})
        self.assertFalse(r.get("ok"))
        self.assertIsNone(r.get("owned"),
                          "an unreachable board reported a NUMBER — his vault would read as "
                          "empty because nobody could look: %r" % r)
        self.assertIn("UNKNOWN", r.get("why") or "")

    def test_a_store_of_the_wrong_shape_is_UNKNOWN_not_zero(self):
        r = CA.vault_population(board={"ok": True, "fullStores": {"d2r_owned": "{not json"}})
        self.assertFalse(r.get("ok"))
        self.assertIsNone(r.get("owned"))
        self.assertIn("UNKNOWN", r.get("why") or "")

    def test_a_missing_assign_store_does_not_invent_filings(self):
        """⚠ With no d2r_muleAssign every name is UNFILED — which is true, and must not read as
        'filed to a locker called undefined'."""
        r = CA.vault_population(board=_board(["a", "b"], None, []))
        self.assertTrue(r.get("ok"))
        self.assertEqual(r["unfiled"], 2)
        self.assertEqual(list(r["byLocker"]), ["«unfiled»"],
                         "a missing assign store produced locker names: %r" % r["byLocker"])

    # ── IT MAY NOT WRITE ────────────────────────────────────────────────────────────────────
    def test_the_door_is_read_only(self):
        """★ REG-1043: the console may never write a grail store. This one only counts."""
        import ast
        import io as _io
        with _io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "vault_population"), None)
        self.assertIsNotNone(fn, "the door moved — re-anchor this gate")
        # ⚠ BOTH CALL FORMS. The first cut collected only `func.attr` — method calls — so a
        # bare `_vault_autoread_save()` was invisible to it and a sabotage that added exactly
        # that sailed through green. A law that inspects calls has to see the calls.
        # [[source-reading-guard]]
        calls = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Attribute):
                    calls.add(f.attr)
                elif isinstance(f, ast.Name):
                    calls.add(f.id)
        self.assertIn("board_ownership", calls,
                      "the door no longer asks the board at all — this law would then be "
                      "inspecting a function that reads nothing: %s" % sorted(calls))
        for banned in ("setItem", "board_tick", "write", "save",
                       "_vault_autoread_save", "_vault_swept_save", "vault_ledger_save",
                       "owned_restore", "rw_restore", "chronicle_apply"):
            self.assertNotIn(banned, calls,
                             "vault_population calls %r — it is a diagnostic and must not change "
                             "where a single item lives. Calls: %s" % (banned, sorted(calls)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
