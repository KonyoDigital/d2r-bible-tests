"""v1511 — CHRONICLE RETRO SWEEP, the engine.

Konyo: "retro and live... especially retro most important" — the sealed reels already contain every
Chronicle screen he has ever opened on camera. This module finds those frames and turns them into a
PROPOSAL. It never writes a ledger.

Three laws, and they are the whole design:

  1. READ-ONLY UNTIL APPLY. `sweep()` returns evidence. Only `apply_proposal()` changes anything, and
     it is a separate call a human makes. A sweep that silently ticked 400 grail rows would be
     unauditable — and un-untickable, because there is no "unfind" in Diablo.
     NO exception: this module cannot write AT ALL, and `test_chronicle_retro` proves it from the
     source text. The v1608 index recovery therefore lives next door in `reel_index.py` — this file
     only READS a missing index back (`reconstruct_index`/`load_index`); reel_index.py is the one
     that puts the rebuilt index on disk.

  2. MERGE-MAX. A chronicle read only ever ADDS. His ledger is the accumulated truth of years; a reel
     from March cannot un-find something found in July, and a page that scrolled past a row is not
     evidence that the row is empty. `notFound` is carried for auditing and never subtracts.

  3. PAY FOR RUNS, NOT FRAMES. A reel is ~150 frames at 1-2fps; reading each one would cost more than
     the tally is worth, and 140 of them are the same page held still. Frames are grouped into STILL
     RUNS, one frame per run is classified, and only runs that come back `chronicle` are read in full.
     A 153-frame reel with one Chronicle visit costs ~8 classifies + the pages, not 153 reads.
     v1689 — AND FRAMES SOMEBODY ALREADY IDENTIFIED ARE NOT PAID FOR TWICE. `known_chronicle` lets a
     caller hand in the frames its journal already marked scene='chronicle' (the live vision lane
     writes exactly that, with the tab); those frames become candidates whatever their stillness and
     cost ZERO classifies, because the classify stage's question is already answered for them.

Everything here is pure: the caller injects the signature function and the reader. That is what lets
the tests exercise the laws against fixtures without a vision model or a single JPEG.
"""

import json
import os
import re

# A "still" pair — frames this similar are the same screen held. Calibrated against sig_diff()'s own
# scale in tv_diablo.py, where ambient render noise stays under the tolerance and opening a panel
# moves whole regions past it.
# v1689 — THE CLAIM THIS COMMENT USED TO MAKE WAS FALSE, and it is the whole reason the retro lane
# never found his Chronicle. It said the threshold was "loose enough to keep a scrolling read in one
# run rather than shattering it into singletons". Measured on reel_s_1786385768689_67392 (217
# frames): the 8 frames the live lane read as Chronicle pages shattered into singleton runs and NOT
# ONE became a candidate — reading a Chronicle means scrolling it, and a scrolled list moves enough
# of the frame to blow past 0.22. The threshold is left alone (loosening it would weld unrelated
# screens together); the fix is `known_chronicle`, which lets already-identified frames in regardless.
STILL_MAX_DIFF = 0.22

# v1712 — THE CHRONICLE'S OWN STILL THRESHOLD, AND WHY IT IS 44× TIGHTER.
#
# THE DEFECT: at 0.22 the retro sweep read NOTHING from footage that provably holds Chronicle
# pages. Measured on his reel_s_1786385768689_67392 — 217 frames, 220 seconds, a journalled visit
# of 8 Chronicle frames — still_runs() returned **ONE run of all 217 frames**. Gameplay, town,
# Chronicle: one run. candidate_runs() then passed that single run on, live_probe() picked ONE
# frame to represent 220 seconds, the frame it picked was gameplay, and the whole session was
# discarded as not-a-Chronicle. That is why 9 of his 10 reels contribute zero pages: only the one
# reel with a journalled visit gets rescued, by known_chronicle= marks, through a different door.
#
# WHY THE THRESHOLD NEVER FIRED: jpeg_sig is a 16×16 grayscale fingerprint and sig_diff counts
# cells differing by more than tol=28. Across the ENTIRE reel the largest frame-to-frame diff is
# 0.133, and the median is 0.000 — at this resolution a D2R scene change simply does not move 22%
# of 256 cells. 0.22 was above the ceiling of what the signal can produce, so no pair ever broke a
# run. A threshold nothing can ever cross is not a loose threshold; it is an absent one.
#
# THE SIGNAL IS THERE. The Chronicle ENTRY boundary measures 0.113 — the largest jump in the reel,
# and 14× the p90 of everything else (0.008). Inside the panel, consecutive frames measure
# 0.000–0.012: he holds it, and scrolling a list moves few cells at 16×16.
#
# CALIBRATION, all 10 reels / 731 frames, cost = classifies, yield = pages read:
#     max_diff   classified   pagesRead
#       0.220        22           0        ← shipped behaviour: pays 22 reads, finds nothing
#       0.010        35           4
#       0.005        45           9        ← chosen
#       0.002        44           8
# 0.005 sits on a stable shelf (0.002 gives 8, 0.005 gives 9) and roughly doubles the classify
# cost to turn a sweep that reads NOTHING into one that reads nine pages. The memory in
# chronicle_swept.json means that cost is paid once per reel, ever.
#
# ⚠ HONESTLY STATED: this is calibrated against the ONE session in his journal that carries a
# Chronicle visit, because that is the only ground truth that exists. It is a named constant
# rather than a number inside a comparison precisely so the next measurement can move it.
# ⚠ NOT SHARED WITH THE VAULT. vault_retro.py:452 deliberately borrows still_runs() and says so
# ("chronicle_retro owns STILL_MAX_DIFF / MIN_RUN_FRAMES"). Retuning the shared constant would
# silently change the vault sweep's cost and grouping on footage nobody measured here, so the
# Chronicle passes its own value explicitly and STILL_MAX_DIFF keeps its meaning for that caller.
CHRON_STILL_MAX_DIFF = 0.002
# v1758 — 0.005 WAS ABOVE THE SIGNAL IT WAS MEANT TO MEASURE, which is the same defect v1712 fixed
# one order of magnitude up (0.22 against a signal whose max was 0.133). Measured on his own
# 08-11 visit, the eight frames the console recorded as ONE chronicle visit:
#
#     2_ -> 3_   0.00000   the same page, genuinely held
#     3_ -> 4_   0.00000   the same page
#     4_ -> 5_   0.00391   A DIFFERENT PAGE  <- merged at 0.005
#     5_ -> 6_   0.00391   A DIFFERENT PAGE  <- merged
#     6_ -> 8_   0.00391   A DIFFERENT PAGE  <- merged
#     8_ -> 9_   0.00000   the same page
#     9_ -> 7_   0.00781   a different page
#
# So SCROLLING the Chronicle moves this fingerprint by 0.00391 and the threshold sat at 0.005: all
# eight frames collapsed into one run, the sweep read the FIRST page only, that page was the top of
# the list showing unfound silhouettes, it refused with "no-found-state", and the visit reported
# nothing found. Seven pages carrying real "First Found" lines - Bartuc's Cut-Throat at 05/20/2026
# 02:19 among them - were never read. That is why his Chronicle never synced: not a missing
# watchdog, a reader that could not see a scroll.
#
# WHY 0.002 AND NOT SOMETHING TUNED-LOOKING: the signal is bimodal with a clean gap. A held page is
# EXACTLY 0.00000 (the fingerprint is identical) and the smallest real page change is 0.00391, so
# every threshold in that gap gives the same answer - measured at 0.003, 0.002, 0.001 and 0.0005,
# all five runs. 0.002 sits in the middle of the gap rather than at either edge.
#
# Why the signal is so small at all: jpeg_sig is a 16x16 grayscale fingerprint of the WHOLE frame,
# and the Chronicle panel's chrome dominates it. The rows of text that actually change are a small
# fraction of those 256 cells, so a full page of different items moves less than 0.4%.
#
# COST: this multiplies reads for a scrolled visit - 5 pages instead of 1 on the frames above. That
# is the point. A sweep that costs one read and finds nothing is not the cheap option.
# Below this a run is somebody walking through town, not a screen being read.
MIN_RUN_FRAMES = 3


def jpeg_sig(path):
    """A 16×16 grayscale fingerprint of a reel JPEG, as 256 bytes.

    Deliberately NOT tv_diablo.frame_sig: that samples raw BMP pixel offsets, and JPEG entropy coding
    shifts every byte after the smallest change — byte-sampling two near-identical JPEGs reads as a
    total mismatch. Decoding is the only honest comparison. Returns None (never a wrong answer) when
    Pillow is absent or the file is unreadable; callers treat None as "cannot group".
    """
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None
    try:
        with Image.open(path) as im:
            return im.convert("L").resize((16, 16)).tobytes()
    except Exception:
        return None


# v1543 — a frame this uniformly one tone carries no screen. Measured on his own reels: the two dead
# captures came in at 95.0% and 99.4%, while the BUSIEST legitimately-dark frame — the D2R title
# screen, which is mostly black — sat at 82.7%. 0.92 leaves a wide margin on both sides. Calibrated
# on one machine's footage, so it is a named constant rather than a number buried in a comparison.
DEAD_FLATNESS = 0.92


def frame_flatness(path):
    """What share of the frame is a single flat tone (0..1), or None if it cannot be measured.

    None is not 0.0 and the difference matters: "I could not look" must never be spent as "I looked
    and it was fine", which is the mistake REG-086 was made of.
    """
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return None
    try:
        with Image.open(path) as im:
            h = im.convert("L").resize((96, 96)).histogram()
    except Exception:
        return None
    n = sum(h)
    if not n:
        return None
    # widest share inside any 17-wide luminance window — one flat tone, allowing for JPEG dither
    return max(sum(h[i:i + 17]) for i in range(0, 240)) / float(n)


def is_dead_frame(path, threshold=DEAD_FLATNESS):
    """A blank capture: the window was grabbed while it had nothing on it.

    Konyo's four reels hold three of these among eleven still screens — a white window, a black one,
    and a black one with a title bar. They are not Chronicle pages and never can be, but the sweep
    still paid a classify for each, and the reader dutifully answered "not a chronicle" about a photo
    of nothing. Refusing them is a straight saving; more importantly, a capture lane producing blank
    frames at all is a fault worth SEEING rather than quietly paying for.

    Returns False when flatness cannot be measured — an unmeasurable frame is still read, because
    skipping something we could not judge is how a real Chronicle page would go missing.
    """
    f = frame_flatness(path)
    if f is None:
        return False
    return f >= threshold


