# -*- coding: utf-8 -*-
"""#22 (his rulings 2026-10-28) - EACH HAND-TEST SCENARIO, TIED TO THE FRAMES OF HIS THAT SHOW ITS SCREEN.

His words: "if you can take my sessions and frames and reels and do the tests your self scenario by scenario then
great.. at least what you can understand from it but i think we need me too", then "templates characters/inventory/
stash those are pretty self-explanatory .. check blueprints always and wire it all properly and sync each scenario to
each visual frame related".

BUILT ON STORES THAT ALREADY EXIST - nothing here reads a picture, asks a model, or writes:
  * TESTING_PHASE.md     the scenario IDs, from its index table. A scenario this file declares no screens for is
                         reported NOT WIRED - never skipped, so the list cannot quietly shrink.
  * the journals         every read of a frame with the screen it saw (`scene`: stash, inventory, loot, town ...),
                         live (deep/ocr/known) and later (intake/verify), joined to its frame by the capture time.
  * retro_triage.json    which frames of a reel carry a stash panel and which tab - the labels for older reels whose
                         reads came only as later re-reads.

THE JOINS (his "make sure to join anything needed to be joined for that logic"):
  scenario -> its ITEMS      the names its **Items:** block lists, kept when the game's own rosters (uniques, set
                             pieces, runewords) know them or a recorded read named them - prose words never pass
  item -> his FRAMES         the frames whose recorded reads named that item, so a scenario names the exact frames
                             that test it, not every frame of its screen
  frame -> its PICTURE       a read's own picture is <frameId>.jpg at the reel root (100_1791910174639.jpg), or the
                             re-read's reel_s_<id>/f_<ms> - the reel folder's f_<ms>.jpg are FOOTAGE stills, whose ms
                             need not match a read's capture time (the first cut joined to those and found 0 of every
                             sample on disk - the count was the tell). A triage-labelled frame IS a still. A frame
                             whose picture was pruned says so.
  scenario -> its CHECK      REC-03 is judged against the deep reads and commitments recorded in its sessions

A REPORT, like printer.py: it prints and deletes nothing. A scenario with a check (REC-03 today) is judged against the
reads recorded on its frames; every other one is INDEXED - its frames named, its expectation still his or a law's.
A character panel is not labelled anywhere yet (#36 builds that reader), so a character scenario says NO FRAMES and
why, rather than borrowing another screen's frames. [[unknown-stays-unknown]] [[the-unjoined-end]]

  python3 tv/scenario_frames.py            every scenario, one line each
  python3 tv/scenario_frames.py REC-03     one scenario, with sample frames
  python3 tv/scenario_frames.py --json
"""
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

#: the journal lanes whose row is a READ of a frame (a live look or a later re-read) - never a note about one
READ_LANES = ("deep", "ocr", "known", "intake", "verify")
#: every stash tab retro_triage labels is a stash screen
_TRIAGE_STASH = ("stash", "shared", "personal", "materials", "runes", "gems")

_STASH, _INV, _FLOOR = ("stash",), ("inventory",), ("loot",)

#: scenario -> the screens its frames show, and what it proves. Screens are the journal's own `scene` words.
SCENARIOS = {
    "VAULT-ATTR-01": {"screens": _STASH, "about": "a stash tooltip of an ethereal socketed base"},
    "VAULT-MAGIC-01": {"screens": _STASH, "about": "magic and rare names read in the stash"},
    "VAULT-INTAKE-01": {"screens": _INV + _STASH, "about": "an item read in the inventory, then in the stash"},
    "MR-01": {"screens": _STASH, "about": "a stash read naming magic, rare, grail, base and unknown items"},
    "MR-02": {"screens": _STASH, "about": "a magic item seen again in the stash"},
    "HAVE-01": {"screens": _STASH + _INV + _FLOOR, "about": "a read naming items he already has"},
    "NEW-01": {"screens": _STASH + _INV + _FLOOR, "about": "a read naming an item he does not have"},
    "REC-03": {"screens": ("*",), "about": "every deep read answered by a warm worker, across its respawn"},
    "REC-07": {"screens": _FLOOR + _STASH, "about": "a floor read and a stash read, each with its receipt"},
    "MULE-VB-01": {"screens": (), "about": "the doll's slot picker", "not_frames": "a board surface - run in node"},
    "MULE-VB-02": {"screens": (), "about": "worn-gear stats", "not_frames": "a board surface - run in node"},
    "MULE-VB2-01": {"screens": (), "about": "drag to a cell", "not_frames": "a board surface - run in node"},
    "UNTICK-01": {"screens": (), "about": "his standing un-ticks", "not_frames": "a board rule - run in node"},
    "HAND-01": {"screens": (), "about": "a hand tick", "not_frames": "a board rule - run in node"},
    "CLAIM-01": {"screens": (), "about": "restore, never reseed", "not_frames": "a board rule - run in node"},
}

