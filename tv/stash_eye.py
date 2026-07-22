# stash_eye.py — eye/brain frame analysis that MIMICS the perfected tally intakes
# without calling or changing gemIntake / runeIntake / materialIntake.
#
# Source of crop truth: bible.html `_tallyPrepImage` v341.59 LOCKED fractions
# (aspect 1.45–1.62, W≥1200 fullscreen D2R):
#   runes: x0=0.083 y0=0.20 x1=0.402 y1=0.468  (9-wide, cube-wrapped)
#   gems:  x0=0.105 y0=0.205 x1=0.388 y1=0.445  (clean 7×5)
# Tab chrome sits JUST ABOVE that grid band — we OCR an upscaled strip there so
# Personal/Shared/Gems/Materials/Runes are readable (full-frame OCR is dark).
#
# Used by: control_app KAI closer + router votes; tv_diablo live stashTab resolve.
# NEVER imports bible, NEVER fires intake, NEVER mutates stash tallies.

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ── LOCKED crop fractions (mirror bible.html _tallyPrepImage) ──────────────
_TALLY_CROPS = {
    "runes": (0.083, 0.20, 0.402, 0.468),
    "gems": (0.105, 0.205, 0.388, 0.445),
    # materials uses the same left-panel band as runes (generic left stash)
    "materials": (0.083, 0.20, 0.402, 0.468),
    "shared": (0.083, 0.18, 0.402, 0.55),
    "personal": (0.083, 0.18, 0.402, 0.55),
}
# Tab labels ride above the grid; measured on 2940×1912 film of this product
_TAB_CHROME = (0.08, 0.12, 0.40, 0.205)

_TALLY_TABS = frozenset(("runes", "gems", "materials"))
_VAULT_TABS = frozenset(("personal", "shared"))
_ALL_TABS = _TALLY_TABS | _VAULT_TABS

# v948.8 — D2R TITLE/RECONNECT SPLASH GUARD. classify_stash_grid's materials
# branch (dark_empty>=0.42 + a little chroma, low gear/tan) is tuned loose on
# purpose (materials is the tab most prone to under-detection — Konyo's repeated
# complaint). That looseness has a false-positive twin: the D2R title/reconnect
# screen ("Press Any Key to Begin" / "Connecting to Battle.net") is ~92% pure
# black with a burning-logo sliver of orange/red chroma — same signature as a
# near-empty materials grid. Caught 2026-07-21 auditing reel
# s_1784636825977_40909: 11 consecutive boot-screen frames grid-fingerprinted
# as stash-materials and the KAI retro funnel spent its one materials shot on
# one of them (materialIntake correctly came back ok:false/total:0 — nothing
# was there — but the slot was wasted and the routing ledger lied about tab
# state). Full-frame OCR still reads the splash text even when the tab-chrome
# crop is pure black, so it's a clean, additive guard that never tightens (and
# so never regresses) the fragile grid heuristic itself.
def is_boot_screen(ocr_lines: Optional[Sequence[Any]]) -> bool:
    """True when full-frame OCR lines match the D2R title/reconnect splash.

    Word-level (not exact-phrase) match — OCR on the fire-lit splash text is
    noisy ("PRESS ANY KfY T& BEGIN" for "...KEY TO BEGIN"), so a strict phrase
    regex missed the exact frame this guard was built for. Any one of these
    combos is distinctive enough that a real stash/gameplay frame won't hit it."""
    blob = " " + re.sub(r"[^a-z0-9]+", " ", " ".join(str(t) for t in (ocr_lines or [])).lower()) + " "
    if blob.strip() == "":
        return False
    def has(w):
        return (" " + w + " ") in blob
    if has("press") and has("any") and has("begin"):
        return True
    if has("connecting") and has("battle"):
        return True
    if has("diablo") and has("resurrected"):
        return True
    if has("blizzard") and has("entertainment"):
        return True
    return False


