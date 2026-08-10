# chronicle_template.py — v1690, THE MEASURED CHRONICLE TEMPLATE.
#
# Konyo: "every picture and screenshot taken within the chronicle feed... it needs to understand
# when the chronicle page gets opened and the template of the chronicle page is open... like a MINI
# version where we already have that has set parameters for this." This module IS that mini version
# for the Chronicle panel — a locked geometric template plus a detector that reads it, the way
# stash_eye's _TALLY_CROPS is the locked template for the stash grid.
#
# THIS IS THE TEMPLATE AND ITS PROOF ONLY (v1690). The three consumers — chronicle_retro.py (retro
# sweep), control_app.py (live closer), tv_diablo.py (live vision routing) — are DELIBERATELY NOT
# WIRED HERE. That is v1691, once this geometry has shipped and been read by a human. Nothing in
# this file imports or is imported by those three; grep for "chronicle_template" in them and expect
# zero hits until then.
#
# ── WHY A PIXEL PATH, NOT AN OCR-LINES PATH (round-1 correction #1) ──────────────────────────────
# Round 1 of this ship built `detect_from_ocr_lines`-shaped detection and was discarded: on real
# Chronicle frames with a found-item tooltip open (the exact footage motivating this ship), full-
# frame/worker OCR returns the TOOLTIP's text — "Required Strength", "Defense:", leet item affix
# lines — not "CHRONICLE" or "Unique"/"Sets". Even on a CLEAN panel, full-frame OCR barely surfaces
# the chrome at all; stash_eye's own tab-chrome path only gets readable text via a deliberate crop +
# 3x upscale, and even that stays fuzzy ("VNIQVE") rather than a clean token match. An OCR-line API
# would therefore return `tooltip`/unknown on precisely the case that matters most. `detect()` below
# reads PIXELS from the frame (same class of move as `control_app.py`'s closer, which already holds
# `fp` and calls `stash_eye.analyze_frame` for the identical reason — "full-frame OCR is dark").
# `detect_from_ocr_lines()` exists too, but only as a WEAK SECONDARY that can corroborate a pixel
# verdict in `why` — it must never be the production classify source and never overrides pixels.
#
# ── WHY THESE BANDS AND NOT STASH_EYE'S (round-1 correction #2) ──────────────────────────────────
# The Chronicle is a CENTERED MODAL, not stash_eye's LEFT-ANCHORED panel: title "CHRONICLE" · three
# tabs Unique | Sets | Runewords · a secondary Normal/Exceptional/Elite strip · a search box · a LEFT
# CATEGORY RAIL · a progress bar + "View Rewards" button · then the list. stash_eye's crops and its
# `x * cal_aspect/aspect` aspect law are written for a panel anchored at the left edge and cannot be
# copied onto a centered one without measuring first — which is how round 1 shipped invented
# fractions. Every band below was MEASURED by opening real frames from
# tv/frames/hist/reel_s_1786385768689_67392/ (native 2940x1912, the same calibration film stash_eye
# locked on) at timestamps 782444 / 790530 / 797582 / 807514 / 814507 / 822654 / 826754 / 852357 (the
# nearest real frame to each requested ts — the reel has no frame at the exact ms) and reading them
# with vision, then confirmed against real pixel data (see MEASURED_ON below) — never derived by
# copying stash_eye's left-anchor math. Off-calibration aspects use `_scale_band_for_aspect`, a
# DIFFERENT and CENTER-PRESERVING derivation (documented at its definition) that is explicitly
# labelled derived-not-measured wherever it is used, exactly as stash_eye labels its own untested
# 16:9 branch — a band this module has not measured must say so, not borrow another module's label.
#
# ── WHY GEOMETRY IS GRADED SEPARATELY FROM VISION LABELS (round-1 correction #3) ──────────────────
# The 8 vision labels available for this reel are sparse and one of the eight is a conf-0.60 read
# whose `names` are literally `['Amulet'] * 7` — not clean ground truth. `test_chronicle_template.py`
# grades pixel geometry (measured, deterministic, reproducible from the source JPEGs) and the vision
# labels SEPARATELY and never averages them — grading a pixel template against sparse/low-confidence
# vision labels alone is how round 1 believed itself correct while its own detector flagged 30 of 31
# non-Chronicle controls AS Chronicle.
#
# ── PURE LAW (asserted structurally by test_chronicle_template.py, the way chronicle_retro's
#    write-free law is asserted) ── this module opens frame files to READ pixels. It performs NO
#    writes, NO deletes/renames, NO network calls, and NO model calls of any kind. It cannot tick,
#    untick, or otherwise touch d2r_foundLog/d2r_setPieces or any ledger — it only ever returns a
#    dict describing what a frame's pixels look like.
#
# ── THE RUNEWORDS DEAD END (documented, not silently folded) ──────────────────────────────────────
# The Chronicle panel has THREE tabs, but the board/intake kind vocabulary only recognises
# "chronicle-uniques" and "chronicle-sets" — there is no "chronicle-runewords" ledger kind anywhere
# in this project today. `detect()` still identifies tab="runewords" honestly when the pixels say so;
# `ledger_kind_for_tab("runewords")` returns None on purpose, and callers MUST treat that None as "no
# ledger path exists yet", never as "fold it into unique or sets". Wiring a runewords ledger is out
# of scope for this file.

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

