# -*- coding: utf-8 -*-
"""REG-1725 — A LIVENESS PROBE NEVER SENDS A CTRL-C ON WINDOWS.

`os.kill(pid, 0)` is the Unix way to ask "is this pid alive?". On Windows signal 0 IS CTRL_C_EVENT: Python hands it to
GenerateConsoleCtrlEvent, and a Ctrl-C cannot be limited to one process group - every process on the caller's console
receives it. REG-1447 (#50) learned that for heart2 and pinned ONE function. REG-1720 then shipped a new probe in
suite_verdict with the same idiom, and its law runs inside the ALT's prover: MEASURED 2026-10-02, after the ALT pulled
it at 15:36, three slices died of KeyboardInterrupt in heart2's own subprocess wait, each was booked "ended without a
census", and the river backed off 3 h. A sweep by syntax tree then found SEVEN more probes with no Windows branch
(control_app x3, fixture_tmp, render_check, second_eye_run) - one of them in the fixture helper every law uses.

So the law is the CLASS, not a function: every `os.kill(<pid>, 0)` in tv/ must sit where Windows cannot reach it -

  * in the NOT-Windows branch of a test on os.name / sys.platform / IS_WIN, or
  * after a Windows branch in the same block that ALWAYS leaves (return / raise on every path).

A mere mention of IS_WIN earlier in the function is NOT a guard - `if IS_WIN: x = 1` followed by the probe still sends
the Ctrl-C, and the scanner's own planted cases prove it refuses that shape. The only sites allowed without a branch
are named below, each with the reason Windows never reaches it.

  · SCANNED: every tv/*.py by syntax tree (a text grep missed `os.kill(int(pid), 0)` - nested parens).
  · DRIVEN: suite_verdict and fixture_tmp, with os.name set to "nt", ask self_prove's safe door and send nothing.
  · INSTRUMENT: planted bare / else-guarded / early-exit / decoy sources classify correctly before any verdict.
RED_PROOF below. [[unknown-stays-unknown]] [[sweep-dont-ask]]
"""
import ast
import glob
import io
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import self_prove as SP  # noqa: E402  (imported here, under the real os.name, before any test bends it)

#: probes Windows never reaches, each with WHY - a new entry needs the same: a reason, not a wish
POSIX_ONLY = {
    ("conftest.py", "no_orphaned_children"):
        "returns before any signal when there is no ps process table, and Windows has none",
    ("test_child_guard_one_tree_per_role.py", "_pid_alive_real"):
        "called only from TheDoorLeavesOneTreePerRole, which is skipUnless(IS_POSIX)",
}


def _is_win_ref(n):
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
        return (n.value.id, n.attr) in (("os", "name"), ("sys", "platform"))
    return isinstance(n, ast.Name) and n.id in ("IS_WIN", "_IS_WIN")


def _win_polarity(test):
    """-> True when the test is TRUE on Windows, False when it is true OFF Windows, None when it does not ask."""
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        p = _win_polarity(test.operand)
        return None if p is None else (not p)
    if _is_win_ref(test) and isinstance(test, ast.Name):
        return True                                            # if IS_WIN:
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and _is_win_ref(test.left) \
            and isinstance(test.comparators[0], ast.Constant) and isinstance(test.comparators[0].value, str):
        win = _names_windows(test.comparators[0].value)
        if isinstance(test.ops[0], ast.Eq):
            return win                                         # == "nt" is Windows; == "darwin" is not
        if isinstance(test.ops[0], ast.NotEq) and win:
            return False                                       # != "nt" is everywhere else
        return None                                            # != "darwin" still lets Windows in
    if isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute) and test.func.attr == "startswith" \
            and _is_win_ref(test.func.value) and test.args and isinstance(test.args[0], ast.Constant) \
            and isinstance(test.args[0].value, str):
        return _names_windows(test.args[0].value)              # startswith("win") / startswith("darwin")
    return None


def _names_windows(v):
    return v == "nt" or v.lower().startswith("win")


