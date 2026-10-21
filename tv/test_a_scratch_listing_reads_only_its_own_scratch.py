# -*- coding: utf-8 -*-
"""REG-2362 — A LAW MAY LIST ITS OWN SCRATCH, AND ONLY ITS OWN SCRATCH.

heart2 keys a proof on the bytes its law can read. A law that lists a directory ITSELF (os.listdir / glob.glob /
os.walk in the law file) reads whatever is there at run time, so heart2 calls it UNKEYABLE and never saves one of its
proofs. MEASURED 2026-10-21: test_control listed directories at 40 sites and its 27 proofs (~4 min each) re-ran on every
push of the v3783 series; test_agent at 6. Of those 46 sites, 29 listed a temp dir the test had made a line earlier -
which no other process writes, so what the listing sees is decided by the code under test, and the key already holds
that. fixture_tmp.list_own / match_own let a law say so: they refuse ANY path that is not strictly inside the parent
contain() made for this process - the tree, his footage, the shared temp root, the parent itself, a symlink out - so
they can never hide a real read of the tree from the heart. A listing of anything else stays os.listdir in the law
file, where heart2 sees it and refuses to key it.

These cases drive the guard in a contained process and in an uncontained one, and pin the one thing the helpers are
for: heart2's own scanner counts os.listdir in a law file and does not count them. [[unknown-stays-unknown]]
RED_PROOF below.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_PARENT = _fx_tmp.contain()
import heart2  # noqa: E402


class AScratchListingReadsOnlyItsOwnScratch(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="own_")          # inside the contained parent
        self.addCleanup(shutil.rmtree, self.d, True)      # removed by its own test, not only at exit
        for n in ("f_1.jpg", "f_2.jpg", "note.txt"):
            with open(os.path.join(self.d, n), "w") as fh:
                fh.write("x")

    def test_its_own_scratch_is_listed_exactly(self):
        self.assertTrue(os.path.realpath(self.d).startswith(os.path.realpath(_PARENT) + os.sep),
                        "PREMISE: mkdtemp did not land inside the contained parent")
        self.assertEqual(sorted(_fx_tmp.list_own(self.d)), ["f_1.jpg", "f_2.jpg", "note.txt"])
        self.assertEqual(sorted(os.path.basename(p) for p in _fx_tmp.match_own(os.path.join(self.d, "f_*.jpg"))),
                         ["f_1.jpg", "f_2.jpg"])

    def test_the_tree_the_parent_the_temp_root_and_an_escape_are_refused(self):
        for path in (HERE, os.path.dirname(HERE), _PARENT, os.path.dirname(os.path.realpath(_PARENT)),
                     os.path.join(self.d, "..", ".."), "."):
            with self.subTest(path=path):
                with self.assertRaises(ValueError, msg="%s was listed as this process's own scratch" % path):
                    _fx_tmp.list_own(path)
        with self.assertRaises(ValueError, msg="a glob over the tree was answered"):
            _fx_tmp.match_own(os.path.join(HERE, "*.py"))

    def test_a_symlink_out_of_the_scratch_is_refused(self):
        link = os.path.join(self.d, "to_the_tree")
        try:
            os.symlink(HERE, link)
        except (OSError, NotImplementedError):
            self.skipTest("this PC cannot make a symlink - the escape is UNMEASURED here, not passing")
        with self.assertRaises(ValueError, msg="a symlink inside the scratch let a listing read the tree"):
            _fx_tmp.list_own(link)

    def test_a_wildcard_above_the_last_part_is_refused(self):
        with self.assertRaises(ValueError, msg="a wildcard directory could reach anything under the parent"):
            _fx_tmp.match_own(os.path.join(os.path.dirname(self.d), "*", "f_*.jpg"))

    def test_a_process_that_never_contained_lists_nothing(self):
        prog = ("import sys, tempfile; sys.path.insert(0, %r)\n"
                "import fixture_tmp as F\n"
                "d = tempfile.mkdtemp(prefix='uncontained_')\n"
                "try:\n    F.list_own(d)\n    print('LISTED')\nexcept ValueError:\n    print('REFUSED')\n"
                "finally:\n    import shutil; shutil.rmtree(d, True)\n" % HERE)
        r = subprocess.run([sys.executable, "-B", "-c", prog], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.stdout.strip(), "REFUSED", "an uncontained process listed a temp dir as its own: %s%s"
                         % (r.stdout, r.stderr[-300:]))

    def test_the_heart_counts_a_listing_and_not_these(self):
        """the point of the helpers, pinned against heart2's own scanner: os.listdir / glob.glob in a law file make it
        unkeyable; list_own / match_own do not"""
        listed = heart2._lists_a_directory(ast.parse("import os, glob\nos.listdir('.')\nglob.glob('*')\n"))
        self.assertEqual(listed, ("os.listdir", 2), "PREMISE: the scanner no longer sees a plain listing")
        mine = heart2._lists_a_directory(ast.parse(
            "import fixture_tmp as _fx_tmp\n_fx_tmp.list_own(d)\n_fx_tmp.match_own(p)\n"))
        self.assertIsNone(mine, "the scanner counts the scratch helpers as a listing, so no law that uses them can "
                                "ever be keyed: %r" % (mine,))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2362 - the containment check is gone: the helpers list the tree, his footage or a shared temp dir "
               "while the heart keys the law as if they could not",
        "file": "fixture_tmp.py",
        "find": "    if p == root or not inside:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2362 - the contained parent itself is listed: it holds every earlier case's leftovers",
        "file": "fixture_tmp.py",
        "find": "    if p == root or not inside:\n",
        "replace": "    if not inside:\n",
        "matches": 1,
    },
    {
        "why": "REG-2362 - the path is not resolved: a symlink inside the scratch reads the tree",
        "file": "fixture_tmp.py",
        "find": "    p = os.path.realpath(path)\n",
        "replace": "    p = os.path.abspath(path)\n",
        "matches": 1,
    },
    {
        "why": "REG-2362 - a process that never contained its scratch lists the shared temp root's children as its own",
        "file": "fixture_tmp.py",
        "find": "    held = _HELD.get(\"dir\")\n    if not held:\n",
        "replace": "    held = _HELD.get(\"dir\") or tempfile.gettempdir()\n    if not held:\n",
        "matches": 1,
    },
    {
        "why": "REG-2362 - a wildcard above the last part reaches every directory under the parent",
        "file": "fixture_tmp.py",
        "find": "    if any(c in d for c in \"*?[\"):\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]
