# -*- coding: utf-8 -*-
"""v3366 (#115) — A DEAD CAPTURE FOLDER IS NOT A FROZEN SCREEN.

MEASURED 2026-09-19, same code, two roots, minutes apart:

    root = ~/gb-shelf                 -> FROZEN   "1 of 17 comparable window series stopped
                                         painting (425 PNG(s) read)"   newest capture 178.9 h old
    root = <where the seat writes>    -> MOVING   "1 window series compared, all painting
                                         (2,692 PNG(s) read)"          newest capture  0.4 h old

The capture folder moved; this tool kept reading the old one; and a folder nobody writes to has a
newest-two that are BYTE-IDENTICAL BY CONSTRUCTION. So it reported a dead compositor for 7.5 days,
about a screen it was not looking at. [[stale-reading]] — a reading that was true once, served with
the confidence of something current.

=== THE FIX IS NOT THE PATH ===
Repointing the constant fixes today and rots the next time the seat moves. The durable fix is that
a verdict about HIS SCREEN may only be drawn from captures recent enough to be about now:
    · `newestAgeS` rides on EVERY verdict, so a reader can judge a MOVING or FROZEN answer without
      rerunning anything
    · a root staler than the bound answers UNKNOWN and NAMES the age — that is a statement about
      the RECORDER, and it must never share a word with a statement about the screen

⚠⚠ AND THE ARM MUST SIT ABOVE THE FROZEN ARM. Below it, `counts["frozen"]` wins first and the age
is computed, stored and never consulted — computed-and-dropped being this repo's most repeated
defect. Order is pinned by position, not by presence. [[the-unjoined-end]]

=== THE BOUND IS MEASURED, WITH ITS DENOMINATOR ===
Across 2,804 captures in the folder the seat actually writes, the gap between consecutive frames is
median 8.0 s, p90 58.0 s, p99 1,070 s, and the WORST gap in the whole history is 0.8 h. The dead
folder's newest capture was 178.9 h old — 220x that worst live gap. 2 h is ~2.5x the worst live
case and ~1/90th of the dead one, so it separates them by a wide margin rather than splitting them
finely. [[feedback-threshold-above-the-ceiling]] — a threshold above the ceiling is an absent one,
and one below the floor fires on everything.

⚠ FIXTURES ONLY. This law fabricates PNG headers in a temp dir and never reads his capture folders:
a test that needs his machine is a test that runs nowhere else. [[regression-guard]] §3
"""
import io
import os
import struct
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import frozen_frame_watch as W  # noqa: E402


def _png(path, w, h, payload=b"\x00"):
    """A file whose IHDR says WxH. `png_geometry` parses the header; the body only has to make two
    files byte-identical or not."""
    with io.open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", w, h))
        f.write(b"\x08\x06\x00\x00\x00" + payload)


def _root(age_s, identical=True, w=2376, h=1456):
    """A folder holding two captures of ONE window, `age_s` old, 60s apart."""
    d = tempfile.mkdtemp()
    a, b = os.path.join(d, "a.png"), os.path.join(d, "b.png")
    _png(a, w, h)
    _png(b, w, h, payload=b"\x00" if identical else b"\x01")
    now = time.time()
    os.utime(a, (now - age_s - 60, now - age_s - 60))
    os.utime(b, (now - age_s, now - age_s))
    return d


class AStaleRootCannotSpeakAboutHisScreen(unittest.TestCase):

    def test_a_root_older_than_the_bound_is_UNKNOWN_not_FROZEN(self):
        """⚠⚠ THE CASE. This exact input read FROZEN for 7.5 days."""
        r = W.report(root=_root(age_s=179 * 3600, identical=True))
        self.assertEqual(
            r["state"], W.UNKNOWN,
            "two byte-identical captures 179 HOURS old reported %s. Nothing has been written to "
            "that folder in a week — the newest two are identical by construction, and calling "
            "that a dead compositor is a claim about a screen nobody looked at." % r["state"])
        self.assertIn("RECORDER", r["why"],
                      "the verdict does not say this is about the recorder rather than the "
                      "screen, so a reader still takes it as evidence about his display: %r"
                      % r["why"][:160])

    def test_a_FRESH_root_still_reports_FROZEN(self):
        """⚠ THE BASELINE. Without it the arm could swallow every verdict and the law would pass
        over a detector that has stopped detecting. [[regression-guard]] §5"""
        r = W.report(root=_root(age_s=30, identical=True))
        self.assertEqual(
            r["state"], W.FROZEN,
            "two byte-identical captures 30 seconds apart in a LIVE folder came back %s. The "
            "staleness arm is now swallowing real findings, which is worse than the defect."
            % r["state"])

    def test_a_fresh_root_that_is_painting_still_reports_MOVING(self):
        r = W.report(root=_root(age_s=30, identical=False))
        self.assertEqual(r["state"], W.MOVING, "a painting screen came back %s" % r["state"])


