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

# ⚠ HIS WINDOWS CONSOLE IS cp1255: a bare print of ⚠ or an em dash crashes the script
# WHILE REPORTING, so a clean tree exits non-zero for a reason unrelated to the check.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
SRC_PATH = os.path.join(HERE, "control_app.py")

# ⚠⚠ v3409 — THE GATE READ ONE FILE AND THE FAULT LIVED IN TWO. The cross-family review of v3404
# named a site v3407 could not reach: console_doctor.py spawns git as well (`git show
# --name-only`, and `git rev-list --count HEAD..origin/main` on the eagle tick). This guard only
# ever opened control_app.py, so it was green while two more console-popping spawns survived in a
# file it never looked at. A guard's REACH is part of its verdict.
SRC_PATHS = (SRC_PATH, os.path.join(HERE, "console_doctor.py"))
DOOR_PATH = os.path.join(HERE, "git_quiet.py")


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


# Aliases the one door is imported under. `git_quiet.run` and `_gq.run` are the door;
# `subprocess.run` is the thing the door exists to replace.
DOOR_MODULES = ("git_quiet", "_git_quiet", "_gq", "GQ")


def _callee_name(node):
    """A DOTTED name, because the last segment alone cannot tell the door from the hole.

    ⚠⚠ v3409 — THIS EXACT BLINDNESS WAS CAUGHT BY heart2, ONE HOUR AFTER I INTRODUCED IT.
    Widening the gate to accept the door's new home, `_gq.run(...)`, I accepted the bare callee
    name "run" — and `subprocess.run(...)` is ALSO an Attribute whose attr is "run". So the guard
    admitted precisely the call it exists to ban, and its own red-proof stayed GREEN through its
    own defeat: `BLIND ← stayed GREEN through its own defeat (1 match(es))`. The match count was
    1, so the sabotage was sound and the LAW was weak. [[sabotage-is-usually-the-wrong-one]]
    (the mirror case) [[source-reading-guard]]
    """
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = func.value
        if isinstance(base, ast.Name):
            return "%s.%s" % (base.id, func.attr)
        return "?.%s" % func.attr
    return None


def _is_the_one_door(name):
    if name == "_git_run":
        return True
    if not name or "." not in name:
        return False
    mod, _, attr = name.rpartition(".")
    return attr == "run" and mod in DOOR_MODULES


class TestWindowsGitSpawnsHideTheConsole(unittest.TestCase):
    def test_every_git_argv_goes_through_the_ONE_door(self):
        offenders, total = [], 0
        for p in SRC_PATHS:
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
            for node in ast.walk(ast.parse(src)):
                if not isinstance(node, ast.Call):
                    continue
                if not _is_git_argv(node):
                    continue
                total += 1
                name = _callee_name(node)
                if not _is_the_one_door(name):
                    offenders.append("%s L%s %s(... ['git', ...])"
                                     % (os.path.basename(p), node.lineno, name or "?"))
        self.assertEqual(
            offenders,
            [],
            "git is spawned outside the one door, so Windows will pop a console and steal "
            "focus:\n  " + "\n  ".join(offenders),
        )
        self.assertGreaterEqual(total, 14,
                                "only %d git argv site(s) were found across %d file(s) — the walk "
                                "has stopped reaching them, which is a green that means nothing"
                                % (total, len(SRC_PATHS)))
        print("git argv sites across %d file(s): %d, all through the one door"
              % (len(SRC_PATHS), total))

    def test_there_is_exactly_ONE_door_body(self):
        """⚠ [[copy-drift]] — two bodies means one of them eventually stops matching."""
        bodies = []
        for name in sorted(os.listdir(HERE)):
            if not name.endswith(".py") or name.startswith("test_"):
                continue
            with io.open(os.path.join(HERE, name), encoding="utf-8") as fh:
                code = "\n".join(l.split("#", 1)[0] for l in fh.read().split("\n"))
            if "mingw64" in code and "STARTF_USESHOWWINDOW" in code:
                bodies.append(name)
        self.assertEqual(bodies, ["git_quiet.py"],
                         "the mingw redirect exists in more than one place, so a fix to one leaves "
                         "the other popping windows: %s" % bodies)

    def test_the_one_door_hides_the_window_on_windows(self):
        with io.open(DOOR_PATH, encoding="utf-8") as fh:
            src = fh.read()
        i = src.find("def run(")
        self.assertGreater(i, -1, "git_quiet.run is gone, so nothing hides git consoles")
        blk = src[i:src.find("\ndef ", i + 1)]
        self.assertIn("WIN_CREATE", blk, "the one door dropped CREATE_NO_WINDOW")
        self.assertIn("GIT_MINGW", blk, "the one door no longer calls mingw64 git directly")
        self.assertNotIn("headless-git", blk,
                         "headless-git.exe still spawns a CUI git.exe child that WT focuses")
        self.assertIn("STARTF_USESHOWWINDOW", blk, "the one door dropped SW_HIDE")
        self.assertIn("GIT_TERMINAL_PROMPT", blk, "the one door can still prompt and steal focus")


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
        "file": "git_quiet.py",
        "find": '        if argv and argv[0] == "git" and os.path.isfile(GIT_MINGW):\n            argv[0] = GIT_MINGW\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3407 — SW_HIDE IS THE SECOND HALF. CREATE_NO_WINDOW governs whether a console is "
               "allocated; STARTF_USESHOWWINDOW + wShowWindow 0 governs whether any window the "
               "child does create is shown. Dropping it leaves the case that Windows Terminal "
               "takes the focus anyway.",
        "file": "git_quiet.py",
        "find": "        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW\n        si.wShowWindow = 0\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
