# -*- coding: utf-8 -*-
"""WRITING ONE GATE SHUT NINETEEN LOCKS, AND THAT IS WHY MOST OF THEM WERE NEVER WIRED TO ANYTHING.

`may()` asks `_heart_says_watched()` before it asks about the surface at all, and that check fails
closed when the heart census is STALE — which it becomes the moment any GATE FILE changes. Measured
2026-09-12, in a single session of writing gates: the census staled four separate times, and on
each one every lock in the registry answered `may=False` with the same sentence about the census
rather than anything about itself.

So the obvious way to finish #84 — wire `may()` into each action site — would have meant: someone
edits a test, and his console loses those features until a ~38-minute re-prove or the overnight
routine catches up. A guard whose false-refusals are caused by ordinary development is a guard
people route around, and then it guards nothing.

HIS RULING, 2026-09-12, and it splits by REVERSIBILITY rather than by convenience:

  · an act that CANNOT BE UNDONE keeps the whole guarantee. A prover that has not caught up is
    reason enough to refuse to delete footage ("there is no undo"), drop the ledger, mule items
    between characters, or spend money on a sweep. Five locks carry `destructive: True`, each
    justified by its own `acts` string rather than by an opinion.
  · an act that REPORTS, WALKS or DECIDES refuses on MERIT alone. "The instrument is out of date"
    is a fact about the instrument; it says nothing about whether that surface has earned the
    right to act.

⚠⚠ AND BLIND IS NOT STALE. A blind instrument is a gate that CANNOT FAIL — that is a fact about
supervision itself, and it fails closed for everything, destructive or not. Collapsing the two
would hand back exactly the confidence the blind-gate work exists to withhold.
[[stale-reading]] [[feedback-blind-fixture-green-gate]] [[unknown-stays-unknown]]
"""
import ast
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

import self_arming as SA  # noqa: E402

STALE_WHY = ("the heart census is STALE: the gate files have changed since it ran "
             "(aaaa != bbbb). The last proof does not speak for the instruments now on disk.")
BLIND_WHY = ("2 instrument(s) are BLIND (some-gate, other-gate) — a surface may not arm itself "
             "while the gates that would catch its failure cannot fail.")


class TestAStaleProverIsNotASafetyVerdict(unittest.TestCase):

    def setUp(self):
        self._real = SA._heart_says_watched

    def tearDown(self):
        SA._heart_says_watched = self._real

    def _with_heart(self, why):
        SA._heart_says_watched = lambda: (False, why)

    def _a_lock(self, destructive):
        for k, v in SA.LOCKS.items():
            if bool(v.get("destructive")) is destructive:
                return k
        return None

    def test_the_two_phrases_still_exist_in_the_branches_they_came_from(self):
        """THE SNIFF GUARD. heart_block_kind() matches TEXT, so a silent reword in
        _heart_says_watched would classify every stale census as 'other' and refuse everything
        again — the outage this split exists to prevent, arriving quietly. Parsed, not grepped:
        the phrases must appear inside that function's own body."""
        tree = ast.parse(io.open(os.path.join(HERE, "self_arming.py"), encoding="utf-8").read())
        fn = None
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == "_heart_says_watched":
                fn = n
        self.assertIsNotNone(fn, "_heart_says_watched is gone — this whole law is about its output")
        body = " ".join(x.value for x in ast.walk(fn)
                        if isinstance(x, ast.Constant) and isinstance(x.value, str))
        for phrase, label in ((SA._HEART_STALE_PHRASE, "stale"), (SA._HEART_BLIND_PHRASE, "blind")):
            self.assertIn(
                phrase, body,
                "_heart_says_watched no longer says %r, so heart_block_kind() can never classify "
                "a %s verdict again and every one of them would be treated as 'other' — which "
                "refuses EVERY lock, destructive or not." % (phrase, label))

    def test_an_ordinary_act_is_judged_on_merit_while_the_prover_catches_up(self):
        """The whole point: writing a gate must not take features off his console."""
        lock = self._a_lock(False)
        self.assertIsNotNone(lock, "no ordinary lock in the registry to test with")
        self._with_heart(STALE_WHY)
        ok, why = SA.may(lock)
        self.assertNotIn(
            "STALE", str(why),
            "%s refused with the census sentence rather than its own. A stale prover is being "
            "treated as a verdict about the surface, so editing a gate still shuts ordinary "
            "actions." % lock)

    def test_an_irreversible_act_still_refuses_on_a_stale_prover(self):
        """The half that must NOT soften. These are the doors with no undo."""
        lock = self._a_lock(True)
        self.assertIsNotNone(lock, "no destructive lock is declared — the split has no teeth")
        self._with_heart(STALE_WHY)
        ok, why = SA.may(lock)
        self.assertFalse(
            ok, "%s is destructive and was permitted while the heart census was STALE. Its own "
                "acts string is the argument against it." % lock)
        self.assertIn("STALE", str(why),
                      "%s refused, but not for the stale census — the reason he would read is "
                      "wrong even though the verdict is right" % lock)

    def test_a_BLIND_instrument_refuses_everything_including_ordinary_acts(self):
        """Blind is not stale. A gate that cannot fail is a fact about supervision."""
        for destructive in (True, False):
            lock = self._a_lock(destructive)
            self._with_heart(BLIND_WHY)
            ok, why = SA.may(lock)
            self.assertFalse(
                ok, "%s (destructive=%s) was permitted while instruments were BLIND. A gate that "
                    "cannot fail is not an out-of-date instrument — it is no instrument."
                    % (lock, destructive))

    def test_every_destructive_lock_says_why_in_its_own_acts_string(self):
        """The classification must be readable from the data, not from a private opinion."""
        d = {k: v for k, v in SA.LOCKS.items() if v.get("destructive")}
        self.assertTrue(d, "nothing is marked destructive, so the split protects nothing")
        for k, v in d.items():
            self.assertTrue(str(v.get("acts") or "").strip(),
                            "%s is marked destructive and does not say what it does" % k)


RED_PROOF = [
    {
        "why": "softens the rule to ALL locks, so an irreversible door — deleting footage with no "
               "undo, dropping the ledger — would act while the prover has not caught up",
        "file": "self_arming.py",
        "find": 'if not (heart_block_kind(_hwhy) == "stale" and not spec.get("destructive")):',
        "replace": 'if not (heart_block_kind(_hwhy) == "stale"):',
        "matches": 1,
    },
    {
        "why": "makes BLIND soften like STALE, handing back the exact confidence a blind gate "
               "exists to withhold",
        "file": "self_arming.py",
        "find": '    if _HEART_BLIND_PHRASE in w:\n        return "blind"',
        "replace": '    if _HEART_BLIND_PHRASE in w:\n        return "stale"',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