FracBox = Tuple[float, float, float, float]

# ── CALIBRATION FILM — same film stash_eye locked _TALLY_CROPS on ─────────────────────────────────
_CAL_FILM = (2940, 1912)
_CAL_ASPECT = _CAL_FILM[0] / float(_CAL_FILM[1])
_CAL_LO, _CAL_HI = 1.45, 1.62  # Konyo's Mac range; stash_eye uses the same window

# ── MEASURED ON (evidence trail — the exact frames read with vision to lock the bands below) ──────
MEASURED_ON = {
    "reel": "reel_s_1786385768689_67392",
    "frames": [
        "f_1786385782444.jpg",  # nearest to requested ts 782689 — Unique tab, mid-scroll (Amulet rows)
        "f_1786385790530.jpg",  # nearest to requested ts 790213 — Unique tab, clean, names+dates visible
        "f_1786385797582.jpg",  # nearest to requested ts 797924 — Unique tab, mid-scroll
        "f_1786385807514.jpg",  # nearest to requested ts 807604 — Unique tab, mid-scroll (Battle* rows)
        "f_1786385814507.jpg",  # nearest to requested ts 814341
        "f_1786385822654.jpg",  # nearest to requested ts 822222
        "f_1786385826754.jpg",  # nearest to requested ts 826830 — TOOLTIP OVER PANEL (Cerebus' Bite)
        "f_1786385852357.jpg",  # nearest to requested ts 852302
    ],
    "negative_control": "f_1786385773403.jpg",  # earliest frame in the same reel: pure gameplay, no panel
}

# ── LOCKED GEOMETRY — fractions of full-frame (W, H) on the calibration film ───────────────────────
# All y-bands are MEASURED directly (visual inspection of the frames above, at native 2940x1912).
# x-bands for the width-scaling helper are measured the same way. Nothing here was copied from
# stash_eye's _TALLY_CROPS.

# Whole modal: outer stone-frame border, anchored to the CENTER of the viewport (not the left edge).
MODAL_BAND: FracBox = (0.215, 0.060, 0.785, 0.941)

# "CHRONICLE" gold title, centered top of the modal.
TITLE_BAND: FracBox = (0.30, 0.062, 0.70, 0.115)

# Red X close button, top-right corner of the modal frame.
CLOSE_X_BAND: FracBox = (0.770, 0.065, 0.800, 0.090)

# The full tab-strip row: three tabs + the search box, all on one row directly under the title.
TAB_STRIP_BAND: FracBox = (0.375, 0.135, 0.765, 0.173)
TAB_BANDS: Dict[str, FracBox] = {
    "unique": (0.378, 0.137, 0.462, 0.171),
    "sets": (0.462, 0.137, 0.542, 0.171),
    "runewords": (0.542, 0.137, 0.623, 0.171),
}
SEARCH_BAND: FracBox = (0.623, 0.137, 0.765, 0.171)

