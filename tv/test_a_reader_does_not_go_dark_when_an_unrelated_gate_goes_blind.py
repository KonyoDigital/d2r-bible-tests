# -*- coding: utf-8 -*-
"""NINE BLIND GATES TOOK THE RIVER OFF HIS SCREEN, AND NONE OF THEM WATCHED THE RIVER.

v3049 wired a `may()` seat into `printer.stream()` — the one chokepoint every river caller goes
through. Its own comment said it "refuses on MERIT only, so a census gone stale from a gate edit
cannot stop him reading the river". It did not do that, and the gap is one word: v3042's softening
clause covers STALE, while v3050 wrote — correctly, and this gate does not touch that rule — that
BLIND never softens and fails closed for everything.

So when routine U re-proved the census at 00:48 and recorded NINE BLIND instruments, the seat
refused. MEASURED END TO END at 01:55, against his live console on :17772, not a fixture:

    /api/river          -> ok:true, lanes.ok:FALSE, rows 0
    lanes.why           -> "the router did not answer (UNKNOWN, not an empty shelf —
                            printer.stream() could not answer"
    the strip rendered  -> "the river could not be drawn"

The render gate could not see it either, because its `activate` kicks `_shLanesLoad()` itself every
0.4s — so the harness was re-asking a question the console had already answered "no" to, and the
two river targets failed as "the panel could not be ACTIVATED", which reads as a layout or a load
problem. Three hours went into the harness before anything asked the SERVER what it was returning.

THE RULE THIS PINS. A surface that ACTS keeps the full guarantee — blind still fails closed for
every destructive lock, and `may_on_merit` refuses those outright so it can never become a soft
door. A surface that merely SHOWS HIM WHAT IS THERE must not go blank because an unrelated gate
lost its red-proof. The honest failure for a display is to show the data and say what is
unverified; showing nothing is the one thing it must not do.

[[unknown-stays-unknown]] [[the-unjoined-end]] [[stale-reading]] [[zero-needs-a-denominator]]
"""
import ast
import io
import os
import unittest

# ⚠ this file PRINTS non-ASCII (· and ⚠) in its own measurements, and his Windows console is
# cp1255 — printing one of those there raises while REPORTING, so a clean tree would look like a
# crash. The suite has a law for exactly this and it caught me on the first push.
from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _calls_in(path, funcname):
    """Every attribute-call spelled inside `funcname`, by PARSING. -> set of names

    ⚠ Parsed, never grepped: the words `may(` and `may_on_merit(` both appear in this file's own
    prose and in printer.py's comments, and a substring search reads those as call sites.
    [[source-reading-guard]]
    """
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == funcname:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                    out.add(sub.func.attr)
    return out


class TestAReaderDoesNotGoDark(unittest.TestCase):

    def test_the_river_chokepoint_asks_merit_not_the_heart(self):
        calls = _calls_in(os.path.join(HERE, "printer.py"), "stream")
        self.assertIn("may_on_merit", calls,
                      "printer.stream() must ask may_on_merit. It is a READ that feeds the river "
                      "strip; asking may() puts his display behind the health of every instrument "
                      "in the tree, and nine blind ones blanked it on 2026-09-13.")
        self.assertNotIn("may", calls,
                         "printer.stream() still calls may() — that is the exact seat that took "
                         "the river off his screen.")

    def test_merit_can_never_arm_a_destructive_lock(self):
        import self_arming as sa
        destructive = [k for k, v in sa.LOCKS.items() if isinstance(v, dict) and v.get("destructive")]
        self.assertTrue(destructive, "no lock is marked destructive — the registry is not loaded, "
                                     "so this law would pass by measuring nothing")
        print("   destructive locks checked: %d -> %s" % (len(destructive), ", ".join(sorted(destructive))))
        for lk in destructive:
            ok, why = sa.may_on_merit(lk)
            self.assertFalse(ok, "may_on_merit permitted %s, which is destructive" % lk)
            self.assertIn("DESTRUCTIVE", str(why),
                          "may_on_merit refused %s but not for being destructive: %s" % (lk, why))

    def test_merit_does_not_consult_the_heart(self):
        """The whole point: merit must not read the census at all."""
        calls = _calls_in(os.path.join(HERE, "self_arming.py"), "may_on_merit")
        self.assertNotIn("_heart_says_watched", calls)
        src = io.open(os.path.join(HERE, "self_arming.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "may_on_merit"]
        self.assertEqual(len(fn), 1, "expected exactly one may_on_merit definition")
        names = {n.id for n in ast.walk(fn[0]) if isinstance(n, ast.Name)}
        self.assertNotIn("_heart_says_watched", names,
                         "may_on_merit reads the heart — then it is just may() and a reader can "
                         "still go dark when an unrelated gate goes blind.")
        print("   may_on_merit names the heart 0 time(s) — measured by parse, not by grep")


RED_PROOF = [
    {
        "why": "puts the river chokepoint back on may(), which is the seat that returned "
               "lanes.ok:false and rendered 'the river could not be drawn' on his live console",
        "file": "printer.py",
        "find": '_ok, _lw = _sa.may_on_merit("printer.stream")',
        "replace": '_ok, _lw = _sa.may("printer.stream")',
        "matches": 1,
    },
    {
        "why": "deletes the destructive refusal, so merit alone could arm deleting footage, "
               "dropping the ledger or spending money on a sweep",
        "file": "self_arming.py",
        "find": '    if spec.get("destructive"):\n        return False, ("%s is DESTRUCTIVE',
        "replace": '    if False:\n        return False, ("%s is DESTRUCTIVE',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
