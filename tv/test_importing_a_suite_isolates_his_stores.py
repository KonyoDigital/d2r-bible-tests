# -*- coding: utf-8 -*-
"""REG-1281 — IMPORTING A SUITE ISOLATES HIS STORES; NO FIXTURE HOOK HAS TO RUN FIRST.

test_control redirected control_app's chronicle and vault state paths in setUpModule. A harness that runs
the file's cases one at a time never calls setUpModule - and on 2026-09-25 mine did exactly that (a
per-test census watcher). Fixture evidence ("Windforce", reel_s_1, f0.jpg) overwrote his live
tv/chron_evidence.json - 324 uniques, 126 sets, 2,714 pages - and seeded chron_autoread,
chron_last_result and chron_hunt_memory. Restored byte-exact from a copy; three laws that read his real
evidence caught it. The hand list also covered only five of the eight state paths.

  · DRIVEN (a fresh interpreter imports test_control and runs NOTHING): every control_app
    _CHRON_*/_VAULT_*_PATH points into the suite's sandbox, and there are at least the eight known today.
  · DRIVEN: importing test_g5_grok_eyes / test_console_fleet points G5_STATS_PATH into their sandbox.
RED_PROOF below.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _child(code):
    env = dict(os.environ)
    env.pop("G5_STATS_PATH", None)
    r = subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True,
                       timeout=180, env=env)
    if r.returncode != 0:
        raise AssertionError("the child import did not run - UNKNOWN, not passing: %s" % r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class ImportingASuiteIsolatesHisStores(unittest.TestCase):

    def test_importing_test_control_moves_every_state_path(self):
        got = _child(
            "import sys, json; sys.argv=['x']; sys.path.insert(0,'.')\n"
            "import test_control as tc, control_app as ca\n"
            "ps = {a: getattr(ca, a) for a in dir(ca) if a.startswith(('_CHRON_','_VAULT_')) and a.endswith('_PATH')"
            " and isinstance(getattr(ca, a), str)}\n"
            "print(json.dumps({'n': len(ps), 'live': sorted(a for a, v in ps.items() if not v.startswith(tc._MOD_TMP))}))")
        self.assertGreaterEqual(got["n"], 8, "premise: the eight state paths known on 2026-09-25 are found")
        self.assertEqual(got["live"], [], "importing test_control left these paths on his live tree: %r" % got["live"])

    def test_importing_the_g5_suites_moves_the_stats_path(self):
        for mod, var in (("test_g5_grok_eyes", "_G5_SANDBOX"), ("test_console_fleet", "_G5_STATS_SANDBOX")):
            got = _child(
                "import sys, os, json; sys.argv=['x']; sys.path.insert(0,'.')\n"
                "import %s as m\n"
                "p = os.environ.get('G5_STATS_PATH') or ''\n"
                "print(json.dumps({'p': p, 'ok': bool(p) and p.startswith(m.%s)}))" % (mod, var))
            self.assertTrue(got["ok"], "importing %s left G5_STATS_PATH at %r" % (mod, got["p"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1281 - test_control isolates only inside setUpModule again: a harness that skips it writes his evidence",
        "file": "test_control.py",
        "find": "\n_isolate_live_state()\n\n\ndef setUpModule():\n",
        "replace": "\n\n\ndef setUpModule():\n",
        "matches": 1,
    },
    {
        "why": "REG-1281 - the G5 suite points its stats at the sandbox only in setUpModule again",
        "file": "test_g5_grok_eyes.py",
        "find": "os.environ[\"G5_STATS_PATH\"] = os.path.join(_G5_SANDBOX, \"g5_stats.json\")  # REG-1281",
        "replace": "_unused_1281 = None  # REG-1281",
        "matches": 1,
    },
]
