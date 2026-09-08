#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2795 — A FIXED-SIZE SOURCE WINDOW MEASURES MY GUESS, NOT THE FILE.

⚠⚠ WHAT IT COST, 2026-09-08. `test_the_river_has_a_mouth._river_payload()` cut
`SRC[i:i + 9000]` from `if path == "/api/river"` and looked for the success payload inside it. Its
own docstring said *"anchored at BOTH ends"*; only one end was real. The route grew, and MEASURED
that day `self._json(200, {` sat at **+9145** — 145 characters past the window. `find` returned -1,
the helper returned None, and two real laws ERRORED on it while a third reported "the /api/river
success payload is gone or renamed" about a route that was perfectly fine.

Nothing about the river had broken. The guard's REACH had, and it shrank a little more every time
somebody documented that handler.

=== ⚠⚠ THE DIRECTION THAT DOES NOT ANNOUNCE ITSELF ===
The river case failed LOUDLY, which is the lucky half. A window that runs short under a NEGATIVE
assertion is silent:

    blk = src[i:i + 3000]
    self.assertNotIn("the forbidden thing", blk)     # <- passes if blk stopped early

That reads as "the forbidden thing is absent" when the truth is "I did not look that far". It is
[[unknown-stays-unknown]] in source-reading clothes: a zero with no denominator, and no author.

