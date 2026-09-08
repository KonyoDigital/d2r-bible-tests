#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2799 — THE LIVE FRAME WAS STAT-ED IN ONE PLACE AND OPENED IN ANOTHER, AND THE CAPTURE MOVES IT.

⚠⚠ WHAT IT COST, 2026-09-08. He pressed MINI AUTO and it refused. The reason, once v2798's toast
finally made refusals visible where he was standing:

    "the grid could not be located on this frame: unreadable:
     [Errno 2] No such file or directory: '.../tv/frames/eye…'"

`_mini_cells_from_live_frame` picked the newest EXISTING label out of
(eye.jpg, live.jpg, live.png, live.bmp) with `os.path.isfile`, then handed the PATH to
`vault_corpus.inventory_lattice()`, which opens it LATER. The capture promotes eye.jpg by replacing
it, so between the stat and that open there is a window where the file does not exist.

That is why MINI AUTO alternated between two different complaints — "the newest frame is Ns old"
and "the grid could not be located" — depending purely on whether a promote was in flight. Two
faces of ONE missing file. MEASURED with no capture running: eye.jpg ABSENT, live.jpg present and
274s old; with a capture running, eye.jpg exists and is newest, and the race is live.

=== ⛔ WHY READING THE BYTES WAS NOT ENOUGH, AND I NEARLY SHIPPED THAT ===
My first cut read the bytes here and then passed the PATH onward anyway — plumbing with no tap. The
read would prove the file existed a moment ago and the readers would still race it. Checked and
confirmed: `inventory_lattice(frame_path)` and `inventory_occupancy(frame_path, lat)` BOTH open what
they are given and neither accepts bytes. So the bytes are written to a private snapshot and the
SNAPSHOT is what travels. [[the-unjoined-end]]

=== ⚠ NOT A WIDER AGE BOUND ===
The obvious "fix" is to relax the 10s freshness rule. That would be treating a race as slowness: the
file's ABSENCE was the event, never its age, and widening the bound would have hidden it for good.
[[feedback-threshold-above-the-ceiling]]
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

FN = "_mini_cells_from_live_frame"


class TheLiveFrameCannotBePulledMidRead(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.frames = os.path.join(self.d, "frames")
        os.makedirs(self.frames, exist_ok=True)
        self._here = CA.HERE
        CA.HERE = self.d          # the function joins HERE/"frames"/<label>

    def tearDown(self):
        CA.HERE = self._here
        shutil.rmtree(self.d, ignore_errors=True)

    def _write(self, label, data=b"\xff\xd8\xff\xe0not-a-real-jpeg"):
        p = os.path.join(self.frames, label)
        io.open(p, "wb").write(data)
        return p

    # ── the instrument first ────────────────────────────────────────────────────────────────
    def test_the_function_is_still_here(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        self.assertTrue(hasattr(CA, FN), "%s is gone or renamed — re-point this law" % FN)

    def test_no_frame_at_all_is_UNKNOWN_not_empty(self):
        """⛔ 'no items are on screen' and 'nobody could read the screen' are opposite facts."""
        cells, why = getattr(CA, FN)()
        self.assertIsNone(cells, "it returned cells with no frame on disk")
        self.assertIn("capture", (why or "").lower(),
                      "the refusal does not point at the capture: %r" % why)

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_the_READER_never_receives_the_LIVE_path(self):
        """★★★ THE DEFECT. If the reader is handed the live path, the capture can pull it out from
        under the open — which is exactly what he hit."""
        self._write("eye.jpg")
        seen = {}

        class _FakeVC(object):
            @staticmethod
            def inventory_lattice(p):
                seen["path"] = p
                return {"ok": True}

            @staticmethod
            def inventory_occupancy(p, lat):
                seen["path2"] = p
                return {"ok": True, "grid": [[1, 0], [0, 0]]}

        real = sys.modules.get("vault_corpus")
        sys.modules["vault_corpus"] = _FakeVC
        try:
            getattr(CA, FN)()
        finally:
            if real is not None:
                sys.modules["vault_corpus"] = real
            else:
                sys.modules.pop("vault_corpus", None)
        self.assertIn("path", seen, "the lattice reader was never called — this law graded nothing")
        live = os.path.join(self.frames, "eye.jpg")
        self.assertNotEqual(
            os.path.realpath(seen["path"]), os.path.realpath(live),
            "the reader was handed the LIVE frame path. The capture replaces that file mid-promote, "
            "so the open races it — reproduce by deleting the file between the stat and the read.")
        self.assertEqual(seen.get("path"), seen.get("path2"),
                         "the two readers were given DIFFERENT files, so the lattice and the "
                         "occupancy describe different pictures")

    def test_a_frame_that_VANISHES_is_skipped_not_fatal(self):
        """⚠ The whole point: one label disappearing costs one candidate, not the attempt."""
        self._write("live.jpg")
        gone = os.path.join(self.frames, "eye.jpg")
        io.open(gone, "wb").write(b"x")
        os.utime(gone, None)          # newest, so it is tried FIRST
        os.unlink(gone)               # ...and is gone by the time it is read
        cells, why = getattr(CA, FN)()
        # live.jpg survives, so it must get past the vanish and refuse on AGE or on the lattice —
        # never on "no live frame", which would mean the survivor was discarded too
        self.assertNotIn("there is no live frame", (why or ""),
                         "a vanished candidate took the surviving one with it: %r" % why)

    def test_no_snapshot_is_left_behind_on_ANY_path(self):
        """⛔ Every refusal passes through the cleanup. A snapshot per press fills his disk, and
        this repo has already paid for an ENOSPC."""
        self._write("eye.jpg")
        before = set(f for f in os.listdir(tempfile.gettempdir()) if f.startswith("minigrid."))
        for _ in range(3):
            getattr(CA, FN)()
        after = set(f for f in os.listdir(tempfile.gettempdir()) if f.startswith("minigrid."))
        self.assertEqual(after - before, set(),
                         "snapshots survived the call: %s" % sorted(after - before))


if __name__ == "__main__":
    unittest.main(verbosity=2)
