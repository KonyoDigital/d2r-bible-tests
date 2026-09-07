# -*- coding: utf-8 -*-
"""THE VAULT ACCUMULATOR'S PROPOSAL WAS SUPERVISED BY NOTHING.

Konyo, 2026-09-07: *"the vault accumalator that should be connected to the heart of the console
with the vault and joined obivously too"* and *"just make sure its all wired and not stale and
connected to the heart.. we soon will hit the VAULT and start debugging that and start doing
tests"*.

MEASURED before this file: `console_doctor` carried exactly ONE vault row — `vault stores` — and it
asks only whether the three JSON files can be READ. Whether what they OFFER is still acceptable was
asked by nothing.

=== ⚠⚠ WHY THAT MATTERS: A PROPOSAL IS A PHOTOGRAPH ===
The stored proposal records a decision made under the bars that existed when it was taken. The bars
can move afterwards, and then the panel shows rows labelled "OWNED · corroborated" that today's own
rule would call unsure — a stale display over a correct gate.

=== ⚠ AND THE DRIFT HAS ALREADY HAPPENED IN BOTH DIRECTIONS ===
When the task for this was written, `KEEP_MIN_WITNESSES` was 3 and 6 of his 7 stored rows failed
it. Re-measured when it came to be built: the bar is **2** again ("HIS RULING, 2026-09-07") and all
7 pass. The task's own premise had expired between writing and building.

That is not an argument against the row — it is the argument FOR it. A number measured once is not
evidence later, and the only durable answer is something that re-asks. [[inherited-claim-is-not-evidence]]

    at bar 2  ->  7 of 7 pass      (today)
    at bar 3  ->  1 of 7 pass      (what the task recorded)

=== ⚠ NOT DANGEROUS, AND THE ROW MUST NOT PRETEND OTHERWISE ===
`control_app.vault_apply` re-gates at the WRITE (v1595 — "the gate has to hold where the WRITE
happens") and is ALL-OR-NOTHING: a stale proposal cannot land six bad rows, it is REFUSED IN FULL.
So the defect was never a corrupt write; it was that nobody was told the display had gone stale.
The row says the delta and stops there.

⛔ IT NEVER RE-GRADES HIS STORED ROWS AND NEVER TOUCHES THE BAR. Lowering KEEP_MIN_WITNESSES to make
stored rows pass would be repairing the bar to fit the data, and the bar guards a deleter.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402
import vault_retro as VR  # noqa: E402

DSRC = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()


def _row():
    return dict(D.CHECKS)["vault proposal"]


def _blk():
    i = DSRC.find("def _check_the_vault_proposal_still_clears_todays_bar():")
    return DSRC[i:DSRC.find("\ndef ", i + 1)]


def _code_only():
    """The row's CODE with its docstring removed. -> str

    ⚠⚠ THIRD TIME IN ONE SESSION. A law that greps a function's source for a forbidden name reads
    the PROSE as well, and this row's docstring necessarily explains `vault_apply` (the write path
    that re-gates and makes a stale proposal harmless). The law went red on its own explanation —
    exactly as the route lane's TOMBSTONE law did, and its banned-import twin one line below it.
    Judge CODE by parsing; read comments only when judging a MEASUREMENT.
    [[measured-true-read-wrong]] [[source-reading-guard]]
    """
    import ast
    import textwrap
    tree = ast.parse(textwrap.dedent(_blk()))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(getattr(body[0], "value", None), ast.Constant) \
                and isinstance(body[0].value.value, str):
            body.pop(0)
    return ast.unparse(tree)


class TheVaultProposalIsWatched(unittest.TestCase):

    # ── ⚠⚠ THE JOIN ─────────────────────────────────────────────────────────────────────────
    def test_the_row_is_REGISTERED(self):
        """A check defined and not in CHECKS runs never — this repo's most repeated defect."""
        self.assertIn("vault proposal", dict(D.CHECKS),
                      "the vault proposal reaches no screen, so a bar that moves is silent")

    def test_it_is_a_DIFFERENT_question_from_vault_stores(self):
        """⚠ `vault stores` already exists and asks whether the FILES ARE READABLE. That is not
        whether the proposal is still acceptable, and the two are similar enough that the gap
        survived — the same shape as the river's 'position vs flow' pair."""
        self.assertIn("vault stores", dict(D.CHECKS))
        self.assertIsNot(dict(D.CHECKS)["vault stores"], _row())

    def test_it_calls_the_REAL_gate_not_a_second_copy(self):
        """★ A re-implementation of the bar would agree with itself for ever while the real gate
        moved underneath it. Proven by SUBSTITUTION, not by grepping for a name."""
        seen = {"n": 0}
        real = VR.gate

        def counting(ev, *a, **k):
            seen["n"] += 1
            return real(ev, *a, **k)
        VR.gate = counting
        try:
            _row()()
        finally:
            VR.gate = real
        self.assertGreater(seen["n"], 0,
                           "the row never called vault_retro.gate, so it is grading with a rule of "
                           "its own that cannot follow the real bar")

    # ── ⚠⚠ THE INSTRUMENT SCAR, PINNED ──────────────────────────────────────────────────────
    def test_it_passes_the_SIGHTING_LIST_and_reads_the_PASS_key(self):
        """★ MY FIRST MEASUREMENT OF THIS WAS AN INSTRUMENT FAILURE, and it looked like a finding.
        `gate()` takes the list of sightings, not the row dict, and its verdict key is "pass", not
        "ok". Passing the row meant iterating a DICT — which yields its keys — so `ev` filtered to
        [] and every row came back "no evidence at all": a confident **0 of 7 FAIL**, including a
        row with 3 witnesses at conf 0.85 against a bar of 2. The suspiciously clean number was the
        tell. [[feedback-suspect-the-instrument]]"""
        blk = _blk()
        self.assertIn('r.get("witnesses")', blk,
                      "the row does not hand gate() the sighting list, so it is re-running the "
                      "exact call that produced a fake 0 of 7")
        self.assertIn('g.get("pass")', blk,
                      "the row reads a verdict key gate() does not write — a missing key is falsy, "
                      "so every row would grade as failing and the console would cry wolf for ever")

    # ── ⚠⚠ THE DRIFT IT EXISTS FOR ──────────────────────────────────────────────────────────
    def test_it_goes_RED_when_the_bar_MOVES_UP(self):
        """★★ THE WHOLE POINT, and today it can only be shown by simulation because the bar happens
        to agree with the store right now. At bar 3, 6 of his 7 stored rows stop clearing — exactly
        the state the task recorded before the bar moved back to 2."""
        real = VR.KEEP_MIN_WITNESSES
        VR.KEEP_MIN_WITNESSES = 3
        try:
            st, say = _row()()
        finally:
            VR.KEEP_MIN_WITNESSES = real
        self.assertEqual(D.MISSING, st,
                         "the bar moved to 3 and the row still reports fine — a proposal graded by "
                         "a rule that no longer applies, which is the defect this row exists for")
        self.assertIn("no longer clear", say.lower())
        self.assertIn("REFUSED", say,
                      "the row does not say the register button would be refused, so he would "
                      "press a dead end")

    def test_it_reads_OK_when_they_AGREE(self):
        st, say = _row()()
        self.assertIn(st, (D.OK, D.MISSING, D.UNKNOWN))
        if st == D.OK:
            self.assertIn("witnesses", say,
                          "an OK with no bar quoted cannot be re-derived — a clean verdict with no "
                          "denominator")

    # ── ⚠ UNKNOWN IS NOT OK ────────────────────────────────────────────────────────────────
    def test_an_unreadable_store_is_UNKNOWN_never_OK(self):
        import json as _json
        real = _json.load

        def boom(*a, **k):
            raise ValueError("simulated")
        _json.load = boom
        try:
            st, say = _row()()
        finally:
            _json.load = real
        self.assertEqual(D.UNKNOWN, st,
                         "a store nobody could read graded as a measured agreement")
        self.assertIn("UNKNOWN", say)

    def test_a_RAISING_gate_is_UNKNOWN_never_OK(self):
        real = VR.gate

        def boom(*a, **k):
            raise RuntimeError("simulated")
        VR.gate = boom
        try:
            st, _ = _row()()
        finally:
            VR.gate = real
        self.assertEqual(D.UNKNOWN, st,
                         "the gate raised and the row still reached a verdict about rows it never "
                         "graded")

    def test_an_EMPTY_proposal_says_so_rather_than_claiming_agreement(self):
        """[[zero-needs-a-denominator]] — 'nothing stored' and 'everything agrees' are different
        facts and must not share a sentence."""
        blk = _blk()
        self.assertIn("empty proposal, not a disagreement", blk,
                      "an empty proposal has no wording of its own, so it reads as a clean bill")
        self.assertIn("empty queue, not a measured agreement", blk,
                      "a missing store has no wording of its own")

    # ── ⛔ THE THING IT MUST NEVER DO ───────────────────────────────────────────────────────
    def test_it_never_writes_and_never_moves_the_bar(self):
        """⛔ Lowering KEEP_MIN_WITNESSES to make stored rows pass would be repairing the bar to fit
        the data. The bar guards a deleter, and the rows are the stale side."""
        blk = _code_only()
        for banned in ("KEEP_MIN_WITNESSES =", "KEEP_CONF_FLOOR =", "json.dump", "_json.dump",
                       ".write(", "apply_proposal", "vault_apply"):
            self.assertNotIn(banned, blk,
                             "the doctor row reaches for %r. It reports a disagreement; it does "
                             "not resolve one, and it must never move the bar or the store"
                             % banned)

    def test_the_bar_itself_has_not_been_quietly_lowered(self):
        """⚠ Pinned separately from the row, because the cheapest way to make this row go green is
        to move the thing it measures against."""
        self.assertGreaterEqual(VR.KEEP_MIN_WITNESSES, 2,
                                "KEEP_MIN_WITNESSES is %r — below two, a single look corroborates "
                                "itself and the bar stops being a bar" % VR.KEEP_MIN_WITNESSES)
        self.assertGreaterEqual(VR.KEEP_CONF_FLOOR, 0.5,
                                "the confidence floor dropped below 0.5")


if __name__ == "__main__":
    unittest.main(verbosity=2)
