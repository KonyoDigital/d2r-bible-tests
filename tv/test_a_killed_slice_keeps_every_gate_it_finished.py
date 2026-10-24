# -*- coding: utf-8 -*-
"""REG-2435 (#186 g) - A KILLED CENSUS KEEPS EVERY GATE IT FINISHED; ONLY THE GATE IN FLIGHT IS OWED AGAIN.

MEASURED 2026-10-22 on his Mac: a census slice stopped at 13:59 lost the 7 small gates it had already finished - a
slice banked through _slice_banker at most once per SLICE_BANK_EVERY_S=60, only when a gate ended, so every gate that
finished inside that minute was lost when the next (long) gate was killed; a FULL census installed no banker at all and
wrote once at its end; and heart2's own signal handler os._exit()s. His self-prover's slices die the same way when the
Mac sleeps or the console relaunches for an update. Now every finished gate is banked into tv/.heart2.json the moment it
ends (a slice and a full run alike), from facts read once per run, under the census file's lock - and its PROVENs are in
the verdict cache before the gate is reported done.

Driven END TO END: the REAL heart2.py (this tree's own bytes, copied) run as its own CLI process over a throwaway repo of
three fixture gates, with its stores pointed at this law's files (HEART2_CACHE_PATH / HEART2_RED_PATH /
HEART2_PUSHES_PATH) and its temp dir inside this law's scratch; the third gate's clean run signals that it is in flight
and is SIGKILLed - the prover's whole process group, no handler runs:
  1. a full census: gates 1 and 2 are in the census with the digests of their files, gate 3 is owed; the verdict cache
     holds the two finished gates' proofs and nothing of gate 3's;
  2. a slice (--slice), the same.
RED_PROOF below.
"""
import hashlib
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

#: the prover and the modules it runs with, copied by NAME from this tree (a proof that tampers heart2.py here is the
#: heart2.py the fixture runs)
_PROVER_FILES = ("heart2.py", "safe_copy.py", "lane_ports.py", "console_safe.py", "law_widths.py", "prove_record.py",
                 "gate_ledger.py",   # REG-2633 era: a proof key asks the stamp rule in gate_ledger
                 os.path.join("gate_trace", "sitecustomize.py"))

_RUN_GATES = r'''
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))


class Gate(object):
    def __init__(self, name, argv, timeout=60, needs_app=False, why=""):
        self.name, self.argv, self.timeout, self.needs_app, self.why = name, argv, timeout, needs_app, why


GATES = [Gate("g%d" % i, [sys.executable, os.path.join(HERE, "g%d.py" % i)], 60) for i in (1, 2, 3)]


def git_free_env(base=None, **extra):
    env = dict((k, v) for k, v in (os.environ if base is None else base).items() if not str(k).upper().startswith("GIT_"))
    env.update(extra)
    return env


def law_env(needs_app, base=None):
    return git_free_env(base)


def needs_app_of(filename):
    return False
'''

_GATE_SRC = r'''
import io, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
RED_PROOF = [{"why": "the subject of gate %(n)d breaks", "file": "s%(n)d.txt", "find": "fine", "replace": "BROKEN",
              "matches": 1}]


class T(unittest.TestCase):
    def test_subject(self):
        with io.open(os.path.join(HERE, "s%(n)d.txt"), encoding="utf-8") as fh:
            self.assertNotIn("BROKEN", fh.read())


if __name__ == "__main__":
    mark = os.environ.get("KILLED_SLICE_MARK") if %(n)d == 3 else None
    if mark:
        with io.open(mark, "w", encoding="utf-8") as fh:
            fh.write("gate 3 is in flight")
        import time
        time.sleep(120)
    unittest.main()
'''


def _sha16(path):
    """The census's own per-gate digest (heart2.gate_shas): sha256 of the file read as text, 16 hex."""
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        return hashlib.sha256(fh.read().encode("utf-8", "replace")).hexdigest()[:16]


