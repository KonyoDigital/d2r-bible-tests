# -*- coding: utf-8 -*-
"""THE FROZEN-SCREEN WATCH READS ONLY RECENT LOOKS.

MEASURED 2026-09-24: GrokBot's evidence root held 9,325 PNGs / 3.2 GB in 597 entries, a new pack about
every 25 minutes, and frozen_frame_watch walked ALL of it on every doctor pass (each open ~36 ms on an
iCloud Desktop). The doctor's 'screen still painting' row took 337.5 s; test_control runs the doctor
several times; a push was refused as "test_control HUNG" at its 1500 s bound on an idle machine (load
2.8). The row now reads the newest FRAMES_TOP_MAX top-level entries only: 0.1 s, same verdict.

  · DRIVEN: a fixture root with 20 packs of frames - frames() reads only the newest packs, and still
    returns the NEWEST frame first; newest_capture_age_s ages from that same newest frame.
  · PREMISE: with the bound lifted the same fixture yields every frame, so the case can fail.
RED_PROOF below.
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

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import frozen_frame_watch as F  # noqa: E402


def _png(path, w=1280, h=720):
    """A real, minimal PNG: png_geometry reads its IHDR."""
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    raw = b"\x00" + b"\x00\x00\x00" * 1
    body = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(body)


class TheWatchReadsOnlyRecentLooks(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ffw-shelf-")
        base = time.time() - 20 * 1500
        for i in range(20):                               # 20 packs, 25 minutes apart
            pack = os.path.join(self.root, "visual-pass-%02d" % i, "shelf")
            os.makedirs(pack)
            for j in range(3):
                p = os.path.join(pack, "f%d.png" % j)
                _png(p)
                t = base + i * 1500 + j * 5
                os.utime(p, (t, t))
            for d in (pack, os.path.dirname(pack)):
                os.utime(d, (base + i * 1500 + 20, base + i * 1500 + 20))
        self.newest = os.path.join(self.root, "visual-pass-19", "shelf", "f2.png")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_only_the_newest_packs_are_read(self):
        fs = F.frames(self.root)
        self.assertEqual(len(fs), F.FRAMES_TOP_MAX * 3,
                         "the watch read %d frames of 60 - it walked the whole shelf" % len(fs))
        self.assertEqual(fs[0]["path"], self.newest, "the bound lost the newest frame")

    def test_the_age_is_taken_from_the_same_newest_frame(self):
        age = F.newest_capture_age_s(self.root, now=os.path.getmtime(self.newest) + 60)
        self.assertAlmostEqual(age, 60, delta=1)

    def test_premise_without_the_bound_every_frame_is_read(self):
        self.assertEqual(len(list(F._recent_pngs(self.root, top_max=10 ** 6))), 60)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the frozen-screen watch walks the whole 3.2 GB shelf on every doctor pass again (337 s; test_control 'HUNG' at 1500 s)",
        "file": "frozen_frame_watch.py",
        "find": "    for _m, path, is_dir in tops[:top_max]:\n",
        "replace": "    for _m, path, is_dir in tops:\n",
        "matches": 1,
    },
]
