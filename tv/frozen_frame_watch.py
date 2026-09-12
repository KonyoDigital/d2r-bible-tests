#!/usr/bin/env python3
"""A FROZEN SCREEN IS A DEAD CONSOLE THAT ANSWERS 200 — detect it from the pixels, not the page.

⚠⚠ THIS IS TASK #34's THESIS, AND IT IS NOT HYPOTHETICAL. Measured on his machine 2026-09-10 from
Grok Bot's own captures: at 19:08 the TV DIABLO window was a DARK BLANK — titlebar and nothing
else — and at 16:16 a WHITE BLANK. At both moments every text-based check reported health:

    GET /            200 in 16ms - 1,744,954 bytes
    GET /api/status  200 in 68ms
    quiet hold - HEART census held - version pin held - did not kill

A page that answers 200 can paint nothing, so a detector that ASKS THE PAGE can never fire on a
dead compositor. This one asks the bytes.

★ THE DETECTOR WAS ALREADY IN THE DATA, FOR FREE. A live console never captures twice to the same
bytes — the clock alone changes. So two consecutive byte-identical frames of the SAME WINDOW is a
screen that stopped painting, and it costs a shasum.

⚠⚠ GROUP BY GEOMETRY OR THE ANSWER IS MEANINGLESS. His shelf holds 383 PNGs from many different
investigations — full-window captures AND derived crops (header, footer, rail, stage). Measured
2026-09-12: eight distinct pixel geometries, the two standing series being 2376x1456 (95 frames)
and 2940x1846 (83). A naive "hash the newest N files" compares a header crop against a footer crop,
never finds a match, and reports NOT FROZEN — a clean-looking verdict from a comparison that could
never have gone red. Frames are only comparable to frames of the same window.
[[zero-needs-a-denominator]] [[feedback-blind-fixture-green-gate]]

⚠ A REPEATED HASH IS THE FINDING, NOT THE VERDICT. Two of the three frozen classes on his shelf
were confirmed blank BY OPENING THE IMAGE; the third was never looked at and stays UNKNOWN. This
module says FROZEN — "these two frames are identical" — and never says "blank", which is a claim
about content that only an eye or an OCR can make.

⚠ ABSENCE IS UNKNOWN, NEVER CLEAN. On CI, and on any machine that is not his, the capture folder
does not exist. A detector that returns "healthy" when it has nothing to read is the exact defect
this repo keeps finding. No frames -> UNKNOWN, and the count that produced it is published.
[[unknown-stays-unknown]] [[silence-is-not-evidence]]
"""
import hashlib
import io
import os
import time

#: where Grok Bot writes its screencaptures of the REAL window. Env-overridable so a test can point
#: it at a fixture, and so this file carries no absolute path (the repo is PUBLIC).
SHELF_ENV = "TV_GB_SHELF"
SHELF_DEFAULT = "~/gb-shelf"

FROZEN = "FROZEN"        # the newest two frames of one window are byte-identical
MOVING = "MOVING"        # the newest two differ - the screen was painting
UNKNOWN = "UNKNOWN"      # fewer than two comparable frames; nobody can tell

#: a geometry needs at least this many frames to count as a standing series rather than a one-off
#: crop from some investigation. Below it the group is reported, but as UNKNOWN.
SERIES_MIN = 2

#: ⚠⚠ TWO FRAMES MUST BE THIS FAR APART BEFORE "IDENTICAL" MEANS ANYTHING, and this constant was
#: earned by my own detector reporting two false positives on its first real run, 2026-09-12:
#:     2940x1846  gap=0.0s  shelf-final-B-matched.png == shelf3-try2-B-...Z.png   -> a FILE COPY
#:     2160x1500  gap=0.1s  shelf-final-stage-B.png   == shelf-final-stage-A.png  -> 0.1s apart
#: A copied file is byte-identical to its source by definition, and two captures a tenth of a
#: second apart are identical on a perfectly healthy screen because nothing on it had time to
#: change. Both would have been reported as a dead compositor. The evidence for FROZEN is not
#: "identical" — it is "identical ACROSS A GAP IN WHICH A LIVE SCREEN WOULD HAVE CHANGED".
#: [[feedback-suspect-the-instrument]] [[sabotage-is-usually-the-wrong-one]]
MIN_GAP_S = 2.0

