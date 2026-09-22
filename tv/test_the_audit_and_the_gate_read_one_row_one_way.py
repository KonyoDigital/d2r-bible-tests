# -*- coding: utf-8 -*-
"""v3415 — THE AUDIT AND THE SHIP GATE MUST READ ONE ROW ONE WAY.

v3403 taught `looked_at` — and therefore `owes_a_look`, and therefore the push gate — that a
verdict of `cannot-tell` is NOT a look. `audit()` never learned it, so one row was read two ways.

MEASURED on the real v3413 row before the fix:

    verdict=cannot-tell   reached=True   family=xai   _has_evidence=True
    looked_at('v3413')  -> 0        owes_a_look('v3413') -> True     (the gate: OWED)
    audit() row         -> looks: 1                                  (the audit: OK )

The gate refused the push, and its own refusal message says *"To see the state: python3
tv/second_eye_ledger.py --audit"* — sending the reader to the one screen that called that row
fine. [[the-unjoined-end]]: the fix was applied at one end of a two-ended thing.

⚠ AND `looks` FEEDS THREE SURFACES, not one: the --audit mark, the --audit headline (`_owed`),
and --backlog's queue in second_eye_run.py all derive from it. They were blind together, which is
why this is fixed at the classification and not at three call sites. [[copy-drift]]

⚠ THIS GATE OWNS ITS OWN LEDGER. `tv/.second_eye.jsonl` is not tracked, so a case that read the
live file would measure his machine and skip on a runner — a permanent skip that reads as a pass.
Every case here builds a temp ledger holding all five row kinds and asks BOTH predicates about it.
[[feedback-fixtures-never-touch-live-data]] [[regression-guard]] §3
"""
import io
import json
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402

XAI = "grok-4-1-fast-reasoning"          # a different family from the author
AUTHOR = "claude-opus-4"                 # the family that writes the code


def _row(version, model=XAI, verdict="clean", reached=True, **kw):
    r = {"version": version, "model": model, "verdict": verdict, "reached": reached,
         "ts": time.time(), "findings": [], "sha": "deadbeef",
         "bytes": {"bible": 1}, "answerFull": "a real answer", "answerHead": "a real answer"}
    r.update(kw)
    return r