_ID = re.compile(r"\[([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\]\(#")


def _doc(doc_path=None):
    """TESTING_PHASE.md's text, or None when it will not read - never '' (an unread file is not an empty one)."""
    try:
        return io.open(doc_path or os.path.join(ROOT, "TESTING_PHASE.md"), encoding="utf-8").read()
    except OSError:
        return None


def scenario_ids(doc_path=None):
    """The scenario IDs in TESTING_PHASE.md's index, in its order. -> [str] | None when the file will not read"""
    text = _doc(doc_path)
    if text is None:
        return None
    seen, out = set(), []
    for m in _ID.finditer(text.split("\n## ", 2)[1] if "\n## " in text else text):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
    return out


def _norm(name):
    """One spelling for a name across the rosters and the reads: lower case, a roster's ' (helm)' suffix off."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", str(name or "")).strip().lower()


def roster_names(directory=None, only=None):
    """Every item name the game's own rosters know (uniques, set pieces, runewords), normalised. only="runewords" -> just
    the runewords. -> set"""
    d, out = directory or HERE, set()
    for f, keys in (("unique_roster.json", ("names",)), ("set_roster.json", ("pieces",)),
                    ("runeword_roster.json", ("names",))):
        if only == "runewords" and f != "runeword_roster.json":
            continue
        try:
            with io.open(os.path.join(d, f), encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        for k in keys:
            v = data.get(k) if isinstance(data, dict) else None
            for n in (v.keys() if isinstance(v, dict) else v or []):
                out.add(_norm(n))
    return out


def scenario_items(sid, doc_path=None, known=None):
    """The item names a scenario's **Items:** block lists, kept only when `known` (the rosters and every name a read
    recorded) holds them - the block is prose, and a word that is not an item must never join. -> [name] | None when
    the file will not read, or when no `known` set was given (REG-2784, the v3828 second eye: the default kept every
    prose word, the opposite of this rule - without the names it may keep, it keeps none and says UNKNOWN)"""
    if known is None:
        return None
    text = _doc(doc_path)
    if text is None:
        return None
    m = re.search(r"(?m)^### " + re.escape(sid) + r" .*?$(.*?)(?=^### |\Z)", text, re.S | re.M)
    block = m.group(1) if m else ""
    im = re.search(r"\*\*Items:\*\*(.*?)(?:\n\*\*|\Z)", block, re.S)
    out = []
    for line in (im.group(1).splitlines() if im else []):
        line = line.strip()
        if not line.startswith("- "):
            continue
        head = re.split(r"[:(]", line[2:], 1)[0]
        for part in re.split(r"\s*/\s*|,\s*|\s+and\s+|\s+or\s+|such as\s+", head):
            n = _norm(part.replace("A rare ring", "").replace("a rare helm", ""))
            if n and (known is None or n in known) and n not in out:
                out.append(n)
    return out


def hist_dir():
    """The reel folder root - the console's own rule (control_app.HIST_DIR: TV_HIST, else tv/frames/hist)."""
    return os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")


def _names_of(r):
    v = r.get("names")
    if isinstance(v, str):
        try:
            import ast as _ast
            v = _ast.literal_eval(v) if v.startswith("[") else [v]
        except (ValueError, SyntaxError):
            v = [v]
    return [_norm(x) for x in (v or []) if isinstance(x, str) and x.strip()]


def journal_paths(directory=None):
    """The live journal and its rotations. -> [path]"""
    if directory is None:
        import replay as _rp
        directory = os.path.dirname(_rp.JOURNAL)
    return sorted(glob.glob(os.path.join(directory, "sessions*.jsonl")))


def _triage_path():
    import retro_triage as _rt
    return _rt._store_path()


def _cap(r):
    c = r.get("captureTs")
    if isinstance(c, (int, float)) and not isinstance(c, bool) and c > 0:
        return int(c)
    if r.get("lane") in ("deep", "ocr", "known"):
        t = r.get("ts")                                   # a live read is written as it is taken
        return int(t) if isinstance(t, (int, float)) and not isinstance(t, bool) and t > 0 else None
    return None                                           # a later re-read without a capture time names no frame


