"""♥ THE RATCHET MUST NOT ERASE WHAT THE HEART HAS BANKED.

v2853. `--ratchet` wrote `{"unproven": N, "proved": M}` straight over `.heart2.json`, the file that
carries every proof name the heart has ever verified. MEASURED in a sandbox, with a prior baseline
loose enough for the ratchet to pass:

    keys 10 -> 2 · provedGates 97 -> 0 · verdictAt 45 -> 0 · blind, declared, partial, total gone
    proved 97 -> 98 — the VERIFIED count replaced by the DECLARATION count

One `--ratchet` erased 97 proofs. The scar was already written in this same file — "`--ratchet`
wrote a two-key dict that dropped `blind` entirely, flipping a DARK heart back to WATCHED" — and it
had been fixed in the prove path only, leaving the ratchet path untouched. [[the-unjoined-end]]

⚠ THESE LAWS PARSE. A grep for `dict(prev)` would pass on a comment describing the rule, and this
repo has paid for prose-reading nine times this session alone. [[source-reading-guard]]
"""
import ast
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)


def _fn(name):
    for n in ast.walk(TREE):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError("heart2.py has no %s() — the law cannot read its subject" % name)


RED_PROOF = [
    {
        "why": "un-merging the ratchet write returns it to the two-key clobber that erased 97 proofs",
        "file": "heart2.py",
        "find": "        _out = dict(prev)",
        "replace": "        _out = {}",
        "matches": 1,
    },
    {
        "why": "returning the declaration count under the key `proved` is the mislabel itself",
        "file": "heart2.py",
        "find": '    return {"total": total, "declared": len(have), "unproven": len(missing),',
        "replace": '    return {"total": total, "proved": len(have), "unproven": len(missing),',
        "matches": 1,
    },
]


class TheRatchetCannotEraseTheCensus(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_ratchet_write_MERGES_the_prior_census(self):
        """★★ The object written to STATE must be built FROM the prior state, never fresh."""
        dumps = [n for n in ast.walk(_fn("main"))
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "dump"]
        self.assertEqual(1, len(dumps),
                         "expected exactly one json.dump in main(); found %d — UNKNOWN, not a pass"
                         % len(dumps))
        arg = dumps[0].args[0]
        self.assertIsInstance(
            arg, ast.Name,
            "the ratchet dumps a %s literal straight over the census. That is the two-key clobber "
            "that erased 97 proof names, verbatim." % type(arg).__name__)
        # ...and that name must carry the PRIOR state, not an empty dict wearing the same name.
        srcs = [ast.unparse(a.value) for a in ast.walk(_fn("main"))
                if isinstance(a, ast.Assign)
                and any(getattr(t, "id", "") == arg.id for t in a.targets)]
        self.assertTrue(srcs, "%s is dumped but never assigned in main()" % arg.id)
        self.assertTrue(
            any("prev" in s for s in srcs),
            "%s is assigned from %r — none of which reads the prior census, so the write still "
            "replaces it. MERGE, NEVER CLOBBER." % (arg.id, srcs))

    def test_report_does_NOT_call_a_declaration_a_proof(self):
        """★★ report() counts gates that DECLARE a proof. It must not name that `proved`."""
        rets = [n for n in ast.walk(_fn("report"))
                if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)]
        self.assertEqual(1, len(rets), "expected one dict return from report(); found %d" % len(rets))
        keys = [k.value for k in rets[0].value.keys if isinstance(k, ast.Constant)]
        self.assertIn("declared", keys,
                      "report() no longer returns `declared` — its callers cannot tell declarations "
                      "from verified proofs: %r" % keys)
        self.assertNotIn(
            "proved", keys,
            "report() returns a key called `proved` while counting DECLARATIONS. A gate can declare "
            "a proof that never ran, or one that came back BLIND; calling those proven is the exact "
            "gap #52 exists to close. Measured: report said 98, verified was 97.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
