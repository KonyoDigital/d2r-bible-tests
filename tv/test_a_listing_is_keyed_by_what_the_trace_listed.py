# -*- coding: utf-8 -*-
"""v3775 (REG-2296) — A GATE THAT LISTS A DIRECTORY IS KEYED BY WHAT ITS TRACED RUN LISTED.

On a v3775 bump-only run 80 gates (404 s) were never stored because the gate file itself calls
os.listdir / glob / os.walk ("the law lists a directory itself"), and 40 more (229 s) because the run
listed tv/frames/hist, a gitignored folder no diff can see. Every PASS is already stored only from a
traced run, and the trace records each listing: an added or deleted tracked file under a listed folder
is a hit, and an untracked one that comes or goes is a hit. So the static walk no longer refuses a
listing law. A listed folder with no tracked file is keyed by a snapshot of every entry under it
(name, size, mtime); any difference, or a snapshot that cannot be taken, runs the gate.
"""
import io
import os
import shutil
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
import test_a_gate_proven_on_these_bytes_is_carried as C  # noqa: E402

_LIST_TV = ("import os, sys\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
            "print(len(os.listdir(HERE)))\nsys.exit(0)\n")
_LIST_HIST = ("import os, sys\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
              "print(sorted(os.listdir(os.path.join(HERE, 'frames', 'hist'))))\nsys.exit(0)\n")


