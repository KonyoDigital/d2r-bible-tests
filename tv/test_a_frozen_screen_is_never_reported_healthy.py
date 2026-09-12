#!/usr/bin/env python3
"""v2995 — A PAGE THAT ANSWERS 200 CAN PAINT NOTHING.

Measured on his machine 2026-09-10 from Grok Bot's captures: at 19:08 the TV DIABLO window was a
DARK BLANK, at 16:16 a WHITE BLANK — titlebar and nothing else — while every text check reported
`GET / 200`, `GET /api/status 200`, "quiet hold - HEART census held - did not kill". A detector
that ASKS THE PAGE cannot fire on a dead compositor. frozen_frame_watch asks the bytes.

★ WHAT THIS GATE IS REALLY FOR. The detector is three lines of shasum and an ocean of ways to be
confidently wrong, and its first real run produced THREE false positives that all looked like a
dead console:

    2940x1846  gap=0.0s     shelf-final-B-matched.png == shelf3-try2-B-...Z.png   a FILE COPY
    2160x1500  gap=0.1s     shelf-final-stage-B.png   == shelf-final-stage-A.png  0.1s apart
    280x280    gap=6407.0s  cursor-onair-ref.png      == cursor-onair.png         a REFERENCE COPY

A copied file is byte-identical to its source by definition; two captures a tenth of a second
apart are identical on a perfectly healthy screen; and a 280x280 crop is not a window at all.
Every test below pins one of those, because the detector going green is worthless and the
detector crying wolf is worse — he learns to skip it, and then it is not there.
[[feedback-suspect-the-instrument]] [[feedback-blind-fixture-green-gate]]
"""
import os
import shutil
import struct
import sys
import tempfile
import time
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import frozen_frame_watch as F  # noqa: E402


def _png(path, w, h, fill=0):
    """Write a minimal valid 8-bit greyscale PNG. -> path

    ⚠ HAND-BUILT, because the gate must run on CI where Pillow is not installed and `sips` does
    not exist. A fixture that cannot be created on the venue is a test that silently does not run.
    [[test-venue]]
    """
    raw = b"".join(b"\x00" + bytes([fill]) * w for _ in range(h))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return path


