# -*- coding: utf-8 -*-
"""#104 — A GATE'S WHY SAYS WHAT IT GUARDS, NEVER HOW MANY CASES OR RED-PROOFS IT HAS.

MEASURED 2026-09-30: 284 of the 738 gate why-texts in run_gates.py typed a count ("11 cases, 9 red-proofs"), and of the
230 whose law file could be counted by its own AST, 72 were already WRONG - a law grows a case, its why keeps the old
number, and the second eye reads the stale number as a claim about the gate (it named one on v3528). His ruling: compute
them, don't type them. A count is a property of the law FILE and is read from it where it is shown (heart2 counts the
red-proofs it runs; the AST counts the cases); a sentence cannot keep up with a file, so it no longer tries.

The law: no Gate(...) why in run_gates.py states a number of cases or red-proofs. Parsed, never grepped - a grep over
this file would match this very rule's text in its own why. [[source-reading-guard]] [[label-outlived-referent]]
The #231 eye on v3531 (88ece312): an unreadable why was the STRING "<unreadable why>" - searched, found clean, and
counted toward the 500 whys the census requires. A why this law cannot read is one it cannot judge, so it is UNKNOWN,
named, and fails; a count typed through a format string is exactly the why it would have waved through.
RED_PROOF below.
"""
import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

GATES = os.path.join(HERE, "run_gates.py")
TYPED = re.compile(r"\b\d+\s+(?:cases?|red-?proofs?)\b", re.I)

RED_PROOF = [
    {
        "why": "#104 - a gate's why types its counts again: the number goes stale the day its law grows a case",
        "file": "run_gates.py",
        "find": "             \"layer merely switched off), the click box says both lamps in words.\"),\n",
        "replace": "             \"layer merely switched off), the click box says both lamps in words. 12 cases, 10 red-proofs\"),\n",
        "matches": 1,
    },
    {
        "why": "#231 on v3531 - a count typed through a format string: the law cannot read the why and scores it clean",
        "file": "run_gates.py",
        "find": "             \"layer merely switched off), the click box says both lamps in words.\"),\n",
        "replace": "             \"layer merely switched off), the click box says both lamps in words. %d cases\" % 12),\n",
        "matches": 1,
    },
]

#: a why this law could not read - UNKNOWN, never a string that can be searched and found clean
_UNREADABLE = object()


def _whys():
    """(gate name, why text) for every Gate(...) in run_gates.py, parsed. -> list"""
    with io.open(GATES, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "Gate" and n.args:
            name = getattr(n.args[0], "value", None)
            why = None
            for kw in n.keywords:
                if kw.arg == "why":
                    try:
                        why = ast.literal_eval(kw.value)
                    except Exception:
                        why = _UNREADABLE
            out.append((name, why))
    return out


class AGateSaysWhatItGuardsNotHowMany(unittest.TestCase):

    def test_the_registry_was_read(self):
        rows = _whys()
        self.assertGreater(len(rows), 500, "only %d gates parsed out of run_gates.py - the census below would be "
                                           "judging a fragment" % len(rows))
        self.assertGreater(sum(1 for _n, w in rows if isinstance(w, str) and w.strip()), 500,
                           "almost no gate carries a why - this law would pass having read nothing")

    def test_every_why_can_be_read(self):
        """A why that is not plain text (a format string, a join, a name) cannot be searched for a typed count - the
        #231 eye found such a why was scored clean. UNKNOWN is said by name and fails; it is never a pass."""
        rows = _whys()
        unread = [name for name, why in rows if why is _UNREADABLE]
        self.assertEqual(unread, [], "%d gate why(s) are not plain text, so whether they type a count is UNKNOWN - "
                                     "write them as sentences: %s" % (len(unread), unread[:12]))

    def test_no_why_types_a_count(self):
        typed = []
        for name, why in _whys():
            if not isinstance(why, str):
                continue
            m = TYPED.search(why)
            if m:
                typed.append("%s: ...%s..." % (name, why[max(0, m.start() - 40):m.end() + 20]))
        self.assertEqual(typed, [], "a gate's why types a count that will go stale the day its law grows - say what "
                                    "it guards, and let the law file be counted:\n  " + "\n  ".join(typed[:12]))

    def test_the_pattern_sees_every_shape_it_must(self):
        """The census is only as good as its pattern: the shapes that were in the file must read as typed counts, and
        ordinary numbers must not."""
        for s in ("11 cases, 9 red-proofs", "3 red-proofs.", "1 case", "41 red-proofs, each", "2 redproofs"):
            self.assertTrue(TYPED.search(s), "the pattern misses %r" % s)
        for s in ("his 31 reels", "v3528", "7 of the tabs", "red-proofs delete one condition", "12 are needed"):
            self.assertFalse(TYPED.search(s), "the pattern flags an ordinary number: %r" % s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
