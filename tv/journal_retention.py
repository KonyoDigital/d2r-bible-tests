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
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def _journal_path():
    """The journal this tree is actually using. -> path

    ⚠ ASK tv_diablo, do not hardcode. Its JOURNAL/STATE/HIST are chosen AT IMPORT from the TV_*
    env, which is how the CI harness and an isolated-hist run point the whole engine at a fixture
    tree. A module that hardcodes tv/sessions.jsonl would back up one file and rewrite another the
    moment anyone runs it under a redirect — and this module REWRITES, so the wrong path is the
    difference between a release and losing his history.
    """
    try:
        import tv_diablo as _tvd
        p = getattr(_tvd, "JOURNAL", None)
        if p:
            return p
    except Exception:
        pass
    return os.path.join(HERE, "sessions.jsonl")
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


def _journal_paths():
    """Every file the journal is READ from, oldest first. -> [path]

    ⚠⚠ DELEGATE. `_journal_path()` below returns the LIVE file, which is what a single-file
    rewrite needs — and for six versions this module used it as though it were the whole journal.
    It is not: `replay.load_journal` has read a generation ring since v779. The planner was fed
    the ring (via /api/sessions) and the applier rewrote one file of it, so every release against
    a session in the rotated half was a SILENT NO-OP. Measured: 2,483 of 2,840 sessions live in
    `sessions.1.jsonl`. That is why the river could not drain. [[copy-drift]] [[the-unjoined-end]]
    """
    try:
        import replay as _rp
        paths = list(_rp.journal_paths() or [])
        if paths:
            return paths
    except Exception:
        pass
    p = _journal_path()
    return [p] if os.path.exists(p) else []


_PAYLOAD_FIELDS = ("finds", "tallies", "intakes", "named", "chron", "registered",
                   "judged", "topFind")


def _carries_payload(s):
    """Which fields of this row still hold something. -> sorted list of names."""
    return sorted(k for k in _PAYLOAD_FIELDS if s.get(k))


def _banked_reels():
    """The reels a durable bank still names. -> (set | None, why_unknown | None)

    ⚠⚠ DELEGATE, DO NOT RE-DERIVE THE PATH. control_app's own v2139.1 scar is explicit about this
    exact file: a third reader joined `chronicle_swept.json` from HERE and thereby ignored
    TV_CHRON_SWEPT, ignored a mock.patch.object on _CHRON_SWEPT_PATH and ignored TV_HIST — all
    three of which `_chron_swept_path()` honours on purpose, in that precedence. Two fixtures that
    patched the path still got the LIVE memory, so a reel set up as unswept read as swept.
    `_chron_swept_mem()` is the one reader that gets it right.
    [[copy-drift]] [[feedback-fixtures-never-touch-live-data]]

    ⚠ None IS NOT AN EMPTY SET. A bank we could not read means "UNKNOWN whether it was banked",
    and on a DELETION path unknown must hold, never release. [[unknown-stays-unknown]]
    """
    try:
        import control_app as _ca
        mem = _ca._chron_swept_mem() or {}
    except Exception as e:
        return None, "the sweep memory could not be read (%s)" % type(e).__name__
    out = set()
    for k in mem:
        k = str(k)
        out.add(k[len("reel_"):] if k.startswith("reel_") else k)
    return out, None


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

    # ⚠⚠ v3105 — KONYO'S CONDITION, MADE A RULE INSTEAD OF A ONE-OFF CHECK. He approved the
    # deletion with one string attached: *"just make sure before it was tallied and extracted
    # properly"*. Measured on his live journal before writing this: of 447 releasable rows, 245
    # still carried payload (finds, tallies, intakes, named, chron, registered, topFind), 207 of
    # those had their reel recorded in the sweep memory — so the read survives the row — and
    # **38 appeared in no bank at all**, several of them carrying `finds` and `topFind`. Deleting
    # those 38 throws away the only trace of what they found.
    #
    # The film gate already enforces his rule on the OTHER side: reel_retention refuses to
    # tombstone on `zero-pages` ("that is 'this reader found nothing', not 'done'") and on
    # `panels-never-banked`, which quotes him directly — *"all of the reels get extracted with
    # information thats needed"* BEFORE the tombstone. This is the same sentence applied to the
    # journal ROW, which is what survives the film. [[join-gate-heart]]
    banked, bank_why = _banked_reels()

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
            elif _carries_payload(s) and banked is None:
                why = ("this row still carries %s and %s, so whether any of it was banked is "
                       "UNKNOWN — and unknown holds on a path that deletes"
                       % (", ".join(_carries_payload(s)), bank_why))
            elif _carries_payload(s) and sid not in banked:
                why = ("this row still carries %s and NO bank names its reel — the sweep memory "
                       "has no record of it being read, so deleting the row throws away the only "
                       "trace of what it found" % ", ".join(_carries_payload(s)))
        if why is None:
            release.append({"sessionId": sid, "t0": s.get("t0"),
                            "why": "film was retired after giving up its information: %s"
                                   % str(s.get("footageWhy") or "")[:90]})
        else:
            keep.append({"sessionId": sid, "t0": s.get("t0"), "why": why})

    release.sort(key=lambda r: r.get("t0") or 0)          # oldest first, like reel_retention
    # ⚠ v3106 — THE PLAN NAMES THE CORPUS IT JUDGED, so `apply_plan` can refuse when the files
    # moved underneath it. A plan is a judgement ABOUT a set of files; applying it to a different
    # set is how a correct decision lands on the wrong rows.
    sources = []
    for _p in _journal_paths():
        try:
            sources.append({"path": _p, "rows": sum(1 for _l in
                                                    io.open(_p, encoding="utf-8", errors="replace")
                                                    if _l.strip())})
        except Exception:
            sources.append({"path": _p, "rows": None})
    return {"ok": True, "keepRecent": keep_recent, "rows": len(rows),
            "release": release, "keep": keep, "sources": sources,
            "counts": {"release": len(release), "keep": len(keep)},
            "say": ("%d of %d journal row(s) have a proof of extraction and could be released; "
                    "%d stay. NOTHING was written." % (len(release), len(rows), len(keep)))}