class AFrozenScreenIsNeverReportedHealthy(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="frozenwatch.")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.now = time.time()

    def _at(self, name, w, h, fill, ago):
        p = _png(os.path.join(self.d, name), w, h, fill)
        t = self.now - ago
        os.utime(p, (t, t))
        return p

    # ── the finding it exists to make ─────────────────────────────────────────────────────────
    def test_two_identical_window_frames_across_a_real_gap_are_frozen(self):
        self._at("a.png", 1280, 800, 7, 60)
        self._at("b.png", 1280, 800, 7, 10)      # identical bytes, 50s later
        r = F.report(self.d, now=self.now)
        self.assertEqual(r["state"], F.FROZEN,
                         "two byte-identical captures of the same window 50s apart is a screen "
                         "that stopped painting; got %s — %s" % (r["state"], r["why"]))

    def test_a_painting_screen_is_moving(self):
        self._at("a.png", 1280, 800, 7, 60)
        self._at("b.png", 1280, 800, 9, 10)      # different bytes
        self.assertEqual(F.report(self.d, now=self.now)["state"], F.MOVING)

    # ── the three ways it was wrong on its first real run ─────────────────────────────────────
    def test_a_copied_file_is_not_a_frozen_screen(self):
        """gap=0.0s — identical because one IS the other. This must never read as a dead console."""
        self._at("orig.png", 1280, 800, 7, 30)
        self._at("copy.png", 1280, 800, 7, 30)   # same bytes AND same mtime
        r = F.report(self.d, now=self.now)
        self.assertNotEqual(r["state"], F.FROZEN,
                            "a file copied from another is byte-identical by definition and says "
                            "nothing about the compositor — %s" % r["why"])

    def test_two_captures_too_close_together_decide_nothing(self):
        """gap=0.1s — a healthy screen is identical over a tenth of a second."""
        self._at("a.png", 1280, 800, 7, 30.0)
        self._at("b.png", 1280, 800, 7, 29.9)
        r = F.report(self.d, now=self.now)
        self.assertEqual(r["state"], F.UNKNOWN,
                         "frames %.1fs apart cannot distinguish a frozen screen from a healthy "
                         "one; the honest answer is UNKNOWN, got %s" % (0.1, r["state"]))

    def test_identical_crops_are_not_a_window_verdict(self):
        """280x280 reference copies are not evidence about a compositor."""
        self._at("cursor.png", 280, 280, 7, 6000)
        self._at("cursor-ref.png", 280, 280, 7, 10)
        r = F.report(self.d, now=self.now)
        self.assertNotEqual(r["state"], F.FROZEN,
                            "a 280x280 crop is not a window — %s" % r["why"])
        self.assertTrue(r["counts"]["cropFrames"] >= 2,
                        "and the excluded frames must be COUNTED, not silently dropped")

    # ── absence must never read as health ─────────────────────────────────────────────────────
    def test_a_missing_shelf_is_unknown_not_clean(self):
        r = F.report(os.path.join(self.d, "does-not-exist"), now=self.now)
        self.assertEqual(r["state"], F.UNKNOWN,
                         "on CI, and on any machine that is not his, there are no captures. A "
                         "detector that returns healthy when it read nothing is the defect.")

    def test_an_empty_shelf_is_unknown_not_clean(self):
        self.assertEqual(F.report(self.d, now=self.now)["state"], F.UNKNOWN)

    def test_one_lone_frame_decides_nothing(self):
        self._at("only.png", 1280, 800, 7, 10)
        self.assertEqual(F.report(self.d, now=self.now)["state"], F.UNKNOWN)

    # ── the verdict must carry its own denominator ────────────────────────────────────────────
    def test_the_report_publishes_what_it_measured(self):
        self._at("a.png", 1280, 800, 7, 60)
        self._at("b.png", 1280, 800, 9, 10)
        self._at("crop.png", 280, 280, 1, 10)
        c = F.report(self.d, now=self.now)["counts"]
        for k in ("pngs", "standing", "frozen", "cropFrames"):
            self.assertIn(k, c, "the verdict must say how much it looked at, or the state is an "
                                "assertion rather than a measurement")
        self.assertEqual(c["pngs"], 3)

    def test_geometry_is_parsed_without_sips_or_pillow(self):
        p = self._at("x.png", 321, 123, 4, 1)
        self.assertEqual(F.png_geometry(p), (321, 123))
        self.assertIsNone(F.png_geometry(os.path.join(self.d, "nope.png")))

    def test_a_frozen_verdict_never_claims_the_screen_is_blank(self):
        """FROZEN is measured from bytes. BLANK is a claim about CONTENT that needs an eye.

        ⚠ MY FIRST CUT OF THIS TEST ASSERTED `"is blank" not in why` AND WENT RED ON THE
        DISCLAIMER — the module says "that it is FROZEN is measured; that it is BLANK is not",
        which is precisely the right thing to say, and a substring match cannot tell a denial from
        a claim. Testing prose by substring is how a correct sentence fails a test.
        [[measured-true-read-wrong]] [[source-reading-guard]]
        """
        self._at("a.png", 1280, 800, 7, 60)
        self._at("b.png", 1280, 800, 7, 10)
        r = F.report(self.d, now=self.now)
        self.assertEqual(r["state"], F.FROZEN)
        self.assertNotIn("BLANK", (F.FROZEN, F.MOVING, F.UNKNOWN),
                         "there must be no BLANK state — the module cannot see content")
        why = " ".join(x.get("why", "") for x in r["series"] if x["state"] == F.FROZEN)
        self.assertIn("needs an eye", why,
                      "a FROZEN verdict must say out loud that blankness is NOT what it measured, "
                      "so a reader cannot promote it into a claim about content")