#: ⚠ A FRAME SMALLER THAN A WINDOW IS NOT A WINDOW. Third false-positive class on the first real
#: run, and the one a time gap cannot catch: `cursor-onair-ref.png` is byte-identical to
#: `cursor-onair.png` and was written 6,407s later, because it is a REFERENCE COPY of it. Two
#: 280x280 crops are not evidence about a compositor however far apart they were saved.
#: This is a constraint on the SUBJECT, not a threshold tuned until the answer looked clean: his
#: window is 2376x1456 captured (1188x728 logical), and nothing below this floor can be a whole
#: window. Excluded geometries are COUNTED AND NAMED in the report - never silently dropped, which
#: would make the denominator a lie. [[zero-needs-a-denominator]]
MIN_WINDOW_W, MIN_WINDOW_H = 640, 480


def shelf_dir():
    return os.path.expanduser(os.environ.get(SHELF_ENV) or SHELF_DEFAULT)


def png_geometry(path):
    """-> (width, height) from the IHDR chunk, or None if this is not a readable PNG.

    ⚠ PARSED FROM THE HEADER, not shelled out to `sips`. sips is macOS-only and this has to be
    able to run on CI, where returning None for every file would make every group empty and the
    whole report a confident UNKNOWN about nothing. [[test-venue]]
    """
    try:
        with io.open(path, "rb") as f:
            head = f.read(24)
    except (IOError, OSError):
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    w = int.from_bytes(head[16:20], "big")
    h = int.from_bytes(head[20:24], "big")
    return (w, h) if w and h else None


def _sha(path):
    try:
        h = hashlib.sha256()
        with io.open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError):
        return None


def frames(root=None):
    """-> [{path, mtime, geom}] every readable PNG under the shelf, newest first."""
    root = root or shelf_dir()
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.lower().endswith(".png"):
                continue
            p = os.path.join(dirpath, fn)
            g = png_geometry(p)
            if g is None:
                continue
            try:
                out.append({"path": p, "mtime": os.path.getmtime(p), "geom": g})
            except (IOError, OSError):
                continue
    out.sort(key=lambda r: -r["mtime"])
    return out