# Secondary strip: Normal / Exceptional / Elite checkboxes + the "All" category dropdown, right below
# the tab row.
SECONDARY_STRIP_BAND: FracBox = (0.239, 0.190, 0.762, 0.215)

# Left category rail: Armor / Weapons / Accessories tree, the % progress bar, and "View Rewards".
LEFT_RAIL_BAND: FracBox = (0.239, 0.230, 0.383, 0.780)

# The scrolling list of items — this is what a v1691 reader would page through.
LIST_BAND: FracBox = (0.400, 0.222, 0.762, 0.941)

# Vertical fraction of frame height per list row, measured from consecutive row centers in the clean
# frame (f_1786385790530.jpg): displayed-pixel row centers ~290,388,485,582,680,777,874 (2000px-wide
# render) give a pitch of ~97.3px there -> 97.3/1301 of frame height.
ROW_PITCH_FRAC = 0.0746

# Tabs with no ledger path in the board/intake kind vocabulary today. See "THE RUNEWORDS DEAD END"
# above. Kept as a set (not a single constant) so a future ledger kind removes itself from here in
# one edit instead of a scattered `!= "runewords"` check.
NO_LEDGER_TABS = frozenset({"runewords"})

_LEDGER_KIND_BY_TAB = {
    "unique": "chronicle-uniques",
    "sets": "chronicle-sets",
    # "runewords" intentionally absent — see NO_LEDGER_TABS.
}


def ledger_kind_for_tab(tab: Optional[str]) -> Optional[str]:
    """The board/intake ledger kind for a detected tab, or None when there isn't one yet.

    None is not a bug to route around — for "runewords" it means the ledger genuinely does not
    exist; for anything else it means the tab itself was not established (occluded/ambiguous).
    """
    if not tab:
        return None
    return _LEDGER_KIND_BY_TAB.get(tab)


# ── AAPECT SCALING — CENTER-PRESERVING, DIFFERENT FROM STASH_EYE'S LEFT-ANCHOR LAW ─────────────────
def _scale_band_for_aspect(frac: FracBox, aspect: float) -> Tuple[FracBox, str]:
    """Scale a width band to an off-calibration aspect, preserving the panel's CENTER.

    stash_eye's law (`x * cal_aspect/aspect`) is correct for a panel anchored at x=0 — the left
    edge stays put and only the right edge moves. The Chronicle modal is anchored at its CENTER, so
    the same formula would silently drag the whole panel sideways. This scales the half-width around
    the band's own midpoint instead. It is exactly as DERIVED-NOT-MEASURED as stash_eye's own 16:9
    branch — no off-Mac Chronicle frame has confirmed it — and every caller of this function must
    say so downstream, the way stash_eye's `_LAST_CROP["branch"]` does.
    """
    x0, y0, x1, y1 = frac
    if not aspect or aspect <= 0:
        return frac, "no-aspect"
    if _CAL_LO <= aspect <= _CAL_HI:
        return frac, "measured-mac"
    k = _CAL_ASPECT / float(aspect)
    cx = (x0 + x1) / 2.0
    half = (x1 - x0) / 2.0 * k
    return (max(0.0, cx - half), y0, min(1.0, cx + half), y1), "derived-not-measured"


# ── PIXEL SIGNAL THRESHOLDS — calibrated against MEASURED_ON's frames, not statistically fit ───────
# close-X red button: measured 0.0682 on both a clean Chronicle frame and a tooltip-occluded one
# (the close button sits outside where a tooltip draws); measured 0.0000 on the gameplay negative
# control. 0.03 keeps a wide margin under the real reading while staying far above the negative.
_CLOSE_X_RED_THRESH = 0.03
# search box brightness: measured 0.0233 clean, 0.0048 under a tooltip that partially covers the
# search box, 0.0000 with no panel open at all. Used as the OCCLUSION GATE for tab resolution: below
# this, the tab-strip border scan is not trusted (see `detect()`).
_SEARCH_BRIGHT_THRESH = 0.012
_SEARCH_BRIGHT_WEAK = 0.003
# list interior mid-gray stone: measured 0.69/0.48/0.71 across three real Chronicle reads vs 0.41 on
# the gameplay negative control.
_LIST_MIDGRAY_THRESH = 0.45
# selected-tab gold/tan border: measured 0.0022 on the Unique tab's own box outline (two independent
# clean frames agreed exactly), 0.0000 on Sets/Runewords in the same frames.
_TAB_BORDER_THRESH = 0.001


