"""ONE way to address a frame, because three ad-hoc ones invented three crises in a day.

WHY THIS EXISTS. A frame in this tree is referred to in THREE shapes, and every measurement that
knew only one of them produced an alarming number that was false:

    <n>_<ms>                        e.g. 21_1787522052389      (journal frameId, no extension)
    f_<ms>.jpg                      e.g. f_1788202324097.jpg   (top-level capture)
    <reel>/f_<ms>.jpg               e.g. reel_s_1784984019250_95276/f_1784984201778

Measured 2026-09-01, each of these was reported to Konyo before being checked, and each was wrong:

    "45% of cited frames are gone from disk"       -> resolver tested only `k == fid`
    "48% carry a reel id where a frame belongs"    -> they are PATHS, which carry more, not less
    "100% of named claims are unprovable"          -> endswith("/"+stem) needs a directory, and
                                                      top-level files have none

With a correct two-way index - full relative path AND bare stem - **every cited frame resolves.
0 gone, in both the named and unnamed sets.** There are no orphaned frameIds and no unprovable
claims. The corpus was never the problem; the questions were.

⚠ THE POINT IS NOT THE DATA, IT IS THE ARITHMETIC. A resolver that silently fails to match
answers "missing", and "missing" is indistinguishable from "deleted" to every caller. That is how
a healthy 9.6 GB archive read as 45% rotted three times in one evening.
[[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]
"""

import os

# a plausible capture epoch in ms: 2001-09-09 .. 2033-05-18. Wide on purpose - this rejects a
# reel's random suffix (5 digits) and an index (1-2 digits), not a real timestamp.
_MIN_TS_DIGITS = 12
_MAX_TS_DIGITS = 14


def timestamp_of(frame_ref):
    """The capture ms inside any of the three shapes. -> int | None.

    None means NOT ESTABLISHED. It never guesses: `reel_s_1788190210097_78660` has two numeric
    chunks and the LAST one is a random suffix, so a naive rsplit returns 78660 - a 1970
    timestamp presented as real. Only chunks of plausible epoch length are accepted.
    """
    if not frame_ref:
        return None
    base = str(frame_ref).replace("\\", "/")
    base = base.rsplit("/", 1)[-1]          # a path's frame is its last segment
    for chunk in reversed(base.replace(".", "_").split("_")):
        # ⚠ TAKE THE LEADING DIGIT RUN, not the whole chunk. 42 rows in his journal carry a
        # suffix - `15_1787496136628#v` - and a bare isdigit() test refuses them outright. The
        # timestamp is right there; refusing it is honest but needlessly lossy.
        run = ""
        for ch in chunk:
            if ch.isdigit():
                run += ch
            else:
                break
        if _MIN_TS_DIGITS <= len(run) <= _MAX_TS_DIGITS:
            try:
                return int(run)
            except ValueError:
                return None
    return None


def reel_of(frame_ref):
    """The reel a path-shaped ref names. -> str | None (a bare ref names no reel)."""
    if not frame_ref:
        return None
    s = str(frame_ref).replace("\\", "/")
    if "/" not in s:
        return None
    head = s.rsplit("/", 1)[0].rsplit("/", 1)[-1]
    return head or None


def stem_of(frame_ref):
    """The bare filename without directory or extension."""
    if not frame_ref:
        return ""
    s = str(frame_ref).replace("\\", "/").rsplit("/", 1)[-1]
    return os.path.splitext(s)[0]


class Index(object):
    """A resolver over one frame root. Built once, asked many times.

    Indexes BOTH ways a frame is addressed, because that is the whole point: by full relative
    path, and by bare stem. A stem can be ambiguous (the same capture ms under two reels); the
    index keeps every hit and `resolve` prefers an exact path match before falling back.
    """

    def __init__(self, root):
        self.root = root
        self.by_path = {}
        self.by_stem = {}
        self.files = 0
        self.bytes = 0
        if not root or not os.path.isdir(root):
            return
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root).replace("\\", "/")
                self.by_path[rel] = full
                self.by_stem.setdefault(stem_of(rel), []).append(rel)
                self.files += 1
                try:
                    self.bytes += os.path.getsize(full)
                except OSError:
                    pass

    def resolve(self, frame_ref):
        """-> the relative path on disk, or None. Exact path wins; stem is the fallback."""
        if not frame_ref:
            return None
        f = str(frame_ref).replace("\\", "/").strip()
        for cand in (f, f + ".jpg", f + ".png"):
            if cand in self.by_path:
                return cand
        hits = self.by_stem.get(stem_of(f)) or []
        if not hits:
            return None
        if len(hits) == 1:
            return hits[0]
        # ambiguous: if the ref names a reel, honour it; otherwise refuse rather than pick
        r = reel_of(f)
        if r:
            for h in hits:
                if h.startswith(r + "/"):
                    return h
        return None

    def exists(self, frame_ref):
        return self.resolve(frame_ref) is not None


def cited_frames(rows):
    """Split a journal into the frames it cites, by whether the row NAMED an item.

    -> (named:set, other:set). A prune gate must never delete anything in `named` - that is the
    receipt for a claim. `other` is fair game once its reel is sealed.
    """
    named, other = set(), set()
    for r in (rows or []):
        fid = r.get("frameId") or r.get("frame")
        if not fid:
            continue
        (named if (r.get("items") or r.get("names")) else other).add(str(fid))
    return named, other


def prunable(index, rows):
    """Which files on disk no claim depends on. -> (prunable:list, protected:int, why)

    The receipt rule, stated once: a frame cited by a row that NAMED an item is PROOF of that
    claim and may not be deleted while the claim stands. Everything else is prunable.
    """
    named, _other = cited_frames(rows)
    protect = set()
    for fid in named:
        hit = index.resolve(fid)
        if hit:
            protect.add(hit)
    out = [p for p in index.by_path if p not in protect]
    return out, len(protect), ("%d file(s) on disk; %d hold the proof of a named claim and are "
                               "protected; %d prunable" % (index.files, len(protect), len(out)))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import io as _io, json as _json, sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import control_app as ca
    idx = Index(ca.HIST_DIR)
    rows = []
    for p in ca._journal_ring():
        if not os.path.isfile(p):
            continue
        with _io.open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(_json.loads(line))
                except Exception:
                    pass
    named, other = cited_frames(rows)
    gone_named = [f for f in named if not idx.exists(f)]
    gone_other = [f for f in other if not idx.exists(f)]
    pr, protected, why = prunable(idx, rows)
    print("frames on disk : %d  (%.2f GB)" % (idx.files, idx.bytes / 1e9))
    print("journal rows   : %d across the ring" % len(rows))
    print("cited by a NAMED row : %d   unresolvable: %d" % (len(named), len(gone_named)))
    print("cited by any other   : %d   unresolvable: %d" % (len(other), len(gone_other)))
    print(why)
