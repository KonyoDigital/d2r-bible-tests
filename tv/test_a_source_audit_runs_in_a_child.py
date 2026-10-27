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
_WORLD = tempfile.mkdtemp(prefix="audit_child_world_")
os.environ["TV_HIST"] = _WORLD          # before anything resolves a cache root
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import audit_child as AC  # noqa: E402
import chronicle_routes as CR  # noqa: E402
import frame_ref as FR  # noqa: E402
import health_engine as HE  # noqa: E402
import control_app as CA  # noqa: E402

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


RED_PROOF = [
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
    {"why": "#172 phase B - every process spawns, a law and a child included",
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
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
