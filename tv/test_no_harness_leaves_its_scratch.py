# -*- coding: utf-8 -*-
"""NO HARNESS THE CONSOLE RUNS LEAVES ITS SCRATCH BEHIND — #171's class, in PRODUCTION code this time.

#171 closed the leak in the TEST files (fixture_tmp.contain). MEASURED 2026-09-26 05:20, while removing eleven heart2
sandboxes: his temp dir still minted, per DAY, 1,890 `diskrep_*` (disk_report_wilson's self-proof, every doctor pass),
196 `heartlane_*` (the doctor's lane row), 49 `sweeplane_/sweeplock_/sweepok_` + 28 `sweeplink_` (sweep_wilson), 48
empty `tvd-gates-*` (run_gates minting one at IMPORT, used by nothing), 26 `render_check-profile-*` (a killed run's
Chrome profile), 15 `vault-sim-*`, 5 `rrw_*`. Every one is production code that runs on his machine, the ALT and
Dean's, again and again - and the #171 law reads only tv/test_*.py.

  · DRIVEN (a real child process, TMPDIR = a fresh empty dir): disk_report_wilson.prove(), reel_router_wilson.prove(),
    sweep_wilson.score() and the doctor's "an attack can still reach the door" row run end to end; afterwards the dir
    holds none of their scratch. PREMISE: each harness really ran (it returned rows).
  · DRIVEN: importing run_gates mints no directory.
  · DRIVEN: render_check's launch sweep removes an old profile no process holds, and keeps a fresh one, a held one
    (named in a running command line) and anything that is not a profile.
  · The STATIC side - every production mkdtemp paired, or explained with a re-proven reason - is ONE list, in
    test_production_scratch_dirs_only_get_fewer (#171's ratchet), lowered by this fix from 24 sites to 2. Not a second
    copy here. [[copy-drift]]
RED_PROOF below.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
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

import test_a_test_run_leaves_no_scratch_dirs as SCRATCH  # noqa: E402  one finder, not a second copy

PREFIXES = ("diskrep_", "rrw_", "sweeplane_", "sweeplock_", "sweepok_", "sweepbusy_", "sweeplink_", "heartlane_",
            "tvd-gates-")

CHILD = r"""
import json, os, sys
sys.path.insert(0, %(here)r)
out = {}
import disk_report_wilson as D
r = D.prove(); out["disk"] = len(r.get("rows") or [])
import reel_router_wilson as R
r = R.prove(); out["router"] = len(r.get("rows") or []) if isinstance(r, dict) else len(r or [])
import sweep_wilson as S
out["sweep"] = len(S.score() or [])
import console_doctor as C
v = C._check_an_attack_can_still_reach_the_door_it_scores(); out["door"] = str(v[0]) if v else None
import run_gates
out["gates"] = len(getattr(run_gates, "GATES", []) or [])
print(json.dumps(out))
"""


class NoHarnessLeavesItsScratch(unittest.TestCase):

    def test_the_harnesses_the_console_runs_leave_nothing_in_the_temp_dir(self):
        tmp = tempfile.mkdtemp(prefix="harnessleak-")
        self.addCleanup(shutil.rmtree, tmp, True)
        env = dict(os.environ, TMPDIR=tmp, TEMP=tmp, TMP=tmp)
        r = subprocess.run([sys.executable, "-c", CHILD % {"here": HERE}], env=env, capture_output=True, text=True,
                           timeout=300, cwd=HERE)
        self.assertEqual(r.returncode, 0, "the harnesses would not run - UNKNOWN, not passing: %s" % r.stderr[-900:])
        ran = json.loads(r.stdout.strip().splitlines()[-1])
        for k in ("disk", "router", "sweep", "gates"):
            self.assertGreater(ran.get(k) or 0, 0, "PREMISE: %s did not really run (%r), so its silence proves nothing" % (k, ran))
        self.assertTrue(ran.get("door"), "PREMISE: the doctor's door row did not answer")
        left = sorted(n for n in os.listdir(tmp) if n.startswith(PREFIXES))
        self.assertEqual(left, [], "these harnesses left their scratch behind - every doctor pass on his machine "
                                   "adds more: %s" % left[:12])

    def test_importing_run_gates_mints_no_directory(self):
        tmp = tempfile.mkdtemp(prefix="harnessleak-")
        self.addCleanup(shutil.rmtree, tmp, True)
        env = dict(os.environ, TMPDIR=tmp, TEMP=tmp, TMP=tmp)
        r = subprocess.run([sys.executable, "-c", "import os, sys; sys.path.insert(0, %r); import run_gates; "
                            "print(sorted(os.listdir(%r)))" % (HERE, tmp)],
                           env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertEqual(r.stdout.strip(), "[]", "importing run_gates made a directory nothing uses: %s" % r.stdout)

    def test_a_killed_runs_chrome_profile_is_swept_and_a_live_one_is_kept(self):
        import render_check as RC
        tmp = tempfile.mkdtemp(prefix="harnessleak-")
        self.addCleanup(shutil.rmtree, tmp, True)

        def mk(name, age_h):
            p = os.path.join(tmp, name)
            os.makedirs(os.path.join(p, "Default"))
            t = time.time() - age_h * 3600
            os.utime(p, (t, t))
            return p
        dead = mk("render_check-profile-dead", 5)
        held = mk("render_check-profile-held", 5)
        fresh = mk("render_check-profile-fresh", 0.1)
        other = mk("not-a-profile", 5)
        running = "/Applications/Google Chrome --headless=new --user-data-dir=%s about:blank\n" % held
        # the #231 eye on v3507: a profile whose Chrome's own SingletonLock names a LIVE pid is kept even when the
        # process list does not mention it; a dangling lock (a killed run) does not protect it
        locked = mk("render_check-profile-locked", 5)
        os.symlink("somehost-%d" % os.getpid(), os.path.join(locked, "SingletonLock"))
        dangling = mk("render_check-profile-dangling", 5)
        p0 = subprocess.Popen([sys.executable, "-c", "pass"]); p0.wait()
        os.symlink("somehost-%d" % p0.pid, os.path.join(dangling, "SingletonLock"))
        for d in (locked, dangling):
            t = time.time() - 5 * 3600
            os.utime(d, (t, t))
        gone = sorted(RC._sweep_dead_profiles(tmp=tmp, running=running))
        self.assertEqual(gone, sorted([dead, dangling]), "the sweep removed %s, not only the dead runs' old profiles" % gone)
        for p in (held, fresh, other, locked):
            self.assertTrue(os.path.isdir(p), "the sweep removed %s - a live Chrome's, a fresh one, or not a profile" % p)

    def test_an_unreadable_process_list_removes_nothing(self):
        """the #231 eye on v3507: `ps` failing or answering nothing is UNKNOWN - read as "nobody holds anything" it would
        delete every live profile an hour old"""
        import render_check as RC
        tmp = tempfile.mkdtemp(prefix="harnessleak-")
        self.addCleanup(shutil.rmtree, tmp, True)
        p = os.path.join(tmp, "render_check-profile-live")
        os.makedirs(p)
        t = time.time() - 5 * 3600
        os.utime(p, (t, t))
        real = RC.subprocess.run
        class _R(object):
            returncode, stdout, stderr = 1, "", "ps: boom"
        RC.subprocess.run = lambda *a, **k: _R()
        try:
            got = RC._sweep_dead_profiles(tmp=tmp)
        finally:
            RC.subprocess.run = real
        self.assertIsNone(got, "an unreadable process list was answered as a list: %r" % (got,))
        self.assertTrue(os.path.isdir(p), "an unreadable process list deleted a profile")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#231 on v3507 - a failed or empty `ps` is read as 'nobody holds anything' and live profiles are deleted",
        "file": "render_check.py",
        "find": "        if _ps.returncode != 0 or not (_ps.stdout or \"\").strip():\n            return None\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#231 on v3507 - Chrome's own SingletonLock no longer protects a live profile the process list missed",
        "file": "render_check.py",
        "find": "        if _profile_locked_by_a_live_chrome(p):\n            continue",
        "replace": "        if False:\n            continue",
        "matches": 1,
    },
    {
        "why": "disk_report_wilson's self-proof stops removing its throwaway histories: 1,890 diskrep_* a day again",
        "file": "disk_report_wilson.py",
        "find": "        SA.may = _real_may\n        _clean_scratch()\n",
        "replace": "        SA.may = _real_may\n",
        "matches": 1,
    },
    {
        "why": "the doctor's lane row leaves its heartlane_ dir on every pass again",
        "file": "console_doctor.py",
        "find": "        import shutil as _sh\n        _sh.rmtree(d, ignore_errors=True)\n",
        "replace": "        pass\n",
        "matches": 1,
    },
    {
        "why": "a sweep_wilson attempt leaves its sweeplink_ dir behind again",
        "file": "sweep_wilson.py",
        "find": "            shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — 432 sweeplink_* were left in his temp dir\n",
        "replace": "            pass\n",
        "matches": 1,
    },
    {
        "why": "run_gates mints an unused scratch dir at import again, in every process that reads GATES",
        "file": "run_gates.py",
        "find": "_GATE_SCRATCH = None\n",
        "replace": "_GATE_SCRATCH = tempfile.mkdtemp(prefix=\"tvd-gates-\")\n",
        "matches": 1,
    },
    {
        "why": "render_check's sweep removes a profile a live Chrome holds",
        "file": "render_check.py",
        "find": " or p in running or n in running:\n",
        "replace": ":\n",
        "matches": 1,
    },
]
