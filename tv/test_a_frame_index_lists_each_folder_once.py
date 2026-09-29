# -*- coding: utf-8 -*-
"""2026-09-28 — THE FRAME INDEX STAT'D EVERY FILE, AND ON WINDOWS THAT IS THE WHOLE RIVER.

HIS WORDS: "the windows needs proper care and attention.. its needs to work perfectly and smoothly there
thats the way we know it will work for dean too".

MEASURED on his ALT (Windows + Boosteroid, 14 reels, v3521): GET /api/river answered in 32.8 s; his Mac
answered the same route for 66 reels in 4.1 s. A read-only profile on the ALT put 8.2 s in one lane view,
4.1 s of it in 34,143 nt.stat calls made by os.path.getsize inside frame_ref.Index, and 1.7 s in 21,349
os.path.relpath calls; reel_retention._dir_mb summed sizes the same way. The directory listing already carries each file's size on Windows, so one listing
per folder answers what 34,143 stats did.

DRIVEN on a fixture tree: the new index equals the old os.walk + getsize + relpath walk exactly (paths,
stems in order, walk order, file and byte counts, a symlinked folder not entered), and building it calls
neither getsize nor relpath nor a per-file os.stat. RED_PROOF below.
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import frame_ref as FR  # noqa: E402


def _old_index(root):
    """The walk this replaced, kept verbatim as the reference."""
    by_path, by_stem, files, size = {}, {}, 0, 0
    for dirpath, _dirs, names in os.walk(root):
        for f in names:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root).replace("\\", "/")
            by_path[rel] = full
            by_stem.setdefault(FR.stem_of(rel), []).append(rel)
            files += 1
            try:
                size += os.path.getsize(full)
            except OSError:
                pass
    return by_path, by_stem, files, size


class AFrameIndexListsEachFolderOnce(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="frame_index_case_")
        self.addCleanup(shutil.rmtree, self.root, True)
        # two reels, each with a nested folder, a stem that repeats across reels, and a loose file
        for reel in ("reel_s_1790000000000", "reel_s_1790000100000"):
            for sub in ("", "hist", "hist/deep"):
                d = os.path.join(self.root, reel, sub)
                os.makedirs(d, exist_ok=True)
                for i in range(4):
                    with open(os.path.join(d, "f_%d_%d.jpg" % (len(sub), i)), "wb") as fh:
                        fh.write(b"x" * (10 + i + len(sub)))
        with open(os.path.join(self.root, "loose.png"), "wb") as fh:
            fh.write(b"yy")
        self.linked = False
        if hasattr(os, "symlink"):
            try:
                os.symlink(os.path.join(self.root, "reel_s_1790000000000"), os.path.join(self.root, "a_link_dir"))
                os.symlink(os.path.join(self.root, "loose.png"), os.path.join(self.root, "a_link_file.png"))
                self.linked = True
            except (OSError, NotImplementedError):
                pass

    def test_it_equals_the_walk_it_replaced(self):
        want_path, want_stem, want_files, want_bytes = _old_index(self.root)
        got = FR.Index(self.root)
        self.assertGreater(want_files, 20, "PREMISE: the fixture tree holds almost nothing")
        self.assertEqual(list(got.by_path.items()), list(want_path.items()),
                         "the index no longer walks the tree the way os.walk did (paths or order)")
        self.assertEqual(got.by_stem, want_stem, "a stem lists different frames, or in a different order")
        self.assertEqual((got.files, got.bytes), (want_files, want_bytes))

    def test_a_symlinked_folder_is_not_entered(self):
        if not self.linked:
            self.skipTest("this PC cannot make a symlink - the case is not measured here")
        got = FR.Index(self.root)
        self.assertFalse(any(p.startswith("a_link_dir/") for p in got.by_path),
                         "the index walked INTO a symlinked folder, which os.walk never did")
        self.assertIn("a_link_file.png", got.by_path, "a symlinked FILE is a file, as os.walk lists it")

    def test_it_asks_no_file_for_its_size_one_by_one(self):
        real_stat = os.stat
        calls = []

        def counting_stat(*a, **k):
            calls.append(a[:1])
            return real_stat(*a, **k)

        def banned(*a, **k):
            raise AssertionError("a per-file path call ran: %r" % (a[:1],))

        with mock.patch.object(os, "stat", counting_stat), \
                mock.patch.object(os.path, "getsize", banned), \
                mock.patch.object(os.path, "relpath", banned):
            got = FR.Index(self.root)
        self.assertGreater(got.files, 20, "PREMISE: nothing was indexed, so nothing was measured")
        self.assertLessEqual(len(calls), 2, "the index made %d os.stat calls for %d files - one per file is "
                                            "what cost his ALT 33 s" % (len(calls), got.files))

    def test_a_reels_size_is_read_from_the_listing_too(self):
        import reel_retention as RR
        want = sum(os.path.getsize(os.path.join(d, f)) for d, _s, fs in os.walk(self.root) for f in fs)

        def banned(*a, **k):
            raise AssertionError("a per-file getsize ran: %r" % (a[:1],))
        with mock.patch.object(os.path, "getsize", banned):
            got = RR._dir_mb(self.root)
        self.assertAlmostEqual(got, want / (1024.0 * 1024.0), places=9,
                               msg="the reel size no longer equals the os.walk sum")
        self.assertEqual(RR._dir_mb(os.path.join(self.root, "never_made")), 0.0)

    def test_a_missing_or_empty_root_is_empty(self):
        for r in (None, "", os.path.join(self.root, "never_made")):
            got = FR.Index(r)
            self.assertEqual((got.files, got.bytes, got.by_path), (0, 0, {}))


RED_PROOF = [
    {
        "why": "2026-09-28 - every file is stat'd for its size again (34,143 stats, 33 s on his ALT)",
        "file": "frame_ref.py",
        "find": "            size = e.stat().st_size\n",
        "replace": "            size = os.path.getsize(os.path.join(folder, e.name))\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - subfolders are walked in reverse, so the index no longer matches os.walk's order",
        "file": "frame_ref.py",
        "find": "            todo.extend(reversed(sub))\n",
        "replace": "            todo.extend(sub)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a symlinked folder is walked into, which os.walk never did",
        "file": "frame_ref.py",
        "find": "                if not e.is_symlink():\n",
        "replace": "                if True:\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - a reel's size is read one getsize per file again",
        "file": "reel_retention.py",
        "find": "                total += size\n",
        "replace": "                total += os.path.getsize(os.path.join(here, name))\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
