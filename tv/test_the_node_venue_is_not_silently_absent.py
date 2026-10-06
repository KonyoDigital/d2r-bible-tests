# -*- coding: utf-8 -*-
"""A VENUE THAT CANNOT RUN THE DRIVES MUST SAY SO ONCE, LOUDLY.

FOUND BY THE CODEX EYE on v3170 (cross-family review, openai/gpt-5.6-terra), and it is right:

    "the new gate can pass without executing its assertion. drive() converts missing Node (or a
     timeout) into skipTest, and unittest counts a skip as not-a-failure."

⚠ THE PATTERN IS THE HOUSE STYLE, NOT A NEW MISTAKE. `skipTest("node unavailable - a skip is NOT
a pass")` appears at 26 sites across 9 law files — the message itself already knows the hazard.
The skip is deliberate: a developer without node should still be able to run the python laws.

★ BUT 26 QUIET SKIPS IS NOT A REPORT. If node ever vanishes from a venue, every law that DRIVES
shipped JavaScript in a real engine stops asserting at once, and the suite still prints OK. That
is the exact shape of [[regression-guard]]'s green-that-lies: SAMPLE != VERDICT, SKIP != PASS.
And [[feedback-blind-fixture-green-gate]] names the HOST MACHINE as one of the usual culprits.

So instead of rewriting 26 call sites into failures, ONE law fails: the venue is asserted once,
by name, with the number of laws that would have gone silent. One loud failure that names the
cause beats twenty-six quiet skips that name nothing.

⚠ IT FAILS EVERYWHERE, NOT ONLY IN CI. A venue that cannot execute the shipped JavaScript is
worth knowing about on a laptop too — that is where a false green is most likely to be believed.
The remedy is one line and it is in the message.

REG-1900 — AND ONLY AN ABSENT NODE MAY SKIP. The quiet skips above were meant for one venue fact, and
13 harnesses (28 sites) also went quiet when the SUBJECT was gone: a renamed function, an anchor that
moved, a script that crashed or hung all came back None and the caller said "node unavailable". So a
rename of the very code a law drives read as a SKIP. MEASURED by renaming each subject in a scratch
copy of the page: 50 laws across 7 files skipped where they now fail. This file now reads every node
harness and refuses one that goes quiet on anything but FileNotFoundError from the node call.
"""
import ast
import glob
import io
import os
import re
import shutil
import subprocess
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

MARK = "node unavailable"

_NODE_CALL = re.compile(r"""\[\s*(?:["']node["']|node\b|NODE\b|_NODE\b|self\.NODE\b|c\b)""")
_SKIPPING = ("skipTest",)


def _is_none_return(n):
    return isinstance(n, ast.Return) and (n.value is None or (isinstance(n.value, ast.Constant) and n.value.value is None))


def _quiet(stmts):
    """Does this block go quiet - return None or skip - without failing?"""
    for s in stmts:
        for n in ast.walk(s):
            if _is_none_return(n):
                return True
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in _SKIPPING:
                return True
    return False


def _segmenter(src):
    """ast.get_source_segment re-splits the whole file per call - minutes on test_control. One split. -> fn(node)"""
    lines = src.split("\n")

    def seg(n):
        if n is None or getattr(n, "lineno", None) is None:
            return ""
        a, b = n.lineno - 1, n.end_lineno - 1
        if a == b:
            return lines[a][n.col_offset:n.end_col_offset]
        return "\n".join([lines[a][n.col_offset:]] + lines[a + 1:b] + [lines[b][:n.end_col_offset]])
    return seg


def violations(src, name="?"):
    """Node harnesses that turn something other than 'no node here' into a None or a skip. -> [(line, why)]"""
    out = []
    if not re.search(r"""\[\s*(?:["']node["']|node\b|NODE\b|_NODE\b|self\.NODE\b|c\b)""", src):
        return out
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [(0, "does not parse")]
    seg = _segmenter(src)
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        runs = [c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr in ("run", "check_output", "Popen") and c.args
                and _NODE_CALL.match(seg(c.args[0]) or "")]
        if not runs:
            continue
        for t in [n for n in ast.walk(fn) if isinstance(n, ast.Try)]:
            if not any(r in set(ast.walk(ast.Module(body=t.body, type_ignores=[]))) for r in runs):
                continue
            for h in t.handlers:
                caught = seg(h.type) if h.type is not None else "everything"
                if caught != "FileNotFoundError" and _quiet(h.body):
                    out.append((h.lineno, "%s: `except %s` goes quiet - only an absent node (FileNotFoundError) "
                                          "may skip; a timeout or a crash is the subject's failure" % (fn.name, caught)))
        for n in ast.walk(fn):
            if isinstance(n, ast.If) and _quiet(n.body):
                test = seg(n.test) or ""
                if "returncode" in test:
                    out.append((n.lineno, "%s: a node run that exited non-zero goes quiet (%s)" % (fn.name, test[:50])))
                elif re.search(r"<\s*0|<\s*\w+\s*$|is None|^not \w+$", test) and not re.search(r"which|NODE|node\b", test):
                    out.append((n.lineno, "%s: a missing anchor goes quiet (%s) - the subject is gone, which is "
                                          "a failure" % (fn.name, test[:50])))
    return out