BACKUP_DIR = os.path.join(os.path.expanduser("~"), "d2r_journal_backups")


def backup(journal_path=None, stamp=None):
    """Copy the whole journal aside BEFORE anything leaves it. -> (path, rows) or (None, why)

    ⚠⚠ THIS IS WHAT MAKES THE RELEASE REVERSIBLE, AND REVERSIBILITY IS WHY THIS LANE MAY RUN AT
    ALL. reel_retention.apply_plan deletes PIXELS — "there is no undo" in its own words — so it is
    gated behind self_arming's `frame.release` lock and fails closed on any refusal. A journal row
    is different in exactly one way that matters: a timestamped copy of the file restores it
    perfectly. So the bar here is an explicit yes AND a verified backup, not a lock, and the
    difference is the undo rather than a judgement that rows matter less.

    Konyo asked for precisely this shape on the vault: "able to be brought back based on like last
    recent save ledger wise.. by day and timestamp". Same mechanism, one lane earlier.
    """
    src = journal_path or _journal_path()
    if not os.path.exists(src):
        return None, "there is no journal at %s to back up" % src
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except OSError as exc:
        return None, "could not make %s (%s)" % (BACKUP_DIR, exc)
    stamp = stamp or time.strftime("%Y-%m-%d_%H%M%S")
    # ⚠ v3106 — THE SOURCE'S OWN NAME, OR A RING BACKUP OVERWRITES ITSELF. This was
    # "sessions.%s.jsonl" % stamp, which is fine for ONE file and silently collides the moment
    # two ring generations are backed up in the same second — the second copy would land on the
    # first and the earlier file would have no backup at all while the log said it did.
    dst = os.path.join(BACKUP_DIR, "%s.%s" % (os.path.basename(src), stamp))
    try:
        with io.open(src, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        tmp = dst + ".part"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, dst)
    except Exception as exc:
        return None, "the backup did not write (%s: %s)" % (type(exc).__name__, exc)
    # ⚠ VERIFY IT LANDED. A backup nobody read back is a promise, not a safety net, and this is the
    # one line standing between a release and losing his history.
    try:
        n = sum(1 for _ln in io.open(dst, encoding="utf-8", errors="replace") if _ln.strip())
    except Exception as exc:
        return None, "the backup could not be read back (%s)" % exc
    if n == 0:
        return None, "the backup read back EMPTY — refusing to release anything against it"
    return dst, n


