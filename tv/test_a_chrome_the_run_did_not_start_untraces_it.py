# -*- coding: utf-8 -*-
"""REG-2443 (#147 R1) - A CHROME THE RUN DID NOT START UNTRACES IT; ONE IT STARTED IS ATTESTED, NEVER SILENT.

A browser law's Chrome loads pages no audit hook sees. gate_trace wrote U for every non-python child - render_check's
own Chrome included - so every browser gate stayed on the whole-suite static key. And render_check._chrome_up
silently ADOPTED whatever answered on its port (a dead prover's leftover, another run's browser pointed at another
tree), with no word in the trace. Now, only when the run is traced (TV_GATE_TRACE):
  * the Chrome _chrome_up starts carries TV_GATE_TRACE_CDP=1 in its own environment -> gate_trace writes C (not U),
    which gate_ledger.read_trace() reads exactly like U unless its caller passes allow_cdp_chrome=True;
  * a port that already answers -> a U line in the trace before it is adopted ("adopted a Chrome this run did not
    start"); if that line cannot be written the Chrome is not adopted at all;
  * a child started WITHOUT the marker, or one that only inherited it from its parent's own environment -> U;
  * the run's own Chrome, found again on a second call, is not "adopted".
Untraced, _chrome_up is exactly as before (its Chrome inherits the environment).

Driven with a STUB Chrome (TV_CHROME, render_check._find_chrome's override) that answers /json/version on the port it
is given - no browser runs, so this proves on his Mac. The stub is a script with a #! line, so those cases need POSIX;
the untraced case and the reader's own rule run everywhere.
RED_PROOF below.
"""
import io
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import gate_ledger as GL  # noqa: E402

_POSIX = os.name == "posix"
_HAVE_NODE = shutil.which("node") is not None

_STUB = r"""#!%(python)s
import http.server, json, os, sys, threading, time
port = None
for a in sys.argv[1:]:
    if a.startswith("--remote-debugging-port="):
        port = int(a.split("=", 1)[1])
if port is None:
    sys.exit(0)


class Version(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"Browser": "StubChrome/1.0"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", port), Version)
parent = os.getppid()


def watch():
    end = time.time() + 90
    while time.time() < end and os.getppid() == parent:
        time.sleep(0.2)
    os._exit(0)


threading.Thread(target=watch, daemon=True).start()
srv.serve_forever()
"""

# one traced child: _chrome_up as a law's process runs it, then the Chrome it holds is taken down
_UP = (r"import sys; sys.path.insert(0, %(tv)r); import render_check as R" "\n"
       r"print('UP', R._chrome_up())" "\n"
       r"%(again)s"
       r"R._chrome_down()" "\n")


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


def _answers(port):
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=1).read()
        return True
    except Exception:
        return False


class _Stubbed(unittest.TestCase):
    def setUp(self):
        self.box = tempfile.mkdtemp(prefix="cdp-stub.")
        self.addCleanup(shutil.rmtree, self.box, True)
        self.stub = os.path.join(self.box, "chrome_stub")
        with io.open(self.stub, "w", encoding="utf-8") as fh:
            fh.write(_STUB % {"python": sys.executable})
        os.chmod(self.stub, os.stat(self.stub).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.port = _free_port()

    def _traced(self, code, extra=None, allow_cdp=False):
        """Run `code` in a python child under the real hook, rooted at this checkout. -> (proc, facts, why)"""
        trace = GL.trace_path()
        try:
            env = GL.trace_env(dict(os.environ), REPO, trace)
            env.update(TV_CHROME=self.stub, TV_RENDER_PORT=str(self.port))
            env.update(extra or {})
            proc = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=env, capture_output=True, text=True,
                                  timeout=120)
            facts, why = GL.read_trace(trace, allow_cdp_chrome=allow_cdp)
            plain = GL.read_trace(trace)
        finally:
            if os.path.exists(trace):
                os.remove(trace)
        return proc, facts, why, plain

    def _start_stub(self):
        p = subprocess.Popen([self.stub, "--remote-debugging-port=%d" % self.port],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: (p.poll() is None and p.kill(), p.wait()))
        end = time.time() + 20
        while time.time() < end and not _answers(self.port):
            time.sleep(0.1)
        self.assertTrue(_answers(self.port), "PREMISE: the stub Chrome never answered")
        return p


