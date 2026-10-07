# -*- coding: utf-8 -*-
"""REG-2009 - A CONSOLE ON A PRIVATE PORT IS A HARNESS, NEVER A ROW IN HIS LIVE FLEET.

GrokBot tick 403 (2026-10-07 19:42-19:47, #230): after a refresh a FOURTH "Konyo" row appeared in the live fleet -
"river UNKNOWN · this console has no native window (headless or --no-open)" - while the plain Konyo row vanished; five
minutes later it was all back. Every console started through main() starts the beacon thread whatever its port, and of
the harnesses that boot a private console (laws, render_check, the push gate's demos, heart2's prove lanes) only a few
fleet laws set TVD_NO_BEACON - run_gates, shard_suite, heart2 and render_check set nothing. A law run on his Mac, in the
same minutes, booted headless consoles. So a test could write a row into the roster his other PCs read, which is also a
plausible source of the fleet churn and hostname rows filed as #237 / #246.

The rule, ONE copy for both senders (_console_beacon and _console_beacon_presence each had their own): CI,
GITHUB_ACTIONS and TVD_NO_BEACON suppress as before, and a console whose port is not the live 17772 suppresses too, with
the reason recorded; TVD_BEACON_ANY_PORT=1 lets a private port through on purpose. Driven here with the network stubbed
- nothing in this law can reach the fleet.
"""
import io
import os
import sys
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

os.environ["TVD_NO_BEACON"] = "1"           # importing the console must not beacon from this process either
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import control_app as CA  # noqa: E402

CLEAN = {}                                    # an environment with none of the suppressing variables


class AHarnessConsoleNeverJoinsTheFleet(unittest.TestCase):

    def test_the_live_port_reports_and_a_private_port_does_not(self):
        self.assertEqual(CA._beacon_suppressed_by(CLEAN, 17772), "", "the live console stopped reporting to the fleet")
        why = CA._beacon_suppressed_by(CLEAN, 17991)
        self.assertIn("private port (17991)", why, "a harness console on a private port reports as a fleet row (REG-2009)")

    def test_a_deliberate_override_lets_a_private_port_through(self):
        self.assertEqual(CA._beacon_suppressed_by({"TVD_BEACON_ANY_PORT": "1"}, 17991), "")

    def test_the_old_rules_still_win(self):
        for k in ("CI", "GITHUB_ACTIONS", "TVD_NO_BEACON"):
            self.assertEqual(CA._beacon_suppressed_by({k: "1"}, 17772), k)

    def _sends(self, fn):
        sent = []

        def _urlopen(*a, **k):
            sent.append(1)
            raise OSError("this law never reaches the network")

        env = {k: v for k, v in os.environ.items() if k not in ("CI", "GITHUB_ACTIONS", "TVD_NO_BEACON")}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(CA, "CONTROL_PORT", 17991), \
                mock.patch("urllib.request.urlopen", _urlopen), \
                mock.patch.object(CA, "_beacon_state_save", lambda *a, **k: None), \
                mock.patch.dict(CA._FLEET_LAST_BODY, {"body": {"machine": "law", "ver": "v0"}}):
            fn()
        return sent, dict(CA._BEACON_LAST)

    def test_neither_sender_reaches_the_fleet_from_a_private_port(self):
        sent, last = self._sends(lambda: CA._console_beacon("hb"))
        self.assertEqual(sent, [], "the full beacon left a private-port console (REG-2009)")
        self.assertIn("private port", last.get("suppressed_by") or "", "the suppression was not recorded")
        sent, _l = self._sends(CA._console_beacon_presence)
        self.assertEqual(sent, [], "the presence beacon left a private-port console (REG-2009)")

    def test_both_senders_ask_the_one_rule(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            code = "\n".join(l.split("#", 1)[0] for l in fh.read().split("\n"))
        self.assertEqual(code.count("    supp = _beacon_suppressed_by()\n"), 2,
                         "a sender keeps its own copy of the suppression rule again")


RED_PROOF = [
    {"why": "REG-2009 - a private-port harness console reports to the live fleet again",
     "file": "tv/control_app.py",
     "find": '    if p != LIVE_CONTROL_PORT and not env.get("TVD_BEACON_ANY_PORT"):\n',
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-2009 - the deliberate override is ignored, so no private console can ever report",
     "file": "tv/control_app.py",
     "find": '    if p != LIVE_CONTROL_PORT and not env.get("TVD_BEACON_ANY_PORT"):\n',
     "replace": "    if p != LIVE_CONTROL_PORT:\n",
     "matches": 1},
    {"why": "REG-2009 - the presence sender skips the rule and reports from a private port",
     "file": "tv/control_app.py",
     "find": '    supp = _beacon_suppressed_by()\n    if supp:\n        _console_beacon("hb")\n        return\n',
     "replace": '    supp = ""\n    if supp:\n        _console_beacon("hb")\n        return\n',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