def report(root=None, now=None):
    """-> {state, why, series: [...], counts} — one verdict per window geometry, plus an overall.

    The overall is FROZEN if ANY standing series is frozen: a console can have several windows and
    only one of them dead, and an average would hide exactly the one that matters.
    """
    root = root or shelf_dir()
    now = time.time() if now is None else now
    fs = frames(root)
    groups = {}
    for r in fs:
        groups.setdefault(r["geom"], []).append(r)

    series = []
    crops = []
    for geom, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        rows.sort(key=lambda r: -r["mtime"])
        label = "%dx%d" % geom
        if geom[0] < MIN_WINDOW_W or geom[1] < MIN_WINDOW_H:
            crops.append({"geom": label, "frames": len(rows)})
            continue
        if len(rows) < SERIES_MIN:
            series.append({"geom": label, "frames": len(rows), "state": UNKNOWN,
                           "why": "only %d frame at this geometry - a single frame cannot be "
                                  "compared to anything" % len(rows)})
            continue
        # ⚠ NOT "the newest two" — the newest, and the most recent frame FAR ENOUGH BEFORE IT to
        # be independent evidence. Taking rows[1] blindly compares a file against its own copy.
        a = rows[0]
        b = None
        for cand in rows[1:]:
            if (a["mtime"] - cand["mtime"]) >= MIN_GAP_S:
                b = cand
                break
        if b is None:
            _near = round(abs(a["mtime"] - rows[1]["mtime"]), 1)
            series.append({"geom": label, "frames": len(rows), "state": UNKNOWN,
                           "ageS": round(now - a["mtime"], 1), "gapS": _near,
                           "newest": os.path.basename(a["path"]),
                           "previous": os.path.basename(rows[1]["path"]),
                           "why": "no frame of this window is %.0fs or more older than the newest "
                                  "(closest is %.1fs). Two captures that close are identical on a "
                                  "HEALTHY screen, and a copied file is identical by definition, "
                                  "so nothing can be concluded" % (MIN_GAP_S, _near)})
            continue
        sa, sb = _sha(a["path"]), _sha(b["path"])
        if sa is None or sb is None:
            series.append({"geom": label, "frames": len(rows), "state": UNKNOWN,
                           "why": "the newest two comparable frames could not be read"})
            continue
        same = (sa == sb)
        # ⚠ PUBLISH THE GAP BETWEEN THE TWO FRAMES. Grok Bot deliberately takes A/B pairs seconds
        # apart to test for progressive paint, so "byte-identical" over 5s and over 3 hours are
        # both real findings and NOT the same strength of one. A verdict that hides which it is
        # cannot be argued with. [[zero-needs-a-denominator]]
        gap = round(abs(a["mtime"] - b["mtime"]), 1)
        series.append({
            "geom": label, "frames": len(rows),
            "state": FROZEN if same else MOVING,
            "ageS": round(now - a["mtime"], 1),
            "gapS": gap,
            "sha": sa[:12],
            "newest": os.path.basename(a["path"]),
            "previous": os.path.basename(b["path"]),
            "why": (("the newest two captures of this window are BYTE-IDENTICAL (%s). A live "
                     "console never captures twice to the same bytes - the clock alone changes - "
                     "so this screen stopped painting across the %.0fs between them. ⚠ That it "
                     "is FROZEN is measured; that it is BLANK is not, and needs an eye on the "
                     "frame." % (sa[:12], gap)) if same
                    else "the newest two captures differ, so the screen was painting"),
        })

    standing = [s for s in series if s["state"] in (FROZEN, MOVING)]
    counts = {"pngs": len(fs), "geometries": len(groups),
              "standing": len(standing),
              "frozen": len([s for s in standing if s["state"] == FROZEN]),
              # said out loud: how much of the folder this verdict is NOT about
              "cropGeometries": len(crops),
              "cropFrames": sum(c["frames"] for c in crops)}

    if not os.path.isdir(root):
        state, why = UNKNOWN, ("the capture folder does not exist here, so nothing about his "
                               "screen is known from this machine. That is not a clean bill.")
    elif not standing:
        state, why = UNKNOWN, ("read %d PNG(s) across %d geometry(ies) and NONE had two frames of "
                               "the same window to compare. Nothing was measured."
                               % (len(fs), len(groups)))
    elif counts["frozen"]:
        state = FROZEN
        why = ("%d of %d comparable window series stopped painting (%d PNG(s) read)"
               % (counts["frozen"], len(standing), len(fs)))
    else:
        state = MOVING
        why = ("%d window series compared, all painting (%d PNG(s) read)"
               % (len(standing), len(fs)))
    if crops:
        why += (" — %d frame(s) across %d sub-window geometry(ies) were excluded as crops, not "
                "windows" % (counts["cropFrames"], counts["cropGeometries"]))
    return {"state": state, "why": why, "series": series, "crops": crops,
            "counts": counts, "root": root}


if __name__ == "__main__":
    # ⚠ HIS CONSOLE IS cp1255 AND CANNOT ENCODE THE ARROWS AND STARS THIS FILE PRINTS. Without
    # this, a CORRECT tree reports FAILURE because the process dies inside its own print — the
    # dangerous direction, because it teaches people to ignore the tool. [[REG-044/054/077]]
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import json
    import sys
    r = report(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({k: v for k, v in r.items() if k not in ("series", "crops")}, indent=2))
    for s in r["series"][:8]:
        print("  %-12s %4s frames  %-8s gap=%-8s %s" % (s["geom"], s["frames"], s["state"],
                                                          s.get("gapS"), s["why"][:80]))
        if s["state"] == FROZEN:
            print("       %s  ==  %s" % (s["newest"], s["previous"]))
