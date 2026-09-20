#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3381 — A READ FROM A SUBPROCESS HAS A DEADLINE, OR IT IS NOT A READ, IT IS A WAIT.

THE SECOND WEDGE IN ONE SESSION, AND THE SAME CLASS AS THE FIRST.

v3380 fixed a browser launch that hung because subprocess.run's timeout path could not reach the
renderer grandchildren holding its stdout pipe. The very next gate run hung AGAIN, in a different
place, for the same underlying reason:

    tv/control_app.py 7668, 10572, 10603:   line = wp.stdout.readline()

A bare readline on a subprocess pipe has no deadline. If `ocr_mac --worker` never emits a line,
the reader waits for ever.

MEASURED 2026-09-20, during the pre-push gate:
  * test_control worker pid 23192 held cumulative CPU FLAT at 3:19.05 -> 3:19.06 -> 3:19.13 ->
    3:19.25 across several minutes - it burned essentially no CPU at all;
  * its child `ocr_mac --worker` (pid 24974) was alive 3:46 having used 0:00.99 - idle too;
  * the hook then reported: "test_control HUNG - killed after 1500s on an IDLE machine
    (load 2.34). Push blocked."

Load 2.34. The machine was doing nothing. For the second time the 1500s bound took the blame for
a hang it did not cause, and for the second time the bound was innocent - six completed runs on
this tree measure 507-564s against it, a 2.66x margin.

⚠ THE CURE ALREADY EXISTED, ONE FILE AWAY. tv/tv_diablo.py OcrWorker.read() speaks the SAME
stdin-path/stdout-JSON protocol to the SAME binary, and it is bounded: a pump thread feeding a
queue, a MONOTONIC deadline, and q.get(timeout=...). control_app.py carried its own copy of that
protocol with none of it. One twin safe, the other not. [[copy-drift]] [[the-unjoined-end]]

⚠ AND MY OWN SWEEP WAS TOO NARROW. After v3380 I swept the class as "browser launches" and as
"lsof calls" and found neither of these three. The class is neither of those things: it is A READ
FROM A SUBPROCESS WITH NO DEADLINE. Both wedges are instances. The heart row is widened to that
class in the same version, because a row that only knows about browsers would have watched this
one hang without a word.

WHAT THIS FILE PINS - behaviour first:
  * a worker that never answers cannot hold the reader past its deadline
  * a worker that exits returns promptly rather than waiting for a line that will never come
  * a worker that DOES answer still returns its parsed payload (the baseline that lets the
    timeout case discriminate)
  * no bare wp.stdout.readline() returns to control_app's code