class AKilledCensusKeepsWhatItFinished(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="killed_slice_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.repo = os.path.join(self.d, "repo")
        self.tv = os.path.join(self.repo, "tv")
        os.makedirs(os.path.join(self.tv, "gate_trace"))
        for rel in _PROVER_FILES:
            shutil.copy2(os.path.join(HERE, rel), os.path.join(self.tv, rel))
        files = {"run_gates.py": _RUN_GATES, "control_app.py": "# sandbox marker\n"}
        for n in (1, 2, 3):
            files["g%d.py" % n] = _GATE_SRC % {"n": n}
            files["s%d.txt" % n] = "all fine here\n"
        for name, text in files.items():
            with io.open(os.path.join(self.tv, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        self.stores = os.path.join(self.d, "stores")
        self.tmp = os.path.join(self.d, "tmp")
        os.makedirs(self.stores)
        os.makedirs(self.tmp)
        self.mark = os.path.join(self.d, "in_flight.mark")
        self.cache = os.path.join(self.stores, ".heart2_cache.json")

    def census_killed_in_gate_3(self, *flags):
        env = dict((k, v) for k, v in os.environ.items() if not k.upper().startswith(("GIT_", "HEART2_")))
        env.update(HEART2_PROVE_WORKERS="1", HEART2_CACHE_PATH=self.cache,
                   HEART2_RED_PATH=os.path.join(self.stores, ".heart2_red.json"),
                   HEART2_PUSHES_PATH=os.path.join(self.stores, "heart2_pushes.jsonl"), HEART2_AUDIT_K="0",
                   KILLED_SLICE_MARK=self.mark, TMPDIR=self.tmp, TEMP=self.tmp, TMP=self.tmp, PYTHONUNBUFFERED="1",
                   PYTHONDONTWRITEBYTECODE="1")
        log = os.path.join(self.d, "prover.log")
        with io.open(log, "wb") as out:
            p = subprocess.Popen([sys.executable, os.path.join(self.tv, "heart2.py"), "--prove", "g1", "g2", "g3"]
                                 + list(flags), cwd=self.tv, env=env, stdout=out, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        try:
            deadline = time.time() + 240
            while not os.path.exists(self.mark) and p.poll() is None and time.time() < deadline:
                time.sleep(0.2)
            self.assertTrue(os.path.exists(self.mark), "PREMISE: gate 3 never started (the prover %s): %s"
                            % ("exited %s" % p.returncode if p.poll() is not None else "timed out", self.tail(log)))
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)         # the prover and every law it runs: no handler, no finally
            except OSError:
                pass
            p.wait()
        return self.tail(log)

    def tail(self, log):
        try:
            with io.open(log, encoding="utf-8", errors="replace") as fh:
                return "\n".join(fh.read().splitlines()[-30:])
        except OSError:
            return "(no log)"

    def census_file(self):
        with io.open(os.path.join(self.tv, ".heart2.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def banked_gates(self):
        if not os.path.exists(self.cache):
            return set()
        with io.open(self.cache, encoding="utf-8") as fh:
            return set(e.get("gate") for e in json.load(fh)["entries"].values() if e.get("verdict") == "PROVEN")

    def assertKeptTheFinishedGates(self, said):
        self.assertTrue(os.path.exists(os.path.join(self.tv, ".heart2.json")),
                        "a killed census left NO census at all - every gate it finished is owed again:\n%s" % said)
        st = self.census_file()
        shas = st.get("gateShas") or {}
        for g in ("g1", "g2"):
            self.assertEqual(shas.get(g), _sha16(os.path.join(self.tv, g + ".py")),
                             "%s finished before the kill and is not in the census against its file (gateShas %s):\n%s"
                             % (g, shas, said))
            self.assertIn(g, st.get("provedGates") or [], "%s finished PROVEN and the census lost it" % g)
        self.assertNotIn("g3", shas, "the gate IN FLIGHT was banked as proved against its file - it was never judged")
        self.assertNotIn("g3", st.get("provedGates") or [], "the gate in flight was banked PROVEN")
        self.assertEqual(self.banked_gates(), {"g1", "g2"},
                         "the verdict cache does not hold exactly the finished gates' proofs:\n%s" % said)

    def test_a_full_census_killed_in_gate_3_keeps_gates_1_and_2(self):
        said = self.census_killed_in_gate_3()
        self.assertKeptTheFinishedGates(said)

    def test_a_slice_killed_in_gate_3_keeps_gates_1_and_2(self):
        said = self.census_killed_in_gate_3("--slice")
        self.assertKeptTheFinishedGates(said)


RED_PROOF = [
    {"why": "REG-2435 - the 60 s throttle is back: a gate that finished inside the minute before a kill is lost",
     "file": "heart2.py",
     "find": "SLICE_BANK_EVERY_S = 0\n",
     "replace": "SLICE_BANK_EVERY_S = 60\n",
     "matches": 1},
    {"why": "REG-2435 - a full census installs no banker and writes once at its end: a kill loses every gate it proved",
     "file": "heart2.py",
     "find": "        _GATE_HOOK[\"fn\"] = _slice_banker(_blank, say, measured=",
     "replace": "        _GATE_HOOK[\"fn\"] = None if stamp else _slice_banker(_blank, say, measured=",
     "matches": 1},
    {"why": "REG-2435 - the gate IN FLIGHT is banked before it is judged: a kill leaves it proved against its file",
     "file": "heart2.py",
     "find": "            holding = [(name, proofs)]\n",
     "replace": "            holding = [(name, proofs)]\n            with lock:\n                out[name] = (PROVEN, [PROVEN] * "
                "len(proofs))\n            _GATE_HOOK[\"fn\"] and _GATE_HOOK[\"fn\"](out, lock)\n",
     "matches": 1},
    {"why": "REG-2435 - the census's gate PROVENs reach the cache only at the run's end: a kill loses them all",
     "file": "heart2.py",
     "find": "        run.cache.flush()          # what this gate proved reaches the disk before the gate is reported done\n",
     "replace": "        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