def _always_leaves(stmts):
    if not stmts:
        return False
    last = stmts[-1]
    if isinstance(last, (ast.Return, ast.Raise)):
        return True
    if isinstance(last, ast.If):
        return _always_leaves(last.body) and _always_leaves(last.orelse)
    if isinstance(last, ast.Try):
        return _always_leaves(last.body) and all(_always_leaves(h.body) for h in last.handlers)
    return False


def _is_kill_zero(c):
    return (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "kill"
            and isinstance(c.func.value, ast.Name) and c.func.value.id == "os" and len(c.args) == 2
            and isinstance(c.args[1], ast.Constant) and c.args[1].value == 0)


def _guarded(path):
    """path: the ancestor chain from the function down to the call. -> True when Windows cannot reach the call."""
    for i in range(len(path) - 1):
        node, child = path[i], path[i + 1]
        if isinstance(node, ast.If):
            p = _win_polarity(node.test)
            if p is True and child in node.orelse:
                return True
            if p is False and child in node.body:
                return True
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list) or child not in block:
                continue
            for prior in block[:block.index(child)]:
                if isinstance(prior, ast.If) and _win_polarity(prior.test) is True and _always_leaves(prior.body):
                    return True
    return False


def sites_in_source(src, fname="<src>"):
    """-> [(fname, function, line, guarded)] for every os.kill(<x>, 0) inside a function."""
    out = []
    tree = ast.parse(src)

    def walk(node, path):
        path = path + [node]
        if _is_kill_zero(node):
            fn = next((p for p in reversed(path) if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
            if fn is not None:
                sub = path[path.index(fn):]
                out.append((fname, fn.name, node.lineno, _guarded(sub)))
            else:
                out.append((fname, "<module>", node.lineno, False))
        for ch in ast.iter_child_nodes(node):
            walk(ch, path)
    walk(tree, [])
    return out


def kill_zero_sites(root=HERE):
    out = []
    for f in sorted(glob.glob(os.path.join(root, "*.py"))):
        with io.open(f, encoding="utf-8") as fh:
            out.extend(sites_in_source(fh.read(), os.path.basename(f)))
    return out


class TheScannerCanTellTheShapesApart(unittest.TestCase):
    """the instrument first: a scanner that cannot see a planted bare probe proves nothing about the tree"""

    def _one(self, src):
        s = sites_in_source(src)
        self.assertEqual(len(s), 1, "PREMISE: the planted probe was not found: %r" % (s,))
        return s[0][3]

    def test_a_bare_probe_with_nested_parens_is_found_and_refused(self):
        self.assertFalse(self._one("import os\ndef f(pid):\n    os.kill(int(pid), 0)\n"))

    def test_the_off_windows_branch_is_guarded(self):
        self.assertTrue(self._one("import os\ndef f(pid):\n    if os.name == 'nt':\n        return 1\n"
                                  "    else:\n        os.kill(pid, 0)\n"))
        self.assertTrue(self._one("IS_WIN=0\ndef f(pid):\n    try:\n        if IS_WIN:\n            pass\n"
                                  "        else:\n            os.kill(pid, 0)\n    except OSError:\n        pass\n"))

    def test_an_early_exit_on_windows_is_guarded(self):
        self.assertTrue(self._one("import os\ndef f(pid):\n    if os.name == 'nt':\n        try:\n"
                                  "            return g(pid)\n        except Exception:\n            return True\n"
                                  "    try:\n        os.kill(pid, 0)\n    except OSError:\n        return False\n"))

    def test_a_test_true_only_off_windows_guards_its_body(self):
        self.assertTrue(self._one("import sys\ndef f(pid):\n    if sys.platform == 'darwin':\n        os.kill(pid, 0)\n"))
        self.assertFalse(self._one("import sys\ndef f(pid):\n    if sys.platform != 'darwin':\n        os.kill(pid, 0)\n"))

    def test_a_windows_mention_that_does_not_leave_is_refused(self):
        self.assertFalse(self._one("IS_WIN=0\ndef f(pid):\n    if IS_WIN:\n        x = 1\n    os.kill(pid, 0)\n"))
        self.assertFalse(self._one("IS_WIN=0\ndef f(pid):\n    if IS_WIN:\n        os.kill(pid, 0)\n"))


class EveryProbeInTheTreeAsksWindowsFirst(unittest.TestCase):

    def test_no_probe_reaches_windows(self):
        sites = kill_zero_sites()
        self.assertGreaterEqual(len(sites), 10, "PREMISE: the scan found only %d probe(s) - it is not reading the "
                                                "tree it judges" % len(sites))
        bare = ["%s:%d %s" % (f, ln, fn) for f, fn, ln, ok in sites if not ok and (f, fn) not in POSIX_ONLY]
        self.assertEqual(bare, [], "os.kill(pid, 0) is a Ctrl-C on Windows (CTRL_C_EVENT), not a probe - ask "
                                   "self_prove.pid_alive there, or name the site in POSIX_ONLY with its reason")

    def test_every_named_exception_still_names_a_probe(self):
        seen = {(f, fn) for f, fn, _ln, _ok in kill_zero_sites()}
        for k, why in POSIX_ONLY.items():
            self.assertTrue(why.strip(), "%s has no reason" % (k,))
            self.assertIn(k, seen, "POSIX_ONLY names %s:%s, which holds no probe any more - a stale exception "
                                   "would excuse the next one" % k)


class TheProbesAskTheSafeDoorOnWindows(unittest.TestCase):
    """driven: with os.name bent to "nt", the two probes a law can reach inside a prover send nothing"""

    def _drive(self, fn):
        kills, asked = [], []
        with mock.patch.object(os, "kill", lambda pid, sig: kills.append((pid, sig))), \
                mock.patch.object(SP, "pid_alive", lambda pid: asked.append(pid) or True), \
                mock.patch.object(os, "name", "nt"):
            got = fn(4242)
        self.assertEqual(kills, [], "a probe sent os.kill on Windows, where signal 0 is a Ctrl-C")
        self.assertEqual(asked, [4242], "PREMISE: the probe did not ask the safe door")
        self.assertIs(got, True)

    def test_the_suite_verdict_probe(self):
        import suite_verdict as SV
        self._drive(SV._pid_alive)

    def test_the_fixture_probe(self):
        import fixture_tmp as FT
        self._drive(FT._alive)


RED_PROOF = [
    {"why": "REG-1725 - suite_verdict probes with os.kill(pid, 0) on Windows again: its own law Ctrl-Cs the prover",
     "file": "suite_verdict.py",
     "find": "    if os.name == \"nt\":\n        try:\n            import self_prove as _sp\n            return _sp.pid_alive(pid)\n"
             "        except Exception:\n            return True                     # unknown: the wait is bounded, and a run is never started beside it\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1725 - the fixture sweep probes with os.kill(pid, 0) on Windows again: every law can Ctrl-C its prover",
     "file": "fixture_tmp.py",
     "find": "    if os.name == \"nt\":                  # REG-1725 - os.kill(pid, 0) is a Ctrl-C there; ask the safe door\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1725 - the window check probes with os.kill(pid, 0) on Windows again, on every launch",
     "file": "control_app.py",
     "find": "        if IS_WIN:\n            return _pid_alive(pid)   # REG-1725 - os.kill(pid, 0) is a Ctrl-C there, not a probe\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1725 - the orphan watch probes its parent with os.kill(ppid, 0) on Windows again",
     "file": "control_app.py",
     "find": "            if IS_WIN:              # REG-1725 - there signal 0 IS a delivery (CTRL_C_EVENT); ask the safe door\n"
             "                if not _pid_alive(ppid):\n                    raise ProcessLookupError(ppid)\n            else:\n"
             "                os.kill(ppid, 0)    # signal 0 = existence check only, delivers nothing\n",
     "replace": "            os.kill(ppid, 0)\n",
     "matches": 1},
    {"why": "REG-1725 - the second-eye snapshot sweep probes with os.kill(pid, 0) on Windows again",
     "file": "second_eye_run.py",
     "find": "    if os.name == \"nt\":                 # REG-1725 - os.kill(pid, 0) is a Ctrl-C there (CTRL_C_EVENT), not a probe\n",
     "replace": "    if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
