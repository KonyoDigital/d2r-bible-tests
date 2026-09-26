# -*- coding: utf-8 -*-
"""#242 — NO LAW HANDS NODE ITS PROGRAM AS AN ARGUMENT. THE PROGRAM TRAVELS ON STDIN.

REG-1308, 2026-09-26: two mule-window laws were green on his Mac and errored on EVERY CI run, each in under 3 s,
because they ran `node -e <program>` and the program was one argument of 134 KB / 422 KB. Linux caps a single argv
string at 131,072 bytes (MAX_ARG_STRLEN); macOS does not. The mule laws were moved to stdin that day — and a sweep
the same hour counted 27 more `node -e <variable>` sites in 25 other law files, every one green today only because
its program happens to be under 128 KB. The first cut of bible.html that grows past the cap turns that law red on
CI with an OS error and no word about the law. So they all moved to `subprocess.run([node, "-"], input=program)`,
and this law keeps it that way — structurally, over every tv/test_*.py, so the 28th site cannot be written.

  · READ (ast, every tv/test_*.py): a call whose first argument is a list that starts with node (NODE, node,
    "node", _node(), shutil.which("node"), node_bin ...) and carries "-e" followed by anything but a string LITERAL
    is a violation — a literal is its own size and cannot grow; a variable is a cut of a file that can.
  · DRIVEN: the scanner is fed a small source holding each shape (the old form, the stdin form, a literal probe, a
    bash -e that is not node) and must flag exactly the old form — so a scanner that sees nothing cannot pass.
RED_PROOF below.
"""
import ast
import glob
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_NODE_NAMES = {"NODE", "node", "node_bin", "NODE_BIN"}


def _is_node(el):
    if isinstance(el, ast.Name):
        return el.id in _NODE_NAMES
    if isinstance(el, ast.Constant) and isinstance(el.value, str):
        return el.value == "node" or el.value.endswith("/node")
    if isinstance(el, ast.Call):
        f = el.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if name == "_node" and not el.args:
            return True
        if name == "which" and el.args and isinstance(el.args[0], ast.Constant) and el.args[0].value == "node":
            return True
    return False


def argv_programs(src, where="<src>"):
    """-> [(where, line)] for every node call that hands its program over as a NON-literal argument after -e."""
    bad = []

    def _elts(n):
        # the #231 eye on v3507: a TUPLE, and a list built by concatenation ([NODE] + ["-e", js]), are the same argv
        if isinstance(n, (ast.List, ast.Tuple)):
            return list(n.elts)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            a, b = _elts(n.left), _elts(n.right)
            return None if a is None or b is None else a + b
        return None
    seen = set()
    for n in ast.walk(ast.parse(src)):
        els = _elts(n)
        if not els or not _is_node(els[0]) or id(els[0]) in seen:
            continue
        seen.add(id(els[0]))
        for i, e in enumerate(els[:-1]):
            if isinstance(e, ast.Constant) and e.value in ("-e", "--eval", "-p", "--print"):
                nxt = els[i + 1]
                if not (isinstance(nxt, ast.Constant) and isinstance(nxt.value, str)):
                    bad.append((where, n.lineno))
    return bad


class NoLawHandsNodeItsProgramOnArgv(unittest.TestCase):

    def test_the_scanner_flags_the_old_form_and_only_it(self):
        src = (
            "import subprocess, shutil\n"
            "NODE = shutil.which('node')\n"
            "def a(js): return subprocess.run([NODE, '-e', js], capture_output=True, text=True)\n"         # 3 BAD
            "def b(js): return subprocess.run([NODE, '-'], input=js, capture_output=True, text=True)\n"    # stdin
            "def c(): return subprocess.run(['node', '-e', \"process.stdout.write('ok')\"])\n"             # literal
            "def d(): return subprocess.run(['bash', '-e', '-c', 'true'])\n"                               # not node
            "def e(js): return subprocess.run([shutil.which('node'), '-e', js + ';'])\n"                   # 7 BAD
            "def f(p): return subprocess.run([_node(), '--eval', p])\n"                                   # 8 BAD
            "def g(js): return subprocess.run((NODE, '-e', js))\n"                                        # 9 BAD
            "def h(js): return subprocess.run([NODE] + ['-e', js])\n"                                     # 10 BAD
        )
        self.assertEqual(sorted(set(ln for _, ln in argv_programs(src))), [3, 7, 8, 9, 10],
                         "the scanner does not see exactly the node calls that pass a program on argv")

    def test_no_law_file_passes_node_a_program_on_argv(self):
        files = sorted(glob.glob(os.path.join(HERE, "test_*.py")))
        self.assertGreater(len(files), 100, "the law files were not found - this scan would measure nothing")
        bad = []
        for f in files:
            with io.open(f, encoding="utf-8") as fh:
                src = fh.read()
            if "node" not in src:
                continue
            try:
                bad += argv_programs(src, os.path.basename(f))
            except SyntaxError:
                continue            # a file that will not parse is another law's red, not this one's
        self.assertEqual(bad, [], "these laws hand node a program as ONE argument - Linux refuses it past 131,072 "
                                  "bytes and the law goes red on CI with no word about itself; pass it on stdin: "
                                  "subprocess.run([NODE, '-'], input=js, ...): %s" % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#242 - a law hands node its program as an argument again; past 128 KB CI refuses it with an OS error",
        "file": "test_the_era_flips_at_chiliad.py",
        "find": "        r = subprocess.run([\"node\", \"-\"], input=js, capture_output=True, text=True, timeout=60)\n",
        "replace": "        r = subprocess.run([\"node\", \"-e\", js], capture_output=True, text=True, timeout=60)\n",
        "matches": 1,
    },
    {
        "why": "#242 - the scanner stops recognising shutil.which('node') as node, so half the law files go unread",
        "file": "test_no_law_hands_node_its_program_on_argv.py",
        "find": "        if name == \"which\" and el.args and isinstance(el.args[0], ast.Constant) and el.args[0].value == \"node\":\n            return True\n",
        "replace": "",
        "matches": 1,
    },
]