def live_probe(frames, path_of, threshold=DEAD_FLATNESS):
    """Pick the frame in a run worth classifying: the middle one, unless it is blank.

    The middle frame is the most settled — the first can be mid-transition and the last mid-exit — so
    it stays the preference. When it is dead the run is not abandoned, because a window that blanked
    for a moment mid-visit is exactly the case where the rest of the run is still a real screen.
    Returns (frame, dead_seen), and (None, n) only when EVERY frame in the run is blank.
    """
    order = sorted(range(len(frames)), key=lambda i: abs(i - len(frames) // 2))
    dead = 0
    for i in order:
        if not is_dead_frame(path_of(frames[i]), threshold):
            return frames[i], dead
        dead += 1
    return None, dead


# v1758 — THE CHRONICLE NEEDS A FINER TOLERANCE THAN "DID THE SCREEN CHANGE".
#
# sig_diff's default tol=28 asks a coarse question on purpose: it is shared with tv_diablo so both
# halves reason about "same screen" on one scale, and 28/255 is right for town-vs-boss.
#
# It is the wrong question for a Chronicle page. jpeg_sig averages a 1440x936 frame into 16x16, so
# ONE cell is a ~90x58 block and the rows of text that change are a sliver of it. Measured on his
# own frames, two COMPLETELY different Chronicle pages — unfound silhouettes vs the A-section with
# Andariel's Visage and Atma's Wail — differ by at most ONE gray level in ONE of the 256 cells:
#
#     3_1786922965432  [35, 33, 25, 46, 59, 58, 40, 33, 32, 33, 31, 29, ...]
#     4_1786922970122  [35, 33, 25, 46, 59, 58, 40, 33, 32, 33, 31, 30, ...]
#
# Nothing clears 28, so sig_diff returns 0.00000 and the two pages read as one held screen. At
# tol=4 the same pairs separate cleanly (0.027 to 0.19 of cells differing).
#
# This is why every threshold above it looked wrong in turn: 0.06 in sweep_frames, then 0.005 in
# CHRON_STILL_MAX_DIFF. Neither was the cause. A threshold cannot rescue a comparison that has
# already thrown the signal away. [[feedback_threshold_above_the_ceiling]]
CHRON_SIG_TOL = 4


def sig_diff(a, b, tol=28):
    """Fraction of samples that MEANINGFULLY differ — the same contract as tv_diablo.sig_diff, so the
    two halves of the system reason about "same screen" on one scale."""
    if not a or not b:
        return 1.0
    if a == b:
        return 0.0
    m = min(len(a), len(b))
    return sum(1 for i in range(m) if abs(a[i] - b[i]) > tol) / m


def still_runs(frames, sig_of, max_diff=STILL_MAX_DIFF, tol=28):
    """Group consecutive frames into runs of "the same screen held still".

    frames: [{"f": name, "ts": ms}, ...] in capture order (a reel's index.json shape).
    sig_of: name -> fingerprint (or None when it cannot be read).

    An unreadable frame BREAKS the run rather than joining it. Silently absorbing a frame we could not
    compare would let one unreadable frame weld two different screens into a single run, and the run
    is what we then pay to classify ONCE — the misgrouping would be invisible and wrong.
    """
    runs = []
    cur = None
    prev_sig = None
    for fr in (frames or []):
        name = (fr or {}).get("f")
        if not name:
            continue
        # v1545 — a frame the seal marked BLANK is skipped outright rather than broken on. It is not
        # an unreadable frame (which must break the run, because we cannot tell what it was); it is a
        # frame we know carried no screen. Dropping it lets a visit that flickered for one frame stay
        # ONE run instead of two, which is one classify instead of two for the same panel.
        if fr.get("blank"):
            continue
        sig = sig_of(name)
        if sig is None:
            cur, prev_sig = None, None
            continue
        if cur is not None and sig_diff(prev_sig, sig, tol=tol) <= max_diff:
            cur["frames"].append(name)
            cur["end_ts"] = (fr.get("ts") or cur["end_ts"])
        else:
            cur = {"frames": [name], "start_ts": fr.get("ts") or 0, "end_ts": fr.get("ts") or 0}
            runs.append(cur)
        prev_sig = sig
    return runs


def candidate_runs(runs, min_frames=MIN_RUN_FRAMES):
    """The runs worth paying a classify for: a screen held still long enough to be READ.

    A Chronicle visit is somebody stopping to look. One or two still frames is a pause mid-fight."""
    return [r for r in (runs or []) if len(r.get("frames") or []) >= min_frames]


def _declared_kind(idx):
    """The chronicle ledger HE declared for this reel, or None.

    Accepts only the two chronicle focuses. A stash/rune/gem mini returns None here and this sweep
    ignores the reel exactly as before — the vault sweep is the one that owns those.
    """
    idx = idx if isinstance(idx, dict) else {}
    f = str(idx.get("focus") or "").strip().lower()
    return f if f in ("chronicle-uniques", "chronicle-sets") else None


# v1607 — THE MARK OF A REBUILT INDEX. Stamped into every index this module reconstructs so a reader
# can always tell "sealed with a full index" from "recovered from the frames on disk". Keep this
# string identical to the one the seal-side recovery writes; two different marks for the same fact
# is exactly the two-screens-disagree failure.
INDEX_REBUILD_MARK = "v1607-recovery"


def reconstruct_index(reel_dir):
    """v1607 — REBUILD A REEL'S index.json FROM THE FRAME NAMES ALONE. PURE: reads a directory
    listing, writes nothing, raises nothing.

    THE BUG THIS EXISTS FOR: a reel whose seal was interrupted keeps all its JPEGs and loses its
    index — and every reader in this file goes through index.json, so 98 frames of real farming
    footage become a black screen. Nothing about that is unrecoverable: a frame is named
    `f_<epoch-ms>.jpg`, which is EXACTLY the payload of an index row — {"f": name, "ts": ms}. The
    filenames ARE the index; the index.json was only ever a cache of them.

    BLANK FLAGS ARE DELIBERATELY OMITTED, and that is a decision, not an oversight:
      · they cost a full JPEG decode per frame (MEASURED on his own 98-frame reel: 0.076–0.082 s
        per frame, ≈8 s of decoding for that one reel),
        and that decode pass is the exact expense that let a kill land before the index was written.
        Rebuilding must never be able to lose the thing it is rebuilding.
      · absent "blank" already means "unmeasured, not blank" everywhere in this module (see the
        seal's v1545 note and live_probe(), which measures for itself when the flag is missing) —
        so an index without the flags is READ correctly today, at the cost of some decodes later.
      · a GUESSED flag would be worse than none: a frame wrongly marked blank is footage silently
        withheld from the sweep, and there is no "unfind" for a page he never got read.
    An index that omits what it did not measure is honest. There is no lazy backfill here on purpose.

    Returns the index dict, or None when the directory holds no parseable frame.
    """
    try:
        names = os.listdir(reel_dir)
    except Exception:
        return None
    rows = []
    for n in names:
        if not (n.startswith("f_") and n.endswith(".jpg")):
            continue
        try:
            ts = int(n[2:-4])
        except (ValueError, TypeError):
            continue          # a name that is not f_<ms>.jpg is not a frame; skip it, never raise
        rows.append({"f": n, "ts": ts})
    if not rows:
        return None
    # Capture ORDER is what still_runs() consumes, and for these names ts order IS capture order.
    rows.sort(key=lambda r: (r["ts"], r["f"]))
    base = os.path.basename(os.path.normpath(reel_dir))
    sid = base[5:] if base.startswith("reel_") else base
    return {"sessionId": sid, "n": len(rows), "frames": rows, "rebuilt": INDEX_REBUILD_MARK}


def _index_ok(idx):
    """A parsed index is USABLE only if it actually carries frames. A dict with an empty/absent
    frames list is indistinguishable from a black screen to every reader here."""
    return isinstance(idx, dict) and bool(idx.get("frames"))


def load_index(reel_dir):
    """THE ONE ACCESSOR every read path in this module goes through. Never writes.

    On-disk index when it exists and parses; otherwise the reconstruction. A truncated or corrupt
    index FALLS BACK rather than raising — a half-written index.json is the same interrupted seal,
    and refusing to play the reel would punish him twice for one crash. Returns None only when there
    is no index and no frame to rebuild one from.
    """
    try:
        with open(os.path.join(reel_dir, "index.json"), encoding="utf-8") as fh:
            idx = json.load(fh)
        if _index_ok(idx):
            return idx
    except Exception:
        idx = None
    return reconstruct_index(reel_dir) or (idx if isinstance(idx, dict) else None)


def _known_kind(v):
    """One journal answer → a chronicle intake kind, or None.

    Accepts the three shapes a caller already has: the raw reader dict the journal stores
    ({"scene": "chronicle", "chronicleTab": "uniques"}), the bare tab word, or the kind itself.
    chronicle_kind()'s refusal is inherited whole — an unreadable tab is None, never a guess.
    """
    if isinstance(v, dict):
        return chronicle_kind(v)
    s = str(v or "").strip().lower()
    if s in ("chronicle-uniques", "chronicle-sets"):
        return s
    if s in ("uniques", "sets"):
        return "chronicle-" + s
    return None


def _known_chronicle_map(known):
    """Normalize `known_chronicle` to {frameName: kind-or-None}. A bare iterable of names is
    "these ARE Chronicle frames, tab unknown" — which is a real state and not the same as absent."""
    if not known:
        return {}
    if isinstance(known, dict):
        return {str(k): _known_kind(v) for k, v in known.items()}
    return {str(n): None for n in known}


# v1689 — HOW FAR A JOURNAL MARK MAY REACH FOR ITS FRAME. The deep lane names its captures
# "<seq>_<captureMs>.jpg" and the reel names its own "f_<captureMs>.jpg" from a DIFFERENT grab, so
# the two never match by string. Measured on his 217-frame reel against the 8 journal rows: the
# nearest reel frame was 55-432ms away, every time, and the reel runs at 1-2fps. 1500ms is wide
# enough for the worst of those and still narrower than the gap to any other session's footage.
JOURNAL_MATCH_MS = 1500


def _key_ms(key):
    """The capture timestamp inside a frame key ('2_1786385782689' → 1786385782689), or None."""
    digits = re.findall(r"\d{10,}", str(key))
    return int(digits[-1]) if digits else None


def _resolve_known(frames, known):
    """Bind the journal's marks to THIS reel's frame names. Pure: reads the index rows it is given.

    A mark arrives as a frame name when the caller already has one, and as a deep-lane frameId
    otherwise — those are a different capture of the same moment, so they are matched by TIME, to the
    nearest frame inside JOURNAL_MATCH_MS. Out of range is dropped rather than stretched: a mark that
    cannot find its frame is worth nothing, and a mark welded onto the wrong frame is worth less.
    """
    if not known:
        return {}
    by_name = {}
    for fr in (frames or []):
        nm = (fr or {}).get("f")
        if nm:
            by_name[nm] = fr.get("ts") or 0
    out = {}
    for key, kind in known.items():
        base = os.path.basename(str(key))
        if base in by_name:
            out[base] = kind
            continue
        if base + ".jpg" in by_name:
            out[base + ".jpg"] = kind
            continue
        ms = _key_ms(base)
        if ms is None:
            continue
        best, best_d = None, None
        for nm, ts in by_name.items():
            if not ts:
                continue
            d = abs(int(ts) - ms)
            if best_d is None or d < best_d:
                best, best_d = nm, d
        if best is not None and best_d <= JOURNAL_MATCH_MS:
            out[best] = kind
    return out


def _run_known_kind(run, known):
    """The ledger the journal recorded for THIS run, or None.

    Only a journal run answers. A still run that happens to contain a marked frame is NOT relabelled
    by it — see _journal_runs(): one mark cannot speak for a run of 217 frames.
    """
    if not (run or {}).get("journal"):
        return None
    kind = run.get("kind")
    if kind:
        return kind
    for n in (run.get("frames") or []):
        k = known.get(n)
        if k:
            return k
    return None


def _journal_runs(frames, known, covered_runs=None):
    """v1689 — the visits the STILLNESS test cannot see, taken from what somebody already read.

    Consecutive journal-marked frames become ONE run (the same shape still_runs() produces, plus
    `journal: True`), so `_distinct` still collapses a page photographed twice while a SCROLLED page
    stays several. A run breaks on an unmarked frame and on a change of ledger — welding a uniques
    page to a sets page would put set pieces in the wrong grail, which is the one mistake this
    module refuses to make anywhere.

    A mark gets its OWN run even when a still run already covers that frame, and this is the whole
    point: measured on his 217-frame reel, the stillness pass produced ONE run spanning the entire
    session, so lending that run the mark's ledger would have declared 217 frames of town and stash a
    Chronicle page. A mark speaks for its own frame and for nothing next to it. `covered_runs` is
    accepted and ignored so an older caller does not break.
    """
    if not known:
        return []
    runs, cur = [], None
    for fr in (frames or []):
        name = (fr or {}).get("f")
        if not name or fr.get("blank") or name not in known:
            cur = None
            continue
        kind = known.get(name)
        ts = fr.get("ts") or 0
        if cur is None or cur.get("kind") != kind:
            cur = {"frames": [name], "start_ts": ts, "end_ts": ts, "journal": True, "kind": kind}
            runs.append(cur)
        else:
            cur["frames"].append(name)
            cur["end_ts"] = ts or cur["end_ts"]
    return runs


def read_reel(reel_dir, classify, read_page, sig_of=None, min_frames=MIN_RUN_FRAMES,
              known_chronicle=None):
    """Sweep ONE sealed reel. Returns evidence — it writes nothing, anywhere.

    classify(frame_path) -> ("chronicle-uniques" | "chronicle-sets" | None)
        one call per candidate run, on the run's middle frame (the most settled one: the first frame
        of a run can still be mid-transition and the last can be mid-exit).
    read_page(frame_path, kind) -> the /api/intake chronicle response dict (v1510 shape).

    Returns {"reel": sid, "runs": n, "candidates": n, "classified": n, "pages": [ … ]}, where every
    page keeps the frame it came from. Provenance is not decoration here: when he asks "why does it
    think I have Windforce", the answer has to be a frame he can look at.
    """
    # v1607 — go through load_index(), never straight at index.json. A reel whose seal was killed
    # mid-write still has every frame; rebuilding the index from the names costs a listdir and turns
    # a black screen back into footage. "no-index" now means what it says: no frames either.
    # Tolerant by construction: rows carry no "blank" key on a rebuilt index (live_probe measures
    # for itself), and the extra "rebuilt"/"blankPass"/"blankPartial" keys the seal may stamp are
    # read through .get() like every other optional field here.
    idx = load_index(reel_dir)
    if not _index_ok(idx):
        return {"reel": os.path.basename(reel_dir), "runs": 0, "candidates": 0,
                "classified": 0, "pages": [], "note": "no-index"}
    sid = idx.get("sessionId") or os.path.basename(reel_dir)
    # v1603 — A CHRONICLE-FOCUSED MINI ALREADY KNOWS ITS LEDGER. Konyo: "for chronicles too.. should
    # have ... a button for it so its focused specifically for each grail chronicle individually and
    # relevant". When he presses 🏆 UNIQUES or 🧩 SETS the reel is stamped focus=chronicle-uniques /
    # chronicle-sets, which is the SAME thing sweep_frames() has skipped the classifier for since
    # v1527 on the live lane — "a recorded visit already knows two things a blind sweep has to pay a
    # model to discover: that these frames ARE the Chronicle, and WHICH ledger was open."
    #
    # This matters more here than on the vault side. chronicle_kind() deliberately returns None for
    # a Chronicle page whose TAB it cannot read, because guessing "uniques" would write set pieces
    # into his grail — so an unreadable tab currently costs the whole page. If he has already SAID
    # which ledger he opened, that failure mode disappears.
    declared_kind = _declared_kind(idx)
    # v1689 — WHAT THE JOURNAL ALREADY KNOWS. Passed in as data, never fetched: this module stays
    # pure (no sessions.jsonl, no console import), which is the only reason the laws above can be
    # tested against fixtures without a vision model.
    sig_of = sig_of or (lambda n: jpeg_sig(os.path.join(reel_dir, n)))
    idx_frames = idx.get("frames") or []
    known = _resolve_known(idx_frames, _known_chronicle_map(known_chronicle))
    # v1778 — THE COARSE TOLERANCE HERE IS DELIBERATE, and a code review flagging it is a false
    # positive worth recording so nobody "fixes" it twice. The two comparisons ask DIFFERENT
    # questions, exactly as _distinct's docstring says: still_runs asks "am I still on the same
    # SCREEN" (one classify per stretch of Chronicle), _distinct asks "is this a different PAGE"
    # (one read per scroll position). Blindness to page changes is what makes the first question
    # cheap to answer.
    #
    # MEASURED on his 08-17 reel before reverting an attempt to "fix" it:
    #     coarse tol=28 : 55 runs -> 55 classifies + 291 pages = 346 calls
    #     fine   tol=4  : 289 runs -> 289 classifies + 292 pages = 581 calls
    # Identical coverage, 68% more spend. The fine tolerance belongs in _distinct (v1771/v1775),
    # where it decides what to READ, and nowhere else.
    runs = still_runs(idx_frames, sig_of, max_diff=CHRON_STILL_MAX_DIFF)
    cands = candidate_runs(runs, min_frames=min_frames)
    # a scrolled Chronicle is never still, so the journal's own marks are candidates in their own
    # right — see _journal_runs() and the STILL_MAX_DIFF note.
    jruns = _journal_runs(idx_frames, known, cands)
    cands = cands + jruns
    pages, classified, blank_runs = [], 0, 0
    trusted = 0   # runs whose ledger came from HIS declared focus rather than a paid classify
    journal_trusted = 0   # runs whose ledger came from a read somebody already paid for
    read_seen = set()     # frames already read this reel — a page is never read (or witnessed) twice
    rescued = 0   # v1770 — short runs read because this reel PROVED it is a Chronicle recording
    rescued_probes = 0   # v1773 — runs saved by a second opinion after a bad probe
    refused_runs = []    # runs a probe rejected, kept in case this reel proves itself
    classify_proved = []  # a PAID classify said chronicle here — a journal mark is not that

    def _sweep_runs(run_list):
        nonlocal classified, blank_runs, trusted, journal_trusted, rescued_probes
        for run in run_list:
            fr = run["frames"]
            # v1543 — never pay to classify a photo of nothing. A blank capture cannot be a Chronicle,
            # and a run that is blank all the way through is a capture fault, not a screen he looked at.
            probe, _dead = live_probe(fr, lambda n: os.path.join(reel_dir, n))
            if probe is None:
                blank_runs += 1
                continue
            jkind = _run_known_kind(run, known)
            if jkind:
                kind = jkind                  # already read once; the answer does not expire
                journal_trusted += 1
            elif declared_kind:
                kind = declared_kind          # he told us; do not pay to rediscover it
                trusted += 1
            else:
                classified += 1
                kind = classify(os.path.join(reel_dir, probe))
                if kind in ("chronicle-uniques", "chronicle-sets"):
                    classify_proved.append(1)
                # ── v1773 — ONE UNLUCKY PROBE MUST NOT DISCARD A WHOLE RUN ──────────────────────
                # classify() runs ONCE per run, on its middle frame, and a "no" throws away every
                # frame behind it. Measured on his 08-17 reel with the real reader: a frame where
                # his cursor was resting on an item — so the game painted a large stat tooltip over
                # the list — came back scene='transition', conf 0.85, names 0. Two clean frames from
                # the same reel came back chronicle/uniques with 6 names each. The panel had not
                # gone anywhere; a popup had covered it, and the run behind that probe was up to 44
                # Chronicle pages thrown away on one frame's bad luck.
                #
                # v1577 fixed this shape when the probe THREW. A confident wrong answer is the same
                # defect wearing better clothes, and it costs more because nothing looks broken.
                #
                # So a refusal gets a second and third opinion from frames far away in the same run,
                # and only then is the run dropped. Bounded: at most two extra probes, and only for
                # runs that were about to be discarded entirely.
                if kind not in ("chronicle-uniques", "chronicle-sets") and len(fr) > 1:
                    refused_runs.append((run, probe))
            if kind not in ("chronicle-uniques", "chronicle-sets"):
                continue
            # The run IS the visit. Reading every frame of a held-still page buys nothing, but a SCROLLED
            # page is a different page — so read the distinct-looking frames, which for a held page is one.
            for name in _distinct(fr, sig_of, max_diff=CHRON_STILL_MAX_DIFF,
                              tol=CHRON_SIG_TOL):
                # v1689 — a frame is READ ONCE. A journal run and a still run can overlap, and the same
                # page read twice is not corroboration: it would arrive at witnesses() as two sightings
                # of one photograph and let a single frame pass a gate that asks for two.
                if name in read_seen:
                    continue
                read_seen.add(name)
                resp = read_page(os.path.join(reel_dir, name), kind) or {}
                pages.append({"reel": sid, "frame": name, "kind": kind, "resp": resp})
    _sweep_runs(cands)

    # ── v1770 — MIN_RUN_FRAMES=3 WAS THROWING AWAY MOST OF A SLOW SCROLL ────────────────────────
    # The floor exists so a sweep does not pay to classify somebody walking through town, and for
    # that job 3 frames is right. It is the wrong judge of a DELIBERATE scroll: Konyo went through
    # the Chronicle slowly, and each page still only held for a frame or two before he moved on.
    # Measured on his 08-17 reel: 339 frames group into 55 distinct screens, and min_frames=3 keeps
    # 24 of them. THIRTY-ONE SCREENS — 56% of what he filmed — were discarded before anything looked
    # at them, which at ~6 found rows per screen is roughly 180 item rows the sweep never read. That
    # is why his tally sat ~9 short of the game's 64% no matter how often he re-swept.
    #
    # _journal_runs already rescues short runs, and its comment names this exact defect ("a scrolled
    # Chronicle is never still"). But it can only rescue frames the JOURNAL marked, and the journal
    # had marked 13 — the fix was real and starved of input.
    #
    # THE DISCRIMINATOR IS THE REEL ITSELF. Once any run here has come back chronicle-*, the
    # walking-through-town rationale cannot apply to this reel: it is a recording of the Chronicle.
    # So the floor drops to 1 for the REST of that reel and nowhere else, which keeps the extra
    # spend on reels that have already proved they carry the pages he wants read.
    if pages and min_frames > 1:
        seen_runs = {id(r) for r in cands}
        # NEVER re-pay for a run the journal already answered. v1689 found this same defect from the
        # other side and rescues journal-marked frames for ZERO classifies; a run whose frames were
        # all read in the first pass is already covered, and classifying it again would spend money
        # to learn something known and hand witnesses() a second sighting of one photograph.
        short = [r for r in runs
                 if id(r) not in seen_runs
                 and (r.get("frames") or [])
                 and not all(f in read_seen for f in r["frames"])]
        if short:
            rescued = len(short)
            _sweep_runs(short)

    # ── v1773 — ONE UNLUCKY PROBE MUST NOT DISCARD A WHOLE RUN ──────────────────────────────────
    # classify() runs ONCE per run, on its middle frame, and a "no" throws away every frame behind
    # it. Measured on his 08-17 reel with the real reader: a frame where his cursor rested on an
    # item — so the game painted a large stat tooltip over the list — came back scene='transition',
    # conf 0.85, names 0, while two clean frames from the same reel came back chronicle/uniques with
    # 6 names each. The panel had not gone anywhere; a popup had covered it, and the run behind that
    # probe was up to 44 Chronicle pages discarded on one frame's bad luck.
    #
    # v1577 fixed this shape when the probe THREW. A confident wrong answer is the same defect in
    # better clothes, and it costs more because nothing looks broken.
    #
    # THE BILL IS WHY THIS RUNS LAST AND ONLY HERE. "ONE classify per run, not per frame" is a real
    # constraint with tests behind it, and a reel of gameplay must not become expensive to rule out.
    # So a second opinion is only ever sought once this reel has ALREADY produced a Chronicle page —
    # the same discriminator v1770 uses — and then at most twice per refused run, from frames as far
    # from the first probe as the run allows.
    # THE PROOF HAS TO COME FROM THE SAME JUDGE. `pages` can be non-empty purely because the journal
    # marked a frame months ago, and a journal mark says "this FRAME was a Chronicle", never "this
    # reel is a Chronicle recording" — v1689's weld test is exactly a session of town carrying one
    # mark. Spending two extra probes on that is how a mark quietly relabels a whole session.
    if classify_proved and refused_runs:
        for run, probe in refused_runs:
            fr = run["frames"]
            # a run the journal already answered is not refused, it is covered — re-probing it would
            # spend money to learn something known (the same exclusion v1770 needs)
            if all(f in read_seen for f in fr):
                continue
            for alt in _second_opinions(fr, probe):
                classified += 1
                kind = classify(os.path.join(reel_dir, alt))
                if kind in ("chronicle-uniques", "chronicle-sets"):
                    rescued_probes += 1
                    for name in _distinct(fr, sig_of):
                        if name in read_seen:
                            continue
                        read_seen.add(name)
                        pages.append({"reel": sid, "frame": name, "kind": kind,
                                      "resp": read_page(os.path.join(reel_dir, name), kind) or {}})
                    break


    return {"reel": sid, "runs": len(runs), "candidates": len(cands) + rescued,
            "classified": classified, "blankRuns": blank_runs, "pages": pages,
            "trustedFocus": trusted, "journalRuns": len(jruns),
            "journalTrusted": journal_trusted, "rescuedShortRuns": rescued,
            "rescuedProbes": rescued_probes}


def _distinct(names, sig_of, max_diff=0.06, tol=28):
    """Within one run, keep only frames that actually LOOK different from the last kept one — a
    scrolled list, not the same page re-photographed 40 times.

    v1771 — THE SAME DEFECT v1758 FIXED, ONE FUNCTION AWAY AND STILL LIVE. This compared with the
    DEFAULT tol=28, and v1758 measured what that does to a Chronicle: two COMPLETELY different pages
    differ by at most one gray level in one of jpeg_sig's 256 cells, so nothing clears 28 and
    sig_diff returns 0.00000. Every frame in a run therefore looked identical to the first, and this
    returned exactly ONE frame per run — measured on his 08-17 reel, runs of 43 and 44 distinct
    scroll positions each yielded a single page read. 128 frames across eight runs: 8 read, 106
    readable.

    THAT IS WHAT MADE THE SECOND EYE LOOK MANDATORY. `cross-frame` — two frames within one reel — is
    the witness Claude can supply alone, and it can never fire when a run is collapsed to one frame.
    So the only witnesses left needed a second LANE or a second RECORDING, and Konyo's optional extra
    pair of eyes had quietly become load-bearing: "why is grok a mandatory thing? we made it that i
    can toggle grok for extra pair of eyes... the default should be claude."

    v1772 REVERTED THIS, AND v1775 PUTS IT BACK, because the evidence behind the revert was false.
    The revert rested on the first real sweep afterwards returning 0 names where the previous code
    returned 22 — and REG-180 traced that to the reader being THROTTLED and answering scene=gameplay
    with no names rather than saying so. The same frames read chronicle/uniques with 6 names before
    the throttle and empty during it. The change was never measured against a working lane.

    THE ONE REAL OBJECTION IN THE REVERT NOTE STANDS AND IS ANSWERED. jpeg_sig fingerprints the WHOLE
    frame, so his item tooltip moves it as much as a scroll does and a 44-frame run selects ~38
    frames. That is not over-selection any more: v1774 taught the reader that a tooltip-covered panel
    is still scene=chronicle, so those frames are real pages carrying real rows, and reading the ones
    the popup leaves visible is the point. A cleaner LIST-REGION signature is still the better
    instrument and is measured in REG-180 — it selects ~240 pages against this one's ~291, so it is a
    refinement, not the difference between working and not.

    WHY IT MATTERS MORE THAN THE COST. With one frame per run there is no second frame, so
    `cross-frame` — the witness Claude supplies WITHOUT a second lane — can never fire, and Konyo's
    optional extra pair of eyes stays load-bearing: "why is grok a mandatory thing?" 

    The signal itself is bimodal exactly as v1758 found:
    measured over 219 consecutive pairs in his long scrolls, 39 are EXACTLY 0.00000 (a held page)
    and the smallest real page change is 0.00391, so CHRON_STILL_MAX_DIFF (0.002) sits mid-gap.
    [[feedback_threshold_above_the_ceiling]]"""
    out, last = [], None
    for n in names:
        s = sig_of(n)
        if s is None:
            continue
        if last is None or sig_diff(last, s, tol=tol) > max_diff:
            out.append(n)
            last = s
    return out


def _second_opinions(frames, probe, limit=2):
    """Frames to re-probe when the middle one said "not a Chronicle page".

    Spread as far from the first probe as the run allows: a tooltip, a fade or a cursor artefact is
    local in time, so the ends of the run are the least likely to share it. Bounded by `limit`
    because a run that really is not a Chronicle must not become expensive to rule out.
    """
    others = [f for f in frames if f != probe]
    if not others:
        return []
    if len(others) <= limit:
        return others
    return [others[0], others[-1]][:limit]


def chronicle_kind(read):
    """v1512 — a reader's answer → the intake kind to read that page with, or None.

    read: the dict tv_diablo.claude_read returns ({"scene": ..., "chronicleTab": ..., ...}).

    THE REFUSAL THAT MATTERS: scene=chronicle with an EMPTY tab returns None. It is tempting to guess
    uniques — it is the bigger ledger and the likelier screen — but a guess here does not cost a
    re-read, it writes set pieces into his grail. A Chronicle page the reader could not identify is
    a page we do not read, and the sweep says so rather than picking a side.
    """
    if not isinstance(read, dict):
        return None
    if str(read.get("scene") or "").lower() != "chronicle":
        return None
    tab = str(read.get("chronicleTab") or "").lower()
    if tab == "uniques":
        return "chronicle-uniques"
    if tab == "sets":
        return "chronicle-sets"
    return None


def classifier(claude_read, on_seen=None):
    """Wrap a reader into the `classify` callable read_reel() wants.

    on_seen(path, read) — optional observer, so a caller can journal EVERY probe including the ones
    that came back "not a chronicle". A sweep that only reports its hits looks like it found
    everything there was; "11 runs probed, 2 were Chronicle" is the honest shape.
    """
    def _classify(path):
        try:
            read = claude_read(path)
        except Exception:
            return None
        if on_seen:
            try:
                on_seen(path, read)
            except Exception:
                pass
        return chronicle_kind(read)
    return _classify


# v1819 — what the game's own `First Found:` stamp looks like: 08/20/2026, 00:49
#
# This is a REFUSAL, not a formatter. The UNIQUES and SETS tabs print `First Found:` and
# `Dropped By:` in opposite orders, so the likeliest reader error by far is a row whose date slot
# holds a monster name. A stamp that is not a date is dropped here rather than carried into the
# ledger: a wrong find-date would survive every later correction, because nothing downstream ever
# re-reads a date it already has.
_STAMP_RX = re.compile(r"^\s*\d{1,2}/\d{1,2}/\d{4}\s*,?\s*\d{1,2}:\d{2}(:\d{2})?\s*$")


def stamp_ok(v):
    """True when v is the game's own First Found stamp, not a monster and not a guess."""
    return bool(_STAMP_RX.match(str(v or "")))



def stamp_key(v):
    """A First Found stamp as a sortable tuple, or None when it is not a stamp.

    v1846 — Konyo: "maybe try to code and focus the AI readers to understand this logic too as an
    addition to the cross reference maybe date and timestamp related coding so they know what they
    registered yesterday and whats new today".

    The stamps have been captured since v1819 and nothing has ever COMPARED two of them. They are
    read as text, stored as text, and printed as text — so the ledger knows every find-date and
    cannot answer "which of these is new". This is the missing arithmetic, and it is deliberately
    the smallest possible piece of it: parse, or say None. `stamp_ok` already decides what counts as
    a stamp; this only orders the ones it accepts.

    Sorts correctly across months and years because the tuple is (year, month, day, hh, mm) rather
    than the printed MM/DD/YYYY, which sorts alphabetically into nonsense.
    """
    if not stamp_ok(v):
        return None
    try:
        date, clock = str(v).split(",", 1)
        m, d, y = [int(x) for x in date.strip().split("/")]
        parts = [int(x) for x in clock.strip().split(":")]
        hh, mm = parts[0], parts[1]
        return (y, m, d, hh, mm)
    except Exception:
        return None


def newest_stamp(prop):
    """The newest First Found stamp anywhere in a proposal or ledger, or None if it holds none.

    None is not a date and must never compare as one — a ledger with no stamps has no newest, and
    saying so is different from saying "the beginning of time". [[unknown-stays-unknown]]
    """
    best = None
    for ledger in ("uniques", "sets"):
        for sightings in ((prop or {}).get(ledger) or {}).values():
            for sg in (sightings or []):
                k = stamp_key((sg or {}).get("foundAt"))
                if k and (best is None or k > best):
                    best = k
    return best


def newly_dated(prop, since):
    """Names in `prop` whose find-date is NEWER than `since` — what he found since the last sweep.

    v1846 — the answer to "what did I register yesterday and what is new today", computed rather
    than guessed. `since` is a stamp_key tuple or None; with None NOTHING is reported as new, because
    a ledger that has never held a stamp cannot tell new from old and must not pretend to. Returns
    {name: stamp} sorted newest first.
    """
    out = []
    for ledger in ("uniques", "sets"):
        for name, sightings in ((prop or {}).get(ledger) or {}).items():
            best = None
            for sg in (sightings or []):
                k = stamp_key((sg or {}).get("foundAt"))
                # compare the KEY against the stored key, not against the (key, raw) pair — the
                # first cut compared a 5-tuple with a 2-tuple and raised on his real ledger
                if k and (best is None or k > best[0]):
                    best = (k, (sg or {}).get("foundAt"))
            if best and since is not None and best[0] > since:
                out.append((best[0], name, best[1]))
    out.sort(reverse=True)
    return [{"name": n, "foundAt": raw} for _k, n, raw in out]


def _stamp_map(raw_map, want_stamp):
    """name -> value, keeping only entries on the right side of the date/monster line."""
    out = {}
    if not isinstance(raw_map, dict):
        return out
    for k, v in list(raw_map.items())[:80]:
        k = str(k or "").strip()[:64]
        v = str(v or "").strip()[:48]
        if not k or not v:
            continue
        if stamp_ok(v) == want_stamp:
            out[k] = v
    return out


def normalize_page(raw, kind, lane, framing=None):
    """v1519 — ONE normalizer, both lanes. Turns a reader's raw JSON into the v1510 response shape.

    This exists because the two lanes were each about to normalize their own answer, and the moment
    they do, "witness: agree" starts meaning two different things depending on who said it — which is
    exactly the drift REG-076 was about. Cross-lane agreement is only evidence if both lanes are
    answering in the same units.

    Returns None for a raw that is not a dict — a refusal, never an empty page (see the lane note in
    two_lane_read: "didn't run" and "saw nothing" must stay different facts).
    """
    if not isinstance(raw, dict):
        return None
    ledger = "sets" if str(kind or "").endswith("sets") else "uniques"

    def names(v, cap=400):
        return [str(x).strip() for x in (v or []) if str(x).strip()][:cap]

    def num(v):
        try:
            n = int(v)
        except Exception:
            return None
        return n if 0 <= n <= 9999 else None

    try:
        conf = max(0.0, min(1.0, float(raw.get("conf") or 0)))
    except Exception:
        conf = 0.0
    state_visible = raw.get("stateVisible") is not False
    wrong_tab = raw.get("wrongTab") is True
    not_chronicle = raw.get("notChronicle") is True
    found = [] if (not_chronicle or wrong_tab or not state_visible) else names(raw.get("found"))
    not_found = names(raw.get("notFound"))
    # v1570 — CARRY `complete`. This rebuilt every set row as {set, pieces} and dropped the flag,
    # while proposal_from_pages reads g.get("complete") off THIS normalised dict — so completeSets
    # could never populate through the normalised path no matter what the reader emitted. The
    # v1566 prompt work fed a funnel that threw the answer away one function later.
    sets = [{"set": str(g.get("set") or "")[:60], "pieces": names(g.get("pieces"), 20),
             "complete": g.get("complete") is True}
            for g in (raw.get("sets") or []) if isinstance(g, dict) and g.get("set")]
    printed = {"found": num(raw.get("printedFound")), "total": num(raw.get("printedTotal"))}
    # THE PARTIAL-PAGE TRAP, closed identically for both lanes: the panel scrolls, so its printed
    # total counts the whole ledger while the page shows a slice. Agreement on a partial page is a
    # coincidence, not corroboration.
    whole = printed["total"] is not None and (len(found) + len(not_found)) == printed["total"]
    witness = ("none" if (printed["found"] is None or not whole)
               else ("agree" if printed["found"] == len(found) else "differ"))
    return {
        "kind": kind, "ledger": ledger, "lane": lane,
        # v1901 — WHICH PIXELS THIS WITNESS ACTUALLY SAW. Cross-lane agreement is evidence only if
        # both lanes read the same rectangle, and for eleven versions they did not: the Claude lane
        # cropped to the list band and the Grok lane was handed the whole desktop grab, with nothing
        # anywhere recording the difference. Both lanes crop now — and a disagreement carries the
        # framing that produced it, so the next one is attributable instead of mysterious.
        # None means the lane did not say, which is not the same as "full". [[unknown-stays-unknown]]
        "framing": (str(framing) if framing else None),
        "found": found, "notFound": not_found, "sets": sets if ledger == "sets" else [],
        "stateVisible": state_visible, "wrongTab": wrong_tab, "wholePage": whole,
        "witness": witness, "conf": conf, "printed": printed,
        # v1819 — the page's own dates. `sort` is copied as printed rather than normalised here so
        # the raw wording survives into the evidence; callers decide what "newest" means.
        #
        # ⚠ v1907 — ONLY THE LIVE LANE SUPPLIES THIS, and an empty string here means NOT ASKED, not
        # "the panel had no sort control". Neither retro prompt (CHRONICLE_READ_PROMPT,
        # CHRONICLE_VISION_PROMPT) mentions `sort` at all — deliberately, because v1828 settled that
        # the printed `First Found:` stamps decide order, never a label. So a retro page's blank
        # `sort` is an absence of a question, and a live page's blank one is an absence of an
        # answer. Do not read the two as the same fact. [[unknown-stays-unknown]]
        "sort": str(raw.get("sort") or "").strip()[:32],
        "foundAt": _stamp_map(raw.get("foundAt"), True),
        "droppedBy": _stamp_map(raw.get("droppedBy"), False),
        "read": {"found": len(found), "notFound": len(not_found)},
        # v1839 — THREE REFUSALS, THREE NAMES. "not-a-chronicle-page" is the console window or
        # gameplay and is a HEALTHY refusal on a screen recording; "no-found-state" is a Chronicle
        # page whose rows could not be judged and is a LOST one. They were the same word, so the
        # refusal count could be read as neither.
        "note": ("not-a-chronicle-page" if not_chronicle
                 else "wrong-ledger" if wrong_tab
                 else ("no-found-state" if not state_visible else None)),
    }


def two_lane_read(path, kind, claude_lane, grok_lane=None):
    """v1514 — TWO LANES ON THE SAME PAGE. Konyo: "we have both claude which is the most important..
    but grok for me specifically i can use as a second pair of eyes and a different view for also
    these exact things! it must be also coded in so it is identically trying to read and retro
    chronicle these tallied in."

    Claude is PRIMARY: if Claude does not answer, there is no page. Grok is a genuinely independent
    second eye — different model, different prompt path, different failure modes — which is what
    makes cross-lane the strongest witness the gate can be given.

    THE RULE THAT MATTERS: the two lanes are NOT max()'d together. A name only one lane saw is kept,
    but it is kept AS a one-lane sighting, so the gate still demands a second kind of witness before
    it grounds. And where the lanes disagree, the disagreement is REPORTED — surfacing it is the
    whole value of having a second eye. Silently taking the bigger number would throw that away and
    leave a system that looks corroborated while being exactly as wrong as its most confident lane.
    """
    primary = claude_lane(path, kind) or {}
    if primary.get("note") or not primary.get("ledger"):
        return dict(primary, lanes={}, lanesRan=["claude"])   # refused or empty — no second opinion needed
    lanes = {nm: ["claude"] for nm in (primary.get("found") or [])}
    ran = ["claude"]
    second = None
    if grok_lane is not None:
        try:
            second = grok_lane(path, kind)
        except Exception:
            second = None
    if not second or second.get("note"):
        # An absent second eye is stated, never implied. "grok didn't run" and "grok agreed" are
        # different facts and the gate must not confuse them.
        return dict(primary, lanes=lanes, lanesRan=ran,
                    laneNote=(second or {}).get("note") or "grok-silent")
    ran.append("grok")
    for nm in (second.get("found") or []):
        lanes.setdefault(nm, []).append("grok")
    both = sorted(n for n, ls in lanes.items() if len(ls) > 1)
    only_c = sorted(n for n, ls in lanes.items() if ls == ["claude"])
    only_g = sorted(n for n, ls in lanes.items() if ls == ["grok"])
    return dict(
        primary,
        found=sorted(lanes),                 # union — the gate, not the reader, decides what grounds
        lanes=lanes,
        lanesRan=ran,
        laneAgreement={"both": both, "claudeOnly": only_c, "grokOnly": only_g},
        # the honest headline: two eyes that agree on 40 of 43 is a much better story than "43 found"
        laneSummary="%d agreed · %d claude-only · %d grok-only" % (len(both), len(only_c), len(only_g)),
    )


def two_lane_reader(claude_lane, grok_lane=None):
    """Bind the two lanes into the `read_page` callable read_reel() wants."""
    def _read(path, kind):
        return two_lane_read(path, kind, claude_lane, grok_lane)
    return _read


_PIECE_BARE = None


def _is_piece_not_set(name):
    """True when `name` is a set PIECE, so it can never be the set itself.

    Compared on the BARE name because the readers print "M'avina's Tenet" while the roster stores
    "M'avina's Tenet (belt)" — the same two-conventions gap that made an earlier guard pass cleanly
    on 86 names none of which could ever have matched. THE COUNT IS THE TELL, so this one was
    measured before it was believed: 5 of his 38 real groups are pieces.
    """
    global _PIECE_BARE
    if _PIECE_BARE is None:
        try:
            import re as _re
            import chronicle_resolve as _res
            _PIECE_BARE = {
                _re.sub(r"\s*\([^)]*\)\s*$", "", v).strip().lower()
                for v in (_res.load_set_roster() or {}).values()
            }
        except Exception:
            _PIECE_BARE = set()
    if not _PIECE_BARE:
        return False          # no roster -> refuse to judge, never refuse the data
    # ⚠ STRIP THE SUFFIX FROM THE INPUT TOO. The first cut stripped it from the ROSTER and compared
    # the raw input, so it caught "M'avina's Tenet" and missed "M'avina's Tenet (belt)" — the very
    # two-conventions gap this guard is a reaction to, inside the guard. Caught by its own test.
    import re as _re
    n = _re.sub(r"\s*\([^)]*\)\s*$", "", " ".join(str(name or "").split())).strip().lower()
    return n in _PIECE_BARE


def proposal_from_pages(pages):
    """Fold read pages into ONE proposal per ledger, keeping every name's evidence.

    A name seen on several frames collects several witnesses — that is the multi-witness signal the
    gate consumes, so the sightings are kept rather than deduped away. Pages the reader REFUSED
    (no-found-state / wrong-ledger, v1510) contribute nothing but are counted, because "8 pages read,
    3 refused" is the honest headline and "5 pages read" is not.
    """
    # v1836 — `pageKeys` is WHICH pages were read, not how many. A scalar cannot survive an
    # idempotent merge: v1835 banks evidence every 20 pages and the final merge re-offers pages
    # already banked, so `pagesRead += pagesRead` counted a long sweep roughly twice. The names were
    # always safe (a sighting is keyed by reel/frame/lane and folds), and only the COUNTERS lied —
    # which is worse than it sounds, because the counters are the headline he reads.
    prop = {"uniques": {}, "sets": {}, "setGroups": {}, "completeSets": {}, "refused": [],
            "pagesRead": 0, "pageKeys": [], "notFound": {"uniques": set(), "sets": set()}}
    _pk = set()
    for p in (pages or []):
        resp = p.get("resp") or {}
        ledger = resp.get("ledger") or ("sets" if p.get("kind") == "chronicle-sets" else "uniques")
        if resp.get("note"):
            prop["refused"].append({"reel": p.get("reel"), "frame": p.get("frame"),
                                    "why": resp.get("note")})
            continue
        prop["pagesRead"] += 1
        _pk.add("%s|%s" % (p.get("reel"), p.get("frame")))
        # v1514 — ONE SIGHTING PER LANE. Two eyes that agree must reach the gate as TWO witnesses;
        # folding them into one row would silently discard the strongest signal in the system.
        lane_map = resp.get("lanes") or {}
        for nm in (resp.get("found") or []):
            for lane in (lane_map.get(nm) or [resp.get("lane") or "claude"]):
                # v1819 — a sighting now carries the row's OWN stamp when the page printed one.
                # Two lanes agreeing on a name is corroboration; two lanes agreeing on a name AND
                # the same find-date is strictly stronger, and it is the only thing that can tell a
                # find made today from one that was simply never read before.
                _sight = {
                    "reel": p.get("reel"), "frame": p.get("frame"),
                    "witness": resp.get("witness") or "none",
                    "conf": resp.get("conf") or 0,
                    "lane": lane,
                }
                _fa = (resp.get("foundAt") or {}).get(nm)
                if _fa:
                    _sight["foundAt"] = _fa
                _db = (resp.get("droppedBy") or {}).get(nm)
                if _db:
                    _sight["droppedBy"] = _db
                if resp.get("sort"):
                    _sight["sort"] = resp["sort"]
                prop[ledger].setdefault(nm, []).append(_sight)
        for nm in (resp.get("notFound") or []):
            prop["notFound"][ledger].add(nm)
            # ── v1921 — A NOT-FOUND READING NEEDS A PAGE AND A LANE, OR IT CANNOT BE JUDGED ──────
            #
            # `notFound` has been a bare set of NAMES since it was written: no reel, no frame, no
            # lane, no moment. So when the same piece is read FOUND on one page and NOT FOUND on
            # another — which happens constantly, because he keeps finding things — nothing could
            # say which reading is newer, or even which photographs disagreed.
            #
            # It cost a wrong answer to him directly. Told that 12 of his 36 proposed set pieces
            # were ones "the game says you do not have", the truth was that three of them
            # (Natalya's Totem, Hsarus' Iron Fist, Hsarus' Iron Heel) carry First Found dates on
            # his newest reel — the not-found readings were simply OLD. A claim built on evidence
            # that cannot be dated is a claim that cannot be checked.
            #
            # The set stays exactly as it was, so every existing reader and gate is untouched. What
            # is added is the RECEIPT beside it. Resolving by recency needs a timestamp on the
            # sighting, which these do not carry yet — so this ship makes the contradiction VISIBLE
            # and says plainly that it does not yet make it RESOLVABLE. [[unknown-stays-unknown]]
            prop.setdefault("notFoundSeen", {}).setdefault(ledger, {}).setdefault(nm, []).append({
                "reel": p.get("reel"), "frame": p.get("frame"),
                "lane": resp.get("lane") or "claude",
            })
        for g in (resp.get("sets") or []):
            nm = g.get("set")
            if not nm:
                continue
            # ── v1932 — A PIECE IS NOT A SET, AND SAYING SO COSTS ONE LOOKUP ────────────────────
            # Measured on his banked evidence: 5 of 38 setGroups keys are PIECE names, not set
            # names — "M'avina's True Sight" (a helm) keyed as a set carrying M'avina's Icy Clutch
            # and M'avina's Tenet; "Cleglaw's Claw" (a shield) carrying Cleglaw's Pincers and Tooth.
            # The reader grouped rows under a row instead of under the heading.
            #
            # setGroups alone is harmless — no UI reads it. `completeSets` is the one that bites: a
            # set the panel calls complete is ONE ROW WORTH FIVE PIECES, expanded by the board. A
            # piece accepted as a set there would tick pieces he does not own, from a single misread
            # heading. It has not happened yet (completeSets is empty on his evidence), which is
            # exactly when a guard is cheap.
            #
            # Refused OUT LOUD, never dropped: a silently discarded group is indistinguishable from
            # a page that held none. [[unknown-stays-unknown]] [[source-reading-guard]]
            if _is_piece_not_set(nm):
                prop.setdefault("refusedGroups", []).append({
                    "set": nm, "reel": p.get("reel"), "frame": p.get("frame"),
                    "why": "this is a set PIECE, not a set — a piece cannot be complete",
                })
                continue
            prop["setGroups"].setdefault(nm, set()).update(g.get("pieces") or [])
            # v1530 — A SET THE PANEL CALLS COMPLETE. The Chronicle often shows a set as done without
            # listing its pieces legibly, and the game saying "complete" IS the claim — one row worth
            # five. It is collected with sightings like any other name, so the gate judges it by the
            # same rule and the board (which owns the piece list) does the expanding.
            if g.get("complete") is True:
                for lane in (lane_map.get(nm) or [resp.get("lane") or "claude"]):
                    prop["completeSets"].setdefault(nm, []).append({
                        "reel": p.get("reel"), "frame": p.get("frame"),
                        "witness": resp.get("witness") or "none",
                        "conf": resp.get("conf") or 0, "lane": lane,
                    })
    prop["notFound"] = {k: sorted(v) for k, v in prop["notFound"].items()}
    # v1921 — THE CONTRADICTION, NAMED. A piece read FOUND on one page and NOT FOUND on another is
    # not noise to be averaged away: it is the most informative row in the proposal, and until now
    # nothing computed it at all. It is reported, never acted on — an older not-found reading is a
    # perfectly ordinary thing when he has since found the item.
    # v1923 — AND RESOLVED BY TIME, because a flat membership test is what produced a wrong answer
    # to his face. I told him 12 of his 36 proposed set pieces were ones the game shows as
    # not-found. Three carried First Found dates on his newest reel: those not-found readings were
    # simply OLD, describing a moment before he owned the item. The real number was one.
    #
    # A not-found reading is not a fact about the item — it is a fact about the item AT ONE MOMENT,
    # and it expires the instant a later look disagrees. The comment above already said so and the
    # code compared two sets as flat membership anyway, which is the same as not knowing it.
    # v1921 put the receipts in `notFoundSeen`; this is the consumer that makes them mean something.
    contested = {}
    resolved = {}
    for _led in ("uniques", "sets"):
        _nf = set(prop.get("notFound", {}).get(_led) or ())
        _seen = (prop.get("notFoundSeen") or {}).get(_led) or {}
        for _nm in (prop.get(_led) or {}):
            if _nm not in _nf and _nm not in _seen:
                continue
            try:
                import counter_ledger as _clg
                _r = _clg.resolve_contested(prop[_led].get(_nm) or [], _seen.get(_nm) or [])
            except Exception:
                _r = {"verdict": "undatable", "say": "the resolver could not be consulted"}
            resolved.setdefault(_led, {})[_nm] = _r
            # A name whose NEWEST look says found is not contested — it is settled, and listing it
            # would rebuild the very padding that produced the wrong claim.
            if _r.get("verdict") != "found":
                contested.setdefault(_led, []).append(_nm)
    prop["contested"] = {k: sorted(v) for k, v in contested.items()}
    prop["contestedResolved"] = resolved
    # ⚠ AND SAY WHEN THE NOT-FOUND SIDE CANNOT BE DATED AT ALL. Receipts for not-found readings
    # (`notFoundSeen`) arrived in v1921; every proposal banked before that carries a flat list of
    # NAMES with no reel, no frame and no time. Such a reading cannot contradict anything, and the
    # danger is that it looks exactly like one that can — which is how "12 of your 36" got said out
    # loud about a set of readings not one of which could be ordered.
    #
    # So the proposal states its own evidential reach. A consumer that wants to call something
    # contested has to look at this first. [[unknown-stays-unknown]]
    _nf_total = sum(len(prop.get("notFound", {}).get(l) or ()) for l in ("uniques", "sets"))
    _nf_withreceipts = sum(len((prop.get("notFoundSeen") or {}).get(l) or {})
                           for l in ("uniques", "sets"))
    prop["notFoundDatable"] = {
        "readings": _nf_total, "withReceipts": _nf_withreceipts,
        "ok": (_nf_total == 0 or _nf_withreceipts >= _nf_total),
        "say": ("every not-found reading carries a receipt and can be ordered against the found "
                "ones" if (_nf_total == 0 or _nf_withreceipts >= _nf_total) else
                "%d of %d not-found reading(s) carry NO reel or frame, so they cannot be ordered "
                "against anything and must not be quoted as contradicting a find. They were banked "
                "before receipts existed; the next sweep records them and they become usable."
                % (_nf_total - _nf_withreceipts, _nf_total))}
    prop["contestedExpired"] = {
        led: sorted(n for n, r in (resolved.get(led) or {}).items() if r.get("verdict") == "found")
        for led in ("uniques", "sets")
        if any(r.get("verdict") == "found" for r in (resolved.get(led) or {}).values())}
    prop["setGroups"] = {k: sorted(v) for k, v in prop["setGroups"].items()}
    prop["pageKeys"] = sorted(_pk)
    return prop


# ── v1513 THE GATE ──────────────────────────────────────────────────────────────
# Konyo's multi-witness doctrine: require 2+ INDEPENDENT agreeing signals before grounding. The word
# doing the work is *independent*. Reading the same frame twice is not two witnesses; nor is one
# reader confident twice. Four kinds of independence exist in this evidence, and they are ranked by
# how hard they are to fake:
#
#   cross-lane   two DIFFERENT readers (Claude, Grok) read the same name — strongest, because the
#                lanes share no prompt, no model and no failure mode (v1514 supplies the second lane)
#   cross-reel   the same name on two different SESSIONS — he opened the Chronicle twice, months
#                apart maybe, and it said the same thing
#   cross-frame  two different frames of one visit — catches a one-frame OCR slip
#   printed      the panel's own progress numbers agreed with our count on that page (v1510)
#
# A name needs TWO. Not two sightings — two kinds, or two of a kind that is genuinely repeatable
# (frames, reels, lanes are; `printed` is a property of a page, so it counts once).
CONF_FLOOR = 0.55        # below this the reader itself was unsure; unsure twice is still unsure
MIN_WITNESSES = 2



def live_pages(rows, ledger_of=None, lane="live"):
    """v1833 — THE FIRST EYES. Konyo: "we had a AI reader for live too just its probably not gonna
    catch it... but if it does why not? make it an extra layer of accuracy its the first eyes".

    While he plays, the live agent reads whatever is on screen. When that is the Chronicle it
    already separates the rows it can SEE from the rows it can see are FOUND — `discovered_names`,
    chronicle-only by design since v763. Measured on his journal: 13 chronicle rows, 10 of them
    carrying discoveries, at conf 0.75, from two sessions. Every one of those was thrown away for
    tally purposes. v1695 wired the live lane's FRAME IDENTITY into the sweep and stopped there;
    the names it had already paid for kept going nowhere. [[plumbing-with-no-tap]]

    THE INDEPENDENCE IS REAL, AND SO IS ITS LIMIT. A live sighting is keyed by its `sessionId`,
    which _reel_key() normalises to exactly the key the retro pages of that same session land under.
    So a live sighting and a retro read of the same footage score `cross-lane` — a genuinely
    different reader, different prompt, different moment — and NOT `cross-reel`, which would be the
    same session's evidence counted twice. witnesses() needed no change for this: it counts distinct
    lanes generically. The two-witness gate still stands, so a live-only name never grounds alone.

    THE LEDGER IS DERIVED, NEVER GUESSED. His live rows carry `chronicleTab: null` — the live prompt
    does not always resolve the tab — and guessing costs more than a re-read: it writes set pieces
    into his unique grail, which is the exact catastrophe chronicle_kind() refuses to risk. So the
    tab is used when present, and otherwise the NAMES decide, against his own generated rosters:
    every resolvable name must agree on one ledger, and a row that is mixed or wholly unresolvable
    is DROPPED. Same move as v1828 preferring the printed `First Found:` stamps over reading a sort
    control — derive it from the data, do not read it off a label.

    Pure: no disk, no journal, no vision. `ledger_of(name) -> "uniques" | "sets" | None` is supplied
    by the caller, which is what keeps this testable against fixtures.
    """
    out = []
    for row in (rows or []):
        if not isinstance(row, dict):
            continue
        if str(row.get("scene") or "").lower() != "chronicle":
            continue
        names = [str(n).strip() for n in (row.get("discovered_names") or row.get("discovered") or [])
                 if str(n).strip()]
        if not names:
            continue
        tab = str(row.get("chronicleTab") or "").strip().lower()
        kind = {"uniques": "chronicle-uniques", "sets": "chronicle-sets"}.get(tab)
        if kind is None and ledger_of is not None:
            seen = set()
            for n in names:
                try:
                    led = ledger_of(n)
                except Exception:
                    led = None
                if led:
                    seen.add(str(led))
            # unanimity or nothing — a mixed page tells us the reader was not on one ledger, and a
            # page nothing resolves tells us only that we cannot say.
            if len(seen) == 1:
                kind = {"uniques": "chronicle-uniques", "sets": "chronicle-sets"}.get(seen.pop())
        if kind not in ("chronicle-uniques", "chronicle-sets"):
            continue
        try:
            conf = max(0.0, min(1.0, float(row.get("conf") or 0)))
        except Exception:
            conf = 0.0
        raw = {"ledger": "sets" if kind.endswith("sets") else "uniques",
               "found": names, "notFound": [], "sets": [],
               # v1907 — JOIN THE WIRE. The live prompt has asked for `chronicleSort` since v1818
               # ("the sort control at the TOP RIGHT of the panel, read literally"), tv_diablo
               # writes the answer into every chronicle row, and this converter built its page
               # WITHOUT it while normalize_page reads `sort` and proposal_from_pages copies it
               # onto every sighting. Two halves each built right, never joined: the field was
               # empty on every page ever produced. [[plumbing-with-no-tap]]
               "sort": row.get("chronicleSort") or row.get("chronicle_sort") or "",
               "stateVisible": True, "wrongTab": False, "conf": conf}
        resp = normalize_page(raw, kind, lane)
        if not resp:
            continue
        reel = row.get("sessionId") or row.get("session") or row.get("reel") or "live"
        frame = row.get("frameId") or row.get("frame") or ("live_%s" % (row.get("ts") or ""))
        out.append({"reel": str(reel), "frame": str(frame), "kind": kind, "resp": resp})
    return out


def merge_proposals(base, incoming):
    """Fold `incoming` into `base` and return a NEW proposal. Evidence only ever ACCUMULATES.

    v1776 — WHY THIS EXISTS. The console kept one result slot, so every sweep REPLACED the last
    one's findings. Konyo watched it happen twice in an hour: "the progress is going up and then
    reversing". Two costs, and the second is the expensive one:

      1. what a sweep found was gone the moment anything else swept — including the watchdog's own
         tick, which is supposed to be helping;
      2. sightings could only corroborate each other INSIDE one run, so `cross-reel` — a name seen
         in two different recordings — could only ever fire if both reels happened to be in the same
         sweep. Read reel A today and reel B tomorrow and the gate sees two lonely single sightings.
         That is most of why nothing could ground without Grok.

    A sighting is identified by (reel, frame, lane): the same photograph read twice is ONE sighting,
    because two reads of one frame is not corroboration (v1689). Anything genuinely new is added.
    The vault path has done exactly this since v1533 — "ACCUMULATE ACROSS SESSIONS, merge-max only";
    the chronicle path never got it.
    """
    out = {"uniques": {}, "sets": {}, "setGroups": {}, "completeSets": {}, "refused": [],
           "pagesRead": 0, "pagesRefused": 0, "notFound": {"uniques": set(), "sets": set()}}
    _seen_ref = set()
    _keys = set()
    for src in (base or {}, incoming or {}):
        if not isinstance(src, dict):
            continue
        for ledger in ("uniques", "sets"):
            for name, sightings in (src.get(ledger) or {}).items():
                bucket = out[ledger].setdefault(name, [])
                seen = {(x.get("reel"), x.get("frame"), x.get("lane")) for x in bucket}
                for sg in (sightings or []):
                    key = (sg.get("reel"), sg.get("frame"), sg.get("lane"))
                    if key in seen:
                        continue
                    seen.add(key)
                    bucket.append(sg)
        # v1798 — AND THE SAME RULE FOR THE SET KEYS, which v1776 left on `.update`.
        #
        # `dict.update` REPLACES the value, so the second proposal's evidence overwrote the first's:
        # a complete-set claim seen in reel A on Monday and reel B on Tuesday came out holding only
        # reel B's sighting, `witnesses()` returned [] instead of ['cross-reel'], and apply_proposal
        # gates that claim by the same MIN_WITNESSES = 2 rule — so a set worth FIVE pieces could never
        # ground on cross-reel evidence, forever. Exactly the defect v1776 was written to kill, in the
        # two keys the loop above did not cover. Found by a code review; reproduced before fixing.
        #
        # completeSets holds SIGHTINGS, so it de-dupes by (reel, frame, lane) like a name does.
        # setGroups holds a set of PIECE NAMES seen under one set heading — a union, because a
        # half-scrolled page showing three of five pieces must never delete the other two.
        for name, sightings in (src.get("completeSets") or {}).items():
            bucket = out["completeSets"].setdefault(name, [])
            seen = {(x.get("reel"), x.get("frame"), x.get("lane")) for x in bucket}
            for sg in (sightings or []):
                key = (sg.get("reel"), sg.get("frame"), sg.get("lane"))
                if key in seen:
                    continue
                seen.add(key)
                bucket.append(sg)
        for name, pieces in (src.get("setGroups") or {}).items():
            out["setGroups"].setdefault(name, set()).update(set(pieces or ()))
        # notFound was dropped entirely by the old merge, so "the game says he has NOT found this"
        # survived one sweep and then vanished — an absence that cannot be carried is an absence
        # nobody can act on.
        # v1921 — carry the RECEIPTS across a merge too, or the page a not-found reading came from
        # survives exactly one sweep. merge_proposals is what makes evidence accumulate; a field it
        # does not know about is a field that quietly resets.
        for _led, _names in (src.get("notFoundSeen") or {}).items():
            for _nm, _seen in (_names or {}).items():
                _bucket = out.setdefault("notFoundSeen", {}).setdefault(_led, {}).setdefault(_nm, [])
                _have = {(x.get("reel"), x.get("frame"), x.get("lane")) for x in _bucket}
                for _s in (_seen or []):
                    _k = (_s.get("reel"), _s.get("frame"), _s.get("lane"))
                    if _k not in _have:
                        _have.add(_k)
                        _bucket.append(_s)
        nf = src.get("notFound") or {}
        if isinstance(nf, dict):
            for ledger, names in nf.items():
                out.setdefault("notFound", {}).setdefault(ledger, set()).update(set(names or ()))
        # v1836 — REFUSALS DEDUPE TOO. This was a bare extend, so a frame refused on Monday and
        # refused again on Tuesday appeared twice, and v1835's checkpointing multiplied that by the
        # number of banks in a run. I misread this list myself tonight — counted a cumulative list
        # as one pass's and briefly called a working fix a failure.
        for r in (src.get("refused") or []):
            if not isinstance(r, dict):
                continue
            key = (r.get("reel"), r.get("frame"), r.get("why"))
            if key in _seen_ref:
                continue
            _seen_ref.add(key)
            out["refused"].append(r)
        # WHICH pages, then how many. A source written before v1836 has no pageKeys, so they are
        # reconstructed from the (reel, frame) its own sightings and refusals already carry — exact
        # for every page that yielded a name or a refusal, which is every page that left a trace.
        keys = src.get("pageKeys")
        if keys is None:
            keys = set()
            for ledger in ("uniques", "sets", "completeSets"):
                for sightings in (src.get(ledger) or {}).values():
                    for sg in (sightings or []):
                        if isinstance(sg, dict) and sg.get("frame"):
                            keys.add("%s|%s" % (sg.get("reel"), sg.get("frame")))
        _keys.update(str(k) for k in (keys or ()))
    # v1799 — RETURN WHAT THE PRODUCER RETURNS. Sets are the right type to accumulate WITH and the
    # wrong type to hand back: this dict is json.dump-ed straight to chron_evidence.json, and
    # `json.dumps` refuses a set — it failed on an EMPTY merge. `_chron_evidence_save` wraps its dump
    # in a bare `except Exception: return False` that nobody checks, so the ledger simply stopped
    # being written and said nothing. v1798's fix for "evidence must ACCUMULATE" broke "evidence gets
    # SAVED", which is the same "progress goes up and then reverses" it was written to kill — only
    # globally this time, and silently.
    #
    # proposal_from_pages already sorts these to lists before returning; the merger must end in the
    # same shape or the two halves of one contract disagree.
    out["notFound"] = {k: sorted(v) for k, v in (out.get("notFound") or {}).items()}
    # and recompute the contradiction over the MERGED evidence, which is the only place it is true
    _con = {}
    for _led in ("uniques", "sets"):
        _nf = set(out.get("notFound", {}).get(_led) or ())
        for _nm in (out.get(_led) or {}):
            if _nm in _nf:
                _con.setdefault(_led, []).append(_nm)
    out["contested"] = {k: sorted(v) for k, v in _con.items()}
    out["setGroups"] = {k: sorted(v) for k, v in (out.get("setGroups") or {}).items()}
    # DERIVED, never accumulated — the whole point. Both are now answers to "what can this ledger
    # prove", which is a question a re-merge cannot change.
    out["pageKeys"] = sorted(_keys)
    out["pagesRead"] = len(_keys)
    out["pagesRefused"] = len(out["refused"])
    return out


def _reel_key(reel):
    """One reel, one key — whichever spelling it was recorded under.

    v1824 — A REEL IS WRITTEN INTO THE EVIDENCE UNDER TWO DIFFERENT NAMES. read_reel takes
    `sid = idx.get("sessionId") or os.path.basename(reel_dir)`, so a reel whose index carries a
    sessionId lands as "s_1787177267889_92273" while one without it falls back to the directory
    name, "reel_s_1787177267889_92273". Both spellings are already sitting in his live ledger.

    witnesses() counts DISTINCT reels, so the same reel read once under each spelling would score
    `cross-reel` — two independent sessions' worth of evidence conjured out of one. This function's
    own rule for cross-frame says it in one line: "Independence has to be independent of itself."
    Normalising here is conservative in the right direction: it can only ever REMOVE a witness, so
    it cannot ground a name that would not otherwise have grounded.
    """
    r = str(reel or "")
    return r[5:] if r.startswith("reel_") else r


def in_game_stamp(sightings):
    """The GAME's own First Found date and dropper for one name, or {} when it cannot be claimed.

    v1864 — Konyo: "i want the console also updateing me on when it was found timestamped in the
    game..(not when the AI READ IT) ... it should be storyline synced with the ingame diablo ii".

    His Chronicle prints it per row — "IMMORTAL KING'S WILL · Dropped By: Andariel · First Found:
    07/18/2026, 02:47" — the reader has been returning it since p1839 (`foundAt`, `droppedBy`), and
    proposal_from_pages already hangs it on each sighting. Nothing downstream had ever read it back
    off. This is that read.

    THE RULE IS AGREEMENT, NOT FIRST-SEEN. A First Found date is a FIXED fact about an item, so two
    lanes reading the same row should print the same string; when they do, that agreement is exactly
    the corroboration the rest of this file is built on. When two different values are equally
    supported the answer is NOT a coin flip — it is that the date is unknown, and unknown is what
    gets returned. [[unknown-stays-unknown]]

    Returns {"at": <raw game string>, "by": <dropper>, "n": <sightings that agreed>} — `at` and `by`
    are decided INDEPENDENTLY, because a page can print a legible date beside an illegible dropper.
    """
    def _pick(key):
        tally = {}
        for sg in (sightings or []):
            v = str((sg or {}).get(key) or "").strip()
            if v:
                tally[v] = tally.get(v, 0) + 1
        if not tally:
            return "", 0
        best = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))
        if len(best) > 1 and best[0][1] == best[1][1]:
            return "", 0          # tied and contradictory — say nothing rather than pick
        return best[0][0], best[0][1]

    at, n_at = _pick("foundAt")
    by, _n_by = _pick("droppedBy")
    out = {}
    if at:
        out["at"] = at
        out["n"] = n_at
    if by:
        out["by"] = by
    return out


