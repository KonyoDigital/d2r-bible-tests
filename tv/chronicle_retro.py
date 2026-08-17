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


def still_runs(frames, sig_of, max_diff=STILL_MAX_DIFF):
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
        if cur is not None and sig_diff(prev_sig, sig) <= max_diff:
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

    def _sweep_runs(run_list):
        nonlocal classified, blank_runs, trusted, journal_trusted
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
            if kind not in ("chronicle-uniques", "chronicle-sets"):
                continue
            # The run IS the visit. Reading every frame of a held-still page buys nothing, but a SCROLLED
            # page is a different page — so read the distinct-looking frames, which for a held page is one.
            for name in _distinct(fr, sig_of):
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


    return {"reel": sid, "runs": len(runs), "candidates": len(cands) + rescued,
            "classified": classified, "blankRuns": blank_runs, "pages": pages,
            "trustedFocus": trusted, "journalRuns": len(jruns),
            "journalTrusted": journal_trusted, "rescuedShortRuns": rescued}


def _distinct(names, sig_of, max_diff=0.06):
    """Within one run, keep only frames that actually LOOK different from the last kept one — a
    scrolled list, not the same page re-photographed 40 times. Tighter than STILL_MAX_DIFF on
    purpose: grouping asks "same screen?", this asks "same pixels?"."""
    out, last = [], None
    for n in names:
        s = sig_of(n)
        if s is None:
            continue
        if last is None or sig_diff(last, s) > max_diff:
            out.append(n)
            last = s
    return out


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


def normalize_page(raw, kind, lane):
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
    found = [] if (wrong_tab or not state_visible) else names(raw.get("found"))
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
        "found": found, "notFound": not_found, "sets": sets if ledger == "sets" else [],
        "stateVisible": state_visible, "wrongTab": wrong_tab, "wholePage": whole,
        "witness": witness, "conf": conf, "printed": printed,
        "read": {"found": len(found), "notFound": len(not_found)},
        "note": "wrong-ledger" if wrong_tab else ("no-found-state" if not state_visible else None),
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


def proposal_from_pages(pages):
    """Fold read pages into ONE proposal per ledger, keeping every name's evidence.

    A name seen on several frames collects several witnesses — that is the multi-witness signal the
    gate consumes, so the sightings are kept rather than deduped away. Pages the reader REFUSED
    (no-found-state / wrong-ledger, v1510) contribute nothing but are counted, because "8 pages read,
    3 refused" is the honest headline and "5 pages read" is not.
    """
    prop = {"uniques": {}, "sets": {}, "setGroups": {}, "completeSets": {}, "refused": [],
            "pagesRead": 0, "notFound": {"uniques": set(), "sets": set()}}
    for p in (pages or []):
        resp = p.get("resp") or {}
        ledger = resp.get("ledger") or ("sets" if p.get("kind") == "chronicle-sets" else "uniques")
        if resp.get("note"):
            prop["refused"].append({"reel": p.get("reel"), "frame": p.get("frame"),
                                    "why": resp.get("note")})
            continue
        prop["pagesRead"] += 1
        # v1514 — ONE SIGHTING PER LANE. Two eyes that agree must reach the gate as TWO witnesses;
        # folding them into one row would silently discard the strongest signal in the system.
        lane_map = resp.get("lanes") or {}
        for nm in (resp.get("found") or []):
            for lane in (lane_map.get(nm) or [resp.get("lane") or "claude"]):
                prop[ledger].setdefault(nm, []).append({
                    "reel": p.get("reel"), "frame": p.get("frame"),
                    "witness": resp.get("witness") or "none",
                    "conf": resp.get("conf") or 0,
                    "lane": lane,
                })
        for nm in (resp.get("notFound") or []):
            prop["notFound"][ledger].add(nm)
        for g in (resp.get("sets") or []):
            nm = g.get("set")
            if not nm:
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
    prop["setGroups"] = {k: sorted(v) for k, v in prop["setGroups"].items()}
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


def witnesses(sightings):
    """The distinct, independent signals behind one proposed name. Returns a sorted list of tags."""
    tags = set()
    lanes = {(s.get("lane") or "claude") for s in (sightings or [])}
    reels = {s.get("reel") for s in (sightings or []) if s.get("reel")}
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
            by_reel.setdefault(s.get("reel"), set()).add(s.get("frame"))
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
    for reel_dir in reel_dirs(hist_dir)[:limit] if limit else reel_dirs(hist_dir):
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
