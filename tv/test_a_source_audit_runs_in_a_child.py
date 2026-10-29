# -*- coding: utf-8 -*-
"""#172 PHASE B - A CONSOLE NEVER PARSES ITS OWN SOURCE IN ITS OWN HEAP; A SHORT-LIVED CHILD DOES, AND THE MEMORY LEAVES.

MEASURED 2026-10-27: the console's ~1 GB of data-driven memory was its own source being parsed - the route census
(chronicle_routes.routes(): ~1,400 files, 939k ast objects) and the lane spans (health_engine._lane_spans(): the 49k-line
control_app.py, 930k objects). Freed ast arenas stay resident (vmmap: 1.2 GB MALLOC_LARGE on his Mac 55 s after a start;
the ALT kept 1.28 GB private on 7.9 GB). A console now sends each cold derivation to tv/audit_child.py, reads the cache the
child wrote, and derives in its own process only when the child failed - recorded, never read as clean.

Driven on the real modules in a fixture world (TV_HIST is a temp dir, so both caches live there, never in his tree):
  - a console derives both with ZERO ast.parse calls in its own process, and the answers equal an in-process derivation;
  - a second ask spawns nothing (a cache hit);
  - a child that fails leaves the console to derive itself, and the state says so;
  - a stale lane cache (another stat of control_app.py) is never served;
  - a law (no console mark) spawns nothing and derives exactly as before.

REG-2733 (measured 2026-10-28): the routes child FAILED every time it ran - 3 of 3 on his Mac, 2 of 2 on the ALT, "the
routes were derived but their cache was not written". The three route keys (chronicle, fleet, roster) stamped every
*_roster.json in tv/, including the HIDDEN per-PC ledgers the live console rewrites all the time (.char_roster.json,
.tvd_roster.json) - files _routes_on_disk() has skipped since REG-1954 - so the key moved under the child's derivation.
Reproduced: touching .tvd_roster.json 4 s into a child made it exit 3. And on the ALT (Python 3.12) the reason was buried
under a SyntaxWarning from stderr; the child's own sentence now leads.

REG-3102 (measured 2026-10-29): RED_PROOF[6] below - wanted() saying yes everywhere - turned into a chain. Each child's own
_lane_spans() found no cache and spawned the next: a level every ~0.19 s at ~72 MB each, nothing derived until the 180 s
timeout. A hosted runner proving this law ran out of memory twice (publish 40812615686, proof shard 7, ~2 min into that
proof). The spawn itself now refuses inside a child, so that proof still goes red through the law with at most one child.
RED_PROOF below.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
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
_fx_tmp.contain()                       # first: the world below, and every child's scratch, leave with this run
_WORLD = tempfile.mkdtemp(prefix="audit_child_world_")
os.environ["TV_HIST"] = _WORLD          # before anything resolves a cache root
import audit_child as AC  # noqa: E402
import chronicle_routes as CR  # noqa: E402
import frame_ref as FR  # noqa: E402
import health_engine as HE  # noqa: E402
import control_app as CA  # noqa: E402
import roster_routes as RTR  # noqa: E402
import fleet_routes as FTR  # noqa: E402

_REAL_PARSE = ast.parse
_EXPECT = {}


def _cold():
    """Both caches forgotten - the memo and the disk copy - and the child state cleared, as a fresh console start."""
    CR.cache_reset()
    HE.__dict__["_LANE_SPAN_CACHE"] = {}      # _lane_spans rebinds this module global, so it is replaced, not cleared
    p = HE._lane_spans_cache_path()
    if p and os.path.exists(p):
        os.remove(p)
    AC.STATE.clear()


def _counted(fn):
    calls = {"n": 0}

    def parse(*a, **k):
        calls["n"] += 1
        return _REAL_PARSE(*a, **k)
    with mock.patch.object(ast, "parse", parse):
        out = fn()
    return out, calls["n"]


def _expected():
    """The same two answers derived the old way, in this process, with no console mark."""
    if not _EXPECT:
        FR.mark_console_path(False)
        _cold()
        d = CA.chronicle_route_state()
        _EXPECT["routes"] = (d.get("ok"), d.get("counts"), len(d.get("routes") or []))
        _EXPECT["spans"] = dict(HE._lane_spans()[0])
        _cold()
    return _EXPECT


class ASourceAuditRunsInAChild(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert CR._CACHE_PATH.startswith(os.path.realpath(_WORLD)) or CR._CACHE_PATH.startswith(_WORLD), \
            "PREMISE: the route cache is not inside the fixture world: %s" % CR._CACHE_PATH
        _expected()

    def tearDown(self):
        FR.mark_console_path(False)

    def test_a_console_parses_nothing_in_its_own_heap(self):
        exp = _expected()
        _cold()
        FR.mark_console_path(True)
        (d, spans), n = _counted(lambda: (CA.chronicle_route_state(), dict(HE._lane_spans()[0])))
        self.assertEqual(n, 0, "the console ast.parsed its own source %d time(s) in its own heap" % n)
        st = AC.status()["audits"]
        self.assertEqual((st["routes"]["runs"], st["routes"]["lastOk"]), (1, True), st["routes"])
        self.assertEqual((st["lane_spans"]["runs"], st["lane_spans"]["lastOk"]), (1, True), st["lane_spans"])
        self.assertEqual((d.get("ok"), d.get("counts"), len(d.get("routes") or [])), exp["routes"],
                         "the child's route census is not the one this process derives")
        self.assertEqual(spans, exp["spans"], "the child's lane spans are not the ones this process derives")
        # a second ask is a cache hit: nothing is spawned
        CR._MEMO["key"] = None
        HE.__dict__["_LANE_SPAN_CACHE"] = {}
        CA.chronicle_route_state()
        HE._lane_spans()
        st = AC.status()["audits"]
        self.assertEqual((st["routes"]["runs"], st["lane_spans"]["runs"]), (1, 1), "a warm cache spawned a child: %r" % st)
        self.assertEqual((st["routes"]["hits"], st["lane_spans"]["hits"]), (1, 1), st)

    def test_a_failed_child_fails_open_and_says_so(self):
        exp = _expected()
        _cold()
        FR.mark_console_path(True)

        def _boom(*a, **k):
            raise subprocess.TimeoutExpired(a[0] if a else "x", AC.TIMEOUT_S)
        with mock.patch.object(AC.subprocess, "run", _boom):
            (d, spans), n = _counted(lambda: (CA.chronicle_route_state(), dict(HE._lane_spans()[0])))
        self.assertGreater(n, 0, "PREMISE: with the child gone the console did not derive at all")
        self.assertEqual((d.get("ok"), d.get("counts"), len(d.get("routes") or [])), exp["routes"])
        self.assertEqual(spans, exp["spans"])
        st = AC.status()["audits"]
        for name in ("routes", "lane_spans"):
            self.assertIs(st[name]["lastOk"], False, "a failed child was recorded as fine: %r" % st[name])
            self.assertIn("derived it itself", st[name]["say"])
            self.assertEqual(st[name]["fails"], 1)

    def test_a_stale_lane_cache_is_never_served(self):
        exp = _expected()
        _cold()
        p = HE._lane_spans_cache_path()
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"key": [1, 1], "val": {"_not_a_lane": ["tvd-ghost", 1, 2]}}, fh)
        FR.mark_console_path(True)
        spans = dict(HE._lane_spans()[0])
        self.assertNotIn("_not_a_lane", spans, "a lane cache for another control_app.py was served")
        self.assertEqual(spans, exp["spans"])

    def test_a_law_never_spawns(self):
        _cold()
        FR.mark_console_path(False)
        self.assertFalse(AC.wanted())
        with mock.patch.object(AC.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("spawned"))):
            (d, spans), n = _counted(lambda: (CA.chronicle_route_state(), dict(HE._lane_spans()[0])))
        self.assertGreater(n, 0, "a law no longer derives in its own process")
        self.assertEqual(AC.status()["audits"]["routes"]["runs"], 0)
        with mock.patch.dict(os.environ, {AC.CHILD_ENV: "1"}):
            FR.mark_console_path(True)
            self.assertFalse(AC.wanted(), "a child would spawn a child")


class AHiddenRosterIsNotAnInput(unittest.TestCase):
    """REG-2733 - each route key, with a private ledger and a shipped roster planted in its listing (patched, never a
    file in tv/): the private one moving leaves the key still; the shipped one moving moves it (so the key can tell)."""

    def _key(self, mod, hidden_mtime, shown_mtime):
        real_listdir, real_mtime = os.listdir, os.path.getmtime
        here = os.path.realpath(mod.HERE)

        def listdir(path):
            names = list(real_listdir(path))
            if os.path.realpath(path) == here:
                names += [".char_roster.json", "zz_shipped_roster.json"]
            return names

        def getmtime(path):
            b = os.path.basename(path)
            if b == ".char_roster.json":
                return hidden_mtime
            if b == "zz_shipped_roster.json":
                return shown_mtime
            return real_mtime(path)
        with mock.patch.object(os, "listdir", listdir), mock.patch.object(os.path, "getmtime", getmtime):
            return mod._source_key()

    def test_a_private_ledger_moving_leaves_every_route_key_still(self):
        for mod in (CR, RTR, FTR):
            a = self._key(mod, 4.0e9 + 5, 4.0e9)
            b = self._key(mod, 4.0e9 + 10, 4.0e9)
            self.assertIsNotNone(a, "PREMISE: %s could not key at all" % mod.__name__)
            self.assertEqual(a, b, "%s's key moved when only a hidden per-PC ledger was rewritten" % mod.__name__)

    def test_a_shipped_roster_moving_still_moves_every_route_key(self):
        for mod in (CR, RTR, FTR):
            self.assertNotEqual(self._key(mod, 1.0, 4.0e9), self._key(mod, 1.0, 4.0e9 + 1),
                                "%s's key no longer sees a shipped roster change" % mod.__name__)


class TheChildsOwnReasonLeads(unittest.TestCase):

    def tearDown(self):
        AC.STATE.clear()

    def test_its_sentence_beats_a_warning_on_stderr(self):
        class _P(object):
            returncode = 3
            stdout = "the routes were derived but their cache was not written (an unkeyable source?)\n"
            stderr = "<unknown>:61: SyntaxWarning: invalid escape sequence '\\s'\n"
        ok, why = AC.run("routes", _spawn=lambda *a, **k: _P())
        self.assertFalse(ok)
        self.assertIn("cache was not written", why, "the child's own reason was buried: %r" % why)
        self.assertNotIn("SyntaxWarning", why)

    def test_a_crash_with_nothing_on_stdout_still_names_its_error(self):
        class _P(object):
            returncode = 1
            stdout = ""
            stderr = "Traceback (most recent call last):\nMemoryError\n"
        self.assertIn("MemoryError", AC.run("routes", _spawn=lambda *a, **k: _P())[1])


class AChildNeverSpawnsAChild(unittest.TestCase):
    """REG-3102 - the spawn ITSELF refuses inside a child, so a wanted() that says yes can never grow a chain."""

    class _P(object):
        returncode, stdout, stderr = 0, "{}", ""

    def tearDown(self):
        AC.STATE.clear()

    def test_a_child_asked_to_spawn_derives_itself(self):
        spawned = []
        with mock.patch.dict(os.environ, {AC.CHILD_ENV: "1"}):
            for name in AC.AUDITS:
                ok, why = AC.run(name, _spawn=lambda *a, **k: spawned.append(a) or self._P())
                self.assertFalse(ok, "a child reported a spawn of %s as done: %r" % (name, why))
                self.assertIn("never spawns a child", why)
        self.assertEqual(spawned, [], "a child spawned a child - each level would spawn the next (REG-3102)")

    def test_without_the_marker_the_spawn_still_happens(self):
        # BASELINE: the same call with no marker reaches the spawn, so the refusal above is the marker's doing
        spawned = []
        with mock.patch.dict(os.environ, {}):
            os.environ.pop(AC.CHILD_ENV, None)
            ok, why = AC.run("routes", _spawn=lambda *a, **k: spawned.append(a) or self._P())
        self.assertEqual(len(spawned), 1, "PREMISE: a console's run() no longer reaches the spawn: %r" % why)
        self.assertTrue(ok, why)


RED_PROOF = [
    {"why": "REG-2733 - the chronicle route key stamps the hidden per-PC ledgers again (the child never caches)",
     "file": "tv/chronicle_routes.py",
     "find": "            if p.endswith(\"_roster.json\") and not p.startswith(\".\"):\n",
     "replace": "            if p.endswith(\"_roster.json\"):\n",
     "matches": 1},
    {"why": "REG-2733 - the fleet route key stamps the hidden per-PC ledgers again",
     "file": "tv/fleet_routes.py",
     "find": "            if p.endswith(\"_roster.json\") and not p.startswith(\".\"):\n",
     "replace": "            if p.endswith(\"_roster.json\"):\n",
     "matches": 1},
    {"why": "REG-2733 - the roster route key stamps the hidden per-PC ledgers again",
     "file": "tv/roster_routes.py",
     "find": "            if p.endswith(\".py\") or (p.endswith(\"_roster.json\") and not p.startswith(\".\")):\n",
     "replace": "            if p.endswith(\".py\") or p.endswith(\"_roster.json\"):\n",
     "matches": 1},
    {"why": "REG-2733 - a warning on stderr stands in for the child's own reason again",
     "file": "tv/audit_child.py",
     "find": "        _said = ((p.stdout or \"\").strip().splitlines() or (p.stderr or \"\").strip().splitlines() or [\"-\"])[-1][:160]\n",
     "replace": "        _said = ((p.stderr or p.stdout or \"\").strip().splitlines() or [\"-\"])[-1][:160]\n",
     "matches": 1},
    {"why": "#172 phase B - the console derives the cold route census in its own heap again",
     "file": "tv/control_app.py",
     "find": "                _ac.run(\"routes\")\n",
     "replace": "                pass\n",
     "matches": 1},
    {"why": "#172 phase B - the console parses control_app.py for the lane spans in its own heap again",
     "file": "tv/health_engine.py",
     "find": "        if _ac.wanted():\n            _got = _lane_spans_disk(_key)\n",
     "replace": "        if False:\n            _got = _lane_spans_disk(_key)\n",
     "matches": 1},
    {"why": "#172 phase B - wanted() says yes in every process, a law included (a child is still held at run(), REG-3102)",
     "file": "tv/audit_child.py",
     "find": "    if os.environ.get(CHILD_ENV) == \"1\":\n        return False\n",
     "replace": "    return True\n",
     "matches": 1},
    {"why": "#172 phase B - a failed child is recorded as fine",
     "file": "tv/audit_child.py",
     "find": "    r[\"lastOk\"] = ok\n",
     "replace": "    r[\"lastOk\"] = True\n",
     "matches": 1},
    {"why": "#172 phase B - a lane cache for another stat of control_app.py is served",
     "file": "tv/health_engine.py",
     "find": "        if blob.get(\"key\") != [int(key[0]), int(key[1])] or not isinstance(blob.get(\"val\"), dict):\n",
     "replace": "        if not isinstance(blob.get(\"val\"), dict):\n",
     "matches": 1},
    {"why": "REG-3102 - a child asked to spawn spawns again (with wanted() wrong too, each level spawns the next)",
     "file": "tv/audit_child.py",
     "find": "    if os.environ.get(CHILD_ENV) == \"1\":\n        return False, \"a child never spawns a child",
     "replace": "    if False:\n        return False, \"a child never spawns a child",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
