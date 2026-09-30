# -*- coding: utf-8 -*-
"""#91 — HIS CHARACTERS LEARN THEMSELVES FROM THE REELS.

Konyo, 2026-09-30, on the Character Builder's "From your characters (class + level)" list: "for character build
based on the reels and character selection it should also learn the character and sync them in automatically after
being witnessed a few times over."

That list was four HAND-TYPED rows in the page source (CHARS: Konyolock Warlock 88, Konyodin Paladin 82 ...). Nothing
ever updated them, so a level he gained stayed unsaid and a character he made never appeared.

MEASURED before building (2026-09-30, his Mac, 30 reels, 14,208 frames):
  · the character-select screen IS filmed — reel_s_1790675069096 opens on it: nine rows, "SOCKET / LEVEL 1 AMAZON",
    "OSENBEICHAN / LEVEL 31 WARLOCK" (title CHAMPION), a LEVEL 81 SORCERESS (title MATRIARCH) under the cursor ...
  · the local OCR CANNOT READ it (the D2R font: tv_diablo.py already records "defeated by the D2R FONT, not by
    resolution"): the list crop came back "LEvEL I BAKBARIAH", "LEVEL. SI Vi*RL•CK" (31 read as SI), "K•NY•Ku>".
    A whole-reel OCR hunt for "Level N <Class>" found NOTHING in 3,051 frames — the instrument, not the footage.
  · and the OCR is no DETECTOR either: shifting the crop 3 pixels swung it from 4 "LEVEL" rows to 1.
  · the PIXELS are: the list panel is flat grey stone — mean saturation 0.036-0.041, brightness 0.36-0.37 on his
    film — while every other screen measured sits far away (title 0.97 sat, Boosteroid queue 0.33, inventory 0.18,
    gameplay 0.11-0.33 at brightness <= 0.24). ~5 ms a frame, so EVERY frame is checked (his visit lasted 2 s).
    The READ is the console's own vision reader, on the panel crop only, and its "screen" answer is the second,
    independent witness: a grey panel that is not the list costs one refused read, never a character.

THE RULE HE ASKED FOR — "after being witnessed a few times over":
  · a VISIT is one stay on the character-select screen (candidate frames within VISIT_GAP_S of each other);
  · a character is LEARNED once it was read on MIN_VISITS separate visits, with a class;
  · its LEVEL is the highest level that MIN_VISITS visits saw it at or above — a level-up is confirmed the next time
    he opens the screen, and a single misread (88 read as 98) never becomes his level: it waits as `pendingLevel`;
  · within one visit the reads are not independent (the same screen), so a visit claims the LOWEST level its reads
    agree on.
PER PC by construction: each console scans its OWN reels into its OWN ledger (tv/.char_roster.json, gitignored), and
the page asks its own console. Nothing here writes a build: the 👤 Characters / builder stores stay manual (#245).
"""
import difflib
import glob
import json
import os
import re
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSES = ("Amazon", "Assassin", "Barbarian", "Druid", "Necromancer", "Paladin", "Sorceress", "Warlock")
TITLES = ("Slayer", "Champion", "Patriarch", "Matriarch", "Destroyer", "Conqueror", "Guardian", "Count", "Countess",
          "Baron", "Baroness", "Lord", "Lady", "Duke", "Duchess", "King", "Queen", "Sir", "Dame")

PANEL_W_H = 0.385        # the list panel's width as a fraction of the frame HEIGHT: D2R scales its UI with height
                         # and anchors this panel to the right edge. MEASURED on his 1440x904 film: the OCR found 4
                         # LEVEL rows at x0 = 0.76w (= w - 0.385h), 0 at 0.70w and 0 at 0.80w — the crop IS the read.
