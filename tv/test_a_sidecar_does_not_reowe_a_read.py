# -*- coding: utf-8 -*-
"""#25 — A MOVED DIRECTORY IS NOT MOVED FILM: the behavioural law, BOTH halves.

kai_report.json (and its .bak siblings) land INSIDE the reel dir and bump the directory
mtime with zero frame change; _chron_reel_owes_a_read used to convict on the dir stamp
alone, minting false re-owes that fed the retirement deadlock (4 reels, 81.3h banner).
v3298 demands FRAME evidence: the f_*.jpg census moved, or a frame is newer than the
directory was at the look. These two tests are the halves that must never both pass by
accident: a sidecar-only touch reads owes=False, and a prune-then-capture at EQUAL count
still reads owes=True (the case control_app:16550's comment exists for — kept, verified).
TestV2202 in test_control.py owns the neighbours; this file owns the sidecar half, born
with the fix. [[heart-first]]
"""
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import control_app as ca


class TestSidecarVsCapture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reowe_test_")
        self._hist = os.environ.get("TV_HIST")
        # TV_HIST IS the hist dir, and rid carries the reel_ prefix — the exact convention
        # TestV2202 uses (control_app: _rd = TV_HIST or HIST_DIR joined with rid)
        os.environ["TV_HIST"] = os.path.join(self.tmp, "hist")
        self.rid = "reel_s_1500000000000_1"
        self.rd = os.path.join(os.environ["TV_HIST"], self.rid)
        os.makedirs(self.rd)
        for i in range(3):
            open(os.path.join(self.rd, "f_%d.jpg" % i), "wb").write(b"x")
        # the look stamp, taken NOW: 3 frames, dir mtime as of this moment
        st = os.stat(self.rd)
        self.mem = {self.rid: {"ts": 1, "classified": 0, "pages": 0, "looked": True,
                               "framesAtLook": 3, "dirMtimeAtLook": st.st_mtime}}

    def tearDown(self):
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_sidecar_write_does_NOT_reowe(self):
        """kai_report.json bumps the dir mtime; the census and newest frame do not move."""
        time.sleep(0.05)
        open(os.path.join(self.rd, "kai_report.json"), "w").write("{}")
        # dir mtime is now PAST the look stamp, frames untouched
        self.assertGreater(os.stat(self.rd).st_mtime, self.mem[self.rid]["dirMtimeAtLook"])
        self.assertFalse(ca._chron_reel_owes_a_read(self.rid, self.mem),
                         "a neighbour's bookkeeping re-bought a read of unchanged film — "
                         "the exact deadlock minting mechanism")

    def test_a_prune_then_capture_at_EQUAL_count_still_reowes(self):
        """The half the strict dir stamp exists for — it must survive the sidecar fix."""
        time.sleep(0.7)   # > the 0.5s frame-vs-dir tolerance; production gap is seconds
        os.remove(os.path.join(self.rd, "f_0.jpg"))
        open(os.path.join(self.rd, "f_9.jpg"), "wb").write(b"y")   # count back to 3, frame NEWER
        self.assertTrue(ca._chron_reel_owes_a_read(self.rid, self.mem),
                        "a prune-then-capture that leaves the count at N went invisible — "
                        "the regression :16550's comment warns against")


RED_PROOF = [
    {"why": "dropping the frame-evidence demand returns to convicting on the dir stamp "
            "alone — every sidecar write re-buys a read of unchanged film",
     "file": "control_app.py",
     "find": "            _ff = _g3.glob(os.path.join(_rd, \"f_*.jpg\"))",
     "replace": "            return True\n            _ff = _g3.glob(os.path.join(_rd, \"f_*.jpg\"))",
     "matches": 1},
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