def witnesses(sightings):
    """The distinct, independent signals behind one proposed name. Returns a sorted list of tags."""
    tags = set()
    lanes = {(s.get("lane") or "claude") for s in (sightings or [])}
    reels = {_reel_key(s.get("reel")) for s in (sightings or []) if s.get("reel")}
    if len(lanes) >= 2:
        tags.add("cross-lane")
    if len(reels) >= 2:
        tags.add("cross-reel")
    # Three separate sessions saying the same thing is a genuinely different strength from two, and
    # it is the honest way to let repetition alone ground a name. TWO reads of one panel — even in
    # different sessions — can share a systematic misread: same model, same font, same row. Three
    # makes that much harder, so it counts as a witness in its own right.
    if len(reels) >= 3:
        tags.add("cross-reel-3+")
    # v1519 — cross-frame means two frames WITHIN one reel. Counting (reel, frame) pairs globally
    # made a single sighting in each of two sessions score cross-reel AND cross-frame — the same
    # repetition banked twice, which would let two witnesses' worth of evidence pass a two-witness
    # gate on the strength of one. Independence has to be independent of itself.
    by_reel = {}
    for s in (sightings or []):
        if s.get("frame"):
            by_reel.setdefault(_reel_key(s.get("reel")), set()).add(s.get("frame"))
    if any(len(v) >= 2 for v in by_reel.values()):
        tags.add("cross-frame")
    if any((s.get("witness") == "agree") for s in (sightings or [])):
        tags.add("printed")
    return sorted(tags)


