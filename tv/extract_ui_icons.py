#!/usr/bin/env python3
"""v1614 — pull the console's tab + MINI icons straight out of the local D2R install.

Konyo: "under mini on air... the logo images should be ART0R also for the tabs themselves not
these emojis.. needs to be HD art0r extracted from the local 28giga game we did this for other
things just needs to be replicated also here".

He is right that it was inconsistent: the board has been rendering true CASC sprites since v384,
while the console it sits inside was still labelling itself with 🏦🪨💎🧪🏆🧩 — system emoji, which
render as a different glyph on every machine he owns and belong to no game at all.

This script is the repeatable version of that extraction. The last one lived entirely in /tmp and
was gone by the next session, so "replicate it" meant rebuilding the toolchain from a memory note
before a single icon could be pulled. Provenance now lives in ICONS below: every icon states the
CASC path it came from, so any of them can be re-pulled or replaced without re-deriving anything.

    python3 tv/extract_ui_icons.py           # writes art/ui_*.png
    python3 tv/extract_ui_icons.py --check   # verify what is on disk, extract nothing

Needs the CascLib toolchain — see the header of _need_toolchain() for the three commands. Without
it the script exits 77 (SKIP), because a machine with no D2R install is not a failing machine; the
committed PNGs are the artifact, and this is how they were made.

THE .sprite FORMAT (corrected here, v1614): SpA1 is a FRAME ATLAS, not one image.
    0x04 u16 version (0x1f)      0x06 u16 frame width      0x08 u32 total width
    0x0C u32 height              0x14 u32 frame count      0x20 u32 payload bytes
    pixels @0x28, raw RGBA8888, `frames` cells laid out left-to-right.
Every item sprite is single-frame, so a reader that ignored the frame count worked perfectly for
611 item icons and then produced garbage on the first UI sprite it met — `total width` there is
frameW*frames, so the naive read walked off the end of the buffer. UI icons are ANIMATED (the
terror-zone glyph has 3 frames, a quest medallion 27), which is why this takes the most opaque
frame: several animate from fully transparent, so frame 0 can be a blank image.
"""
import io
import os
import struct
import subprocess
import sys

# This tool PRINTS non-ASCII (the icon table, the em dashes in every reason). On a non-UTF-8
# console that crashes while reporting, so a clean tree exits non-zero — REG-044/054/077/078.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "art")
SKIP = 77

D2R = os.environ.get("D2R_INSTALL") or os.path.join(
    os.path.expanduser("~"), "CXPBottles", "Battle.net Desktop App", "drive_c",
    "Program Files (x86)", "Diablo II Resurrected")
EXTRACT = os.environ.get("CASC_EXTRACT", "/tmp/casc_extract")
FRAMEWORK = os.environ.get("CASC_FRAMEWORK", "/tmp/CascLib/build")

# role -> (CASC path, what it is in the game, why it fits the role)
#
# The six header tabs all take QUEST MEDALLIONS, which is a deliberate family: they share one
# frame, one palette and one silhouette weight, so the tab strip reads as a set instead of six
# unrelated pictures. Four of the six are literal name matches to the tab they label.
#
# The six MINI focuses take ITEM sprites instead, because MINI's focuses ARE item categories —
# what he is pointing the camera at. An item icon says "runes" more directly than any medallion.
ICONS = {
    # ── header tabs ─────────────────────────────────────────────────────────────────────────
    "tab_session": (r"data\hd\global\ui\questicons\a3q4.sprite",
                    "Lam Esen's Tome", "a session log is a journal — the game's own book icon"),
    "tab_forge": (r"data\hd\global\ui\questicons\a4q2.sprite",
                  "Hell's Forge", "the Forge tab, labelled with the game's Forge quest"),
    "tab_funi": (r"data\hd\global\ui\questicons\a2q6.sprite",
                 "The Seven Tombs", "gold frame around a treasure gem — the uniques chronicle"),
    "tab_fsets": (r"data\hd\global\ui\questicons\a3q1.sprite",
                  "The Golden Bird", "GREEN gems — green is the set-item colour in D2"),
    "tab_tools": (r"data\hd\global\ui\questicons\a1q3.sprite",
                  "Tools of the Trade", "the smith's-tools quest, for the Tools tab"),
    "tab_tvd": (r"data\hd\global\ui\questicons\a4q3.sprite",
                "Terror's End", "Diablo's own face, for TV DIABLO"),
    # ── MINI focuses ────────────────────────────────────────────────────────────────────────
    "foc_stash": (r"data\hd\global\ui\items\misc\quest\horadric_cube.sprite",
                  "Horadric Cube", "the box loot goes in"),
    # ── panel headers ───────────────────────────────────────────────────────────────────────
    "tz": (r"data\hd\global\ui\panel\waypoints\terror_zone_icon.sprite",
           "terror zone icon", "the game's OWN terror-zone glyph, for the TZ panel"),
    "chronicle": (r"data\hd\global\ui\items\misc\book\identify_book.sprite",
                  "Tome of Identify", "the book you read your own history out of — CHRONICLE SWEEP"),
}

