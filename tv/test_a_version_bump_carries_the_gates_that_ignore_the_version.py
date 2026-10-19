# -*- coding: utf-8 -*-
"""v3774 — A VERSION BUMP IS NOT A CHANGE TO EVERY GATE.

bump_version.py rewrites known stamp lines in bible.html, tv/control_app.py, tv/tv_diablo.py and
tv/WINDOWS_SHIP.json, and its regenerations touch BLUEPRINT.md, RESUME_HERE.md and TASKS.md the
same way. Under gate memory (v3772) those paths are inputs of most gates, so a bump-only diff reran
760 of 1003 gates. MEASURED on a real bump of the v3772 tree: 760 -> 108 reruns.

A path whose diff since the proof is ONLY stamp lines no longer invalidates a gate that does not
read the version. Any other changed line in the same file still runs the gate. A gate whose own
script or name speaks of the version still runs. An unequal swap, a failed git diff, or a line the
diff reader does not recognise all run. CI never consults the ledger.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import gate_ledger as GL  # noqa: E402

PROBES = {"python": "3.9.9", "node": "v20.0.0", "playwright": "1.40.0"}
_APP = ('import os\n'
        'def status():\n'
        '    return {\n'
        '        "ver": "v100",\n'
        '        "ok": True,\n'
        '    }\n'
        'SALT = 1\n')
_PLAIN_LAW = "import control_app\nimport sys\nprint('OK')\nsys.exit(0)\n"
_VERSION_LAW = ("import control_app\nimport sys\n"
                "assert control_app.status()['ver']  # reads VERSION\nprint('OK')\nsys.exit(0)\n")


class _Env(object):
    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *exc):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class _G(object):
    def __init__(self, name, argv, cwd):
        self.name, self.argv, self.cwd = name, argv, cwd
        self.timeout, self.needs_app, self.skip_ok = 30, False, ()


def _git(root, *args):
    p = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p


def _write(root, rel, text):
    with io.open(os.path.join(root, rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


class AVersionBumpCarries(unittest.TestCase):
    def setUp(self):
        self.held = _Env(GITHUB_ACTIONS=None, GATE_LEDGER=None,
                         TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="gbump-arm."), "a.json"))
        self.held.__enter__()
        self.addCleanup(self.held.__exit__, None, None, None)
        root = tempfile.mkdtemp(prefix="gbump.")
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "tv"))
        _write(root, ".gitignore", ".gate_ledger.json\n.gate_inputs.json\n*.tmp\n")
        _write(root, "tv/control_app.py", _APP)
        _write(root, "tv/t_plain.py", _PLAIN_LAW)
        _write(root, "tv/t_reads.py", _VERSION_LAW)
        _git(root, "init", "-q", "-b", "main")
        _git(root, "config", "user.email", "b@example.com")
        _git(root, "config", "user.name", "b")
        _git(root, "config", "commit.gpgsign", "false")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "base")
        self.root = root
        self.led = os.path.join(root, ".gate_ledger.json")
        self.plain = _G("plain-fixture", [sys.executable, os.path.join(root, "tv", "t_plain.py")], root)
        self.reads = _G("reads-fixture", [sys.executable, os.path.join(root, "tv", "t_reads.py")], root)

    def _book(self, *gates):
        book = GL.Ledger(path=self.led, probes=dict(PROBES))
        for g in gates:
            self.assertTrue(book.record(g, True), "PREMISE: no PASS stored for %s" % g.name)
        return GL.Ledger(path=self.led, probes=dict(PROBES))

    def _edit(self, old, new):
        p = os.path.join(self.root, "tv", "control_app.py")
        with io.open(p, encoding="utf-8") as fh:
            s = fh.read()
        self.assertIn(old, s)
        _write(self.root, "tv/control_app.py", s.replace(old, new, 1))

    def test_premise_the_plain_gate_depends_on_the_stamp_file(self):
        book = self._book(self.plain)
        self._edit("SALT = 1", "SALT = 2")
        entry, why = book.lookup(self.plain)
        self.assertIsNone(entry, "PREMISE: control_app.py is not an input of the fixture gate")

    def test_a_bump_only_change_carries_a_gate_that_ignores_the_version(self):
        book = self._book(self.plain)
        self._edit('"ver": "v100"', '"ver": "v101"')
        entry, why = book.lookup(self.plain)
        self.assertIsNotNone(entry, "a stamp-only edit reran a gate that never reads the version: %s" % why)

    def test_a_committed_bump_also_carries(self):
        book = self._book(self.plain)
        self._edit('"ver": "v100"', '"ver": "v101"')
        _git(self.root, "commit", "-qam", "bump")
        entry, why = book.lookup(self.plain)
        self.assertIsNotNone(entry, "a committed stamp-only bump was not carried: %s" % why)

    def test_a_real_edit_in_the_stamp_file_still_runs(self):
        book = self._book(self.plain)
        self._edit('"ok": True', '"ok": False')
        entry, why = book.lookup(self.plain)
        self.assertIsNone(entry, "a real edit beside the stamp line was carried")

    def test_a_bump_plus_a_real_edit_still_runs(self):
        book = self._book(self.plain)
        self._edit('"ver": "v100"', '"ver": "v101"')
        self._edit("SALT = 1", "SALT = 3")
        entry, why = book.lookup(self.plain)
        self.assertIsNone(entry, "a bump hid a real edit in the same file")

    def test_a_gate_that_reads_the_version_still_runs(self):
        book = self._book(self.reads)
        self._edit('"ver": "v100"', '"ver": "v101"')
        entry, why = book.lookup(self.reads)
        self.assertIsNone(entry, "a gate whose script reads the version was carried over a bump")

    def test_a_gate_named_for_the_version_still_runs(self):
        g = _G("test_build_stamp_fixture", self.plain.argv, self.root)
        book = self._book(g)
        self._edit('"ver": "v100"', '"ver": "v101"')
        entry, why = book.lookup(g)
        self.assertIsNone(entry, "a gate named for the build was carried over a bump")

    def test_an_added_stamp_line_is_not_a_swap(self):
        book = self._book(self.plain)
        self._edit('"ver": "v100",\n', '"ver": "v100",\n        "ver": "v101",\n')
        entry, why = book.lookup(self.plain)
        self.assertIsNone(entry, "a second stamp line (a real code change) was carried")

    def test_a_removed_dash_dash_line_is_not_a_header(self):
        diff = ("diff --git a/tv/tv_diablo.py b/tv/tv_diablo.py\nindex 1..2 100644\n"
                "--- a/tv/tv_diablo.py\n+++ b/tv/tv_diablo.py\n@@ -1,2 +1 @@\n"
                '-VERSION = "v1"   # a\n--- x\n+VERSION = "v2"   # b\n')
        self.assertFalse(GL.stamp_only_diff("tv/tv_diablo.py", diff),
                         "a removed '-- x' line was read as a diff header")

    def test_unknown_diff_lines_and_unknown_files_fail_closed(self):
        diff = ("diff --git a/tv/tv_diablo.py b/tv/tv_diablo.py\n--- a/tv/tv_diablo.py\n"
                "+++ b/tv/tv_diablo.py\n@@ -1 +1 @@\n"
                '-VERSION = "v1"   # a\n+VERSION = "v2"   # b\n\\ No newline at end of file\n')
        self.assertFalse(GL.stamp_only_diff("tv/tv_diablo.py", diff))
        self.assertFalse(GL.stamp_only_diff("tv/other.py", "@@ -1 +1 @@\n-a\n+b\n"))
        self.assertFalse(GL.stamp_only_diff("tv/tv_diablo.py", ""))

    def test_the_ship_table_may_grow_by_a_row(self):
        diff = ("@@ -9 +9,2 @@\n-| **v1** | `(this commit)` | v1 — a |\n"
                "+| **v2** | `(this commit)` | v2 — b |\n+| **v1** | `abc1234` | v1 — a |\n")
        self.assertTrue(GL.stamp_only_diff("TASKS.md", diff), "a bump's TASKS.md row reran the gates")
        self.assertFalse(GL.stamp_only_diff("TASKS.md", diff + "+ prose\n"))

    def test_every_bump_surface_is_declared(self):
        with io.open(os.path.join(HERE, "bump_version.py"), encoding="utf-8") as fh:
            bump = fh.read()
        for rel in ("bible.html", "tv/control_app.py", "tv/tv_diablo.py", "tv/WINDOWS_SHIP.json"):
            self.assertIn(os.path.basename(rel).split(".")[0], bump)
            self.assertIn(rel, GL.STAMP_SURFACES, "%s is stamped by the bump and not declared" % rel)

    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": "every stamp-surface path is dropped, so a real edit beside the stamp carries",
     "file": "gate_ledger.py",
     "find": "        stamped = self.stamp_only(root, sha, changed)  # LEDGER-STAMP-ONLY\n",
     "replace": "        stamped = set(p for p in changed if p in STAMP_SURFACES)  # LEDGER-STAMP-ONLY\n",
     "matches": 1},
    {"why": "stamp detection is switched off, so a bump-only change reruns the gate",
     "file": "gate_ledger.py",
     "find": "        stamped = self.stamp_only(root, sha, changed)  # LEDGER-STAMP-ONLY\n",
     "replace": "        stamped = set()  # LEDGER-STAMP-ONLY\n",
     "matches": 1},
    {"why": "a non-stamp changed line is accepted",
     "file": "gate_ledger.py",
     "find": "            if k is None:  # STAMP-OTHER-LINE\n                return False\n",
     "replace": "            if k is None:  # STAMP-OTHER-LINE\n                continue\n",
     "matches": 1},
    {"why": "an unrecognised diff line is accepted",
     "file": "gate_ledger.py",
     "find": "        return False  # STAMP-UNKNOWN-LINE",
     "replace": "        continue  # STAMP-UNKNOWN-LINE",
     "matches": 1},
    {"why": "an unequal swap of stamp lines passes",
     "file": "gate_ledger.py",
     "find": "    return bool(added) and sorted(removed) == sorted(added)  # STAMP-PAIRED\n",
     "replace": "    return bool(added)  # STAMP-PAIRED\n",
     "matches": 1},
    {"why": "the ship table may not grow, so a bump's TASKS.md row reruns gates",
     "file": "gate_ledger.py",
     "find": "        return bool(added) and len(added) >= len(removed)  # STAMP-GROWS\n",
     "replace": "        return False  # STAMP-GROWS\n",
     "matches": 1},
    {"why": "a gate whose script reads the version is carried",
     "file": "gate_ledger.py",
     "find": "                    self._verdep[rel] = bool(_VERSION_WORDS.search(fh.read()))  # STAMP-VERSION-SCRIPT\n",
     "replace": "                    self._verdep[rel] = False  # STAMP-VERSION-SCRIPT\n",
     "matches": 1},
    {"why": "a gate named for the build is carried",
     "file": "gate_ledger.py",
     "find": "        if _VERSION_NAME.search(str(name or \"\")):  # STAMP-VERSION-NAME\n",
     "replace": "        if False:  # STAMP-VERSION-NAME\n",
     "matches": 1},
    {"why": "headers are skipped inside a hunk, so a removed '-- x' line vanishes",
     "file": "gate_ledger.py",
     "find": "        if not in_hunk and line.startswith((\"index \", \"--- \", \"+++ \")):  # STAMP-HEADER\n",
     "replace": "        if line.startswith((\"index \", \"--- \", \"+++ \")):  # STAMP-HEADER\n",
     "matches": 1},
    {"why": "the stamp-only set is never removed from the change set",
     "file": "gate_ledger.py",
     "find": "            changed = changed - stamped  # STAMP-DROP\n",
     "replace": "            changed = changed  # STAMP-DROP\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