def gate_verdict(name, sightings, conf_floor=CONF_FLOOR, min_witnesses=MIN_WITNESSES):
    """Should this name be grounded? Returns a verdict that EXPLAINS itself either way.

    {"pass": bool, "witnesses": [...], "why": str, "bestConf": float, "sightings": n}

    The `why` is not decoration. When he asks why his grail did not move, the answer has to be a
    sentence, not a boolean — and when it DID move, the reason has to survive being questioned.
    """
    sightings = list(sightings or [])
    best = max([float(s.get("conf") or 0) for s in sightings] or [0.0])
    w = witnesses(sightings)
    if not sightings:
        return {"pass": False, "witnesses": [], "bestConf": 0.0, "sightings": 0,
                "why": "no evidence at all"}
    if best < conf_floor:
        return {"pass": False, "witnesses": w, "bestConf": best, "sightings": len(sightings),
                "why": "the reader itself was unsure (%.2f < %.2f) — unsure twice is still unsure"
                       % (best, conf_floor)}
    if len(w) < min_witnesses:
        return {"pass": False, "witnesses": w, "bestConf": best, "sightings": len(sightings),
                "why": "only %d independent witness%s (%s) — needs %d"
                       % (len(w), "" if len(w) == 1 else "es", ", ".join(w) or "none", min_witnesses)}
    return {"pass": True, "witnesses": w, "bestConf": best, "sightings": len(sightings),
            "why": "corroborated by %s" % ", ".join(w)}


