# -*- coding: utf-8 -*-
"""THE ADMISSION BAR MUST BE ABLE TO NAME WHAT IT WOULD ADMIT — AND WHAT IT WOULD THROW OUT.

#105 established the rule: only ledger+proof enters the vault. It was measured — 14 names carry a
corroborated proof — and then his vault went on showing 165 items, because the LOCKERS are built
from `d2r_owned` (222 names) routed by `d2r_muleAssign`, and **the board holds no proof store at
all**: the only `d2r_vault*` keys in bible.html are Backfill, BackfillUndo, EvidenceRestore,
Removed and RerouteDone. The witnesses live in `vault_accum.json`, on the console's side.

So the bar was designed, measured, written down, and never told to the surface it governs.
[[the-unjoined-end]] [[plumbing-with-no-tap]]

⚠⚠ AND NAMING THE 14 IS WHY THIS GATE EXISTS, BECAUSE THE NAMES CHANGE THE RULING. Measured on
his tree, 2026-09-17:

    Full Rejuvenation Potion · Super Mana Potion · Horadric Cube · Radiance (103 witnesses)
    six Grand Charms · Bone Break · Magefist · Heart of the Oak · Renewed Black Cleft

Every one is a consumable, a charm, or the Cube. **Not one is a unique or set piece his vault
actually holds** — no Shako, no Tal Rasha, no Griswold. They cleared the bar because an OCR sweep
sees a rejuv potion in every stash frame and a Shako in one.

So "only ledger+proof enters", applied literally, would **empty his vault of every real keeper and
keep the potions**. A count alone said "14 earn it" and sounded like progress; the NAMES say the
bar is measuring frame frequency, not worth. A population is not a verdict until you have read
what is in it. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

This law does not enforce the bar. It keeps the door honest and keeps that finding attached to it,
so nobody — me included — wires "only 14 may enter" to his lockers on the strength of the count.
"""
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
import live_store as LS