@unittest.skipUnless(_POSIX, "the stub Chrome is a #! script - POSIX only")
class AChromeTheRunStartedIsAttested(_Stubbed):
    def test_the_chrome_chrome_up_starts_is_a_C_line(self):
        proc, facts, why, plain = self._traced(_UP % {"tv": HERE, "again": ""}, allow_cdp=True)
        self.assertIn("UP True", proc.stdout, "PREMISE: the stub Chrome did not come up: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "the run's own attested Chrome untraced a reader that allows it: %s" % why)
        self.assertTrue(any("chrome_stub" in c for c in facts["C"]), "no C line names the Chrome: %r" % facts["C"])
        self.assertIsNone(plain[0], "a ledger read (no allow) carried a run with a Chrome")
        self.assertIn("a Chrome this run started for its pages", plain[1] or "")

    def test_its_own_chrome_found_again_is_not_adopted(self):
        again = "print('AGAIN', R._chrome_up())\n"
        proc, facts, why, _plain = self._traced(_UP % {"tv": HERE, "again": again}, allow_cdp=True)
        self.assertIn("AGAIN True", proc.stdout, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(why, "the run's own Chrome, asked for twice, read as adopted: %s" % why)


@unittest.skipUnless(_POSIX, "the stub Chrome is a #! script - POSIX only")
class AChromeTheRunDidNotStartUntracesIt(_Stubbed):
    def test_an_answering_port_is_adopted_with_a_U_line(self):
        self._start_stub()
        proc, facts, why, _plain = self._traced(_UP % {"tv": HERE, "again": ""}, allow_cdp=True)
        self.assertIn("UP True", proc.stdout, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(facts, "a Chrome this run did not start was adopted and the trace still carried")
        self.assertIn("adopted a Chrome this run did not start", why or "")

    def test_an_unmarked_child_is_a_U_line(self):
        code = ("import os, subprocess, time\n"
                "p = subprocess.Popen([%r, '--remote-debugging-port=%d'], env=dict(os.environ))\n"
                "time.sleep(0.3); p.kill(); p.wait()\n" % (self.stub, self.port))
        proc, facts, why, _plain = self._traced(code, allow_cdp=True)
        self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(facts, "a Chrome started without the marker was read as attested")
        self.assertIn("started chrome_stub", why or "")

    def test_a_marker_the_process_inherited_attests_nothing(self):
        code = ("import os, subprocess, time\n"
                "p = subprocess.Popen([%r, '--remote-debugging-port=%d'], env=dict(os.environ))\n"
                "time.sleep(0.3); p.kill(); p.wait()\n" % (self.stub, self.port))
        proc, facts, why, _plain = self._traced(code, extra={"TV_GATE_TRACE_CDP": "1"}, allow_cdp=True)
        self.assertEqual(proc.returncode, 0, "PREMISE: %s" % proc.stderr[-600:])
        self.assertIsNone(facts, "a marker inherited from the process's own environment attested its child")
        self.assertIn("started chrome_stub", why or "")

    def test_a_trace_that_cannot_take_the_line_is_never_adopted(self):
        self._start_stub()
        code = (_UP % {"tv": HERE, "again": ""})
        env = dict(os.environ, TV_GATE_TRACE=self.box, TV_CHROME=self.stub, TV_RENDER_PORT=str(self.port))
        proc = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=env, capture_output=True, text=True,
                              timeout=120)
        self.assertIn("UP False", proc.stdout, "a Chrome was adopted though the trace could not say so: %s"
                      % (proc.stdout + proc.stderr)[-600:])
        self.assertIn("not adopted", proc.stdout)


@unittest.skipUnless(_HAVE_NODE and shutil.which("git"), "no node (or no git) on PATH - the node twin cannot run here")
class ANodeChildAttestsTheSameWay(unittest.TestCase):
    def test_node_writes_C_for_a_marked_child_and_U_for_an_unmarked_one(self):
        box = tempfile.mkdtemp(prefix="cdp-node.")
        self.addCleanup(shutil.rmtree, box, True)
        script = os.path.join(box, "spawn.js")
        with io.open(script, "w", encoding="utf-8") as fh:
            fh.write("const cp = require('child_process');\n"
                     "cp.spawnSync('git', ['--version'], {env: Object.assign({}, process.env, {TV_GATE_TRACE_CDP: '1'})});\n"
                     "if (process.argv[2] === 'both') cp.spawnSync('git', ['--version'], {env: Object.assign({}, process.env)});\n")
        for arg, want_ok in (("one", True), ("both", False)):
            trace = GL.trace_path()
            try:
                env = GL.trace_env(dict(os.environ), REPO, trace)
                proc = subprocess.run(["node", script, arg], cwd=REPO, env=env, capture_output=True, text=True,
                                      timeout=60)
                facts, why = GL.read_trace(trace, allow_cdp_chrome=True)
            finally:
                os.remove(trace)
            self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
            if want_ok:
                self.assertIsNone(why, "node's marked child was not attested: %s" % why)
                self.assertTrue(facts["C"], "node wrote no C line")
            else:
                self.assertIn("started git", why or "", "node's unmarked child was not a U")


class UntracedChromeUpIsAsBefore(unittest.TestCase):
    """Driven in this process with Popen captured, as test_safe_copy drives the launch: no trace, no marker."""

    def _captured_env(self, trace_value):
        import urllib.request as _u
        import render_check as R
        seen = {}

        class _Captured(RuntimeError):
            pass

        def _fake_popen(args, **kw):
            seen["kw"] = kw
            raise _Captured("captured before launch")

        def _no_cdp(*a, **k):
            raise IOError("no CDP here - force the launch path")
        saved = (subprocess.Popen, _u.urlopen, R.CHROME, R.PORT, os.environ.get("TV_GATE_TRACE"))
        try:
            subprocess.Popen, _u.urlopen, R.CHROME, R.PORT = _fake_popen, _no_cdp, sys.executable, _free_port()
            if trace_value is None:
                os.environ.pop("TV_GATE_TRACE", None)
            else:
                os.environ["TV_GATE_TRACE"] = trace_value
            try:
                R._chrome_up()
            except _Captured:
                pass
        finally:
            subprocess.Popen, _u.urlopen, R.CHROME, R.PORT = saved[:4]
            if saved[4] is None:
                os.environ.pop("TV_GATE_TRACE", None)
            else:
                os.environ["TV_GATE_TRACE"] = saved[4]
            _p = getattr(R, "_CHROME_PROFILE", None)
            if _p and os.path.isdir(_p) and "render_check-profile-" in os.path.basename(_p):
                shutil.rmtree(_p, True)
                R._CHROME_PROFILE = None
        self.assertIn("kw", seen, "PREMISE: _chrome_up never reached Popen")
        return seen["kw"].get("env")

    def test_untraced_the_chrome_inherits_the_environment(self):
        self.assertIsNone(self._captured_env(None), "an untraced run's Chrome got an environment of its own")

    def test_traced_the_chrome_carries_the_marker(self):
        env = self._captured_env(os.path.join(tempfile.gettempdir(), "never-written.tsv"))
        self.assertEqual((env or {}).get("TV_GATE_TRACE_CDP"), "1", "a traced run's Chrome carries no marker")


RED_PROOF = [
    {"why": "a child started without the marker is attested", "file": "gate_trace/sitecustomize.py",
     "find": "            return theirs == \"1\" and os.environ.get(\"TV_GATE_TRACE_CDP\") != \"1\"\n",
     "replace": "            return True\n", "matches": 1, "needs": "posix"},
    {"why": "a marker the process only inherited attests its child", "file": "gate_trace/sitecustomize.py",
     "find": "            return theirs == \"1\" and os.environ.get(\"TV_GATE_TRACE_CDP\") != \"1\"\n",
     "replace": "            return theirs == \"1\"\n", "matches": 1, "needs": "posix"},
    {"why": "an attested Chrome is written as U", "file": "gate_trace/sitecustomize.py",
     "find": "            emit(\"C\", \"started %s, a Chrome this run started for its pages\" % (head or \"a process\"))"
             "  # TRACE-CDP-ATTESTED\n",
     "replace": "            emit(\"U\", \"started %s, a Chrome this run started for its pages\" % (head or \"a process\"))"
                "  # TRACE-CDP-ATTESTED\n", "matches": 1, "needs": "posix"},
    {"why": "the reader accepts an attested Chrome by default", "file": "gate_ledger.py",
     "find": "        if kind == \"C\" and allow_cdp_chrome:  # LEDGER-CDP-ATTESTED\n",
     "replace": "        if kind == \"C\":  # LEDGER-CDP-ATTESTED\n", "matches": 1, "needs": "posix"},
    {"why": "an answering port is adopted with no U line", "file": "render_check.py",
     "find": "        if _trace and not _ours:\n", "replace": "        if False:\n", "matches": 1, "needs": "posix"},
    {"why": "the run's own Chrome found again reads as adopted", "file": "render_check.py",
     "find": "        _ours = _mine is not None and _mine.poll() is None\n", "replace": "        _ours = False\n",
     "matches": 1, "needs": "posix"},
    {"why": "the Chrome _chrome_up starts carries no marker", "file": "render_check.py",
     "find": "        env=(dict(os.environ, TV_GATE_TRACE_CDP=\"1\") if _trace else None))  # RENDER-CDP-MARK\n",
     "replace": "        env=None)  # RENDER-CDP-MARK\n", "matches": 1},
    {"why": "an untraced run's Chrome gets the marker too", "file": "render_check.py",
     "find": "        env=(dict(os.environ, TV_GATE_TRACE_CDP=\"1\") if _trace else None))  # RENDER-CDP-MARK\n",
     "replace": "        env=dict(os.environ, TV_GATE_TRACE_CDP=\"1\"))  # RENDER-CDP-MARK\n", "matches": 1},
    {"why": "a Chrome is adopted though the trace could not take the line", "file": "render_check.py",
     "find": "                      \"start it (%s) - not adopted\" % (PORT, type(_we).__name__))\n                return False\n",
     "replace": "                      \"start it (%s) - not adopted\" % (PORT, type(_we).__name__))\n",
     "matches": 1, "needs": "posix"},
    {"why": "the node twin writes U for a marked child", "file": "gate_trace/node_trace.cjs",
     "find": "      emit('C', 'started ' + (head || 'a process') + ', a Chrome this run started for its pages');"
             "  // TRACE-CDP-ATTESTED\n",
     "replace": "      emit('U', 'started ' + (head || 'a process'));  // TRACE-CDP-ATTESTED\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