def strict_gate(conf_floor=CONF_FLOOR, min_witnesses=MIN_WITNESSES):
    """The gate to hand apply_proposal. Keeps the verdicts so a caller can show its reasoning."""
    seen = {}

    def _gate(name, sightings):
        v = gate_verdict(name, sightings, conf_floor, min_witnesses)
        seen[name] = v
        return v["pass"]

    _gate.verdicts = seen
    return _gate


def sweep_frames(paths, kind, read_page, sig_of=None, reel_of=None):
    """v1527 — read a KNOWN set of chronicle frames. No classify, at all.

    This is what the live lane buys. A recorded visit (v1522) already knows two things a blind sweep
    has to pay a model to discover: that these frames ARE the Chronicle, and WHICH ledger was open.
    So a visit sweep skips the classify stage entirely and pays only for distinct pages — typically
    one or two reads for a whole panel he scrolled through.

    Frames are still de-duplicated by appearance: he holds the panel still for seconds at 2fps, and
    reading the same pixels forty times would cost forty reads for one page.

    v1758 — THE DEDUPE THRESHOLD WAS 0.06, FIFTEEN TIMES THE SIGNAL IT HAD TO SEE, and that single
    number is why his Chronicle never synced. Measured on his own 08-11 visit: SCROLLING the panel
    moves jpeg_sig by 0.00391, while a genuinely held page moves it by exactly 0.00000. At 0.06
    every page of a scrolled panel collapsed into the first frame, so an 8-frame visit read ONE
    page — the top of the list, all unfound silhouettes — refused it with "no-found-state", and
    reported the visit as holding nothing. Seven pages carrying real First Found lines, including
    Bartuc's Cut-Throat at 05/20/2026 02:19, were never looked at.

    The old docstring sold that as the cheap path: "typically one or two reads for a whole panel he
    scrolled through". One read of a scrolled panel is not thrift, it is a miss — and it cost the
    same as a read that works.

    It now uses CHRON_STILL_MAX_DIFF, the constant that already exists for exactly this question,
    so there is ONE number to reason about instead of two that disagreed.
    """
    sig_of = sig_of or jpeg_sig
    reel_of = reel_of or (lambda p: os.path.basename(os.path.dirname(p)))
    paths = [p for p in (paths or []) if p]
    keep, last = [], None
    for p in paths:
        sg = sig_of(p)
        if sg is None:
            keep.append(p)          # unreadable to US is not unreadable to the model — let it try
            continue
        if last is None or sig_diff(last, sg, tol=CHRON_SIG_TOL) > CHRON_STILL_MAX_DIFF:
            keep.append(p)
            last = sg
    pages = []
    for p in keep:
        resp = read_page(p, kind) or {}
        pages.append({"reel": reel_of(p), "frame": os.path.basename(p), "kind": kind, "resp": resp})
    return {"framesGiven": len(paths), "pagesRead": len(keep), "classified": 0, "pages": pages}