def tab_from_ocr_lines(lines: Optional[Sequence[Any]]) -> str:
    """Active-tab guess from OCR lines.

    Stash chrome always prints ALL five tab names — first-hit order wrongly
    returned 'materials' whenever the strip was fully readable. Rule:
      · 0 hits → ''
      · 1 unique canon → that tab
      · 2+ canons → '' (ambiguous chrome; pixel/grid fingerprint decides)
    """
    blob = " ".join(str(t).lower() for t in (lines or []))
    if not blob.strip():
        return ""
    # normalize common OCR garble of RotW tab labels (never break the word "materials")
    blob = re.sub(r"matera?l\$?", "materials", blob)   # mATERIAL$ style
    blob = re.sub(r"materlal", "materials", blob)
    blob = re.sub(r"sha[ak]e?d", "shared", blob)
    blob = re.sub(r"pers[o•\*]*n?a?l?", "personal", blob)
    # gems garbles: G→6/9, m→rn/nn, trailing $/s noise (Gems is the shortest label
    # so OCR mangles it hardest — the ROUND-2 miss). Keep bounded to gem-ish tokens.
    blob = re.sub(r"\b[6g9]e[rmn]{1,3}[sz$]?\b", "gems", blob)
    blob = re.sub(r"\bgens\b", "gems", blob)
    blob = re.sub(r"\bgemz\b", "gems", blob)
    order = (
        ("materials", "materials"), ("material", "materials"),
        ("runes", "runes"), ("gems", "gems"),
        ("personal", "personal"), ("shared", "shared"),
        ("rune", "runes"), ("gem", "gems"),
    )
    hits: List[str] = []
    for key, canon in order:
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", blob):
            if canon not in hits:
                hits.append(canon)
    if len(hits) == 1:
        return hits[0]
    return ""


def _open_rgb(path: str):
    from PIL import Image  # type: ignore
    im = Image.open(path).convert("RGB")
    return im


def _crop_frac(im, frac: Tuple[float, float, float, float]):
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


def prep_tab_chrome(src_path: str, dest_path: str, scale: int = 3) -> Optional[str]:
    """Intake-style: crop tab chrome ABOVE the tally grid, upscale, high-contrast JPEG.

    Returns dest_path on success, else None. Mimics how intakes enlarge digits —
    tab labels need the same treatment or Vision/OCR returns [].
    """
    try:
        from PIL import ImageEnhance, ImageOps  # type: ignore
        im = _open_rgb(src_path)
        crop = _crop_frac(im, _TAB_CHROME)
        if crop is None:
            return None
        sw, sh = crop.size
        if sw < 8 or sh < 4:
            return None
        up = crop.resize((max(8, sw * scale), max(8, sh * scale)), getattr(__import__("PIL.Image", fromlist=["Image"]).Image, "LANCZOS", 1))
        g = ImageOps.autocontrast(up.convert("L"))
        g = ImageEnhance.Contrast(g).enhance(2.4)
        # also keep a color path for Vision OCR workers that want RGB
        rgb = up.convert("RGB")
        rgb = ImageEnhance.Contrast(rgb).enhance(1.8)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)) or ".", exist_ok=True)
        rgb.save(dest_path, format="JPEG", quality=95)
        return dest_path
    except Exception:
        return None


def prep_stash_grid(src_path: str, dest_path: str, layout: str = "runes",
                    max_edge: int = 1200, cap: float = 3.2) -> Optional[str]:
    """Mimic _tallyPrepImage crop+enlarge for a layout (runes|gems|materials|shared).

    Pure image prep — does NOT call intake or the model.
    """
    try:
        from PIL import Image  # type: ignore
        im = _open_rgb(src_path)
        w, h = im.size
        aspect = (w / float(h)) if h else 0
        frac = _TALLY_CROPS.get(layout) or _TALLY_CROPS["runes"]
        if 1.45 <= aspect <= 1.62 and w >= 1200:
            crop = _crop_frac(im, frac)
        elif aspect >= 1.3:
            # foreign / windowed — whole left 46% (same law as intake foreign tier)
            crop = im.crop((0, 0, max(8, int(w * 0.46)), h))
        else:
            crop = _crop_frac(im, frac)
        if crop is None:
            return None
        sw, sh = crop.size
        scale = min(cap, max_edge / float(max(sw, sh, 1)))
        nw = max(1, int(round(sw * scale)))
        nh = max(1, int(round(sh * scale)))
        up = crop.resize((nw, nh), Image.LANCZOS)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)) or ".", exist_ok=True)
        up.save(dest_path, format="JPEG", quality=92)
        return dest_path
    except Exception:
        return None