def _open_rgb(path: str):
    from PIL import Image  # type: ignore

    return Image.open(path).convert("RGB")


def _crop_frac(im, frac: FracBox):
    w, h = im.size
    x0, y0, x1, y1 = frac
    box = (
        max(0, int(w * x0)),
        max(0, int(h * y0)),
        min(w, max(1, int(w * x1))),
        min(h, max(1, int(h * y1))),
    )
    if box[2] <= box[0] or box[3] <= box[1]:
        return None
    return im.crop(box)


def _sample(crop, stride: int = 2):
    """Yield (r,g,b) at a stride — sampling, not scanning every pixel, keeps this cheap and pure."""
    w, h = crop.size
    px = crop.load()
    for x in range(0, w, stride):
        for y in range(0, h, stride):
            yield px[x, y]


def _red_fraction(crop) -> float:
    n = tot = 0
    for r, g, b in _sample(crop):
        tot += 1
        if r > 130 and (r - g) > 50 and (r - b) > 50:
            n += 1
    return n / tot if tot else 0.0


def _bright_fraction(crop, thresh: float = 150.0) -> float:
    n = tot = 0
    for r, g, b in _sample(crop):
        tot += 1
        if (0.299 * r + 0.587 * g + 0.114 * b) > thresh:
            n += 1
    return n / tot if tot else 0.0


def _midgray_fraction(crop) -> float:
    n = tot = 0
    for r, g, b in _sample(crop):
        tot += 1
        l = 0.299 * r + 0.587 * g + 0.114 * b
        if 35 <= l <= 110 and abs(r - g) < 18 and abs(g - b) < 18:
            n += 1
    return n / tot if tot else 0.0


def _gold_border_fraction(crop) -> float:
    n = tot = 0
    for r, g, b in _sample(crop, stride=3):
        tot += 1
        if 100 <= r <= 210 and 80 <= g <= 180 and 50 <= b <= 150 and (r - b) >= 15 and r >= g - 5:
            n += 1
    return n / tot if tot else 0.0


def geometry_signals(frame_path: str) -> Optional[Dict[str, Any]]:
    """The raw MEASURED pixel signals for a frame — no thresholds, no verdict.

    Exists so tests (and any future caller) can grade geometry on its own terms, separate from the
    sparse/low-confidence vision labels (round-1 correction #3). Returns None if the frame cannot be
    opened at all — never a zeroed-out dict pretending to be a real reading.
    """
    if not frame_path or not os.path.isfile(frame_path):
        return None
    try:
        im = _open_rgb(frame_path)
    except Exception:
        return None
    w, h = im.size
    aspect = (w / float(h)) if h else 0.0
    close_x = _crop_frac(im, CLOSE_X_BAND)
    search = _crop_frac(im, SEARCH_BAND)
    listband = _crop_frac(im, LIST_BAND)
    if close_x is None or search is None or listband is None:
        return None
    tab_scores = {}
    for tab, box in TAB_BANDS.items():
        c = _crop_frac(im, box)
        tab_scores[tab] = _gold_border_fraction(c) if c is not None else 0.0
    return {
        "size": (w, h),
        "aspect": round(aspect, 4),
        "close_x_red": round(_red_fraction(close_x), 4),
        "search_bright": round(_bright_fraction(search), 4),
        "list_midgray": round(_midgray_fraction(listband), 4),
        "tab_border": {k: round(v, 4) for k, v in tab_scores.items()},
    }