def reel_dirs(hist_dir, newest_first=True):
    """Every sealed reel under a hist root, newest first by default."""
    try:
        names = [n for n in os.listdir(hist_dir) if n.startswith("reel_")]
    except Exception:
        return []
    paths = [os.path.join(hist_dir, n) for n in names]
    # v1607 — THIS LINE USED TO SILENTLY DROP AN INDEX-LESS REEL, which is how 98 real frames became
    # invisible to sweep_hist / vault_retro / theatre at once. Now every candidate is HEALED on first
    # read: a missing index is rebuilt from the frame names, a present one is returned untouched, and
    # only a directory with no frames at all is dropped.
    # The `reel_` prefix filter above is load-bearing — tv/frames/hist also holds cache1280/cache160,
    # thumbnail caches full of f_*.jpg that are NOT reels and must never be given an index.
    # v1608 — PURE. A reel with frames but no index.json is still footage: load_index() rebuilds it
    # IN MEMORY so it is VISIBLE here without this read-only module writing anything. Putting that
    # rebuilt index on disk is reel_index.ensure_reel_index()'s job (console boot sweep / --apply).
    paths = [p for p in paths if os.path.isdir(p) and _index_ok(load_index(p))]
    paths.sort(key=lambda p: os.path.basename(p), reverse=newest_first)
    return paths


