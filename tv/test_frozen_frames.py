#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A FROZEN FEED AND A BLANK SCREEN ARE TWO FINDINGS, AND NEITHER MAY BE REPORTED AS THE OTHER.

⚠⚠ MEASURED 2026-09-10 (#34) on his real `~/gb-shelf` — 194 captures of his TV DIABLO window,
taken while Grok Bot's own status ticks read `GET / 200 · 1,744,954 bytes` and "quiet hold · census
held". Three long runs of byte-identical frames, every one of them a window with nothing in it but
the titlebar, two confirmed by opening the image and looking:

    34 identical @ 286,148 B   09-09 20:57 -> 09-10 06:12   BLANK (luminance 30, dark)
    18 identical @ 276,288 B   09-10 08:59 -> 09-10 16:16   BLANK (luminance 255, white)
    16 identical @ 275,319 B   09-10 06:58 -> 09-10 08:44   BLANK (luminance 255, white)
     3 identical @ 2,017,008 B 09-10 12:20 -> 09-10 12:21   **PAINTED**

⚠⚠ READ THE LAST ROW. It is why this suite exists in the shape it does. That run is frozen and has
content on it — a feed that stopped while the last good paint was still on screen. If FROZEN and
BLANK were one verdict, that run would be published as a blank console nobody ever looked at, and
the 34-frame run would be publishable as "just a repeated file". A repeated hash is a POINTER: it
says the feed stopped moving and it cannot say what is on the screen. [[unknown-stays-unknown]]

⚠ NOTHING HERE READS HIS SHELF. Every capture in this file is built into a temp directory with
`tempfile`, so this suite measures the same thing on his Mac and on a CI runner, and it cannot see
or touch the live one. The numbers above were measured by pointing the module at his shelf BY HAND,
which is a report, not a test. [[feedback-fixtures-never-touch-live-data]]

⚠ THE FIXTURES CARRY WINDOW CHROME AND A DROP SHADOW ON PURPOSE. A blank window with neither is a
fixture that can only pass — the one case this module exists to catch is a blank BODY under a
titlebar, inside a soft alpha shadow, and both of those dilute the uniformity the bar is written
against. paint_witness's own v2752 scar is exactly this: two rows of chrome at luminance 255 held a
completely black console over both ink conditions. [[feedback-blind-fixture-green-gate]]
"""
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import frozen_frames as FF   # noqa: E402
import paint_witness as PW   # noqa: E402


# ── the fixture capture: a window, its titlebar, and the soft shadow around it ───────────────────
IMG_W, IMG_H = 600, 1400
SHADOW = 40                       #: the drop shadow ring, an ALPHA RAMP and not transparency
WIN = (SHADOW, SHADOW, IMG_W - SHADOW, IMG_H - SHADOW)      # 520 x 1320, the size of his 2x window
CHROME_H = int((WIN[3] - WIN[1]) * 0.065)                   # 85px — his measures 5.3% of the window
WHITE, DARK = (255, 255, 255), (30, 30, 30)
CHROME = (246, 246, 246)          #: a light titlebar, as his white-blank capture actually has
CHROME_EDGE = (255, 255, 255)     #: the titlebar's bottom border — the v2752 shape, full-width ink


def _chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))


def _png(rows):
    """RGBA scanlines -> PNG bytes, filter 0 throughout. -> bytes"""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", IMG_W, IMG_H, 8, 6, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(raw, 6))
            + _chunk(b"IEND", b""))


def _shadow_row():
    """One row entirely outside the window: black at a partial alpha, never alpha 0 everywhere."""
    return b"".join(bytes((0, 0, 0, 120)) for _ in range(IMG_W))


def _body_row(colour, painted_shift=None, base=None):
    """One row of the window, with its shadow shoulders. -> bytes"""
    x0, x1 = WIN[0], WIN[2]
    left = b"".join(bytes((0, 0, 0, 60 + i)) for i in range(x0))
    right = b"".join(bytes((0, 0, 0, 60 + i)) for i in reversed(range(IMG_W - x1)))
    if painted_shift is None:
        mid = bytes(tuple(colour) + (255,)) * (x1 - x0)
    else:
        s = (painted_shift % (x1 - x0)) * 4
        mid = base[s:] + base[:s]
    return left + mid + right


def capture_bytes(kind, nonce=0):
    """A whole fake capture of his window. -> bytes

    kind: "white" / "dark" -> a blank body under a titlebar; "painted" -> content everywhere.
    nonce changes ONE body pixel, so two captures of the same kind differ in bytes while showing
    the same thing — which is how the pixel finding is proven independent of the hash finding.
    """
    x0, x1 = WIN[0], WIN[2]
    width = x1 - x0
    base = b"".join(bytes(((x * 5) % 256,) * 3 + (255,)) for x in range(width))
    shadow = _shadow_row()
    chrome = _body_row(CHROME)
    edge = _body_row(CHROME_EDGE)
    rows = []
    for y in range(IMG_H):
        if y < WIN[1] or y >= WIN[3]:
            rows.append(shadow)
        elif y < WIN[1] + CHROME_H - 3:
            rows.append(chrome)
        elif y < WIN[1] + CHROME_H:
            rows.append(edge)
        elif kind == "painted":
            rows.append(_body_row(None, painted_shift=y * 11, base=base))
        else:
            rows.append(_body_row(WHITE if kind == "white" else DARK))
    if nonce:
        y = WIN[1] + CHROME_H + 5
        r = bytearray(rows[y])
        o = (x0 + 7) * 4
        r[o:o + 3] = bytes(((nonce * 37) % 256,) * 3)
        rows[y] = bytes(r)
    return _png(rows)


class _Shelf(object):
    """A throwaway capture directory. Never his."""

    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="frozen-frames-")
        self.n = 0

    def put(self, blob, mtime, name=None):
        self.n += 1
        p = os.path.join(self.dir, name or ("cap-%03d.png" % self.n))
        with open(p, "wb") as fh:
            fh.write(blob)
        os.utime(p, (mtime, mtime))
        return p

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


NOW = 1_788_000_000.0


class FrozenFramesReadsThePixelsAndTheBytes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # built ONCE — a capture is 3.4 MB of scanlines and every law below reuses these bytes.
        cls.white = capture_bytes("white")
        cls.dark = capture_bytes("dark")
        cls.painted = capture_bytes("painted")

    def setUp(self):
        self.shelf = _Shelf()

    def tearDown(self):
        self.shelf.close()

    def _feed(self, blobs, step=60, end=NOW):
        for i, b in enumerate(blobs):
            self.shelf.put(b, end - (len(blobs) - 1 - i) * step)
        return FF.scan(self.shelf.dir, newest=16, decode=4, now=end)

    # ── the bar is not this module's to own ──────────────────────────────────────────────────────
    def test_the_blank_bar_is_paint_witness_s_and_is_not_re_typed_here(self):
        """One bar for 'is anything drawn'. A second copy here is a copy that drifts."""
        self.assertIs(FF.BLANK, PW.BLANK)
        self.assertIs(FF.PAINTED, PW.PAINTED)
        self.assertIs(FF.UNKNOWN, PW.UNKNOWN)
        self.assertEqual(FF.FROZEN_RUN, PW.BLANK_STRIKES,
                         "the frozen-run bar drifted away from paint_witness.BLANK_STRIKES")
        with open(os.path.join(HERE, "frozen_frames.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn("modalShare >=", src,
                         "frozen_frames.py is deciding blankness itself instead of asking "
                         "paint_witness.verdict — that is a second bar and it will drift")

    # ── THE WHOLE POINT: two findings, never merged ──────────────────────────────────────────────
    def test_a_frozen_run_of_painted_frames_is_frozen_and_not_blank(self):
        """His 12:20 run, 3 identical frames with content on them. FROZEN must not imply BLANK."""
        rep = self._feed([self.painted] * 4)
        self.assertEqual(rep["frozen"]["state"], FF.FROZEN, rep["verdict"])
        self.assertEqual(rep["blank"]["state"], FF.PAINTED,
                         "a repeated hash was published as a blank screen nobody looked at: %s"
                         % rep["verdict"])
        self.assertIn("FROZEN", rep["verdict"])
        self.assertIn("PAINTED", rep["verdict"])

    def test_a_moving_feed_of_blank_frames_is_blank_and_not_frozen(self):
        """The mirror: every frame differs, and every frame is empty. Pixels decide blankness."""
        rep = self._feed([capture_bytes("white", nonce=i) for i in (1, 2, 3, 4)])
        self.assertEqual(rep["frozen"]["state"], FF.MOVING,
                         "four different files were reported as a frozen feed: %s" % rep["verdict"])
        self.assertEqual(rep["blank"]["state"], FF.BLANK,
                         "a window with nothing drawn on it read as painted because its BYTES kept "
                         "changing: %s" % rep["verdict"])

    def test_his_34_frame_run_shape_reads_frozen_AND_blank(self):
        """Both findings can be true at once, and then both are stated."""
        rep = self._feed([self.dark] * 5)
        self.assertEqual(rep["frozen"]["state"], FF.FROZEN, rep["verdict"])
        self.assertEqual(rep["blank"]["state"], FF.BLANK, rep["verdict"])
        self.assertEqual(len(rep["findings"]), 2)
        self.assertTrue(rep["findings"][0].startswith("FEED"))
        self.assertTrue(rep["findings"][1].startswith("PIXEL"))

    # ── the crop is load-bearing, and the white window is the case that proves it ────────────────
    def test_a_white_blank_window_under_its_titlebar_reads_blank(self):
        """His 08:59->16:16 run. The ink test cannot fire on white; only the crop saves this."""
        rep = self._feed([self.white] * 4)
        self.assertEqual(rep["blank"]["state"], FF.BLANK,
                         "a white window with only a titlebar drawn read as painted — the shadow "
                         "and the chrome diluted the one-colour test below its bar: %s"
                         % rep["blank"]["why"])
        self.assertIn("SINGLE colour", rep["blank"]["why"])

    def test_a_dark_blank_window_under_its_titlebar_reads_blank(self):
        rep = self._feed([self.dark] * 4)
        self.assertEqual(rep["blank"]["state"], FF.BLANK, rep["blank"]["why"])

    def test_a_window_with_content_on_it_reads_painted(self):
        """The direction that costs him something: a wrong BLANK would replace a window in use."""
        rep = self._feed([capture_bytes("painted", nonce=i) for i in (1, 2, 3, 4)])
        self.assertEqual(rep["blank"]["state"], FF.PAINTED, rep["blank"]["why"])
        self.assertEqual(rep["frozen"]["state"], FF.MOVING, rep["frozen"]["why"])

    # ── a zero needs a denominator ───────────────────────────────────────────────────────────────
    def test_an_empty_directory_is_unknown_and_never_moving(self):
        rep = FF.scan(self.shelf.dir, now=NOW)
        self.assertEqual(rep["captures"], 0)
        self.assertEqual(rep["examined"], 0)
        self.assertEqual(rep["frozen"]["state"], FF.UNKNOWN,
                         "an empty capture directory was reported as a moving feed: %s"
                         % rep["verdict"])
        self.assertEqual(rep["blank"]["state"], FF.UNKNOWN,
                         "an empty capture directory was reported as a painted screen: %s"
                         % rep["verdict"])

    def test_a_directory_that_cannot_be_listed_is_unknown_and_says_so(self):
        missing = os.path.join(self.shelf.dir, "no-such-shelf")
        rep = FF.scan(missing, now=NOW)
        self.assertFalse(rep["ok"], "an unreadable directory reported ok: %s" % rep["verdict"])
        self.assertEqual(rep["frozen"]["state"], FF.UNKNOWN)
        self.assertEqual(rep["blank"]["state"], FF.UNKNOWN)
        self.assertTrue(rep["why"], "the failure was swallowed - nothing said why")
        self.assertIn("could not be listed", " ".join(rep["why"]))

    def test_every_verdict_carries_the_numbers_it_was_measured_over(self):
        """'0 frozen' over 0 files read is a broken reader wearing the clothes of a measurement."""
        rep = self._feed([self.painted, self.white, self.dark])
        for token in ("capture(s) in the directory", "examined", "decoded", "undecodable"):
            self.assertIn(token, rep["verdict"], rep["verdict"])
        self.assertEqual(rep["captures"], 3)
        self.assertEqual(rep["examined"], 3)
        self.assertEqual(rep["decoded"] + rep["undecodable"], 3)

    # ── an unmeasured frame is unknown, not clean ────────────────────────────────────────────────
    def test_a_capture_whose_pixels_will_not_decode_is_unknown_not_painted(self):
        p = self.shelf.put(b"\x89PNG\r\n\x1a\nrubbish that is not a chunk", NOW)
        seen = FF.look(p)
        self.assertEqual(seen["state"], FF.UNKNOWN,
                         "an undecodable file was given a verdict about his screen: %s"
                         % seen["why"])
        rep = FF.scan(self.shelf.dir, now=NOW)
        self.assertEqual(rep["decoded"], 0)
        self.assertEqual(rep["undecodable"], 1)
        self.assertEqual(rep["blank"]["state"], FF.UNKNOWN, rep["blank"]["why"])

    def test_a_painted_frame_beside_an_undecodable_one_cannot_read_clean(self):
        """Some of the newest frames were never looked at, so 'nothing is blank' is a sample."""
        self.shelf.put(self.painted, NOW - 60)
        self.shelf.put(b"\x89PNG\r\n\x1a\x0anot a png body", NOW, name="cap-broken.png")
        rep = FF.scan(self.shelf.dir, now=NOW)
        self.assertEqual(rep["decoded"], 1)
        self.assertEqual(rep["undecodable"], 1)
        self.assertEqual(rep["blank"]["state"], FF.UNKNOWN,
                         "a half-read decode window reported the screen painted: %s"
                         % rep["blank"]["why"])
        self.assertIn("could not be decoded", rep["blank"]["why"])

    def test_a_truncated_png_is_unknown_rather_than_half_decoded(self):
        p = self.shelf.put(self.white[:len(self.white) // 3], NOW, name="cap-cut.png")
        seen = FF.look(p)
        self.assertEqual(seen["state"], FF.UNKNOWN, seen["why"])

    def test_a_capture_over_the_decode_budget_is_refused_not_attempted(self):
        """The budget branch, exercised. His largest capture decodes to 22 MB against a 96 MB
        budget, so nothing on his shelf has ever reached this arm — and a branch no input reaches
        is a branch nobody has ever seen work. [[feedback-threshold-above-the-ceiling]]"""
        p = self.shelf.put(self.white, NOW)
        was = FF.MAX_DECODE_BYTES
        try:
            FF.MAX_DECODE_BYTES = 1024
            seen = FF.look(p)
        finally:
            FF.MAX_DECODE_BYTES = was          # ⚠ or this fixture leaks into the next law
        self.assertEqual(seen["state"], FF.UNKNOWN, seen["why"])
        self.assertIn("budget", seen["why"])
        self.assertEqual(FF.look(p)["state"], FF.BLANK,
                         "the budget was not put back — every later law is now measuring a "
                         "crippled decoder")

    def test_a_png_shape_the_decoder_does_not_support_is_unknown_not_painted(self):
        """Palette and interlaced PNGs are refused rather than half-read. 0 of his 194 captures
        are either — which is exactly why this is asserted rather than assumed."""
        for name, ihdr in (("cap-palette.png", struct.pack(">IIBBBBB", 8, 8, 8, 3, 0, 0, 0)),
                           ("cap-interlaced.png", struct.pack(">IIBBBBB", 8, 8, 8, 6, 0, 0, 1)),
                           ("cap-16bit.png", struct.pack(">IIBBBBB", 8, 8, 16, 6, 0, 0, 0))):
            blob = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
                    + _chunk(b"IDAT", zlib.compress(b"\x00" * 64)) + _chunk(b"IEND", b""))
            seen = FF.look(self.shelf.put(blob, NOW, name=name))
            self.assertEqual(seen["state"], FF.UNKNOWN,
                             "%s was given a verdict about his screen: %s" % (name, seen["why"]))
            self.assertIn("not supported", seen["why"])

    # ── the run-length bar must be able to refuse ────────────────────────────────────────────────
    def test_two_identical_captures_are_under_the_bar_and_read_moving(self):
        rep = self._feed([self.painted, self.painted])
        self.assertEqual(rep["frozen"]["runLength"], 2)
        self.assertEqual(rep["frozen"]["state"], FF.MOVING,
                         "a run of 2 fired a bar of %d" % FF.FROZEN_RUN)

    def test_a_repeat_further_back_is_reported_without_calling_the_feed_frozen(self):
        """His shelf's shape: old frozen runs behind a feed that has since started moving."""
        rep = self._feed([self.white, self.white, self.white,
                          capture_bytes("painted", nonce=1), capture_bytes("painted", nonce=2)])
        self.assertEqual(rep["frozen"]["state"], FF.MOVING, rep["frozen"]["why"])
        self.assertEqual(rep["frozen"]["framesInRuns"], 3,
                         "the historical run was lost from the report: %s" % rep["frozen"]["runs"])

    # ── age is its own question ──────────────────────────────────────────────────────────────────
    def test_freshness_is_reported_beside_the_state_and_never_folded_into_it(self):
        self._feed([self.dark] * 4, step=60, end=NOW)     # the same four frames, read twice
        stale = FF.scan(self.shelf.dir, newest=16, decode=4, now=NOW + FF.STALE_SEC + 60)
        self.assertEqual(stale["frozen"]["state"], FF.FROZEN,
                         "an old frozen run stopped being frozen because it was old")
        self.assertEqual(stale["frozen"]["freshness"], "STALE", stale["verdict"])
        fresh = FF.scan(self.shelf.dir, newest=16, decode=4, now=NOW + 5)
        self.assertEqual(fresh["frozen"]["freshness"], "FRESH", fresh["verdict"])

    # ── the fixture may never reach his shelf ────────────────────────────────────────────────────
    def test_this_suite_reads_only_its_own_temp_directory(self):
        rep = self._feed([self.painted])
        self.assertEqual(rep["dir"], self.shelf.dir)
        self.assertNotEqual(os.path.realpath(self.shelf.dir),
                            os.path.realpath(FF.DEFAULT_DIR))
        self.assertIn(tempfile.gettempdir().split(os.sep)[1], os.path.realpath(self.shelf.dir))


RED_PROOF = [
    {
        'why': 'deleting the titlebar crop: his white-blank window has a light titlebar with a full-width bright border, and paint_witness only skips its own CHROME_TOP_PX (36) which these 2x captures dwarf. Measured on his real capture, uncropped: modalShare 0.9199 against a 0.98 bar, p99 255 and brightShare 0.9199 — so the one-colour test misses it AND the ink test structurally cannot fire on white. Without this line a confirmed-blank console reads PAINTED, which is the whole defect #34 exists for',
        'file': 'frozen_frames.py',
        'find': '    cy0 = y0 + int(win_h * CHROME_TOP_FRACTION)',
        'replace': '    cy0 = y0',
        'matches': 1,
    },
    {
        'why': 'deleting the drop-shadow trim: a file on the shelf carries a soft alpha ramp around the window that paint_witness never sees, because it reads live windows with kCGWindowImageBoundsIgnoreFraming. With the shadow inside the measured region a blank window is no longer one colour and reads PAINTED',
        'file': 'frozen_frames.py',
        'find': '    x0, y0, x1, y1 = window_rect(w, h, ch, rows)',
        'replace': '    x0, y0, x1, y1 = 0, 0, w, h',
        'matches': 1,
    },
    {
        'why': 'letting an unexamined feed read as healthy — the single most convincing wrong answer this module could give, because MOVING+PAINTED over 0 files read is indistinguishable from a live console. A zero needs a denominator',
        'file': 'frozen_frames.py',
        'find': '        rep["verdict"] = _verdict(rep)\n        return rep\n\n    runs = frozen_runs(read)',
        'replace': '        rep["frozen"]["state"] = MOVING\n        rep["blank"]["state"] = PAINTED\n        rep["verdict"] = _verdict(rep)\n        return rep\n\n    runs = frozen_runs(read)',
        'matches': 1,
    },
    {
        'why': 'returning an empty list instead of None when the capture directory cannot be listed — a broken reader then looks exactly like a directory with nothing in it, and the scan reports 0 captures instead of naming the failure',
        'file': 'frozen_frames.py',
        'find': '        return None, "the capture directory could not be listed (%s: %s)" % (type(e).__name__, e)',
        'replace': '        return [], ""',
        'matches': 1,
    },
    {
        'why': 'giving a file whose pixels would not decode a verdict about his screen. UNKNOWN is not PAINTED: an unread frame is the one state that must never read clean',
        'file': 'frozen_frames.py',
        'find': '    except Unreadable as e:\n        out["why"] = "the pixels could not be read: %s" % e\n        return out',
        'replace': '    except Unreadable as e:\n        out["state"] = PAINTED\n        out["why"] = "the pixels could not be read: %s" % e\n        return out',
        'matches': 1,
    },
    {
        'why': 'COLLAPSING THE TWO FINDINGS — deriving blankness from the repeated hash instead of from decoded pixels. His 12:20 run is 3 byte-identical frames WITH CONTENT ON THEM; under this edit that run would be published as a blank console nobody ever looked at, and a repeated hash would have become a verdict about the screen',
        'file': 'frozen_frames.py',
        'find': '    rep["blank"]["blankFrames"] = sum(1 for f in frames if f["state"] == BLANK)',
        'replace': '    rep["blank"]["blankFrames"] = run_len if run_len >= FROZEN_RUN else 0',
        'matches': 1,
    },
    {
        'why': 'putting the frozen bar above its ceiling so the FROZEN arm can never fire — his 34-frame run would read as a moving feed. A threshold no input can reach is an absent one',
        'file': 'frozen_frames.py',
        'find': '    if run_len >= FROZEN_RUN:',
        'replace': '    if run_len >= FROZEN_RUN + 99:',
        'matches': 1,
    },
    {
        'why': 'deleting the decode budget: a malformed or hostile IHDR then makes a gate allocate whatever it declares, in pure Python, inside a push that is already killed at ten minutes. UNKNOWN is the honest answer to "this would not fit"',
        'file': 'frozen_frames.py',
        'find': '    if h * stride > MAX_DECODE_BYTES:',
        'replace': '    if False:',
        'matches': 1,
    },
    {
        'why': 'accepting an interlaced PNG this decoder cannot read: the scanlines are Adam7 passes, not rows, so it would reconstruct a picture that was never in the file and hand a verdict about his screen based on it. A shape that is not supported must be refused, not approximated',
        'file': 'frozen_frames.py',
        'find': '    if interlace:\n        raise Unreadable("interlaced PNGs are not supported")',
        'replace': '    if False:\n        raise Unreadable("interlaced PNGs are not supported")',
        'matches': 1,
    },
    {
        'why': 'letting a decode window that was only half read report PAINTED. Some of the newest frames were never looked at, so "nothing is blank" would be a claim about a sample dressed as a claim about the window',
        'file': 'frozen_frames.py',
        'find': '    elif rep["undecodable"]:',
        'replace': '    elif False:',
        'matches': 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
