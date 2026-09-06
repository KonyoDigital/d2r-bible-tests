# -*- coding: utf-8 -*-
"""v2746 — THE CARD CALLED HIS OWN CHRONICLE "INHERITED", AND THE NEW FIELD MUST NOT REPEAT v2739.

MEASURED on his LIVE /api/fleet, not inferred:

    NICKNAME   install       onOwnerSeed   ledgerName
    Dean       f8ceea724d93  True          None
    Konyo      23d0486747ce  True          None      <- HIS OWN BOARD
    Wife PC    6ee926f9d70d  None          None

`tv/control_ui.html` renders the warning on `t.onOwnerSeed === true` with no exclusion, so KONYO'S
OWN CARD said his 292 uniques "were inherited, not synced". They are his. The flag is not wrong — it
answers "does this world resolve to the seed ledger" — but that question has the SAME ANSWER on the
board the seed was written from and on a board that merely inherited it. A true flag under a
sentence that means something else. [[label-outlived-referent]]

His rule settles it: *"one board being seedable is legitimate (it's yours); two is contamination."*
That is a FLEET judgement no single row can make, so the card stops accusing and instead reports
what the authority measured per ledger — true on either board, and strictly more informative:

    uniques    SEEDED   of 292, the owner's seed supplies 246 - about 46 were earned on that board
    runewords  SEEDED   the seed can supply 99 and this board reports only 94 - 5 rows MISSING

⚠⚠ THE SECOND LINE IS THE ONE THAT MATTERS: a store holding FEWER rows than the seed would have
written CANNOT have been seeded. That is a disproof of inheritance, and the blanket warning could
never express it. It is how Dean's runewords were shown to be his own.

=== WHY THIS FILE EXISTS AT ALL: v2739 SHIPPED THIS EXACT DEFECT ===
v2739 computed `onOwnerSeed` on the board AND read it on the card, and the SHAPER BETWEEN THEM —
`functions/api/console.js` — did not forward it. Both ends built, never joined; the field existed at
both ends and never arrived. Adding a SECOND field without adding it to the shaper repeats that
precisely, so this gate walks all three hops. [[the-unjoined-end]] [[plumbing-with-no-tap]]
"""
import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

APP = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
WORKER = io.open(os.path.join(ROOT, "functions", "api", "console.js"), encoding="utf-8").read()


def _code_only(blk):
    """Strip comments. A law that matches its own prose about a bug grades nothing.
    [[measured-true-read-wrong]]"""
    out = []
    for ln in (blk or "").split("\n"):
        st = ln.lstrip()
        if st.startswith("#") or st.startswith("//") or st.startswith("*") or st.startswith("/*"):
            continue
        out.append(ln)
    return "\n".join(out)


