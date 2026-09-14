# -*- coding: utf-8 -*-
"""KONYO'S AMNESTY COVERS WHAT PREDATES THE INSTRUMENT, AND NOTHING AFTER IT.

His ruling, 2026-09-14, after being shown that "drain to 8" and his own condition contradict each
other: *"it can go.. whatever was in the past for here specifically its fine.. just make sure
forward it is all working"*.

⚠⚠ THE MEASUREMENT THAT PRODUCED THE QUESTION. `reel_tombstones.json`'s earliest deletion is
2026-08-24 23:49, and **2,385 of the 2,424 `unknown` rows — 98.4% — are runs that STARTED BEFORE
THAT**. Their film was gone before any instrument existed to record it going. No record was ever
written and none can be manufactured, so his earlier condition ("make sure before it was tallied
and extracted properly") could never be satisfied for them: they would be held forever, and the
river could never reach 8. That is what he waived.

⚠ THE CUTOFF IS DERIVED FROM THE LEDGER, NEVER A CONSTANT. A hardcoded date is a number nobody can
re-derive and one that keeps being true as the tree moves. Reading the ledger's own first entry
means the amnesty covers precisely "older than the instrument" — and the day a reel is tombstoned
earlier, the boundary moves with it. A run that started after the ledger existed is NEVER covered,
no matter how old it later becomes. That is the "forward" half enforced by arithmetic rather than
by intention. [[unknown-stays-unknown]]

⚠ AND THE AMNESTY DOES NOT WAIVE THE ONLY-TRACE HOLD. A row that is the only copy of a find is a
different concern from a row with no retention record, and he ruled on the second. Measured after
the amnesty landed: 389 rows still held, of which the large majority carry payload the evidence
ledger does not cite. If he wants those too, that is a separate sentence he has not said.
"""
import io
import os
import sys
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import journal_retention as JR      # noqa: E402

BEGAN = 1_787_604_588_927           # the real ledger's first deletion, for fixture arithmetic


def _row(sid, t0, state="unknown", **kw):
    r = {"sessionId": sid, "t0": t0, "footageState": state, "footageWhy": ""}
    r.update(kw)
    return r


