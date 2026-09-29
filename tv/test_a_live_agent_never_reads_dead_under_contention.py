# -*- coding: utf-8 -*-
"""#78 — A LIVE AGENT NEVER READS DEAD BECAUSE A LOCK WAS BUSY.

MEASURED 2026-09-29 in the v3523 pre-flight: test_button_matrix's SIM agent was up ("bridge up", "agent ping") and six
seconds later read DEAD ("reads grow or bridge stays: reads=0") - only under load, never alone (18 s green). The status
read asks `_agent_alive()`, which trusts the child handle only when it gets `_lock` quickly; otherwise it asks
`_pid_cached()`, whose 10 s port-scan cache could hold a None scanned while the agent was still booting. Nothing told
the cache the agent had started, so a live agent was 'off' until the cache aged out - the v872 "STANDBY keeps
jumping at me" shape, on his screen under game load.

DRIVEN: `_lock` held by another thread, a stale None planted in the cache, the real `_agent_alive()` asked. And every
place the console sets `_agent_proc` must tell the cache (parsed with ast, never grepped). RED_PROOF below.
"""
import ast
import os
import sys
import threading
import time
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
_fx_tmp.contain()
import control_app as ca  # noqa: E402


class _Live(object):
    pid = 424242

    def poll(self):
        return None


class _Held(object):
    """Hold the console's _lock from another thread for the life of the block - the contention, reproduced."""

    def __enter__(self):
        self.got, self.go = threading.Event(), threading.Event()

        def hold():
            with ca._lock:
                self.got.set()
                self.go.wait(10)
        self.t = threading.Thread(target=hold, daemon=True)
        self.t.start()
        assert self.got.wait(5), "PREMISE: could not take the console's lock"
        return self

    def __exit__(self, *a):
        self.go.set()
        self.t.join(5)


class ALiveAgentReadsAlive(unittest.TestCase):

    def setUp(self):
        self.saved = (ca._agent_proc, dict(ca._PID_CACHE))
        ca._agent_proc = _Live()

    def tearDown(self):
        ca._agent_proc = self.saved[0]
        ca._PID_CACHE.clear()
        ca._PID_CACHE.update(self.saved[1])

    def test_the_premise_a_stale_none_under_contention_reads_dead(self):
        ca._PID_CACHE.update(pid=None, ts=time.time())
        with mock.patch.object(ca, "_port_listener_pid", lambda port=None: None), _Held():
            self.assertFalse(ca._agent_alive(), "PREMISE: the stale-None shape no longer reads dead - re-measure")

    def test_a_started_agent_tells_the_cache_and_reads_alive_under_contention(self):
        ca._PID_CACHE.update(pid=None, ts=time.time())
        ca._pid_cache_seed(_Live.pid)
        with mock.patch.object(ca, "_port_listener_pid", lambda port=None: None), _Held():
            self.assertTrue(ca._agent_alive(), "a live agent read DEAD because the lock was busy")

    def test_a_stopped_agent_makes_the_next_read_look_again(self):
        ca._PID_CACHE.update(pid=_Live.pid, ts=time.time())
        ca._pid_cache_seed(None)
        looked = []
        with mock.patch.object(ca, "_port_listener_pid", lambda port=None: looked.append(1)), _Held():
            ca._pid_cached()
        self.assertEqual([1], looked, "after a stop the cache kept answering for the old agent")


def _is_agent_assign(st):
    return isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_agent_proc" for t in st.targets)


def _seed_call(st):
    """-> the _pid_cache_seed Call when `st` is one, else None"""
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Name) \
            and st.value.func.id == "_pid_cache_seed":
        return st.value
    return None


def _blocks(tree):
    """Every statement list inside a function or class. The module body is skipped by name: its one
    `_agent_proc = None` is the initializer, run while the cache is itself still at its (None, 0) start."""
    for n in ast.walk(tree):
        if isinstance(n, ast.Module):
            continue
        for field in ("body", "orelse", "finalbody"):
            b = getattr(n, field, None)
            if isinstance(b, list) and b and isinstance(b[0], ast.stmt):
                yield b


class EveryPlaceThatSetsTheAgentTellsTheCache(unittest.TestCase):
    """Per BLOCK, not per function: the spawn's own function also seeds on its failure path, and a per-function check
    stayed GREEN with the spawn's seed removed (measured when this law was written)."""

    def test_every_assignment_is_followed_by_a_seed_in_its_own_block(self):
        tree = ast.parse(open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        sites, silent = 0, []
        for block in _blocks(tree):
            for i, st in enumerate(block):
                if not _is_agent_assign(st):
                    continue
                sites += 1
                seeds = [c for c in (_seed_call(x) for x in block[i + 1:]) if c is not None]
                spawn = isinstance(st.value, ast.Call)
                ok = bool(seeds) and (not spawn or any(
                    isinstance(a, ast.Attribute) and isinstance(a.value, ast.Name) and a.value.id == "_agent_proc"
                    and a.attr == "pid" for c in seeds for a in c.args))
                if not ok:
                    silent.append("line %d (%s)" % (st.lineno, "spawn" if spawn else "clear"))
        self.assertGreaterEqual(sites, 4, "PREMISE: the console sets _agent_proc in fewer places than it did")
        self.assertEqual([], silent, "these set _agent_proc and never tell the cache: %s" % silent)


RED_PROOF = [
    {
        "why": "2026-09-29 - a started agent never tells the cache; under load it reads DEAD for up to 10 s",
        "file": "tv/control_app.py",
        "find": "            _agent_proc = subprocess.Popen(**popen_kw)\n            _pid_cache_seed(_agent_proc.pid)\n",
        "replace": "            _agent_proc = subprocess.Popen(**popen_kw)\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the seed does nothing, so the stale None stands",
        "file": "tv/control_app.py",
        "find": "    _PID_CACHE[\"pid\"] = int(pid) if pid else None\n    _PID_CACHE[\"ts\"] = time.time() if pid else 0.0\n",
        "replace": "    return None\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - the stop path forgets to tell the cache",
        "file": "tv/control_app.py",
        "find": "        _agent_mode = \"off\"\n        _pid_cache_seed(None)\n    _stop_inflight = False",
        "replace": "        _agent_mode = \"off\"\n    _stop_inflight = False",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
