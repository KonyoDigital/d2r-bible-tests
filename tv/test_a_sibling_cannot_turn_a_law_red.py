# -*- coding: utf-8 -*-
"""#160 critic R3 (REG-2439) - A SIBLING PROVER CANNOT TURN A BLIND LAW RED, SO IT CANNOT MAKE ONE PROVEN.

Two provers now run side by side on one machine by design (his self-prover's census and a push, each with its lanes,
up to two Chromes). A tampered run that goes red is credited as the law catching the tamper - but a sibling's write into
a temp dir both runs share, or onto anything else both can reach, turns a run red just as well, and a blind law then
reads PROVEN and is banked. So:
  · every law run in a sandbox heart2 built gets a TMPDIR/TEMP/TMP of its own inside that sandbox (removed after the
    run), and D2R_REPO naming the sandbox (board_sync defaulted to the real checkout);
  · under concurrency - another prover holds a slot, or a browser gate shares the machine with K > 1 - a tampered red is
    a verdict only when it goes red AGAIN when asked a second time (its named red cases, else the whole run); the
    narrowed pair's tampered half the same.

Driven through the REAL _prove_one / _prove_narrow / _run_gate / _run_gate_once over a fixture law in a sandbox heart2
tracks; the "sibling" is a write made only while the tampered run is running:
  1. a sibling's file in the SHARED temp dir does not reach the law's run - a blind law stays BLIND; the run's TMPDIR is
     inside its sandbox and its D2R_REPO is the sandbox's repo;
  2. under concurrency, a red the sibling caused once is not confirmed - UNPROVABLE, never PROVEN; a law that really
     catches the tamper is PROVEN, confirmed;
  3. the same for the narrowed pair: an unconfirmed narrowed red decides nothing, and the full proof finds the law BLIND.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2 as H  # noqa: E402

#: the fixture law: red when a flag a sibling might write exists - in its temp dir (SHARED_FLAG_NAME) or at an absolute
#: path both provers can reach (SIBLING_FLAG); Catches.test_catch reddens on "BROKEN" (a real catch). It records what it
#: was given as its temp dir and its repo.
_LAW = r'''
import io, json, os, sys, tempfile, unittest
here = os.path.dirname(os.path.abspath(__file__))


def _subject():
    with io.open(os.path.join(here, "sub" + "ject.txt"), encoding="utf-8") as fh:
        return fh.read()


class Sibling(unittest.TestCase):
    def test_no_flag_in_my_temp_dir(self):
        self.assertFalse(os.path.exists(os.path.join(tempfile.gettempdir(), "sibling.flag")))

    def test_no_flag_where_both_reach(self):
        p = os.environ.get("SIBLING_FLAG")
        self.assertFalse(p and os.path.exists(p))


class Catches(unittest.TestCase):
    def test_catch(self):
        if os.environ.get("LAW_CATCHES"):
            self.assertNotIn("BROKEN", _subject())


if __name__ == "__main__":
    rec = os.environ.get("SIBLING_REC")
    if rec:
        with io.open(rec, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"tmp": tempfile.gettempdir(), "repo": os.environ.get("D2R_REPO")}) + "\n")
    unittest.main()
'''
_FILE = "t_sibling_law.py"
PROOF = {"why": "fixture", "file": "subject.txt", "find": "fine", "replace": "BROKEN", "matches": 1}


class _Case(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="sibling_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.root = os.path.join(self.d, "box")                   # a sandbox heart2 tracks, as make_sandbox's
        self.tv = os.path.join(self.root, "repo", "tv")
        os.makedirs(self.tv)
        for name, text in ((_FILE, _LAW), ("subject.txt", "all fine here\n")):
            with io.open(os.path.join(self.tv, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        H._track_sandbox(self.root)
        self.addCleanup(H._SANDBOXES.discard, self.root)
        self.flag = os.path.join(self.d, "sibling.flag")         # where both "provers" reach
        self.shared = os.path.join(tempfile.gettempdir(), "sibling.flag")
        self.rec = os.path.join(self.d, "rec.jsonl")
        self.saved = dict((k, getattr(H, k)) for k in ("_run_gate", "_SLOT", "_others_proving", "_PUSH", "_CENSUS",
                                                       "RED_MEMORY", "_RED", "_RED_USED"))
        self.addCleanup(lambda: [setattr(H, k, v) for k, v in self.saved.items()])
        self.env = dict((k, os.environ.get(k)) for k in ("SIBLING_FLAG", "SIBLING_REC", "LAW_CATCHES",
                                                         "HEART2_RED_MEMORY", "HEART2_RED_PATH"))
        self.addCleanup(self._restore_env)
        os.environ.update(SIBLING_FLAG=self.flag, SIBLING_REC=self.rec)
        os.environ.pop("LAW_CATCHES", None)
        os.environ.pop("HEART2_RED_PATH", None)
        os.environ["HEART2_RED_MEMORY"] = "0"
        self.said, self.calls = [], 0

    def _restore_env(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def sibling_writes_during(self, call_no, path):
        """The "sibling": `path` exists only while run number `call_no` of this proof is running."""
        real = self.saved["_run_gate"]

        def spy(sandbox_tv, filename, timeout=180, extra=(), script=None, widths=None):
            self.calls += 1
            if self.calls == call_no:
                with io.open(path, "w") as fh:
                    fh.write("a sibling was here")
            try:
                return real(sandbox_tv, filename, timeout=timeout, extra=extra, script=script, widths=widths)
            finally:
                if self.calls == call_no and os.path.exists(path):
                    os.remove(path)
        H._run_gate = spy

    def concurrency(self):
        """Another prover holds a slot on this machine (the probe of the slot files, answered)."""
        H._SLOT = {"n": 0}
        H._others_proving = lambda: [1]

    def prove(self):
        return H._prove_one(self.tv, "sibling-fixture", _FILE, dict(PROOF), 0, self.said.append)


class ASiblingCannotTurnALawRed(_Case):

    def test_a_sibling_file_in_the_shared_temp_dir_never_reaches_a_law_run(self):
        self.sibling_writes_during(2, self.shared)               # call 1 clean, call 2 tampered
        self.assertEqual(self.prove(), H.BLIND,
                         "a sibling's file in the SHARED temp dir turned a blind law's tampered run red: %s" % self.said)
        with io.open(self.rec, encoding="utf-8") as fh:
            seen = [json.loads(l) for l in fh if l.strip()]
        for r in seen:
            self.assertTrue(os.path.realpath(r["tmp"]).startswith(os.path.realpath(self.root) + os.sep),
                            "a law run's TMPDIR is not inside its sandbox: %s" % r)
            self.assertEqual(os.path.realpath(r["repo"] or ""), os.path.realpath(os.path.join(self.root, "repo")),
                             "a law run's D2R_REPO is not its sandbox's repo: %s" % r)

    def test_under_concurrency_an_unconfirmed_red_is_never_proven(self):
        self.concurrency()
        self.sibling_writes_during(2, self.flag)
        self.assertEqual(self.prove(), H.UNPROVABLE,
                         "a red a sibling caused once was credited to the law: %s" % self.said)
        self.assertTrue(any("under concurrency" in l and "another prover holds slot(s) 1" in l for l in self.said),
                        self.said)
        self.assertEqual(self.calls, 3, "the red was not asked a second time")

    def test_under_concurrency_a_real_catch_is_confirmed_and_proven(self):
        self.concurrency()
        os.environ["LAW_CATCHES"] = "1"
        self.sibling_writes_during(0, self.flag)                 # no sibling at all
        self.assertEqual(self.prove(), H.PROVEN, self.said)
        self.assertEqual(self.calls, 3, "PREMISE: the red was not confirmed by a second tampered run")

    def test_under_concurrency_an_unconfirmed_narrowed_red_decides_nothing(self):
        self.concurrency()
        H._RED, H._RED_USED = {"path": None, "sig": None, "entries": None, "folded": True}, {}
        H.RED_MEMORY = os.path.join(self.d, ".heart2_red.json")
        os.environ.pop("HEART2_RED_MEMORY", None)
        H._red_remember(H._red_key("sibling-fixture", 0, PROOF), "sibling-fixture", 0, ["Sibling.test_no_flag_where_both_reach"])

        class _Push(object):
            browser = set()
        H._PUSH = _Push()                                        # the push narrows before any clean run
        self.sibling_writes_during(2, self.flag)                 # call 1 narrowed clean, call 2 narrowed tampered
        self.assertEqual(self.prove(), H.BLIND,
                         "a narrowed red a sibling caused once decided the proof: %s" % self.said)


RED_PROOF = [
    {"why": "#160 - a law run shares the prover's TMPDIR again: a sibling's file there turns a blind law PROVEN",
     "file": "heart2.py",
     "find": "            env[\"TMPDIR\"] = env[\"TEMP\"] = env[\"TMP\"] = _run_tmp          # PRIVATE-TMPDIR\n",
     "replace": "            pass\n",
     "matches": 1},
    {"why": "#160 critic R3 - an unconfirmed red under concurrency is accepted: a sibling's one write banks a blind law",
     "file": "heart2.py",
     "find": "        if _again is not False:                  # CONFIRM-RED\n",
     "replace": "        if False:                  # CONFIRM-RED\n",
     "matches": 1},
    {"why": "#160 critic R3 - the narrowed pair accepts an unconfirmed red under concurrency",
     "file": "heart2.py",
     "find": "    if ok_t is False and _concurrent(_gname) and _confirm_red(",
     "replace": "    if False and _concurrent(_gname) and _confirm_red(",
     "matches": 1},
    {"why": "#160 - board_sync in a law run defaults to the REAL checkout: a sandboxed run writes his TASKS.md",
     "file": "heart2.py",
     "find": "        env[\"D2R_REPO\"] = os.path.dirname(os.path.abspath(sandbox_tv))\n",
     "replace": "        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
