# -*- coding: utf-8 -*-
"""REG-1703 - `second_eye_run.py --backlog --dry` MUST SEND NOTHING.

MEASURED 2026-10-02: the backlog branch called run_one(v) without --dry, so a dry run asked Grok for a real look. A time
bound on the caller then killed the parent and left the `grok -p` child orphaned (ppid 1), its answer recordable by
nobody. A flag that says "send nothing" and sends is worse than no flag: it is the one a careful caller reaches for.

What this law drives: the REAL main() with the ledger's audit and the history stubbed to owe two versions, and run_one
replaced by a recorder - every owed version must reach run_one with dry=True when --dry is given, and with dry=False
when it is not (so the case can tell the two apart).
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

import second_eye_run as R  # noqa: E402


class ADryBacklogSendsNothing(unittest.TestCase):

    def drive(self, argv):
        calls = []
        saved = (R.run_one, R.versions_in_history, R.SEL.audit, R.SEL.owes_a_look)
        self.addCleanup(lambda: (setattr(R, "run_one", saved[0]), setattr(R, "versions_in_history", saved[1]),
                                 setattr(R.SEL, "audit", saved[2]), setattr(R.SEL, "owes_a_look", saved[3])))
        R.SEL.audit = lambda *_a, **_k: [{"version": "v9001", "looks": 0}, {"version": "v9002", "looks": 1}]
        R.SEL.owes_a_look = lambda v: True
        R.versions_in_history = lambda *_a, **_k: (["v9003"], None)
        R.run_one = lambda v, **kw: calls.append((v, kw.get("dry", False))) or True
        self.assertEqual(R.main(argv), 0)
        return calls

    def test_every_owed_version_is_built_dry(self):
        calls = self.drive(["--backlog", "--dry"])
        self.assertEqual(sorted(v for v, _ in calls), ["v9001", "v9003"], "the owed set changed: %r" % calls)
        self.assertTrue(all(d is True for _, d in calls), "a --dry backlog asked for a real look: %r" % calls)

    def test_without_dry_it_really_asks(self):
        """premise: the recorder can tell the two apart"""
        calls = self.drive(["--backlog"])
        self.assertTrue(calls and all(d is False for _, d in calls), calls)


RED_PROOF = [
    {
        "why": "REG-1703 - the backlog drops --dry again and a dry run sends a real look",
        "file": "second_eye_run.py",
        "find": "        ok = all(run_one(v, dry=a.dry) for v in owed)\n",
        "replace": "        ok = all(run_one(v) for v in owed)\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