SAMPLE_EVERY = 1         # every frame (~1 fps): MEASURED, his visit on reel_s_1790675069096 lasted 2 frames
# BOTH stone panels, measured on all 45,555 frames of his 30 reels (2026-09-30): 8 real character-select visits read
# right sat 0.022-0.052 / val 0.355-0.361 and left sat 0.086-0.109 / val 0.215-0.219. With the right panel alone the
# scan also flagged two blank white browser pages (val 0.999 / left 1.0), a snow field in play (right val 0.461, left
# sat 0.217) and the game LOBBY (left val 0.153). The bands keep a margin because another PC films at another size.
RIGHT_SAT_MAX = 0.07
RIGHT_VAL = (0.30, 0.45)
LEFT_SAT = (0.05, 0.16)
LEFT_VAL = (0.17, 0.27)
VISIT_GAP_S = 90         # candidate frames further apart than this are separate visits
MIN_VISITS = 2           # "witnessed a few times over"
MAX_READS_PER_VISIT = 2
READS_PER_HOUR = 8       # the paid reader is his subscription; this lane never spends more than this
TICK_BUDGET_S = 8.0      # wall time one tick may spend scanning (it rides a 45 s loop: <20% of one core, and less
                         # on the ALT, where the game shares an 8 GB box)

_FRAME_TS = re.compile(r"f_(\d{10,})\.(?:jpg|jpeg|png)$", re.I)


def store_path():
    return os.environ.get("TV_CHARS_LEARNED") or os.path.join(HERE, ".char_roster.json")


def hist_root():
    try:
        import tv_diablo as _td
        return _td.HIST_DIR
    except Exception:
        return os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")


# ── the detector (free) ─────────────────────────────────────────────────────────────────────────────────────
def _sv(im, box):
    from PIL import ImageStat
    st = ImageStat.Stat(im.crop(tuple(int(v) for v in box)).resize((20, 40)).convert("HSV"))
    return st.mean[1] / 255.0, st.mean[2] / 255.0


def panel_stats(path):
    """(right_sat, right_val, left_sat, left_val), 0..1: the list panel on the right and the menu column on the
    left, or None when the frame cannot be opened. JPEG draft mode decodes at 1/4 size — both panels are flat
    stone, so a quarter of the pixels says the same thing (measured ~7 ms a frame over his 45,555)."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.draft("RGB", (max(1, im.size[0] // 4), max(1, im.size[1] // 4)))
            im = im.convert("RGB")
            w, h = im.size
            rs, rv = _sv(im, (max(0, w - PANEL_W_H * h), 0.07 * h, w, 0.93 * h))
            ls, lv = _sv(im, (0.02 * h, 0.40 * h, 0.30 * h, 0.95 * h))
            return rs, rv, ls, lv
    except Exception:
        return None


def looks_like_char_select(stats):
    """(bool, why) from panel_stats(): the grey stone list on the right AND the stone menu column on the left."""
    if not stats:
        return False, "frame unreadable"
    rs, rv, ls, lv = stats
    right = rs < RIGHT_SAT_MAX and RIGHT_VAL[0] < rv < RIGHT_VAL[1]
    left = LEFT_SAT[0] < ls < LEFT_SAT[1] and LEFT_VAL[0] < lv < LEFT_VAL[1]
    say = "right sat %.3f val %.3f · left sat %.3f val %.3f" % (rs, rv, ls, lv)
    if right and left:
        return True, "both stone panels (%s)" % say
    return False, ("no list panel" if not right else "no menu column") + " (%s)" % say


def panel_crop(path, out_dir):
    """Crop the character list (right-hand panel) to its own file. Returns the crop path, or None — a frame that
    cannot be opened is not a frame that showed nothing."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
            box = (max(0, int(w - (PANEL_W_H + 0.02) * h)), 0, w, h)
            dst = os.path.join(out_dir, "cs_" + os.path.basename(path))
            im.crop(box).convert("RGB").save(dst, quality=88)
            return dst
    except Exception:
        return None