def _ledger(rows):
    fd, p = tempfile.mkstemp(suffix=".jsonl", prefix="eye_gate_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return p


class TestTheAuditAndTheGateReadOneRowOneWay(unittest.TestCase):

    def setUp(self):
        self._paths = []

    def tearDown(self):
        for p in self._paths:
            try:
                os.remove(p)
            except Exception:
                pass

    def _both(self, rows, version):
        """-> (audit_says_ok, gate_says_ok) for the SAME temp ledger."""
        p = _ledger(rows)
        self._paths.append(p)
        got = [s for s in L.audit(path=p) if s["version"] == version]
        self.assertEqual(len(got), 1, "audit() did not produce exactly one row for %s" % version)
        return bool(got[0]["looks"]), (not L.owes_a_look(version, path=p)), got[0]

    # ---- the baseline: the two surfaces CAN both say OK, or the cases below are vacuous -----

    def test_BASELINE_a_real_look_satisfies_BOTH(self):
        a, g, row = self._both([_row("v9001", verdict="clean")], "v9001")
        self.assertTrue(a, "the audit refuses even a clean look — every case below would then "
                           "agree for the wrong reason")
        self.assertTrue(g, "the gate refuses even a clean look")

    def test_BASELINE_a_findings_verdict_is_still_a_look(self):
        """Finding something is the eye WORKING. Only 'could not judge' is a non-look."""
        a, g, _ = self._both([_row("v9002", verdict="findings",
                                   findings=[{"what": "x"}])], "v9002")
        self.assertTrue(a)
        self.assertTrue(g)

    # ---- the defect ------------------------------------------------------------------------

    def test_a_cannot_tell_is_not_a_look_on_EITHER_surface(self):
        a, g, row = self._both([_row("v9003", verdict="cannot-tell")], "v9003")
        self.assertFalse(g, "the gate stopped refusing a could-not-judge verdict")
        self.assertFalse(a, "the AUDIT still counts a could-not-judge as a look — this is the "
                            "v3415 defect: one row, two readings, and the gate's own refusal "
                            "message points the reader at this screen")
        self.assertEqual(row["cannot"], 1,
                         "the could-not-judge row vanished instead of being counted as its own "
                         "state — recorded, and NOT a look")

    def test_the_two_surfaces_agree_on_every_row_kind(self):
        """The LAW, not a number: whatever the ledger holds, the two must answer alike."""
        KINDS = (
            ("v9101", dict(verdict="clean")),
            ("v9102", dict(verdict="findings", findings=[{"what": "x"}])),
            ("v9103", dict(verdict="cannot-tell")),
            ("v9104", dict(reached=False)),                       # an empty seat
            ("v9105", dict(model=AUTHOR)),                        # the family that wrote it
            ("v9106", dict(verdict="")),                          # no verdict at all
        )
        rows = [_row(v, **kw) for v, kw in KINDS]
        p = _ledger(rows)
        self._paths.append(p)
        bad = []
        for v, _kw in KINDS:
            got = [s for s in L.audit(path=p) if s["version"] == v][0]
            if bool(got["looks"]) != (not L.owes_a_look(v, path=p)):
                bad.append((v, got["looks"], L.owes_a_look(v, path=p)))
        self.assertEqual(bad, [], "the audit and the ship gate disagree about %d row kind(s): %r "
                                  "— one row must not have two readings" % (len(bad), bad))

    def test_a_cannot_tell_does_not_count_as_BOUND_evidence_either(self):
        """A non-look cannot supply the byte-binding that makes a look trustworthy."""
        _a, _g, row = self._both([_row("v9004", verdict="cannot-tell")], "v9004")
        self.assertEqual(row["bound"], 0,
                         "a could-not-judge row was counted as evidence bound to bytes")

    def test_a_cannot_tell_beside_a_real_look_still_leaves_the_version_looked_at(self):
        """One honest non-answer must not erase a genuine look taken alongside it."""
        a, g, row = self._both([_row("v9005", verdict="cannot-tell"),
                                _row("v9005", verdict="clean")], "v9005")
        self.assertTrue(a, "a real look was thrown away because a could-not-judge sat beside it")
        self.assertTrue(g)
        self.assertEqual((row["looks"], row["cannot"]), (1, 1),
                         "the two rows were not counted as one look and one non-look")

    def test_the_count_is_still_carried_not_discarded(self):
        """Recorded, never silently dropped — a non-look nobody can see is a non-look nobody
        will re-ask. [[unknown-stays-unknown]]"""
        _a, _g, row = self._both([_row("v9006", verdict="cannot-tell"),
                                  _row("v9006", verdict="cannot-tell")], "v9006")
        self.assertEqual(row["cannot"], 2)
        self.assertEqual(row["attempts"], 2, "the attempts count stopped matching the rows")

    # ---- and his screen has to say it -------------------------------------------------------

    def test_the_audit_screen_names_the_could_not_judge(self):
        """The gate sends him HERE. This screen must explain the refusal, not contradict it."""
        src = io.open(os.path.join(HERE, "second_eye_ledger.py"),
                      encoding="utf-8", errors="replace").read()
        self.assertIn('cannot-tell=%d', src,
                      "the --audit row never prints the could-not-judge count, so a version it "
                      "marks OWED gives no reason and reads like one nobody ever asked")


RED_PROOF = [
    {
        "why": "v3415 - THE MISCOUNT, RESTORED. Counting a could-not-judge as a look is exactly "
               "the pre-fix behaviour: audit said OK looks=1 for the same v3413 row the push gate "
               "refused, and the gate's refusal pointed the reader at that screen.",
        "file": "second_eye_ledger.py",
        "find": '            st["cannot"] += 1',
        "replace": '            st["looks"] += 1',
        "matches": 1,
    },
    {
        "why": "v3415 - THE TEST BLINDED. With the verdict never consulted, a could-not-judge "
               "falls through to the plain look branch and the two surfaces disagree again.",
        "file": "second_eye_ledger.py",
        "find": '        elif fam and _has_evidence(r) and is_not_a_look(r.get("verdict")):',
        "replace": '        elif fam and _has_evidence(r) and False:',
        "matches": 1,
    },
    {
        "why": "v3415 - THE REASON WITHHELD. Without the printed count a version reads OWED with "
               "no explanation, which is indistinguishable from one nobody ever asked - and the "
               "difference decides whether to re-ask or to widen the payload.",
        "file": "second_eye_ledger.py",
        "find": '("  cannot-tell=%d \\u2014 recorded, and NOT a look"',
        "replace": '("" ',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