class AListingIsKeyedByItsTrace(unittest.TestCase):
    def setUp(self):
        self.held = C._Env(GITHUB_ACTIONS=None, GATE_LEDGER=None,
                           TV_SELF_ARMING_LEDGER=os.path.join(tempfile.mkdtemp(prefix="ls-arm."), "a.jsonl"))
        self.held.__enter__()
        self.addCleanup(self.held.__exit__, None, None, None)

    def _tree(self, files, hist=None):
        root, led = C._tree(files)
        self.addCleanup(shutil.rmtree, root, True)
        if hist is not None:
            with io.open(os.path.join(root, ".gitignore"), "a", encoding="utf-8") as fh:
                fh.write("tv/frames/\n")
            C._commit(root, "ignore footage")
            os.makedirs(os.path.join(root, "tv", "frames", "hist"))
            for name, text in hist.items():
                C._write(root, "tv/frames/hist/" + name, text)
        return root, led

    def test_a_listing_law_has_a_key(self):
        root, led = self._tree({"t_ls.py": _LIST_TV})
        key, _m, why = C._open(led).key_for(C._gate(root, "t_ls.py"))
        self.assertIsNotNone(key, why)

    def test_a_listing_law_is_stored_and_a_new_file_under_it_runs_it(self):
        root, led = self._tree({"t_ls.py": _LIST_TV, "other.py": "a\n"})
        gate = C._gate(root, "t_ls.py")
        book = C._open(led)
        self.assertTrue(C._prove(book, gate), book.last_why)
        C._write(root, "tv/other.py", "b\n")
        entry, why = C._open(led).lookup(gate)
        self.assertIsNotNone(entry, "an edit the listing cannot see stopped the carry: %s" % why)
        C._write(root, "tv/brand_new.py", "N = 1\n")
        entry, why = C._open(led).lookup(gate)
        self.assertIsNone(entry, "a new file in the listed folder was carried")

    def _hist(self):
        root, led = self._tree({"t_hist.py": _LIST_HIST}, hist={"a.jpg": "aaaa"})
        gate = C._gate(root, "t_hist.py")
        book = C._open(led)
        self.assertTrue(C._prove(book, gate), "an ignored listing was not keyed: %s" % book.last_why)
        entry, why = C._open(led).lookup(gate)
        self.assertIsNotNone(entry, "an unchanged footage folder did not carry: %s" % why)
        return root, led, gate

    def test_an_unchanged_footage_folder_carries(self):
        self._hist()

    def test_a_new_reel_runs_it(self):
        root, led, gate = self._hist()
        C._write(root, "tv/frames/hist/b.jpg", "bb")
        entry, why = C._open(led).lookup(gate)
        self.assertIsNone(entry, "a new reel in the footage folder was carried")
        self.assertIn("listing of tv/frames/hist", why or "")

    def test_a_rewritten_reel_runs_it(self):
        root, led, gate = self._hist()
        C._write(root, "tv/frames/hist/a.jpg", "a much longer body")
        self.assertIsNone(C._open(led).lookup(gate)[0], "a rewritten reel was carried")

    def test_a_renamed_reel_runs_it(self):
        root, led, gate = self._hist()
        d = os.path.join(root, "tv", "frames", "hist")
        os.rename(os.path.join(d, "a.jpg"), os.path.join(d, "z.jpg"))
        self.assertIsNone(C._open(led).lookup(gate)[0], "a renamed reel was carried")

    def test_an_unreadable_snapshot_runs_it(self):
        root, led, gate = self._hist()
        book = C._open(led)
        book._ensure()
        book.entries[gate.name]["snaps"] = "x"
        entry, why = book.lookup(gate)
        self.assertIsNone(entry)

    def test_a_missing_or_huge_folder_has_no_snapshot(self):
        root = tempfile.mkdtemp(prefix="ls-snap.")
        self.addCleanup(shutil.rmtree, root, True)
        self.assertIsNone(GL.listing_snap(root, "absent"))
        os.makedirs(os.path.join(root, "big"))
        for i in range(5):
            C._write(root, "big/f%d" % i, "x")
        held = GL._SNAP_MAX
        GL._SNAP_MAX = 3
        try:
            self.assertIsNone(GL.listing_snap(root, "big"), "a folder past the cap was snapshotted")
        finally:
            GL._SNAP_MAX = held
        self.assertEqual(len(GL.listing_snap(root, "big")), 5)

    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": "the static walk refuses a listing law again", "file": "gate_ledger.py",
     "find": "                allow_listing=True,  # LEDGER-LISTING-TRACED\n",
     "replace": "                allow_listing=False,  # LEDGER-LISTING-TRACED\n", "matches": 1},
    {"why": "a footage listing is refused instead of snapshotted", "file": "gate_ledger.py",
     "find": "            snap = listing_snap(root, path)\n", "replace": "            snap = None\n", "matches": 1},
    {"why": "a moved snapshot still carries", "file": "gate_ledger.py",
     "find": "            if listing_snap(root, path) != snaps[path]:  # LEDGER-SNAP-MOVED\n",
     "replace": "            if False:  # LEDGER-SNAP-MOVED\n", "matches": 1},
    {"why": "the snapshot is not stored with the PASS", "file": "gate_ledger.py",
     "find": "            \"snaps\": dict(traced.get(\"snaps\") or {}),\n", "replace": "            \"snaps\": {},\n",
     "matches": 1},
    {"why": "the trace drops its snapshots", "file": "gate_ledger.py",
     "find": "        return {\"inputs\": inputs, \"listed\": listed, \"snaps\": snaps,\n",
     "replace": "        return {\"inputs\": inputs, \"listed\": listed, \"snaps\": {},\n", "matches": 1},
    {"why": "a huge folder is snapshotted", "file": "gate_ledger.py",
     "find": "                if len(out) > _SNAP_MAX:  # LEDGER-SNAP-MAX\n",
     "replace": "                if False:  # LEDGER-SNAP-MAX\n", "matches": 1},
    {"why": "a missing folder snapshots as empty", "file": "gate_ledger.py",
     "find": "        if os.path.islink(top) or not os.path.isdir(top):\n            return None\n",
     "replace": "        if False:\n            return None\n", "matches": 1},
    {"why": "the snapshot ignores size and mtime", "file": "gate_ledger.py",
     "find": "                                              st.st_size, st.st_mtime_ns))\n",
     "replace": "                                              0, 0))\n", "matches": 1},
    {"why": "the snapshot ignores names", "file": "gate_ledger.py",
     "find": "                out.append(\"%s\\t%d\\t%d\" % (os.path.relpath(full, top).replace(os.sep, \"/\"),\n",
     "replace": "                out.append(\"%s\\t%d\\t%d\" % (\"\",\n", "matches": 1},
    {"why": "an unreadable snapshot is trusted", "file": "gate_ledger.py",
     "find": "        if not isinstance(snaps, dict):\n            return None, \"the stored listing snapshot is unreadable\"\n",
     "replace": "        if not isinstance(snaps, dict):\n            snaps = {}\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