def classify_stash_grid(src_path: str) -> Tuple[str, Dict[str, Any]]:
    """Pixel fingerprint of the left stash GRID (intake crop region) → tab guess.

    Mimics the spirit of _runeSheetPrep (luminance / owned-stone detection) and
    gem colour columns — WITHOUT running the intake model.

    Returns (label, detail) where label is one of:
      stash-runes | stash-gems | stash-materials | stash | gameplay
    """
    detail: Dict[str, Any] = {"method": "grid-fingerprint"}
    try:
        from PIL import Image  # type: ignore
        im = _open_rgb(src_path)
        w, h = im.size
        if w < 200 or h < 200:
            return "gameplay", detail
        # use gems crop as the common left-grid window (overlaps runes/materials)
        crop = _crop_frac(im, _TALLY_CROPS["gems"])
        if crop is None:
            return "gameplay", detail
        # sample down for speed
        g = crop.resize((84, 56), Image.BILINEAR)
        px = list(g.getdata())
        n = len(px) or 1
        # features
        gold_tan = 0      # rune stones (pale limestone / tan)
        chroma = 0        # saturated gems (ruby/sapphire/emerald…)
        dark_empty = 0
        mid_gear = 0      # mixed shared/personal equipment
        bright = 0
        hue_bkt = [0] * 6  # v948.20 — sextant histogram of the saturated pixels
        for r, gch, b in px:
            lum = 0.299 * r + 0.587 * gch + 0.114 * b
            if lum > 115:
                bright += 1
            if lum < 40:
                dark_empty += 1
            # limestone / parchment rune: high lum, low chroma, R≈G≈B or slightly warm
            cr = abs(r - gch) + abs(gch - b) + abs(r - b)
            if lum > 100 and cr < 55 and r > 90:
                gold_tan += 1
            # gem: high chroma, one channel dominates
            mx, mn = max(r, gch, b), min(r, gch, b)
            if (mx - mn) > 70 and mx > 120 and lum > 50:
                chroma += 1
                # sextant hue bucket (standard HSV hue → 6 bins), df>0 guaranteed
                df = mx - mn
                if mx == r:
                    hh = ((gch - b) / df) % 6
                elif mx == gch:
                    hh = ((b - r) / df) + 2
                else:
                    hh = ((r - gch) / df) + 4
                hue_bkt[int(hh) % 6] += 1
            # gear/metal: mid lum, moderate chroma (rings, charms)
            if 55 < lum < 140 and 25 < cr < 90:
                mid_gear += 1
        ft = gold_tan / n
        fc = chroma / n
        fd = dark_empty / n
        fg = mid_gear / n
        fb = bright / n
        # v948.20 — hue diversity: how many hue sextants each hold a meaningful share
        # of the saturated pixels. The Gems tab is a grid of DISTINCT gem colours
        # (ruby-red · emerald-green · sapphire-blue · amethyst-purple · topaz-yellow),
        # so ≥3 sextants light up — a fire-spark / single-colour gameplay frame does not.
        _hmin = max(2, int(0.006 * n))
        hue_div = sum(1 for x in hue_bkt if x >= _hmin)
        detail.update({
            "frac_tan": round(ft, 4), "frac_chroma": round(fc, 4),
            "frac_dark": round(fd, 4), "frac_gear": round(fg, 4),
            "frac_bright": round(fb, 4), "hue_div": hue_div,
        })
        # decision tree — shared/personal vaults have COLOURED ring gems (chroma)
        # that must NOT be misread as the Gems tab. Gear density gates first.
        # shared/personal: gear / mixed mid-tones dominate the left panel
        if fg >= 0.14:
            detail["pick"] = "stash"
            return "stash", detail
        # gems tab: high chroma AND low gear (pure jewel grid, not jewelry on gear)
        if fc >= 0.11 and fg < 0.10 and fc >= ft:
            detail["pick"] = "gems"
            return "stash-gems", detail
        # v948.20 — gems tab, MODERATE chroma (the ROUND-2 miss). A packed gem grid is
        # small vivid icons on mostly-dark cells, so total chroma is only ~0.05-0.10 —
        # it fell in the DEAD ZONE between the high-chroma gems floor (fc>=0.11) above
        # and the materials chroma cap (fc<0.045) below, and dropped to stash-default.
        # ROOT of the s_1784736270319 f_1784736381363 GEMS MISS: fc=0.058 measured.
        # Discriminated from dark-gameplay fire-sparks (fc~0.025) by the fc floor, and
        # from a single-colour glow by hue_div>=3 (multiple distinct gem colours). fd is
        # a closed stash-panel band (splash/combat run much darker). Verified on a
        # 2722-frame sweep of every reel: fires on 67 frames, ALL genuine Gems-tab stills
        # across 16 sessions, zero flips out of materials/runes/gameplay.
        if (0.045 <= fc < 0.11 and hue_div >= 3 and fg < 0.12
                and ft < 0.08 and 0.30 <= fd <= 0.55 and fc >= ft):
            detail["pick"] = "gems-multihue"
            return "stash-gems", detail
        # runes: pale limestone stones dominate (tan high, chroma low)
        if ft >= 0.08 and fc < 0.06 and fb >= 0.12:
            detail["pick"] = "runes"
            return "stash-runes", detail
        # materials: dark empties + a little chroma (essences/keys/organs) but NOT
        # gear-dense vault, NOT the vivid gem chroma band, and BOUNDED away from
        # near-pure-black scenes (boot/loading splash, dark gameplay with fire chroma —
        # the false-positive twin the is_boot_screen guard was built for).
        # v948.19 — RECALIBRATED (Grok forensic #5, 2026-07-21 21:05 fast run: 'materials 0
        # classes'). The old band (fd>=0.42, fc 0.04-0.10) was miscalibrated on BOTH sides,
        # found by cross-referencing real materialIntake RECEIPTS (ground truth — the LOCKED
        # intake actually read materials and confirmed totals) against their source frames:
        #   · UNDER-detection: 2 receipted-real materials frames (reel_s_1784561282553_86929/
        #     f_1784561356596.jpg total=184, reel_s_1784561832500_95271/f_1784561874907.jpg
        #     total=210) measured fd=0.3839 fc=0.0308 — BELOW the old fd>=0.42 and fc>=0.04
        #     floors, so the grid vote never fired and only OCR chrome-read could catch it.
        #   · OVER-detection: dark gameplay-with-fire combat frames (e.g.
        #     reel_s_1784647619282_26240/f_1784647734875.jpg, a Catacombs fight, fd=0.7795)
        #     and D2R boot/reconnect splash frames (fd 0.85-0.95, the is_boot_screen class)
        #     landed INSIDE the old band and grid-fingerprinted as materials with zero UI
        #     open — exactly the wrong-cell class this heuristic must never produce.
        # New band verified against a 3200-frame sweep of every historical reel: adds the 2
        # receipted-real frames + 4 more visually-confirmed Materials-tab frames across 4
        # OTHER sessions (true positives), while removing 88 false positives (every one
        # inspected was a boot-splash/lobby cluster at a reel's start) and zero confirmed
        # regressions on gems/personal/shared/runes ground truth. fd is now a closed band
        # (not just a floor) because every confirmed real STASH-panel frame across all tabs
        # sampled fd in [0.31, 0.42] — gameplay/splash scenes run much darker.
        if 0.30 <= fd <= 0.55 and 0.02 <= fc < 0.045 and fg < 0.12 and ft < 0.08:
            detail["pick"] = "materials"
            return "stash-materials", detail
        # softer vault
        if fg >= 0.08 or (fb >= 0.08 and ft < 0.10):
            detail["pick"] = "stash"
            return "stash", detail
        if fd >= 0.60 and fb < 0.06:
            detail["pick"] = "gameplay"
            return "gameplay", detail
        detail["pick"] = "stash-default"
        return "stash", detail
    except Exception as e:
        detail["err"] = str(e)[:80]
        return "gameplay", detail


