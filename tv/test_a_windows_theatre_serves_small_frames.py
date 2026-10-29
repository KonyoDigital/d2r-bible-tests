# -*- coding: utf-8 -*-
"""#218 (REG-3038, after REG-3033) - A WINDOWS CONSOLE'S THEATRE AND SHELF SCRUB GET SMALL FRAMES, NOT FULL ONES.

The theatre's derivatives (cache160 for the Shelf scrub, cache1280 for play) were made by sips, so control_app gated all of
them off Windows: `_serve_hist`'s ?w=160/1280 branch carried `and not IS_WIN` and `_prewarm_session_frames` returned at
once on IS_WIN. A Windows console therefore served every scrub thumbnail and every played frame at full size - and
_serve_hist's own note says what that costs: "a decoded 2560px JPEG is ~14MB RGBA in the WebView". On the ALT, free
memory fell 1.5 GB -> 560 MB in an hour (#172). Now both make their derivative on every PC through
shadow_sessions.make_derivative (sips on a Mac, exactly the call the theatre always made; else Pillow), and a PC with
neither still serves the full frame, as before. A sibling at the same site, fixed with it: the prewarm keyed its cache by
the frame's BASENAME while _serve_hist reads by the frame's path under the shelf (v2238), so a prewarmed reel frame sat
where no GET looked. Part files are named per thread, since the scrub asks for many at once.

The 400-frame seal prewarm (_prewarm_seal_cache) stays Mac-only on purpose: a bulk background pass on a PC short of
memory; the on-demand GET covers it. Driven: the real _serve_hist and _prewarm_session_frames on a console made a Windows
console for the call (IS_WIN and sys.platform), over a fixture shelf - never his. RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx  # noqa: E402
_fx.contain()
import control_app as CA  # noqa: E402
import shadow_sessions as SS  # noqa: E402
from PIL import Image  # noqa: E402


def _jpeg(path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.new("RGB", size)
    px = im.load()
    for x in range(0, size[0], 9):
        for y in range(0, size[1], 7):
            px[x, y] = ((x * 3) % 256, (y * 5) % 256, ((x + y) * 7) % 256)
    im.save(path, "JPEG", quality=90)


class AWindowsTheatreServesSmallFrames(unittest.TestCase):

    def setUp(self):
        self.hist = tempfile.mkdtemp(prefix="win_theatre_")
        _jpeg(os.path.join(self.hist, "10_1793000000000.jpg"), (2560, 1440))
        _jpeg(os.path.join(self.hist, "reel_s_1", "f_1793000001000.jpg"), (2560, 1440))
        self.patches = [mock.patch.object(CA, "HIST_DIR", self.hist), mock.patch.object(CA, "IS_WIN", True),
                        mock.patch.object(SS.sys, "platform", "win32")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        shutil.rmtree(self.hist, True)

    def _get(self, rel, w):
        with Image.open(io.BytesIO(self._bytes(rel, w))) as im:
            return im.size

    def _bytes(self, rel, w):
        h = CA.Handler.__new__(CA.Handler)
        got = {}
        h.path = "/hist/%s?w=%s" % (rel, w)
        h._json = lambda code, obj: got.update(code=code, body=obj)
        h.send_response = lambda code: got.update(code=code)
        h.send_header = lambda k, v: None
        h.end_headers = lambda: None
        h.wfile = io.BytesIO()
        h._serve_hist(rel)
        self.assertEqual(got.get("code"), 200, got)
        return h.wfile.getvalue()

    def test_the_scrub_gets_a_160_px_frame_and_play_a_1280_px_frame(self):
        self.assertEqual(max(self._get("10_1793000000000.jpg", "160")), 160,
                         "a Windows console served the Shelf scrub a full-size frame")
        self.assertEqual(max(self._get("10_1793000000000.jpg", "1280")), 1280,
                         "a Windows console served the theatre a full-size frame")
        self.assertTrue(os.path.isfile(os.path.join(self.hist, "cache160", "10_1793000000000.jpg")))
        self.assertTrue(os.path.isfile(os.path.join(self.hist, "cache1280", "10_1793000000000.jpg")))

    def test_a_pc_with_no_resizer_still_serves_the_frame(self):
        with mock.patch.dict(sys.modules, {"PIL": None, "PIL.Image": None}):
            data = self._bytes("reel_s_1/f_1793000001000.jpg", "160")
        with open(os.path.join(self.hist, "reel_s_1", "f_1793000001000.jpg"), "rb") as fh:
            self.assertEqual(data, fh.read(), "with no resizer the frame was not served whole")

    def test_the_prewarm_runs_on_windows_and_writes_where_the_get_reads(self):
        beats = [{"frame": "10_1793000000000.jpg"}, {"frame": "reel_s_1/f_1793000001000.jpg"}]
        h = CA.Handler.__new__(CA.Handler)
        h._prewarm_session_frames(beats, limit=80, width="1280")
        for t in [t for t in threading.enumerate() if t.name == "tvd-prewarm-sess"]:
            t.join(30)
        made = sorted(_fx.list_own(os.path.join(self.hist, "cache1280"))) \
            if os.path.isdir(os.path.join(self.hist, "cache1280")) else []
        self.assertEqual(made, ["10_1793000000000.jpg", "reel_s_1__f_1793000001000.jpg"],
                         "the prewarm made nothing on Windows, or keyed a reel frame where no GET reads it: %r" % made)
        calls = []
        real = SS.make_derivative
        with mock.patch.object(SS, "make_derivative", lambda *a, **k: calls.append(a) or real(*a, **k)):
            self.assertEqual(max(self._get("reel_s_1/f_1793000001000.jpg", "1280")), 1280)
        self.assertEqual(calls, [], "the GET made again a frame the prewarm had already made")

    def test_two_writers_never_share_a_part_file(self):
        names = []
        real = os.replace
        both = threading.Barrier(2)

        def spy(a, b):
            names.append(a)
            try:
                both.wait(10)          # both writers alive at once, each holding its written part file
            except threading.BrokenBarrierError:
                pass
            return real(a, b)
        src = os.path.join(self.hist, "10_1793000000000.jpg")
        dst = os.path.join(self.hist, "cache160", "x.jpg")
        with mock.patch.object(SS.os, "replace", spy):
            ts = [threading.Thread(target=SS.make_derivative, args=(src, dst, 160, 72)) for _ in range(2)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(30)
        self.assertEqual(len(names), 2)
        self.assertNotEqual(names[0], names[1], "two writers of one derivative wrote the same part file")


RED_PROOF = [
    {"why": "REG-3038 - the ?w= branch is gated off Windows again (the scrub gets full frames)",
     "file": "tv/control_app.py",
     "find": "        if want_w in (\"1280\", \"160\"):   # v802 — 160 = scrub thumbnails\n",
     "replace": "        if want_w in (\"1280\", \"160\") and not IS_WIN:   # v802 — 160 = scrub thumbnails\n",
     "matches": 1},
    {"why": "REG-3038 - the theatre's prewarm returns at once on Windows again",
     "file": "tv/control_app.py",
     "find": "        path under the shelf, v2238): it wrote the BASENAME, so every prewarmed reel frame sat where no GET looked.\"\"\"\n        paths = []\n",
     "replace": "        path under the shelf, v2238): it wrote the BASENAME, so every prewarmed reel frame sat where no GET looked.\"\"\"\n        if IS_WIN:\n            return\n        paths = []\n",
     "matches": 1},
    {"why": "REG-3038 - the prewarm keys a reel frame by its basename, where no GET reads",
     "file": "tv/control_app.py",
     "find": "                    cached = os.path.join(cache_dir, os.path.relpath(src, os.path.realpath(HIST_DIR)).replace(os.sep, \"__\"))\n",
     "replace": "                    cached = os.path.join(cache_dir, os.path.basename(fr))\n",
     "matches": 1},
    {"why": "REG-3038 - the theatre's derivative never asks Pillow",
     "file": "tv/shadow_sessions.py",
     "find": "    return _sips_thumb(src, dst, max_px, quality, timeout) or _pil_thumb(src, dst, max_px, quality)\n",
     "replace": "    return _sips_thumb(src, dst, max_px, quality, timeout)\n",
     "matches": 1},
    {"why": "REG-3038 - Pillow makes every derivative 160 px, whatever was asked",
     "file": "tv/shadow_sessions.py",
     "find": "    return _sips_thumb(src, dst, max_px, quality, timeout) or _pil_thumb(src, dst, max_px, quality)\n",
     "replace": "    return _sips_thumb(src, dst, max_px, quality, timeout) or _pil_thumb(src, dst)\n",
     "matches": 1},
    {"why": "REG-3038 - two writers share one part file",
     "file": "tv/shadow_sessions.py",
     "find": "    tmp = \"%s.%d.%d.part\" % (dst, os.getpid(), threading.get_ident())\n",
     "replace": "    tmp = dst + \".part\"\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
