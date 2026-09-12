#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every doctor check is either CORROBORATED by a joint or says why it cannot be.

⚠⚠ WHY THIS EXISTS. Measured 2026-09-12: 36 of 59 doctor checks appeared in NEITHER registry, so
for more than half the roster "a joint corroborates this" and "nobody ever looked" were the same
state — indistinguishable, and both silent. A check nobody has classified looks exactly like a
check somebody decided needs no joint, and only one of those is a decision.

⚠ AND THE ROT RAN BOTH WAYS. Two keys — 'reel rungs' and 'cold read exemption' — named doctor
checks that HAVE NEVER EXISTED. `git log -S "reel rungs"` returns one commit repo-wide, and
console_doctor.py is not in its file list: the builder and the registry key landed in one hop and
the eagle row was never added. So the registry also claimed coverage for rows nobody runs, which
inflates the explained count in the flattering direction.

THE THREE LAWS, and each is the shape of a real defect already found:
  1. every live check is explained EXACTLY once — unexplained is the 36; twice is a contradiction
  2. no registry key names a check that does not exist — the 2 phantoms
  3. every joint id a COVERED_BY entry cites is a joint that actually RUNS — a covered claim
     pointing at an unregistered builder is coverage on paper only

⚠ THESE READ REAL OBJECTS, NEVER SOURCE TEXT. The registries and the roster are imported and
compared as data, so a rename cannot slip past a regex and a comment mentioning a check name
cannot satisfy a law. [[source-reading-guard]] [[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import console_doctor as CD          # noqa: E402
import corroborate as C              # noqa: E402


def _roster():
    return [n for n, _ in CD.CHECKS]


def _joint_ids():
    """Every joint id that a REGISTERED builder actually returns. -> set

    ⚠ Parsed from the live BUILDERS list by CALLING nothing — each builder's id is the first
    element of the tuple it returns, and calling them would run real measurements against his
    tree. The ids are literals, so ast reads them without executing a thing.
    """
    import ast
    import io
    src = io.open(os.path.join(HERE, "corroborate.py"), encoding="utf-8").read()
    registered = {getattr(b, "__name__", "") for b in C.BUILDERS}
    out = set()
    for fn in ast.walk(ast.parse(src)):
        if isinstance(fn, ast.FunctionDef) and fn.name in registered:
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Tuple) and sub.value.elts:
                    e = sub.value.elts[0]
                    if isinstance(e, ast.Constant) and isinstance(e.value, str):
                        out.add(e.value)
                        break
    return out


class EveryDoctorCheckIsExplained(unittest.TestCase):

    def test_every_check_is_explained_exactly_once(self):
        roster = set(_roster())
        cov, noj = set(C.COVERED_BY), set(C.NO_JOINT_YET)
        missing = sorted(n for n in roster if n not in cov and n not in noj)
        self.assertFalse(
            missing,
            "%d of %d doctor check(s) are in NEITHER registry, so nothing distinguishes 'a joint "
            "covers this' from 'nobody has looked': %s"
            % (len(missing), len(roster), missing[:6]))
        both = sorted(cov & noj)
        self.assertFalse(
            both,
            "%d check(s) are in BOTH registries — corroborated and declared unjointable at the "
            "same time, which is a contradiction, not an explanation: %s" % (len(both), both))

    def test_no_registry_key_names_a_check_that_does_not_exist(self):
        roster = set(_roster())
        phantom = sorted((set(C.COVERED_BY) | set(C.NO_JOINT_YET)) - roster)
        self.assertFalse(
            phantom,
            "%d registry key(s) name no live doctor check, so they explain nothing and inflate "
            "the explained count: %s. Either the row was renamed and the key must follow, or the "
            "key was born pointing at a check that was never added." % (len(phantom), phantom))

    def test_every_covered_claim_cites_a_joint_that_actually_runs(self):
        live = _joint_ids()
        self.assertTrue(
            live, "no joint ids could be parsed from the registered builders — this law would "
                  "pass vacuously, so it fails instead")
        bad = []
        for check, joints in C.COVERED_BY.items():
            for j in (joints if isinstance(joints, (list, tuple)) else [joints]):
                if j not in live:
                    bad.append((check, j))
        self.assertFalse(
            bad,
            "%d COVERED_BY claim(s) cite a joint id that no REGISTERED builder returns, so the "
            "check is covered on paper by something that never runs: %s" % (len(bad), bad[:5]))


RED_PROOF = [
    {
        "why": "an unexplained check is the exact defect this file was written for — 36 of 59 were "
               "in neither registry, and removing an entry must put one back into that state",
        "file": "corroborate.py",
        "find": "    'stray processes':",
        "replace": "    'stray processes NOT A REAL CHECK':",
        "matches": 1,
    },
    {
        "why": "a key naming no live check inflates the explained count in the flattering "
               "direction; renaming a roster entry must make its registry key a phantom",
        "file": "console_doctor.py",
        "find": '("test venue",',
        "replace": '("test venue RENAMED",',
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
