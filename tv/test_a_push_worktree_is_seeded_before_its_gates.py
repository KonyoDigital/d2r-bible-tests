# -*- coding: utf-8 -*-
"""#143 (REG-2451) - A PUSH WORKTREE IS SEEDED WITH WHAT ITS GATES READ, BY COPY, BEFORE ITS GATES RUN.

A fresh worktree made to push from lacked the gitignored state the pre-push gates read, so pushes refused one gap at a
time (console-demos: node_modules; the render gate's heart-stored surfaces: tv/.heart2.json - unseeded, six read
'shrank'). tv/seed_worktree.py joins worktree creation to that state in one call. Driven here on a FIXTURE main checkout
and a FIXTURE worktree pointer in this law's own scratch - no git is run, and free disk comes from TV_SEED_FREE_BYTES:

  1. a fresh worktree gets REAL copies: node_modules a directory (never a link into main - a node_modules symlink once
     deleted main's real one), its files their own inodes, an edit to the copy never reaches main, a relative link
     inside node_modules/.bin kept inside the copy, tv/.heart2.json byte-equal, the staging area gone, the headroom said;
  2. tv/.second_eye.jsonl is ASKED of second_eye_ledger: one per machine (#178) -> not copied, and said; per checkout
     (an older module, or told so) -> copied;
  3. nothing present is overwritten;
  4. a seed that would leave free disk under his 8 GB ON AIR floor is refused with exit 2 and NOTHING copied - and the
     boundary is exact: leaving the floor itself is allowed;
  5. the main checkout itself is never a destination, and a path that is not a worktree root is refused.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (the docstrings carry non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import seed_worktree as SW  # noqa: E402

PLENTY = 10 ** 13


def _put(path, text):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class APushWorktreeIsSeededBeforeItsGates(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="seed-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.main = os.path.join(self.root, "main")
        common = os.path.join(self.main, ".git")
        os.makedirs(os.path.join(common, "worktrees"))
        _put(os.path.join(self.main, "node_modules", "pkg", "index.js"), "module.exports = 1;\n")
        _put(os.path.join(self.main, "node_modules", "pkg", "lib", "deep.js"), "module.exports = 2;\n")
        self.links = True
        try:
            os.makedirs(os.path.join(self.main, "node_modules", ".bin"))
            os.symlink(os.path.join("..", "pkg", "index.js"), os.path.join(self.main, "node_modules", ".bin", "tool"))
        except (OSError, NotImplementedError):
            self.links = False                    # no symlink privilege (Windows): the link case is not driven here
        _put(os.path.join(self.main, "tv", ".heart2.json"), json.dumps({"surfaces": {"vault": 41}}) + "\n")
        _put(os.path.join(self.main, "tv", ".second_eye.jsonl"), json.dumps({"version": "v0001"}) + "\n")
        self.wt = self._worktree("wt")
        self.said = []
        self._env = mock.patch.dict(os.environ, {SW.ENV_FREE: str(PLENTY)})
        self._env.start()
        self.addCleanup(self._env.stop)

    def _worktree(self, name):
        root = os.path.join(self.root, name)
        meta = os.path.join(self.main, ".git", "worktrees", name)
        os.makedirs(os.path.join(root, "tv"))
        os.makedirs(meta)
        _put(os.path.join(meta, "gitdir"), os.path.join(root, ".git") + "\n")
        _put(os.path.join(meta, "commondir"), "../..\n")
        _put(os.path.join(root, ".git"), "gitdir: %s\n" % meta)
        return root

    def _seed(self, dest, **kw):
        del self.said[:]
        return SW.seed(dest, say=self.said.append, **kw)

    def _out(self):
        return "\n".join(self.said)

    # 1 ---------------------------------------------------------------------------------------------------------------
    def test_a_fresh_worktree_gets_real_copies(self):
        rc = self._seed(self.wt)
        self.assertEqual(rc, 0, self._out())
        nm = os.path.join(self.wt, "node_modules")
        self.assertTrue(os.path.isdir(nm) and not os.path.islink(nm),
                        "node_modules was not seeded as a real directory - a link into main is how main's real "
                        "node_modules was deleted once")
        copy, orig = os.path.join(nm, "pkg", "index.js"), os.path.join(self.main, "node_modules", "pkg", "index.js")
        self.assertEqual(_read(copy), _read(orig))
        self.assertFalse(os.path.islink(copy))
        self.assertNotEqual(os.stat(copy).st_ino, os.stat(orig).st_ino, "the seeded file IS main's file")
        _put(copy, "edited in the worktree\n")
        self.assertEqual(_read(orig), "module.exports = 1;\n", "an edit in the worktree reached main's node_modules")
        self.assertEqual(_read(os.path.join(nm, "pkg", "lib", "deep.js")), "module.exports = 2;\n")
        if self.links:
            tool = os.path.join(nm, ".bin", "tool")
            self.assertTrue(os.path.islink(tool) and not os.path.isabs(os.readlink(tool)))
            self.assertTrue(os.path.realpath(tool).startswith(os.path.realpath(nm) + os.sep),
                            "a .bin link points out of the copy: %s" % os.path.realpath(tool))
        h = os.path.join(self.wt, "tv", ".heart2.json")
        self.assertEqual(_read(h), _read(os.path.join(self.main, "tv", ".heart2.json")))
        self.assertFalse(os.path.islink(h))
        self.assertFalse(os.path.lexists(os.path.join(self.wt, ".seed-tmp")), "the staging area was left behind")
        self.assertIn("headroom", self._out())
        self.assertIn("copied", self._out())

    # 2 ---------------------------------------------------------------------------------------------------------------
    def test_the_second_eye_ledger_is_asked_not_assumed(self):
        led = os.path.join(self.wt, "tv", ".second_eye.jsonl")
        self.assertEqual(self._seed(self.wt), 0, self._out())
        self.assertFalse(os.path.lexists(led), "the per-machine second-eye ledger was copied into the worktree")
        self.assertIn("one per machine", self._out())
        wt2 = self._worktree("wt2")
        self.assertEqual(self._seed(wt2, second_eye=True), 0, self._out())
        self.assertTrue(os.path.isfile(os.path.join(wt2, "tv", ".second_eye.jsonl")),
                        "a per-checkout second-eye ledger was not seeded")
        import second_eye_ledger as SEL
        wt3 = self._worktree("wt3")
        with mock.patch.object(SEL, "machine_ledger", None):     # a module from before #178
            self.assertEqual(self._seed(wt3), 0, self._out())
        self.assertTrue(os.path.isfile(os.path.join(wt3, "tv", ".second_eye.jsonl")),
                        "a module that keeps the ledger per checkout was not asked - the copy was skipped")

    # 3 ---------------------------------------------------------------------------------------------------------------
    def test_nothing_present_is_overwritten(self):
        mine = os.path.join(self.wt, "tv", ".heart2.json")
        _put(mine, "the worktree's own\n")
        self.assertEqual(self._seed(self.wt), 0, self._out())
        self.assertEqual(_read(mine), "the worktree's own\n", "seeding overwrote a file the worktree already had")
        self.assertIn("already present", self._out())

    # 4 ---------------------------------------------------------------------------------------------------------------
    def test_the_on_air_floor_refuses_and_copies_nothing(self):
        need = SW._tree_bytes(os.path.join(self.main, "node_modules"))[1] + \
            os.path.getsize(os.path.join(self.main, "tv", ".heart2.json"))
        floor = int(SW.FLOOR_GB * 1e9)
        self.assertEqual(SW.FLOOR_GB, 8.0, "his ON AIR floor is 8 GB (control_app.ON_AIR_FLOOR_GB)")
        os.environ[SW.ENV_FREE] = str(floor + need - 1)
        self.assertEqual(self._seed(self.wt), 2, "a seed leaving free disk under the floor was not refused: %s"
                         % self._out())
        for rel in ("node_modules", os.path.join("tv", ".heart2.json"), ".seed-tmp"):
            self.assertFalse(os.path.lexists(os.path.join(self.wt, rel)), "a refused seed still wrote %s" % rel)
        self.assertIn("ON AIR", self._out())
        os.environ[SW.ENV_FREE] = str(floor + need)
        self.assertEqual(self._seed(self.wt), 0, "a seed leaving exactly the floor was refused: %s" % self._out())

    # 5 ---------------------------------------------------------------------------------------------------------------
    def test_the_main_checkout_is_never_a_destination(self):
        self.assertEqual(self._seed(self.main), 2, "the main checkout was accepted as its own seed destination: %s"
                         % self._out())
        self.assertIn("main checkout itself", self._out())
        self.assertFalse(os.path.lexists(os.path.join(self.main, ".seed-tmp")))
        self.assertEqual(self._seed(os.path.join(self.wt, "tv")), 2, "a path inside a worktree was seeded: %s"
                         % self._out())


RED_PROOF = [
    {"why": "#143 - node_modules is LINKED into the worktree instead of copied: a link is a file, `git add -A` commits it, "
            "and checking that out in main replaced main's real node_modules (v3525)",
     "file": "seed_worktree.py",
     "find": "        _copy_tree(src, staged)\n",
     "replace": "        os.symlink(src, staged)\n",
     "matches": 1},
    {"why": "#143 - the on-air floor is dropped: a seed may take free disk under his 8 GB line, where ON AIR refuses",
     "file": "seed_worktree.py",
     "find": "    if free - need < floor:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "#143 - the main checkout is accepted as a seed destination (seeded from itself)",
     "file": "seed_worktree.py",
     "find": "    if os.path.realpath(main) == os.path.realpath(worktree):\n",
     "replace": "    if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