def fuse_tab_signals(
    ocr_tab: str = "",
    grid_label: str = "",
    journal_tab: str = "",
    model_tab: str = "",
    allow_grid_solo: bool = False,
) -> Tuple[str, List[str]]:
    """Fuse eye signals into one tab + list of agreeing sources.

    Priority (eyes, before router):
      1) OCR single-tab (chrome strip) when unambiguous
      2) grid fingerprint tally tab (runes/gems/materials)
      3) model deep-read stashTab
      4) journal sticky
      5) grid said plain stash → personal/shared from journal/model if any

    allow_grid_solo (v948.7 KAI retro): when the film still is already a stash panel
    (grid/chrome fingerprint), grid may promote runes/gems/materials WITHOUT a live
    deep journal sticky — Theatre has the pixels; post-seal funnel must recheck them.
    Live path keeps allow_grid_solo=False so loading screens don't invent tallies.
    """
    sources: List[str] = []
    ocr_tab = (ocr_tab or "").lower().strip()
    journal_tab = (journal_tab or "").lower().strip()
    model_tab = (model_tab or "").lower().strip()
    gl = (grid_label or "").lower().strip()
    grid_tab = ""
    if gl.startswith("stash-"):
        grid_tab = gl[len("stash-"):]
    elif gl == "stash":
        grid_tab = "stash"

    # stash-open corroboration — grid alone on a dark loading screen invents materials
    stash_open = (
        journal_tab in _ALL_TABS or journal_tab == "stash"
        or model_tab in _ALL_TABS or model_tab == "stash"
        or ocr_tab in _ALL_TABS
        or grid_tab == "stash"
        or str(grid_label or "").startswith("stash")
    )

    # 1 OCR tally wins over vague vault labels (same law as live _resolve_stash_tab)
    if ocr_tab in _TALLY_TABS:
        sources.append("ocr")
        if grid_tab == ocr_tab:
            sources.append("grid")
        if journal_tab == ocr_tab:
            sources.append("journal")
        if model_tab == ocr_tab:
            sources.append("model")
        return ocr_tab, sources

    # 2 grid fingerprint tally — when stash panel is open
    if grid_tab in _TALLY_TABS and stash_open:
        # live: need journal/model/ocr corroboration (or journal vault sticky counts as open)
        # KAI retro: allow_grid_solo when grid itself already classified a tally layout
        has_other = bool(journal_tab or model_tab or ocr_tab)
        if has_other or allow_grid_solo:
            sources.append("grid")
            if allow_grid_solo and not has_other:
                sources.append("solo")
            if journal_tab == grid_tab:
                sources.append("journal")
            if model_tab == grid_tab:
                sources.append("model")
            if ocr_tab == grid_tab:
                sources.append("ocr")
            return grid_tab, sources

    # 3 model tally
    if model_tab in _TALLY_TABS:
        sources.append("model")
        if journal_tab == model_tab:
            sources.append("journal")
        return model_tab, sources

    # 4 journal tally sticky
    if journal_tab in _TALLY_TABS:
        sources.append("journal")
        return journal_tab, sources

    # 5 vault tabs
    for cand, src in ((ocr_tab, "ocr"), (model_tab, "model"), (journal_tab, "journal")):
        if cand in _VAULT_TABS:
            sources.append(src)
            if grid_tab in ("stash", "personal", "shared"):
                sources.append("grid")
            return cand, sources

    if grid_tab == "stash" or gl == "stash":
        sources.append("grid")
        return "shared" if not journal_tab else journal_tab, sources  # plain stash panel open

    return "", sources