def _laws_that_need_node():
    """Every law file that would go quiet without node. -> sorted [basename]"""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        try:
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
        except Exception:
            continue
        if MARK in src and os.path.basename(p) != os.path.basename(__file__):
            out.append(os.path.basename(p))
    return out


class OnlyAnAbsentNodeMaySkip(unittest.TestCase):
    """REG-1900 — a harness that goes quiet when its SUBJECT is gone reads a rename as a skip."""

    def test_no_node_harness_goes_quiet_on_anything_but_an_absent_node(self):
        bad, harnesses = [], 0
        for p in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
            if "node" not in src:
                continue
            harnesses += 1
            bad += ["%s:%d %s" % (os.path.basename(p), ln, why) for ln, why in violations(src, p)]
        self.assertGreater(harnesses, 20, "PREMISE: the node harnesses were not found - this law reads nothing")
        self.assertEqual(bad, [], "%d node harness path(s) go quiet on a missing subject, a crash or a hang - "
                                  "each reads a broken law as a SKIP:\n  %s" % (len(bad), "\n  ".join(bad[:20])))

    def test_the_detector_sees_each_quiet_shape(self):
        """The rule, driven: each shape REG-1900 removed is caught, and the one allowed skip is not."""
        anchor = ("def f():\n    i = UI.find('x')\n    if i < 0:\n        return None\n"
                  "    r = subprocess.run(['node', p])\n    return r\n")
        crash = ("def f():\n    r = subprocess.run(['node', p])\n    if r.returncode != 0:\n        return None\n"
                 "    return r\n")
        broad = ("def f(self):\n    try:\n        r = subprocess.run(['node', p], timeout=9)\n"
                 "    except (OSError, subprocess.TimeoutExpired):\n        self.skipTest('node unavailable')\n")
        fine = ("def f():\n    try:\n        r = subprocess.run(['node', p])\n    except FileNotFoundError:\n"
                "        return None\n    if r.returncode != 0:\n        raise AssertionError(r.stderr)\n    return r\n")
        for name, src in (("a missing anchor", anchor), ("a crashed run", crash), ("a broad except", broad)):
            self.assertTrue(violations(src), "%s went quiet and the detector did not see it" % name)
        self.assertEqual(violations(fine), [], "the one allowed skip - no node here - was refused")


class TheNodeVenueIsNotSilentlyAbsent(unittest.TestCase):

    def test_node_is_present_or_this_venue_cannot_prove_the_shipped_javascript(self):
        laws = _laws_that_need_node()
        self.assertTrue(laws, "nothing drives node any more - this guard is now pointless and "
                              "should be deleted rather than left as decoration")
        where = shutil.which("node")
        self.assertIsNotNone(
            where,
            "node is NOT on this venue, so %d law file(s) would skip instead of assert and the "
            "suite would still print OK: %s. Every one of them drives SHIPPED JavaScript in a "
            "real engine - without node, nothing proves the page behaves at all. "
            "Remedy: install node (CI already does, via actions/setup-node). "
            "A skip is not a pass." % (len(laws), ", ".join(laws[:6])))

    def test_the_node_on_this_venue_actually_runs(self):
        """PRESENT IS NOT WORKING. A node on PATH that cannot execute is the same false green,
        wearing a passing `which`. [[the-unjoined-end]]"""
        if shutil.which("node") is None:
            self.skipTest("no node — the law above is the one that reports that")
        try:
            r = subprocess.run(["node", "-e", "process.stdout.write('ok')"],
                               capture_output=True, text=True, timeout=30)
        except Exception as exc:
            self.fail("node is on PATH but would not run (%s)" % type(exc).__name__)
        self.assertEqual(r.returncode, 0, "node exited %s: %s" % (r.returncode, (r.stderr or "")[:200]))
        self.assertEqual((r.stdout or "").strip(), "ok",
                         "node ran but did not produce its own output — the drives would read "
                         "an empty result as a page defect")


RED_PROOF = [
    {"why": "REG-1900 - a node harness swallows every exception again, so a renamed subject reads as a SKIP",
     "file": "test_the_art_resolver_folds_the_apostrophe.py",
     "find": "    except FileNotFoundError:\n        return None          # REG-1900 - the ONE skip: there is no node on this venue\n",
     "replace": "    except Exception:\n        return None\n",
     "matches": 1},
    {"why": "REG-1900 - the detector stops seeing a broad except that goes quiet",
     "file": "test_the_node_venue_is_not_silently_absent.py",
     "find": "                if caught != \"FileNotFoundError\" and _quiet(h.body):\n",
     "replace": "                if False and caught != \"FileNotFoundError\" and _quiet(h.body):\n",
     "matches": 1},
    {"why": "REG-1900 - the detector stops seeing a missing anchor that goes quiet",
     "file": "test_the_node_venue_is_not_silently_absent.py",
     "find": "                elif re.search(r\"<\\s*0|",
     "replace": "                elif False and re.search(r\"<\\s*0|",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