class TestTheAmnestyCoversOnlyThePast(unittest.TestCase):

    def setUp(self):
        self._began = JR._ledger_began
        self._bank = JR._banked_reels
        self.addCleanup(lambda: setattr(JR, "_ledger_began", self._began))
        self.addCleanup(lambda: setattr(JR, "_banked_reels", self._bank))
        JR._banked_reels = lambda: (set(), None)
        # enough dated rows that "the newest 8" is never what does the work
        self.filler = [_row("s_filler_%03d" % i, BEGAN + 500_000 + i, state=JR.EXTRACTED)
                       for i in range(12)]

    def _plan(self, extra, began=(BEGAN, None)):
        JR._ledger_began = lambda: began
        return JR.plan(self.filler + extra, hist_dir=os.path.join(HERE, "no-such-frames"))

    def test_a_run_older_than_the_ledger_is_released(self):
        row = _row("s_before", BEGAN - 1)
        p = self._plan([row])
        rel = {r["sessionId"] for r in p["release"]}
        print("   started 1ms BEFORE the ledger -> released: %s" % ("s_before" in rel))
        self.assertIn("s_before", rel,
                      "a run whose film was gone before the ledger existed is held for a record "
                      "that could never have been written — it would be held forever")

    def test_a_run_younger_than_the_ledger_is_held(self):
        """★ THE FORWARD HALF. This is the clause that makes the amnesty an amnesty rather than a
        repeal."""
        row = _row("s_after", BEGAN + 1)
        p = self._plan([row])
        rel = {r["sessionId"] for r in p["release"]}
        held = {r["sessionId"]: r["why"] for r in p["keep"]}
        print("   started 1ms AFTER the ledger  -> released: %s" % ("s_after" in rel))
        self.assertNotIn("s_after", rel,
                         "a run the ledger COULD have recorded was released without a record — "
                         "that is the amnesty creeping forward, which is the one thing his ruling "
                         "excluded")
        self.assertIn("s_after", held)

    def test_an_unreadable_ledger_grants_no_amnesty(self):
        """No beginning means no boundary, and a boundary nobody can compute may not be assumed."""
        row = _row("s_before", BEGAN - 1)
        p = self._plan([row], began=(None, "the ledger could not be read"))
        rel = {r["sessionId"] for r in p["release"]}
        print("   with an UNREADABLE ledger -> released: %s" % ("s_before" in rel))
        self.assertNotIn("s_before", rel,
                         "the amnesty fired with no boundary to measure against — unknown must "
                         "hold on a path that deletes")

    def test_the_amnesty_does_not_waive_the_only_trace_hold(self):
        """He ruled on rows with no retention record. A row that is the only copy of a find is a
        different concern and he has not spoken to it."""
        row = _row("s_before_payload", BEGAN - 1, finds=[{"name": "Shako"}], topFind="Shako")
        p = self._plan([row])
        rel = {r["sessionId"] for r in p["release"]}
        held = {r["sessionId"]: r["why"] for r in p["keep"]}
        print("   pre-ledger row CARRYING a find -> released: %s" % ("s_before_payload" in rel))
        self.assertNotIn("s_before_payload", rel,
                         "the amnesty released a row that is the only trace of a find — it waives "
                         "the missing-record hold, not the only-copy hold")
        self.assertIn("only trace", held["s_before_payload"])

    def test_the_boundary_is_derived_not_hardcoded(self):
        """⚠ A hardcoded date is a number nobody can re-derive and one that keeps being true as the
        tree moves. The boundary must come from the ledger itself."""
        import ast
        with io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_ledger_began"), None)
        self.assertIsNotNone(fn, "_ledger_began is gone")
        big = [n.value for n in ast.walk(fn)
               if isinstance(n, ast.Constant) and isinstance(n.value, int) and n.value > 1_000_000]
        attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        print("   _ledger_began: %d hardcoded epoch-like constant(s) · reads %s"
              % (len(big), sorted(a for a in attrs if "tombstone" in a)))
        self.assertEqual(big, [],
                         "_ledger_began carries a hardcoded timestamp %s — the boundary must be "
                         "READ from the ledger so it cannot drift from the instrument it describes"
                         % big)
        self.assertIn("_tombstone_path", attrs,
                      "_ledger_began does not ask reel_retention for the ledger path")


    # ── the label on the delete path must not claim a proof the waiver replaced ───────────────
    def test_an_amnesty_release_does_not_claim_a_proof(self):
        """⚠⚠ THE ONE LINE HE READS BEFORE APPROVING A DELETION. Every release used to say "film
        was retired after giving up its information" — with an EMPTY tail, because a waived row has
        no `footageWhy` — and the summary said they "have a proof of extraction". Measured on a
        fixture: `5 of 13 … have a proof of extraction` when four had one and the fifth was the
        waiver. The waiver is precisely the case where no proof exists.
        [[label-outlived-referent]] [[zero-needs-a-denominator]]"""
        row = _row("s_before", BEGAN - 1)
        p = self._plan([row])
        got = next(r for r in p["release"] if r["sessionId"] == "s_before")
        print("   amnesty row why: %r" % got["why"][:70])
        self.assertTrue(got.get("amnesty"), "the release does not mark itself as a waiver")
        self.assertNotIn("giving up its information", got["why"],
                         "a waived row claims the proof label of a genuinely retired one")
        self.assertIn("WAIVER and not a proof", p["say"],
                      "the summary folds waivers and proofs into one count: %r" % p["say"])
        self.assertEqual(p.get("amnesty"), 1,
                         "the plan does not report how many of its releases are waivers")

    def test_a_genuine_proof_is_still_called_a_proof(self):
        """The correction may not turn every release into a waiver — that would be the same
        conflation pointing the other way."""
        row = _row("s_real", BEGAN + 5, state=JR.EXTRACTED, footageWhy="read and sealed")
        p = self._plan([row])
        got = next(r for r in p["release"] if r["sessionId"] == "s_real")
        print("   retired row why: %r" % got["why"][:70])
        self.assertFalse(got.get("amnesty"))
        self.assertIn("giving up its information", got["why"])

RED_PROOF = [
    {
        "why": "an amnesty release goes back to wearing the proof label, so the one line he reads "
               "before approving a deletion says extraction happened for rows where it provably "
               "never did",
        "file": "journal_retention.py",
        "find": "            _amnesty = (str(s.get(\"footageState\") or \"\") != EXTRACTED)",
        "replace": "            _amnesty = False",
        "matches": 1,
    },
    {
        "why": "the amnesty stops checking the boundary, so every row with no retention record is "
               "released regardless of when it ran — his ruling covered the past and this would "
               "make it cover the future too",
        "file": "journal_retention.py",
        "find": "                  and not (began and isinstance(s.get(\"t0\"), (int, float)) and s[\"t0\"] < began)):",
        "replace": "                  and False):",
        "matches": 1,
    },
    {
        "why": "an unreadable ledger starts granting amnesty to everything — a boundary nobody "
               "could compute, assumed rather than measured, on a path that deletes",
        "file": "journal_retention.py",
        "find": "        return None, \"the retention ledger could not be read (%s)\" % type(e).__name__",
        "replace": "        return 9999999999999, None",
        "matches": 1,
    },
    {
        "why": "the boundary becomes a hardcoded constant instead of the ledger's own first entry, "
               "so it cannot follow the instrument it claims to describe",
        "file": "journal_retention.py",
        "find": "    return min(stamps), None",
        "replace": "    return 1787604588927, None",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
