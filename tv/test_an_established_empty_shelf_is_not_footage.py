# -*- coding: utf-8 -*-
"""#123 — AN ESTABLISHED, EMPTY SHELF IS A VENUE WITHOUT FOOTAGE; AN EMPTIED ONE IS NOT.

⚠ WHY: machine_tree.establish() creates every root and proves a write with a probe it then removes,
so any host that ran the recorder has an empty tv/frames/hist. On CI an earlier gate does exactly
that, reel_demo._shelf() answered "present", and a runner that never held a frame failed "the
printer walked his shelf" on every push (`0 reel(s) walked … ⚠ 1 check(s) DISAGREE`).

The line this pins is the one reel_demo's own docstring draws: a shelf that EXISTS and walked
nothing is the real defect and must stay a FAIL. So EMPTY needs both halves — the directory holds
nothing, AND this host has no record of ever closing a reel. A ledger naming a closed reel means
footage WAS here; a ledger that will not read means nobody can say it never was. Both stay
"present". [[unknown-stays-unknown]] [[test-venue]]

DRIVEN on temp shelves and a temp ledger — never his hist, never his tombstones. RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import reel_demo as D        # noqa: E402
import reel_retention as RR  # noqa: E402
import tv_diablo as TD       # noqa: E402


class AnEstablishedEmptyShelfIsNotFootage(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="empty-shelf-")
        self.hist = os.path.join(self.tmp, "frames", "hist")
        self.ledger = os.path.join(self.tmp, "reel_tombstones.json")
        self._hist, self._path = TD.HIST_DIR, RR._tombstone_path
        TD.HIST_DIR = self.hist
        RR._tombstone_path = lambda *a, **k: self.ledger

    def tearDown(self):
        TD.HIST_DIR, RR._tombstone_path = self._hist, self._path
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ledger(self, text):
        with io.open(self.ledger, "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_no_directory_is_absent(self):
        self.assertEqual(D._shelf()[0], "absent")

    def test_a_directory_establish_left_behind_is_empty(self):
        os.makedirs(self.hist)
        # the probe establish() removes, and any other dotfile, is not footage
        io.open(os.path.join(self.hist, ".DS_Store"), "w").close()
        st, why = D._shelf()
        self.assertEqual(st, "empty", why)
        self.assertIn("no tombstone ledger", why)

    def test_one_frame_is_a_shelf(self):
        os.makedirs(self.hist)
        io.open(os.path.join(self.hist, "1_1789333293692.jpg"), "w").close()
        self.assertEqual(D._shelf()[0], "present")

    def test_an_emptied_shelf_with_closed_reels_on_record_is_NOT_a_venue(self):
        """Footage was here and is gone: the walked-nothing FAIL must still fire."""
        os.makedirs(self.hist)
        self._ledger(json.dumps({"reels": [{"reel": "r1", "mb": 3.0}]}))
        st, why = D._shelf()
        self.assertEqual(st, "present", why)
        self.assertIn("1 closed reel", why)

    def test_an_unreadable_ledger_is_not_a_record_of_nothing(self):
        os.makedirs(self.hist)
        self._ledger("{not json")
        st, why = D._shelf()
        self.assertEqual(st, "present", "an unreadable ledger was read as 'never closed a reel': %s"
                         % why)

    def test_a_ledger_with_no_reel_list_is_not_zero(self):
        os.makedirs(self.hist)
        self._ledger(json.dumps([]))
        self.assertEqual(D._closed_reels_on_record()[0], None)
        self.assertEqual(D._shelf()[0], "present")

    def test_an_empty_ledger_is_a_measured_zero(self):
        os.makedirs(self.hist)
        self._ledger(json.dumps({"reels": []}))
        self.assertEqual(D._shelf()[0], "empty")

    def test_every_skip_exits_77_whatever_the_venue_is_called(self):
        """Both return paths of main() ask the ONE decision (state == SKIPPED)."""
        real = D.demo
        try:
            for venue in ("no-shelf", "empty-shelf", "a-venue-nobody-has-named-yet"):
                D.demo = lambda *a, _v=venue, **k: {"ok": False, "state": "SKIPPED", "venue": _v,
                                                    "reels": [], "checks": [], "why": "simulated"}
                self.assertEqual(D.main([]), 77, "a %r skip did not exit 77" % venue)
            D.demo = lambda *a, **k: {"ok": False, "state": "FAIL", "reels": [], "checks": [],
                                      "why": "simulated"}
            self.assertEqual(D.main([]), 1, "a FAIL with no reels exited as a skip")
        finally:
            D.demo = real

    def test_the_gate_declares_both_venues(self):
        import re
        import run_gates as RG
        g = [x for x in RG.GATES if x.name == "reel_demo"]
        self.assertEqual(len(g), 1, "premise: the reel_demo gate is registered once")
        pats = tuple(getattr(g[0], "skip_ok", None) or ())
        for state in ("absent", "empty"):
            line = "his reel shelf is %s on this venue (x), so nothing was walked" % state
            self.assertTrue(any(re.search(p, line) for p in pats),
                            "an %s-shelf skip is undeclared, so run_gates counts it a failure" % state)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#123 - an unreadable tombstone ledger read as 'this host never closed a reel': an emptied shelf skips instead of failing",
        "file": "reel_demo.py",
        "find": "        if closed == 0:\n",
        "replace": "        if not closed:\n",
        "matches": 1,
    },
    {
        "why": "#123 - the early exit keyed on a venue spelling again: the empty-shelf skip exits 1 while printing 'a declared SKIP'",
        "file": "reel_demo.py",
        "find": "        return 77 if r.get(\"state\") == \"SKIPPED\" else 1\n",
        "replace": "        return 77 if r.get(\"venue\") == \"no-shelf\" else 1\n",
        "matches": 1,
    },
    {
        "why": "#123 - the shelf's contents never asked: a directory holding frames reads as an established empty tree",
        "file": "reel_demo.py",
        "find": "        held = [n for n in os.listdir(p) if not n.startswith(\".\")]\n",
        "replace": "        held = []\n",
        "matches": 1,
    },
    {
        "why": "#123 - run_gates declares only the absent sentence: an empty-shelf skip is undeclared and counted a failure",
        "file": "run_gates.py",
        "find": "         skip_ok=(r\"reel shelf is (?:absent|empty) on this venue\",)),",
        "replace": "         skip_ok=(r\"reel shelf is absent on this venue\",)),",
        "matches": 1,
    },
]
