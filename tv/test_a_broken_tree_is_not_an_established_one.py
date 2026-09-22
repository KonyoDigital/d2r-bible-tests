#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3410 — A BROKEN TREE IS NOT AN ESTABLISHED ONE, AND HALF A HARNESS IS NOT HALF A TREE.

Both laws were named by the CROSS-FAMILY REVIEW of v3405 (grok-cli, 2026-09-22) and then verified
and adversarially refuted against the real source. Recorded with their provenance because the
third finding of that review was REFUTED by measurement, and a reviewer that is right twice and
wrong once is worth more than one that is never checked.

⚠⚠ ONE: A FAILED CREATE WAS CACHED AS DONE. `machine_tree.establish()` reports a create or
prove-write failure as a ROW and never raises, so `_establish_footage()` stamping
`_FOOTAGE_ESTABLISHED` on the strength of "it returned" recorded a broken tree as an established
one. MEASURED with TV_HIST=/dev/null/nope/hist: establish() returned normally carrying
('frames/hist','failed','could not be created (NotADirectoryError)'), the stamp landed, and call
#2 was a CACHE HIT. Nothing in the tree ever clears that global, so `_archive_footage_copy` then
reaches `shutil.disk_usage()` on a directory that is not there, raises FileNotFoundError, and it
is swallowed as `return False` — every film frame dropped, silently, for the life of the process.
v3404's per-frame `os.makedirs(hist_dir, exist_ok=True)` used to heal that the moment a drive
remounted; v3405 removed it.

⚠⚠ TWO: HALF A HARNESS IS NOT HALF A TREE. With TV_FRAMES_DIR set and TV_HIST unset — exactly
`replay.py:217` spawning a tv_diablo child — establish()'s `if not p: continue` skipped the hist
root and reported total success, while `tv_diablo.py` still computes HIST_DIR = join(FRAMES,
"hist"). MEASURED: makedirs ['/tmp/SAND/frames'] only, HIST_DIR created False. Every archive from
boot then died on the missing directory, and `_FOOTAGE_WHY` still read 'grab', so the console
showed no reason and no disk-full.

