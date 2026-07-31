"""v1511 — CHRONICLE RETRO SWEEP, the engine.

Konyo: "retro and live... especially retro most important" — the sealed reels already contain every
Chronicle screen he has ever opened on camera. This module finds those frames and turns them into a
PROPOSAL. It never writes a ledger.

Three laws, and they are the whole design:

  1. READ-ONLY UNTIL APPLY. `sweep()` returns evidence. Only `apply_proposal()` changes anything, and
     it is a separate call a human makes. A sweep that silently ticked 400 grail rows would be
     unauditable — and un-untickable, because there is no "unfind" in Diablo.

  2. MERGE-MAX. A chronicle read only ever ADDS. His ledger is the accumulated truth of years; a reel
     from March cannot un-find something found in July, and a page that scrolled past a row is not
     evidence that the row is empty. `notFound` is carried for auditing and never subtracts.

  3. PAY FOR RUNS, NOT FRAMES. A reel is ~150 frames at 1-2fps; reading each one would cost more than
     the tally is worth, and 140 of them are the same page held still. Frames are grouped into STILL
     RUNS, one frame per run is classified, and only runs that come back `chronicle` are read in full.
     A 153-frame reel with one Chronicle visit costs ~8 classifies + the pages, not 153 reads.

Everything here is pure: the caller injects the signature function and the reader. That is what lets
the tests exercise the laws against fixtures without a vision model or a single JPEG.
"""

import json
import os

# A "still" pair — frames this similar are the same screen held. Calibrated against sig_diff()'s own
# scale in tv_diablo.py, where ambient render noise stays under the tolerance and opening a panel
# moves whole regions past it. Scrolling a list moves a band, so the threshold is deliberately loose
# enough to keep a scrolling read in one run rather than shattering it into singletons.
STILL_MAX_DIFF = 0.22
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


def read_reel(reel_dir, classify, read_page, sig_of=None, min_frames=MIN_RUN_FRAMES):
    """Sweep ONE sealed reel. Returns evidence — it writes nothing, anywhere.

    classify(frame_path) -> ("chronicle-uniques" | "chronicle-sets" | None)
        one call per candidate run, on the run's middle frame (the most settled one: the first frame
        of a run can still be mid-transition and the last can be mid-exit).
    read_page(frame_path, kind) -> the /api/intake chronicle response dict (v1510 shape).

    Returns {"reel": sid, "runs": n, "candidates": n, "classified": n, "pages": [ … ]}, where every
    page keeps the frame it came from. Provenance is not decoration here: when he asks "why does it
    think I have Windforce", the answer has to be a frame he can look at.
    """
    idx_path = os.path.join(reel_dir, "index.json")
    try:
        with open(idx_path, encoding="utf-8") as fh:
            idx = json.load(fh)
    except Exception:
        return {"reel": os.path.basename(reel_dir), "runs": 0, "candidates": 0,
                "classified": 0, "pages": [], "note": "no-index"}
    sid = idx.get("sessionId") or os.path.basename(reel_dir)
    sig_of = sig_of or (lambda n: jpeg_sig(os.path.join(reel_dir, n)))
    runs = still_runs(idx.get("frames") or [], sig_of)
    cands = candidate_runs(runs, min_frames=min_frames)
    pages, classified = [], 0
    for run in cands:
        fr = run["frames"]
        probe = fr[len(fr) // 2]
        classified += 1
        kind = classify(os.path.join(reel_dir, probe))
        if kind not in ("chronicle-uniques", "chronicle-sets"):
            continue
        # The run IS the visit. Reading every frame of a held-still page buys nothing, but a SCROLLED
        # page is a different page — so read the distinct-looking frames, which for a held page is one.
        for name in _distinct(fr, sig_of):
            resp = read_page(os.path.join(reel_dir, name), kind) or {}
            pages.append({"reel": sid, "frame": name, "kind": kind, "resp": resp})
    return {"reel": sid, "runs": len(runs), "candidates": len(cands),
            "classified": classified, "pages": pages}


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
    sets = [{"set": str(g.get("set") or "")[:60], "pieces": names(g.get("pieces"), 20)}
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
    prop = {"uniques": {}, "sets": {}, "setGroups": {}, "refused": [], "pagesRead": 0,
            "notFound": {"uniques": set(), "sets": set()}}
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
            if nm:
                prop["setGroups"].setdefault(nm, set()).update(g.get("pieces") or [])
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
        if last is None or sig_diff(last, sg) > 0.06:
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
    paths = [p for p in paths if os.path.isfile(os.path.join(p, "index.json"))]
    paths.sort(key=lambda p: os.path.basename(p), reverse=newest_first)
    return paths


def sweep_hist(hist_dir, classify, read_page, limit=None, sig_of=None, on_reel=None,
               skip_reels=None):
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
        r = read_reel(reel_dir, classify, read_page, sig_of=sig_of)
        try:
            with open(os.path.join(reel_dir, "index.json"), encoding="utf-8") as fh:
                frames_seen += len(json.load(fh).get("frames") or [])
        except Exception:
            pass
        pages.extend(r.get("pages") or [])
        stat = {k: r.get(k) for k in ("reel", "runs", "candidates", "classified", "note")}
        stat["pages"] = len(r.get("pages") or [])
        stats.append(stat)
        if on_reel:
            try:
                on_reel(stat)
            except Exception:
                pass
    prop = proposal_from_pages(pages)
    return {
        "reels": stats,
        "proposal": prop,
        "totals": {
            "reels": len(stats),
            "skippedReels": skipped,
            "framesSeen": frames_seen,
            "classified": sum(s.get("classified") or 0 for s in stats),
            "pagesRead": prop.get("pagesRead", 0),
            "refused": len(prop.get("refused") or []),
            "uniques": len(prop.get("uniques") or {}),
            "sets": len(prop.get("sets") or {}),
        },
    }


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
        res = sweep_hist(args.hist, classify=lambda p: None, read_page=lambda p, k: {},
                         limit=args.limit,
                         on_reel=lambda s: print("  %-34s %3d runs → %2d classifies"
                                                 % (s["reel"][:34], s["runs"] or 0, s["classified"] or 0)))
        t = res["totals"]
        saved = 100 * (1 - (t["classified"] / t["framesSeen"])) if t["framesSeen"] else 0
        print("\n📜 %d reels · %d frames → %d classifies (%.0f%% cheaper than reading every frame)"
              % (t["reels"], t["framesSeen"], t["classified"], saved))
        print("   run with the real reader to turn those into a proposal; nothing is written either way.")
        raise SystemExit(0)

    print("This sweep needs a reader. Use --cost for the free grouping pass, or drive sweep_hist()")
    print("from the console, which owns the Claude + Grok lanes and the apply step.")
