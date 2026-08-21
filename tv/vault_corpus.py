#!/usr/bin/env python3
"""What ownership footage does he ACTUALLY have? — the first artifact of the Vault Manager project.

    python3 tv/vault_corpus.py            # index the reels the sweeps walk
    python3 tv/vault_corpus.py --loose    # index the loose frames in frames/hist too

WHY THIS EXISTS, AND WHY IT IS FIRST. His brief asks the readers to log his inventory, his equipment
and his stash, verify across 3+ sessions that nothing moved, and render it back 1:1. None of that is
buildable until one question is answered with a number: HOW MANY FRAMES OF EACH SURFACE DOES HE
HAVE, AND WHICH TAB IS EACH ONE ON. Every previous attempt at this lane was argued rather than
measured, and REG-185 ("0 of 17 reels declare an ownership surface") was read for months as "there
is no stash footage" when it only ever said "no reel DECLARED one".

MEASURED THE FIRST TIME THIS RAN, 2026-08-21:

    frames/hist ROOT (loose)      883 frames   —  12 stash+inventory,  8 with a readable tab
    the 27 REELS the sweeps walk 1970 frames   — 112 stash+inventory, 151 with a readable tab

    ...and the two sets share ZERO filenames. They are separate archives, and every stash measurement
    before this file — the 68-frame corpus, the gem calibration, stash_grid_truth.json — was taken on
    the LOOSE half, which no sweep has ever walked.

TWO SIGNALS, BOTH STRUCTURAL, NEITHER A MODEL CALL:
  · the INVENTORY title — gold text on stone in a fixed band, scored as a FRACTION so a fire-lit
    screen (0.2355) and a menu (0.0071) fall outside the tight window the real title occupies.
    ⚠ Gold alone is not enough and the window is the whole trick: the lobby, the in-game menu and
    the Chronicle panel all print gold titles, and all six candidates I opened in the 0.002-0.01
    band were one of those three. Only the tight cluster is the panel.
  · the ACTIVE-TAB GEM (v1912) — which stash tab is selected, 12/12 on the labelled corpus.

It reads nothing but pixels, spends no vision, and writes one index file.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

# The INVENTORY title band, measured off his own "both panels open" frame (6_1784984233446).
TITLE_BAND = (0.56, 0.125, 0.80, 0.165)
# The tight window the real title occupies. Below it: no panel. Above it: another gold thing.
TITLE_MIN, TITLE_MAX = 0.0006, 0.0012
OUT = os.path.join(HERE, "vault_corpus_index.json")


def title_score(path):
    """Fraction of the title band that is D2R's gold-on-stone lettering. None if unreadable."""
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
    except Exception:
        return None
    w, h = im.size
    if w < 200 or h < 200:
        return None
    c = im.crop((int(w * TITLE_BAND[0]), int(h * TITLE_BAND[1]),
                 int(w * TITLE_BAND[2]), int(h * TITLE_BAND[3])))
    px = c.load()
    W, H = c.size
    n = 0
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if r > 150 and g > 110 and b < 110 and (r - b) > 60 and (r - g) < 90:
                n += 1
    return n / float(W * H or 1)


def scan(paths):
    """-> rows of {frame, reel, title, panel, tab}. Pure; no writes, no model calls."""
    import stash_eye as se
    rows = []
    for reel, p in paths:
        s = title_score(p)
        if s is None:
            continue
        tab, _d = se.tab_from_gem(p)
        panel = bool(TITLE_MIN < s < TITLE_MAX)
        if panel or tab:
            rows.append({"reel": reel, "frame": os.path.basename(p),
                         "title": round(s, 4), "panel": panel, "tab": tab or None})
    return rows


def _paths(hist, loose=False):
    import glob
    out = []
    for d in sorted(glob.glob(os.path.join(hist, "reel_*"))):
        for p in sorted(glob.glob(os.path.join(d, "*.jpg"))):
            out.append((os.path.basename(d), p))
    if loose:
        for p in sorted(glob.glob(os.path.join(hist, "*.jpg"))):
            out.append(("(loose)", p))
    return out


def main(argv=None):
    import collections
    import time
    argv = list(argv if argv is not None else sys.argv[1:])
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    paths = _paths(hist, loose=("--loose" in argv))
    if not paths:
        print("⚠ no frames under %s — nothing to index, which is not the same as nothing to find"
              % hist)
        return 2
    print("scanning %d frame(s) under %s …" % (len(paths), hist))
    t0 = time.time()
    rows = scan(paths)
    by_reel = collections.Counter(r["reel"] for r in rows if r["tab"])
    tabs = collections.Counter(r["tab"] for r in rows if r["tab"])
    panels = sum(1 for r in rows if r["panel"])
    print("\n%d frame(s) carry ownership evidence, in %.0fs" % (len(rows), time.time() - t0))
    print("  stash+inventory template (both panels open): %d" % panels)
    print("  a READABLE stash tab (the active-tab gem):   %d" % sum(tabs.values()))
    print("\n  by tab:  %s" % (dict(tabs) or "none"))
    print("  ⚠ a tab with no frames cannot be verified, simulated or debugged — say so rather than "
          "letting its absence read as 'nothing there'.")
    print("\n  by reel (tab-readable frames):")
    for reel, n in by_reel.most_common(12):
        print("     %-34s %d" % (reel, n))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"hist": hist, "scanned": len(paths), "rows": rows,
                   "totals": {"withEvidence": len(rows), "panels": panels,
                              "tabReadable": sum(tabs.values()), "byTab": dict(tabs)}},
                  fh, indent=1)
    print("\nwrote %s" % os.path.relpath(OUT, os.path.dirname(HERE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
