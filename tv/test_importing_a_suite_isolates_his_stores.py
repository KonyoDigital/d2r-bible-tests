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
  · REG-1650 (v3539) DRIVEN: the vault lane's store - resolved by a FUNCTION, so the discovery above never saw it -
    resolves into the sandbox after importing test_control; only a console process runs the boot re-entry that
    writes it; and the run_gates live-state guard names the file.
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

    def test_importing_test_control_moves_the_vault_lanes_store_too(self):
        """REG-1650 — the vault lane's memory had no _VAULT_*_PATH global, only a function, so the discovery above
        could not see it and every test_control run in his tree read and wrote his REAL .vault_autoread.json.
        MEASURED in his live file 2026-10-01: lastWhy["reel_qqq"] = "vault_retro exploded" - a test_control fixture.
        The FUNCTION is asked, because the function is what every reader and writer calls."""
        got = _child(
            "import sys, json; sys.argv=['x']; sys.path.insert(0,'.')\n"
            "import test_control as tc, control_app as ca\n"
            "p = ca._vault_autoread_path()\n"
            "print(json.dumps({'p': p, 'ok': p.startswith(tc._MOD_TMP)}))")
        self.assertTrue(got["ok"], "importing test_control left the vault lane's store on his live tree: %r" % got["p"])

    def test_only_a_console_clears_the_parking_bay(self):
        """REG-1650 — the boot re-entry WRITES his lane memory, and status_payload() reaches it in ANY process that
        imports control_app; five suites call it with no store isolation, from his checkout, at every push."""
        import control_app as ca
        import frame_ref as fr
        calls = []
        saved = (ca.vault_reentry_sweep, ca._VAULT_REENTRY_DONE, dict(ca._VAULT_AUTOREAD_REFRESH), fr.on_console_path())
        ca.vault_reentry_sweep = lambda dry=True: calls.append(dry) or {"readmitted": []}
        ca._VAULT_AUTOREAD_REFRESH["running"] = True          # the kick returns before starting its survey thread
        try:
            fr.mark_console_path(False)
            ca._VAULT_REENTRY_DONE = False
            ca._vault_autoread_kick()
            self.assertEqual(calls, [], "a process that is not a console cleared the bay - a test or the gate wrote "
                                        "his lane memory")
            fr.mark_console_path(True)
            ca._VAULT_REENTRY_DONE = False
            ca._vault_autoread_kick()
            self.assertEqual(calls, [False], "PREMISE: the console no longer clears the bay at all")
        finally:
            ca.vault_reentry_sweep, ca._VAULT_REENTRY_DONE = saved[0], saved[1]
            ca._VAULT_AUTOREAD_REFRESH.clear()
            ca._VAULT_AUTOREAD_REFRESH.update(saved[2])
            fr.mark_console_path(saved[3])

    def test_the_gate_watches_the_vault_lanes_store(self):
        import run_gates
        self.assertIn(".vault_autoread.json", run_gates._LIVE_STATE,
                      "a suite that writes the vault lane's memory would not be named by the live-state guard")

    def test_a_law_does_not_write_his_vault_lane_memory(self):
        """REG-2150. test_seal_named calls vault_sweep_start(force=True). The sweep thread
        finishes in _vault_lane_note_outcome, which saves. That gate is not a console and
        does not repoint the store, so the save created tv/.vault_autoread.json. The
        v3628 shard blamed test_seal_named, which writes nothing of its own."""
        got = _child(
            "import os, sys, json, tempfile\n"
            "sys.path.insert(0, '.')\n"
            "import control_app as ca, frame_ref as fr\n"
            "live = os.path.join(os.path.dirname(os.path.abspath(ca.__file__)), '.vault_autoread.json')\n"
            "existed = os.path.isfile(live)\n"
            "before = open(live, 'rb').read() if existed else None\n"
            "root = tempfile.mkdtemp(prefix='vault-law-')\n"
            "reel = os.path.join(root, 'reel_s_1500000000001_12001')\n"
            "os.makedirs(reel)\n"
            "ca._VAULT_JOB['incompleteWhy'] = 'fixture reason from a law'\n"
            "ca._VAULT_JOB['error'] = None\n"
            "ca._VAULT_JOB['notDefinitiveWhy'] = None\n"
            "ca._VAULT_AUTOREAD_STORE['tried'] = False\n"
            "ca._VAULT_AUTOREAD_STORE['readable'] = None\n"
            "why = ca._vault_lane_note_outcome(reel, swept={})\n"
            "created = (not existed) and os.path.isfile(live)\n"
            "changed = bool(existed and os.path.isfile(live) and open(live, 'rb').read() != before)\n"
            "if created:\n"
            "    os.remove(live)\n"
            "print(json.dumps({'console': bool(fr.on_console_path()), 'why': why,\n"
            " 'created': created, 'changed': changed}))")
        self.assertFalse(got["console"], "the child was a console, so this measured the wrong process")
        self.assertTrue(got["why"], "the note gave no reason, so the save was never asked: %r" % got)
        self.assertFalse(got["created"] or got["changed"],
                         "a law wrote his vault lane memory: %r" % got)
        world = _child(
            "import os, sys, json, tempfile, shutil\n"
            "sys.path.insert(0, '.')\n"
            "root = tempfile.mkdtemp(prefix='vault-world-')\n"
            "os.environ['TV_HIST'] = root\n"
            "import control_app as ca\n"
            "reel = os.path.join(root, 'reel_s_1500000000099_21500')\n"
            "os.makedirs(reel)\n"
            "ca._VAULT_JOB['incompleteWhy'] = 'fixture world'\n"
            "ca._VAULT_JOB['error'] = None\n"
            "ca._VAULT_JOB['notDefinitiveWhy'] = None\n"
            "ca._VAULT_AUTOREAD_STORE['tried'] = False\n"
            "ca._VAULT_AUTOREAD_STORE['readable'] = None\n"
            "live = os.path.join(os.path.dirname(os.path.abspath(ca.__file__)), '.vault_autoread.json')\n"
            "existed = os.path.isfile(live)\n"
            "before = open(live, 'rb').read() if existed else None\n"
            "why = ca._vault_lane_note_outcome(reel, swept={})\n"
            "store = os.path.join(root, '.vault_autoread.json')\n"
            "created = (not existed) and os.path.isfile(live)\n"
            "changed = bool(existed and os.path.isfile(live) and open(live, 'rb').read() != before)\n"
            "print(json.dumps({'why': bool(why), 'in_world': os.path.isfile(store),\n"
            " 'created': created, 'changed': changed}))\n"
            "shutil.rmtree(root, ignore_errors=True)")
        self.assertTrue(world["why"] and world["in_world"],
                        "a fixture world no longer keeps its own lane memory: %r" % world)
        self.assertFalse(world["created"] or world["changed"],
                         "a fixture world wrote his vault lane memory: %r" % world)
        import control_app as ca
        import frame_ref as fr
        was = fr.on_console_path()
        live = os.path.join(os.path.dirname(os.path.abspath(ca.__file__)), ".vault_autoread.json")
        try:
            fr.mark_console_path(False)
            self.assertFalse(ca._vault_autoread_write_allowed(live),
                             "a non-console was allowed to write the live store")
            fr.mark_console_path(True)
            self.assertTrue(ca._vault_autoread_write_allowed(live),
                            "the console was refused its own lane memory")
        finally:
            fr.mark_console_path(was)

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
        "why": "REG-2150 - a law saves the vault lane into his tree again",
        "file": "control_app.py",
        "find": "        dest = _vault_autoread_path()\n"
                "        if not _vault_autoread_write_allowed(dest):       # REG-2150\n"
                "            _failed = True\n"
                "            return False\n",
        "replace": "        dest = _vault_autoread_path()\n",
        "matches": 1,
    },
    {
        "why": "REG-1281 - test_control isolates only inside setUpModule again: a harness that skips it writes his evidence",
        "file": "test_control.py",
        "find": "\n_isolate_live_state()\n\n\ndef setUpModule():\n",
        "replace": "\n\n\ndef setUpModule():\n",
        "matches": 1,
    },
    {
        "why": "REG-1650 - the vault store's function ignores the suite's sandbox again: test_control writes his lane memory",
        "file": "control_app.py",
        "find": "    if _VAULT_AUTOREAD_PATH != _VAULT_AUTOREAD_AT_IMPORT:\n"
                "        return _VAULT_AUTOREAD_PATH       # patched on purpose (a suite's sandbox) — honour it\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1650 - any process that asks for a status clears the bay again, writing his lane memory",
        "file": "control_app.py",
        "find": "    if not _VAULT_REENTRY_DONE and _bay_ours:\n",
        "replace": "    if not _VAULT_REENTRY_DONE:\n",
        "matches": 1,
    },
    {
        "why": "REG-1650 - the live-state guard forgets the vault lane's store again",
        "file": "run_gates.py",
        "find": "               \".vault_autoread.json\")\n",
        "replace": "               )\n",
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
