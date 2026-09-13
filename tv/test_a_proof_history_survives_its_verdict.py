# -*- coding: utf-8 -*-
"""A CHECK'S PROOF HISTORY MUST REACH EVERY BRANCH, AND A VESSEL MUST INHERIT ITS WATCHER'S SCORE.

Two breaks, found together, both the shape this tree keeps producing: built at both ends, joined on
one path only.

⚠⚠ BREAK 1 — THE SCORER ONLY RAN WHEN NOTHING WAS WRONG. `_row` computes the Wilson number from
`k`/`n` in ONE place, correctly, and `check_self_arming` passed them on its **OK** return and on
NEITHER of the others. So the moment a lock actually went inert — the finding that whole check
exists to make — the row lost `proofK`, `proofN` and `score` entirely, because `_row` only scores
when `n` is not None.

MEASURED on his live console before the fix: the selfArming row was `state=warn` and carried no k,
no n and no score KEY AT ALL. After: `proofK=556 proofN=564 score=0.9723`. Five hundred and
sixty-four sabotages of evidence, invisible precisely when something was wrong.

A proof history does not depend on today's verdict. A lock sabotaged 564 times and refusing 556 has
that history whether the answer is OK, WARN or UNKNOWN — and the heart needs it MOST when the answer
is not OK. [[the-unjoined-end]] [[zero-needs-a-denominator]]

⚠⚠ BREAK 2 — THE LOOKUP ASKED IN A VOCABULARY NOTHING ANSWERED IN. `heart.vessels()` builds
`scored` from the organ rows and then asks `scored.get(watcher)` where `watcher` is a LANE name from
the census (`_drift_loop`, `_orphan_watch`, ...). The dict was keyed ONLY on organ ids — `lanes`,
`readers`, `selfArming`, `board_join`, `laneLiveness`. **The intersection of those two vocabularies
is empty**, so FLOWING was unreachable by any path, for any vessel, ever.

Every organ row already answers "what do you watch" in `surfaces`. Keying by that too is the bridge:
MEASURED, 20 surfaces now resolve to a proven score where none did before.

⚠ AND FLOWING IS STILL `None`, WHICH IS NOW THE TRUE ANSWER RATHER THAN AN ARTEFACT. The 20 vessels
are watched by `laneLiveness`, which carries no score because nobody has ever sabotaged it. That is
UNPROVEN — work owed — and it must never be drawn as 0, which would mean "tested and never refused".
[[unknown-stays-unknown]]
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _fn(module, name):
    with io.open(os.path.join(HERE, module), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("%s.%s is gone" % (module, name))


class TestAProofHistorySurvivesItsVerdict(unittest.TestCase):

    def test_every_row_return_carries_the_proof_tally(self):
        """PARSED, not grepped — a law that reads source must parse it."""
        fn = _fn("health_engine.py", "check_self_arming")
        rets = [n for n in ast.walk(fn)
                if isinstance(n, ast.Return) and isinstance(n.value, ast.Call)
                and getattr(n.value.func, "id", "") == "_row"]
        self.assertGreaterEqual(len(rets), 2, "check_self_arming no longer branches")
        # ⚠ THE RULE IS "EVERY RETURN THAT HAS A PROOF QUEUE", not "at most one may skip". The
        # three UNKNOWN returns fire BEFORE `locks` is bound — the queue could not be read at all —
        # so they have nothing to tally and must not pretend to. A count-based threshold would
        # have let a real verdict branch go naked as soon as a fourth UNKNOWN path appeared.
        verdicts, naked = [], []
        for r in rets:
            state = getattr(r.value.args[1], "id", "?") if len(r.value.args) >= 2 else "?"
            if state == "UNKNOWN":
                continue                     # no queue to count
            verdicts.append((r.lineno, state))
            kw = {k.arg for k in r.value.keywords}
            if "n" not in kw or "k" not in kw:
                naked.append((r.lineno, state))
        self.assertTrue(verdicts, "check_self_arming no longer returns a verdict at all")
        self.assertEqual(
            naked, [],
            "%d verdict return(s) omit k/n: %s. A row that drops its proof history on a bad verdict "
            "makes the score vanish exactly when something is wrong — measured, the live warn row "
            "carried no k, no n and no score at all, hiding 564 sabotages of evidence"
            % (len(naked), naked))
        print("check_self_arming: %d verdict return(s) %s — all carry k and n"
              % (len(verdicts), [s for _l, s in verdicts]))

    def test_the_warn_branch_specifically_scores(self):
        """The branch that fires ON A FINDING is the one that used to lose the number."""
        fn = _fn("health_engine.py", "check_self_arming")
        found = False
        for n in ast.walk(fn):
            if not (isinstance(n, ast.Return) and isinstance(n.value, ast.Call)):
                continue
            if getattr(n.value.func, "id", "") != "_row":
                continue
            args = n.value.args
            if len(args) >= 2 and getattr(args[1], "id", "") == "WARN":
                found = True
                kw = {k.arg for k in n.value.keywords}
                self.assertIn("n", kw, "the WARN return dropped its proof tally again")
                self.assertIn("k", kw, "the WARN return dropped its proof tally again")
        self.assertTrue(found, "the WARN branch is gone — it is the one that reports inert locks")
        print("the WARN branch carries k and n")

    def test_a_vessel_can_inherit_its_watchers_score(self):
        """The bridge: `scored` must be keyed by what organs WATCH, not only by organ ids."""
        import health_engine as H
        organs = H.report().get("rows") or []
        ids = {str(r.get("id") or "") for r in organs}
        surfaces = set()
        for r in organs:
            surfaces.update(str(s) for s in (r.get("surfaces") or []) if s)
        self.assertTrue(surfaces, "no organ names a single surface — nothing can inherit a score")
        # the two vocabularies really are different; that WAS the bug
        self.assertFalse(surfaces & ids,
                         "organ ids and surface names overlap now, so this law no longer proves "
                         "the bridge is needed — re-derive it")
        src = io.open(os.path.join(HERE, "heart.py"), encoding="utf-8").read()
        i = src.find("    scored = {}")
        self.assertGreater(i, 0, "heart.py no longer builds `scored`")
        block = src[i:i + 2200]
        code = "\n".join(l.split("#", 1)[0] for l in block.splitlines())
        self.assertIn('r.get("surfaces")', code,
                      "`scored` is keyed on organ ids alone again — the lookup asks for LANE names, "
                      "the two vocabularies do not intersect, and FLOWING becomes unreachable by "
                      "any path for any vessel")
        print("scored is keyed by %d surface name(s) as well as %d organ id(s)"
              % (len(surfaces), len(ids)))

    def test_unproven_is_never_drawn_as_zero(self):
        """`None` (nobody tested it) and `0.0` (tested, never refused) are opposite facts."""
        import heart
        v = heart.vessels()
        counts = v.get("counts") or {}
        self.assertIn("FLOWING", counts, "the vessel table lost its FLOWING count")
        if counts.get("FLOWING") is None:
            self.assertTrue(str(v.get("flowingWhy") or "").strip(),
                            "FLOWING is None and nothing says why — an unmeasured number with no "
                            "sentence beside it reads as zero to every human who sees it")
            print("FLOWING is None (unmeasured) and carries a reason — correct")
        else:
            print("FLOWING = %s" % counts.get("FLOWING"))


RED_PROOF = [
    {
        "why": "the WARN branch drops its proof tally again, so the moment a lock goes inert the "
               "row loses proofK/proofN/score and 564 sabotages of evidence vanish exactly when "
               "something is wrong",
        "file": "health_engine.py",
        "find": '''                    % (len(inert), worst.get("lock")), ev, k=tot_k, n=tot_n,''',
        "replace": '''                    % (len(inert), worst.get("lock")), ev,''',
        "matches": 1,
    },
    {
        "why": "`scored` goes back to organ ids alone, so the lookup (which asks for LANE names) "
               "finds nothing and FLOWING is unreachable for every vessel",
        "file": "heart.py",
        "find": '''        for _surf in (r.get("surfaces") or []):''',
        "replace": '''        for _surf in ():''',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
