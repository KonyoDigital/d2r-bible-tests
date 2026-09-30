# -*- coding: utf-8 -*-
"""REG-1640 — THE DOCTOR'S HARNESS ROW MAY NEVER SWAP THE CONSOLE'S THREAD MACHINERY.

MEASURED 2026-10-01 on his Mac: the vault lamp froze and never refreshed again. `_vault_autoread_kick`
sets `_VAULT_AUTOREAD_REFRESH["running"]`, starts a thread, and only that thread clears the flag.
The eagle runs every doctor row INSIDE the console process, and the row "sweep attack reaches its
door" called `sweep_wilson._refused_quiet` there — whose `_guarded` swaps `threading.Thread` for the
WHOLE PROCESS while it calls the sweep door. A kick inside that window got a stand-in whose start()
does nothing: the flag stayed True and the lamp stayed frozen until a restart. Reproduced in a
separate process: swap, kick, restore -> running True forever.

  · DRIVEN, the real row with a real child: in THIS process the sweep door is never called, and
    `threading.Thread` is the real class before, during and after. PREMISE: the child answered.
  · DRIVEN, the row with its child faked: every answer the child can give maps to its row (door
    refused = OK, lock first = UNKNOWN, leaked = MISSING, raised = MISSING, nothing readable,
    unimportable or refused = UNKNOWN, no answer inside the bound = UNKNOWN), the child is bounded,
    and the scratch dir it is handed exists while it runs and is gone afterwards.
  · DRIVEN, the harness side: `sweep_wilson.py --reach-probe <dir>` prints one JSON line, and a
    missing dir is refused rather than probed.
RED_PROOF below. [[the-cure-that-kills-the-patient]] [[heart-first]]
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_ledgers as _fx_ledgers  # noqa: E402  never HIS eagle ledgers
_fx_ledgers.redirect()
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as CD  # noqa: E402
import sweep_wilson as SW  # noqa: E402

_REAL_THREAD = threading.Thread


class _Done(object):
    def __init__(self, stdout, returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, "", returncode


class TheRowAsksAChild(unittest.TestCase):

    def test_the_door_is_never_called_in_the_process_that_runs_the_row(self):
        import control_app as ca
        seen = []
        real_door = ca.chronicle_sweep_start

        def spy(*a, **k):
            seen.append(threading.Thread is _REAL_THREAD)
            return real_door(*a, **k)
        ca.chronicle_sweep_start = spy
        try:
            st, why = CD._check_an_attack_can_still_reach_the_door_it_scores()
        finally:
            ca.chronicle_sweep_start = real_door
        self.assertIs(threading.Thread, _REAL_THREAD, "the row left threading.Thread swapped in this process")
        self.assertEqual(seen, [], "the row called the sweep door INSIDE the process running it - in his console "
                                   "that swaps threading.Thread under every lane (thread real during the calls: %s)"
                                   % seen)
        self.assertIn(st, (CD.OK, CD.UNKNOWN, CD.MISSING))
        for dead in ("would not start", "did not answer", "nothing readable", "would not import"):
            self.assertNotIn(dead, why, "PREMISE: the child did not really answer, so this proves nothing: %s" % why)

    def test_a_thread_started_while_the_row_runs_really_runs(self):
        """the vault lamp's own shape: a flag set, a thread started, only the thread clears the flag.

        ⚠ The door is made SLOW (0.5 s) in this process, so if the row ever calls it here again the
        swap window is wide enough that the kicker is certain to land in it - measured: at the door's
        real speed the window is milliseconds and this kicker missed it. The flag is POLLED, never
        join()ed, because the stand-in thread has no join()."""
        import time
        import control_app as ca
        ran = []
        stop = []

        def kicker():
            while not stop:
                flag = {"running": True}
                try:
                    t = threading.Thread(target=lambda f=flag: (f.update(running=False), ran.append(1)))
                    t.daemon = True
                    t.start()
                except Exception:
                    ran.append("STUCK")
                    return
                deadline = time.time() + 2.0
                while flag["running"] and time.time() < deadline:
                    time.sleep(0.001)
                if flag["running"]:
                    ran.append("STUCK")
                    return
        real_door = ca.chronicle_sweep_start

        def slow_door(*a, **k):
            time.sleep(0.5)
            return real_door(*a, **k)
        ca.chronicle_sweep_start = slow_door
        k = _REAL_THREAD(target=kicker)
        k.daemon = True
        k.start()
        try:
            CD._check_an_attack_can_still_reach_the_door_it_scores()
        finally:
            ca.chronicle_sweep_start = real_door
            stop.append(1)
            k.join(5.0)
        self.assertNotIn("STUCK", ran, "a thread started while the doctor row ran never ran - its flag is stuck, "
                                       "which is the frozen vault lamp")
        self.assertTrue(ran, "PREMISE: the kicker never started a thread, so this proves nothing")


class TheChildsAnswerIsTheRow(unittest.TestCase):

    def _row(self, answer=None, raises=None, stdout=None):
        calls = []
        real = subprocess.run

        def fake(argv, **kw):
            d = argv[-1]
            calls.append({"argv": list(argv), "kw": kw, "dir_exists": os.path.isdir(d), "dir": d})
            if raises is not None:
                raise raises
            return _Done(stdout if stdout is not None else json.dumps(answer))
        subprocess.run = fake
        try:
            st, why = CD._check_an_attack_can_still_reach_the_door_it_scores()
        finally:
            subprocess.run = real
        self.assertEqual(len(calls), 1, "the row asked the child %d times" % len(calls))
        return st, why, calls[0]

    def test_the_door_refused_is_ok(self):
        st, why, _c = self._row({"reach": True})
        self.assertEqual(st, CD.OK, why)

    def test_the_lock_answered_first_is_unknown(self):
        st, why, _c = self._row({"reach": None})
        self.assertEqual(st, CD.UNKNOWN, why)
        self.assertIn("heart2.py --prove", why)

    def test_a_leak_is_missing(self):
        st, why, _c = self._row({"reach": False})
        self.assertEqual(st, CD.MISSING, why)

    def test_a_raised_attack_is_missing(self):
        st, why, _c = self._row({"raised": "KeyError"})
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("KeyError", why)

    def test_an_unreadable_answer_is_unknown(self):
        for out in ("", "Traceback (most recent call last):\n  boom", "[1, 2]", '{"usage": "x"}'):
            st, why, _c = self._row(stdout=out)
            self.assertEqual(st, CD.UNKNOWN, "%r read as %s: %s" % (out, st, why))

    def test_an_unimportable_console_is_unknown(self):
        st, why, _c = self._row({"unimportable": "SyntaxError"})
        self.assertEqual(st, CD.UNKNOWN, why)

    def test_no_answer_inside_the_bound_is_unknown(self):
        st, why, _c = self._row(raises=subprocess.TimeoutExpired(["x"], CD.REACH_PROBE_S))
        self.assertEqual(st, CD.UNKNOWN, why)
        self.assertIn("did not answer", why)

    def test_the_child_is_bounded_and_asked_the_one_question(self):
        _st, _why, c = self._row({"reach": True})
        self.assertIn("--reach-probe", c["argv"])
        self.assertTrue(c["argv"][1].endswith("sweep_wilson.py"), c["argv"])
        t = c["kw"].get("timeout")
        self.assertTrue(isinstance(t, (int, float)) and 0 < t <= 120,
                        "the child is unbounded (timeout=%r) - a hung child would hang the eagle's tick" % (t,))

    def test_the_scratch_dir_exists_while_the_child_runs_and_is_gone_after(self):
        for kw in ({"answer": {"reach": True}}, {"raises": subprocess.TimeoutExpired(["x"], 1)}):
            _st, _why, c = self._row(**kw)
            self.assertTrue(c["dir_exists"], "the child was handed a dir that did not exist")
            self.assertFalse(os.path.exists(c["dir"]), "the row left its scratch dir behind (%s) after %s"
                             % (c["dir"], sorted(kw)))


class TheHarnessAnswersFromItsOwnProcess(unittest.TestCase):

    def test_the_probe_prints_one_json_line(self):
        d = tempfile.mkdtemp(prefix="reachprobe-")
        self.addCleanup(lambda: os.path.isdir(d) and os.rmdir(d))
        r = subprocess.run([sys.executable, os.path.join(HERE, "sweep_wilson.py"), "--reach-probe", d],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, cwd=HERE)
        self.assertEqual(r.returncode, 0, r.stderr[-600:])
        ans = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertIn("reach", ans)
        self.assertIn(ans["reach"], (True, False, None))

    def test_a_missing_dir_is_refused_not_probed(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "sweep_wilson.py"), "--reach-probe",
                            os.path.join(HERE, "no", "such", "dir")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, cwd=HERE)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("reach", json.loads(r.stdout.strip().splitlines()[-1]))


RED_PROOF = [
    {"why": "REG-1640 - the row asks the harness INSIDE the process running it again (the frozen vault lamp)",
     "file": "console_doctor.py",
     "find": "        p = subprocess.run([sys.executable, os.path.join(HERE, \"sweep_wilson.py\"), \"--reach-probe\", d],\n"
             "                           capture_output=True, text=True, encoding=\"utf-8\", errors=\"replace\",\n"
             "                           close_fds=False, timeout=REACH_PROBE_S, cwd=HERE)\n",
     "replace": "        import control_app as _ca\n"
                "        p = type(\"P\", (), {\"returncode\": 0, \"stdout\": json.dumps({\"reach\": _sw.reach_probe(_ca, d)})})()\n",
     "matches": 1},
    {"why": "REG-1640 - the child is unbounded: a hung harness child hangs the eagle's tick",
     "file": "console_doctor.py",
     "find": "                           close_fds=False, timeout=REACH_PROBE_S, cwd=HERE)\n",
     "replace": "                           close_fds=False, cwd=HERE)\n",
     "matches": 1},
    {"why": "REG-1640 - the row stops removing the scratch dir it hands the child (853 heartlane_* once)",
     "file": "console_doctor.py",
     "find": "    finally:\n        _sh.rmtree(d, ignore_errors=True)\n    ans = None\n",
     "replace": "    finally:\n        pass\n    ans = None\n",
     "matches": 1},
    {"why": "REG-1640 - a child that answered nothing readable is read as the lock answering first... as OK",
     "file": "console_doctor.py",
     "find": "    if not isinstance(ans, dict):\n        return UNKNOWN, (\"the sweep harness child answered nothing readable",
     "replace": "    if not isinstance(ans, dict):\n        return OK, (\"the sweep harness child answered nothing readable",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
