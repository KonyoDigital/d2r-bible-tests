# -*- coding: utf-8 -*-
"""REG-1258 — THE PUSH GATE NEVER ADOPTS A BROWSER IT DID NOT START.

MEASURED 2026-09-24, before a push: another Claude session's headless Chrome held :9224 for its own web
research. hooks/pre-push asked "does something answer on :9224?" and, if so, USED it - and so did
render_check._chrome_up() and crest_loudness behind it. The gate would have opened its tabs in someone
else's browser, at that browser's window size, and graded the page there. A port that answers is not a
browser you own.

The hook now chooses the first port from 9224 up that nothing listens on and exports it as
TV_RENDER_PORT, which render_check.PORT (and so crest_loudness) already reads.

  · DRIVEN (bash, the REAL snippet cut from hooks/pre-push between its markers): with a listener held on
    the first port, the chosen port is a different, free one - never the held one, never 9222/9223.
  · PREMISE: with nothing held, the snippet chooses the first port - so the held case can fail.
  · JOINED: the render block launches and polls "$TV_RENDER_PORT", with no literal 9224 left in it, and
    render_check reads the same variable.
RED_PROOF below.
"""
import io
import os
import re
import shutil
import socket
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

HOOK = os.path.join(ROOT, "hooks", "pre-push")


def _hook():
    with io.open(HOOK, encoding="utf-8") as f:
        return f.read()


def _snippet():
    src = _hook()
    i = src.index("# >>> choose-render-port\n")
    j = src.index("# <<< choose-render-port\n", i)
    return src[i:j]


def _choose(from_port):
    script = _snippet() + '\necho "CHOSEN=$TV_RENDER_PORT"\n'
    env = dict(os.environ, TV_RENDER_PORT_FROM=str(from_port))
    r = subprocess.run(["bash", "-c", "set -u\n" + script], capture_output=True, text=True, timeout=60, env=env)
    if r.returncode != 0:
        raise AssertionError("the hook's port snippet did not run - UNKNOWN, not passing: %s" % r.stderr[:400])
    m = re.search(r"CHOSEN=(\d+)", r.stdout)
    if not m:
        raise AssertionError("the snippet exported nothing - UNKNOWN: %r" % r.stdout[:300])
    return int(m.group(1))


def _free_block():
    """A port P above 9224 where P and P+1 both bind right now (the OS picks; we only borrow the number)."""
    for _ in range(20):
        a = socket.socket()
        a.bind(("127.0.0.1", 0))
        p = a.getsockname()[1]
        a.close()
        if p < 9300 or p > 65000:
            continue
        try:
            b = socket.socket()
            b.bind(("127.0.0.1", p + 1))
            b.close()
            return p
        except OSError:
            continue
    raise unittest.SkipTest("no free port pair found - UNMEASURED, not passing")


@unittest.skipIf(shutil.which("bash") is None,
                 "bash absent - this law is UNMEASURED, not passing")
class TheGateNeverAdoptsABrowserItDidNotStart(unittest.TestCase):

    def test_premise_with_nothing_held_the_first_port_is_chosen(self):
        p = _free_block()
        self.assertEqual(_choose(p), p)

    def test_a_held_port_is_skipped(self):
        p = _free_block()
        held = socket.socket()
        held.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        held.bind(("127.0.0.1", p))
        held.listen(1)
        try:
            got = _choose(p)
        finally:
            held.close()
        self.assertNotEqual(got, p, "the gate chose a port something else is listening on - it would adopt that browser")
        self.assertGreater(got, p)

    def test_never_his_ports(self):
        self.assertGreaterEqual(_choose(9222), 9224, "the gate may never choose his Chrome (9222) or TradingView (9223)")

    def test_the_render_block_uses_the_chosen_port(self):
        code = "\n".join(l.split("#", 1)[0] for l in _hook().split("\n"))
        i = code.find('if ! curl -s -m 2 -o /dev/null "http://127.0.0.1:$TV_RENDER_PORT/json/version"; then')
        self.assertGreater(i, -1, "the render block no longer probes the chosen port")
        self.assertIn('--remote-debugging-port="$TV_RENDER_PORT"', code)
        self.assertEqual(re.findall(r"127\.0\.0\.1:9224|remote-debugging-port=9224", code), [],
                         "a literal :9224 is back in the hook - it would adopt whatever answers there")
        self.assertLess(code.find("export TV_RENDER_PORT="), i, "the port is exported after the render block needs it")

    def test_render_check_reads_the_same_variable(self):
        import render_check as rc
        with io.open(rc.__file__, encoding="utf-8") as f:
            self.assertIn('os.environ.get("TV_RENDER_PORT"', f.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1258 - the hook adopts whatever answers on the first port again (another session's browser)",
        "file": "hooks/pre-push",
        "find": "  if (exec 3<>\"/dev/tcp/127.0.0.1/$_rp\") 2>/dev/null; then continue; fi\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1258 - the render block probes a literal :9224 again instead of the chosen port",
        "file": "hooks/pre-push",
        "find": "  if ! curl -s -m 2 -o /dev/null \"http://127.0.0.1:$TV_RENDER_PORT/json/version\"; then\n",
        "replace": "  if ! curl -s -m 2 -o /dev/null http://127.0.0.1:9224/json/version; then\n",
        "matches": 1,
    },
]
