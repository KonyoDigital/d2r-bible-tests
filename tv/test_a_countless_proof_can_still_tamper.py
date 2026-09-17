# -*- coding: utf-8 -*-
"""A PROOF THAT DECLARES NO MATCH COUNT MUST STILL BE ABLE TO TAMPER.

`RED_PROOF` is declared in two shapes. 374 gates use dicts carrying a numeric `matches`; **12 use
4-tuples that carry no count at all** (REG-1045). v3241 taught the comparison to treat an absent
count as UNKNOWN — check `got >= 1` always, compare exactly only when somebody declared a number —
which is right, and which the well-formedness law already did.

**And `_prove_one` passes that same value straight to `str.replace` as its count:**

```python
_tampered = original.replace(find, repl, want)     # want is None
"aa".replace("a", "b", None)
TypeError: 'NoneType' object cannot be interpreted as an integer
```

So all 32 count-less proofs would have raised **at the tampering step** — the fix for "the prover
could not READ them" would have become "the prover crashes while TAMPERING them", one line later.
Found by a cross-family review of v3241, the version that introduced the None.

⚠ ONE FIELD, THREE READERS, and each needed telling separately: `_normalise_proofs` (absent is
legal), the comparison (absent means do not compare), and `str.replace` (absent is not an integer).
Every time this repo has been bitten it was a second reader of a field somebody had just changed
the meaning of. [[unknown-stays-unknown]] [[copy-drift]] [[the-unjoined-end]]

The rule is the same everywhere: nobody declared a number, so tamper EVERY occurrence — which is
precisely what `got` counted and what the `got >= 1` check accepted a moment earlier.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import heart2 as H


class TestACountlessProofCanStillTamper(unittest.TestCase):

    def _tamper_expr(self):
        """The real assignment from _prove_one, parsed — not a retyped copy. [[copy-drift]]"""
        with io.open(os.path.join(HERE, "heart2.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_prove_one"), None)
        self.assertIsNotNone(fn, "_prove_one moved — re-anchor this gate")
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and any(
                    getattr(t, "id", "") == "_tampered" for t in node.targets):
                return node
        return None

    # ── THE LAW ──────────────────────────────────────────────────────────────────────────────
    def test_the_tamper_never_passes_an_absent_count_to_replace(self):
        """★ str.replace's third argument must be an int or absent — never None."""
        node = self._tamper_expr()
        self.assertIsNotNone(node, "the tamper assignment is gone — re-anchor this gate")
        src = ast.dump(node)
        self.assertIn("IfExp", src,
                      "`_tampered` is a single unconditional call, so whatever `want` holds is "
                      "handed to str.replace as its count. With a count-less proof that is None, "
                      "and None is a TypeError — every 4-tuple proof would raise at the moment it "
                      "tampers. Assignment:\n%s" % ast.dump(node))

    def test_replace_with_no_count_changes_every_occurrence(self):
        """The rule, stated as behaviour: no declaration means tamper them all."""
        original = "x1 x1 x1"
        self.assertEqual(original.replace("x1", "Y"), "Y Y Y")
        self.assertEqual(original.replace("x1", "Y", 1), "Y x1 x1",
                         "a declared count must still limit the tamper")

    def test_a_None_count_really_does_raise(self):
        """⚠ THE PREMISE, MEASURED. If this ever stops raising the law above is theatre."""
        with self.assertRaises(TypeError):
            "aa".replace("a", "b", None)

    # ── AND THE SHAPE THAT MADE IT POSSIBLE ─────────────────────────────────────────────────
    def test_countless_proofs_exist_in_the_tree(self):
        """If none existed the guard would be untested prose, so this measures the population."""
        countless = sum(1 for _n, f in H.gate_files()
                        for pr in (H.red_proofs_in(f) or [])
                        if isinstance(pr, dict) and pr.get("matches") is None)
        self.assertGreater(
            countless, 0,
            "no proof in the tree declares an absent match count, so nothing exercises the "
            "count-less path — the guard is unmeasured, not safe [[unknown-stays-unknown]]")
        print("   %d count-less proof(s) rely on this path" % countless)

    def test_every_proof_is_a_dict_by_the_time_it_leaves_the_reader(self):
        """The reader normalises both shapes, so no consumer needs to know there were two."""
        bad = [(n, type(pr).__name__) for n, f in H.gate_files()
               for pr in (H.red_proofs_in(f) or []) if not isinstance(pr, dict)]
        self.assertEqual(bad, [], "these left the reader un-normalised: %r" % bad[:4])


if __name__ == "__main__":
    unittest.main(verbosity=2)
