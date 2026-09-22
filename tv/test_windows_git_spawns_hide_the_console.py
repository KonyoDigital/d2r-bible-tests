# -*- coding: utf-8 -*-
"""Windows git children of TV DIABLO must not allocate a console.

Konyo, 2026-09-21: git.exe windows steal focus every couple of minutes, 2-3 in a
row, while the console is sitting idle. PATH git (`Git\\cmd\\git.exe`) is a CUI
wrapper; a spawn without CREATE_NO_WINDOW (and without preferring mingw64 git)
pops a real terminal and alt-tabs him off the game.

This guard reads control_app.py as a tree, not as a character window, and fails
when a git argv is handed to subprocess.run / Popen / check_output instead of
_git_run.
"""
import ast
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(HERE, "control_app.py")


def _is_git_argv(node):
    """True when the call's first positional arg is an argv whose first element is 'git'.

    ⚠⚠ v3407 — AND AN ARGV CAN BE *BUILT*, NOT ONLY WRITTEN. The first cut matched only a
    literal List/Tuple, so `["git", "-C", root, ...] + list(paths)` — a BinOp — was invisible to
    it. MEASURED the hour this shipped: the AST walk reported 13 sites clean while a far cruder
    regex in the heart row found a 14th, in `_tree_is_mid_edit`. Two checks disagreeing IS the
    finding; the stricter-looking instrument was the blind one. [[feedback-contradiction-is-the-finding]]
    """
    if not node.args:
        return False
    a0 = node.args[0]
    while isinstance(a0, ast.BinOp) and isinstance(a0.op, ast.Add):
        a0 = a0.left                      # ["git", ...] + list(paths) -> the literal on the left
    if isinstance(a0, (ast.List, ast.Tuple)) and a0.elts:
        e0 = a0.elts[0]
        return isinstance(e0, ast.Constant) and e0.value == "git"
    return False


def _callee_name(node):
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


class TestWindowsGitSpawnsHideTheConsole(unittest.TestCase):
    def test_every_git_argv_goes_through__git_run(self):
        with io.open(SRC_PATH, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)
        offenders = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_git_argv(node):
                continue
            name = _callee_name(node)
            if name != "_git_run":
                offenders.append("L%s %s(... ['git', ...])" % (node.lineno, name or "?"))
        self.assertEqual(
            offenders,
            [],
            "git is spawned without _git_run, so Windows will pop a console and steal focus:\n  "
            + "\n  ".join(offenders),
        )

    def test__git_run_hides_the_window_on_windows(self):
        with io.open(SRC_PATH, encoding="utf-8") as fh:
            src = fh.read()
        i = src.find("def _git_run(")
        self.assertGreater(i, -1, "_git_run is gone, so nothing hides git consoles")
        blk = src[i:src.find("\ndef ", i + 1)]
        self.assertIn("_WIN_CREATE", blk, "_git_run dropped CREATE_NO_WINDOW")
        self.assertIn("_GIT_MINGW", blk, "_git_run no longer calls mingw64 git directly")
        self.assertNotIn("headless-git", blk,
                         "headless-git.exe still spawns a CUI git.exe child that WT focuses")
        self.assertIn("STARTF_USESHOWWINDOW", blk, "_git_run dropped SW_HIDE")
        self.assertIn("GIT_TERMINAL_PROMPT", blk, "_git_run can still prompt and steal focus")


RED_PROOF = [
    {
        "why": "v3407 — ONE SITE IS ENOUGH TO POP A WINDOW. Sending a single git argv back to "
               "subprocess.run restores a CUI child on Windows: `pythonw` owns no console, so the "
               "child ALLOCATES one, and that is a real terminal on top of D2R. Measured live "
               "2026-09-21 — 2-3 windows in a row, every couple of minutes, while the console sat "
               "idle. The AST walk must name the offender by line rather than pass because most "
               "sites are correct.",
        "file": "control_app.py",
        "find": '        r = _git_run(\n            ["git", "rev-list", "HEAD..origin/main", "--count"],',
        "replace": '        r = subprocess.run(\n            ["git", "rev-list", "HEAD..origin/main", "--count"],',
        "matches": 1,
    },
    {
        "why": "v3407 — WITHOUT THE MINGW REDIRECT THE FLAG PROTECTS THE WRONG BINARY. Git for "
               "Windows' PATH git is a 46 KB CUI WRAPPER that spawns the real git WITHOUT "
               "inheriting CREATE_NO_WINDOW, so hiding the wrapper hides nothing. Dropping "
               "_GIT_MINGW leaves a helper that looks careful and still alt-tabs him off the game.",
        "file": "control_app.py",
        "find": '        if argv and argv[0] == "git" and os.path.isfile(_GIT_MINGW):\n            argv[0] = _GIT_MINGW\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3407 — SW_HIDE IS THE SECOND HALF. CREATE_NO_WINDOW governs whether a console is "
               "allocated; STARTF_USESHOWWINDOW + wShowWindow 0 governs whether any window the "
               "child does create is shown. Dropping it leaves the case that Windows Terminal "
               "takes the focus anyway.",
        "file": "control_app.py",
        "find": "        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW\n        si.wShowWindow = 0\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
