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

REG-2366 — THE LINK THAT SHOWS THE PATH IS RESOLVED MUST BE ONE THIS PC CAN MAKE. Red-proof [2] (realpath -> abspath)
has one catcher: a directory link inside the scratch that points at the tree. Windows refuses os.symlink without a
privilege his ALT and Dean's PC do not hold, so that case skipped in both runs there, the tampered run read green, and
the heart filed [2] BLIND - one BLIND shuts every lock on a PC (REG-1677). Now the link is fixture_tmp.link_dir: a
symlink, else a Windows directory junction (no privilege; realpath resolves it - REG-1668's way). And [2] declares
`"needs": "dir-link"`, whose probe (fixture_tmp.can_link_a_directory) makes a link the same way: a PC that can make
neither files [2] ELSEWHERE, never BLIND, and a PC whose probe says yes may not skip the case - it fails instead.
RED_PROOF below.
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

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

    def test_a_link_out_of_the_scratch_is_refused(self):
        """★ the ONE catcher of red-proof [2] (the path not resolved): a directory link inside the scratch pointing at
        the tree. REG-2366 - a symlink where this PC allows one, else a Windows junction (no privilege needed, REG-1668):
        his ALT and Dean's PC refuse the symlink, and this case skipping in both runs read BLIND there."""
        link = os.path.join(self.d, "to_the_tree")
        how = _fx_tmp.link_dir(HERE, link)
        if how:
            self.addCleanup(_fx_tmp.unlink_dir_link, link)    # runs BEFORE setUp's rmtree: the link, never the tree
        if not how or os.path.realpath(link) != os.path.realpath(HERE):
            why = ("made a %s that realpath does not resolve to the tree" % how) if how else \
                  "could make neither a symlink nor a junction"
            # proof [2] declares "dir-link": where heart2's probe (the same link_dir, the same realpath) also says no,
            # the heart files [2] ELSEWHERE and never asks this case - a skip here is honest. Where the probe says YES,
            # the heart judges [2] on this PC and a skip would read BLIND and shut every lock: that is a red instead.
            if _fx_tmp.can_link_a_directory():
                self.fail("this PC %s inside the scratch, yet heart2's dir-link probe says it can make one - the heart "
                          "judges red-proof [2] here, and a skip would file it BLIND" % why)
            self.skipTest("this PC %s - the escape is UNMEASURED here, not passing (heart2 files proof [2] "
                          "ELSEWHERE on such a PC)" % why)
        with self.assertRaises(ValueError, msg="a %s inside the scratch let a listing read the tree" % how):
            _fx_tmp.list_own(link)

    def test_a_parent_swapped_for_a_link_lists_nothing(self):
        """★ REG-2455 (A2's Grok low 2) - _own() re-resolved the contained parent on EVERY call, so renaming the parent
        and putting a link to another tree in its place made that tree "the scratch" - and list_own listed it. contain()
        now resolves the parent ONCE. Driven in a child process (its own parent, swapped for real): the listing under
        the swapped parent raises, and the other tree is never listed."""
        fake = tempfile.mkdtemp(prefix="fake_tree_")       # outside the CHILD's parent: this process's own scratch
        prog = (
            "import os, sys, tempfile, time\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import fixture_tmp as F\n"
            "def mv(a, b):  # Windows may refuse a rename for a moment while a scanner holds a handle\n"
            "    for i in range(25):\n"
            "        try:\n"
            "            return os.rename(a, b)\n"
            "        except PermissionError:\n"
            "            if os.name != 'nt' or i == 24:\n"
            "                raise\n"
            "            time.sleep(0.2)\n"
            "parent = F.contain()\n"
            "sub = tempfile.mkdtemp(prefix='own_')\n"
            "open(os.path.join(sub, 'real.txt'), 'w').close()\n"
            "fake = sys.argv[2]\n"
            "os.makedirs(os.path.join(fake, os.path.basename(sub)))\n"
            "open(os.path.join(fake, os.path.basename(sub), 'FAKE.txt'), 'w').close()\n"
            "moved = parent + '.moved'\n"
            "mv(parent, moved)\n"
            "how = F.link_dir(fake, parent)\n"
            "try:\n"
            "    if not how or os.path.realpath(parent) != os.path.realpath(fake):\n"
            "        print('NOLINK')\n"
            "    else:\n"
            "        try:\n"
            "            print('LISTED %r' % sorted(F.list_own(sub)))\n"
            "        except ValueError:\n"
            "            print('REFUSED')\n"
            "        try:\n"
            "            print('MATCHED %r' % F.match_own(os.path.join(sub, '*.txt')))\n"
            "        except ValueError:\n"
            "            print('REFUSED')\n"
            "finally:\n"
            "    if how:\n"
            "        F.unlink_dir_link(parent)\n"
            "    mv(moved, parent)\n")
        r = subprocess.run([sys.executable, "-B", "-c", prog, HERE, fake], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        out = (r.stdout or "").strip().splitlines()
        if out == ["NOLINK"]:
            if _fx_tmp.can_link_a_directory():
                self.fail("this PC could not swap the parent for a link, yet heart2's dir-link probe says it can make "
                          "one - the heart judges this proof here, and a skip would file it BLIND")
            self.skipTest("this PC can make no directory link - the swap is UNMEASURED here, not passing")
        self.assertEqual(out, ["REFUSED", "REFUSED"],
                         "a listing under a parent swapped for a link to another tree was answered - it listed that "
                         "tree as this process's own scratch: %r %s" % (out, (r.stderr or "")[-400:]))

    def test_a_swap_during_the_listing_answers_nothing(self):
        """★ REG-2455 - list_own / match_own read the RESOLVED directory and check the path again AFTER the read, so a
        directory renamed aside and replaced by a link to another tree WHILE it is being listed raises: that tree's
        names are never handed back as this scratch's. Driven in a child process whose own listing call makes the swap
        (os.listdir for list_own, os.scandir for match_own's glob), between fixture_tmp's check and its read."""
        fake = tempfile.mkdtemp(prefix="fake_tree_")       # outside the CHILD's parent: this process's own scratch
        with open(os.path.join(fake, "FAKE.txt"), "w") as fh:
            fh.write("another tree\n")
        prog = (
            "import os, sys, tempfile, time\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import fixture_tmp as F\n"
            "def mv(a, b):  # Windows may refuse a rename for a moment while a scanner holds a handle\n"
            "    for i in range(25):\n"
            "        try:\n"
            "            return os.rename(a, b)\n"
            "        except PermissionError:\n"
            "            if os.name != 'nt' or i == 24:\n"
            "                raise\n"
            "            time.sleep(0.2)\n"
            "F.contain()\n"
            "fake = sys.argv[2]\n"
            "def attempt(call, name):\n"
            "    sub = tempfile.mkdtemp(prefix='own_')\n"
            "    open(os.path.join(sub, 'real.txt'), 'w').close()\n"
            "    real, done = getattr(os, name), {}\n"
            "    def swapping(*a, **k):\n"
            "        if not done:\n"
            "            done['moved'] = sub + '.moved'\n"
            "            mv(sub, done['moved'])\n"
            "            done['how'] = F.link_dir(fake, sub)\n"
            "            if not done['how']:\n"
            "                raise RuntimeError('no link')\n"
            "        return real(*a, **k)\n"
            "    setattr(os, name, swapping)\n"
            "    try:\n"
            "        return 'LISTED %r' % (call(sub),)\n"
            "    except ValueError:\n"
            "        return 'REFUSED'\n"
            "    except RuntimeError:\n"
            "        return 'NOLINK'\n"
            "    finally:\n"
            "        setattr(os, name, real)\n"
            "        if done.get('how'):\n"
            "            F.unlink_dir_link(sub)\n"
            "        if done.get('moved'):\n"
            "            mv(done['moved'], sub)\n"
            "print(attempt(lambda d: sorted(F.list_own(d)), 'listdir'))\n"
            "print(attempt(lambda d: sorted(os.path.basename(x) for x in F.match_own(os.path.join(d, '*.txt'))),"
            " 'scandir'))\n")
        r = subprocess.run([sys.executable, "-B", "-c", prog, HERE, fake], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        out = (r.stdout or "").strip().splitlines()
        if "NOLINK" in out:
            if _fx_tmp.can_link_a_directory():
                self.fail("this PC could not swap the directory for a link, yet heart2's dir-link probe says it can "
                          "make one - the heart judges this proof here, and a skip would file it BLIND")
            self.skipTest("this PC can make no directory link - the swap is UNMEASURED here, not passing")
        self.assertEqual(out, ["REFUSED", "REFUSED"],
                         "a directory swapped for a link to another tree while it was being listed was answered - "
                         "that tree's names came back as this scratch's: %r %s" % (out, (r.stderr or "")[-400:]))

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


def _refused(*a, **k):
    """os.symlink as Windows answers it without the privilege (MEASURED on his ALT, REG-1668)"""
    raise OSError(1314, "A required privilege is not held by the client")


def _no_junction(*a, **k):
    raise OSError(4390, "The file or directory is not a reparse point")


class TheEscapeIsMeasuredWhereALinkCanBeMade(unittest.TestCase):
    """REG-2366 - red-proof [2] is judged only where a directory link can be made, and on Windows a refused symlink
    becomes a junction - so the proof reads PROVEN where it can be, ELSEWHERE where it cannot, and never BLIND.
    Every case here runs on every OS: nothing in it needs a link this PC must be able to make."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="link_")          # inside the contained parent
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_the_heart_asks_the_question_the_case_asks(self):
        """the capability is wired end to end: heart2 knows "dir-link", its probe is the same routine the case uses,
        proof [2] declares it, and the heart's answer on this PC is the probe's"""
        self.assertEqual(tuple(heart2.PROOF_NEEDS_HOST.get("dir-link") or ())[:2],
                         ("fixture_tmp", "can_link_a_directory"),
                         "heart2 does not know the dir-link capability (or asks another probe): a proof declaring it is "
                         "INVALID everywhere, or judged by a question the case never asks")
        proofs = heart2.red_proofs_in(os.path.abspath(__file__))
        unresolved = [p for p in proofs if p.get("replace") == "    p = os.path.abspath(path)\n"]
        self.assertEqual(len(unresolved), 1, "PREMISE: the unresolved-path proof is not where it was")
        self.assertEqual(unresolved[0].get("needs"), "dir-link",
                         "the unresolved-path proof does not declare dir-link: on a PC that can make no link its one "
                         "catcher skips in both runs and the heart files it BLIND")
        self.assertIs(heart2.host_lacks("dir-link")[0], not _fx_tmp.can_link_a_directory(),
                      "the heart's answer for this PC is not the probe's")

    def test_a_pc_that_can_make_no_link_reads_elsewhere(self):
        """★ the shape of a PC with no way to link: the symlink refused, and on Windows the junction and `mklink /J`
        refused too - link_dir makes nothing, the probe says no, and the heart files [2] ELSEWHERE instead of judging
        a case that can only skip"""
        refused_cmd = subprocess.CompletedProcess(["cmd"], 1, b"", b"refused")
        with mock.patch.object(os, "symlink", _refused), \
                mock.patch.dict(sys.modules, {"_winapi": types.SimpleNamespace(CreateJunction=_no_junction)}), \
                mock.patch.object(subprocess, "run", lambda *a, **k: refused_cmd):
            self.assertIsNone(_fx_tmp.link_dir(HERE, os.path.join(self.d, "no_link")),
                              "PREMISE: a link was made with every way to make one refused")
            self.assertFalse(_fx_tmp.can_link_a_directory(),
                             "the dir-link probe says yes on a PC that can make no link: the heart judges [2] there "
                             "and its one catcher cannot run")
            self.assertIs(heart2.host_lacks("dir-link")[0], True,
                          "a PC that can make no link does not read [2] ELSEWHERE")

    def test_a_refused_symlink_becomes_a_junction_on_windows(self):
        """★ REG-1668's way, driven on any OS: with the symlink refused on a Windows-shaped run, link_dir asks for a
        junction - target first, then the link, as CPython's _winapi.CreateJunction takes them. (The junction itself
        is CPython's; this pins that it is asked for, and the right way round.)"""
        target, link, made = os.path.join(self.d, "target"), os.path.join(self.d, "junction"), []
        self.addCleanup(_fx_tmp.unlink_dir_link, link)     # a sabotaged run may reach a real `mklink /J` on Windows
        with mock.patch.object(os, "symlink", _refused), mock.patch.object(os, "name", "nt"), \
                mock.patch.dict(sys.modules, {"_winapi": types.SimpleNamespace(
                    CreateJunction=lambda src, dst: made.append((src, dst)))}):
            how = _fx_tmp.link_dir(target, link)
        self.assertEqual(how, "junction", "a refused symlink did not fall back to a junction on Windows: the escape is "
                                          "never measured there and [2] is ELSEWHERE on every PC he plays on")
        self.assertEqual(made, [(os.path.abspath(target), os.path.abspath(link))],
                         "the junction was asked for the wrong way round (CreateJunction takes the target first)")


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
        "why": "REG-2362 - the path is not resolved: a link inside the scratch (a symlink, or a junction on Windows) "
               "reads the tree",
        "file": "fixture_tmp.py",
        "find": "    p = os.path.realpath(path)\n",
        "replace": "    p = os.path.abspath(path)\n",
        "matches": 1,
        # REG-2366 - its one catcher needs a directory link: a PC that can make neither a symlink nor a junction files
        # this proof ELSEWHERE (proven where one can be made), never BLIND
        "needs": "dir-link",
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
    {
        "why": "REG-2366 - the junction fallback is gone: on Windows without the symlink privilege the escape is never "
               "measured, and [2] is ELSEWHERE on every PC he plays on",
        "file": "fixture_tmp.py",
        "find": "        _winapi.CreateJunction(os.path.abspath(target), os.path.abspath(link))\n",
        "replace": "        raise OSError(\"no junction\")\n",
        "matches": 1,
    },
    {
        "why": "REG-2366 - the dir-link probe says yes on a PC that can make no link: the heart judges [2] where its one "
               "catcher cannot run",
        "file": "fixture_tmp.py",
        "find": "        if not link_dir(target, link):\n            return False\n",
        "replace": "        if not link_dir(target, link):\n            return True\n",
        "matches": 1,
    },
    {
        "why": "REG-2366 - heart2 forgets the dir-link capability: [2] declares a name no probe knows and reads INVALID "
               "on every PC",
        "file": "heart2.py",
        "find": "    \"dir-link\": (\"fixture_tmp\", \"can_link_a_directory\",\n",
        "replace": "    \"dir-link-gone\": (\"fixture_tmp\", \"can_link_a_directory\",\n",
        "matches": 1,
    },
    {
        "why": "REG-2455 - the contained parent is re-resolved on every call: a rename + link swap makes another tree "
               "'the scratch', and list_own lists it",
        "file": "fixture_tmp.py",
        "find": "    root = _HELD.get(\"real\") or os.path.realpath(held)\n",
        "replace": "    root = os.path.realpath(held)\n",
        "matches": 1,
        "needs": "dir-link",
    },
    {
        "why": "REG-2455 - list_own never checks the path again after its read: a swap during the listing hands another "
               "tree's names back as this scratch's",
        "file": "fixture_tmp.py",
        "find": "    _still_own(path, p)\n    return names\n",
        "replace": "    return names\n",
        "matches": 1,
        "needs": "dir-link",
    },
    {
        "why": "REG-2455 - match_own never checks the path again after its glob: a swap during the match hands another "
               "tree's paths back as this scratch's",
        "file": "fixture_tmp.py",
        "find": "    _still_own(d, p)\n",
        "replace": "    pass\n",
        "matches": 1,
        "needs": "dir-link",
    },
]
