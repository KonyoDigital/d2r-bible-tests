# -*- coding: utf-8 -*-
"""REG-1300 — THE EYE'S WARM WORKERS BOUND THEIR WRITES, NOT ONLY THEIR READS.

v3391 found that a pipe WRITE to a worker blocks once the pipe buffer fills, that a blocking write
does not raise, and that control_app._ocr_ask computed its deadline on the line AFTER the write -
so a worker that stopped draining its stdin held the caller for ever. It fixed that one site
(tv/test_a_worker_read_has_a_deadline.py pins it) and left the two twins in tv_diablo.py:

    VisionWorker.ask   self.p.stdin.write(json.dumps(msg) + "\\n"); self.p.stdin.flush()
    OcrWorker.read     self.p.stdin.write(ap + "\\n"); self.p.stdin.flush()

MEASURED 2026-09-25: the "a worker read has a deadline" doctor row read MISSING naming exactly
tv_diablo.py:3614 and :4428, on his Mac console AND on the ALT's. Those two workers carry the
vision lane and the OCR fast lane; a wedge there stops every read with the lane still reporting on.

⚠ The row grades ORDER (a write that precedes its deadline), because order is what a source scan
can see. Moving the `deadline =` line up one would have turned it green and bounded nothing. So
this law drives the SHIPPED classes against a worker that never reads its stdin, with a payload
larger than the pipe buffer (16,384 bytes measured on this Mac - a short one fits and returns even
unbounded, which would prove nothing).

  · DRIVEN: OcrWorker.read and VisionWorker.ask against a stdin-deaf worker return None inside
    their deadline, drop the worker, and the worker process is killed (never reused).
  · DRIVEN baselines: an answering worker still returns its payload through the same path.
  · JOINED: the doctor row that named both lines now reads OK over tv/.
Every call runs on a thread with a join bound: a law about hangs must not be able to hang.
RED_PROOF below.
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import tv_diablo as TD  # noqa: E402
import console_doctor as CD  # noqa: E402

DEAF_TO_STDIN = "import time\ntime.sleep(600)\n"

OCR_ECHO = textwrap.dedent(
    """
    import sys, json
    for line in sys.stdin:
        sys.stdout.write(json.dumps({"lines": ["Shako"], "got": line.strip(), "mode": "ocr"}) + "\\n")
        sys.stdout.flush()
    """
)

VISION_ECHO = textwrap.dedent(
    """
    import sys, json
    for line in sys.stdin:
        sys.stdout.write(json.dumps({"type": "result", "result": "saw it"}) + "\\n")
        sys.stdout.flush()
    """
)

BIG = 200000      # > the 16,384-byte pipe buffer, so an unbounded write really blocks


def _popen(script, test):
    fh = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    fh.write(script)
    fh.close()
    p = subprocess.Popen([sys.executable, fh.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def _clean():
        try:
            p.kill()
        except Exception:
            pass
        try:
            p.wait(timeout=5)
        except Exception:
            pass
        for stream in (p.stdin, p.stdout):
            try:
                if stream:
                    stream.close()
            except Exception:
                pass
        try:
            os.unlink(fh.name)
        except Exception:
            pass
    test.addCleanup(_clean)
    return p


def _wire(worker, p):
    """Hand a live process to a worker the way its own _spawn does: pipe pump into a queue."""
    import queue
    worker.p = p
    worker.q = queue.Queue()

    def _pump(proc, q):
        try:
            for ln in proc.stdout:
                q.put(ln)
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=_pump, args=(p, worker.q), daemon=True).start()


def _bounded(fn, wait):
    box = {}

    def _run():
        try:
            box["r"] = fn()
        except Exception as e:           # a raise is an answer; a hang is not
            box["e"] = e
    t = threading.Thread(target=_run, daemon=True)
    t0 = time.monotonic()
    t.start()
    t.join(wait)
    if t.is_alive():
        raise AssertionError("the call did not return within %.0fs - the write is UNBOUNDED, and "
                             "this is the wedge that stops the whole lane" % wait)
    if "e" in box:
        raise box["e"]
    return box.get("r"), time.monotonic() - t0


def _dies(p, within=5.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < within:
        if p.poll() is not None:
            return True
        time.sleep(0.05)
    return False


class TheOcrWorkerBoundsItsWrite(unittest.TestCase):

    def test_a_stdin_deaf_worker_cannot_hold_the_read(self):
        w = TD.OcrWorker()
        p = _popen(DEAF_TO_STDIN, self)
        _wire(w, p)
        got, took = _bounded(lambda: w.read("/" + "x" * BIG, timeout=1.5), wait=20.0)
        self.assertIsNone(got, "a worker that never read its input produced a reading: %r" % (got,))
        self.assertLess(took, 10.0, "the write held the OCR lane %.1fs past a 1.5s deadline" % took)
        self.assertIsNone(w.p, "a worker whose write never landed is still in use - the abandoned "
                               "write can land later and pair a stale path with the next reply")
        self.assertTrue(_dies(p), "the deaf worker was dropped but left running")

    def test_an_answering_worker_still_reads(self):
        w = TD.OcrWorker()
        _wire(w, _popen(OCR_ECHO, self))
        got, _ = _bounded(lambda: w.read("/some/frame.png", timeout=10.0), wait=20.0)
        self.assertIsInstance(got, dict, "a healthy OCR worker returned nothing")
        self.assertEqual(got.get("lines"), ["Shako"])
        self.assertEqual(got.get("got"), os.path.abspath("/some/frame.png"),
                         "the path did not reach the worker")


class TheVisionWorkerBoundsItsWrite(unittest.TestCase):

    def setUp(self):
        keep = (TD._sub_budget_check, TD._sub_budget_record)
        TD._sub_budget_check = lambda kind="vision": None      # never touch the real budget store
        TD._sub_budget_record = lambda: None

        def _restore():
            TD._sub_budget_check, TD._sub_budget_record = keep
        self.addCleanup(_restore)

    def test_a_stdin_deaf_worker_cannot_hold_the_ask(self):
        w = TD.VisionWorker()
        p = _popen(DEAF_TO_STDIN, self)
        _wire(w, p)
        got, took = _bounded(lambda: w.ask("y" * BIG, timeout=2.0), wait=25.0)
        self.assertIsNone(got, "a worker that never read its prompt produced an answer: %r" % (got,))
        self.assertLess(took, 12.0, "the write held the vision lane %.1fs past a 2s deadline" % took)
        self.assertIsNone(w.p, "a worker whose write never landed is still in use")
        self.assertTrue(_dies(p), "the deaf worker was dropped but left running")

    def test_an_answering_worker_still_answers(self):
        w = TD.VisionWorker()
        _wire(w, _popen(VISION_ECHO, self))
        got, _ = _bounded(lambda: w.ask("what is on screen", timeout=10.0), wait=20.0)
        self.assertEqual(got, "saw it", "a healthy vision worker's answer did not arrive")


class TheDoctorRowAgrees(unittest.TestCase):

    def test_the_row_that_named_both_lines_reads_ok(self):
        st, why = CD._check_a_worker_read_has_a_deadline()
        self.assertEqual(st, CD.OK, "the doctor still names an unbounded worker write: %s" % why)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1300 - the helper waits on the write without the deadline: a stdin-deaf worker "
               "holds the vision and OCR lanes for ever again",
        "file": "tv_diablo.py",
        "find": "        return done.get(timeout=max(0.05, deadline - time.monotonic())) is True\n",
        "replace": "        return done.get() is True\n",
        "matches": 1,
    },
    {
        "why": "REG-1300 - OcrWorker.read writes to the pipe bare again, before and outside its deadline",
        "file": "tv_diablo.py",
        "find": "                if not _pipe_write_by(self.p, ap + \"\\n\", deadline):\n",
        "replace": "                self.p.stdin.write(ap + \"\\n\"); self.p.stdin.flush()\n                if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1300 - VisionWorker.ask writes the prompt bare again, before and outside its deadline",
        "file": "tv_diablo.py",
        "find": "                if not _pipe_write_by(self.p, json.dumps(msg) + \"\\n\", deadline):\n",
        "replace": "                self.p.stdin.write(json.dumps(msg) + \"\\n\"); self.p.stdin.flush()\n                if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1300 - a dropped deaf worker is left running: one leaked child per wedge",
        "file": "tv_diablo.py",
        "find": "    try:\n        p.kill()\n    except Exception:\n        pass\n\n    def _bury(pr):\n",
        "replace": "    try:\n        pass\n    except Exception:\n        pass\n\n    def _bury(pr):\n",
        "matches": 1,
    },
]