class TestTheAdmissionBarKnowsWhatItWouldAdmit(unittest.TestCase):

    # ⚠⚠ THE SKIP BELONGS TO ONE LAW, NOT THE WHOLE CLASS. It was in setUp, so on any clone
    # without his `vault_accum.json` — GitHub CI, a fresh checkout — unittest skipped ALL FIVE
    # cases and the gate exited 0. `Gate("test_admission_bar")` then reported GREEN having
    # exercised nothing, which is the precise defect `live_store` was built to make visible:
    # "a gate that always skips is the same defect as one that is always green."
    # Named by a cross-family review of v3246, the version that introduced it.
    #
    # Only ONE law here reads his real ledger. The other four stub `vault_ledger_load` and are
    # therefore venue-independent — they must run everywhere, and they are the ones that pin the
    # contract. [[regression-guard]] [[feedback-blind-fixture-green-gate]]
    def _needs_his_ledger(self):
        LS.require(self, "vault_accum.json",
                   why="this law reads his REAL vault ledger; the others stub the loader and run "
                       "in any venue")

    # ── THE DOOR ─────────────────────────────────────────────────────────────────────────────
    def test_it_names_them_rather_than_only_counting_them(self):
        """★ A count said '14 earn it' and sounded like progress. The names said otherwise."""
        self._needs_his_ledger()
        r = CA.vault_proven_names()
        self.assertTrue(r.get("ok"), "the door could not read the ledger: %r" % r.get("why"))
        proven = r.get("proven")
        self.assertIsInstance(proven, list, "the door returns a count with no list, so nobody can "
                                            "read WHAT would be admitted — which is the whole "
                                            "finding")
        self.assertEqual(len(proven), r.get("provenN"), "the count and the list disagree")
        for row in proven:
            self.assertTrue(str(row.get("name") or "").strip(), "an admitted row has no name")
            self.assertGreaterEqual(row.get("witnesses") or 0, r.get("bar"),
                                    "%r is below the bar it was admitted by" % row.get("name"))

    def test_an_unreadable_ledger_is_UNKNOWN_and_never_an_empty_set(self):
        """★ An empty `proven` reaching the board marks everything he owns as unproven — a wipe
        of meaning, from a failed read."""
        real = CA.vault_ledger_load
        CA.vault_ledger_load = lambda *a, **k: (_ for _ in ()).throw(IOError("gone"))
        self.addCleanup(setattr, CA, "vault_ledger_load", real)
        r = CA.vault_proven_names()
        self.assertFalse(r.get("ok"))
        self.assertIsNone(r.get("proven"),
                          "an unreadable ledger produced a LIST — every name he owns would be "
                          "marked unproven on the strength of a failed read: %r" % (r,))
        self.assertIn("UNKNOWN", r.get("why") or "", "the refusal does not say it is unknown")

    def test_a_malformed_row_falls_short_rather_than_crashing_the_door(self):
        """★ `{"witnesses": 2}` made `len(2)` a TypeError, uncaught, in a door the heart and his
        board both read — a crash renders as a blank chip with no reason. A row whose witnesses
        are not a list has not been SHOWN to carry any, so it counts as zero."""
        real = CA.vault_ledger_load
        CA.vault_ledger_load = lambda *a, **k: {"owned": [
            {"name": "int-witnesses", "witnesses": 2},
            {"name": "none-witnesses", "witnesses": None},
            {"name": "real", "witnesses": [{"s": 1}, {"s": 2}]},
        ]}
        self.addCleanup(setattr, CA, "vault_ledger_load", real)
        r = CA.vault_proven_names(min_witnesses=2)
        self.assertTrue(r.get("ok"), "a malformed row took the whole door down: %r" % r)
        self.assertEqual([x["name"] for x in r["proven"]], ["real"],
                         "a row whose `witnesses` is an int was admitted on the strength of a "
                         "number that is not a witness list: %r" % r)
        self.assertEqual(r.get("shortOfBar"), 2, "the malformed rows were not counted as short")

    def test_the_door_never_returns_None_so_a_caller_cannot_miss_the_refusal(self):
        """⚠ `{"ok": False}` is a live truthy dict. A caller writing `if not door():` would sail
        straight past an unreadable ledger — so the contract line must not promise None."""
        real = CA.vault_ledger_load
        CA.vault_ledger_load = lambda *a, **k: (_ for _ in ()).throw(IOError("gone"))
        self.addCleanup(setattr, CA, "vault_ledger_load", real)
        r = CA.vault_proven_names()
        self.assertIsInstance(r, dict, "the door returned a non-dict, so `ok` cannot be read")
        self.assertTrue(r, "the door returned something falsy — a caller checking truthiness "
                           "would read a refusal as 'nothing to do'")
        import io as _io
        with _io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        # ⚠ THE CONTRACT LINE, NOT THE BLOCK. My first cut read 400 characters of the docstring
        # and matched the sentence that EXPLAINS the old wrong contract — "(The first version of
        # this line said "dict | None" ...)" — so a law about the promise failed on the paragraph
        # correcting it. Fourth time today prose has blinded a guard of mine; the window has to
        # be the one line that makes the promise. [[feedback-comments-vs-code]]
        i = src.find("def vault_proven_names(")
        self.assertNotEqual(i, -1, "the door moved — re-anchor this gate")
        j = src.find('"""', i)
        contract = src[j:src.find("\n", j)]
        self.assertIn("->", contract, "the docstring's first line states no return type: %r"
                                      % contract)
        # ⚠ BAN THE TYPE UNION, NOT THE WORD. The corrected line reads "-> ALWAYS a dict,
        # never None" — it uses the token to say the OPPOSITE, so banning `None` failed the law
        # on the sentence that satisfies it. That is the SAME mistake three times inside one
        # gate: ban what the code DOES, never a word it contains. [[feedback-comments-vs-code]]
        for union in ("| None", "|None", "-> None", "or None"):
            self.assertNotIn(union, contract,
                             "the contract line promises %r, which this door never returns — the "
                             "UNKNOWN lives in `proven`, inside the dict, and a caller checking "
                             "`is None` would sail past a refusal: %r" % (union, contract))

    def test_a_ledger_of_the_wrong_shape_is_also_UNKNOWN(self):
        real = CA.vault_ledger_load
        CA.vault_ledger_load = lambda *a, **k: {"owned": "not a list"}
        self.addCleanup(setattr, CA, "vault_ledger_load", real)
        r = CA.vault_proven_names()
        self.assertFalse(r.get("ok"))
        self.assertIsNone(r.get("proven"))

    def test_the_bar_is_stated_once_and_is_honoured(self):
        """★ THE BAR SELECTS, on a ledger whose witness counts are KNOWN.

        ⚠ My first version compared two bars against HIS ledger and asserted `high <= low`. Every
        one of his 14 rows clears a bar of 2, so removing the bar entirely left both sets at 14
        and `14 <= 14` passed — a sabotage that deletes the comparison sails straight through a
        law written with `assertLessEqual`. A law that cannot distinguish "selected" from "let
        everything through" is measuring nothing. [[sabotage-is-usually-the-wrong-one]]"""
        real = CA.vault_ledger_load
        CA.vault_ledger_load = lambda *a, **k: {"owned": [
            {"name": "one-witness", "witnesses": [{"session": "s"}], "conf": 0.5},
            {"name": "two-witness", "witnesses": [{"session": "s"}, {"session": "t"}], "conf": 0.6},
            {"name": "five-witness", "witnesses": [{"session": str(i)} for i in range(5)],
             "conf": 0.9},
        ]}
        self.addCleanup(setattr, CA, "vault_ledger_load", real)

        at2 = CA.vault_proven_names(min_witnesses=2)
        self.assertEqual([r["name"] for r in at2["proven"]], ["five-witness", "two-witness"],
                         "a bar of 2 admitted the wrong set — the one-witness row must be held "
                         "out and both others let in: %r" % at2)
        self.assertEqual(at2.get("shortOfBar"), 1,
                         "the door does not report how many fell SHORT, so a bar that admits "
                         "nothing is indistinguishable from a ledger that is empty")

        at5 = CA.vault_proven_names(min_witnesses=5)
        self.assertEqual([r["name"] for r in at5["proven"]], ["five-witness"],
                         "a bar of 5 did not select down to the single row that clears it: %r"
                         % at5)
        self.assertEqual(at5.get("bar"), 5, "the door does not report the bar it used")

        at99 = CA.vault_proven_names(min_witnesses=99)
        self.assertEqual(at99["proven"], [],
                         "a bar nothing clears still admitted rows, so the bar is decoration")
        self.assertEqual(at99.get("shortOfBar"), 3,
                         "all three fell short and the door did not say so")

    # ── THE FINDING THE COUNT HID ────────────────────────────────────────────────────────────
    def test_the_finding_is_recorded_beside_the_door(self):
        """⚠ The names are the finding. If this docstring's measurement is ever deleted, the next
        reader sees '14 earn it' and wires the bar to his lockers."""
        import io as _io
        with _io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        i = src.find("def vault_proven_names(")
        self.assertNotEqual(i, -1, "the door is gone — re-anchor this gate")
        j = src.find("\ndef ", i + 1)
        doc = src[i:j]
        self.assertIn("d2r_owned", doc,
                      "the door does not record that the LOCKERS render a different population, "
                      "which is the reason the bar gates nothing")
        self.assertIn("UNKNOWN", doc,
                      "the door does not record that an unreadable ledger must not read as none")


if __name__ == "__main__":
    unittest.main(verbosity=2)
