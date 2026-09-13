#!/usr/bin/env python3
"""WHAT MAY LEAVE THE JOURNAL, AND WHY EVERY OTHER ROW STAYS. Writes nothing.

Konyo, 2026-09-13: *"it should all go through the river and end up in tombstone and then in
deleted after being extracted"*, and *"should be left with last 8 sessions/reels"*.

⚠⚠ THE REEL RIVER IS ALREADY FINISHED, AND THIS IS THE HALF THAT IS NOT. Measured 2026-09-13:
20 reels on disk, `ROUTED 20` — every one routed, which reel_router's own note calls "the REAL
tombstone" — and `TOMBSTONE 0`, which means none have LEFT THE DISK. That zero is CORRECT: the 20
are 8 he asked to keep + 9 the test suite pins + 3 still held, and retention refuses all three
groups for good reasons. There is nothing left for the REEL planner to release.

His shelf still shows **419 rows**, because the shelf lists JOURNAL sessions and a row outlives its
film. 2,893 journaled · 2,474 hidden as empty · 419 shown · **20 reels**. Roughly 195 of the shown
rows name film that no longer exists.

⚠⚠⚠ AND THIS MODULE DELETES NOTHING. `plan()` classifies and explains, exactly as
`reel_retention.plan()` does — "what may go, oldest first, and WHY every other reel stays. Writes
nothing." A journal row is his record of a night he played. The apply half is a separate decision
and it is HIS.

THE EXTRACTION RULE, and it is deliberately strict:

    RELEASABLE   footageState == "retired" — the film gave up its information and was THEN
                 released. That is the system's own proof that extraction happened, produced by
                 the retention lane, not by this module guessing.
    HELD         everything else, including rows with no film at all. "No film" is not "extracted";
                 it is an absence of evidence either way. [[unknown-stays-unknown]]

⚠ FOUR THINGS ARE NEVER RELEASABLE, whatever the state says:
    · the newest KEEP_RECENT sessions — his own number, and reel_retention already uses 8
    · any row whose reel still has film on disk — the river has not finished with it
    · any row whose reel the TEST SUITE opens by name — deleting one turns a real check into a
      permanent skip, which has already happened three times
    · any row that cannot be dated, because "newest 8" is meaningless without an order
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

#: his number, and the SAME one reel_retention keeps. Imported rather than re-typed — two copies
#: of a retention floor is how the two halves of one river start disagreeing. [[copy-drift]]
try:
    from reel_retention import KEEP_RECENT
except Exception:
    KEEP_RECENT = 8

#: the only state that proves the information was taken before the film went
EXTRACTED = "retired"


def _film_on_disk(sid, hist_dir):
    """Does this session's reel still hold frames? -> (bool, n)"""
    import glob
    d = os.path.join(hist_dir, "reel_" + str(sid))
    if not os.path.isdir(d):
        return False, 0
    n = len(glob.glob(os.path.join(d, "f_*.jpg")))
    return n > 0, n


def plan(sessions, hist_dir=None, keep_recent=KEEP_RECENT):
    """Classify every journal row. -> dict. WRITES NOTHING.

    sessions: the /api/sessions payload rows (already carry footageState/footageWhy).
    """
    hist_dir = hist_dir or os.path.join(HERE, "frames", "hist")
    try:
        import frame_authority as _fa
        pinned = set(_fa.test_referenced_reels() or ())
    except Exception:
        pinned = None            # UNKNOWN -> hold everything that might be a fixture

    rows = [s for s in (sessions or []) if isinstance(s, dict)]
    dated = [s for s in rows if isinstance(s.get("t0"), (int, float))]
    dated.sort(key=lambda s: s.get("t0") or 0, reverse=True)
    newest = {str(s.get("sessionId") or "") for s in dated[:max(0, int(keep_recent))]}

    release, keep = [], []
    for s in rows:
        sid = str(s.get("sessionId") or "")
        why = None
        if not sid:
            why = "this row carries no session id, so it can be neither dated nor matched to film"
        elif not isinstance(s.get("t0"), (int, float)):
            why = "this row cannot be dated, and 'the newest %d' is meaningless without an order" % keep_recent
        elif sid in newest:
            why = "one of the %d most recent runs — kept whatever its state says" % keep_recent
        elif pinned is None:
            why = "the fixture list could not be read, so every row is held rather than risk deleting one the suite opens by name"
        elif ("reel_" + sid) in pinned or sid in pinned:
            why = "the TEST SUITE opens this reel by name — releasing it turns a real check into a permanent skip"
        else:
            has, n = _film_on_disk(sid, hist_dir)
            if has:
                why = "its reel still holds %d frame(s) on disk — the river has not finished with it" % n
            elif str(s.get("footageState") or "") != EXTRACTED:
                why = ("footageState is %r, not %r — no film is not the same fact as extracted, "
                       "and an absence of evidence is not a proof"
                       % (str(s.get("footageState") or "none"), EXTRACTED))
        if why is None:
            release.append({"sessionId": sid, "t0": s.get("t0"),
                            "why": "film was retired after giving up its information: %s"
                                   % str(s.get("footageWhy") or "")[:90]})
        else:
            keep.append({"sessionId": sid, "t0": s.get("t0"), "why": why})

    release.sort(key=lambda r: r.get("t0") or 0)          # oldest first, like reel_retention
    return {"ok": True, "keepRecent": keep_recent, "rows": len(rows),
            "release": release, "keep": keep,
            "counts": {"release": len(release), "keep": len(keep)},
            "say": ("%d of %d journal row(s) have a proof of extraction and could be released; "
                    "%d stay. NOTHING was written." % (len(release), len(rows), len(keep)))}


def main(argv=None):
    import json
    import urllib.request
    port = os.environ.get("TV_PORT", "17772")
    with urllib.request.urlopen("http://127.0.0.1:%s/api/sessions" % port, timeout=120) as r:
        rows = json.loads(r.read().decode("utf-8", "replace")).get("sessions") or []
    p = plan(rows)
    print(p["say"])
    from collections import Counter
    print("\nWHY ROWS STAY (top reasons):")
    for w, n in Counter(k["why"][:72] for k in p["keep"]).most_common(8):
        print("   %5d  %s" % (n, w))
    print("\nRELEASABLE, oldest first (first 8 of %d):" % len(p["release"]))
    for r in p["release"][:8]:
        print("   %s" % r["sessionId"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