MEASURED across tv/*.py:
    68 fixed-size windows, 23 files, 0 files unparseable
    25 of them sit in a function that ALSO makes a negative assertion   <- the silent set
    43 have only positive assertions                                    <- these fail loudly

⚠ AND THE FIRST COUNT OF THIS WAS ITSELF A GREP, WHICH SAID 80. It matched the pattern inside
COMMENTS and STRING LITERALS — including the comments explaining this very defect. Over-counted by
12. A law about reading source wrongly, measured by reading source wrongly.
[[source-reading-guard]] [[feedback-suspect-the-instrument]]

=== ⛔ WHY THIS IS A RATCHET AND NOT A BAN ===
Sixty-eight sites cannot be rewritten safely in one pass, and a law that fails on all of them is a
law nobody can ship. A ratchet is honest about the debt: the number may FALL, it may not RISE, and
the silent subset is tracked separately because it is the one that matters. Where a subject has a
real boundary — the next `if path ==`, the next `def`, a closing brace — anchor BOTH ends instead,
as `_river_payload` now does.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

#: MEASURED 2026-09-08. These are debt ceilings, not targets — lower them when sites are fixed.
TOTAL_CEILING = 68
#: The windows a short read would carry SILENTLY past a negative assertion.
SILENT_CEILING = 25

#: assertions that PASS when the window came up short
_NEGATIVE = ("assertNotIn", "assertFalse", "assertIsNone", "assertNotRegex", "assertNotEqual")


def _is_fixed_window(node):
    """`x[i : i + N]` where both ends name the SAME variable and N is a literal int.

    ⚠ PARSED, NEVER GREPPED — the whole point. A regex over this repo's test files matches the
    pattern inside the very comments that explain why it is wrong.
    ⚠ `x[i : j + N]` is NOT this defect: the end is anchored to something else and moves with it.
    Only a window measured from its own start is a guess about length.
    """
    if not isinstance(node, ast.Subscript):
        return False
    sl = node.slice
    if not isinstance(sl, ast.Slice) or sl.lower is None or sl.upper is None:
        return False
    up = sl.upper
    return (isinstance(up, ast.BinOp) and isinstance(up.op, ast.Add)
            and isinstance(up.right, ast.Constant) and isinstance(up.right.value, int)
            and isinstance(sl.lower, ast.Name) and isinstance(up.left, ast.Name)
            and sl.lower.id == up.left.id)


def scan():
    """-> (total, silent, rows, unparsed). Rows are (file, function, line, N, negatives)."""
    total = silent = unparsed = 0
    rows = []
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py"):
            continue
        try:
            tree = ast.parse(io.open(os.path.join(HERE, name), encoding="utf-8",
                                     errors="replace").read())
        except SyntaxError:
            unparsed += 1
            continue
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            wins = [n.lineno for n in ast.walk(fn) if _is_fixed_window(n)]
            if not wins:
                continue
            negs = sum(1 for n in ast.walk(fn)
                       if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in _NEGATIVE)
            total += len(wins)
            if negs:
                silent += len(wins)
            for ln in wins:
                rows.append((name, fn.name, ln, negs))
        # module-level windows count too — a helper outside a class is where _river_payload lived
        top = [n for n in ast.walk(tree) if _is_fixed_window(n)]
        infn = {n.lineno for fn in [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]
                for n in ast.walk(fn) if _is_fixed_window(n)}
        loose = [n.lineno for n in top if n.lineno not in infn]
        total += len(loose)
        for ln in loose:
            rows.append((name, "<module>", ln, 0))
    return total, silent, rows, unparsed


class ASourceWindowMustReachItsSubject(unittest.TestCase):

    # ── the instrument first ─────────────────────────────────────────────────────────────────
    def test_the_scanner_is_not_blind(self):
        """★ THE COUNT IS THE TELL. A scanner that finds nothing passes everything, and this whole
        law would then be furniture."""
        total, silent, rows, unparsed = scan()
        self.assertEqual(unparsed, 0,
                         "%d file(s) would not parse, so their windows are UNMEASURED — this law "
                         "cannot report a total it did not read" % unparsed)
        self.assertGreaterEqual(total, 40,
                                "the scanner found only %d fixed-size windows; it was finding 68 "
                                "on 2026-09-08. Suspect the instrument before the tree." % total)
        self.assertTrue(rows, "no rows returned beside a non-zero total — the scanner disagrees "
                              "with itself")

    # ── ⚠⚠ THE RATCHETS ──────────────────────────────────────────────────────────────────────
    def test_the_total_never_GROWS(self):
        total, _s, rows, _u = scan()
        worst = {}
        for f, _fn, _ln, _n in rows:
            worst[f] = worst.get(f, 0) + 1
        top = sorted(worst.items(), key=lambda kv: -kv[1])[:5]
        self.assertLessEqual(
            total, TOTAL_CEILING,
            "fixed-size source windows rose to %d (ceiling %d). Each one measures a GUESS about "
            "how far the subject reaches, and the subject grows every time somebody documents it "
            "— that is how the /api/river guard came to examine nothing. Anchor both ends against "
            "a real boundary instead. Worst files: %s" % (total, TOTAL_CEILING, top))

    def test_the_SILENT_subset_never_GROWS(self):
        """★★ THE ONE THAT MATTERS. Under a negative assertion a short window does not fail — it
        reports absence it never looked for."""
        _t, silent, rows, _u = scan()
        named = sorted({(f, fn) for f, fn, _ln, negs in rows if negs})
        self.assertLessEqual(
            silent, SILENT_CEILING,
            "windows sitting under a NEGATIVE assertion rose to %d (ceiling %d). A window that "
            "runs short there PASSES having examined nothing, and nothing reports it — the same "
            "shape as a 0 with no denominator, with no author. Either anchor both ends, or assert "
            "the slice did not end exactly at its cap before trusting the verdict. Sites: %s"
            % (silent, SILENT_CEILING, named[:12]))

    # ── ⛔ AND THE ONE THAT WAS FIXED STAYS FIXED ─────────────────────────────────────────────
    def test_the_river_mouth_guard_is_anchored_at_both_ends(self):
        """The site that cost the round. If it regresses to a byte count the rest of this law is
        philosophy."""
        p = os.path.join(HERE, "test_the_river_has_a_mouth.py")
        if not os.path.isfile(p):
            self.skipTest("test_the_river_has_a_mouth.py is gone — a skip is NOT a pass")
        src = io.open(p, encoding="utf-8").read()
        tree = ast.parse(src)
        fn = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_river_payload"]
        self.assertTrue(fn, "_river_payload is gone or renamed — re-point this law")
        bad = [n.lineno for n in ast.walk(fn[0]) if _is_fixed_window(n)]
        self.assertEqual(bad, [],
                         "_river_payload went back to a fixed-size window at line(s) %s. It "
                         "already failed once this way: the payload sat at +9145 and the window "
                         "was 9000." % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