# ── the reader's answer, normalized ─────────────────────────────────────────────────────────────────────────
def _fold(name):
    """The key a name is matched on: the D2R font draws O as ⊕, readers vary in case."""
    s = str(name or "").replace("⊕", "O").replace("Ø", "O").replace("◎", "O")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _clean_name(name):
    s = str(name or "").replace("⊕", "O").replace("Ø", "O").replace("◎", "O").strip()
    s = re.sub(r"\s+", " ", s)
    # D2R names: 2-15 characters, letters plus at most one '-' or '_'; anything else is a misread
    if not re.fullmatch(r"[A-Za-z][A-Za-z\-_]{1,14}", s):
        return None
    # the game's font is small capitals, so an all-caps answer ("RUNEWORDER") says nothing about the real case:
    # shown as "Runeworder". A mixed-case answer ("OsenbeiChan") is kept as the reader saw it. The KEY folds case.
    return s.title() if s.isupper() else s


def _clean_class(cls):
    c = str(cls or "").strip()
    if not c:
        return None
    for k in CLASSES:
        if c.lower() == k.lower():
            return k
    m = difflib.get_close_matches(c.title(), CLASSES, n=1, cutoff=0.75)
    return m[0] if m else None


def _clean_level(v):
    try:
        n = int(str(v).strip())
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 99 else None


def normalize(raw):
    """The reader's JSON -> (rows, why). rows: [{name, key, cls, level, title}] for every row that is a character.
    `why` names a refusal; ([], 'other screen') is a MEASURED answer, (None, why) is not an answer at all."""
    if raw is None:
        return None, "no answer"
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return None, "not JSON"
    if not isinstance(raw, dict):
        return None, "not an object"
    if raw.get("note"):
        return None, str(raw.get("note"))[:120]
    if str(raw.get("screen") or "").lower() != "character-select":
        return [], "other screen"
    rows = []
    for r in raw.get("chars") or []:
        if not isinstance(r, dict):
            continue
        name = _clean_name(r.get("name"))
        if not name:
            continue
        title = str(r.get("title") or "").strip().title() or None
        rows.append({"name": name, "key": _fold(name), "cls": _clean_class(r.get("cls")),
                     "level": _clean_level(r.get("level")), "title": title if title in TITLES else None})
    return rows, ("%d rows" % len(rows))


# ── the ledger ──────────────────────────────────────────────────────────────────────────────────────────────
def _empty():
    return {"version": 1, "chars": {}, "visits": {}, "reels": {},
            "stats": {"ticks": 0, "frames": 0, "reads": 0, "refused": 0, "lastTs": None, "lastWhy": "", "readTs": []}}


def load():
    """The ledger, or None when it exists and cannot be read — UNKNOWN, never an empty ledger (an empty one would
    be written back over the real one on the next tick)."""
    p = store_path()
    if not os.path.exists(p):
        return _empty()
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict) or not isinstance(d.get("chars"), dict):
            return None
        base = _empty()
        for k in base:
            d.setdefault(k, base[k])
        return d
    except Exception:
        return None


def save(d):
    p = store_path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, p)