def _reel_known(known, reel):
    """The journal marks that apply to ONE reel. Accepts a flat {frame: kind} map (frame ids are
    unique across reels) or a {reelBasename: {frame: kind}} map, so the caller can hand in whichever
    shape it already holds without reshaping it."""
    if isinstance(known, dict):
        sub = known.get(reel)
        if isinstance(sub, (dict, list, tuple, set)):
            return sub
    return known


def sweep_hist(hist_dir, classify, read_page, limit=None, sig_of=None, on_reel=None,
               skip_reels=None, known_chronicle=None, priced_only=False):
    """v1524 — `skip_reels` is the sweep's MEMORY: reel basenames already read, which are not paid
    for twice. A sealed reel never changes, so re-reading one buys nothing and costs everything.

    A skipped reel is REPORTED as skipped, never silently omitted. "12 reels · 9 already swept" is
    the honest headline; showing 3 would make his footage look thinner than it is and quietly hide
    that most of the answer came from a previous run."""
    """THE RETRO SWEEP: every sealed reel he has, folded into ONE proposal.

    Still writes nothing. Returns {"reels": [...per-reel stats...], "proposal": {...}, "totals": {...}}.

    on_reel(stat) fires as each reel finishes, so a long sweep can report progress instead of going
    quiet for ten minutes — a silent sweep is one he kills halfway and never trusts again.

    The totals deliberately carry `framesSeen` and `classified` alongside `pagesRead`. He should be
    able to see that 394 frames cost 11 classifies without taking anyone's word for it.
    """
    skip = set(skip_reels or ())
    stats, pages = [], []
    frames_seen = 0
    skipped = 0
    # v1781 — LIMIT COUNTS REELS IT CAN ACTUALLY READ, NOT REELS IT WALKS PAST.
    # The slice used to happen BEFORE the skip test: with limit=1 and the newest reel already swept,
    # the sweep took that one reel, reported "already-swept", and stopped — never reaching the reel
    # it was asked for. The reel watchdog passes limit=1 on every tick, so once the newest reel was
    # swept the watchdog could never read anything again, whatever it targeted. Demonstrated in
    # isolation: tick 2 targeted reel_s_1000_older and read_reel was called only for
    # reel_s_2000_newest. It also hid v1779's fix, which narrows skip_reels to the targeted reel and
    # could not work while the slice ran first.
    #
    # Skipped reels are STILL reported (the "12 reels · 9 already swept" headline stays honest);
    # they just do not consume the budget.
    _all = reel_dirs(hist_dir)
    _ordered = [d for d in _all if os.path.basename(d) not in skip]
    if limit:
        _ordered = _ordered[:limit]
    _report_skipped = [d for d in _all if os.path.basename(d) in skip]
    for reel_dir in _report_skipped + _ordered:
        if os.path.basename(reel_dir) in skip:
            skipped += 1
            st = {"reel": os.path.basename(reel_dir), "runs": 0, "candidates": 0,
                  "classified": 0, "pages": 0, "note": "already-swept"}
            stats.append(st)
            if on_reel:
                try:
                    on_reel(st)
                except Exception:
                    pass
            continue
        r = read_reel(reel_dir, classify, read_page, sig_of=sig_of,
                      known_chronicle=_reel_known(known_chronicle, os.path.basename(reel_dir)))
        # v1607 — same accessor as read_reel(), so the frame COUNT and the frames actually swept can
        # never disagree. Counting straight off index.json here would have reported 0 frames for a
        # reel the sweep had just read 98 of.
        frames_seen += len((load_index(reel_dir) or {}).get("frames") or [])
        pages.extend(r.get("pages") or [])
        stat = {k: r.get(k) for k in ("reel", "runs", "candidates", "classified", "blankRuns",
                                      "journalRuns", "note")}
        stat["pages"] = len(r.get("pages") or [])
        stats.append(stat)
        if on_reel:
            try:
                on_reel(stat)
            except Exception:
                pass
    prop = proposal_from_pages(pages)
    totals = {
        "reels": len(stats),
        "skippedReels": skipped,
        "framesSeen": frames_seen,
        "candidates": sum(s.get("candidates") or 0 for s in stats),
        "classified": sum(s.get("classified") or 0 for s in stats),
        "trustedFocus": sum(s.get("trustedFocus") or 0 for s in stats),
        "blankRuns": sum(s.get("blankRuns") or 0 for s in stats),
        "journalRuns": sum(s.get("journalRuns") or 0 for s in stats),
        "pagesRead": prop.get("pagesRead", 0),
        "refused": len(prop.get("refused") or []),
        "uniques": len(prop.get("uniques") or {}),
        "sets": len(prop.get("sets") or {}),
        # v1838 — SURFACE THE AUDIT TRAIL SO IT CAN BE AUDITED. notFound is carried on purpose and
        # subtracts from nothing (test_notFound_is_carried_for_audit_and_subtracts_from_nothing) —
        # absence is not allowed to un-tick a find, and that stays true. But it reached no surface a
        # person reads, and an audit nobody can see is not an audit.
        #
        # It is also the cheapest INSTRUMENT check there is: a Chronicle page yielding eight found
        # names and zero not-found ones means the reader is seeing the ticks and missing the list,
        # which is the exact failure v1758 spent a whole version on. Zero here is a smell, not a
        # clean bill. [[feedback-suspect-the-instrument]]
        "notFound": sum(len(v or ()) for v in (prop.get("notFound") or {}).values()),
    }
    return {
        "reels": stats,
        "proposal": prop,
        "totals": totals,
        "verdict": sweep_verdict(totals, priced_only=priced_only),
    }


