# -*- coding: utf-8 -*-
"""REG-2123 - A PRIVATE CONSOLE NEVER SHARES A PORT WITH HIS.

test_button_matrix boots its own control_app and drives ON / OFF / STOP on it. Only the control port was private: the agent
port (TV_PORT) fell through to :17771, which is where HIS live agent listens, so the private app's OFF asked his agent to shut
down and its STOP SIGTERMed whatever listened there. Measured in his agent log on 2026-10-09: eleven ON AIR sessions cut between
02:00 and 02:37 ("closing session (off)" / "signal:SIGTERM"), each lining up with a gate shard, a push or a run of that law.

A law that RAN the matrix could only fail by touching his agent, so this one never runs an app: it calls the shipped
_boot_control with Popen replaced, reads the environment it would hand the private app, and requires both of that app's ports
to be its own - never his console's 17772 or his agent's 17771, never the same port twice. render_check, the headless-console
law and test_roundtrip_sim already give theirs TV_PORT=port+1; this holds the matrix to the same rule.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

HIS = {"17771", "17772"}


class _DeadChild(object):
    """What Popen hands back: a child that has already exited, so _boot_control returns at once (its SKIP path)."""
    pid = 0

    def poll(self):
        return 1

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 1


class APrivateConsoleNeverSharesHisPorts(unittest.TestCase):

    def _boot_env(self, inherited):
        import test_button_matrix as M
        seen = []
        real_popen = M.subprocess.Popen

        def fake(argv, env=None, **_kw):
            seen.append((list(argv), dict(env or {})))
            return _DeadChild()
        old = dict(os.environ)
        try:
            for k in ("TV_PORT", "TV_CONTROL_PORT", "TV_LANE_PORT_BASE"):
                os.environ.pop(k, None)
            os.environ.update(inherited)
            M.subprocess.Popen = fake
            self.assertIsNone(M._boot_control(), "a child that died on startup must read as a SKIP, not a console")
        finally:
            M.subprocess.Popen = real_popen
            os.environ.clear()
            os.environ.update(old)
        apps = [env for argv, env in seen if any(str(a).endswith("control_app.py") for a in argv)]
        self.assertEqual(len(apps), 1, "PRINT THE DENOMINATOR: _boot_control started %d control_app(s)" % len(apps))
        return apps[0]

    def test_its_agent_port_is_its_own_with_nothing_inherited(self):
        env = self._boot_env({})
        agent, ctrl = env.get("TV_PORT", ""), env.get("TV_CONTROL_PORT", "")
        self.assertTrue(agent, "the private app gets no TV_PORT, so its agent falls back to his :17771")
        self.assertNotIn(agent, HIS, "the private app's agent port is his: %s" % agent)
        self.assertNotIn(ctrl, HIS, "the private app's control port is his: %s" % ctrl)
        self.assertNotEqual(agent, ctrl, "the private app's agent and control share one port")

    def test_a_repeated_free_port_is_drawn_again_and_the_law_pings_its_childs_agent(self):
        """REG-2128 (the v3632 second eye) - the OS may hand back the same ephemeral port twice; the agent port is drawn again
        until it differs, and the law's own fallback agent is the port it handed the child."""
        import test_button_matrix as M
        seq = iter([40001, 40001, 40002])
        real = M._free_port
        try:
            M._free_port = lambda: next(seq)
            env = self._boot_env({})
            agent_url = M.AGENT
        finally:
            M._free_port = real
        self.assertEqual((env.get("TV_CONTROL_PORT"), env.get("TV_PORT")), ("40001", "40002"),
                         "a repeated free port went to both of the private app's doors: %r" % ((env.get("TV_CONTROL_PORT"), env.get("TV_PORT")),))
        self.assertEqual(agent_url, "http://127.0.0.1:40002", "the law's fallback agent is not the one it handed its child")

    def test_his_agent_port_in_the_environment_is_never_handed_on(self):
        """Even when the shell running the gate carries his ports, the private app does not inherit them."""
        env = self._boot_env({"TV_PORT": "17771", "TV_CONTROL_PORT": "17772"})
        self.assertNotIn(env.get("TV_PORT", ""), HIS, "his agent port in the shell reached the private app")
        self.assertNotIn(env.get("TV_CONTROL_PORT", ""), HIS, "his console port in the shell reached the private app")


RED_PROOF = [
    {"why": "REG-2128 - the two free-port draws are trusted to differ, so the private app can get one port for both",
     "file": "tv/test_button_matrix.py",
     "find": "    while agent_port == port:\n        agent_port = _free_port()\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2128 - the law's fallback agent stays the parent's TV_PORT / :17771 instead of the port it handed its child",
     "file": "tv/test_button_matrix.py",
     "find": "    AGENT = \"http://127.0.0.1:%d\" % agent_port\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2123 - the matrix's private app inherits TV_PORT again, so its OFF / STOP reach his live agent on :17771",
     "file": "tv/test_button_matrix.py",
     "find": "    env = dict(os.environ, TV_CONTROL_PORT=str(port), TV_PORT=str(agent_port), TV_ROBOT=\"1\",\n",
     "replace": "    env = dict(os.environ, TV_CONTROL_PORT=str(port), TV_ROBOT=\"1\",\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
