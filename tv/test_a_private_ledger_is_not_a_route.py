# -*- coding: utf-8 -*-
"""REG-1954 - A HIDDEN *_roster.json IS A PRIVATE LEDGER, NEVER A CHRONICLE OR ROSTER ROUTE.

The v3602 pre-prove from his main checkout: test_organ_matrix red untampered - "the corroborator invented lane(s) that
do not exist: {'.char'}". Both route finders discover routes from `*_roster.json` on disk, and char_select keeps its
per-PC learned-character ledger at tv/.char_roster.json (gitignored, present only on a PC that learned characters).
It was read as a route keyed ".char", the corroborator published "chronicle..char" / "roster..char", and every
worktree (no such file) stayed green.

The law plants a shipped roster and a hidden ledger in a temp dir and asks BOTH finders: only the shipped one is a
route.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import chronicle_routes as CR  # noqa: E402
import roster_routes as RR  # noqa: E402


class APrivateLedgerIsNotARoute(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="routes_law_")
        for n in ("unique_roster.json", ".char_roster.json"):
            with io.open(os.path.join(self.d, n), "w", encoding="utf-8") as fh:
                fh.write("{}")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_both_finders_skip_a_hidden_ledger(self):
        for mod in (CR, RR):
            with self.subTest(mod.__name__), mock.patch.object(mod, "HERE", self.d):
                got = mod._routes_on_disk()
                self.assertIn(("unique", "unique_roster.json"), got, "baseline: the shipped roster was not found")
                self.assertNotIn((".char", ".char_roster.json"), got,
                                 "%s read a private dot-file ledger as a route (REG-1954)" % mod.__name__)


RED_PROOF = [
    {
        "why": "REG-1954 - the chronicle route finder reads hidden ledgers again (.char_roster.json becomes route '.char')",
        "file": "tv/chronicle_routes.py",
        "find": "        if p.startswith(\".\"):\n            continue\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1954 - the roster route finder reads hidden ledgers again",
        "file": "tv/roster_routes.py",
        "find": "        if p.startswith(\".\"):\n            continue\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