def sweep_verdict(totals, priced_only=False):
    """v1541 — WHY AN EMPTY SWEEP IS EMPTY. There is more than one way to find nothing, and they
    need different things done about them.

    Konyo: *"i tried this yesterday and it didnt work properly."*

    It worked. His four sealed reels hold 394 frames of lobby, character select, the title screen,
    two stash panels and three blank captures — and not one Chronicle page. The sweep looked at
    eleven still screens, classified none of them as a Chronicle, and correctly proposed nothing.
    Which is indistinguishable from broken, because it never said any of that.

    The rest of this arc already knows better: live_miss_audit.py refuses to dress "nothing to
    judge" as "everything works". The sweep never got the same manners. Four distinct nothings:

      no-footage      no reels at all — play a session first
      all-swept       every reel was already read; the memory is doing its job
      no-chronicle    ★ HIS CASE. Screens were examined; none was a Chronicle page.
      read-nothing    Chronicle pages WERE found and read, and they yielded no names —
                      that one really is the reader, and it is the only one that is.

    Only the last means the reading is at fault. Collapsing the first three into it would send him
    debugging a prompt when what he needs is to open the Chronicle while the console is watching.

    v1689 — AND A FIFTH, WHICH IS NOT A NOTHING AT ALL:

      not-measured    ★ `priced_only`. No reader ran. The --cost pass installs a classify that
                      always returns None and a read_page that returns {}, so pagesRead is 0 BY
                      CONSTRUCTION and every genuine branch below is being fed a fiction. It printed
                      "NONE was a Chronicle page … not a reader failure" over a reel that provably
                      holds eight Chronicle pages. A stub reader may report COST; it may never
                      report what the footage contains.
    """
    if priced_only:
        t = totals or {}
        return {"state": "not-measured", "ok": True,
                "say": ("No reader ran. This pass prices frames — %d reel(s) grouped into %d still "
                        "screen(s) — and reads none of them, so what the footage holds is unmeasured."
                        % (t.get("reels") or 0, t.get("candidates") or 0)),
                "do": ("Run the real sweep (the console owns the Claude + Grok lanes) to find out "
                       "whether these frames hold a Chronicle. Nothing is written either way.")}
    t = totals or {}
    reels = t.get("reels") or 0
    skipped = t.get("skippedReels") or 0
    cands = t.get("candidates") or 0
    classified = t.get("classified") or 0
    pages = t.get("pagesRead") or 0
    blank = t.get("blankRuns") or 0
    names = (t.get("uniques") or 0) + (t.get("sets") or 0)

    if names:
        return {"state": "found", "ok": True,
                "say": "%d name(s) proposed from %d Chronicle page(s)." % (names, pages),
                "do": ""}
    if not reels:
        return {"state": "no-footage", "ok": True,
                "say": "There is no sealed footage to sweep yet.",
                "do": "Play a session with TV DIABLO watching — it seals a reel when you finish."}
    if reels and skipped >= reels:
        return {"state": "all-swept", "ok": True,
                "say": "All %d reel(s) were already swept, so nothing was re-read." % reels,
                "do": "Record a new session, or reset the sweep memory to read them again."}
    if not cands:
        return {"state": "no-stills", "ok": True,
                "say": ("%d reel(s) were grouped and no screen was held still long enough to be worth "
                        "reading — that is footage of moving, not of looking at a panel." % reels),
                "do": "Open the Chronicle and leave it on screen for a few seconds before moving on."}
    # `classified` is the number of classify CALLS, not the number that came back as a Chronicle —
    # read_reel() increments it before it asks. The count that means "we found a Chronicle" is
    # pagesRead. Reading it the other way put this exact case in the branch below and told him to
    # hold the panel steadier, when the panel was never opened at all.
    if not pages:
        # v1543 — a blank-capture count is not a footnote. Runs that were skipped for being one flat
        # tone are the capture lane handing the reader photographs of nothing, and saying so here is
        # the difference between "your Chronicle was not on camera" and "your camera was not on".
        blanks = (" %d run(s) were skipped as BLANK CAPTURES — the window was grabbed with nothing "
                  "on it, which is worth fixing on its own." % blank) if blank else ""
        return {"state": "no-chronicle", "ok": True,
                "say": ("%d still screen(s) across %d reel(s) were examined and NONE was a Chronicle "
                        "page — so there was nothing to read. This is not a reader failure.%s"
                        % (cands, reels, blanks)),
                "do": ("Open the Chronicle in game while TV DIABLO is watching, hold it still for a "
                       "few seconds on the UNIQUES page and again on the SETS page, then sweep. "
                       "(No console running? Photograph the Chronicle and use the board's "
                       "📜 Read my Chronicle buttons instead — v1540.)")}
    return {"state": "read-nothing", "ok": False,
            "say": ("%d Chronicle page(s) WERE read and produced no names. This one is the reading "
                    "itself, not the footage." % pages),
            "do": "Check the refusals below — a page can be the wrong ledger, or show no found-marks."}


def merge_max(existing, proposed_names):
    """THE MERGE LAW: union, never difference.

    existing: the names already found (any iterable). proposed_names: names this sweep found.
    Returns {"merged": sorted, "added": sorted, "already": sorted} — `added` is what he actually
    gains, and it is the only number worth showing him.
    """
    have = set(existing or [])
    prop = set(proposed_names or [])
    return {
        "merged": sorted(have | prop),
        "added": sorted(prop - have),
        "already": sorted(prop & have),
    }


def apply_proposal(proposal, existing, gate=None):
    """The ONLY function here that produces a change — and even then it hands the change back rather
    than writing it, so the caller owns the write and the receipt.

    gate(name, sightings) -> bool decides what is allowed through. Default: nothing. An absent gate
    means "no policy has been stated", and applying a whole grail because nobody specified a rule is
    exactly the failure this arc exists to avoid. v1513 supplies the real gate.

    Returns {"uniques": {...merge_max...}, "sets": {...}, "held": [...]} where `held` names everything
    the gate refused, WITH its evidence, so a refusal is reviewable instead of silent.
    """
    gate = gate or (lambda name, sightings: False)
    out, held = {}, []
    # v1530 — a complete-set claim is judged by the SAME rule as a name. "The panel said Tal Rasha is
    # done" is exactly the kind of claim that is cheap to read wrong and expensive to be wrong about,
    # since one accepted claim ticks every piece.
    passed_sets = []
    for nm, sightings in sorted((proposal.get("completeSets") or {}).items()):
        if gate(nm, sightings):
            passed_sets.append(nm)
        else:
            held.append({"ledger": "completeSets", "name": nm, "sightings": sightings})
    out["completeSets"] = passed_sets
    for ledger in ("uniques", "sets"):
        passed = []
        for nm, sightings in sorted((proposal.get(ledger) or {}).items()):
            if gate(nm, sightings):
                passed.append(nm)
            else:
                held.append({"ledger": ledger, "name": nm, "sightings": sightings})
        out[ledger] = merge_max((existing or {}).get(ledger) or [], passed)
    out["held"] = held
    return out


# ── CLI ─────────────────────────────────────────────────────────────────────────
# Print-only, on purpose. This module may never write, and a CLI that dropped a proposal file would
# break the law the whole arc rests on — so the sweep SHOWS you what it found and you decide.
if __name__ == "__main__":
    import console_safe  # noqa: F401  — emoji must survive a non-UTF-8 console
    import argparse

    ap = argparse.ArgumentParser(description="Chronicle retro sweep over the sealed reels.")
    ap.add_argument("--hist", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "frames", "hist"))
    ap.add_argument("--limit", type=int, default=None, help="only the N newest reels")
    ap.add_argument("--cost", action="store_true",
                    help="FREE: group frames into runs and report what a real sweep WOULD cost")
    args = ap.parse_args()

    if args.cost:
        # the honest pitch, computed on his own film rather than asserted
        _COST_PICKED = []

        def _cost_classify(path):
            _COST_PICKED.append(path)     # remember WHICH frame, then refuse: free, and nothing read
            return None

        # v1689 — priced_only says out loud what this pass is: _cost_classify NEVER returns a kind
        # and read_page returns {}, so a verdict computed from these totals would be a stub reader's
        # opinion of footage it never looked at. It said "NONE was a Chronicle page" about eight
        # Chronicle pages.
        res = sweep_hist(args.hist, classify=_cost_classify, read_page=lambda p, k: {},
                         limit=args.limit, priced_only=True,
                         on_reel=lambda s: print("  %-34s %3d runs → %2d classifies"
                                                 % (s["reel"][:34], s["runs"] or 0, s["classified"] or 0)))
        t = res["totals"]
        saved = 100 * (1 - (t["classified"] / t["framesSeen"])) if t["framesSeen"] else 0
        print("\n📜 %d reels · %d frames → %d classifies (%.0f%% cheaper than reading every frame)"
              % (t["reels"], t["framesSeen"], t["classified"], saved))
        print("   run with the real reader to turn those into a proposal; nothing is written either way.")
        # v1541 — WHAT THOSE STILL SCREENS ACTUALLY ARE. The cost pass has always said how many
        # frames it would classify and never what they were, so "11 classifies" reads as "11
        # Chronicle pages" when it means "11 screens worth looking at". On a machine I cannot see —
        # his Windows PC — this listing is the difference between a diagnosis and a guess: he runs
        # one command, opens the named frames, and knows immediately whether the Chronicle is in his
        # footage at all.
        print("\n   the frames a real sweep would pay to classify — open them and see what they are:")
        for p in _COST_PICKED:
            print("     %s" % p)
        v = res.get("verdict") or {}
        if v.get("say"):
            print("\n   %s" % v["say"])
            if v.get("do"):
                print("   → %s" % v["do"])
        raise SystemExit(0)

    print("This sweep needs a reader. Use --cost for the free grouping pass, or drive sweep_hist()")
    print("from the console, which owns the Claude + Grok lanes and the apply step.")