def class_from_tab(tab: str) -> str:
    tab = (tab or "").lower()
    if tab in _TALLY_TABS:
        return "stash-" + tab
    if tab in _VAULT_TABS or tab == "stash":
        return "stash"
    return ""


def analyze_frame(
    path: str,
    ocr_lines: Optional[Sequence[Any]] = None,
    journal_tab: str = "",
    model_tab: str = "",
    ocr_worker_read=None,
    work_dir: Optional[str] = None,
    allow_grid_solo: bool = False,
) -> Dict[str, Any]:
    """Full eye analysis of one photo (for KAI / live resolve).

    ocr_worker_read: optional callable(path)->dict with 'lines' (warm OCR worker).
    When provided, tab chrome is prepped intake-style and re-OCR'd.
    allow_grid_solo: KAI retro reel pass — grid may name tally tabs without live sticky.
    """
    out: Dict[str, Any] = {
        "path": path,
        "ocrTab": "",
        "gridLabel": "",
        "gridDetail": {},
        "tab": "",
        "cls": "gameplay",
        "sources": [],
        "kaiVer": 3,
    }
    if not path or not os.path.isfile(path):
        return out

    # v948.8 — title/reconnect splash guard, before grid/OCR tab fusion can
    # mistake the burning-logo screen for a near-empty materials grid.
    if is_boot_screen(ocr_lines):
        out["cls"] = "gameplay"
        out["sources"] = ["boot-screen-guard"]
        return out

    # full-frame OCR lines if already available
    ocr_tab = tab_from_ocr_lines(ocr_lines or [])
    # intake-style tab chrome re-OCR
    if ocr_worker_read is not None:
        try:
            wd = work_dir or os.path.dirname(path) or "/tmp"
            chrome = os.path.join(wd, ".stash_eye_tab.jpg")
            if prep_tab_chrome(path, chrome):
                j = ocr_worker_read(chrome) or {}
                t2 = tab_from_ocr_lines(j.get("lines") or [])
                if t2:
                    ocr_tab = t2
                    out["chromeOcr"] = list((j.get("lines") or [])[:8])
        except Exception:
            pass
    out["ocrTab"] = ocr_tab

    gl, gd = classify_stash_grid(path)
    out["gridLabel"] = gl
    out["gridDetail"] = gd

    tab, sources = fuse_tab_signals(
        ocr_tab, gl, journal_tab, model_tab, allow_grid_solo=allow_grid_solo)
    out["tab"] = tab
    out["sources"] = sources
    # class from fused tab; retro solo grid still only yields cls when fuse accepted it
    if tab:
        out["cls"] = class_from_tab(tab) or "gameplay"
    elif gl == "stash" and (journal_tab or model_tab or ocr_tab or allow_grid_solo):
        out["cls"] = "stash"
    else:
        out["cls"] = "gameplay"
    return out
