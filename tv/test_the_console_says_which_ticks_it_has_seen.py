# -*- coding: utf-8 -*-
"""REG-3010 (#163, his ruling 2026-10-29 Q6) - THE CONSOLE SAYS WHICH TICKED NAMES IT HAS SEEN, IN ONE READ.

The board lists the ticks nothing on IT vouches for (REG-3009); the console's Chronicle inbox then drops every name the
console's own ledgers hold a sighting of, and asks Dean about the rest. control_app.evidence_names is that question: the walk
evidence_for takes (the chronicle books, then the vault witness ledger), for a whole list, reading each ledger ONCE. A name
nobody saw is False; a vault ledger that exists and will not read makes a name the books do not hold None (UNKNOWN) - never
False, so no tick is called unconfirmed on a ledger nobody could open; a chronicle ledger that will not read is ok False.
POST /api/evidence_names serves it.

Python, against fixture ledgers in a temp dir (never his). RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

BOOKS = {"uniques": {"Wormskull": [{"reel": "reel_s_1_1", "frame": "a.jpg", "lane": "stash"}]},
         "sets": {"Aldur's Advance (boots)": [{"reel": "reel_s_2_2", "frame": "b.jpg", "lane": "stash"}]}}
VAULT = {"owned": [{"name": "Grief", "lane": "stash",
                    "witnesses": [{"session": "s_3_3", "frame": "c.jpg", "lane": "stash", "conf": 0.9}]}]}
NAMES = ["Wormskull", "Aldur's Advance (boots)", "Grief", "Authority", "Wizardspike"]


class TheConsoleSaysWhichTicksItHasSeen(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ev_names_")
        self.ledger = os.path.join(self.tmp, "vault_accum.json")
        with io.open(self.ledger, "w", encoding="utf-8") as fh:
            json.dump(VAULT, fh)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ask(self, names, books=BOOKS, ledger=None):
        calls = {"chron": 0, "vault": 0}
        real_read = CA._vault_store_read

        def chron():
            calls["chron"] += 1
            if isinstance(books, Exception):
                raise books
            return books

        def vread(p):
            calls["vault"] += 1
            return real_read(p)

        with mock.patch.object(CA, "_chron_evidence_load", chron), \
                mock.patch.object(CA, "_vault_store_read", vread), \
                mock.patch.object(CA, "VAULT_LEDGER_PATH", ledger or self.ledger):
            return CA.evidence_names(names), calls

    def test_each_name_is_answered_from_the_books_and_the_vault(self):
        got, _ = self._ask(NAMES)
        self.assertTrue(got["ok"], got)
        self.assertEqual(got["has"], {"Wormskull": True, "Aldur's Advance (boots)": True, "Grief": True,
                                      "Authority": False, "Wizardspike": False}, got)

    def test_each_ledger_is_read_once_for_the_whole_list(self):
        _, calls = self._ask(NAMES)
        self.assertEqual(calls, {"chron": 1, "vault": 1}, "a ledger was re-read per name: %r" % calls)

    def test_an_unreadable_vault_ledger_makes_the_unseen_names_unknown_never_unseen(self):
        bad = os.path.join(self.tmp, "torn.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("{ not json")
        got, _ = self._ask(NAMES, ledger=bad)
        self.assertTrue(got["ok"], got)
        self.assertIsNone(got["has"]["Authority"], "a name only the torn vault ledger could answer read as never seen")
        self.assertTrue(got["has"]["Wormskull"], "a name the books hold lost its answer to a torn vault ledger")
        self.assertIn("could not be read", got.get("vaultWhy", ""))

    def test_an_unreadable_chronicle_ledger_answers_nothing(self):
        got, _ = self._ask(NAMES, books=ValueError("torn"))
        self.assertFalse(got["ok"])
        self.assertNotIn("has", got)

    def test_the_route_serves_it(self):
        s = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = s.index('        if path == "/api/evidence_names":\n')
        branch = s[i:s.index("            return\n", i)]
        self.assertIn('evidence_names(body.get("names"))', branch, "the POST route does not answer from evidence_names")


RED_PROOF = [
    {"why": "REG-3010 - the vault ledger's sightings are not asked",
     "file": "tv/control_app.py",
     "find": "        for led, sightings, extra in _evidence_sources(n, prop, None, vread):\n",
     "replace": "        for led, sightings, extra in _evidence_sources(n, prop, 'uniques', vread):\n",
     "matches": 1},
    {"why": "REG-3010 - an unreadable vault ledger reads as never seen",
     "file": "tv/control_app.py",
     "find": "        has[n] = True if got else (None if unread else False)\n",
     "replace": "        has[n] = True if got else False\n",
     "matches": 1},
    {"why": "REG-3010 - the vault ledger is read again for every name",
     "file": "tv/control_app.py",
     "find": "    got = _vault_evidence_for(n, _vault_read)\n",
     "replace": "    got = _vault_evidence_for(n)\n",
     "matches": 1},
    {"why": "REG-3010 - the route is not wired",
     "file": "tv/control_app.py",
     "find": "            self._json(200, evidence_names(body.get(\"names\")))\n",
     "replace": "            self._json(200, {\"ok\": False, \"why\": \"not wired\"})\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
