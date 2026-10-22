# -*- coding: utf-8 -*-
"""REG-2461 / REG-2462 (#181) — A PC KEEPS ITS OWN SLOWEST REQUEST AND ITS OWN RIVER EPOCH, AND NEVER SHOWS ANOTHER'S.

MEASURED 2026-10-22 (git ls-files, and the code): tv/.status_worst.json and tv/.river_epoch.json are TRACKED, so every
update ships them to every PC. The console read the tracked record as THIS PC's slowest request (_status_worst_load),
published it as `worstRequest`, and kept it as the bar a new request must beat. The committed record is v3404's
1,773,092 ms fleetOrigin request from his Mac, so a fresh PC - Dean's - published his Mac's 29.5 minutes as its own
until something there was slower still, and never recorded a slow request of its own below that. The epoch harness
wrote the tracked epoch file in place (`io.open(p, "w").write(json.dumps(...))` truncates first, so a raise in dumps
left it empty). His doctrine: what a PC shows about itself comes from that PC's own stores; another PC's number is
UNKNOWN here, never shown.

THE LAW, in a fixture world - TV_HIST names this law's own scratch before control_app is imported, and
_fixture_root_for_state() honours it at every call, so his tv/ is never read or written:
  · another PC's record under the tracked name and no per-PC file -> _status_worst_load() is None and the published
    worstRequest is None (nothing measured here yet);
  · a slow /api/status request (status_payload, its network, CLI and git producers stubbed, the agent probe held for
    0.8 s) is kept in the per-PC file and published, and the tracked file's bytes stay identical;
  · the names the code writes - read from the code, with their .tmp - are ignored by git's own matcher in a throwaway
    repo seeded with the tree's .gitignore files (GIT_* scrubbed for these calls, the host's global excludes off);
  · river_epoch.write lands whole: a record it cannot serialise leaves the previous one byte-identical.
The tracked files are not deleted in this change: on a PC where one is locally modified (the ALT's ` M`, REG-1837) a
commit that deletes it makes `git pull --ff-only` refuse for good. [[unknown-stays-unknown]] [[the-unjoined-end]]
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp  # noqa: E402

fixture_tmp.contain()
#: the fixture world, named BEFORE control_app is imported so every module-level path it builds lands here too
WORLD = tempfile.mkdtemp(prefix="own-records-")
os.environ["TV_HIST"] = WORLD

import control_app as CA  # noqa: E402
import river_epoch as RE  # noqa: E402

GIT = shutil.which("git")
#: the files this law's verdict reads - part of its proof key
PROOF_NEEDS = ["../.gitignore", ".gitignore"]
#: another PC's record, shaped like the one the tracked file holds
ELSEWHERE = {"totalMs": 1773092.2, "slowest": {"ms": 1772731.2, "name": "fleetOrigin"},
             "sections": {"fleetOrigin": 1772731.2}, "unattributedMs": 1.9, "atMs": 1789975980187, "ver": "v3404",
             "capture": False, "mode": "off", "agent": False, "lockWaitDelta": 0}
TRACKED = ".status_worst.json"


class _World(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pc-", dir=WORLD)
        env = mock.patch.dict(os.environ, {"TV_HIST": self.root})
        env.start()
        self.addCleanup(env.stop)
        self.assertEqual(os.path.realpath(CA._fixture_root_for_state()), os.path.realpath(self.root),
                         "PREMISE: the fixture world is not where the console's state resolves")
        saved = {k: (dict(v) if isinstance(v, dict) else v) for k, v in CA._STATUS_TIMING.items()}
        self.addCleanup(lambda: (CA._STATUS_TIMING.clear(), CA._STATUS_TIMING.update(saved)))
        CA._STATUS_TIMING.update(worstRequest=None, last=None)
        self.tracked = os.path.join(self.root, TRACKED)
        with io.open(self.tracked, "w", encoding="utf-8") as fh:
            json.dump(ELSEWHERE, fh, indent=1, sort_keys=True)
        with open(self.tracked, "rb") as fh:
            self.tracked_bytes = fh.read()

    def tracked_untouched(self):
        with open(self.tracked, "rb") as fh:
            self.assertEqual(fh.read(), self.tracked_bytes, "the tracked record was written - it ships to every PC")


class ThisPCsRecordOnly(_World):

    def test_another_pcs_record_is_never_this_pcs(self):
        self.assertFalse(os.path.exists(CA._status_worst_path()), "PREMISE: this PC already has a record")
        self.assertIsNone(CA._status_worst_load(),
                          "another PC's slowest request (the tracked file) was read as this PC's own")
        CA._STATUS_TIMING["last"] = {"totalMs": 24.0, "sections": {}, "unattributedMs": 0.0, "slowest": None}
        pub = CA._status_timing_payload()
        self.assertIsNone(pub.get("worstRequest"),
                          "worstRequest published %r - another PC's number under this PC's name"
                          % ((pub.get("worstRequest") or {}).get("totalMs"),))
        self.tracked_untouched()

    def test_a_slow_request_here_is_kept_here_and_only_here(self):
        def held_probe():
            time.sleep(0.8)                 # the agent probe is the first producer: this request is a slow one
            return False
        stubs = (mock.patch.object(CA, "_agent_alive", held_probe),
                 mock.patch.object(CA, "fleet_origin_status", lambda force_fetch=False: {"ok": False, "behind": None}),
                 mock.patch.object(CA, "_published_ver", lambda: (None, None)),
                 mock.patch.object(CA, "screen_recording_ok_cached", lambda: True),
                 mock.patch.object(CA, "_bible_ver", lambda: None),
                 mock.patch.object(CA, "_claude_auth_state", lambda *a, **k: None))
        for s in stubs:
            s.start()
            self.addCleanup(s.stop)
        CA.status_payload()
        here = CA._status_worst_path()
        self.assertTrue(os.path.isfile(here),
                        "a slow request on this PC left no record of its own - the tracked record was the bar to beat")
        with io.open(here, encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertGreaterEqual(rec.get("totalMs"), CA._STATUS_SLOW_MS)
        self.assertLess(rec.get("totalMs"), ELSEWHERE["totalMs"], "the kept record is not this PC's request")
        self.assertEqual((CA._status_timing_payload().get("worstRequest") or {}).get("totalMs"), rec["totalMs"],
                         "the request kept here is not the one published")
        self.tracked_untouched()


@unittest.skipIf(GIT is None, "git is absent - this law is UNMEASURED, not passing")
class TheRecordsNeverTravel(unittest.TestCase):

    def test_git_ignores_the_names_the_code_writes(self):
        names = [os.path.basename(CA._status_worst_path()), os.path.basename(RE.EPOCH_PATH)]
        self.assertNotIn(TRACKED, names, "the console writes the tracked record again")
        rels = []
        for n in names:
            rels += ["tv/" + n, "tv/" + n + ".tmp"]
        d = tempfile.mkdtemp(prefix="own-records-ignore-")
        self.addCleanup(shutil.rmtree, d, True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}   # REG-2392: a hook's GIT_DIR outranks cwd=
        subprocess.run([GIT, "init", "-q", d], check=True, env=env)
        os.makedirs(os.path.join(d, "tv"))
        for rel in (".gitignore", os.path.join("tv", ".gitignore")):
            if os.path.isfile(os.path.join(ROOT, rel)):
                shutil.copyfile(os.path.join(ROOT, rel), os.path.join(d, rel))
        no_host = "core.excludesFile=" + os.path.join(d, "no-host-excludes")
        tracked = [r for r in rels
                   if subprocess.run([GIT, "-c", no_host, "check-ignore", "-q", "--no-index", r],
                                     cwd=d, env=env).returncode != 0]
        self.assertEqual(tracked, [], "this PC's own records are trackable - one update ships them to every PC")


class TheEpochIsWrittenWhole(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="epoch-write-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.p = os.path.join(self.d, "epoch.json")

    def test_a_record_that_cannot_be_written_leaves_the_last_one_whole(self):
        RE.write({"cycles": [], "stoppedBecause": "the last epoch"}, path=self.p)
        with open(self.p, "rb") as fh:
            before = fh.read()
        with self.assertRaises(TypeError):
            RE.write({"cycles": [object()]}, path=self.p)
        with open(self.p, "rb") as fh:
            self.assertEqual(fh.read(), before, "a failed epoch write emptied the last epoch's record")

    def test_a_written_record_reads_back_and_leaves_no_tmp(self):
        self.assertEqual(RE.write({"fired": ["eligible"]}, path=self.p), self.p)
        with io.open(self.p, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"fired": ["eligible"]})
        self.assertFalse(os.path.exists(self.p + ".tmp"), "the epoch's tmp was left beside its record")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2461 - with no record of its own the console falls back to the tracked file: another PC's slowest "
               "request is published as this PC's, and is the bar this PC's requests must beat",
        "file": "control_app.py",
        "find": "    except FileNotFoundError:\n"
                "        return None             # REG-2461 - nothing measured HERE yet: UNKNOWN, never another PC's record\n",
        "replace": "    except FileNotFoundError:\n"
                   "        try:\n"
                   "            with io.open(os.path.join(_fixture_root_for_state(), \".status_worst.json\"), "
                   "encoding=\"utf-8\") as fh:\n"
                   "                return json.load(fh)\n"
                   "        except Exception:\n"
                   "            return None\n",
        "matches": 1,
    },
    {
        "why": "REG-2461 - the console writes its slowest request into the tracked file again, which ships to every PC",
        "file": "control_app.py",
        "find": "        dest = _status_worst_path()\n",
        "replace": "        dest = os.path.join(_fixture_root_for_state(), \".status_worst.json\")\n",
        "matches": 1,
    },
    {
        "why": "REG-2462 - the epoch harness writes the tracked tv/.river_epoch.json again",
        "file": "river_epoch.py",
        "find": "EPOCH_PATH = os.path.join(HERE, \".river_epoch.here.json\")\n",
        "replace": "EPOCH_PATH = os.path.join(HERE, \".river_epoch.json\")\n",
        "matches": 1,
    },
    {
        "why": "REG-2461 - this PC's slowest-request record is trackable: one `git add -A` ships it to every PC",
        "file": "../.gitignore",
        "find": "\ntv/.status_worst.here.json\n",
        "replace": "\n",
        "matches": 1,
    },
    {
        "why": "REG-2462 - this PC's epoch record is trackable: one `git add -A` ships it to every PC",
        "file": "../.gitignore",
        "find": "\ntv/.river_epoch.here.json\n",
        "replace": "\n",
        "matches": 1,
    },
    {
        "why": "REG-2462 - the epoch is written in place again: a record dumps cannot serialise empties the last one",
        "file": "river_epoch.py",
        "find": "    text = json.dumps(ep, indent=1, ensure_ascii=False) + \"\\n\"\n"
                "    tmp = p + \".tmp\"\n"
                "    with io.open(tmp, \"w\", encoding=\"utf-8\") as fh:\n"
                "        fh.write(text)\n"
                "    os.replace(tmp, p)\n",
        "replace": "    io.open(p, \"w\", encoding=\"utf-8\").write(json.dumps(ep, indent=1, ensure_ascii=False) + \"\\n\")\n",
        "matches": 1,
    },
]