def detect(frame_path: str) -> Dict[str, Any]:
    """detect(frame) -> {is_chronicle, tab, confidence, why}

    PURE: reads pixels from frame_path, nothing else. No writes, no network, no model call.
    tab is one of "unique" | "sets" | "runewords" | None — None whenever the tab strip cannot be
    read with confidence (occluded by a tooltip, ambiguous, or the panel isn't Chronicle at all).
    A Sets page misread as Uniques writes a wrong count into his grail truth, so this REFUSES
    (tab=None) rather than guessing whenever the signal is not clean.
    """
    sig = geometry_signals(frame_path)
    if sig is None:
        return {"is_chronicle": False, "tab": None, "confidence": 0.0,
                "why": "frame unreadable or missing"}

    branch = "measured-mac" if _CAL_LO <= sig["aspect"] <= _CAL_HI else "derived-not-measured"

    score = 0.0
    reasons = []
    if sig["close_x_red"] >= _CLOSE_X_RED_THRESH:
        score += 0.55
        reasons.append("close-X red button present (%.3f)" % sig["close_x_red"])
    if sig["list_midgray"] >= _LIST_MIDGRAY_THRESH:
        score += 0.25
        reasons.append("list interior stone-gray present (%.3f)" % sig["list_midgray"])
    occluded = sig["search_bright"] < _SEARCH_BRIGHT_THRESH
    if not occluded:
        score += 0.20
        reasons.append("search box clear (%.3f)" % sig["search_bright"])
    elif sig["search_bright"] >= _SEARCH_BRIGHT_WEAK:
        score += 0.08
        reasons.append("search box partially occluded (%.3f)" % sig["search_bright"])
    else:
        reasons.append("search box fully occluded (%.3f)" % sig["search_bright"])

    is_chronicle = sig["close_x_red"] >= _CLOSE_X_RED_THRESH and score >= 0.55
    if branch == "derived-not-measured":
        score = min(score, 0.6)
        reasons.append("aspect %.3f outside the measured 1.45-1.62 window: bands derived, not "
                        "measured — treat this reading as UNCONFIRMED" % sig["aspect"])

    tab = None
    if is_chronicle:
        if occluded:
            reasons.append("tab strip occluded — refusing to name a tab rather than guess")
        else:
            best_tab, best_val = None, 0.0
            second_val = 0.0
            for t, v in sig["tab_border"].items():
                if v > best_val:
                    second_val = best_val
                    best_tab, best_val = t, v
                elif v > second_val:
                    second_val = v
            if best_tab and best_val >= _TAB_BORDER_THRESH and (second_val == 0 or best_val >= 1.5 * second_val):
                tab = best_tab
                reasons.append("tab border matched %s (%.4f vs runner-up %.4f)" % (best_tab, best_val, second_val))
                if tab in NO_LEDGER_TABS:
                    reasons.append("tab=%s has NO LEDGER PATH today (NO_LEDGER_TABS) — "
                                   "not folded into unique or sets" % tab)
            else:
                reasons.append("tab border ambiguous (%s) — refusing to name a tab" % sig["tab_border"])

    return {
        "is_chronicle": bool(is_chronicle),
        "tab": tab,
        "confidence": round(min(1.0, max(0.0, score)), 2),
        "why": "; ".join(reasons) if reasons else "no signal",
    }


def detect_from_ocr_lines(lines) -> Optional[str]:
    """WEAK SECONDARY ONLY (round-1 correction #1). Never the production classify source, never
    allowed to override a pixel verdict from `detect()`. Exists purely so a caller with OCR lines
    already in hand (e.g. a lane that ran OCR for some other reason) can add one more corroborating
    word to `why` — nothing here should ever gate is_chronicle or tab on its own.

    Returns a loose guess ("unique"/"sets"/"runewords") or None; deliberately does not distinguish
    "found nothing" from "no lines given" because neither is trustworthy enough to act on alone.
    """
    if not lines:
        return None
    text = " ".join(str(l) for l in lines).upper()
    if "RUNEWORD" in text:
        return "runewords"
    if "SETS" in text or "SET ITEM" in text:
        return "sets"
    if "UNIQUE" in text or "VNIQVE" in text:
        return "unique"
    return None


if __name__ == "__main__":
    import sys

    from console_safe import enable

    enable()
    for p in sys.argv[1:]:
        print(p, detect(p))
