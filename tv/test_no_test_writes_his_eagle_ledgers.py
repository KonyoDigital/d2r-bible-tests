# -*- coding: utf-8 -*-
"""v3470 — no test process may write HIS eagle ledgers.

⚠⚠ WHAT IT COST: seven doctor suites drove console_doctor / unknown_age with fake checks and never
redirected TV_UNKNOWN_AGE / TV_EAGLE_SLOW, so every run appended 'exploder' (813), 'exploding check'
(803) and 'costly-one' to his live tv/.unknown_age.json and tv/.eagle_slow.json, and run_gates'
live-state watcher did not name either file, so CI filed it as "also touched" and moved on.
[[feedback-fixtures-never-touch-live-data]] — the guard goes on the FIXTURE.

Reads the gate files as AST (the compiler, never a regex over prose) and DRIVES the helper and the
real unknown_age writer against a temp path. RED_PROOF below.
"""
import ast
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

GATES = ["test_the_doctor_times_each_check.py", "test_the_screen_bills_the_same_rows_the_engine_does.py",
         "test_control.py", "test_board_tally_alarm.py", "test_a_periodic_check_is_still_watched_unattended.py",
         "test_health_engine.py", "test_a_skipped_periodic_check_still_emits_a_row.py"]
LIVE = (".unknown_age.json", ".eagle_slow.json")


def _calls_redirect_at_module_level(path):
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    for node in tree.body:                      # MODULE level only — a call inside a def may never run
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            f = node.value.func
            if isinstance(f, ast.Attribute) and f.attr == "redirect":
                return True
    return False


class NoTestWritesHisEagleLedgers(unittest.TestCase):

    def test_every_suite_that_drives_the_doctor_redirects_at_import(self):
        missing = [g for g in GATES if not _calls_redirect_at_module_level(os.path.join(HERE, g))]
        self.assertEqual(missing, [], "these suites drive the doctor and never redirect his ledgers: %r"
                         % missing)

    def test_the_helper_points_every_unset_ledger_outside_the_tree(self):
        import fixture_ledgers as FL
        saved = dict((v, os.environ.pop(v, None)) for v, _ in FL.VARS)
        try:
            got = FL.redirect()
            for var, path in got.items():
                self.assertFalse(os.path.abspath(path).startswith(os.path.abspath(HERE) + os.sep),
                                 "%s still points INTO tv/: %s" % (var, path))
        finally:
            for v, val in saved.items():
                if val is None:
                    os.environ.pop(v, None)
                else:
                    os.environ[v] = val

    def test_a_redirected_write_never_touches_the_live_file(self):
        import unknown_age as UA
        live = os.path.join(HERE, ".unknown_age.json")
        before = os.stat(live).st_mtime if os.path.exists(live) else None
        d = tempfile.mkdtemp(prefix="ua-law-")
        saved = os.environ.get("TV_UNKNOWN_AGE")
        try:
            os.environ["TV_UNKNOWN_AGE"] = os.path.join(d, "age.json")
            UA.attach([{"check": "a fixture check that must never reach him", "state": "unknown"}])
            self.assertTrue(os.path.exists(os.path.join(d, "age.json")),
                            "BASELINE: the redirected write did not happen, so nothing was measured")
        finally:
            if saved is None:
                os.environ.pop("TV_UNKNOWN_AGE", None)
            else:
                os.environ["TV_UNKNOWN_AGE"] = saved
            import shutil
            shutil.rmtree(d, ignore_errors=True)
        after = os.stat(live).st_mtime if os.path.exists(live) else None
        self.assertEqual(before, after, "a redirected write still moved his live ledger")

    def test_the_live_state_watcher_names_both_ledgers(self):
        import run_gates as RG
        for n in LIVE:
            self.assertIn(n, RG._LIVE_STATE, "run_gates would file a write to %s as 'also touched', "
                          "never as the suite writing his state" % n)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "test_control stops redirecting: every pre-push appends fixture checks to his ledgers again",
        "file": "test_control.py",
        "find": "_fx_ledgers.redirect()\n",
        "replace": "pass\n",
        "matches": 1,
    },
    {
        "why": "the helper points nowhere new: a test process writes the tree's own ledger files",
        "file": "fixture_ledgers.py",
        "find": "            p = os.path.join(tempfile.gettempdir(), \"tvd_fixture_%s_%d.json\" % (stem, os.getpid()))\n",
        "replace": "            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), \".%s.json\" % stem)\n",
        "matches": 1,
    },
    {
        "why": "the watcher forgets the ledger again: CI files a write to it as 'also touched'",
        "file": "run_gates.py",
        "find": "               \".unknown_age.json\", \".eagle_slow.json\")\n",
        "replace": "               \".eagle_slow.json\")\n",
        "matches": 1,
    },
]