class TheAgeRidesOnEveryVerdict(unittest.TestCase):

    def test_every_verdict_carries_the_age(self):
        for label, root in (("stale", _root(179 * 3600)),
                            ("fresh-frozen", _root(30)),
                            ("moving", _root(30, identical=False))):
            r = W.report(root=root)
            self.assertIn("newestAgeS", r,
                          "the %s verdict carries no age, so `root` is printed and its staleness "
                          "is not — which is how a dead folder and a frozen screen came to produce "
                          "the same word" % label)
            self.assertIsNotNone(r["newestAgeS"], "%s verdict has a null age over real files" % label)
        self.assertIn("staleBoundS", r, "the bound is not published beside the age, so a reader "
                                        "cannot tell how close to stale a verdict is")

    def test_an_empty_folder_has_NO_age_rather_than_zero(self):
        """[[unknown-stays-unknown]] — 0 would read as 'a capture just arrived'."""
        d = tempfile.mkdtemp()
        self.assertIsNone(W.newest_capture_age_s(d),
                          "an empty folder reported an age. 0 seconds means a capture landed this "
                          "instant, which is the opposite of the truth")
        r = W.report(root=d)
        self.assertIsNone(r["newestAgeS"])


class TheArmSitsAboveTheFrozenArm(unittest.TestCase):
    """⚠⚠ Below it, counts['frozen'] wins and the age is computed and never consulted."""

    def test_the_stale_arm_is_evaluated_first(self):
        src = io.open(os.path.join(HERE, "frozen_frame_watch.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        i_stale = code.find("_age_s > STALE_ROOT_S")
        i_frozen = code.find('elif counts["frozen"]:')
        self.assertGreater(i_stale, -1, "the staleness arm is gone")
        self.assertGreater(i_frozen, -1, "the frozen arm is gone")
        self.assertLess(
            i_stale, i_frozen,
            "the staleness arm sits BELOW the frozen arm (stale at %d, frozen at %d), so "
            "counts['frozen'] decides first and the age is computed, stored and never consulted."
            % (i_stale, i_frozen))

    def test_the_bound_is_above_the_worst_observed_live_gap(self):
        """A bound under the real cadence fires on healthy folders; one far above never fires.
        Worst observed live gap: 0.8 h. Dead folder: 178.9 h."""
        self.assertGreater(W.STALE_ROOT_S, 0.8 * 3600,
                           "the bound is at or below the worst gap seen in a LIVE folder, so a "
                           "healthy capture stream would be declared stale")
        self.assertLess(W.STALE_ROOT_S, 24 * 3600,
                        "the bound is a day or more, so a folder that died yesterday still speaks "
                        "with full confidence about his screen")


class OneResolverForBothModules(unittest.TestCase):
    """[[copy-drift]] — pointing one must point the other."""

    def test_both_modules_agree_WITHOUT_an_env_too(self):
        """⚠⚠ THE CASE v3366 DID NOT HAVE, AND THE HALF-FIX IT LET THROUGH.

        v3366 taught frozen_frames to honour TV_GB_SHELF and left its FALLBACK hardcoded. Measured
        on the shipped tree:

            env set    watch -> /tmp/fixture      frames -> /tmp/fixture     agreed
            NO env     watch -> verify-evidence   frames -> ~/gb-shelf       DISAGREED

        So on the path most runs actually take, one module read the live folder and the other read
        the abandoned one — the exact defect this file exists about, surviving inside its own fix.
        Checking only the overridden path is what let it through. [[copy-drift]]
        """
        import frozen_frames as F
        saved = os.environ.pop("TV_GB_SHELF", None)
        try:
            a = os.path.realpath(W.shelf_dir())
            b = os.path.realpath(F.default_dir())
        finally:
            if saved is not None:
                os.environ["TV_GB_SHELF"] = saved
        self.assertEqual(
            a, b,
            "with NO env set the two modules resolve DIFFERENT capture folders:\n"
            "    frozen_frame_watch -> %s\n    frozen_frames      -> %s\n"
            "One resolver means one resolver on both paths, not only the overridden one." % (a, b))

    def test_it_resolves_at_CALL_time_not_at_import(self):
        """⚠ A module constant is evaluated once at load, so an env set afterwards never takes —
        the redirect that silently does not apply. [[stale-reading]]"""
        import frozen_frames as F
        saved = os.environ.get("TV_GB_SHELF")
        os.environ["TV_GB_SHELF"] = "/tmp/set-after-import-xyz"
        try:
            got = os.path.realpath(F.default_dir())
        finally:
            if saved is None:
                os.environ.pop("TV_GB_SHELF", None)
            else:
                os.environ["TV_GB_SHELF"] = saved
        self.assertEqual(
            got, os.path.realpath("/tmp/set-after-import-xyz"),
            "an env set AFTER import did not take (%s) — the value is frozen at module load, so a "
            "test or caller redirecting it is silently ignored" % got)

    def test_frozen_frames_honours_the_same_env(self):
        src = io.open(os.path.join(HERE, "frozen_frames.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            'os.environ.get("TV_GB_SHELF")', code,
            "frozen_frames still hardcodes the capture folder with no override, so redirecting "
            "frozen_frame_watch redirects only half the tooling — which is how one could be "
            "pointed at a fixture while the other read a folder dead for 7.5 days")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "moving the stale arm below the frozen arm lets a dead folder report FROZEN again",
        "file": "tv/frozen_frame_watch.py",
        "find": "    elif _age_s is not None and _age_s > STALE_ROOT_S:",
        "replace": "    elif False:",
        "matches": 1,
    },
    {
        "why": "an empty folder reporting age 0 reads as a capture that just landed",
        "file": "tv/frozen_frame_watch.py",
        "find": "    if newest is None:\n        return None",
        "replace": "    if newest is None:\n        return 0.0",
        "matches": 1,
    },
    {
        "why": "dropping the age from the verdict puts root back on screen with no staleness beside it",
        "file": "tv/frozen_frame_watch.py",
        "find": '            "newestAgeS": (round(_age_s, 1) if _age_s is not None else None),',
        "replace": "",
        "matches": 1,
    },
    {
        # ⚠ v3367 — THE PROOF FOR THE HALF-FIX v3366 SHIPPED. It taught the env path and left the
        # FALLBACK hardcoded, so with NO env set the two modules read DIFFERENT folders and one of
        # them was the dead one. Only testing BOTH paths found it.
        "why": "returning the hardcoded fallback puts frozen_frames back on the dead folder whenever no env is set - the path most runs take",
        "file": "tv/frozen_frames.py",
        "find": "        import frozen_frame_watch as _w\n        return _w.shelf_dir()",
        "replace": '        return os.path.expanduser("~/gb-shelf")',
        "matches": 1,
    },
    # ⚠⚠ RETIRED IN v3367, DELIBERATELY — ITS SUBJECT MOVED. This proof tampered
    # `DEFAULT_DIR`, which v3366 had taught to read the env. v3367 made the CLI call
    # `default_dir()` instead, resolving at CALL time through the ONE shared resolver, so
    # DEFAULT_DIR is no longer consulted by anything the law checks — and the string this proof
    # removed still survives inside default_dir()'s own fallback, which is why it went BLIND at
    # match count 1 rather than at 0. An INERT sabotage, caused by the code moving underneath it.
    # The proof directly above replaces it and tampers the live path.
    # Retired, not deleted-in-silence: a premise that changed must be retired on purpose.
    # [[regression-guard]] §4 · [[source-reading-guard]] §4c cause (3)
]
