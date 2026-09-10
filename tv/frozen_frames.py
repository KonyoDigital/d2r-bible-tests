#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IS THE CAPTURE FEED STILL MOVING, AND IS ANYTHING DRAWN ON IT? — read from the FILES, not the page.

⚠⚠ MEASURED 2026-09-10 (#34). Grok Bot screencaptures his TV DIABLO window to `~/gb-shelf/`. While
it was doing that, its own status ticks read `GET / 200 · 1,744,954 bytes`, `GET /api/status 200`
and "quiet hold · census held" — and two of the frames those ticks were written beside, opened and
LOOKED AT, are a TV DIABLO window with nothing in it but the titlebar. One white, one dark.
**EVERY TEXT CHECK SAID HEALTHY WHILE THE SCREEN WAS DEAD.** A 200 from a server is evidence about
the server. The pixels are the only witness that can answer for the screen.
[[feedback-verify-ui-with-grok-eyes]] [[unknown-stays-unknown]]

⚠⚠ AND THE SECOND DETECTOR WAS SITTING IN THE FILE SIZES FOR FREE. A live console cannot capture
twice to the same bytes — the clock alone changes. Measured over his real shelf, 194 captures:

    34 byte-identical @ 286,148 B   09-09 20:57 -> 09-10 06:12   (dark blank, confirmed by eye)
    18 byte-identical @ 276,288 B   09-10 08:59 -> 09-10 16:16   (white blank, confirmed by eye)
    16 byte-identical @ 275,319 B   09-10 06:58 -> 09-10 08:44   (white blank, confirmed by eye)
    87 of 194 captures sit inside a repeated hash

── ⚠⚠ THE TWO FINDINGS ARE SEPARATE AND THIS MODULE NEVER MERGES THEM ─────────────────────────
A REPEATED HASH IS A POINTER, NOT A VERDICT. It says the feed stopped moving; it cannot say what
is on the screen. A window can be frozen on a perfectly painted frame (a wedged renderer holding
the last good paint), and a window can be blank while the clock in its titlebar still ticks, so
every frame differs. So:

    frozen  <- sha256 over the FILE BYTES. Says the feed repeated. Says nothing about content.
    blank   <- decoded PIXELS, judged by paint_witness's bar. Says nothing about repetition.

They are reported as two states in two fields with two reasons. Collapsing them would let a
confirmed-blank run be reported as "just frozen", and — worse — let a repeated hash be published
as a blank screen nobody ever looked at. Of the three runs above, two were opened and confirmed by
eye; the third was UNKNOWN until this module decoded it. It is now measured, not assumed.

── ⚠⚠ THE BAR IS paint_witness's, QUOTED, NEVER RE-TYPED ──────────────────────────────────────
`paint_witness.verdict()` already owns "is anything drawn on this window", calibrated against his
real console in both states plus three ordinary applications, with two scars in its own source
about thresholds that outlived their instrument. This module decodes a PNG into the exact bitmap
shape `paint_witness.measure()` consumes and asks IT. There is no second threshold here to drift
away from that one. [[copy-drift]]

⚠ WHAT THIS MODULE DOES OWN IS THE CROP, AND THE CROP IS LOAD-BEARING. paint_witness reads live
windows through `kCGWindowImageBoundsIgnoreFraming`, so its bitmap has no drop shadow. A file on
the shelf HAS one, and the shadow is not transparent — it is a soft alpha ramp. MEASURED on his
real white-blank capture (`heart2-212-215-20260910-065806.png`, 2376x1456):

    crop                                   modalShare   p99   brightShare   verdict
    none (shadow + titlebar included)         0.9199     255      0.9199     PAINTED   <- WRONG
    shadow trimmed + titlebar cropped         1.0000     255      0.0000     BLANK     <- right

0.9199 is under the 0.98 bar, and a WHITE blank window has p99 255 and a bright share of 92%, so
the ink test cannot fire on it either. Without the crop this module would call his confirmed-blank
window painted — the exact shape of paint_witness's own v2752 scar, where two rows of window chrome
at luminance 255 cleared both ink conditions on a completely black console. The trim is measured
from the ALPHA CHANNEL, not guessed: a row or column belongs to the window when at least
OPAQUE_SHARE of its sampled alphas are 255. [[feedback-threshold-above-the-ceiling]]

── ⚠ A ZERO NEEDS A DENOMINATOR ───────────────────────────────────────────────────────────────
"0 frozen" over 0 captures read is a broken reader wearing the clothes of a measurement. Every
report here carries `captures`, `examined` and `decoded`, and a scan that examined nothing is
UNKNOWN — never MOVING, never PAINTED. An unreadable directory is UNKNOWN. A file whose pixels
would not decode is UNKNOWN and is counted in `undecodable`, and while any of the newest frames is
undecodable the blank finding cannot read clean. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

── ⚠ THE AGE IS A SEPARATE QUESTION AGAIN ─────────────────────────────────────────────────────
FROZEN is a statement about the frames: the newest N are byte-identical. Whether that means his
console is frozen RIGHT NOW depends on when the newest one was written — a shelf nobody has
written to since Tuesday cannot testify about today. So `freshness` is its own field beside the
state, never folded into it. [[stale-reading]]

    python3 tv/frozen_frames.py                       # look at the default shelf, say what was seen
    python3 tv/frozen_frames.py --dir DIR --json
    python3 tv/frozen_frames.py --dir DIR --strict    # exit 1 on FROZEN or BLANK
"""
import hashlib
import json
import os
import struct
import sys
import time
import zlib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import paint_witness as PW  # noqa: E402

#: ⚠ QUOTED FROM paint_witness, NOT RE-TYPED — there is exactly one bar for "is anything drawn".
BLANK = PW.BLANK
PAINTED = PW.PAINTED
UNKNOWN = PW.UNKNOWN

#: the frozen-feed states. Deliberately NOT the same words as the blank states, so a reader can
#: never mistake one finding's answer for the other's.
FROZEN = "FROZEN"
MOVING = "MOVING"

#: was the window frontmost when the frame was taken, and — if the feed is frozen — which of the
#: two things the console said it could not tell apart is this. Four more words, still no merging.
KEY = "KEY"
NOT_KEY = "NOT_KEY"
WEDGED = "WEDGED"
THROTTLED = "THROTTLED"

#: WHICH ARM of paint_witness.verdict said BLANK, and they are NOT equally trustworthy.
#: ⚠⚠ MEASURED 2026-09-10 — THE INK ARM PRODUCED A FALSE BLANK ON HIS SHELF AND I OPENED THE FILE
#: TO CATCH IT. `VISUAL1-after.png` reads `p99 55, brightShare 0.26%` and the ink arm calls it
#: blank. It is a COMPLETE, fully painted console — MY HUNT, POLARIS SPEAR, the TZ tracker, THE
#: FLEET, a live tooltip — rendered in his DARK theme ("🌙 2 dark" in its own footer). Nothing is
#: wrong with the window; it is dim, and the ink arm's whole premise is that a painted console has
#: a bright tail.
#: The single-colour arm cannot make that mistake: 100% of a window being ONE colour is not a
#: rendering of anything. So the arm is REPORTED on every frame, and a caller that is about to do
#: something irreversible to his window on a BLANK verdict must look at which one fired.
#: This is paint_witness's Family A — "a wrong BLANK replaces the window he is looking at, mid-use"
#: — observed in the wild rather than in a harness. [[visual-regression-detector]]
ARM_SINGLE_COLOUR = "single-colour"
ARM_INK = "ink"

#: the traffic lights. MEASURED over the 134 window captures on his shelf that carry chrome:
#:     chroma <= 40    108 captures   grey lights, the window was not key
#:     41 .. 149         2 captures   unclassifiable, reported UNKNOWN
#:     chroma >= 150    24 captures   coloured lights, the window was key
#: Both bars sit inside a 109-wide empty band that holds 2 of 134 readings. A bar placed at the
#: edge of the population it must accept is a bar that fails on the next capture.
KEY_CHROMA_MIN = 150
GREY_CHROMA_MAX = 40

#: ⚠ ALSO QUOTED. paint_witness's own doctrine is that a single frame is a sample and consecutive
#: agreeing frames are what justify acting; `BLANK_STRIKES` is that number. A frozen run is the
#: same shape of claim, so it uses the same number rather than inventing a second one.
FROZEN_RUN = PW.BLANK_STRIKES

#: how many of the newest captures get their BYTES hashed, and how many get their PIXELS decoded.
#: Decoding is the expensive half (0.6-2.3s per capture of his window, pure Python), so the two
#: windows are separate numbers rather than one compromise.
NEWEST_HASHED = 16
NEWEST_DECODED = 4

#: a capture older than this cannot testify about the present. Reported, never folded into a state.
STALE_SEC = 900

#: a row/column belongs to the window when this share of its sampled alphas is fully opaque. The
#: drop shadow is a soft ramp, so "alpha != 0" trims almost nothing — MEASURED on his shelf, an
#: alpha!=0 trim left 2376x1456 at 2375x1448 and the white blank still read PAINTED.
#: ⚠ 0.60 AND NOT 0.90, AND THE REASON IS THAT THE TWO POPULATIONS ARE NOWHERE NEAR EACH OTHER. A
#: shadow row has ~0% fully-opaque pixels; a window row has as many as the window is wide — 92.7%
#: on his 2376px captures, 86.7% on a narrower one. 0.90 sat INSIDE the second population and
#: would trim the whole picture away on any capture whose margins are a little wider; 0.60 sits in
#: the empty middle. A bar set at the edge of the values it must accept is a bar that fails on the
#: next capture, not on this one. [[feedback-threshold-above-the-ceiling]]
OPAQUE_SHARE = 0.60

#: how much of the window's own height is OS titlebar rather than anything the page drew. His
#: window chrome measures 73px of a 1372px window in these 2x captures (5.3%); paint_witness's own
#: CHROME_TOP_PX is 36 of a 660px window (5.45%) — the same chrome, so the same FRACTION at any
#: scale, which is why this is a fraction and not a pixel count that would be wrong on every
#: capture that is not exactly his window size. 8% is that measurement with headroom.
#: ⚠ paint_witness.measure() then crops its own CHROME_TOP_PX on top of this. That is additive and
#: deliberate: it keeps paint_witness the sole owner of "skip the chrome", and 36 more rows of a
#: 1300-row window is 2.7% of content, against a bar with a 0.43 margin.
CHROME_TOP_FRACTION = 0.08
#: rounded window corners and the 1px window border are not evidence about what the page drew.
SIDE_FRACTION = 0.02

#: a decode that would allocate more than this is refused as UNKNOWN rather than attempted. Pure
#: Python unfiltering runs ~0.45s per raw MB on the history-dependent filters (Up/Average/Paeth).
MAX_DECODE_BYTES = 96 * 1024 * 1024

CAPTURE_EXTS = (".png",)

#: where Grok Bot puts his window. Only a DEFAULT for the CLI — nothing in this module reads it
#: unless a caller asks for it, and no test may point at it. [[feedback-fixtures-never-touch-live-data]]
DEFAULT_DIR = os.path.expanduser("~/gb-shelf")

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
#: samples/channels per PNG colour type. 3 (palette) is absent on purpose — it needs PLTE and no
#: screen capture produces it, so it is reported UNKNOWN rather than half-decoded.
_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


class Unreadable(Exception):
    """This file's pixels could not be established. The answer is UNKNOWN, never PAINTED."""


# ── the PNG reader: stdlib only, zlib + struct ───────────────────────────────────────────────────
def png_rows(path):
    """Fully reconstructed scanlines. -> (w, h, channels, [bytearray, ...])

    ⚠ EVERY refusal raises Unreadable with a reason. Nothing here returns a plausible-looking
    bitmap it did not actually decode — a wrong bitmap would be published as a verdict about his
    screen, and a missing one is merely unknown.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    if blob[:8] != _PNG_SIG:
        raise Unreadable("not a PNG (signature is %r)" % blob[:8])
    ihdr, idat, i = None, [], 8
    while i + 12 <= len(blob):
        (ln,), typ = struct.unpack(">I", blob[i:i + 4]), blob[i + 4:i + 8]
        body = blob[i + 8:i + 8 + ln]
        if typ == b"IHDR":
            ihdr = body
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        i += 12 + ln
    if ihdr is None or len(ihdr) < 13:
        raise Unreadable("no IHDR chunk")
    if not idat:
        raise Unreadable("no IDAT chunk")
    w, h, depth, colour, _comp, _filt, interlace = struct.unpack(">IIBBBBB", ihdr[:13])
    if depth != 8:
        raise Unreadable("bit depth %d is not supported (only 8)" % depth)
    if interlace:
        raise Unreadable("interlaced PNGs are not supported")
    if colour not in _CHANNELS:
        raise Unreadable("colour type %d is not supported" % colour)
    ch = _CHANNELS[colour]
    stride = 1 + w * ch
    if not w or not h:
        raise Unreadable("IHDR declares %dx%d" % (w, h))
    if h * stride > MAX_DECODE_BYTES:
        raise Unreadable("%dx%d would decode to %.0f MB, over the %.0f MB budget"
                         % (w, h, h * stride / 1048576.0, MAX_DECODE_BYTES / 1048576.0))
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as e:
        raise Unreadable("the IDAT stream would not inflate (%s)" % e)
    if len(raw) < h * stride:
        raise Unreadable("truncated: %d bytes of scanline data, %d needed" % (len(raw), h * stride))
    rows, prev = [], bytearray(w * ch)
    for r in range(h):
        f = raw[r * stride]
        cur = bytearray(raw[r * stride + 1:(r + 1) * stride])
        if f == 0:
            pass
        elif f == 1:                                             # Sub
            for k in range(ch, len(cur)):
                cur[k] = (cur[k] + cur[k - ch]) & 255
        elif f == 2:                                             # Up
            for k in range(len(cur)):
                cur[k] = (cur[k] + prev[k]) & 255
        elif f == 3:                                             # Average
            for k in range(len(cur)):
                a = cur[k - ch] if k >= ch else 0
                cur[k] = (cur[k] + ((a + prev[k]) >> 1)) & 255
        elif f == 4:                                             # Paeth
            for k in range(len(cur)):
                a = cur[k - ch] if k >= ch else 0
                b = prev[k]
                c = prev[k - ch] if k >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                cur[k] = (cur[k] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        else:
            raise Unreadable("scanline %d declares filter %d, which is not a PNG filter" % (r, f))
        rows.append(cur)
        prev = cur
    return w, h, ch, rows


def window_rect(w, h, ch, rows):
    """The opaque window inside the drop shadow. -> (x0, y0, x1, y1)

    ⚠ MEASURED FROM THE ALPHA CHANNEL. On a capture with no alpha there is nothing to measure and
    the whole image is the rect — stated, not silently assumed to be shadow-free.
    """
    if ch not in (2, 4):
        return 0, 0, w, h
    ai = ch - 1
    xs = list(range(0, w, max(1, w // 120)))
    ys = list(range(0, h, max(1, h // 120)))

    def row_is_window(y):
        row = rows[y]
        return sum(1 for x in xs if row[x * ch + ai] == 255) >= OPAQUE_SHARE * len(xs)

    def col_is_window(x):
        return sum(1 for y in ys if rows[y][x * ch + ai] == 255) >= OPAQUE_SHARE * len(ys)

    y0, y1 = 0, h
    while y0 < h and not row_is_window(y0):
        y0 += 1
    while y1 > y0 and not row_is_window(y1 - 1):
        y1 -= 1
    x0, x1 = 0, w
    while x0 < w and not col_is_window(x0):
        x0 += 1
    while x1 > x0 and not col_is_window(x1 - 1):
        x1 -= 1
    # ⚠ A trim that ate the picture is a broken instrument, not a tiny window. Fall back to the
    # whole image and let the bar judge that, rather than reporting a measurement of 6 pixels.
    if (y1 - y0) < 8 or (x1 - x0) < 8:
        return 0, 0, w, h
    return x0, y0, x1, y1


def shot(path):
    """A capture file in the exact bitmap shape paint_witness.measure() consumes. -> (shot, rect)"""
    w, h, ch, rows = png_rows(path)
    x0, y0, x1, y1 = window_rect(w, h, ch, rows)
    win_w, win_h = x1 - x0, y1 - y0
    cy0 = y0 + int(win_h * CHROME_TOP_FRACTION)
    cx0 = x0 + int(win_w * SIDE_FRACTION)
    cx1 = x1 - int(win_w * SIDE_FRACTION)
    if cx1 - cx0 < 4 or y1 - cy0 < 4:
        raise Unreadable("the window rect %dx%d leaves nothing to measure after the chrome crop"
                         % (win_w, win_h))
    if ch < 3:                                   # greyscale -> RGB, so three bytes mean three
        body = bytearray()
        for row in rows[cy0:y1]:
            for v in row[cx0 * ch:cx1 * ch:ch]:
                body += bytes((v, v, v))
        out_ch = 3
    else:
        body = bytearray(b"".join(bytes(row[cx0 * ch:cx1 * ch]) for row in rows[cy0:y1]))
        out_ch = ch
        # ⚠ paint_witness reads `b, g, r = buf[o], buf[o+1], buf[o+2]` because Quartz hands it
        # BGRA. PNG is RGBA. Swapping here rather than there keeps the luminance weights (299/587/
        # 114) applied to the channels they were written for — on a grey window the swap changes
        # nothing, which is exactly why leaving it out would never have been caught by a fixture.
        red = body[0::out_ch]
        body[0::out_ch] = body[2::out_ch]
        body[2::out_ch] = red
    cw, chh = cx1 - cx0, y1 - cy0
    return ({"w": cw, "h": chh, "buf": bytes(body), "bpr": cw * out_ch, "bpp": out_ch},
            (x0, y0, x1, y1))


def look(path):
    """BLANK / PAINTED / UNKNOWN for one capture FILE. -> dict, always the same shape.

    ⚠ `arm` names WHICH of paint_witness's two blank tests fired, because one of them has been
    seen to be wrong on his own data and the other cannot be. See ARM_INK above.
    """
    out = {"file": os.path.basename(path), "state": UNKNOWN, "why": "", "rect": None,
           "measure": None, "arm": None}
    try:
        sh, rect = shot(path)
    except Unreadable as e:
        out["why"] = "the pixels could not be read: %s" % e
        return out
    except Exception as e:                       # pragma: no cover - a reader fault is still UNKNOWN
        out["why"] = "the reader failed on this file (%s: %s)" % (type(e).__name__, e)
        return out
    m = PW.measure(sh)
    state, why = PW.verdict(m)
    out.update({"state": state, "why": why, "measure": m, "rect": list(rect)})
    if state == BLANK:
        # ⚠ read from the MEASUREMENT against paint_witness's own constant, never by matching the
        # wording of its sentence — a reason string is prose and it is allowed to be reworded.
        out["arm"] = (ARM_SINGLE_COLOUR if (m.get("modalShare") or 0) >= PW.BLANK_MODAL_SHARE
                      else ARM_INK)
    return out


# ── WEDGED or THROTTLED: the question the console said it could not answer ───────────────────────
def key_state(path):
    """Was this window FRONTMOST at the moment this frame was taken? -> dict

    ⚠⚠ THE ANSWER IS IN THE FILE, WHICH IS WHY IT CAN BE ASKED ABOUT HISTORY AT ALL. macOS draws
    a KEY window's three traffic lights in red/yellow/green and a NON-KEY window's in flat grey.
    That is a per-capture record of key state, written by the window server at capture time —
    unlike asking the window server NOW, which says nothing whatever about a frame from 08:59.
    [[stale-reading]]

    MEASURED on his shelf, max chroma (max(R,G,B) - min(R,G,B)) in the traffic-light corner:

        heart2-212-215-...png    chroma   0   grey lights   BLANK, one of the 16-frame run
        HEART2-LOOK-90-95.png    chroma   5   grey lights   BLANK, one of the 34-frame run
        heart2-...-190801-IDT    chroma   5   grey lights   BLANK, his 19:08 exhibit
        HEART2-LOOK-153.png      chroma 227   rgb(229,177,2) — the yellow light. KEY.

    ⚠ IT NEEDS THE CHROME, SO IT NEEDS THE SHADOW. A capture with no drop shadow was not taken of
    a single window (a full-screen grab, a crop), the titlebar cannot be located in it, and the
    answer is UNKNOWN rather than a reading of whatever happens to sit in that corner.
    """
    out = {"state": UNKNOWN, "chroma": None, "samples": 0, "why": ""}
    try:
        w, h, ch, rows = png_rows(path)
    except Unreadable as e:
        out["why"] = "the pixels could not be read: %s" % e
        return out
    if ch < 3:
        out["why"] = "a greyscale capture carries no colour, so the lights cannot be read"
        return out
    x0, y0, x1, y1 = window_rect(w, h, ch, rows)
    if (x0, y0, x1, y1) == (0, 0, w, h):
        out["why"] = ("no window chrome was found: nothing in this capture is a drop shadow, so it "
                      "was not taken of one window and the titlebar cannot be located")
        return out
    win_w, win_h = x1 - x0, y1 - y0
    best, n = 0, 0
    for yy in range(y0 + int(win_h * 0.012), y0 + max(int(win_h * 0.055), 2), 2):
        row = rows[yy]
        for xx in range(x0 + int(win_w * 0.004), x0 + max(int(win_w * 0.09), 2), 2):
            o = xx * ch
            r, g, b = row[o], row[o + 1], row[o + 2]
            n += 1
            s = max(r, g, b) - min(r, g, b)
            if s > best:
                best = s
    out["chroma"], out["samples"] = best, n
    if not n:
        out["why"] = "the titlebar corner had no pixels to sample"
        return out
    if best >= KEY_CHROMA_MIN:
        out["state"] = KEY
        out["why"] = ("the traffic lights are COLOURED (chroma %d over %d samples) — macOS draws "
                      "them grey on a window that is not key, so this window was frontmost when "
                      "the frame was taken" % (best, n))
    elif best <= GREY_CHROMA_MAX:
        out["state"] = NOT_KEY
        out["why"] = ("the titlebar is GREYSCALE (chroma %d over %d samples) — the traffic lights "
                      "are not coloured, so this window was NOT frontmost when the frame was taken"
                      % (best, n))
    else:
        # ⚠ THE MIDDLE IS UNKNOWN AND IT IS NOT EMPTY BY ACCIDENT. A value between the two bars is
        # a titlebar this instrument cannot classify, and guessing which side it falls on is how a
        # harmless background window gets reported as his black-screen fault.
        out["why"] = ("chroma %d over %d samples sits between the grey bar (%d) and the coloured "
                      "bar (%d) — this titlebar cannot be classified"
                      % (best, n, GREY_CHROMA_MAX, KEY_CHROMA_MIN))
    return out


def frontmost_app():
    """Which application is frontmost RIGHT NOW. -> (name or None, why)

    ⚠⚠ REPORTED, NEVER DECIDING, AND THAT IS THE WHOLE POINT OF WHERE IT SITS. Two reasons, and
    each one alone would be enough:

      1. IT IS ABOUT NOW. His frozen runs are hours old. What is in front at this second says
         nothing about what was in front at 08:59, and the frames themselves carry that answer.
         [[stale-reading]]
      2. DECIDING ON IT WOULD NEED A CONSTANT NOBODY HAS VERIFIED — the display name his pywebview
         console registers under. His console was not running when this was written, so that name
         could only have been guessed, and a guessed string in a comparison quietly answers False
         forever. A threshold nobody measured is an absent one. [[unknown-stays-unknown]]

    So this returns the NAME and the caller prints it beside the verdict as context. `lsappinfo`
    is read-only, instant, and needs no Automation grant — unlike osascript, which prompts. Off
    macOS it does not exist and the answer is None, which is not "nothing is frontmost".
    """
    try:
        import subprocess
        asn = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True,
                             timeout=5).stdout.strip()
        if not asn:
            return None, "lsappinfo named no front application"
        out = subprocess.run(["lsappinfo", "info", "-only", "name", asn],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        name = out.split("=")[-1].strip().strip('"') if "=" in out else out
        if not name:
            return None, "the front application (%s) would not give its name" % asn
        return name, "the front application is %r" % name
    except Exception as e:
        return None, "the front application could not be established (%s)" % type(e).__name__


def disambiguate(rep):
    """WEDGED / THROTTLED / UNKNOWN for a frozen feed. -> dict

    ⚠⚠ THE CONSOLE ASKED THIS QUESTION IN ITS OWN WORDS AND SAID IT COULD NOT ANSWER IT: "TWO
    THINGS LOOK LIKE THIS ... the window is simply not frontmost (WebKit throttles frames in the
    background, which is normal and harmless), or the renderer has wedged while the DOM stays
    alive". This answers it from the pixels, and refuses to answer where the pixels cannot.

    ⚠⚠ AND ONE COMBINATION IS DELIBERATELY UNKNOWN RATHER THAN THROTTLED — the one his shelf is
    actually full of. Throttling freezes the LAST PAINTED FRAME; it does not empty a window. So a
    background window that is also BLANK is not explained by throttling — but nothing here has
    measured what does explain it, and filing his real fault under "normal and harmless" is the
    one error that would make this whole module worse than nothing. It reports the contradiction.
    [[unknown-stays-unknown]] [[feedback-contradiction-is-the-finding]]
    """
    out = {"state": UNKNOWN, "why": "", "keyState": UNKNOWN, "keyWhy": "",
           "frontmostAppNow": None, "frontmostWhy": "not asked"}
    f, b = rep.get("frozen") or {}, rep.get("blank") or {}
    if f.get("state") != FROZEN:
        out["why"] = ("the feed is %s, so there is no frozen frame to tell apart from a throttled "
                      "one" % f.get("state"))
        return out
    frames = b.get("frames") or []
    if not frames:
        out["why"] = "no frame was decoded, so the titlebar could never be read"
        return out
    ks = key_state(os.path.join(rep["dir"], frames[0]["file"]))
    out["keyState"], out["keyWhy"] = ks["state"], ks["why"]
    if f.get("freshness") == "FRESH":
        name, why = frontmost_app()
        out["frontmostAppNow"], out["frontmostWhy"] = name, why
    else:
        out["frontmostWhy"] = ("the newest capture is %ss old, and what is frontmost NOW says "
                               "nothing about what was frontmost then" % f.get("ageSec"))
    arm = frames[0].get("arm")
    if ks["state"] == KEY:
        out["state"] = WEDGED
        out["why"] = ("the feed is FROZEN and the window was FRONTMOST when the frame was taken "
                      "(%s). A window that is on top and still draws nothing is not being "
                      "throttled — that is the wedge." % ks["why"])
    elif ks["state"] == NOT_KEY and b.get("state") == PAINTED:
        out["state"] = THROTTLED
        out["why"] = ("the feed is FROZEN, the window was NOT frontmost (%s), and its last frame "
                      "still has content on it. That is what WebKit throttling looks like: the "
                      "last painted frame, held. Harmless." % ks["why"])
    elif ks["state"] == NOT_KEY and b.get("state") == BLANK:
        out["why"] = (
            "the window was NOT frontmost (%s), which would normally read as harmless throttling "
            "— but the newest frame is BLANK (by the %s test), and throttling holds the LAST "
            "PAINTED FRAME rather than emptying a window. The two readings CONTRADICT, nothing "
            "here has measured which is true, and this is NOT being filed as harmless.%s"
            % (ks["why"], arm,
               "" if arm == ARM_SINGLE_COLOUR else
               " ⚠ and the ink test is the one that has been seen to call a dim but fully "
               "painted console blank, so the BLANK half is itself a candidate, not a fact."))
    else:
        out["why"] = ("the window's key state could not be established (%s), so a frozen feed "
                      "cannot be told apart from a throttled one" % ks["why"])
    return out


# ── the feed: bytes only, no decoding ────────────────────────────────────────────────────────────
def captures(directory):
    """Every capture in the directory, oldest first. -> (entries, why)

    An entry is {"name", "path", "mtime", "size"}. `why` is non-empty only when the directory
    itself could not be read — and then `entries` is None, NOT an empty list, because an empty
    list would be indistinguishable from a directory with nothing in it.
    """
    try:
        names = os.listdir(directory)
    except Exception as e:
        return None, "the capture directory could not be listed (%s: %s)" % (type(e).__name__, e)
    out = []
    for n in sorted(names):
        if not n.lower().endswith(CAPTURE_EXTS):
            continue
        p = os.path.join(directory, n)
        try:
            st = os.stat(p)
        except Exception:
            continue                              # vanished between listdir and stat
        if not os.path.isfile(p):
            continue
        out.append({"name": n, "path": p, "mtime": st.st_mtime, "size": st.st_size})
    out.sort(key=lambda e: (e["mtime"], e["name"]))
    return out, ""


def sha_of(path):
    """sha256 of the file's bytes, or None if it could not be read."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()
    except Exception:
        return None


def frozen_runs(entries):
    """Every repeated hash among these entries. -> [{"sha","count","first","last","bytes","names"}]

    ⚠ A POINTER, NOT A VERDICT. This function knows nothing about what is on the screen and must
    never grow an opinion about it.
    """
    by = {}
    for e in entries:
        if not e.get("sha"):
            continue
        by.setdefault(e["sha"], []).append(e)
    runs = []
    for sha, members in by.items():
        if len(members) < 2:
            continue
        runs.append({"sha": sha, "count": len(members),
                     "first": members[0]["mtime"], "last": members[-1]["mtime"],
                     "bytes": members[0]["size"],
                     "names": [m["name"] for m in members]})
    runs.sort(key=lambda r: (-r["count"], r["first"]))
    return runs


def newest_identical_run(entries):
    """How many of the NEWEST consecutive captures are byte-identical. -> (n, sha)"""
    if not entries:
        return 0, None
    sha = entries[-1].get("sha")
    if not sha:
        return 0, None
    n = 0
    for e in reversed(entries):
        if e.get("sha") != sha:
            break
        n += 1
    return n, sha


# ── the report ───────────────────────────────────────────────────────────────────────────────────
def scan(directory, newest=NEWEST_HASHED, decode=NEWEST_DECODED, now=None):
    """FROZEN and BLANK as two separate findings over one capture directory. -> dict"""
    now = time.time() if now is None else now
    rep = {
        "dir": directory, "at": now, "ok": False,
        "captures": 0, "examined": 0, "decoded": 0, "undecodable": 0,
        "why": [],
        "frozen": {"state": UNKNOWN, "why": "nothing has been examined yet",
                   "runLength": None, "bar": FROZEN_RUN, "sha": None,
                   "runs": [], "framesInRuns": 0,
                   "freshness": UNKNOWN, "ageSec": None, "staleAfterSec": STALE_SEC},
        "blank": {"state": UNKNOWN, "why": "nothing has been decoded yet",
                  "blankFrames": 0, "bySingleColour": 0, "byInk": 0, "frames": []},
        "wedge": {"state": UNKNOWN, "why": "nothing has been examined yet",
                  "keyState": UNKNOWN, "keyWhy": "", "frontmostAppNow": None,
                  "frontmostWhy": "not asked"},
        "findings": [], "verdict": "",
    }
    entries, why = captures(directory)
    if entries is None:
        rep["why"].append(why)
        rep["frozen"]["why"] = why
        rep["blank"]["why"] = why
        rep["verdict"] = _verdict(rep)
        return rep
    rep["ok"] = True
    rep["captures"] = len(entries)

    window = entries[-int(newest):] if newest and newest > 0 else list(entries)
    for e in window:
        e["sha"] = sha_of(e["path"])
    read = [e for e in window if e.get("sha")]
    rep["examined"] = len(read)

    # ⚠⚠ A ZERO NEEDS A DENOMINATOR. "0 frozen" over 0 captures examined is a broken reader, and it
    # is the single most convincing wrong answer this module could give — it looks exactly like a
    # healthy feed. Both findings stay UNKNOWN here and nothing below can talk them out of it.
    if not read:
        rep["frozen"]["why"] = ("nothing could be examined: %d capture file(s) in the directory, "
                                "%d readable — an unread feed is UNKNOWN, not moving"
                                % (len(entries), 0))
        rep["blank"]["why"] = ("nothing could be decoded: 0 of %d capture(s) were read"
                               % len(entries))
        rep["verdict"] = _verdict(rep)
        return rep

    runs = frozen_runs(read)
    run_len, run_sha = newest_identical_run(read)
    age = now - read[-1]["mtime"]
    rep["frozen"].update({
        "runs": runs, "framesInRuns": sum(r["count"] for r in runs),
        "runLength": run_len, "sha": run_sha, "ageSec": round(age, 1),
        "freshness": "FRESH" if age <= STALE_SEC else "STALE",
    })
    if run_len >= FROZEN_RUN:
        rep["frozen"]["state"] = FROZEN
        rep["frozen"]["why"] = (
            "the newest %d of %d capture(s) examined are BYTE-IDENTICAL (%s..., %s bytes) — a live "
            "console cannot capture twice to the same bytes, the clock alone changes. This says "
            "the feed stopped moving; it says NOTHING about what is on the screen"
            % (run_len, len(read), (run_sha or "")[:12], "{:,}".format(read[-1]["size"])))
    else:
        rep["frozen"]["state"] = MOVING
        rep["frozen"]["why"] = (
            "the newest %d of %d capture(s) examined differ (a run of %d is needed before this "
            "reads FROZEN); %d frame(s) sit in a repeated hash further back"
            % (min(FROZEN_RUN, len(read)), len(read), FROZEN_RUN,
               sum(r["count"] for r in runs)))

    to_decode = read[-int(decode):] if decode and decode > 0 else []
    frames = [look(e["path"]) for e in reversed(to_decode)]      # newest first
    rep["blank"]["frames"] = frames
    rep["decoded"] = sum(1 for f in frames if f["state"] != UNKNOWN)
    rep["undecodable"] = sum(1 for f in frames if f["state"] == UNKNOWN)
    rep["blank"]["blankFrames"] = sum(1 for f in frames if f["state"] == BLANK)
    rep["blank"]["bySingleColour"] = sum(1 for f in frames if f.get("arm") == ARM_SINGLE_COLOUR)
    rep["blank"]["byInk"] = sum(1 for f in frames if f.get("arm") == ARM_INK)

    if not frames:
        rep["blank"]["why"] = ("no capture was decoded: %d examined, decode window %d"
                               % (len(read), decode))
    elif rep["decoded"] == 0:
        rep["blank"]["why"] = ("none of the %d newest capture(s) would decode — UNKNOWN, which is "
                               "not the same as painted: %s"
                               % (len(frames), frames[0]["why"]))
    elif rep["blank"]["blankFrames"]:
        rep["blank"]["state"] = BLANK
        rep["blank"]["why"] = ("%d of the %d newest capture(s) decoded have NOTHING DRAWN on them "
                               "(%d by the single-colour test, %d by the INK test which has been "
                               "seen to call a dim but fully painted console blank; %d could not "
                               "be decoded). Newest blank frame: %s — %s"
                               % (rep["blank"]["blankFrames"], rep["decoded"],
                                  rep["blank"]["bySingleColour"], rep["blank"]["byInk"],
                                  rep["undecodable"],
                                  next(f["file"] for f in frames if f["state"] == BLANK),
                                  next(f["why"] for f in frames if f["state"] == BLANK)))
    elif rep["undecodable"]:
        # ⚠ UNKNOWN STAYS UNKNOWN. Some of the newest frames were never looked at, so "nothing is
        # blank" is a claim about a sample, not about the window. [[unknown-stays-unknown]]
        rep["blank"]["why"] = ("%d of the %d newest capture(s) decoded and are painted, but %d "
                               "could not be decoded at all — the newest frames are not all "
                               "accounted for" % (rep["decoded"], len(frames), rep["undecodable"]))
    else:
        rep["blank"]["state"] = PAINTED
        rep["blank"]["why"] = ("all %d of the newest capture(s) have content drawn on them: %s"
                               % (rep["decoded"], frames[0]["why"]))

    rep["wedge"] = disambiguate(rep)
    rep["verdict"] = _verdict(rep)
    return rep


def _verdict(rep):
    """One line that names ALL THREE findings and their denominators. -> str

    ⚠ The states are printed side by side and never reduced to one word. A caller that wants a
    single boolean has to decide which question it is asking, which is the point.
    """
    f, b, wg = rep["frozen"], rep["blank"], rep["wedge"]
    rep["findings"] = [
        "FEED  %-9s %s" % (f["state"], f["why"]),
        "PIXEL %-9s %s" % (b["state"], b["why"]),
        "CAUSE %-9s %s" % (wg["state"], wg["why"]),
    ]
    return ("feed=%s pixels=%s cause=%s | %d capture(s) in the directory, %d examined, %d decoded, "
            "%d undecodable | freshness=%s" %
            (f["state"], b["state"], wg["state"], rep["captures"], rep["examined"], rep["decoded"],
             rep["undecodable"], f["freshness"]))


def main(argv):
    directory, as_json, strict = DEFAULT_DIR, False, False
    newest, decode = NEWEST_HASHED, NEWEST_DECODED
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--dir" and i + 1 < len(argv):
            directory = os.path.expanduser(argv[i + 1]); i += 1
        elif a == "--newest" and i + 1 < len(argv):
            newest = int(argv[i + 1]); i += 1
        elif a == "--decode" and i + 1 < len(argv):
            decode = int(argv[i + 1]); i += 1
        elif a == "--json":
            as_json = True
        elif a == "--strict":
            strict = True
        i += 1
    rep = scan(directory, newest=newest, decode=decode)
    if as_json:
        print(json.dumps(rep, indent=1, sort_keys=True, default=str))
    else:
        print("%s  %s" % (os.path.basename(directory) or directory, rep["verdict"]))
        for line in rep["findings"]:
            print("  " + line)
        for r in rep["frozen"]["runs"][:5]:
            print("    run of %-3d @ %10s bytes  %s -> %s  %s..."
                  % (r["count"], "{:,}".format(r["bytes"]),
                     time.strftime("%m-%d %H:%M", time.localtime(r["first"])),
                     time.strftime("%m-%d %H:%M", time.localtime(r["last"])), r["sha"][:12]))
        for fr in rep["blank"]["frames"]:
            print("    %-8s %s" % (fr["state"], fr["file"]))
    if rep["frozen"]["state"] == UNKNOWN and rep["blank"]["state"] == UNKNOWN:
        return 2
    if strict and (rep["frozen"]["state"] == FROZEN or rep["blank"]["state"] == BLANK):
        return 1
    return 0


if __name__ == "__main__":
    # ⚠ WINDOWS PRINTS THIS FILE'S VERDICT IN cp1255, AND AN EMOJI IS A CRASH THERE, NOT A MOJIBAKE.
    # This module reports with ⚠/✅ characters, so on a non-UTF-8 console it would die WHILE
    # REPORTING — a clean tree exiting non-zero, with the traceback where the answer should be.
    # Guarded here rather than at import so the library path stays side-effect free.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