def record(d, visit_id, rows, meta=None):
    """Fold one read of one visit into the ledger. Within a visit a character keeps the LOWEST level its reads
    agree on (two reads of one screen are not two witnesses)."""
    v = d["visits"].setdefault(visit_id, {"reads": 0, "rows": 0})
    v["reads"] = int(v.get("reads") or 0) + 1
    v["rows"] = max(int(v.get("rows") or 0), len(rows or []))
    v.update({k: meta[k] for k in (meta or {}) if k in ("reel", "ts", "tab", "frames", "reader")})
    for r in rows or []:
        c = d["chars"].setdefault(r["key"], {"name": r["name"], "cls": {}, "visitLevel": {}, "titles": {},
                                             "firstTs": None, "lastTs": None})
        # the SPELLING is voted too: MEASURED on his reels one character came back "SOCKET" (-> "Socket") on one
        # read and "SOcket" on another, and last-read-wins showed whichever was newest. The shown name is the form
        # most reads agree on (the first seen on a tie); the KEY never depended on it.
        forms = c.setdefault("forms", {})
        forms[r["name"]] = int(forms.get(r["name"]) or 0) + 1
        best = max(forms.values())
        c["name"] = next(f for f in forms if forms[f] == best)
        if r.get("cls"):
            per = c["cls"].setdefault(r["cls"], [])
            if visit_id not in per:
                per.append(visit_id)
        if r.get("level"):
            prev = c["visitLevel"].get(visit_id)
            c["visitLevel"][visit_id] = r["level"] if prev is None else min(prev, r["level"])
        else:
            c["visitLevel"].setdefault(visit_id, None)
        if r.get("title"):
            c["titles"][r["title"]] = int(c["titles"].get(r["title"]) or 0) + 1
        ts = (meta or {}).get("ts")
        if ts:
            c["firstTs"] = ts if not c.get("firstTs") else min(c["firstTs"], ts)
            c["lastTs"] = ts if not c.get("lastTs") else max(c["lastTs"], ts)
    return d


def learned(d, min_visits=MIN_VISITS):
    """The characters the reels have witnessed enough: [{name, key, cls, level, pendingLevel, visits, title,
    lastTs}], highest level first. None when the ledger is UNKNOWN."""
    if d is None:
        return None
    out = []
    for key, c in (d.get("chars") or {}).items():
        visits = sorted(c.get("visitLevel") or {})
        if len(visits) < min_visits:
            continue
        cls_votes = {k: len(set(v)) for k, v in (c.get("cls") or {}).items()}
        if not cls_votes:
            continue
        best = max(cls_votes.values())
        winners = sorted(k for k, n in cls_votes.items() if n == best)
        if len(winners) != 1 or best < min_visits:
            continue                      # two classes tie, or the class itself is not witnessed enough
        seen = sorted([lv for lv in (c.get("visitLevel") or {}).values() if lv], reverse=True)
        level = seen[min_visits - 1] if len(seen) >= min_visits else None
        pending = seen[0] if seen and (level is None or seen[0] > level) else None
        titles = c.get("titles") or {}
        out.append({"name": c.get("name"), "key": key, "cls": winners[0], "level": level, "pendingLevel": pending,
                    "visits": len(visits), "title": (max(titles, key=titles.get) if titles else None),
                    "lastTs": c.get("lastTs")})
    out.sort(key=lambda r: (-(r["level"] or 0), str(r["name"]).lower()))
    return out


# ── the scan (one bounded tick) ─────────────────────────────────────────────────────────────────────────────
def _default_reader(crop_path):
    import tv_diablo as _td
    return _td.charselect_read(crop_path)


def _frame_ts(p):
    m = _FRAME_TS.search(os.path.basename(p))
    return int(m.group(1)) if m else None