def load_frames(paths=None, triage=None):
    """Every frame a read or the triage names, with its screens. -> ({(session, captureTs): {screens, reads, lanes}},
    deep rows by session for checks)"""
    frames = collections.defaultdict(lambda: {"screens": set(), "reads": 0, "lanes": collections.Counter(), "names": set(),
                                              "pics": set()})
    deep_by = collections.defaultdict(list)
    for p in (journal_paths() if paths is None else paths):
        try:
            fh = io.open(p, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                sid, lane = r.get("sessionId"), r.get("lane")
                if not sid:
                    continue
                if lane in ("deep", "deep-owed"):
                    deep_by[sid].append(r)
                if lane not in READ_LANES:
                    continue
                c = _cap(r)
                if c is None:
                    continue
                f = frames[(sid, c)]
                f["reads"] += 1
                f["lanes"][lane] += 1
                f["names"].update(_names_of(r))
                fid = r.get("frameId")
                if isinstance(fid, str) and re.match(r"^(\d+_\d+|reel_s_\d+_\d+/f_\d+)$", fid):
                    f["pics"].add(fid + ".jpg")
                if isinstance(r.get("scene"), str) and r.get("scene") and r.get("scene") != lane:
                    f["screens"].add(r["scene"])
    tri = None
    try:
        with io.open(_triage_path() if triage is None else triage, encoding="utf-8") as fh:
            tri = json.load(fh)
    except (OSError, ValueError):
        tri = None
    rows = tri.get("reels") if isinstance(tri, dict) and isinstance(tri.get("reels"), dict) else tri
    for reel, row in (rows.items() if isinstance(rows, dict) else ()):
        if not (isinstance(reel, str) and reel.startswith("reel_") and isinstance(row, dict)):
            continue
        for name, tab in (row.get("panelFrames") or {}).items():
            m = re.match(r"^f_(\d+)\.jpg$", str(name))
            if m and tab in _TRIAGE_STASH:
                f = frames[(reel[len("reel_"):], int(m.group(1)))]
                f["screens"].add("stash")
                f["pics"].add("%s/%s" % (reel, name))
    return frames, deep_by


#: REG-2784 (the v3828 second eye) - REC-03's own Expect: "every deep row of the session is mode 'warm' ... no 'oneshot'
#: rows, and no 'g5-primary' rows (if there are, EYES was not OFF)". Measured on his journal: warm 1,084 · empty 907 ·
#: g5-only 149 · g5-backup 12 · oneshot 7. A read the vision worker answered warm passes; a frame with nothing to read
#: (empty) called no worker and says nothing either way; a worker that died, a one-shot, or a read the backup had to
#: answer fails; a read another eye answered, a canned stub, or no mode at all is not a REC-03 read - UNKNOWN, never PASS.
_REC03_WARM = frozenset(("warm",))
_REC03_NEUTRAL = frozenset(("empty",))
_REC03_FAIL = frozenset(("oneshot", "error", "timeout", "g5-backup"))


def check_rec03(sessions, deep_by):
    """REC-03 against the record: in each session with 9 or more worker reads (enough to cross the 8-turn worker
    respawn), every one was answered by a warm worker and every commitment got its answer. The newest such session -
    by its LATEST recorded read (REG-2784: never its earliest, and a row with no time never drags it down) - decides;
    older ones are reported, not hidden. -> (verdict, why)"""
    long_ = []
    for sid in sessions:
        g = deep_by.get(sid) or []
        deep = [r for r in g if r.get("lane") == "deep"]
        worker = [r for r in deep if str(r.get("mode")) not in _REC03_NEUTRAL]
        if len(worker) < 9:
            continue
        owed = sum(1 for r in g if r.get("lane") == "deep-owed")
        modes = collections.Counter(str(r.get("mode")) for r in deep)
        ts = [int(r.get("ts") or 0) for r in g]
        t1 = max([t for t in ts if t > 0] or [0])
        long_.append((t1, sid, len(worker), owed, modes))
    if not long_:
        return "UNKNOWN", "no recorded session has 9 or more worker reads, so no read crossed a worker respawn"
    long_.sort(key=lambda x: (x[0], x[1]), reverse=True)
    t1, sid, n, owed, modes = long_[0]
    oneshot = sum(m.get("oneshot", 0) for _, _, _, _, m in long_)
    lost = sum(max(0, o - d) for _, _, d, o, _ in long_)
    why = ("newest long session %s: %d worker read(s), modes %s, %d commitment(s); across %d long session(s): %d oneshot "
           "read(s), %d commitment(s) never answered" % (sid, n, dict(modes), owed, len(long_), oneshot, lost))
    if not t1:
        return "UNKNOWN", why + " - no long session carries a read time, so none can be called the newest"
    if any(modes.get(m, 0) for m in _REC03_FAIL) or owed > n:
        return "FAIL", why
    other = sorted(m for m in modes if m not in _REC03_WARM | _REC03_NEUTRAL | _REC03_FAIL)
    if other:
        return "UNKNOWN", why + " - read(s) of mode %s are not REC-03 reads (another eye, a stub, or no mode)" % other
    return "PASS", why


def report(ids=None, doc_path=None, paths=None, triage=None, sample=5, rosters=None, hist=None):
    """-> [{id, about, screens, frames, sessions, reads, items, itemsRead, itemsNever, itemFrames, sample, onDisk,
    verdict, why}] in the document's order"""
    if not ids:
        ids = scenario_ids(doc_path)
        if ids is None:
            return [{"id": None, "verdict": "UNKNOWN", "why": "TESTING_PHASE.md would not read, so no scenario is known"}]
    ids = list(ids)
    frames, deep_by = load_frames(paths, triage)
    read_names = set()
    for f in frames.values():
        read_names |= f["names"]
    known_rosters = roster_names() if rosters is None else set(rosters)
    runewords = roster_names(only="runewords") if rosters is None else set(rosters) & roster_names(only="runewords")
    known = known_rosters | read_names
    root = hist or hist_dir()
    out = []
    for sid in ids:
        spec = SCENARIOS.get(sid)
        row = {"id": sid, "about": None, "screens": [], "frames": 0, "sessions": 0, "reads": 0, "sample": [],
               "items": [], "itemsRead": [], "itemsNever": [], "itemFrames": 0, "onDisk": 0, "verdict": "NOT WIRED", "why": "no screens declared for this scenario in scenario_frames.SCENARIOS"}
        if spec is None:
            out.append(row)
            continue
        row.update(about=spec["about"], screens=list(spec["screens"]))
        if spec.get("not_frames"):
            row.update(verdict="NOT FRAMES", why=spec["not_frames"])
            out.append(row)
            continue
        want = set(spec["screens"])
        hit = sorted(k for k, f in frames.items() if "*" in want or (f["screens"] & want))
        items = scenario_items(sid, doc_path, known)
        if items is None:
            row.update(verdict="UNKNOWN", why="TESTING_PHASE.md would not read, so its items are unknown")
            out.append(row)
            continue
        iset = set(items)
        # ⚠ A BASE READ BESIDE A RUNEWORD IS THAT RUNEWORD'S BASE. Looked at 14_1791910969555.jpg (MR-01's one frame):
        # a Spirit tooltip, whose second line reads "Monarch" - MR-01's white-base control it is not. So an item no
        # roster names (a base, a magic or rare name) does not join on a frame that also reads a runeword.
        named = known_rosters if known_rosters is not None else set()

        def _joins(k):
            got = frames[k]["names"] & iset
            if frames[k]["names"] & runewords:
                got = set(n for n in got if n in named)
            return got
        by_item = sorted(k for k in hit if _joins(k))
        seen = set()
        for k in by_item:
            seen |= _joins(k)
        # the sample is the scenario's OWN frames when its items were read, else frames of its screen
        pick = (by_item or hit)[-sample:]

        def _pic(k):
            have = [x for x in sorted(frames[k]["pics"]) if os.path.exists(os.path.join(root, x))]
            return have[0] if have else None
        row.update(frames=len(hit), sessions=len(set(s for s, _ in hit)),
                   reads=sum(frames[k]["reads"] for k in hit), items=items,
                   itemsRead=[n for n in items if n in seen], itemsNever=[n for n in items if n not in seen],
                   itemFrames=len(by_item),
                   sample=[_pic(k) or ("reel_%s · %d (picture not on disk)" % k) for k in pick],
                   onDisk=sum(1 for k in pick if _pic(k)))
        if not hit:
            row.update(verdict="NO FRAMES", why="no frame of his is labelled %s" % "/".join(spec["screens"]))
        elif sid == "REC-03":
            row["verdict"], row["why"] = check_rec03(set(s for s, _ in hit), deep_by)
        else:
            row.update(verdict="INDEXED",
                       why=("%d of its %d item(s) read on %d frame(s) of his%s; the expectation is checked by him or a law"
                            % (len(row["itemsRead"]), len(items), len(by_item),
                               (" - never read: " + ", ".join(row["itemsNever"][:4])) if row["itemsNever"] else ""))
                       if items else "no item of its list is in the rosters or any read - its screen's frames are named")
        out.append(row)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    ids = [a for a in argv if not a.startswith("--")]
    rows = report(ids or None)
    if as_json:
        print(json.dumps(rows, indent=1))
        return 0
    for r in rows:
        print("%-15s %-10s frames %5d  sessions %3d  reads %5d  %s" % (r["id"], r["verdict"], r["frames"], r["sessions"],
                                                                        r["reads"], r["why"]))
        if ids:
            print("    sample (%d of %d on disk):" % (r["onDisk"], len(r["sample"])))
            for s in r["sample"]:
                print("    " + s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
