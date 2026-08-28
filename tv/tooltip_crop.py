#!/usr/bin/env python3
"""FIND THE TOOLTIP RECTANGLE by differencing frames in a hover run.

⚠ WHY THIS IS DERIVABLE AND #31 IS NOT. Both want geometry out of his footage, and I had them filed
as the same kind of blocked. They are not:

  #31 wants SLOT identity — which cell of the stash lattice an item sits in. That needs the lattice
      calibrated against a real stash frame AND a reader that emits a coordinate, and
      tv_diablo.claude_vault_read returns {items, conf, surface, note} with no coordinate anywhere.

  THIS wants the TOOLTIP rectangle, and vault_retro:1091 already records the property that gives it
      away for free: "on a tooltip pass the panel is identical frame to frame and only a small
      tooltip rectangle changes". So the rectangle IS the difference between consecutive frames.
      Nothing to calibrate, no schema change, no new reader.

WHAT IT IS FOR (#45). Every receipt already carries a frameId. With the rectangle, the crop that
NAMED an item can be stored beside the item — so when the console says he owns Shako, he can see the
tooltip it read. That is the difference between a ledger that asserts and a ledger that shows.

⚠ IT DECIDES NOTHING ABOUT OWNERSHIP. It answers "where on this frame did the picture change", never
"what does it say". A crop is evidence to look at, not a second witness — treating it as one would
double-count the single look that produced it. [[d2r-multiwitness-corroboration]]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# A tooltip is a small overlay, never the whole panel. These bounds are what separate "the tooltip
# moved" from "he changed tab" or "the reel cut" — and a diff that covers most of the frame is the
# SECOND case, which must be refused rather than cropped.
MIN_FRAC = 0.002      # below this the difference is JPEG noise, not a drawn rectangle
MAX_FRAC = 0.45       # above this the whole screen changed; that is not a tooltip
PAD = 6               # a few pixels of margin so the border is not shaved off


def _gray(path):
    """Load as greyscale. -> (pixels, w, h) or (None, why, None)"""
    try:
        from PIL import Image
    except Exception as e:
        return None, "PIL is not available: %s" % str(e)[:60], None
    try:
        im = Image.open(path).convert("L")
    except Exception as e:
        return None, "could not open %s: %s" % (os.path.basename(path), str(e)[:60]), None
    return list(im.getdata()), im.size[0], im.size[1]


def changed_rect(path_a, path_b, thresh=18):
    """The bounding box of what differs between two frames. -> (rect|None, why)

    rect is (left, top, right, bottom) in pixels. `thresh` is per-pixel greyscale distance; JPEG
    ringing around static text runs well under it.
    """
    a, wa, ha = _gray(path_a)
    if a is None:
        return None, wa
    b, wb, hb = _gray(path_b)
    if b is None:
        return None, wb
    if (wa, ha) != (wb, hb):
        # ⚠ DIFFERENT SIZES IS NOT A TOOLTIP, and silently resizing would invent a rectangle.
        return None, ("frames differ in size (%dx%d vs %dx%d) — that is a capture change, not a "
                      "tooltip" % (wa, ha, wb, hb))
    lo_x, lo_y, hi_x, hi_y, n = wa, ha, -1, -1, 0
    for i, (pa, pb) in enumerate(zip(a, b)):
        if abs(pa - pb) < thresh:
            continue
        n += 1
        y, x = divmod(i, wa)
        if x < lo_x: lo_x = x
        if x > hi_x: hi_x = x
        if y < lo_y: lo_y = y
        if y > hi_y: hi_y = y
    if hi_x < 0:
        return None, "the two frames are identical above the noise threshold"
    frac = float(n) / (wa * ha)
    if frac < MIN_FRAC:
        return None, ("only %.3f%% of pixels moved — below the %.1f%% floor, so this is noise "
                      "rather than a drawn rectangle" % (frac * 100, MIN_FRAC * 100))
    if frac > MAX_FRAC:
        return None, ("%.1f%% of the frame changed — above the %.0f%% ceiling, so the whole screen "
                      "moved and no tooltip can be claimed" % (frac * 100, MAX_FRAC * 100))
    rect = (max(0, lo_x - PAD), max(0, lo_y - PAD),
            min(wa, hi_x + PAD + 1), min(ha, hi_y + PAD + 1))
    return rect, None


def crop_to(path, rect, dest):
    """Write the crop. -> (ok, why)"""
    try:
        from PIL import Image
        im = Image.open(path)
        im.crop(rect).save(dest)
        return True, None
    except Exception as e:
        return False, "could not write the crop: %s" % str(e)[:80]


def bounds_are_reachable():
    """PROVE the floor and ceiling admit a real tooltip. -> (ok, why)

    A window that nothing can fall inside is an absent gate wearing tuned numbers, and I shipped
    exactly that mistake earlier today on the vault confluence floors.
    [[feedback-threshold-above-the-ceiling]]
    """
    if not (0 < MIN_FRAC < MAX_FRAC < 1):
        return False, "the bounds are not an interval: %r .. %r" % (MIN_FRAC, MAX_FRAC)
    # A D2R tooltip on a 1440x900 panel runs roughly 260x300 = 6% of the frame. It must fit.
    typical = (260.0 * 300.0) / (1440.0 * 900.0)
    if not (MIN_FRAC < typical < MAX_FRAC):
        return False, ("a typical tooltip covers %.1f%% of the frame, outside the %.1f%%-%.0f%% "
                       "window — this could never fire"
                       % (typical * 100, MIN_FRAC * 100, MAX_FRAC * 100))
    return True, None


def main(argv=None):
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    ok, why = bounds_are_reachable()
    print("tooltip crop — bounds %s" % ("\U0001f7e2 reachable" if ok else "\U0001f534 %s" % why))
    argv = list(argv or [])
    if len(argv) >= 2:
        rect, why = changed_rect(argv[0], argv[1])
        print("  rect: %s" % (rect if rect else "⚪ UNKNOWN — %s" % why))
        if rect and len(argv) >= 3:
            good, w = crop_to(argv[0], rect, argv[2])
            print("  wrote %s" % argv[2] if good else "  \U0001f534 %s" % w)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
