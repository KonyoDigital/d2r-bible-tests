# -*- coding: utf-8 -*-
"""v3845 - A BUMP-ONLY COMMIT INHERITS ITS PARENT'S PASSES (Elad, 2026-10-30 11:24).

Since v3843 every bump also writes tv/CHANGELOG.json. It was no stamp surface, so every bump read as a code
change and reran the gates its parent had just passed. The changelog now leaves the change set only as ONE new
head entry in bump_version's exact shape, for the bump's own new version, with leak-checked items. Any other
edit - an old entry reworded, a second entry, an entry for another version, any non-bump file - voids the
inheritance and the gate reruns. Builds on the v3774 fixture (test_a_version_bump_carries_the_gates_that_ignore_the_version).
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import test_a_version_bump_carries_the_gates_that_ignore_the_version as M  # noqa: E402  (fixture first: contain())
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

OLD = [{"ver": M.U, "date": "2026-10-19", "items": ["first thing"]}]


def _log(entries):
    return json.dumps(entries, indent=2, ensure_ascii=False)


class ABumpOnlyCommitInherits(unittest.TestCase):
    _base_setUp = M.ACoherentBumpCarries.setUp
    for _n in ("head", "gate", "book", "edit", "carried"):
        locals()[_n] = getattr(M.ACoherentBumpCarries, _n)
    _bump_files = M.ACoherentBumpCarries.bump

    def setUp(self):
        self._base_setUp()
        M._write(self.root, "tv/CHANGELOG.json", _log(OLD))
        M._git(self.root, "add", "-A")
        M._git(self.root, "commit", "-q", "-m", "changelog")
        M._SHAS[M.U] = self.head()

    def bump(self, entries=None):
        self._bump_files()
        new = {"ver": M.V, "date": "2026-10-30", "items": ["a second thing", "and a third"]}
        M._write(self.root, "tv/CHANGELOG.json", _log(entries if entries is not None else [new] + OLD))

    def test_a_bump_with_its_changelog_entry_carries(self):
        g = self.gate("t_plain.py"); b = self.book(g)
        self.bump()
        ok, why = self.carried(g, b)
        self.assertTrue(ok, "a bump-only change (with its changelog entry) reran a gate: %s" % why)

    def test_a_committed_bump_only_commit_carries(self):
        g = self.gate("t_plain.py"); b = self.book(g)
        self.bump()
        M._git(self.root, "commit", "-qam", "bump")
        self.assertTrue(self.carried(g, b)[0])

    def test_any_non_bump_change_voids_the_inheritance(self):
        g = self.gate("t_plain.py"); b = self.book(g)
        self.bump()
        self.edit("tv/control_app.py", "SALT = 1", "SALT = 9")
        self.assertFalse(self.carried(g, b)[0], "a code edit rode a bump and kept the parent's pass")

    def test_a_reworded_old_changelog_entry_voids_it(self):
        g = self.gate("t_plain.py"); b = self.book(g)
        new = {"ver": M.V, "date": "2026-10-30", "items": ["a second thing"]}
        self.bump([new, {"ver": M.U, "date": "2026-10-19", "items": ["first thing, rewritten"]}])
        self.assertFalse(self.carried(g, b)[0], "an edit to an old changelog entry was taken as a bump")

    def test_a_changelog_entry_for_another_version_voids_it(self):
        g = self.gate("t_plain.py"); b = self.book(g)
        self.bump([{"ver": "v555", "date": "2026-10-30", "items": ["x"]}] + OLD)
        self.assertFalse(self.carried(g, b)[0], "a changelog entry for a version the bump did not make carried")

    def test_two_new_changelog_entries_void_it(self):
        g = self.gate("t_plain.py"); b = self.book(g)
        e = {"ver": M.V, "date": "2026-10-30", "items": ["x"]}
        self.bump([e, dict(e)] + OLD)
        self.assertFalse(self.carried(g, b)[0], "two changelog entries were taken as one bump")

    def test_a_gate_that_reads_the_changelog_reruns(self):
        M._write(self.root, "tv/t_cl.py", "import control_app\nprint(open('CHANGELOG.json').read()[:1])\n")
        M._git(self.root, "add", "-A"); M._git(self.root, "commit", "-qm", "cl law")
        g = self.gate("t_cl.py"); b = self.book(g)
        self.bump()
        self.assertFalse(self.carried(g, b)[0], "a gate that reads the changelog carried over a bump")


RED_PROOF = [
    {"why": "the changelog is no stamp surface, so a bump-only commit reruns every gate",
     "file": "tv/gate_ledger.py",
     "find": '    "tv/CHANGELOG.json": (),  # handled by _changelog_versions',
     "replace": '    "tv/CHANGELOG.jsonX": (),  # handled by _changelog_versions', "matches": 1},
    {"why": "a second hunk beside the new head entry (an old entry reworded) is not looked at",
     "file": "tv/gate_ledger.py",
     "find": "    if not hunks or len(hunks) != 1:\n        return None\n    o, n, rem, add = hunks[0]\n    if rem or o != 1",
     "replace": "    if not hunks:\n        return None\n    o, n, rem, add = hunks[0]\n    if rem or o != 1", "matches": 1},
]

if __name__ == "__main__":
    unittest.main()
