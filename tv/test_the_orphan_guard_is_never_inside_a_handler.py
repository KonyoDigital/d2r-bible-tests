# -*- coding: utf-8 -*-
"""THE THREAD THAT CAN END THE CONSOLE MUST NOT HAVE ITS TRIGGER INSIDE AN EXCEPTION HANDLER.

`board_window._orphan_watch` polls the control server and calls `os._exit(0)` once it has been
unreachable for ~100s. That is the guard that stops a board window outliving the console that
spawned it — the orphaned-process case that made his Mac hot (three full consoles, PPID 1, load
average 5.42 -> 3.08 the moment they were killed).

⚠⚠ MEASURED 2026-09-13, AND IT SHIPPED. v3076 inserted a `try`/`except` around a `lane_trace.note`
call immediately above the guard, and the old `if misses >= 5: … os._exit(0)` kept its indentation
— becoming the SECOND STATEMENT OF THAT `except`, after `pass`. Found by the cross-family second
eye reading the PUSHED diff, and reproduced here by AST:

    os._exit  ancestry:  FunctionDef > While > Try > ExceptHandler > If

`lane_trace.note` catches every exception and returns False, so it never raises. The self-close
could therefore effectively NEVER run: the window would poll for ever with `misses` climbing past
5 and stay up. The inversion is the worst part — a WORKING corroborator is what disabled the
killer, so the healthier the machine, the more certainly the guard was dead.

⚠ AND THE EXISTING COVERAGE GATE STAYED GREEN. `test_the_nested_KILLER_thread_is_covered` asserts
`_lane_tick` appears in the function's AST dump; `os._exit` was still in the tree, so nothing
failed. A guard that only asks "is the name present" cannot see the name move into a branch that
never runs. [[source-reading-guard]]
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _ancestry(fn):
    """Every os._exit call in `fn`, with the node types enclosing it. -> [(lineno, [types])]"""
    out = []

    def walk(node, path):
        for ch in ast.iter_child_nodes(node):
            if (isinstance(ch, ast.Call)
                    and getattr(ch.func, "attr", None) == "_exit"):
                out.append((ch.lineno, list(path)))
            walk(ch, path + [type(ch).__name__])

    walk(fn, [])
    return out


class TestTheOrphanGuardIsNeverInsideAHandler(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            self.tree = ast.parse(fh.read())
        self.fn = None
        for n in ast.walk(self.tree):
            if isinstance(n, ast.FunctionDef) and n.name == "_orphan_watch":
                self.fn = n
        self.assertIsNotNone(self.fn, "_orphan_watch is gone — re-point this guard")

    def test_the_guard_still_exists_at_all(self):
        calls = _ancestry(self.fn)
        print("os._exit call(s) in _orphan_watch: %d" % len(calls))
        self.assertEqual(len(calls), 1,
                         "expected exactly one self-close; found %d. A guard that was deleted and "
                         "a guard that was moved are both failures here" % len(calls))

    def test_the_self_close_is_not_buried_in_an_except_branch(self):
        for lineno, path in _ancestry(self.fn):
            print("  os._exit line %d ancestry: %s" % (lineno, " > ".join(path)))
            self.assertNotIn(
                "ExceptHandler", path,
                "os._exit sits inside an exception handler at line %d. It then runs ONLY when that "
                "handler's try raises — and lane_trace.note swallows everything and returns False, "
                "so the console's orphan guard would never fire and board windows would outlive "
                "their console for ever" % lineno)

    def test_it_is_reached_on_an_ordinary_iteration(self):
        """Not merely outside a handler — actually on the loop's own path."""
        for lineno, path in _ancestry(self.fn):
            self.assertIn("While", path,
                          "the self-close at line %d is not inside the poll loop at all" % lineno)
            # ⚠ NAME WHAT IS FORBIDDEN, NOT WHAT IS ALLOWED. The first cut demanded the list
            # between the loop and the call be EMPTY and failed on `Expr` — the statement wrapper
            # around the call itself, which is not a branch at all. A guard that fails on the
            # correct shape teaches people to loosen it. [[sabotage-is-usually-the-wrong-one]]
            FORBIDDEN = ("ExceptHandler", "Try", "With", "AsyncWith", "For", "AsyncFor",
                         "While", "FunctionDef", "Lambda")
            inner = path[path.index("While") + 1:]
            bad = [t for t in inner if t in FORBIDDEN]
            self.assertEqual(bad, [],
                             "the self-close is nested under %s between the poll loop and its "
                             "own test; each of those is a path that can silently stop it "
                             "running" % bad)
        print("self-close sits directly under the poll loop, behind its own `if` only")


RED_PROOF = [
    {
        "why": "the orphan guard goes back inside the lane_trace handler, where it runs only if a "
               "function that swallows every exception somehow raises — so a board window whose "
               "console has died stays up for ever, which is the orphaned-process case that made "
               "his Mac hot",
        "file": "control_app.py",
        # ⚠ ANCHOR ON ASCII. The first cut wrote \\U0001f4fa where control_app.py carries the
        # literal emoji, so the tamper matched 0 times and heart2 called it INVALID — the sabotage
        # was wrong, not the law. [[sabotage-is-usually-the-wrong-one]]
        # ⚠⚠ THE SABOTAGE MUST MOVE IT, NOT DISABLE IT. Two earlier cuts were wrong and heart2
        # said so both times: one wrote a \\U escape where control_app.py carries a literal emoji
        # (0 matches, INVALID), and one replaced the test with `if False:` — which leaves os._exit
        # exactly where it is, so a POSITION law correctly stayed green (BLIND). This re-creates
        # the real v3076 defect: the guard migrates INTO an exception handler.
        "find": "            if misses >= 5:\n                print(f\"📺 board window: control server unreachable for ~{misses * 20}s — \"\n                      f\"self-closing (orphan guard).\", flush=True)\n                os._exit(0)\n",
        "replace": "            try:\n                pass\n            except Exception:\n                if misses >= 5:\n                    print(f\"📺 board window: control server unreachable for ~{misses * 20}s — \"\n                          f\"self-closing (orphan guard).\", flush=True)\n                    os._exit(0)\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
