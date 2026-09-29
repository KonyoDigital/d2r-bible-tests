#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#54 — EQUIPPED ITEMS, PIXEL-EXACT, PER CHARACTER, CARRIED ACROSS THE HOURLY REELS OF ONE GAME SESSION.

WHAT EXISTED, so that this adds rather than duplicates:
    slot_identity.EQUIP_SLOTS      six doll slots MEASURED in frame fractions (v2375/v2376), four REFUSED
    slot_identity.worn_slot_of     a frame point -> the measured slot it lies in, or why not
    main_character                 WHICH NAMES are his gear, Wilson-scored over sightings — no slot, no
                                   pixels, no character: one ledger for whoever is logged in
    reel_door                      which door opened a reel, read once from the journal
    control_app._shadow_rollover   cuts a shadow reel every hour and re-opens ~2 s later — so ONE evening
                                   of play is N reels, and nothing joined them back together

WHAT WAS MISSING, measured before this was written (REG-340 stands: `character` appeared in ZERO journal
rows, `worn_slot_of` had ZERO callers outside its own law, and `EQUIP_SLOTS` was read by nothing but its
tests): the doll geometry was calibrated and never joined to a read; the equipment learner had no idea WHO
was wearing what; and the hourly rollover produced reels that no surface could say belonged to one game.
[[the-unjoined-end]]

THE RECORD, keyed by the character read at LOGIN / CHARACTER SELECT — the one screen that prints the
name (REG-340: the film cannot name the character during play, so the name comes from the login row and
is CARRIED). Per character, per doll slot: the item, the slot's box in THAT frame's pixels, the frame it
was seen on, how many frames saw it. A worn item whose slot cannot be told is recorded UNPLACED with the
reason — worn is a fact, the slot is a separate fact, and a guessed slot tells him he wears something he
carries. [[unknown-stays-unknown]]

THE CHAIN ACROSS REELS. A login row is always a boundary: a new game session begins there. A reel that
opens WITHOUT a login continues the previous game session only when the gap between the previous reel's
seal and this reel's first row is one the rollover itself produces (ROLLOVER_GAP_MS), and it then
INHERITS that session's character, marked `carried`. Any longer gap is a reel nobody can attribute, and
its worn items land in `unattributed` with a denominator — never under the last character seen.