# Roles served by art that already exists, so nothing is pulled twice.
#
# The two CHRONICLE focuses deliberately reuse their own tab medallion. Three real set items were
# tried first (Griswold's Edge, Natalya's Mark, Taebaek's Glory) and all three failed the only test
# that matters here: at 18px a sword is a diagonal line and a dark grey shield is a smudge. The
# medallions survive the size because they were drawn as icons — and reusing the tab's own picture
# says "this focus IS that chronicle" better than a second, unrelated image would.
REUSED = {
    "foc_runes": "hd_ber_rune.png",
    "foc_gems": "hd_perfect_ruby.png",
    "foc_materials": "hd_burning_essence_of_terror.png",
    "foc_uniques": "ui_tab_funi.png",
    "foc_sets": "ui_tab_fsets.png",
}

OUT_PX = 96   # tabs render ~18px, MINI ~20px; 96 covers 3x retina with room to spare


def read_sprite(raw, label):
    if raw[:4] != b"SpA1":
        raise ValueError("%s is not an SpA1 sprite" % label)
    frame_w = struct.unpack("<H", raw[6:8])[0]
    total_w = struct.unpack("<I", raw[8:12])[0]
    height = struct.unpack("<I", raw[12:16])[0]
    frames = struct.unpack("<I", raw[20:24])[0] or 1
    need = total_w * height * 4
    if len(raw) < 40 + need:
        raise ValueError("%s: header claims %d px bytes, file has %d" % (label, need, len(raw) - 40))
    # THE ATLAS STRIDE IS NOT THE HEADER'S FRAME WIDTH. u16@6 is the frame's CONTENT width; the
    # cells can carry padding, and the quest medallions do: 27 frames across a 4671px atlas is a
    # stride of 173 against a stated width of 171. Slicing at 171 would shear every frame by two
    # pixels more than the last, so the final medallion arrives visibly cut. Derive the stride from
    # the atlas instead and let the alpha bbox crop trim whatever padding was there.
    if total_w % frames:
        raise ValueError("%s: %dpx atlas does not divide into %d frames" % (label, total_w, frames))
    stride = total_w // frames
    if stride < frame_w:
        raise ValueError("%s: stride %d narrower than the stated frame width %d"
                         % (label, stride, frame_w))
    from PIL import Image
    atlas = Image.frombytes("RGBA", (total_w, height), raw[40:40 + need])
    return [atlas.crop((i * stride, 0, i * stride + frame_w, height)) for i in range(frames)]


def best_frame(raw, label):
    """The most opaque frame. Several UI icons animate up from fully transparent, so frame 0 can
    be blank — taking it would write an empty PNG that looks exactly like a missing icon."""
    frames = read_sprite(raw, label)
    return max(frames, key=lambda im: sum(im.split()[3].getdata()))


def _need_toolchain():
    """    git clone --depth 1 https://github.com/ladislav-zezula/CascLib.git /tmp/CascLib
    cd /tmp/CascLib && mkdir -p build && cd build && \\
      cmake -DCMAKE_BUILD_TYPE=Release -DCASC_BUILD_SHARED_LIB=ON \\
            -DCMAKE_POLICY_VERSION_MINIMUM=3.5 .. && make -j4
    g++ -O2 -std=c++17 -I/tmp/CascLib/src -x c++ tv/casc_extract.c \\
        -F/tmp/CascLib/build -framework casc -o /tmp/casc_extract"""
    missing = []
    if not os.path.exists(EXTRACT):
        missing.append("the extractor (%s)" % EXTRACT)
    if not os.path.isdir(D2R):
        missing.append("the D2R install (%s)" % D2R)
    return missing


def pull(casc_path, label):
    env = dict(os.environ, DYLD_FRAMEWORK_PATH=FRAMEWORK)
    tmp = os.path.join("/tmp", "_uiicon.sprite")
    r = subprocess.run([EXTRACT, D2R, "data:" + casc_path, tmp],
                       env=env, capture_output=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        raise RuntimeError("%s: extract failed — %s" % (label, r.stderr.decode()[:120]))
    with open(tmp, "rb") as fh:
        raw = fh.read()
    os.unlink(tmp)
    return raw


def main():
    check = "--check" in sys.argv
    names = sorted(ICONS) + sorted(REUSED)

    if check:
        bad = []
        for role in sorted(ICONS):
            p = os.path.join(ART, "ui_%s.png" % role)
            if not os.path.exists(p) or os.path.getsize(p) < 200:
                bad.append("ui_%s.png" % role)
        for role, fn in sorted(REUSED.items()):
            if not os.path.exists(os.path.join(ART, fn)):
                bad.append("%s (reused by %s)" % (fn, role))
        if bad:
            print("MISSING: " + ", ".join(bad))
            return 1
        print("OK — all %d console icons present in art/" % len(names))
        return 0

    missing = _need_toolchain()
    if missing:
        print("SKIP — no extraction possible here: %s" % "; ".join(missing))
        print(_need_toolchain.__doc__)
        return SKIP

    from PIL import Image
    for role in sorted(ICONS):
        casc, what, why = ICONS[role]
        raw = pull(casc, role)
        im = best_frame(raw, role)
        bb = im.getbbox()
        if not bb:
            raise RuntimeError("%s decoded to a fully transparent image" % role)
        im = im.crop(bb)
        im.thumbnail((OUT_PX, OUT_PX), Image.LANCZOS)
        out = os.path.join(ART, "ui_%s.png" % role)
        im.save(out, optimize=True)
        print("%-14s %-22s %sx%s  <- %s" % (role, what, im.width, im.height, casc))
    print("\n%d icons written to art/ui_*.png; %d reused from the v384 item pull"
          % (len(ICONS), len(REUSED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
