# -*- coding: utf-8 -*-
"""REG-1730 — THE v3557 SECOND EYE'S FINDINGS, EACH REPRODUCED BY READING THE CODE, AND CLOSED.

The cross-family look at v3557 (Grok CLI, the full 70,688-char diff 36812d92..af202672) returned five findings. Two were
REFUTED by the code (recorded in BUGS.md REG-1730): `self_prove.pid_alive` and control_app's `_pid_alive` never raise,
and `_absorb` never writes an empty `filledBy`. Three were real:

  · suite_verdict.inflight() trusted any live pid on a record a KILLED run never cleared - after the pid is reused, the
    push waits out --wait (900 / 1500 s) for a stranger. A record older than its run's own bound is not in flight now.
  · vault_retro._absorb filed an incoming list / dict BY REFERENCE, so mutating the row afterwards changed a filed fact.
    It files a copy now.
  · the boot installer held _PIP_BOOT_LOCK only around pip; site.addsitedir (which mutates sys.path) and the import
    re-check ran unlocked, so the Pillow and numpy boot threads could interleave there. The lock covers both now.
RED_PROOF below. [[unknown-stays-unknown]] [[stale-reading]]
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import suite_verdict as SV  # noqa: E402
import vault_retro as vr  # noqa: E402
import control_app as ca  # noqa: E402
import win_relaunch as wr  # noqa: E402


class AKilledRunsRecordIsNotInFlightForEver(unittest.TestCase):

    def setUp(self):
        d = tempfile.mkdtemp(prefix="inflight_age_")
        self.addCleanup(shutil.rmtree, d, True)
        self.path = os.path.join(d, "suite_verdicts.json")

    def _plant(self, started):
        with open(self.path, "w") as fh:
            json.dump({"inflight": {"test_control|k": {"pid": os.getpid(), "started": started}}}, fh)

    def test_premise_a_young_record_with_a_live_pid_is_in_flight(self):
        self._plant(time.time() - 30)
        self.assertIsNotNone(SV.inflight("test_control", "k", path=self.path))

    def test_a_record_older_than_its_run_could_last_is_a_reused_pid(self):
        self._plant(time.time() - (SV.RUN_TIMEOUT_S["test_control"] + 600))
        self.assertIsNone(SV.inflight("test_control", "k", path=self.path),
                          "a live pid on a record older than the run's own bound was trusted as the run")


class AFiledFactIsACopy(unittest.TestCase):

    def test_mutating_the_row_after_it_was_absorbed_never_moves_a_filed_fact(self):
        have = {}
        base = {"name": "Shako", "lane": "stash", "kind": "item", "count": 1, "conf": 0.9, "lastSeenTs": 1}
        vr._absorb(have, dict(base, witnesses=[{"session": "s1", "frame": "f1", "lane": "stash"}]))
        later = {"session": "s1", "frame": "f1", "lane": "stash", "sockets": ["Ist"], "eth": False}
        vr._absorb(have, dict(base, witnesses=[later]))
        w = have[("Shako", "stash")]["witnesses"][0]
        self.assertEqual(w.get("sockets"), ["Ist"], "PREMISE: the re-read did not fill its sockets")
        later["sockets"].append("Ber")
        self.assertEqual(w.get("sockets"), ["Ist"], "a filed fact moved when the row it came from was mutated")


class TheBootInstallCheckIsUnderTheLock(unittest.TestCase):

    def setUp(self):
        self._win, self._scratch = ca.IS_WIN, wr.scratch_console
        ca.IS_WIN = True
        wr.scratch_console = lambda *a, **k: False
        self.addCleanup(self._restore)

    def _restore(self):
        ca.IS_WIN, wr.scratch_console = self._win, self._scratch

    def test_sys_path_is_changed_and_rechecked_only_while_the_lock_is_held(self):
        import site
        held = []
        state = {"present": False}

        def find(name):
            held.append(("find", ca._PIP_BOOT_LOCK.locked()))
            return object() if state["present"] else None

        class _P(object):
            returncode, stderr, stdout = 0, "", ""

        def run(argv, **kw):
            state["present"] = True
            return _P()

        def addsitedir(p, *a, **k):
            held.append(("addsitedir", ca._PIP_BOOT_LOCK.locked()))
        with mock.patch.object(site, "addsitedir", addsitedir):
            rec = ca._ensure_pkg_at_boot("numpy", "numpy", "NUMPY_BOOT", _find=find, _run=run)
        self.assertTrue(rec and rec.get("tried"), "PREMISE: the installer did not run: %r" % (rec,))
        adds = [h for h in held if h[0] == "addsitedir"]
        self.assertTrue(adds, "PREMISE: site.addsitedir was never called: %r" % held)
        self.assertTrue(all(h[1] for h in adds), "site.addsitedir ran without the boot lock: %r" % held)
        self.assertEqual(held[-1], ("find", True), "the import re-check ran without the boot lock: %r" % held)


RED_PROOF = [
    {"why": "REG-1730 - a killed run's record is trusted again: the push waits out --wait for a reused pid",
     "file": "suite_verdict.py",
     "find": "            and time.time() - float(_st) > RUN_TIMEOUT_S.get(name, 1500) + 120:\n",
     "replace": "            and False:\n",
     "matches": 1},
    {"why": "REG-1730 - an absorbed list is filed by reference again: mutating the row moves a filed fact",
     "file": "vault_retro.py",
     "find": "                old[_f] = json.loads(json.dumps(_v)) if isinstance(_v, (dict, list)) else _v\n",
     "replace": "                old[_f] = _v\n",
     "matches": 1},
    {"why": "REG-1730 - sys.path is changed and the import re-checked outside the boot lock again",
     "file": "control_app.py",
     "find": "    with _PIP_BOOT_LOCK:\n        try:\n            import site\n",
     "replace": "    if True:\n        try:\n            import site\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