class TheDoctorActuallyAsksTheDetector(unittest.TestCase):
    """⚠⚠ v2998 — BOTH v2995 GATES TESTED THE DETECTOR AND NEITHER TOUCHED THE DOCTOR. All three
    of this file's red-proofs targeted frozen_frame_watch.py alone, so deleting the CHECKS row
    would have left every test green with the detector built and nobody calling it — this repo's
    single most repeated defect, shipped inside the very gate meant to close it. The STALE_S
    freshness rule had no test AT ALL, which is why the bug below lived long enough to reach main.
    [[the-unjoined-end]] [[plumbing-with-no-tap]]"""

    ROW = "screen still painting"

    def test_the_doctor_carries_a_screen_painting_row(self):
        """⚠ IMPORTED AND READ AS DATA, NOT GREPPED — the words appear in prose all over that
        file. CHECKS is what the runner consumes. [[source-reading-guard]]"""
        import console_doctor as cd
        names = [n for n, _fn in cd.CHECKS]
        self.assertEqual(names.count(self.ROW), 1,
                         "console_doctor.CHECKS must carry exactly one %r row; it carries %d"
                         % (self.ROW, names.count(self.ROW)))
        self.assertTrue(callable([fn for n, fn in cd.CHECKS if n == self.ROW][0]))

    def _verdict(self, series, counts=None):
        """Run the doctor row against a stubbed detector report. -> (state, why)"""
        import console_doctor as cd
        import frozen_frame_watch as FFW
        rep = {"state": (FFW.FROZEN if any(x["state"] == FFW.FROZEN for x in series)
                         else FFW.MOVING),
               "why": "stub", "series": series,
               "counts": counts or {"pngs": 383, "standing": len(series), "frozen": 0,
                                    "cropFrames": 0, "cropGeometries": 0}}
        real = FFW.report
        FFW.report = lambda *a, **k: rep
        try:
            return cd._check_the_screen_is_still_painting()
        finally:
            FFW.report = real

    def test_a_stale_freeze_is_not_reported_as_a_live_fault(self):
        """⚠⚠ THE BUG, REPRODUCED BEFORE IT WAS FIXED. The freshness guard took the MINIMUM ageS
        across ALL series, so a frozen series five hours old was graded live whenever ANY other
        geometry had a recent capture: min(120, 18000) = 120, the stale branch never fired, and
        the doctor returned MISSING 'HIS SCREEN STOPPED PAINTING' about a screen that had been
        repainting for five hours. The freshness of a verdict is the age of the EVIDENCE IT RESTS
        ON. [[stale-reading]]"""
        import frozen_frame_watch as FFW
        state, why = self._verdict([
            {"geom": "2376x1456", "frames": 95, "state": FFW.MOVING, "ageS": 120.0, "gapS": 25.0},
            {"geom": "2940x1846", "frames": 83, "state": FFW.FROZEN, "ageS": 18000.0,
             "gapS": 30.0, "sha": "deadbeef1234", "newest": "a.png", "previous": "b.png"},
        ])
        self.assertEqual(state, "unknown",
                         "a freeze whose newest frame is 5h old says nothing about the screen NOW, "
                         "however fresh some unrelated geometry is; got %s — %s" % (state, why))

    def test_the_freshest_frozen_series_governs_not_the_one_with_most_frames(self):
        """⚠⚠ TWICE NOW THE FRESHNESS QUESTION WAS ANSWERED BY WHATEVER SORTED FIRST. v2998 took
        min(ageS) over ALL series; v3001 took `frozen[0]` — and report() sorts by -len(rows), never
        by age. Reproduced: a 95-frame freeze 5h old beside a 12-frame freeze 60 SECONDS old
        returned UNKNOWN, and the live fault this row exists for was never reported."""
        import frozen_frame_watch as FFW
        state, why = self._verdict([
            {"geom": "2376x1456", "frames": 95, "state": FFW.FROZEN, "ageS": 18000.0,
             "gapS": 30.0, "sha": "stale1234567", "newest": "a", "previous": "b"},
            {"geom": "2940x1846", "frames": 12, "state": FFW.FROZEN, "ageS": 60.0,
             "gapS": 30.0, "sha": "live12345678", "newest": "c", "previous": "d"},
        ])
        self.assertEqual(state, "missing",
                         "a freeze measured 60s ago is live evidence however many frames some "
                         "older geometry has; got %s — %s" % (state, why))
        self.assertIn("2940x1846", why, "and it must name the FRESH series, not the stale one")

    def test_an_ok_verdict_excludes_series_too_old_to_speak_for_now(self):
        """⚠ THE MIRROR OF THE SAME BUG. An OK here is a claim about EVERY series, so it cannot
        rest on the freshest: one window captured 2 minutes ago and another untouched for 5 hours
        returned 'all painting' — a clean bill for a window nobody had looked at since morning."""
        import frozen_frame_watch as FFW
        state, why = self._verdict([
            {"geom": "2376x1456", "frames": 95, "state": FFW.MOVING, "ageS": 120.0, "gapS": 25.0},
            {"geom": "2940x1846", "frames": 83, "state": FFW.MOVING, "ageS": 18000.0, "gapS": 30.0},
        ])
        self.assertEqual(state, "ok")
        self.assertIn("1 window series compared", why,
                      "the claim must cover only what it can actually speak for")
        self.assertIn("excluded", why,
                      "and the series it could NOT speak for must be counted out loud, or the "
                      "denominator is a lie")

    def test_every_series_stale_is_unknown_not_a_clean_bill(self):
        import frozen_frame_watch as FFW
        state, _why = self._verdict([
            {"geom": "2376x1456", "frames": 95, "state": FFW.MOVING, "ageS": 18000.0, "gapS": 25.0},
        ])
        self.assertEqual(state, "unknown",
                         "with nothing recent enough to judge, a clean bill has no evidence")

    def test_a_fresh_freeze_is_still_reported(self):
        """The other direction, or the fix above would be a way of never firing at all."""
        import frozen_frame_watch as FFW
        state, why = self._verdict([
            {"geom": "2376x1456", "frames": 95, "state": FFW.FROZEN, "ageS": 60.0, "gapS": 25.0,
             "sha": "deadbeef1234", "newest": "a.png", "previous": "b.png"},
        ])
        self.assertEqual(state, "missing",
                         "a freeze measured a minute ago IS the fault this row exists for; "
                         "got %s — %s" % (state, why))