"""

import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

import control_app as CA

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _code_only(src):
    """Code with comments AND every docstring gone.

    ⚠⚠ A DOCSTRING IS NOT A COMMENT, and stripping "#" does not touch one. This distinction has
    now produced FOUR separate false readings in a single session - including this very law,
    whose first run reported a surviving bare readline that was its own explanatory prose. A
    string blanked here keeps its LINE COUNT so any line number derived from the result still
    points at the right place. [[source-reading-guard]] section 4b
    """
    no_comments = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
    try:
        tree = ast.parse(src)
    except Exception:
        return no_comments
    lines = no_comments.split("\n")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not (isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant)
                and isinstance(first.value.value, str)):
            continue
        a = first.lineno - 1
        b = (getattr(first, "end_lineno", None) or first.lineno)
        for i in range(a, min(b, len(lines))):
            lines[i] = ""          # blank, not deleted — line numbers must survive
    return "\n".join(lines)


def _fn_code(name):
    tree = ast.parse(SRC)
    lines = SRC.split("\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            end = getattr(node, "end_lineno", None) or node.lineno
            start = node.lineno
            b = node.body
            if b and isinstance(b[0], ast.Expr) and \
               isinstance(getattr(b[0], "value", None), ast.Constant) and \
               isinstance(b[0].value.value, str):
                start = (getattr(b[0], "end_lineno", None) or b[0].lineno)
            seg = "\n".join(lines[start:end]) if start >= node.lineno else \
                  "\n".join(lines[node.lineno - 1:end])
            return _code_only(seg)
    return None


# A worker that accepts a path and NEVER answers. This is `ocr_mac --worker` reduced to the one
# behaviour that matters, and it reproduces the hang without needing the real binary.
DEAF_WORKER = textwrap.dedent(
    """
    import sys, time
    for _ in sys.stdin:
        time.sleep(600)
    """
)

ECHO_WORKER = textwrap.dedent(
    """
    import sys, json
    for line in sys.stdin:
        sys.stdout.write(json.dumps({"lines": ["ok"], "got": line.strip()}) + "\\n")
        sys.stdout.flush()
    """
)

# ⚠ v3391 — A WORKER THAT NEVER READS ITS INPUT AT ALL. The deaf worker above still DRAINS
# stdin (`for _ in sys.stdin`) and merely fails to answer, so it exercises the READ bound only.
# This one never touches stdin, so the pipe fills and the WRITE blocks — the half v3381 left
# unbounded and the half that wedged the gate three times.
DEAF_TO_STDIN = textwrap.dedent(
    """
    import time
    time.sleep(600)
    """
)

DYING_WORKER = textwrap.dedent(
    """
    import sys
    sys.stdin.readline()
    sys.exit(0)
    """
)


def _spawn(script):
    fh = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    fh.write(script)
    fh.close()
    p = subprocess.Popen([sys.executable, fh.name],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         text=True, bufsize=1)
    return p, fh.name


class AWorkerReadHasADeadline(unittest.TestCase):

    def _cleanup(self, p, path):
        try:
            p.kill()
        except Exception:
            pass
        try:
            os.unlink(path)
        except Exception:
            pass

    # ---------- behaviour ----------

    def test_a_worker_that_never_answers_cannot_hold_the_reader(self):
        """THE WHOLE POINT. A bare readline waits for ever here; this must come back."""
        p, path = _spawn(DEAF_WORKER)
        self.addCleanup(self._cleanup, p, path)
        t0 = time.monotonic()
        got = self._ask_bounded(p, "/nonexistent/frame.png", timeout=2.0, wait=20.0)
        elapsed = time.monotonic() - t0
        self.assertEqual(got, {}, "a silent worker must yield {}, never a fabricated reading")
        self.assertLess(elapsed, 30.0,
                        "did not return within 30s - this is the hang that blocked the push "
                        "(measured %.1fs)" % elapsed)


    def _ask_bounded(self, p, path, timeout, wait):
        """Call _ocr_ask on a thread and REFUSE to inherit its hang.

        ⚠ A law about deadlines must not be able to hang. Called directly, a sabotaged (unbounded)
        _ocr_ask blocks for ever: the case would HANG rather than fail, and heart2's 180s per-proof
        bound would report "timed out" instead of RED — a decisive proof degraded into a timeout,
        and the bound blamed for it. That is this file's own subject, one level up.
        """
        import threading as _th
        box = {}

        def _run():
            try:
                box["r"] = CA._ocr_ask(p, path, timeout=timeout)
            except Exception as e:          # a raise is an answer; a hang is not
                box["e"] = e

        t = _th.Thread(target=_run, daemon=True)
        t.start()
        t.join(wait)
        if t.is_alive():
            self.fail("_ocr_ask did not return within %.1fs against a %.1fs deadline - the call "
                      "is UNBOUNDED and this is the wedge that refused three pushes" % (wait, timeout))
        if "e" in box:
            raise box["e"]
        return box.get("r")

    def test_a_worker_that_never_reads_its_input_cannot_hold_the_writer(self):
        """v3391 — THE OTHER HALF OF THE TRANSACTION, and the one that actually wedged the gate.

        v3381 bounded the read and left `wp.stdin.write(path); flush()` unbounded, with the
        deadline computed AFTER it. A blocking write does not raise, so the try/except around it
        could never fire. MEASURED on an idle reaped machine: test_control wedged with CPU flat
        at 2:59.02 -> 2:59.03 over 25s, ONE child (ocr_mac alive and idle) and two pipes held;
        the gate then refused the push with "HUNG - killed after 1500s on an IDLE machine".

        ⚠ THE PATH IS DELIBERATELY LARGER THAN THE PIPE BUFFER (measured at 16,384 bytes by lsof
        on the wedged process). A short path fits in the buffer and returns even when nobody is
        reading, so a small fixture would pass against the UNBOUNDED code and prove nothing.
        [[regression-guard]] section 5
        """
        p, path = _spawn(DEAF_TO_STDIN)
        self.addCleanup(self._cleanup, p, path)
        big = "x" * 200000
        t0 = time.monotonic()
        got = self._ask_bounded(p, big, timeout=2.0, wait=25.0)
        elapsed = time.monotonic() - t0
        self.assertEqual(got, {}, "a worker that never reads must yield {}, never a reading")
        self.assertLess(elapsed, 30.0,
                        "the WRITE held the caller %.1fs past a 2s deadline - this is the wedge "
                        "that refused three pushes" % elapsed)

    def test_a_poisoned_worker_is_not_reused(self):
        """An abandoned writer thread can still complete later and push a stale path into the
        pipe, desyncing every following request from its reply. A wrong ANSWER is worse than no
        answer, so a worker whose write timed out is never asked again."""
        p, path = _spawn(DEAF_TO_STDIN)
        self.addCleanup(self._cleanup, p, path)
        self._ask_bounded(p, "x" * 200000, timeout=1.0, wait=25.0)
        self.assertTrue(getattr(p, "_ocr_dead", False),
                        "the worker was not marked dead, so the next call may read a reply that "
                        "belongs to the abandoned write")
        t0 = time.monotonic()
        self.assertEqual(self._ask_bounded(p, "/small.png", timeout=5.0, wait=25.0), {})
        self.assertLess(time.monotonic() - t0, 1.0,
                        "a poisoned worker was asked again and cost another wait")

    def test_a_worker_that_answers_still_returns_its_payload(self):
        """BASELINE. Without this, a helper that always returned {} would pass the case above."""
        p, path = _spawn(ECHO_WORKER)
        self.addCleanup(self._cleanup, p, path)
        got = CA._ocr_ask(p, "/some/frame.png", timeout=15.0)
        self.assertIsInstance(got, dict)
        self.assertEqual(got.get("lines"), ["ok"],
                         "a healthy worker's payload must still arrive: %r" % (got,))
        self.assertEqual(got.get("got"), "/some/frame.png",
                         "the path must actually reach the worker")

    def test_a_worker_that_exits_returns_rather_than_waiting_for_a_line(self):
        """EOF is a value. Without the sentinel the reader waits out its whole deadline on a
        process that is already gone, which is how a fast failure becomes a slow one."""
        p, path = _spawn(DYING_WORKER)
        self.addCleanup(self._cleanup, p, path)
        t0 = time.monotonic()
        got = CA._ocr_ask(p, "/some/frame.png", timeout=20.0)
        elapsed = time.monotonic() - t0
        self.assertEqual(got, {})
        self.assertLess(elapsed, 15.0,
                        "waited %.1fs for a worker that had already exited - EOF is not being "
                        "turned into a value" % elapsed)

    def test_a_dead_handle_is_answered_not_crashed(self):
        """None must be survivable: the callers reach here on paths where the worker never spawned."""
        self.assertEqual(CA._ocr_ask(None, "/x.png", timeout=1.0), {})

    # ---------- structure ----------

    def test_the_deadline_is_monotonic(self):
        """A wall-clock deadline can be extended by an NTP step mid-wait. [[stale-reading]]"""
        code = _fn_code("_ocr_ask")
        self.assertTrue(code, "_ocr_ask is gone")
        self.assertIn("monotonic", code, "the deadline is not monotonic")

    def test_the_queue_read_is_bounded(self):
        code = _fn_code("_ocr_ask")
        self.assertIn("timeout=", code,
                      "the queue read carries no timeout, which is the defect itself")

    def test_eof_is_turned_into_a_value(self):
        code = _fn_code("_ocr_ask")
        self.assertIn("put(None)", code,
                      "the pump never signals EOF, so a dead worker is indistinguishable from a "
                      "slow one")

    def test_no_bare_readline_returns_to_control_app(self):
        """The regression this file exists to prevent, asked of the CODE and not of the prose."""
        code = _code_only(SRC)
        n = code.count("wp.stdout.readline()")
        self.assertEqual(n, 0,
                         "%d bare wp.stdout.readline() call(s) are back in control_app - each one "
                         "can wait for ever and will be reported as a 1500s timeout" % n)

    def test_every_worker_ask_goes_through_the_bounded_helper(self):
        """A helper nobody calls is documentation. [[the-unjoined-end]]"""
        code = _code_only(SRC)
        self.assertGreaterEqual(code.count("_ocr_ask(wp,"), 3,
                                "the three call sites no longer all route through the bounded "
                                "helper")


    def test_this_law_cannot_hang_on_its_own_deaf_fixture(self):
        """A LAW ABOUT DEADLINES MUST NOT BE ABLE TO HANG.

        MEASURED TWICE on 2026-09-20. Cases that questioned a never-answering worker through the
        raw helper turned heart2's per-proof bound INTO the verdict: first 3 proofs, then 2, came
        back UNPROVABLE - "tampered run: timed out after 180s" - instead of RED. The sabotages
        were decisive every time; the instrument simply could not say so, and the bound took the
        blame for its own subject one level up. [[feedback-suspect-the-instrument]]

        Two distinct sabotages land here and BOTH become infinite waits: dropping the queue
        timeout, and computing the deadline on the wall clock while the loop still compares a
        monotonic one (epoch 1.7e9 against uptime - a deadline ~57 years out).

        So any case that spawns a worker which cannot answer goes through the bounded wrapper,
        which fails in seconds rather than inheriting the hang.
        """
        with io.open(__file__, encoding="utf-8") as _fh:
            own = _code_only(_fh.read())
        offenders = []
        for chunk in own.split("\n    def ")[1:]:
            name = chunk.split("(", 1)[0].strip()
            if not name.startswith("test_"):
                continue
            if name == "test_this_law_cannot_hang_on_its_own_deaf_fixture":
                continue          # this law must NAME the shapes it bans, so it matches itself
            if "DEAF_WORKER" not in chunk and "DEAF_TO_STDIN" not in chunk:
                continue
            if "CA._ocr_ask(" in chunk:
                offenders.append(name)
        self.assertEqual(offenders, [],
                         "these cases spawn a worker that cannot answer AND ask it directly, so "
                         "a sabotaged run hangs instead of failing and every red-proof on this "
                         "file degrades into a 180s timeout: %s" % (offenders,))


RED_PROOF = [
    {
        "why": "v3381 bounded the READ and left the WRITE unbounded with the deadline computed "
               "after it; restoring that is the exact wedge that refused three pushes",
        "file": "tv/control_app.py",
        "find": "        _th.Thread(target=_send, args=(wp, _sent), daemon=True, name=\"ocr-send\").start()\n"
                "        if _sent.get(timeout=max(0.05, deadline - _tm.monotonic())) is not True:\n"
                "            return {}",
        "replace": "        wp.stdin.write(path + \"\\n\")\n"
                   "        wp.stdin.flush()",
        "matches": 1,
    },
    {
        "why": "without poisoning, an abandoned writer can later push a stale path into the pipe "
               "and every following reply belongs to the wrong request",
        "file": "tv/control_app.py",
        "find": "    if getattr(wp, \"_ocr_dead\", False):\n        return {}",
        "replace": "    if False:\n        return {}",
        "matches": 1,
    },
    {
        "why": "the queue timeout IS the deadline; without it the reader waits for ever and the "
               "deaf-worker case must go red",
        "file": "tv/control_app.py",
        "find": "            ln = q.get(timeout=max(0.05, deadline - _tm.monotonic()))",
        "replace": "            ln = q.get()",
        "matches": 1,
    },
    {
        "why": "without the EOF sentinel a worker that has already exited still costs the caller "
               "its entire deadline, so the dying-worker case must go red",
        "file": "tv/control_app.py",
        "find": "            qq.put(None)",
        "replace": "            pass",
        "matches": 1,
    },
    {
        "why": "restoring a bare readline at a real call site is the exact regression; the code "
               "law must catch it",
        "file": "tv/control_app.py",
        "find": "                        j = _ocr_ask(wp, fp)",
        "replace": "                        wp.stdin.write(fp + \"\\n\"); wp.stdin.flush()\n"
                   "                        line = wp.stdout.readline()\n"
                   "                        j = json.loads(line) if line else {}",
        "matches": 1,
    },
    {
        "why": "a wall-clock deadline can be extended by an NTP step mid-wait, which is how a "
               "bounded wait silently becomes an unbounded one",
        "file": "tv/control_app.py",
        "find": "    deadline = _tm.monotonic() + timeout",
        "replace": "    deadline = _tm.time() + timeout",
        "matches": 1,
    },
    {
        "why": "a case that questions a never-answering worker directly cannot fail - it HANGS, "
               "and every red-proof on this file degrades into a 180s timeout (measured twice, "
               "2026-09-20)",
        "file": "tv/test_a_worker_read_has_a_deadline.py",
        "find": '        t0 = time.monotonic()\n        got = self._ask_bounded(p, "/nonexistent/frame.png", timeout=2.0, wait=20.0)',
        "replace": '        t0 = time.monotonic()\n        got = CA._ocr_ask(p, "/nonexistent/frame.png", timeout=2.0)',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
