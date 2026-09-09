"""♥ A VERSION THE LEDGER HAS NEVER HEARD OF IS THE ONE MOST LIKELY TO BLOCK THE NEXT PUSH.

v2854. `--backlog` built its answer from `SEL.audit(None)`, and audit()'s own docstring states its
scope out loud: "Every version mentioned in the ledger". A version that shipped and was never looked
at produces NO row at all, so it could not appear in the one command whose entire job is "show me
what is stacking up".

MEASURED 2026-09-09, both directions of the contradiction:
    --backlog            "3 version(s) owe a look: v2772, v2774, v2776"   (v2852 absent)
    --check v2852 --gate "v2852 OWES A LOOK — nothing was ever recorded for it"
I trusted the quiet one, pushed v2853, and the pre-push gate refused it. After the fix, over 249
shipped versions in 400 commits: 111 had never been looked at, against the 3 it used to report.

⚠ THESE LAWS PARSE. A grep would pass on the prose above, which describes the defect in full.
[[source-reading-guard]] [[silence-is-not-evidence]] [[zero-needs-a-denominator]]
"""
import ast
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: E402  — this file prints ★ ⚠ ♥; on a non-UTF-8
console_safe.enable()  # console it would crash while REPORTING and a clean tree would
                       # exit non-zero. [[unknown-stays-unknown]]

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)


def _fn(name):
    for n in ast.walk(TREE):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError("second_eye_run.py has no %s() — the law cannot read its subject" % name)


RED_PROOF = [
    {
        "why": "un-asking owes_a_look leaves the backlog reading only rows that already exist, "
               "which is the blindness itself",
        "file": "second_eye_run.py",
        "find": "            if _v not in _known and SEL.owes_a_look(_v):",
        "replace": "            if _v not in _known and False:",
        "matches": 1,
    },
    {
        "why": "un-anchoring the subject pattern re-admits versions a commit merely MENTIONS, "
               "which counted v1554 as a ship",
        "file": "second_eye_run.py",
        "find": '_VER_LEADING_RUN = re.compile(r"^(v\\d{4}(?:\\s*[+,&]\\s*v\\d{4})*)\\b")',
        "replace": '_VER_LEADING_RUN = re.compile(r"(v\\d{4}(?:\\s*[+,&]\\s*v\\d{4})*)\\b")',
        "matches": 1,
    },
]


class TheBacklogSeesAVersionWithNoRow(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_backlog_asks_the_SAME_predicate_the_gate_asks(self):
        """★★ For a version with no ledger row, the backlog must ask owes_a_look — not infer."""
        calls = [n for n in ast.walk(_fn("main"))
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "owes_a_look"]
        self.assertTrue(
            calls,
            "main() never calls owes_a_look. The backlog then reports only versions the ledger "
            "already knows about, and a version with NO row — the strongest case of owing a look — "
            "stays invisible. That is how v2853 was pushed into a refusal.")

    def test_the_shipped_list_comes_from_history_not_from_the_ledger(self):
        """★★ The candidate set must be what SHIPPED, or the ledger defines its own completeness."""
        called = {n.func.id for n in ast.walk(_fn("main"))
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn(
            "versions_in_history", called,
            "main() does not enumerate shipped versions, so the backlog's denominator is the "
            "ledger's own contents — a set that cannot contain what was never recorded.")

    def test_the_subject_pattern_is_ANCHORED(self):
        """★★ 'v2853 — ...' stamps a ship; 'fix: the v2804 row ...' merely mentions one."""
        # ⚠⚠ v2865 — THIS COUNTED EVERY PATTERN CONTAINING d{4} AND DEMANDED EXACTLY ONE, so
        # v2862's second pattern (_VER_TOKEN, which splits a leading RUN like "v2859+v2860") turned
        # this law red on CI — a law broken by a change it was not about. Name the SUBJECT pattern
        # by its variable instead of counting look-alikes. [[label-outlived-referent]]
        pats = [ast.unparse(n.value.args[0])
                for n in ast.walk(TREE)
                if isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == "_VER_LEADING_RUN" for t in n.targets)
                and isinstance(n.value, ast.Call) and n.value.args]
        self.assertEqual(1, len(pats),
                         "expected exactly one _VER_LEADING_RUN assignment; found %d — UNKNOWN, "
                         "not a pass" % len(pats))
        self.assertTrue(
            "^" in pats[0][:6],
            "the version pattern %r is not anchored, so any commit that MENTIONS a version counts "
            "it as shipped. Measured over 400 subjects: 252 stamp a ship, 19 only refer back, and "
            "the loose form reported v1554 as a shipped version owing a look." % pats[0])

    def test_a_clean_backlog_prints_its_denominator(self):
        """★★ 'nothing owes a look' over an empty candidate set is UNKNOWN, not clean."""
        msgs = [a.value for n in ast.walk(_fn("main"))
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"
                for a in ast.walk(n)
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
                and "nothing owes a look" in a.value]
        self.assertTrue(msgs, "the clean-backlog message is gone; this law cannot read its subject")
        self.assertIn(
            "examined", msgs[0],
            "the clean verdict %r names no denominator. A zero from a candidate set nobody sized "
            "cannot be told from a zero because the enumeration returned nothing." % msgs[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