RED_PROOF = [
    {
        "why": "removing the CHECKS row rebuilds the defect this whole file exists to close: the "
               "detector present, correct, and called by nobody",
        "file": "console_doctor.py",
        "find": '    ("screen still painting", _check_the_screen_is_still_painting),\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "taking the FIRST frozen series instead of the freshest silences a 60-second-old "
               "freeze whenever an older geometry happens to carry more frames — report() sorts "
               "by frame count and never by age",
        "file": "console_doctor.py",
        "find": "        f = min(frozen, key=lambda x: x.get(\"ageS\"))",
        "replace": "        f = frozen[0]",
        "matches": 1,
    },
    {
        "why": "letting stale series back into the OK claim restores the clean bill for a window "
               "nobody has looked at in five hours",
        "file": "console_doctor.py",
        "find": "    fresh = [x for x in _series if x.get(\"ageS\") <= STALE_S]",
        "replace": "    fresh = list(_series)",
        "matches": 1,
    },
    {
        "why": "removing the independence walk makes the detector compare the newest frame with "
               "whatever is next in the list — including a copy of itself — so a copied file "
               "reads as a dead compositor again",
        "file": "frozen_frame_watch.py",
        "find": "            if (a[\"mtime\"] - cand[\"mtime\"]) >= MIN_GAP_S:",
        "replace": "            if True:",
        "matches": 1,
    },
    {
        "why": "letting a missing capture folder report MOVING turns 'I read nothing' into a "
               "clean bill of health, which is the whole defect this file exists to refuse",
        "file": "frozen_frame_watch.py",
        "find": "        state, why = UNKNOWN, (\"the capture folder does not exist here",
        "replace": "        state, why = MOVING, (\"the capture folder does not exist here",
        "matches": 1,
    },
    {
        "why": "dropping the window floor lets 280x280 reference crops back into the window "
               "verdict, which is how a cursor thumbnail became a frozen console",
        "file": "frozen_frame_watch.py",
        "find": "        if geom[0] < MIN_WINDOW_W or geom[1] < MIN_WINDOW_H:",
        "replace": "        if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠ HIS CONSOLE IS cp1255 AND CANNOT ENCODE THE ARROWS AND STARS THIS FILE PRINTS. Without
    # this, a CORRECT tree reports FAILURE because the process dies inside its own print — the
    # dangerous direction, because it teaches people to ignore the tool. [[REG-044/054/077]]
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