class TheVerdictReachesTheCard(unittest.TestCase):

    # ── HOP 0: the subjects exist ─────────────────────────────────────────────────────────────
    def test_the_guard_can_find_all_three_hops(self):
        self.assertIn("def grail_tally", APP, "the tally builder is gone")
        self.assertIn("onOwnerSeed", WORKER, "the worker no longer shapes the seed fields at all")
        self.assertIn("ftt-seed", UI, "the card's seed block is gone")

    # ── HOP 1: the tally COMPUTES it ──────────────────────────────────────────────────────────
    def test_the_tally_carries_the_authority_verdict(self):
        i = APP.find("def grail_tally")
        j = APP.find("\ndef ", i + 1)
        blk = _code_only(APP[i:j])
        self.assertIn('out["ledgerVerdict"]', blk,
                      "the tally no longer carries the authority's verdict, so the card is back to "
                      "a bare boolean that cannot tell his board from Dean's")
        self.assertIn("classify_row", blk,
                      "the verdict is no longer produced by ledger_authority.classify_row")

    def test_a_failed_classification_is_UNKNOWN_not_a_cheerful_default(self):
        i = APP.find("def grail_tally")
        j = APP.find("\ndef ", i + 1)
        blk = _code_only(APP[i:j])
        self.assertIn('"ok": False', blk,
                      "a verdict that could not be computed no longer marks itself not-ok, so it "
                      "would render as 'nothing inherited here' — a clean answer nobody measured")

    # ── ⚠⚠ HOP 2: THE SHAPER, WHICH IS THE ONE v2739 FORGOT ───────────────────────────────────
    def test_the_worker_FORWARDS_the_verdict(self):
        self.assertIn("ledgerVerdict", WORKER,
                      "functions/api/console.js does not forward ledgerVerdict. This is EXACTLY the "
                      "v2739 defect: the field is computed on the board and read on the card, and "
                      "the shaper between them drops it, so it exists at both ends and never "
                      "arrives.")

    def test_the_worker_does_not_RE_DERIVE_the_verdict(self):
        """Passing the authority's own object through is the point. Re-deriving any part of it in
        the worker creates a second opinion nobody reconciles — the copy-drift shape."""
        i = WORKER.find("ledgerVerdict")
        seg = WORKER[i:i + 300]
        for bad in ("seedSupplies", "provenance:", "SEEDED"):
            self.assertNotIn(bad, seg,
                             "the worker appears to RECOMPUTE part of the verdict (%r) instead of "
                             "forwarding it" % bad)

    # ── HOP 3: the card RENDERS it, and stops accusing ────────────────────────────────────────
    def test_the_card_prefers_the_per_ledger_verdict(self):
        i = UI.find("var _lvRows")
        self.assertGreater(i, 0, "the card no longer builds per-ledger rows from the verdict")
        seg = _code_only(UI[i:i + 1400])
        self.assertIn("t.ledgerVerdict", _code_only(UI[max(0, i - 400):i + 400]),
                      "the card no longer reads the verdict")
        self.assertIn("ftts-row", seg, "the per-ledger row markup is gone")

    def test_the_blanket_sentence_is_a_FALLBACK_not_the_first_answer(self):
        """⚠ THE REGRESSION THIS GUARDS. If the blanket warning is evaluated before the verdict,
        his own card accuses him again and every other law here still passes."""
        i_rows = UI.find("var _lvRows")
        # ⚠ THE APOSTROPHE IS AN ESCAPE IN THE SOURCE, NOT A LITERAL. The file stores
        # `OWNER\u2019S`, so searching for the rendered curly character finds NOTHING and this law
        # would fail on a correct file — the third time apostrophe bytes have misled a search in
        # this session alone. Match the escaped form, and fall back to the literal.
        i_blanket = UI.find("running on the OWNER\\u2019S SEED")
        if i_blanket < 0:
            i_blanket = UI.find(u"running on the OWNER\u2019S SEED")
        self.assertGreater(i_blanket, 0, "the fallback sentence is gone entirely")
        self.assertLess(i_rows, i_blanket,
                        "the blanket 'inherited, not synced' sentence is reached BEFORE the "
                        "per-ledger verdict, so the accusation renders on his own board again")

    def test_UNKNOWN_is_styled_as_its_own_state(self):
        """A console that did not answer must not look like one that answered 'clean'."""
        self.assertIn("ftts-unknown", UI,
                      "UNKNOWN no longer has its own treatment, so an unanswered console renders "
                      "identically to a measured-clean one")

    # ── the authority itself must actually disprove inheritance, not just describe it ─────────
    def test_the_authority_can_DISPROVE_inheritance_from_counts(self):
        """⚠ THE LOAD-BEARING DIRECTION. Dean's runewords are 94 against a seed of 99. A store with
        FEWER rows than the seed would have written cannot have been seeded, and that is the only
        thing counting can prove. If this stops working, the card loses its one real disproof."""
        import ledger_authority as LA
        row = {"uniques": {"have": 249, "total": 403}, "sets": {"have": 128, "total": 135},
               "runewords": {"have": 94, "total": 99},
               "onOwnerSeed": True, "ledgerName": None, "seedLedger": "KonyoEndgame"}
        v = LA.classify_row(row)
        rw = [L for L in (v.get("ledgers") or []) if L.get("ledger") == "runewords"]
        self.assertTrue(rw, "the verdict no longer reports a runewords ledger")
        why = str(rw[0].get("why") or "")
        self.assertIn("94", why, "the runewords verdict no longer cites the measured figure")
        self.assertTrue(re.search(r"MISSING|missing|fewer", why),
                        "the verdict no longer says the store holds FEWER rows than the seed would "
                        "have written — that shortfall is the only disproof of inheritance that "
                        "counting can give. why=%r" % why[:160])

    def test_everything_still_parses(self):
        ast.parse(APP)


if __name__ == "__main__":
    unittest.main(verbosity=2)