THE CORROBORATOR PAIR. A read may say WHICH slot in words (`names_slot`, the reader's vocabulary) and/or
WHERE (`names_xy`, a frame point). The word and the geometry are two independent sources: when both answer
and agree the slot is corroborated; when they disagree the slot is a CONFLICT and the item is UNPLACED with
both answers written down; when only one answers, that one is the answer and the record says which.
[[heart-first]] rule 1

⚠ THE READER DOES NOT EMIT THESE FIELDS YET. `_parse_read` now ACCEPTS `scene: "char-select"`, `character`,
`names_slot` and `names_xy` and writes them to the journal row, but READ_PROMPT does not ask for them,
because changing READ_PROMPT means bumping PROMPT_VER, and control_app._chron_seal_current voids every
zero-page chronicle seal on a PROMPT_VER change — a paid re-sweep of his reels. That is his decision, not
this module's, and it is written in BUGS.md REG-1522. Until then every reel reads UNATTRIBUTED and this
ledger's `characters` stays empty — an empty store with a reason, not a fabricated one.

⚠ PURE: stdlib + slot_identity. No console import, so the laws drive it over a throwaway journal and the
fixture packs' frames. It decides nothing about the vault; it records.
"""
import io
import json
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import slot_identity as _SI  # noqa: E402

#: the deep reader's scene for the login / character-select screen — the only screen that prints the name
CHAR_SELECT_SCENE = "char-select"
#: names_loc value the reader already emits for worn gear (main_character.EQUIPMENT_ALIASES accepts it)
EQUIPPED_LOC = "equipped"
#: the reader's slot vocabulary IS the doll's — one tuple, owned by the geometry (six measured, four refused)
DOLL_SLOTS = _SI.DOLL_SLOTS
#: the store, beside the other ledgers of whichever world TV_HIST names
STORE_NAME = "equipped_ledger.json"
LANE = "equipped-ledger"

#: The largest seal->first-row gap the hourly rollover ITSELF produces, in ms. Measured from the watcher's
#: own constants (control_app): a stop takes ~8 s (its rotate margin says so), the relook after a rollover is
#: _SHADOW_ROTATE_RELOOK_S = 2 s, and if that relook is refused the next look is a full
#: _SHADOW_WATCH_EVERY_S = 20 s later — 30 s of mechanism. 90 s is that with 3x slack for a slow seal, and
#: still far below the 60 s away-grace plus any human "quit and come back". A law pins it between the
#: mechanism's own sum and five minutes, so it can neither miss a rollover nor chain two evenings.
ROLLOVER_GAP_MS = 90 * 1000
#: keep this many frame ids per slot record — enough to count sightings, small enough to stay a record
_FRAMES_KEPT = 40
_PREVIOUS_KEPT = 8
_INGESTED_KEPT = 4000


# ── where ──────────────────────────────────────────────────────────────────────────────────────────────
def world():
    """The directory this store lives in: his tv/ normally, the fixture's when TV_HIST names one.

    The ONE rule every state file uses (tv_diablo._fixture_root), called rather than copied — v2788 is the
    scar for a verbatim copy that drifted. A request for isolation that cannot be honoured never degrades
    to his tree. [[copy-drift]] [[feedback-fixtures-never-touch-live-data]]
    """
    try:
        import tv_diablo as _tvd
        return _tvd._fixture_root(HERE)
    except Exception:
        _h = (os.environ.get("TV_HIST") or "").strip()
        return _h if (_h and os.path.isabs(_h)) else HERE


def store_path(store=None):
    return store or os.path.join(world(), STORE_NAME)


# ── pixels ─────────────────────────────────────────────────────────────────────────────────────────────
def jpeg_size(path):
    """(width, height) of a JPEG from its SOF marker, stdlib only. -> tuple | None

    None means "could not read a size" — not a file, not a JPEG, no SOF before EOF. The ALT had no Pillow
    (#227), so a size reader that needs it would refuse on the machine that films the most.
    """
    try:
        with io.open(path, "rb") as fh:
            b = fh.read(65536)
    except Exception:
        return None
    if len(b) < 4 or b[0:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 <= len(b):
        if b[i] != 0xFF:
            return None
        m = b[i + 1]
        if m == 0xFF:
            i += 1
            continue
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        ln = struct.unpack(">H", b[i + 2:i + 4])[0]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return (w, h) if (w > 0 and h > 0) else None
        i += 2 + ln
    return None


def frame_path(hist_dir, sid, frame_id):
    """Where a reel's frame sits: <hist>/reel_<sid>/<frame>.jpg (the sealed layout, and the fixture
    packs'), else <hist>/<frame>.jpg (a reel still rolling). -> path | None"""
    if not (hist_dir and frame_id):
        return None
    fid = str(frame_id)
    if not fid.endswith(".jpg"):
        fid += ".jpg"
    sid = str(sid or "")
    reel = sid if sid.startswith("reel_") else ("reel_" + sid if sid else "")
    for p in ((os.path.join(hist_dir, reel, fid) if reel else None), os.path.join(hist_dir, fid)):
        if p and os.path.isfile(p):
            return p
    return None


def frame_size(hist_dir, sid, frame_id):
    """-> ((w, h), None) or (None, why). A frame not on disk is UNKNOWN, never the calibration size."""
    p = frame_path(hist_dir, sid, frame_id)
    if not p:
        return None, "frame %s of reel %s is not on disk under %s" % (frame_id, sid, os.path.basename(str(hist_dir or "?")))
    sz = jpeg_size(p)
    if not sz:
        return None, "frame %s is on disk but its size could not be read from the JPEG header" % frame_id
    return sz, None


def slot_box(slot, frame_w, frame_h):
    """The doll slot's box in THIS frame's pixels. -> ((x, y, w, h), None) or (None, why)

    The measured fractions in slot_identity.EQUIP_SLOTS, scaled — the same aspect band worn_slot_of
    trusts, because D2R anchors the doll and scales with HEIGHT, so outside that band the horizontal
    fractions move and nothing has been measured there. Four slots are REFUSED by name: a box interpolated
    for helm or gloves would place a real item in a box nobody measured.
    """
    if slot not in DOLL_SLOTS:
        return None, "%r is not a doll slot (the doll has %s)" % (slot, ", ".join(DOLL_SLOTS))
    if slot in _SI.UNMEASURED_SLOTS:
        return None, ("the %s slot is not measured (slot_identity refuses %s) — the item is worn there, "
                      "its box is UNKNOWN" % (slot, ", ".join(_SI.UNMEASURED_SLOTS)))
    try:
        fw, fh = float(frame_w), float(frame_h)
    except (TypeError, ValueError):
        return None, "frame size is not numeric"
    if fw <= 0 or fh <= 0:
        return None, "frame measures %gx%g" % (fw, fh)
    aspect = fw / fh
    if not (_SI._PANEL_CAL_LO <= aspect <= _SI._PANEL_CAL_HI):
        return None, ("this frame is %.3f aspect; the doll was measured at %.3f and nothing outside "
                      "%.2f-%.2f has been measured" % (aspect, _SI._PANEL_CAL_ASPECT, _SI._PANEL_CAL_LO,
                                                      _SI._PANEL_CAL_HI))
    fx, fy, fwf, fhf = _SI.EQUIP_SLOTS[slot]
    return (round(fx * fw, 2), round(fy * fh, 2), round(fwf * fw, 2), round(fhf * fh, 2)), None


# ── rows ───────────────────────────────────────────────────────────────────────────────────────────────
def _ts(row):
    """The row's own millisecond stamp. -> int | None

    REG-1558 — None means the row carries no readable stamp: UNKNOWN, never epoch 0. A 0 here sorted
    an undatable row before everything, chained it to nothing, and stamped a slot record as seen in
    1970 — a failed read wearing a measurement. `ts` first (the capture clock), else `captureTs`;
    an unparseable or non-positive value is skipped, not coerced. [[stale-reading]] §3
    [[unknown-stays-unknown]]
    """
    if not isinstance(row, dict):
        return None
    for k in ("ts", "captureTs"):
        v = row.get(k)
        if v is None or v == "" or isinstance(v, bool):
            continue
        try:
            t = int(v)
        except (TypeError, ValueError):
            continue
        if t > 0:
            return t
    return None


def _newest(*stamps):
    """max over the KNOWN stamps; None when none is known — never 0 for 'nobody knows'."""
    known = [int(s) for s in stamps if isinstance(s, (int, float)) and not isinstance(s, bool)]
    return max(known) if known else None


def _sort_key(row):
    """Dated rows by time; undated rows after them, in file order (the sort is stable)."""
    t = _ts(row)
    return (1, 0) if t is None else (0, t)


def character_of_row(row):
    """The character a LOGIN row names. -> (name, None) or (None, why)

    Only a char-select row may name him: a `character` on any other scene is text the reader saw
    somewhere else (a merc, chat, a player), and REG-340 measured that the name is not on screen in play.
    """
    if not isinstance(row, dict):
        return None, "not a row"
    if str(row.get("scene") or "") != CHAR_SELECT_SCENE:
        return None, "scene %r is not the login screen" % (row.get("scene"),)
    ch = row.get("character")
    if not isinstance(ch, str) or not ch.strip():
        return None, "a login row with no readable character name"
    return ch.strip()[:32], None


def read_rows(journals):
    """Every parseable row across the journal paths given. -> (rows, report)

    report = {read: [paths], absent: [paths], unreadable: [(path, why)], rows: n, bad: n}. A rotated
    generation that does not exist is ABSENT (normal); a path that exists and cannot be read is
    UNREADABLE — and the caller must treat 'nothing read at all' as UNKNOWN, never as an empty journal.
    [[zero-needs-a-denominator]]
    """
    rows, rep = [], {"read": [], "absent": [], "unreadable": [], "rows": 0, "bad": 0}
    if isinstance(journals, str):
        journals = [journals]
    for p in journals or []:
        if not p or not os.path.exists(p):
            rep["absent"].append(p)
            continue
        try:
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln.startswith("{"):
                        continue
                    rep["rows"] += 1
                    try:
                        r = json.loads(ln)
                    except Exception:
                        rep["bad"] += 1
                        continue
                    if isinstance(r, dict) and r.get("sessionId"):
                        rows.append(r)
            rep["read"].append(p)
        except Exception as e:
            rep["unreadable"].append((p, type(e).__name__))
    return rows, rep


def reels_from_rows(rows):
    """Group rows by reel. -> [reel], sorted by first row; each {sid, t0, t1, door, sealed, sealedTs, rows}

    t0 / t1 are the first and last KNOWN stamps (None when no row is dated). `sealed` is a fact about
    the rows — a session_end row exists — and `sealedTs` is that row's stamp, which may be UNKNOWN.
    """
    by = {}
    for r in rows:
        sid = str(r.get("sessionId") or "")
        if not sid:
            continue
        by.setdefault(sid, []).append(r)
    out = []
    for sid, rs in by.items():
        rs.sort(key=_sort_key)
        door = None
        for r in rs:
            if r.get("door"):
                door = str(r.get("door"))
                break                       # first writer wins — the door that opened it (reel_door)
        # REG-1558 — SEALED and WHEN are two facts. Folding them into one field made an undated seal
        # row read as "still rolling", so that reel was never filed and never owed.
        seal_rows = [r for r in rs if str(r.get("scene") or "") == "session_end"]
        dated = [t for t in (_ts(r) for r in rs) if t is not None]
        out.append({"sid": sid, "t0": (dated[0] if dated else None), "t1": (dated[-1] if dated else None),
                    "door": door, "sealed": bool(seal_rows),
                    "sealedTs": _newest(*[_ts(r) for r in seal_rows]), "rows": rs})
    out.sort(key=lambda x: ((1, 0, x["sid"]) if x["t0"] is None else (0, x["t0"], x["sid"])))
    return out


def char_spans(reel):
    """Split one reel at its login rows. -> [span]; span = {t0, t1, character, via, loginFrame, rows}

    The rows before the first login form a span with character None and via None — the one a rollover
    chain may fill. Every login opens a new span with via "char-select". A login that names nobody is
    still a BOUNDARY (a new game began) with character None and via "char-select": the name is unknown,
    the fact that he logged in is not.
    """
    spans, cur = [], None
    for r in reel["rows"]:
        if str(r.get("scene") or "") == CHAR_SELECT_SCENE:
            name, _why = character_of_row(r)
            if cur is not None and cur["rows"]:
                spans.append(cur)
            cur = {"t0": _ts(r), "t1": _ts(r), "character": name, "via": "char-select",
                   "loginFrame": r.get("frameId"), "rows": []}
            continue
        if cur is None:
            cur = {"t0": _ts(r), "t1": _ts(r), "character": None, "via": None, "loginFrame": None,
                   "rows": []}
        cur["rows"].append(r)
        if cur["t0"] is None:
            cur["t0"] = _ts(r)              # an undated opener: the span starts at its first KNOWN row
        cur["t1"] = _newest(cur["t1"], _ts(r))
    if cur is not None and (cur["rows"] or cur["via"]):
        spans.append(cur)
    return spans


def game_sessions(reels, gap_ms=None):
    """Chain reels' spans into game sessions. -> (sessions, by_span)

    sessions: [{id, character, characterVia, reels, spans, t0, t1, joins}] ; by_span: {(sid, t0): session}
    A span that opens with a login starts a session. A reel's pre-login span continues the previous
    session only across a rollover-sized gap (seal -> first row <= gap_ms), inheriting its character as
    `carried`; otherwise it is its own session with no character. [[unknown-stays-unknown]]
    """
    gap = int(ROLLOVER_GAP_MS if gap_ms is None else gap_ms)
    sessions, by_span, prev_reel, cur = [], {}, None, None
    for reel in reels:
        spans = char_spans(reel)
        for i, sp in enumerate(spans):
            if sp["via"] == "char-select":
                cur = {"id": "g_%s_%s" % (reel["sid"], "undated" if sp["t0"] is None else sp["t0"]),
                       "character": sp["character"],
                       "characterVia": "char-select", "reels": [reel["sid"]], "spans": 1,
                       "t0": sp["t0"], "t1": sp["t1"], "joins": []}
                sessions.append(cur)
                sp["carried"] = None
            else:
                # the reel's pre-login span: continue the previous session across a rollover gap only
                joined, gap_why = False, None
                if i == 0 and cur is not None and prev_reel is not None:
                    seal = prev_reel["sealedTs"] if prev_reel["sealedTs"] is not None else prev_reel["t1"]
                    if seal is None or reel["t0"] is None:
                        # REG-1558 — a gap nobody can measure is not a rollover-sized gap. Chaining on a
                        # guessed clock would file this reel's gear under the previous character.
                        gap_why = ("the gap from %s cannot be measured (%s is undated), so nothing chains"
                                   % (prev_reel["sid"],
                                      "the previous reel" if seal is None else "this reel's first row"))
                    else:
                        g = reel["t0"] - int(seal)
                        if 0 <= g <= gap:
                            cur["reels"].append(reel["sid"])
                            cur["spans"] += 1
                            cur["t1"] = _newest(cur["t1"], sp["t1"])
                            cur["joins"].append({"from": prev_reel["sid"], "to": reel["sid"], "gapMs": g,
                                                 "doors": [prev_reel["door"], reel["door"]]})
                            sp["character"] = cur["character"]
                            sp["carried"] = ("carried from %s across a %d s gap" % (prev_reel["sid"], g // 1000)
                                             if cur["character"] else None)
                            joined = True
                        elif g < 0:
                            gap_why = ("this reel starts %s s before %s sealed — overlapping reels do not chain"
                                       % ((-g) // 1000, prev_reel["sid"]))
                        else:
                            gap_why = ("the gap from %s (%s s) is longer than a rollover (%d s)"
                                       % (prev_reel["sid"], g // 1000, gap // 1000))
                if not joined:
                    why = "no login in this reel and " + (gap_why or "no rollover-sized gap to a previous reel")
                    cur = {"id": "g_%s_nologin" % reel["sid"], "character": None, "characterVia": None,
                           "reels": [reel["sid"]], "spans": 1, "t0": sp["t0"], "t1": sp["t1"],
                           "joins": [], "why": why}
                    sessions.append(cur)
                    sp["carried"] = None
            sp["session"] = cur["id"]
            by_span[(reel["sid"], sp["t0"])] = cur
        reel["spans"] = spans
        prev_reel = reel
    return sessions, by_span


# ── one read ───────────────────────────────────────────────────────────────────────────────────────────
def worn_from_row(row, hist_dir):
    """Every worn item a read names, each with its slot decided by word AND geometry. -> [worn]

    worn = {item, slot, slotBy, why, box, boxWhy, frame, frameSize, ts, xy}
    """
    out = []
    loc = row.get("names_loc") or {}
    if not isinstance(loc, dict):
        return out
    # REG-1558 — {} is "the read named none"; None (or a row from before #54) is UNKNOWN: nobody
    # parsed slot words / points for this read. Those are different facts and each gets its reason.
    words_raw, points_raw = row.get("names_slot"), row.get("names_xy")
    words = words_raw if isinstance(words_raw, dict) else {}
    points = points_raw if isinstance(points_raw, dict) else {}
    words_unknown, points_unknown = not isinstance(words_raw, dict), not isinstance(points_raw, dict)
    fid, sid = row.get("frameId"), row.get("sessionId")
    size, size_why = (frame_size(hist_dir, sid, fid) if fid else (None, "the row names no frame"))
    for name, where in loc.items():
        if str(where or "").strip().lower() != EQUIPPED_LOC:
            continue
        item = str(name).strip()
        if not item:
            continue
        word = str(words.get(name) or "").strip().lower() or None
        if word is not None and word not in DOLL_SLOTS:
            word = None
        xy = points.get(name)
        pt = None
        try:
            if isinstance(xy, (list, tuple)) and len(xy) == 2:
                pt = (float(xy[0]), float(xy[1]))
        except (TypeError, ValueError):
            pt = None
        geo, geo_why = None, None
        if pt is not None:
            if size is None:
                geo_why = "the point cannot be placed: %s" % size_why
            else:
                geo, geo_why = _SI.worn_slot_of(pt, size[0], size[1])
        # ── the corroborator pair: the reader's WORD and the frame's GEOMETRY ─────────────────────
        if word and geo:
            if word == geo:
                slot, by, why = word, "reader+geometry", "the reader's word and the point agree"
            else:
                slot, by = None, "conflict"
                why = ("CONFLICT: the reader says %s, the point (%g,%g) lies in the %s box — unplaced "
                       "until one of them is wrong" % (word, pt[0], pt[1], geo))
        elif word:
            slot, by = word, "reader"
            why = ("the reader's word alone" + (" (geometry could not check: %s)" % geo_why if pt is not None
                                                 else ""))
        elif geo:
            slot, by, why = geo, "geometry", "the point alone, in a measured box"
        else:
            slot, by = None, None
            if pt is not None:
                why = "the point alone, and it answers nothing: %s" % geo_why
            elif words_unknown or points_unknown:
                why = ("no slot evidence, and it is UNKNOWN whether there was any: %s" % " and ".join(
                    w for w, u in (("the read's slot words were never parsed", words_unknown),
                                   ("the read's points were never parsed", points_unknown)) if u))
            else:
                why = "the read carried no slot word and no point"
        box, box_why = (None, None)
        if slot:
            if size is None:
                box, box_why = None, size_why
            else:
                box, box_why = slot_box(slot, size[0], size[1])
        out.append({"item": item, "slot": slot, "slotBy": by, "why": why, "box": (list(box) if box else None),
                    "boxWhy": box_why, "frame": fid, "frameSize": (list(size) if size else None),
                    "ts": _ts(row), "xy": (list(pt) if pt else None)})
    return out


# ── the store ──────────────────────────────────────────────────────────────────────────────────────────
def _empty():
    return {"characters": {}, "unattributed": {"reads": 0, "reels": [], "names": {}, "why": None},
            "gameSessions": {}, "lane": {"worked": 0, "lastTs": None, "ingested": []}}


def load(store=None):
    """-> (dict, None) or (None, why). Absent is an EMPTY store (nothing ever ingested); unreadable is UNKNOWN."""
    p = store_path(store)
    if not os.path.exists(p):
        return _empty(), None
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as e:
        return None, "%s could not be read (%s)" % (os.path.basename(p), type(e).__name__)
    if not isinstance(d, dict):
        return None, "%s is not a mapping" % os.path.basename(p)
    base = _empty()
    for k, v in base.items():
        if k not in d or not isinstance(d[k], type(v)):
            d[k] = v
    return d, None


def _save(d, store=None):
    p = store_path(store)
    try:
        import provenance as _PV
        d = _PV.stamp(d, by="equipped_ledger", extra={"store": "equipped_ledger"})
    except Exception:
        pass
    tmp = p + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    os.replace(tmp, p)


def _file_worn(char_rec, w, sid, gid):
    """Merge one worn sighting into a character record. Sightings count FRAMES, not calls."""
    fid = str(w.get("frame") or "")
    if w["slot"]:
        slots = char_rec.setdefault("slots", {})
        cur = slots.get(w["slot"])
        if cur and cur.get("item") == w["item"]:
            frames = cur.setdefault("frames", [])
            if fid and fid not in frames:
                frames.append(fid)
                del frames[:-_FRAMES_KEPT]
                cur["sightings"] = int(cur.get("sightings") or 0) + 1
            cur["ts"] = _newest(cur.get("ts"), w["ts"])
            if w["box"] is not None:
                cur["box"], cur["boxWhy"], cur["frameSize"] = w["box"], None, w["frameSize"]
            elif cur.get("box") is None:
                cur["boxWhy"] = w["boxWhy"]
            cur["slotBy"], cur["why"] = w["slotBy"], w["why"]
            cur["lastFrame"] = fid or cur.get("lastFrame")
        else:
            prev = list((cur or {}).get("previous") or [])
            if cur:
                prev.append({"item": cur.get("item"), "ts": cur.get("ts"), "frame": cur.get("lastFrame")})
                del prev[:-_PREVIOUS_KEPT]
            slots[w["slot"]] = {"item": w["item"], "box": w["box"], "boxWhy": w["boxWhy"],
                                "frame": fid or None, "lastFrame": fid or None, "frameSize": w["frameSize"],
                                "frames": ([fid] if fid else []), "sightings": 1,
                                "firstTs": w["ts"], "ts": w["ts"], "slotBy": w["slotBy"], "why": w["why"],
                                "reel": sid, "gameSession": gid, "previous": prev}
    else:
        un = char_rec.setdefault("unplaced", {})
        cur = un.get(w["item"]) or {"sightings": 0, "frames": [], "firstTs": w["ts"]}
        if fid and fid not in cur["frames"]:
            cur["frames"].append(fid)
            del cur["frames"][:-_FRAMES_KEPT]
            cur["sightings"] = int(cur.get("sightings") or 0) + 1
        cur["why"], cur["lastTs"], cur["reel"] = w["why"], _newest(cur.get("lastTs"), w["ts"]), sid
        un[w["item"]] = cur
    for key, val in (("reels", sid), ("gameSessions", gid)):
        lst = char_rec.setdefault(key, [])
        if val and val not in lst:
            lst.append(val)
    char_rec["lastTs"] = _newest(char_rec.get("lastTs"), w["ts"])


def ingest(journals, hist_dir, now_ms=None, store=None, gap_ms=None):
    """Read the journals, file every worn item of every SEALED reel not yet ingested. -> receipt

    receipt = {ok, why, ingested: [sid], rolling: [sid], filed, unattributed, characters, journal}
    ok None = UNKNOWN (no journal readable, or the store unreadable) and NOTHING is written.
    """
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    rows, rep = read_rows(journals)
    if not rep["read"]:
        return {"ok": None, "why": "no journal could be read (%d absent, %d unreadable) — the ledger is UNKNOWN, "
                                   "not empty" % (len(rep["absent"]), len(rep["unreadable"])),
                "ingested": [], "rolling": [], "filed": 0, "unattributed": 0, "journal": rep}
    d, why = load(store)
    if d is None:
        return {"ok": None, "why": why + " — nothing filed over a store that cannot be read",
                "ingested": [], "rolling": [], "filed": 0, "unattributed": 0, "journal": rep}
    reels = reels_from_rows(rows)
    sessions, _by = game_sessions(reels, gap_ms=gap_ms)
    for s in sessions:
        d["gameSessions"][s["id"]] = {k: v for k, v in s.items()}
    done = set(d["lane"].get("ingested") or [])
    ingested, rolling, filed, unatt = [], [], 0, 0
    for reel in reels:
        if not reel["sealed"]:
            rolling.append(reel["sid"])
            continue
        if reel["sid"] in done:
            continue
        for sp in reel.get("spans") or []:
            gid = sp.get("session")
            for r in sp["rows"]:
                for w in worn_from_row(r, hist_dir):
                    if sp["character"]:
                        rec = d["characters"].setdefault(sp["character"], {"name": sp["character"], "slots": {},
                                                                           "unplaced": {}, "reels": [],
                                                                           "gameSessions": [], "lastTs": None})
                        if sp.get("carried"):
                            via = rec.setdefault("carried", {})
                            via[reel["sid"]] = sp["carried"]
                        _file_worn(rec, w, reel["sid"], gid)
                        filed += 1
                    else:
                        u = d["unattributed"]
                        u["reads"] = int(u.get("reads") or 0) + 1
                        if reel["sid"] not in u["reels"]:
                            u["reels"].append(reel["sid"])
                        nm = u.setdefault("names", {})
                        if len(nm) < 60 or w["item"] in nm:
                            nm[w["item"]] = int(nm.get(w["item"]) or 0) + 1
                        u["why"] = ("worn items seen in a reel with no login and no rollover chain — %s"
                                    % (d["gameSessions"].get(gid, {}).get("why") or "the reel's session names no character"))
                        unatt += 1
        ingested.append(reel["sid"])
    if ingested:
        lane = d["lane"]
        lane["ingested"] = (list(lane.get("ingested") or []) + ingested)[-_INGESTED_KEPT:]
        lane["worked"] = int(lane.get("worked") or 0) + len(ingested)
        lane["lastTs"] = now
        try:
            _save(d, store)
        except Exception as e:
            return {"ok": False, "why": "filed %d worn item(s) but the store would not write (%s)"
                                        % (filed, type(e).__name__), "ingested": [], "rolling": rolling,
                    "filed": filed, "unattributed": unatt, "journal": rep}
    why = ("ingested %d sealed reel(s): %d worn item(s) filed under %d character(s), %d unattributed"
           % (len(ingested), filed, len(d["characters"]), unatt)
           if ingested else "nothing new: every sealed reel in the journal is already in the ledger")
    if rolling:
        why += " · %d reel(s) still rolling, left for their seal" % len(rolling)
    return {"ok": True, "why": why, "ingested": ingested, "rolling": rolling, "filed": filed,
            "unattributed": unatt, "characters": sorted(d["characters"]), "journal": rep}


# ── the heart's vocabulary ─────────────────────────────────────────────────────────────────────────────
def contract(journals=None, store=None, now_ms=None):
    """This lane in the shared supervision vocabulary. -> dict

    on       True — it has no switch; it runs at every seal (after_session_ended)
    worked   LIFETIME reels ingested, from the store — a per-process counter cannot say "has this ever worked"
    lastTs   when it last filed something; None = never
    owed     sealed reels in the journal not yet in the ledger; None when the journal or the store cannot
             be read — UNKNOWN is never 0. [[heart-first]] §3 §7
    oldestOwedSealTs  the OLDEST owed seal's stamp — the age that says whether the lane is late (REG-1559);
             None when nothing is owed or no owed seal carries a readable time. owedUndated counts the latter.
    """
    d, why = load(store)
    if d is None:
        return {"on": True, "worked": None, "lastTs": None, "owed": None, "newestSealTs": None,
                "oldestOwedSealTs": None, "owedUndated": None, "sealedNotIngested": None, "say": why}
    lane = d.get("lane") or {}
    out = {"on": True, "worked": int(lane.get("worked") or 0), "lastTs": lane.get("lastTs"),
           "owed": None, "newestSealTs": None, "oldestOwedSealTs": None, "owedUndated": None,
           "sealedNotIngested": None,
           "characters": len(d.get("characters") or {}),
           "placed": sum(len(c.get("slots") or {}) for c in (d.get("characters") or {}).values()),
           "unplaced": sum(len(c.get("unplaced") or {}) for c in (d.get("characters") or {}).values()),
           "unattributedReads": int((d.get("unattributed") or {}).get("reads") or 0)}
    if journals is None:
        out["say"] = "the journal was not asked, so what is owed is UNKNOWN"
        return out
    rows, rep = read_rows(journals)
    if not rep["read"]:
        out["say"] = "no journal could be read, so what is owed is UNKNOWN — not zero"
        return out
    done = set(lane.get("ingested") or [])
    sealed = [(r["sid"], r["sealedTs"]) for r in reels_from_rows(rows) if r["sealed"]]
    owed = [(sid, t) for sid, t in sealed if sid not in done]
    out["owed"], out["sealedNotIngested"] = len(owed), [sid for sid, _t in owed]
    out["newestSealTs"] = _newest(*[t for _s, t in sealed])
    # REG-1559 — the age that says whether the lane is LATE is the OLDEST owed seal's, never the
    # newest seal of all reels: a lane failing at every seal keeps a fresh newest seal forever.
    out["oldestOwedSealTs"] = (min(t for _s, t in owed if t is not None)
                               if any(t is not None for _s, t in owed) else None)
    out["owedUndated"] = sum(1 for _s, t in owed if t is None)
    out["say"] = say(d, owed=len(owed))
    return out


def say(d, owed=None):
    """One sentence a surface can print. -> str"""
    chars = (d or {}).get("characters") or {}
    placed = sum(len(c.get("slots") or {}) for c in chars.values())
    unpl = sum(len(c.get("unplaced") or {}) for c in chars.values())
    un = int(((d or {}).get("unattributed") or {}).get("reads") or 0)
    head = ("%d character(s): %d slot(s) placed, %d worn item(s) unplaced" % (len(chars), placed, unpl)
            if chars else "no character on record yet")
    if un:
        head += " · %d worn read(s) unattributed (no login, no rollover chain)" % un
    if owed is None:
        head += " · owed UNKNOWN"
    elif owed:
        head += " · %d sealed reel(s) owed" % owed
    return head


def main(argv):
    try:
        from console_safe import enable as _en
        _en()
    except Exception:
        pass
    if argv[:1] == ["--ingest"] and len(argv) >= 3:
        r = ingest([argv[1]], argv[2])
        print(json.dumps(r, indent=1))
        return 0 if r.get("ok") else (2 if r.get("ok") is None else 1)
    d, why = load()
    if d is None:
        print("UNKNOWN: %s" % why)
        return 2
    print(say(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