def tick(root=None, stats=None, reader=None, now=None, budget_s=TICK_BUDGET_S, clock=time.time):
    """One bounded pass: continue scanning the reels (newest first) for candidate frames, read at most
    MAX_READS_PER_VISIT per visit and READS_PER_HOUR in all, fold the answers in, save. Returns a status dict."""
    d = load()
    if d is None:
        return {"ok": False, "why": "the ledger could not be read — UNKNOWN, nothing written"}
    root = root or hist_root()
    stats = stats or panel_stats
    reader = reader or _default_reader
    now_s = float(now if now is not None else clock())
    t0 = clock()
    st = d["stats"]
    st["ticks"] = int(st.get("ticks") or 0) + 1
    st["readTs"] = [t for t in (st.get("readTs") or []) if now_s - float(t) < 3600]
    reels = sorted(glob.glob(os.path.join(root, "reel_*")), reverse=True)
    alive = set(os.path.basename(r) for r in reels)
    for gone in [k for k in d["reels"] if k not in alive]:
        d["reels"].pop(gone, None)            # the FIFO deleted it; its visits stay in the ledger
    work = tempfile.mkdtemp(prefix="tvd-cs-")
    scanned = candidates = reads = 0
    why = ""
    try:
        for rd in reels:
            name = os.path.basename(rd)
            frames = sorted(glob.glob(os.path.join(rd, "f_*.jpg")))
            rs = d["reels"].setdefault(name, {"pos": 0, "frames": 0, "open": None})
            rs["frames"] = len(frames)
            i = int(rs.get("pos") or 0)
            while i < len(frames):
                if clock() - t0 > budget_s:
                    why = "tick budget spent"
                    break
                p = frames[i]
                i += SAMPLE_EVERY
                rs["pos"] = i
                scanned += 1
                hit, _w = looks_like_char_select(stats(p))
                if not hit:
                    continue
                candidates += 1
                ts = _frame_ts(p) or 0
                op = rs.get("open")
                if not op or ts - int(op.get("lastTs") or 0) > VISIT_GAP_S * 1000:
                    op = {"id": "%s#%d" % (name, ts), "firstTs": ts, "lastTs": ts, "reads": 0}
                op["lastTs"] = ts
                rs["open"] = op
                if op["reads"] >= MAX_READS_PER_VISIT:
                    continue
                if len(st["readTs"]) >= READS_PER_HOUR:
                    why = "hourly read cap (%d) reached" % READS_PER_HOUR
                    continue
                crop = panel_crop(p, work)
                if not crop:
                    continue
                raw = reader(crop)
                st["readTs"].append(now_s)
                op["reads"] += 1
                rows, rwhy = normalize(raw)
                if rows is None:
                    st["refused"] = int(st.get("refused") or 0) + 1
                    st["lastWhy"] = "read refused: " + rwhy
                    continue
                st["reads"] = int(st.get("reads") or 0) + 1
                reads += 1
                if rows:
                    record(d, op["id"], rows, {"reel": name, "ts": ts, "reader": "vision",
                                               "frames": [os.path.basename(p)]})
            if why == "tick budget spent":
                break
    finally:
        for f in glob.glob(os.path.join(work, "*")):
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            os.rmdir(work)
        except OSError:
            pass
    st["frames"] = int(st.get("frames") or 0) + scanned
    st["lastTs"] = int(now_s * 1000)
    if why:
        st["lastWhy"] = why
    save(d)
    return {"ok": True, "scanned": scanned, "candidates": candidates, "reads": reads, "why": why or "scanned"}


def owed(d, root=None):
    """Frames not yet scanned, over the reels on disk. None when either side cannot be counted."""
    if d is None:
        return None
    try:
        n = 0
        for rd in glob.glob(os.path.join(root or hist_root(), "reel_*")):
            total = len(glob.glob(os.path.join(rd, "f_*.jpg")))
            pos = int(((d.get("reels") or {}).get(os.path.basename(rd)) or {}).get("pos") or 0)
            n += max(0, -(-(total - pos) // SAMPLE_EVERY))
        return n
    except Exception:
        return None


def status(root=None):
    """The heart's vocabulary: on · worked · lastTs · owed — plus what was learned. UNKNOWN is a state."""
    d = load()
    if d is None:
        return {"on": True, "worked": None, "lastTs": None, "owed": None, "learned": None,
                "say": "the character ledger could not be read — UNKNOWN"}
    st = d.get("stats") or {}
    got = learned(d) or []
    return {"on": True, "worked": int(st.get("reads") or 0), "lastTs": st.get("lastTs"), "owed": owed(d, root),
            "learned": len(got), "seen": len(d.get("chars") or {}), "visits": len(d.get("visits") or {}),
            "ticks": int(st.get("ticks") or 0), "refused": int(st.get("refused") or 0),
            "say": st.get("lastWhy") or ""}
