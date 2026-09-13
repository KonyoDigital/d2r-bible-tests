# -*- coding: utf-8 -*-
"""A SEAM THAT LETS TESTS ASSUME SUPERVISION MUST NEVER LET THE LOCK'S OWN LAW ASSUME IT.

`self_arming._heart_says_watched()` reads TV_HEART_CENSUS so that tests about SWEEP LOGIC stop
depending on whether his heart census happens to be fresh. That is worth having — measured
2026-09-13, editing 16 gate files staled the census, closed `vault.sweep_start` and failed 20
tests that were not about supervision at all — but it is a seam into a SAFETY path, and a seam
into a safety path is exactly the thing that quietly stops guarding.

Two ways it could rot, and this file refuses both:

  1. THE LOCK'S OWN LAWS START USING IT. `test_a_STALE_census_closes_the_lock` exists to prove
     that a stale census closes the lock. If that file ever points TV_HEART_CENSUS at a census
     saying "all proven", it proves nothing and everything downstream still reads green.
  2. THE SEAM STOPS FAILING CLOSED. An unreadable or absent census is UNKNOWN, and UNKNOWN has
     never armed anything here. A seam that returns True on a missing file would hand every
     destructive lock an easy yes.

[[feedback-fixtures-never-touch-live-data]] [[unknown-stays-unknown]] [[regression-guard]]
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _names_in(path, funcname=None):
    """Every Name/Str the file (or one function in it) mentions, by PARSING. -> set

    ⚠ parsed, never grepped: "TV_HEART_CENSUS" appears in this file's own prose and in
    self_arming's comments, and a substring search would read those as usage.
    [[source-reading-guard]]
    """
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    node = tree
    if funcname:
        got = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == funcname]
        if not got:
            return None
        node = got[0]
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
        elif isinstance(n, ast.Name):
            out.add(n.id)
    return out


class TestTheSeamNeverSoftensTheLock(unittest.TestCase):

    def test_the_locks_own_law_reads_the_REAL_census(self):
        p = os.path.join(HERE, "test_the_lock_derives_from_the_heart.py")
        self.assertTrue(os.path.exists(p), "the lock's own law file is gone or renamed")
        names = _names_in(p)
        hits = sum(1 for s in names if "TV_HEART_CENSUS" in str(s))
        print("   TV_HEART_CENSUS mentions in the lock's own law file: %d" % hits)
        self.assertEqual(
            0, hits,
            "test_the_lock_derives_from_the_heart.py mentions TV_HEART_CENSUS. That file exists to "
            "prove a STALE census closes the lock; if it can point the census at a fixture saying "
            "'all proven', the proof is worthless and every surface downstream reads green on it.")

    def test_the_seam_is_resolved_at_CALL_time(self):
        names = _names_in(os.path.join(HERE, "self_arming.py"), "_heart_says_watched")
        self.assertIsNotNone(names, "_heart_says_watched is gone or renamed")
        self.assertIn("TV_HEART_CENSUS", names,
                      "the seam is not read inside _heart_says_watched. An env honoured only at "
                      "import is a redirect that silently does not take — the shape this repo "
                      "already learned for TV_SELF_ARMING_LEDGER.")

    def test_an_absent_census_still_fails_CLOSED(self):
        import self_arming as sa
        old = os.environ.get("TV_HEART_CENSUS")
        os.environ["TV_HEART_CENSUS"] = os.path.join(HERE, "__no_such_census__.json")
        try:
            ok, why = sa.may("vault.sweep_start")
            print("   absent census -> may=%r" % ok)
            self.assertFalse(ok, "an ABSENT census armed a destructive lock: %s" % str(why)[:120])
        finally:
            if old is None:
                os.environ.pop("TV_HEART_CENSUS", None)
            else:
                os.environ["TV_HEART_CENSUS"] = old


RED_PROOF = [
    {
        "why": "removes the call-time env read, so the seam is dead and every test that assumes "
               "supervision silently goes back to depending on his live census",
        "file": "self_arming.py",
        "find": '_p = os.environ.get("TV_HEART_CENSUS") or os.path.join(_h2.HERE, ".heart2.json")',
        "replace": '_p = os.path.join(_h2.HERE, ".heart2.json")',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