⚠ THE ASYMMETRY IS THE WHOLE CARE. frames-set/hist-empty can be DERIVED (it stays inside the
harness's own scratch tree). hist-set/frames-empty CANNOT — frames would be the LIVE tree, and
provisioning that from inside an isolated harness is the risk machine_tree exists to prevent. So
one is derived and the other is REFUSED and named.

⚠ AND THE OBVIOUS FIX WAS THE DANGEROUS HALF, caught by the blast-radius skeptic before it
shipped: refusing to stamp on ANY bad row retries at FILM CADENCE, and on the live lane
establish() falls through to ensure(create=True) which walks ALL SIX roots — a prove-write storm
per frame. Worse, a REFUSED anchor is not transient and would be retried forever. Hence three
states, not two.
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import machine_tree as MT   # noqa: E402
import tv_diablo as TD      # noqa: E402


def _reset():
    for g in ("_FOOTAGE_ESTABLISHED", "_FOOTAGE_BROKEN_KEY", "_FOOTAGE_LAST_TRY"):
        TD.__dict__.pop(g, None)


class _Stub(object):
    """Stands in for machine_tree inside _establish_footage. Counts the calls."""
    FAILED, UNUSABLE, REFUSED = MT.FAILED, MT.UNUSABLE, MT.REFUSED
    CREATED, FOUND = MT.CREATED, MT.FOUND

    def __init__(self, rows):
        self.rows, self.calls = rows, 0

    def establish(self):
        self.calls += 1
        return list(self.rows)


def _drive(rows, times=1, retry_s=None):
    """Run _establish_footage() `times` with machine_tree stubbed. -> (calls, stamped)."""
    real = sys.modules.get("machine_tree")
    old_retry = TD._FOOTAGE_RETRY_S
    if retry_s is not None:
        TD._FOOTAGE_RETRY_S = retry_s
    stub = _Stub(rows)
    sys.modules["machine_tree"] = stub
    _reset()
    try:
        for _ in range(times):
            TD._establish_footage()
    finally:
        sys.modules["machine_tree"] = real
        TD._FOOTAGE_RETRY_S = old_retry
        stamped = TD.__dict__.get("_FOOTAGE_ESTABLISHED")
        _reset()
    return stub.calls, stamped


OK_ROWS = [{"root": "frames", "state": MT.CREATED}, {"root": "frames/hist", "state": MT.FOUND}]


class TestABrokenTreeIsNotAnEstablishedOne(unittest.TestCase):

    def test_BASELINE_a_healthy_establish_DOES_stamp(self):
        """Without this every refusal below would pass on a door that is simply jammed shut."""
        calls, stamped = _drive(OK_ROWS, times=2)
        self.assertEqual(calls, 1, "a healthy tree must be established ONCE and then cached")
        self.assertIsNotNone(stamped, "a healthy establish did not stamp the cache at all")

    def test_a_FAILED_row_does_NOT_stamp_the_cache(self):
        rows = OK_ROWS[:1] + [{"root": "frames/hist", "state": MT.FAILED,
                               "why": "could not be created (NotADirectoryError)"}]
        calls, stamped = _drive(rows, times=1)
        self.assertIsNone(stamped,
                          "a tree whose hist root FAILED was recorded as established — every "
                          "later archive then dies on a missing directory, silently, forever")

    def test_an_UNUSABLE_row_does_NOT_stamp_the_cache(self):
        rows = OK_ROWS[:1] + [{"root": "frames/hist", "state": MT.UNUSABLE,
                               "why": "a write does not land"}]
        _, stamped = _drive(rows, times=1)
        self.assertIsNone(stamped, "a root that exists but cannot be written was cached as fine")

    def test_a_broken_tree_IS_RETRIED_once_the_bound_has_passed(self):
        """⚠ the self-heal the removed per-frame makedirs used to give for free."""
        rows = OK_ROWS[:1] + [{"root": "frames/hist", "state": MT.FAILED, "why": "x"}]
        calls, _ = _drive(rows, times=3, retry_s=0.0)
        self.assertEqual(calls, 3,
                         "a broken tree was never re-attempted, so a drive that remounts never "
                         "heals until the process restarts")

    def test_the_retry_is_RATE_LIMITED_so_it_cannot_storm_at_film_cadence(self):
        """⚠ THE DANGEROUS HALF. establish() on the live lane walks ALL SIX roots and
        prove-writes each; doing that per frame is a storm, not a fix."""
        rows = OK_ROWS[:1] + [{"root": "frames/hist", "state": MT.FAILED, "why": "x"}]
        calls, _ = _drive(rows, times=5, retry_s=600.0)
        self.assertEqual(calls, 1,
                         "a broken tree was re-established %d times inside the bound — at film "
                         "cadence that is a prove-write storm on every frame" % calls)

    def test_a_REFUSED_row_DOES_stamp__a_refusal_is_not_transient(self):
        """⚠ Its anchor could not be established and will not become establishable by asking
        again. Retrying a refusal forever is the storm wearing a fix's clothes."""
        rows = OK_ROWS[:1] + [{"root": "frames/hist", "state": MT.REFUSED,
                               "why": "no anchor — will not guess a location"}]
        calls, stamped = _drive(rows, times=4, retry_s=600.0)
        self.assertIsNotNone(stamped, "a REFUSED root left the cache unstamped, so it is retried")
        self.assertEqual(calls, 1, "a refusal was re-asked %d times" % calls)

    def test_a_root_this_process_does_NOT_write_cannot_block_the_stamp(self):
        """Only frames and frames/hist are written here. A backup root's fault is someone
        else's lane and must not make the film retry forever."""
        rows = OK_ROWS + [{"root": "board_backups", "state": MT.FAILED, "why": "x"}]
        _, stamped = _drive(rows, times=1)
        self.assertIsNotNone(stamped,
                            "an unrelated root's failure blocked the footage cache")


class TestHalfAHarnessIsNotHalfATree(unittest.TestCase):

    def _establish(self, hist=None, frames=None):
        keep = {k: os.environ.get(k) for k in ("TV_HIST", "TV_FRAMES_DIR")}
        for k, v in (("TV_HIST", hist), ("TV_FRAMES_DIR", frames)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            return MT.establish()
        finally:
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_TV_FRAMES_DIR_alone_DERIVES_and_creates_the_hist_root(self):
        d = tempfile.mkdtemp(prefix="v3410frames_")
        f = os.path.join(d, "watch")
        rows = self._establish(frames=f)
        hist = os.path.join(f, "hist")
        got = {r["root"]: r for r in rows}
        self.assertIn("frames/hist", got,
                      "replay.py sets TV_FRAMES_DIR without TV_HIST; the hist root was skipped "
                      "entirely and establish() still reported success")
        self.assertTrue(os.path.isdir(hist),
                        "HIST_DIR (%s) is what tv_diablo writes to and the door never made it" % hist)
        self.assertNotEqual(got["frames/hist"]["state"], MT.REFUSED)

    def test_TV_HIST_alone_REFUSES_the_frames_root_by_name(self):
        """⚠ It cannot be derived: frames would be the LIVE tree."""
        d = tempfile.mkdtemp(prefix="v3410hist_")
        h = os.path.join(d, "hist")
        rows = self._establish(hist=h)
        got = {r["root"]: r for r in rows}
        self.assertIn("frames", got,
                      "the frames root was silently skipped — a root nobody established must "
                      "never read as one that was")
        self.assertEqual(got["frames"]["state"], MT.REFUSED)
        self.assertIsNone(got["frames"]["path"],
                          "a REFUSED root still named a path, which is the one outcome worse "
                          "than no tree")

    def test_BOTH_set_still_establishes_both_and_derives_nothing(self):
        d = tempfile.mkdtemp(prefix="v3410both_")
        f, h = os.path.join(d, "w"), os.path.join(d, "h")
        rows = self._establish(hist=h, frames=f)
        got = {r["root"]: r["state"] for r in rows}
        self.assertNotEqual(got.get("frames"), MT.REFUSED)
        self.assertNotEqual(got.get("frames/hist"), MT.REFUSED)
        self.assertTrue(os.path.isdir(f) and os.path.isdir(h))
        self.assertEqual(len([r for r in rows if r["root"] == "frames/hist"]), 1,
                         "the derived row and the env row were both reported")


RED_PROOF = [
    {
        "why": "v3410 — WITHOUT THE _hurt CHECK A FAILED TREE IS CACHED AS ESTABLISHED. "
               "establish() never raises on a create failure, so the stamp lands on the strength "
               "of 'it returned' and every later archive dies on a missing directory, swallowed, "
               "for the life of the process.",
        "file": "tv_diablo.py",
        "find": "    if _hurt:\n        globals()[\"_FOOTAGE_BROKEN_KEY\"] = key\n        return\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3410 — WITHOUT THE RATE LIMIT THE FIX BECOMES A STORM. On the live lane "
               "establish() falls through to ensure(create=True), which walks all six roots and "
               "prove-writes each; retrying that on every film frame costs more than the defect. "
               "This is the half the blast-radius skeptic killed before it shipped. ⚠ The first spelling of this tamper DELETED the two lines, which left the outer `if` with an empty body - heart2 called it INVALID, and it was right: a gate reddened by a SyntaxError proves nothing about the law. Flipping the comparison changes BEHAVIOUR and still parses.",
        "file": "tv_diablo.py",
        "find": "if (_now - (globals().get(\"_FOOTAGE_LAST_TRY\") or 0.0)) < _FOOTAGE_RETRY_S:",
        "replace": "if (_now - (globals().get(\"_FOOTAGE_LAST_TRY\") or 0.0)) > _FOOTAGE_RETRY_S:",
        "matches": 1,
    },
    {
        "why": "v3410 — WITHOUT THE DERIVE, replay.py's TV_FRAMES_DIR-only child gets a frames "
               "root and no hist root, while tv_diablo still computes HIST_DIR = join(FRAMES, "
               "'hist'). establish() reports total success and every archive from boot dies on "
               "the directory it never made.",
        "file": "machine_tree.py",
        "find": "        if frames and not hist:\n            hist = os.path.join(frames, \"hist\")\n",
        "replace": "        if False:\n            hist = os.path.join(frames, \"hist\")\n",
        "matches": 1,
    },
    {
        "why": "v3410 — WITHOUT THE REFUSED ROW the un-derivable half is SILENTLY SKIPPED, which "
               "is the one thing this module forbids: a root nobody established reading exactly "
               "like one that was.",
        "file": "machine_tree.py",
        "find": "                rows.append({\"root\": name, \"anchor\": \"env\", \"path\": None, \"state\": REFUSED,",
        "replace": "                continue\n                rows.append({\"root\": name, \"anchor\": \"env\", \"path\": None, \"state\": REFUSED,",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
