# -*- coding: utf-8 -*-
"""#246 L11 — EVERY ROW THE MAIN LEDGER LOCKS REACHES THE BOARD'S LOCK. Both halves, joined, driven.

tv/main_character.py has kept a Wilson ledger of what he wears since v2320 — `is_locked` needs his 3 sightings and
a lower bound over 0.43 on "seen on his character" — and bible.html read it ZERO times. So the ledger could lock
an item and the board could still file it to a mule: two halves, each built right, joined at neither.
[[the-unjoined-end]]

WHAT THIS LAW HOLDS:
  · THE CONSOLE HALF — GET /api/main_locks, served by the REAL control_app Handler on an ephemeral port over a
    FIXTURE ledger (main_character.LEDGER pointed at a temp file; his real ledger is never read), answers every
    row `is_locked` locks — and only those — with the reason.
  · THE BOARD HALF — the SHIPPED lock block, cut from bible.html and run in node, fed that exact answer: every
    locked row locks the board's `_laneLocked` and the door refuses it; an unlocked row does not.
  · THE JOIN — the path the board fetches is the path the console serves, and it answered 200.
  · UNKNOWN STAYS UNKNOWN — an unreadable ledger is ok:false with `locked: null` (never an empty list), and the
    board keeps MAIN_LOCKS null on it: "nobody could ask" never reads as "nothing is his gear".
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  — this run's scratch dirs leave with it
_fx_tmp.contain()

import control_app as ca  # noqa: E402
import main_character as MC  # noqa: E402
from test_main_gear_never_files_to_a_mule import _src, _lock_block, HARNESS as _H  # noqa: E402

NODE = shutil.which("node")

#: game item names only; the counts are the shape his ledger keeps, never his rows
LEDGER = {
    "gore rider": {"name": "Gore Rider", "equip": 3, "seen": 3, "sessions": ["s1", "s2", "s3"]},
    "string of ears": {"name": "String of Ears", "equip": 1, "seen": 1, "sessions": ["s1"]},
    "raven frost": {"name": "Raven Frost", "equip": 0, "seen": 5, "sessions": ["s1", "s2", "s3", "s4", "s5"]},
}


class EveryLockedMainRowReachesTheBoard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="main_locks_law_")
        cls.real_ledger = MC.LEDGER
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        MC.LEDGER = cls.real_ledger
        cls.srv.shutdown()
        cls.srv.server_close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _serve(self, content):
        p = os.path.join(self.tmp, "main_character.json")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
        MC.LEDGER = p
        with urllib.request.urlopen("http://127.0.0.1:%d/api/main_locks" % self.port, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8"))

    def _board(self, answer, names):
        body = ("var OUT = { applied: window._mainLocksApply(%s), main: window.MAIN_LOCKS, locks: {}, files: {} };"
                "var L2 = [{ session: 's_a', frame: 'f_a.jpg', conf: 0.9 }, { session: 's_b', frame: 'f_b.jpg', conf: 0.85 }];"
                "%s.forEach(function(n){ OUT.locks[n] = window._laneLocked(n);"
                " OUT.files[n] = !!window.vaultFile(n, { lane: 'stash', sessions: L2 }).ok; });"
                "process.stdout.write(JSON.stringify(OUT));" % (json.dumps(answer), json.dumps(names)))
        from test_every_mule_filing_carries_its_witness import _door, _say_line
        s = _src()
        prog = _H + _say_line(s) + _lock_block(s) + _door(s) + body
        r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise AssertionError("the shipped lock would not execute: %s" % (r.stderr or r.stdout)[-600:])
        return json.loads(r.stdout)

    def test_the_console_publishes_exactly_what_the_ledger_locks(self):
        st, d = self._serve(json.dumps(LEDGER))
        self.assertEqual(200, st)
        self.assertTrue(d.get("ok"), d)
        want = sorted(row["name"] for row in LEDGER.values() if MC.is_locked(row["name"])[0])
        self.assertEqual(["Gore Rider"], want, "premise: the fixture must lock exactly one row")
        got = sorted(r["name"] for r in d["locked"])
        self.assertEqual(want, got, "the console's answer and the ledger's own verdict disagree")
        self.assertTrue(all(r.get("why") for r in d["locked"]), "a published lock carries no reason")

    @unittest.skipIf(NODE is None, "node is absent — the board half is UNMEASURED, not passing")
    def test_every_published_lock_locks_the_board_and_the_door_refuses_it(self):
        _st, d = self._serve(json.dumps(LEDGER))
        names = [row["name"] for row in LEDGER.values()]
        o = self._board(d, names)
        self.assertTrue(o["applied"], "the board refused the console's answer: %r" % d)
        for row in LEDGER.values():
            locked = MC.is_locked(row["name"])[0]
            self.assertEqual("equipment" if locked else "", o["locks"][row["name"]],
                             "%s: the ledger says locked=%s and the board says %r" % (row["name"], locked,
                                                                                    o["locks"][row["name"]]))
            self.assertEqual(not locked, o["files"][row["name"]],
                             "%s: the door %s a name the ledger %s" % (row["name"],
                                                                     "filed" if o["files"][row["name"]] else "refused",
                                                                     "locks" if locked else "does not lock"))

    def test_the_board_fetches_the_path_the_console_serves(self):
        block = _lock_block(_src())
        paths = re.findall(r"fetch\('(/api/[a-z_]+)'", block)
        self.assertEqual(["/api/main_locks"], paths, "the board's MAIN-lock read names a path: %r" % paths)
        st, _d = self._serve(json.dumps(LEDGER))
        self.assertEqual(200, st, "the path the board fetches is not served")

    @unittest.skipIf(NODE is None, "node is absent — the board half is UNMEASURED, not passing")
    def test_an_unreadable_ledger_is_unknown_on_both_sides(self):
        _st, d = self._serve("{ this is not json")
        self.assertIs(False, d.get("ok"), "an unreadable ledger answered ok: %r" % d)
        self.assertIsNone(d.get("locked"), "an unreadable ledger published an EMPTY lock list — 'nothing is his gear'")
        o = self._board(d, ["Gore Rider"])
        self.assertFalse(o["applied"])
        self.assertIsNone(o["main"], "the board stored an answer nobody could give")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 W4 - the console stops serving the MAIN ledger to the board",
        "file": "control_app.py",
        "find": "        if path == \"/api/main_locks\":\n",
        "replace": "        if path == \"/api/main_locks_gone\":\n",
        "matches": 1,
    },
    {
        "why": "#246 W4 - the board reads a key the console never sends, so no published lock ever lands",
        "file": "bible.html",
        "find": "  if (!d || d.ok !== true || !Array.isArray(d.locked)) return false;\n",
        "replace": "  if (!d || d.ok !== true || !Array.isArray(d.lockedRows)) return false;\n",
        "matches": 1,
    },
    {
        "why": "#246 W4 - the ledger's answer publishes nothing it locks",
        "file": "main_character.py",
        "find": "    return {\"ok\": True, \"locked\": [dict(row) for row in r[\"locked\"]], \"tracked\": r[\"tracked\"],\n",
        "replace": "    return {\"ok\": True, \"locked\": [], \"tracked\": r[\"tracked\"],\n",
        "matches": 1,
    },
]
