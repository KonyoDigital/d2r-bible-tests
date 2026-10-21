# -*- coding: utf-8 -*-
"""R4 (REG-2341) - TWO PROVERS NEVER TEAR OR THIN A STORE.

FOUND in the v1 writers (read 2026-10-21): heart2's verdict cache and red memory each wrote through ONE fixed tmp name
with no cross-process lock, while a worktree's pre-flight runs beside main's push - two writers on one file. Driven here with REAL processes and threads; the overlap is
made certain by TV_STORE_HOLD_S (a law's seam: a writer holds its written tmp unreplaced, so the other writer is provably
inside the same window - never a race left to luck):

  1. two processes, released together by a barrier, writing the verdict cache: every write of both survives (the store
     directory's lock);
  2. with NO lock to be had (a machine without flock), two writers inside the window at once each install their own
     bytes - a tmp named for one writer is never moved by the other's rename;
  3. a tmp a DEAD writer left beside a store is swept, a live writer's never, and nothing beside a guard is touched;
  4. an old-code writer (a copy of the v1 flush body: fixed tmp, no lock, {_why, entries} only) writes the file it always
     wrote, and the v2 store - with a section that writer would strip - is never reached.
EVERYTHING HERE IS A FIXTURE: throwaway directories, stores named like heart2's. Nothing of his is read or written.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

HOLD = "1.0"          # seconds a writer holds its written tmp before the rename: both writers are inside the window

_WRITER = r'''
import json, os, sys, time
sys.path.insert(0, sys.argv[1])
kind, path, key, go = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
import heart2 as H
open(go + "." + key + ".ready", "w").close()
while not os.path.exists(go):          # the barrier: both writers start the same instant
    time.sleep(0.01)
now = int(time.time() * 1000)
if kind == "cache":
    c = H._VerdictCache(path=path, say=lambda *a, **k: None)
    c.store(key, {"verdict": "PROVEN", "provedAt": now, "gate": key, "proof": 0})
    ok = c.flush()
print(json.dumps({"key": key, "ok": bool(ok)}))
'''


def _quiet(*a, **k):
    pass


class _Env(object):
    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *_e):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def _entries(path):
    with io.open(path, encoding="utf-8") as fh:
        body = json.load(fh)
    return body.get("entries") if isinstance(body, dict) else None


class TwoProversNeverTearTheStore(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="h2tear.")
        self.addCleanup(shutil.rmtree, self.root, True)

    def _pair(self, kind, path):
        """Two REAL processes write one store, released together, each holding its tmp for HOLD s. -> their reports"""
        script = os.path.join(self.root, "writer.py")
        with io.open(script, "w", encoding="utf-8") as fh:
            fh.write(_WRITER)
        go = os.path.join(self.root, "go-%s" % kind)
        env = dict(os.environ, TV_STORE_HOLD_S=HOLD)
        env.pop("HEART2_CACHE_PATH", None)
        env.pop("HEART2_RED_PATH", None)
        procs = [subprocess.Popen([sys.executable, script, HERE, kind, path, "%s%s" % (kind, n), go], env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                 for n in ("A", "B")]
        deadline = time.time() + 60
        while time.time() < deadline and not all(os.path.exists("%s.%s%s.ready" % (go, kind, n)) for n in ("A", "B")):
            time.sleep(0.02)            # both are imported and waiting at the barrier
        with io.open(go, "w", encoding="utf-8") as fh:
            fh.write("go")
        out = []
        for p in procs:
            o, e = p.communicate(timeout=60)
            self.assertEqual(p.returncode, 0, "a writer crashed: %s" % e[-600:])
            out.append(json.loads(o.strip().splitlines()[-1]))
        return out

    def test_two_processes_writing_at_once_both_survive_in_every_store(self):
        """★ the cache: two writers inside one window, every write kept (the lock)"""
        jobs = [("cache", os.path.join(self.root, "c", ".heart2_cache.json"))]
        for _k, p in jobs:
            os.makedirs(os.path.dirname(p))
        reports = {}

        def run(kind, path):
            reports[kind] = self._pair(kind, path)

        threads = [threading.Thread(target=run, args=job) for job in jobs]
        for t in threads:
            t.start()
        for t in threads:
            t.join(120)
        for kind, path in jobs:
            self.assertEqual(sorted(r["ok"] for r in reports.get(kind) or []), [True, True],
                             "%s: a writer did not finish its write: %s" % (kind, reports.get(kind)))
            ent = _entries(path)
            self.assertIsInstance(ent, dict, "%s: the store does not parse after two writers" % kind)
            self.assertEqual(sorted(ent), ["%sA" % kind, "%sB" % kind],
                             "%s: one writer erased the other's write - the store is unlocked: %s" % (kind, sorted(ent)))

    def test_with_no_lock_two_writers_never_move_each_others_bytes(self):
        """★ a machine with no flock: two writers inside the window at once - each tmp is its own, so each rename installs
        its own bytes and neither finds its tmp gone"""
        path = os.path.join(self.root, ".heart2_cache.json")
        got = {}

        def write(tag):
            body = {"format": 2, "entries": {tag: {"verdict": H.PROVEN, "provedAt": 1}}}
            got[tag] = H._StoreFile(path, _quiet).commit(lambda disk: body)

        real = H._fcntl
        H._fcntl = None
        try:
            with _Env(TV_STORE_HOLD_S="0.6"):
                a = threading.Thread(target=write, args=("A",))
                a.start()
                time.sleep(0.2)          # A has written its tmp and is holding it
                b = threading.Thread(target=write, args=("B",))
                b.start()
                a.join(30)
                b.join(30)
        finally:
            H._fcntl = real
        self.assertEqual(got.get("A"), (True, None), "the first writer failed: %s" % (got,))
        self.assertEqual(got.get("B"), (True, None), "the second writer's tmp was moved by the first writer's rename - "
                                                     "one tmp name shared by two writers: %s" % (got,))
        self.assertEqual(sorted(_entries(path)), ["B"], "the store holds neither writer's own bytes")
        self.assertEqual([n for n in os.listdir(self.root) if n.endswith(".tmp")], [], "a tmp outlived its write")

    def test_a_dead_writers_tmp_is_swept_and_a_live_ones_is_kept(self):
        """★ R9 - a tmp left by a writer whose pid no longer runs leaves when the store opens; this process's stays; a tmp
        named beside a guard is never touched"""
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        path = os.path.join(self.root, ".heart2_cache.json")
        names = {"dead": ".heart2_cache.json.%d.7.tmp" % dead.pid, "dead_prev": ".heart2_cache.json.%d.7.tmp.prev" % dead.pid,
                 "live": ".heart2_cache.json.%d.7.tmp" % os.getpid(), "guard": "control_app.py.%d.7.tmp" % dead.pid}
        for n in names.values():
            with io.open(os.path.join(self.root, n), "w", encoding="utf-8") as fh:
                fh.write("x")
        H._VerdictCache(path=path, say=_quiet)
        H._StoreFile(os.path.join(self.root, "control_app.py"), _quiet).sweep()
        left = set(os.listdir(self.root))
        self.assertNotIn(names["dead"], left, "a dead writer's tmp was left beside the store")
        self.assertNotIn(names["dead_prev"], left, "a dead writer's .prev link was left beside the store")
        self.assertIn(names["live"], left, "a LIVE writer's tmp was swept")
        self.assertIn(names["guard"], left, "a file beside a guard was swept")

    def test_an_old_code_writer_never_reaches_the_new_store(self):
        """★ (critic) the code that ran before REG-2341 flushes {_why, entries} through a fixed tmp with no lock - into the
        file IT always resolved (main's tv/). The v2 store lives elsewhere, so a section that writer would strip survives"""
        main = os.path.join(self.root, "main")
        wt = os.path.join(self.root, "wt")
        gd = os.path.join(main, ".git", "worktrees", "wt")
        for d in (os.path.join(main, "tv"), gd, os.path.join(wt, "tv")):
            os.makedirs(d)
        with io.open(os.path.join(gd, "commondir"), "w", encoding="utf-8") as fh:
            fh.write("../..\n")
        with io.open(os.path.join(wt, ".git"), "w", encoding="utf-8") as fh:
            fh.write("gitdir: %s\n" % gd)
        v2 = H._shared_cache_path(here=os.path.join(wt, "tv"), repo=wt, env={})
        v1 = os.path.join(main, "tv", ".heart2_cache.json")      # what the pre-REG-2341 rule resolved, from either tree
        self.assertNotEqual(os.path.realpath(v2), os.path.realpath(v1), "the v2 store IS the file old code writes")
        os.makedirs(os.path.dirname(v2))
        with io.open(v2, "w", encoding="utf-8") as fh:
            json.dump({"format": 2, "pushes": [{"forecast": 1}],
                       "entries": {"k2": {"verdict": H.PROVEN, "provedAt": 2}}}, fh)

        def v1_flush(path, mine):                      # a copy of the v1 flush body, as old code still runs it
            disk = {}
            if os.path.exists(path):
                with io.open(path, encoding="utf-8") as fh:
                    disk = json.load(fh).get("entries") or {}
            for k, v in disk.items():
                if k not in mine and isinstance(v, dict) and v.get("verdict") == H.PROVEN:
                    mine[k] = v
            with io.open(path + ".tmp", "w", encoding="utf-8") as fh:
                json.dump({"_why": "v1", "entries": mine}, fh, sort_keys=True)
            os.replace(path + ".tmp", path)

        v1_flush(v1, {"k1": {"verdict": H.PROVEN, "provedAt": 1}})
        with io.open(v2, encoding="utf-8") as fh:
            body = json.load(fh)
        self.assertEqual(body.get("pushes"), [{"forecast": 1}], "an old-code flush stripped the v2 store's sections")
        self.assertEqual(sorted(body.get("entries") or {}), ["k2"], "an old-code flush reached the v2 store")
        self.assertEqual(body.get("format"), 2)


RED_PROOF = [
    {"why": "R4 - the store directory is not locked: two writers inside one window, and one write is lost",
     "file": "heart2.py",
     "find": "            fd = os.open(folder, os.O_RDONLY)\n            _fcntl.flock(fd, _fcntl.LOCK_EX)\n",
     "replace": "            fd = os.open(folder, os.O_RDONLY)\n",
     "matches": 1},
    {"why": "R4 - one fixed tmp name for every writer: with no lock, the first rename moves the second writer's bytes",
     "file": "heart2.py",
     "find": "        return \"%s.%d.%d.tmp\" % (self.path, os.getpid(), threading.get_ident())\n",
     "replace": "        return self.path + \".tmp\"\n",
     "matches": 1},
    {"why": "R9 - a dead writer's tmp is never swept, and a 320 MB leftover rides beside the store for good",
     "file": "heart2.py",
     "find": "        self.file.sweep()                # R9 - a tmp a dead writer left beside the store\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "(critic) the v2 store is the file old code writes, so an old flush strips its sections",
     "file": "heart2.py",
     "find": "        return os.path.join(common, \"heart2\"), None\n",
     "replace": "        return os.path.join(os.path.dirname(common), \"tv\"), None\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
