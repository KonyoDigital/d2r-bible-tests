# -*- coding: utf-8 -*-
"""R8 (#150, REG-2437) - A LONG GATE CHECKPOINTS ITS PROOFS: A KILL KEEPS ALL BUT THE LAST STRETCH, NEVER A WRONG ONE.

His order, 2026-10-21: "heart proofs also need memory registered so they pull and fetch, same for interrupted process".
A gate's PROVENs wait for its closing clean run (REG-1988) and are banked only then, so a hard kill - the hook's deadline,
Ctrl-C, the Mac sleeping - lost every proof of the gate in flight (war_stash: 29 proofs x ~70 s in ONE gate). Now, past a
time threshold since the gate's last green clean run (HEART2_CHECKPOINT_S here, a law's seam: 0 = after every proof that
is not the last), the closing run is asked over the proofs since the last checkpoint: green banks and flushes them NOW
and seals them; red makes that batch and every unrun proof UNPROVABLE and stops the gate.

Driven through the REAL heart2 - its own CLI process for the kill, the REAL _prove_push / _prove_gates / lanes / gate
loops / _checkpoint / _closing_clean / _prove_one / _run_gate in-process for the rest - over a fixture law whose tampered
run can leave its sandbox drifted (CK_DRIFT_ON) or block (CK_KILL_ON); the verdict cache is this law's own file:
  1. SIGKILL right after "checkpoint banked": the banked prefix is in the store; the next run serves it and proves only
     the rest;
  2. a RED checkpoint banks nothing of its batch, every unrun proof is UNPROVABLE (never NOT RUN), the gate stops;
  3. a green checkpoint, then a red closing run: the sealed prefix stays PROVEN and banked, only the rest is UNPROVABLE -
     census and push alike;
  4. a push stopped by another lane's failure (fail fast) banks the bracketed prefix it proved before the stop.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

#: the fixture law. Catches.test_catch reddens on any "BROKEN"; Clean.test_not_drifted reddens once a tampered run has
#: left its sandbox drifted (CK_DRIFT_ON names the tamper that does). CK_KILL_ON + CK_KILL_MARK: that tampered run says it
#: is in flight and blocks (for the kill). CK_SLOW_S: every tampered run takes that long.
_LAW = r'''
import io, os, sys, time, unittest
here = os.path.dirname(os.path.abspath(__file__))
SUBJECT = os.path.join(here, "sub" + "ject.txt")
FLAG = os.path.join(here, "drift" + "ed.flag")


def _subject():
    with io.open(SUBJECT, encoding="utf-8") as fh:
        return fh.read()


class Catches(unittest.TestCase):
    def test_catch(self):
        self.assertNotIn("BROKEN", _subject())


class Clean(unittest.TestCase):
    def test_not_drifted(self):
        self.assertFalse(os.path.exists(FLAG), "an earlier run left this sandbox drifted")


if __name__ == "__main__":
    s = _subject()
    if os.environ.get("CK_DRIFT_ON") and os.environ["CK_DRIFT_ON"] in s:
        with io.open(FLAG, "w", encoding="utf-8") as fh:
            fh.write("drifted")
    if os.environ.get("CK_KILL_MARK") and os.environ.get("CK_KILL_ON") and os.environ["CK_KILL_ON"] in s:
        with io.open(os.environ["CK_KILL_MARK"], "w", encoding="utf-8") as fh:
            fh.write("in flight")
        time.sleep(120)
    if os.environ.get("CK_SLOW_S") and "BROKEN" in s:
        time.sleep(float(os.environ["CK_SLOW_S"]))
    unittest.main()
'''
_GATE, _FILE = "checkpoint-fixture", "t_checkpoint_law.py"
PROOFS = [{"why": "p%d" % i, "file": "subject.txt", "find": w, "replace": "BROKEN%d" % i, "matches": 1}
          for i, w in enumerate(("alpha", "beta", "gamma"))]
SUBJECT = "alpha beta gamma\n"

_RUN_GATES = r'''
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))


class Gate(object):
    def __init__(self, name, argv, timeout=60, needs_app=False, why=""):
        self.name, self.argv, self.timeout, self.needs_app, self.why = name, argv, timeout, needs_app, why


GATES = [Gate("%s", [sys.executable, os.path.join(HERE, "%s")], 60)]


def git_free_env(base=None, **extra):
    env = dict((k, v) for k, v in (os.environ if base is None else base).items() if not str(k).upper().startswith("GIT_"))
    env.update(extra)
    return env


def law_env(needs_app, base=None):
    return git_free_env(base)


def needs_app_of(filename):
    return False
''' % (_GATE, _FILE)

#: the prover and the modules it runs with, copied by NAME from this tree for the CLI case
_PROVER_FILES = ("heart2.py", "safe_copy.py", "lane_ports.py", "console_safe.py", "law_widths.py", "prove_record.py",
                 "gate_ledger.py",   # REG-2633 era: a proof key asks the stamp rule in gate_ledger
                 os.path.join("gate_trace", "sitecustomize.py"))


def _quiet(*a, **k):
    pass


def _no_facts(have, say):
    return None, dict((n, list(range(len(p)))) for n, _f, p in have), [n for n, _f, _p in have], \
        {"anchor": 0, "entry": 0, "target": 0}


class _Patch(object):
    def __init__(self, **kw):
        self.kw, self.old = kw, {}

    def __enter__(self):
        for k, v in self.kw.items():
            self.old[k] = getattr(H, k)
            setattr(H, k, v)
        return self

    def __exit__(self, *_e):
        for k, v in self.old.items():
            setattr(H, k, v)
        return False


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


class _Case(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="checkpoint_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cache_path = os.path.join(self.d, ".heart2_cache.json")
        e = _Env(HEART2_RED_MEMORY="0", HEART2_PROVE_WORKERS="1", TV_LAW_WIDTHS=None, HEART2_AUDIT_K="0",
                 HEART2_CHECKPOINT_S="0", CK_DRIFT_ON=None, CK_KILL_ON=None, CK_KILL_MARK=None, CK_SLOW_S=None)
        e.__enter__()
        self.addCleanup(e.__exit__)

    def make(self, files=None):
        def _make(say=print):
            root = tempfile.mkdtemp(prefix="ckbox.", dir=self.d)
            repo = os.path.join(root, "repo")
            for rel, text in (files or {"tv/control_app.py": "# sandbox marker\n", "tv/" + _FILE: _LAW,
                                        "tv/subject.txt": SUBJECT}).items():
                p = os.path.join(repo, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with io.open(p, "w", encoding="utf-8") as fh:
                    fh.write(text)
            return os.path.join(repo, "tv"), root
        return _make

    def banked(self, path=None):
        path = path or self.cache_path
        if not os.path.exists(path):
            return []
        with io.open(path, encoding="utf-8") as fh:
            # REG-2440 also banks a traced twin ("t:" key) once gate_ledger rides along; the prefix is the static-keyed set
            return sorted((e.get("gate"), e.get("proof")) for k, e in json.load(fh)["entries"].items()
                          if e.get("verdict") == H.PROVEN and not str(k).startswith("t:"))

    def census(self, have=None):
        said = []
        run = H._CensusRun(cache=H._VerdictCache(path=self.cache_path, say=said.append), red=False)
        with _Patch(make_sandbox=self.make(), _CENSUS=run):
            results, per = H._prove_gates(have or [(_GATE, _FILE, PROOFS)], said.append, workers=1)
        return results, per, said

    def push(self, have=None, workers="1"):
        said, stopped = [], []
        cache = H._VerdictCache(path=self.cache_path, say=said.append)
        with _Env(HEART2_PROVE_WORKERS=workers), _Patch(make_sandbox=self.make(), _push_facts=_no_facts):
            results, per = H._prove_push(have or [(_GATE, _FILE, PROOFS)], said.append, stopped, cache=cache)
        return results, per, stopped, said


class AKillAfterACheckpointKeepsThePrefix(_Case):

    def test_a_sigkill_after_checkpoint_banked_keeps_the_prefix_and_the_next_run_proves_only_the_rest(self):
        repo = os.path.join(self.d, "repo")
        tv = os.path.join(repo, "tv")
        os.makedirs(os.path.join(tv, "gate_trace"))
        for rel in _PROVER_FILES:
            shutil.copy2(os.path.join(HERE, rel), os.path.join(tv, rel))
        law = _LAW + "\nRED_PROOF = %r\n" % (PROOFS,)       # the CLI reads the gate's own declaration
        for name, text in (("run_gates.py", _RUN_GATES), ("control_app.py", "# sandbox marker\n"), (_FILE, law),
                           ("subject.txt", SUBJECT)):
            with io.open(os.path.join(tv, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        tmp = os.path.join(self.d, "tmp")
        os.makedirs(tmp)
        mark = os.path.join(self.d, "in_flight.mark")
        env = dict((k, v) for k, v in os.environ.items() if not k.upper().startswith(("GIT_", "HEART2_", "CK_")))
        env.update(HEART2_PROVE_WORKERS="1", HEART2_CACHE_PATH=self.cache_path,
                   HEART2_RED_PATH=os.path.join(self.d, ".heart2_red.json"), HEART2_RED_MEMORY="0",
                   HEART2_PUSHES_PATH=os.path.join(self.d, "heart2_pushes.jsonl"), HEART2_AUDIT_K="0",
                   HEART2_CHECKPOINT_S="0", TMPDIR=tmp, TEMP=tmp, TMP=tmp, PYTHONUNBUFFERED="1",
                   PYTHONDONTWRITEBYTECODE="1")
        log = os.path.join(self.d, "prover.log")

        def run(extra):
            with io.open(log, "wb") as out:
                return subprocess.Popen([sys.executable, os.path.join(tv, "heart2.py"), "--prove", _GATE, "--slice"],
                                        cwd=tv, env=dict(env, **extra), stdout=out, stderr=subprocess.STDOUT,
                                        start_new_session=True)

        def said():
            with io.open(log, encoding="utf-8", errors="replace") as fh:
                return fh.read()
        p = run({"CK_KILL_ON": "BROKEN2", "CK_KILL_MARK": mark})
        try:
            deadline = time.time() + 240
            while not os.path.exists(mark) and p.poll() is None and time.time() < deadline:
                time.sleep(0.2)
            self.assertTrue(os.path.exists(mark), "PREMISE: proof 2 never ran:\n%s" % said()[-3000:])
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)          # no handler runs, no finally: only what is on disk survives
            except OSError:
                pass
            p.wait()
        first = said()
        self.assertIn("(checkpoint banked)", first, "PREMISE: no checkpoint was taken:\n%s" % first[-3000:])
        self.assertEqual(self.banked(), [(_GATE, 0), (_GATE, 1)],
                         "a kill after 'checkpoint banked' did not keep the banked prefix in the store:\n%s"
                         % first[-3000:])
        p = run({})
        p.wait(timeout=240)
        second = said()
        for i in (0, 1):
            self.assertIn("%s[%d]" % (_GATE, i), second)
            self.assertTrue(any(("%s[%d]" % (_GATE, i)) in l and "PROVEN (cached by census" in l
                                for l in second.splitlines()),
                            "the next run re-proved the checkpointed proof [%d]:\n%s" % (i, second[-3000:]))
        self.assertFalse(any(("%s[2]" % _GATE) in l and "cached" in l for l in second.splitlines()),
                         "the proof that was in flight was served - it was never judged:\n%s" % second[-3000:])
        self.assertEqual(self.banked(), [(_GATE, 0), (_GATE, 1), (_GATE, 2)], second[-3000:])


class ACheckpointBanksOnlyWhatAGreenCleanRunBrackets(_Case):

    def test_a_red_checkpoint_banks_nothing_of_its_batch_and_stops_the_gate(self):
        with _Env(CK_DRIFT_ON="BROKEN1"):
            results, per, said = self.census()
        self.assertEqual(per[_GATE], [H.PROVEN, H.UNPROVABLE, H.UNPROVABLE],
                         "a red checkpoint: its batch and every unrun proof are UNPROVABLE:\n%s" % "\n".join(said))
        self.assertEqual(results, {_GATE: H.UNPROVABLE})
        self.assertEqual(self.banked(), [(_GATE, 0)], "a red checkpoint banked its batch:\n%s" % "\n".join(said))
        os.remove(self.cache_path)                       # the push proves from nothing, as the census did
        with _Env(CK_DRIFT_ON="BROKEN1"):
            results, per, stopped, said = self.push()
        self.assertEqual(per[_GATE], [H.PROVEN, H.UNPROVABLE, H.UNPROVABLE],
                         "at push, a red checkpoint's unrun proofs must read UNPROVABLE, never NOT RUN:\n%s"
                         % "\n".join(said))
        self.assertEqual(self.banked(), [(_GATE, 0)], "at push, a red checkpoint banked its batch")

    def test_a_green_checkpoint_then_a_red_closing_run_keeps_only_the_sealed_prefix(self):
        with _Env(CK_DRIFT_ON="BROKEN2"):
            results, per, said = self.census()
        self.assertEqual(per[_GATE], [H.PROVEN, H.PROVEN, H.UNPROVABLE],
                         "the closing run took back proofs a green checkpoint had sealed:\n%s" % "\n".join(said))
        self.assertTrue(any("(checkpoint banked)" in l for l in said), said)
        self.assertEqual(self.banked(), [(_GATE, 0), (_GATE, 1)], "\n".join(said))
        os.remove(self.cache_path)
        with _Env(CK_DRIFT_ON="BROKEN2"):
            results, per, stopped, said = self.push()
        self.assertEqual(per[_GATE], [H.PROVEN, H.PROVEN, H.UNPROVABLE],
                         "at push, the closing run took back proofs a green checkpoint had sealed:\n%s" % "\n".join(said))
        self.assertEqual(self.banked(), [(_GATE, 0), (_GATE, 1)], "\n".join(said))

    def test_a_push_stopped_by_another_lane_banks_its_bracketed_prefix(self):
        """MEASURED, not read: another lane's fail-fast stops the push mid-gate; this gate's proofs judged before the stop
        pass its closing run and are banked - the graceful stop keeps them."""
        blind = [{"why": "blind", "file": "subject.txt", "find": "alpha", "replace": "ALPHA", "matches": 1}]
        with _Env(CK_SLOW_S="2", HEART2_CHECKPOINT_S="3600"):
            results, per, stopped, said = self.push(
                [(_GATE, _FILE, PROOFS), ("checkpoint-blind-fixture", _FILE, blind)], workers="2")
        self.assertTrue(stopped and stopped[0][0] == "checkpoint-blind-fixture",
                        "PREMISE: the blind gate did not stop the push: %s\n%s" % (stopped, "\n".join(said)))
        mine = per[_GATE]
        self.assertIn(None, mine, "PREMISE: the stop came after every proof of the gate ran: %s" % mine)
        done = [(_GATE, i) for i, v in enumerate(mine) if v == H.PROVEN]
        self.assertTrue(done, "PREMISE: no proof of the gate finished before the stop: %s\n%s" % (mine, "\n".join(said)))
        self.assertEqual([b for b in self.banked() if b[0] == _GATE], done,
                         "the graceful stop did not bank the bracketed prefix it proved:\n%s" % "\n".join(said))


RED_PROOF = [
    {"why": "R8 - a checkpoint banks its batch whatever its clean run said: a drifted sandbox's PROVEN is banked",
     "file": "heart2.py",
     "find": "    if outcome in (\"red\", \"unknown\"):                    # CHECKPOINT-RED: nothing of the batch is banked\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "R8 - the census's closing run judges the sealed prefix again: a later drift takes back checkpointed proofs",
     "file": "heart2.py",
     "find": "        per = _closing_clean(name, [None if i in ck[\"sealed\"] else v for i, v in enumerate(got)], say)  # REG-1988\n"
             "        for i in ck[\"sealed\"]:\n",
     "replace": "        per = _closing_clean(name, list(got), say)  # REG-1988\n        for i in ():\n",
     "matches": 1},
    {"why": "R8 - the push's closing run judges the sealed prefix again: a later drift takes back checkpointed proofs",
     "file": "heart2.py",
     "find": "        per = [None if i in ck[\"sealed\"] else v for i, v in enumerate(per)]   # R8 - SEALED-EXCLUDED: its "
             "checkpoint stands\n",
     "replace": "        ck[\"sealed\"] = set()\n",
     "matches": 1},
    {"why": "R8 - a checkpoint banks in memory only: a kill after 'checkpoint banked' loses the whole gate again",
     "file": "heart2.py",
     "find": "        cache.flush()                                    # CHECKPOINT-FLUSH: what a kill after this line keeps\n",
     "replace": "        pass\n",
     "matches": 1},
    {"why": "R8 - a red checkpoint's unrun proofs read NOT RUN at push: a drifted sandbox reads as a fail-fast stop",
     "file": "heart2.py",
     "find": "                    got.setdefault(j, UNPROVABLE)        # never NOT RUN",
     "replace": "                    pass                                 # never NOT RUN",
     "matches": 1},
    {"why": "R8 - no checkpoint is ever taken: a long gate keeps every PROVEN in memory until its end",
     "file": "heart2.py",
     "find": "    if time.time() - t_last < _checkpoint_after_s(runs):\n",
     "replace": "    if True:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
