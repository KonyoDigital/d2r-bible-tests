#!/usr/bin/env python3
"""Turn ONE captured game frame into a zone `*_graphic.png` in the family's style.

WHY THIS EXISTS. REG-113 has been open since v1639 and is fully diagnosed: the game ships a
TILESET for Halls of Anguish (levels.txt -> "Act 5 - Temple 1", LevelType 32; lvltypes.txt ->
Expansion/wildtemple/interior.dt1), while the `*_graphic.png` family is 800x800 SCENE pictures.
There is no drop-in asset in CASC to re-extract, so the entry's own "re-extract like v1578" cannot
be followed. **The fix is a FRAME, not an extraction** — one capture of any wildtemple interior,
taken while the console is recording, processed to the family's style.

That left a 30-second in-game action blocked behind a research project. This is the research
project, done, so the action is all that is left.

    python3 art/make_zone_graphic.py <frame.jpg> act5-hallsofanguish

WHAT IT DOES, and every number is measured off the four existing family members rather than chosen:

    size    800x800, centre-cropped to square first so nothing is squashed
    mean    41.8 / 46.4 / 40.2 / 40.0  -> the new file is gamma-matched into that band
    stdev   38.5 / 34.9 / 24.1 / 31.0  -> reported, and REFUSED below 15

⚠ IT REFUSES RATHER THAN GUESSING. A frame that is nearly flat (stdev < 15) is the failure v1610
recorded on the tz_* family — a blank grey tile passing a byte-size floor — so it is rejected here
instead of shipped. And it prints the two statistics WITHOUT claiming they mean the picture is
right: REG-113 exists precisely because this file's luminance (42.9) and variance (24.9) were both
healthy while the picture stayed wrong. **OPEN THE RESULT AND LOOK AT IT.** No threshold closes
this one. [[feedback-verify-not-proxy]]
"""
import os
import sys


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    src, stem = argv[1], argv[2].replace(".png", "")
    try:
        from PIL import Image, ImageStat
    except Exception as e:
        print("Pillow is needed: %s" % e)
        return 2
    if not os.path.isfile(src):
        print("no such frame: %s" % src)
        return 2

    here = os.path.dirname(os.path.abspath(__file__))
    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
    im = im.resize((800, 800), Image.LANCZOS)

    mean = sum(ImageStat.Stat(im).mean) / 3.0
    TARGET = 42.0                      # the family's own mean, 41.8/46.4/40.2/40.0
    if mean > 1:
        import math
        g = math.log(max(TARGET, 1) / 255.0) / math.log(max(mean, 1) / 255.0)
        g = max(0.25, min(4.0, g))
        lut = [min(255, int(round(255.0 * ((i / 255.0) ** g)))) for i in range(256)] * 3
        im = im.point(lut)

    st = ImageStat.Stat(im)
    mean2, sd = sum(st.mean) / 3.0, sum(st.stddev) / 3.0
    if sd < 15.0:
        print("REFUSED — stdev %.1f is below the family floor (15). A near-flat picture is the "
              "v1610 failure, not a dark scene. Capture a lit interior and try again." % sd)
        return 1

    # MATCH THE FAMILY'S FORMAT, not just its brightness. Measured: three of the four members are
    # mode "P" with 138-206 distinct colours and 104-122KB; a straight RGB save of a game frame
    # lands at ~750KB, seven times the family and seven times the page weight. 256-colour adaptive
    # quantisation is what they already are.
    out = os.path.join(here, stem + "_graphic.png")
    im.convert("P", palette=Image.ADAPTIVE, colors=256).save(out, "PNG", optimize=True)
    print("wrote %s" % out)
    print("  mean  %.1f   (family 40.0-46.4)" % mean2)
    print("  stdev %.1f   (family 24.1-38.5)" % sd)
    print("  size  %.0fKB (family 104-122KB)" % (os.path.getsize(out) / 1024.0))
    print("\n⚠ BOTH STATISTICS WERE ALREADY HEALTHY ON THE BROKEN FILE. Open it and look at it,")
    print("  and have a different model family describe it cold. That is what closes REG-113.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