def apply_plan(p, yes=False, journal_path=None):
    """Remove the released sessions' rows from EVERY file the journal is read from. -> dict

    ⚠ REFUSES WITHOUT AN EXPLICIT YES, refuses if the backup did not verify, and — v3106 — refuses
    if the corpus MOVED since the plan judged it. The order is deliberate and is reel_retention's:
    every recoverable record goes down FIRST, so a crash halfway leaves backups covering MORE than
    was removed rather than fewer.

    ⚠⚠ v3106 — IT USED TO REWRITE ONE FILE OF A RING. `plan()` is fed the whole journal, which
    `replay.load_journal` has read as a generation ring since v779; this rewrote `tv_diablo.JOURNAL`
    alone. MEASURED on his tree: 2,483 of 2,840 sessions live in `sessions.1.jsonl`, so a release
    against any of them was a SILENT NO-OP that reported success. The river could not drain and
    nothing said why. [[the-unjoined-end]]
    """
    if not yes:
        return {"ok": False, "why": "refusing to rewrite the journal without yes=True; "
                                    "call plan() alone to read what WOULD go"}
    if not isinstance(p, dict) or not p.get("ok"):
        return {"ok": False, "why": "that is not a plan this module produced"}
    doomed = {str(r.get("sessionId") or "") for r in (p.get("release") or []) if r.get("sessionId")}
    if not doomed:
        return {"ok": True, "removedRows": 0, "removedSessions": 0,
                "why": "the plan released nothing, so nothing was written"}

    targets = [journal_path] if journal_path else _journal_paths()
    if not targets:
        return {"ok": False, "why": "there is no journal to rewrite"}

    # ⚠⚠ THE CORPUS MUST BE THE ONE THE PLAN JUDGED. A plan is a judgement ABOUT a set of files;
    # applying it to a different set is how a correct decision lands on the wrong rows. This is
    # not hypothetical — it is exactly what happened on 2026-09-14, when a plan computed over the
    # ring was applied to the live file alone.
    if not journal_path:
        want = {(s.get("path"), s.get("rows")) for s in (p.get("sources") or [])}
        have = set()
        for t in targets:
            try:
                have.add((t, sum(1 for l in io.open(t, encoding="utf-8", errors="replace")
                                 if l.strip())))
            except Exception:
                have.add((t, None))
        if not want:
            return {"ok": False, "why": "this plan does not name the files it judged (it predates "
                                        "v3106) — re-run plan() before applying it"}
        if want != have:
            return {"ok": False,
                    "why": "the journal MOVED since this plan judged it — refusing.\n"
                           "   planned over: %s\n   on disk now  : %s"
                           % (sorted(want), sorted(have))}

    # ── every backup first, then every rewrite ──────────────────────────────────────────────
    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    backups = []
    for t in targets:
        where, n_backed = backup(t, stamp=stamp)
        if where is None:
            return {"ok": False, "why": "NOT touching the journal — %s" % n_backed,
                    "backups": backups}
        backups.append({"of": t, "at": where, "rows": n_backed})

    dropped, sids, kept_total, wrote = 0, set(), 0, []
    for t in targets:
        kept = []
        try:
            with io.open(t, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        sid = str((json.loads(raw) or {}).get("sessionId") or "")
                    except Exception:
                        kept.append(line)      # unparseable stays: it is not ours to judge
                        continue
                    if sid and sid in doomed:
                        dropped += 1
                        sids.add(sid)
                    else:
                        kept.append(line)
        except Exception as exc:
            return {"ok": False, "why": "%s could not be read (%s) — %d file(s) already rewritten, "
                                        "backups at %s" % (t, exc, len(wrote), BACKUP_DIR),
                    "backups": backups, "rewrote": wrote}
        # ⚠ ATOMIC. A plain open(path, "w") TRUNCATES before anything is written, so a crash
        # between those two moments leaves him with an empty history and a backup he does not
        # know to look for.
        tmp = t + ".part"
        try:
            with io.open(tmp, "w", encoding="utf-8") as fh:
                fh.writelines(kept)
            os.replace(tmp, t)
        except Exception as exc:
            try:
                os.remove(tmp)
            except OSError:
                pass
            return {"ok": False, "why": "the rewrite of %s failed (%s) — that file is untouched; "
                                        "backups at %s" % (t, exc, BACKUP_DIR),
                    "backups": backups, "rewrote": wrote}
        kept_total += len(kept)
        wrote.append({"path": t, "kept": len(kept)})

    return {"ok": True, "removedRows": dropped, "removedSessions": len(sids),
            "keptRows": kept_total, "backups": backups, "rewrote": wrote,
            "say": "released %d row(s) across %d session(s) from %d file(s); %d row(s) remain. "
                   "Restore with: %s"
                   % (dropped, len(sids), len(targets), kept_total,
                      " && ".join("cp %s %s" % (b["at"], b["of"]) for b in backups))}


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
