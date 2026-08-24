#!/usr/bin/env python3
"""THE ONE DELETION AUTHORITY over his footage.

Three things could delete frames or reels, and each carried its own private idea of "safe":

  · control_app._prune_once  — kept a frame only when it LOOKED different from the one before
                               (sig_diff <= 0.02, whole frame, tol=28). A hover tooltip — the ONLY
                               place D2R ever writes an item name — moves that number by LITERALLY
                               ZERO. Measured on his own reel: three frames naming three different
                               grand charms are pairwise 0.00000 apart. v2058 turned it off after a
                               replay showed it dropping 67 frames including FOUR witness frames,
                               each the second session for one of his seven owned rows.
  · reel_retention           — asked the vault lane and the durable stores. The right questions, in
                               the one place the other two never called.
  · space_warden             — build artifacts only, behind a NEVER list. Correct, and out of scope.

None of them asked the same question, and only one of them asked the vault lane at all.
This module is that one question, asked once, in one place.

THE RULE, and it is his, in his own words:

    "after the sweep ... data needs to be extracted and ledgered and counted for items as
     witnesses so when they get pruned they continue to exist on record"
    "the ledger should tell us when it was seen by AI so we can see visually in retro and
     visually debug in retro if needed surgically anything"

Those two pull against each other, and the resolution IS the design: a frame that WITNESSED a row is
the visual proof of that row and is never deleted; a frame from a sealed reel that witnessed nothing
has already given up everything it had. So the question is never "does this frame look like the last
one" — it is **IS THIS FRAME EVIDENCE**. sig_diff cannot answer that at any tolerance, which is why
replacing it was the fix rather than retuning it.

Every predicate errs toward KEEPING. An unreadable store, an unparsable name, a missing index all
resolve to "do not delete". "I could not tell" must never mean "delete it", because there is no
un-delete for footage — the same asymmetry that makes the throw-out bar higher than the keep bar.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:                                   # the report below prints a box-file glyph, and a CLI that
    from console_safe import enable    # crashes while REPORTING makes a clean tree exit non-zero
    enable()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

KEEP_RECENT = 5            # never touch the newest five reels, whatever any ledger says
DURABLE_STORES = ("vault_accum.json", "vault_seen.json")
SEAL_STORE = "vault_swept.json"


def _load(root, fn):
    """None means COULD NOT READ, which is not the same as empty. Callers must treat it as a hold."""
    return _load_state(root, fn)[0]


def _load_state(root, fn):
    """(blob, state) where state is 'absent' | 'ok' | 'unreadable'.

    v2079 — AND THE THREE ARE NOT TWO. `_load` folded ABSENT and UNREADABLE into one None, and
    `witness_index` then reported ok=False for both. On a tree that has simply never run a vault
    sweep — every test fixture, and any fresh install — the durable stores are absent, so the
    authority declared itself unreliable and a caller that honours `ok` holds every reel forever.

    That is not a hypothetical: it went red across ~17 reel_retention cases within one gate run of
    the change that started honouring `ok`. The over-correction is the same defect as the one it
    was correcting, pointed the other way — "I could not read it" and "there is nothing to read"
    are opposite facts and neither may borrow the other's answer.
    [[unknown-stays-unknown]] [[gate-blind-to-unexercised-input]]
    """
    fp = os.path.join(root, fn)
    if not os.path.exists(fp):
        return {}, "absent"
    try:
        with open(fp, encoding="utf-8") as fh:
            return json.load(fh), "ok"
    except Exception:
        return None, "unreadable"


def _rows_of(blob):
    if not isinstance(blob, dict):
        return []
    rows = blob.get("owned") if "owned" in blob else blob.get("rows")
    return [r for r in (rows or []) if isinstance(r, dict)]


def witness_index(root=None):
    """Which FRAMES and which SESSIONS are named as witnesses in the durable stores.

    A witness frame is the pixels behind a row he can see in the vault. Deleting one does not make
    the row wrong — the row survives, that is the point of extracting — but it destroys the only
    way to ever answer "show me why you think I own this", which is the retro-debugging he asked
    for by name.

    `ok` is False when ANY store was unreadable. A caller that deletes on a partial index would be
    deleting on the strength of a file it could not open.
    """
    root = root or HERE
    frames, sessions, ok, seen = set(), set(), True, {}
    for fn in DURABLE_STORES:
        blob, state = _load_state(root, fn)
        if state == "unreadable":
            # Only THIS makes the index partial. An absent store contributes nothing and that is a
            # measurement, not a gap — see _load_state.
            ok = False
            seen[fn] = None
            continue
        if state == "absent":
            seen[fn] = 0
            continue
        n = 0
        for r in _rows_of(blob):
            for w in (r.get("witnesses") or []):
                if not isinstance(w, dict):
                    continue
                if w.get("frame"):
                    frames.add(os.path.basename(str(w["frame"])))
                    n += 1
                if w.get("session"):
                    sessions.add(str(w["session"]))
        seen[fn] = n
    return {"frames": frames, "sessions": sessions, "ok": ok, "perStore": seen}


def sealed_sessions(root=None):
    """Sessions the vault sweep has SEALED — it read what there was to read and said so.

    Returns (mapping, ok). A seal is not permanent: v2002 stamps the reader on it, so a newer
    VAULT_PROMPT_VER reopens the reel by itself. Deleting a sealed reel's frames FORECLOSES that
    reopen, which is why sealing alone never authorises deletion here — it is one of three
    conditions, not the verdict.
    """
    blob = _load(root or HERE, SEAL_STORE)
    if not isinstance(blob, dict):
        return {}, False
    return blob, True


def _session_of(path):
    b = os.path.basename(str(path or "").rstrip("/"))
    return b[len("reel_"):] if b.startswith("reel_") else b


def _reel_ts(reel_dir):
    """Sort key: the epoch ms in reel_s_<ms>_<n>. A name that will not parse sorts NEWEST, so it is
    the last thing anyone deletes rather than the first."""
    try:
        return int(os.path.basename(reel_dir).split("_")[2])
    except Exception:
        return float("inf")


def recent_reels(hist_dir, keep=KEEP_RECENT):
    """The newest `keep` reel directories — held whatever the ledgers say, because the sweep that
    would extract them may simply not have run yet."""
    reels = [d for d in glob.glob(os.path.join(hist_dir, "reel_*")) if os.path.isdir(d)]
    return set(sorted(reels, key=_reel_ts)[-keep:]) if reels else set()


def frame_verdict(frame_path, sealed=None, wit=None, recent=None):
    """MAY this one frame be deleted? Returns (bool, why) and the why is written for him, not for a log.

    Four ways to be held, and each is a different thing not being true yet:
      · its reel is one of the newest              the sweep may not have run
      · its reel is not sealed                     evidence not extracted; deleting loses it
      · it is named as a witness                   it is the visual proof of a row he can see
      · anything above could not be read           an unreadable store can only ever HOLD
    """
    if sealed is None or wit is None:
        raise ValueError("frame_verdict needs the indexes passed in — reading them per frame would "
                         "ask the disk thousands of times and let them drift mid-pass")
    reel_dir = os.path.dirname(os.path.abspath(frame_path))
    sess = _session_of(reel_dir)
    if recent and reel_dir in recent:
        return False, "one of the newest %d recordings — nothing is pruned from those" % KEEP_RECENT
    if not wit.get("ok"):
        return False, ("a durable store could not be read (%s), so the witness list is incomplete "
                       "and every frame is treated as evidence" % ", ".join(
                           k for k, v in (wit.get("perStore") or {}).items() if v is None))
    if sess not in (sealed or {}):
        return False, ("recording %s is not sealed — the sweep has not said it read everything "
                       "here, so these pixels may be the only copy of a name" % sess)
    if os.path.basename(frame_path) in (wit.get("frames") or set()):
        return False, ("this frame is a WITNESS behind a row in his vault — it is the only way to "
                       "ever show him why that row is there")
    return True, "recording %s is sealed and this frame witnessed nothing" % sess


def plan_frames(hist_dir, root=None, keep=KEEP_RECENT):
    """What a witness-aware prune WOULD free. Reports; deletes nothing.

    Reporting rather than acting is deliberate: this replaces a deleter that ran automatically and
    was wrong, and the first thing its replacement should do is be readable.
    """
    sealed, seal_ok = sealed_sessions(root)
    wit = witness_index(root)
    recent = recent_reels(hist_dir, keep)
    out = {"prunable": [], "heldBy": {}, "bytes": 0, "kept": 0, "scanned": 0,
           "sealOk": seal_ok, "witnessOk": wit["ok"],
           "witnessFrames": len(wit["frames"]), "sealedSessions": len(sealed)}
    if not seal_ok:
        out["say"] = ("%s could not be read, so NOTHING is prunable — a prune that cannot tell a "
                      "sealed recording from an unswept one is the prune that ate the names" % SEAL_STORE)
        return out
    for d in sorted(glob.glob(os.path.join(hist_dir, "reel_*")), key=_reel_ts):
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.jpg"))):
            out["scanned"] += 1
            ok, why = frame_verdict(f, sealed, wit, recent)
            if ok:
                try:
                    out["bytes"] += os.path.getsize(f)
                except OSError:
                    continue
                out["prunable"].append(f)
            else:
                out["kept"] += 1
                key = why.split("—")[0].strip()
                out["heldBy"][key] = out["heldBy"].get(key, 0) + 1
    out["say"] = ("%d of %d frame(s) could be freed (%.2f GB). %d held, and every witness frame "
                  "behind his vault rows is among them."
                  % (len(out["prunable"]), out["scanned"], out["bytes"] / 1e9, out["kept"]))
    return out


def test_referenced_reels(repo=None):
    """Reel ids the TEST SUITE opens by name. A reel a test reads is a FIXTURE, whatever the ledgers
    say about it.

    v2069 — MEASURED, after the fact, on a prune I had already run. Six reels were deleted as
    "sealed by both lanes, has given up its information" and THREE of them were named by
    tv/test_control.py. The suite did not go red: those tests are written to skipTest when the
    footage is absent, so a real check silently became a permanent skip — a gate that always skips
    is the same defect as one that is always green.

    It had happened twice before and been absorbed: the suite already carries two cases marked
    "fixture reel ... was pruned — PERMANENTLY skipped in both venues". Nobody was wrong at any
    step, which is exactly why it kept happening — the deleter asked the ledgers and the ledgers
    have no idea a test exists.

    Only REAL reel ids count (a 10-16 digit epoch): tests build their own throwaway dirs called
    reel_s_1_1, and holding those would be holding nothing.

    ⚠ AND A TEST LITERAL CAN CLAIM REAL FOOTAGE BY ACCIDENT. This scan cannot tell a reel a test
    READS from one a test merely NAMES. v2071 wrote `reel_s_1787523300658_1` into a guard as an
    illustration, and the orphan fold minted that exact directory from the same t0 an hour later —
    so retention began holding 3.15 GB of his footage with the reason "the TEST SUITE opens this
    reel", which was false. It errs toward KEEPING, so nothing was endangered; what was wrong was
    the REASON, and a wrong reason is how a real hold later gets dismissed as noise.

    Use a stamp no recording can carry (the v2071 guards now use 1500000000000 — 2017) whenever a
    test SYNTHESISES a reel name rather than pointing at footage on disk.
    """
    import re
    root = repo or os.path.dirname(HERE)
    # plan() asks this for every run and the suite file alone is ~0.9 MB — 28 ms a call, which is
    # nothing once and 2.8 s across a hundred plans. Keyed on the files' (size, mtime) so an edited
    # test is picked up immediately rather than cached into invisibility.
    try:
        stamp = tuple(sorted(
            (f, os.stat(f).st_size, int(os.stat(f).st_mtime))
            for pat in ("tv/test_*.py", "tests/*.spec.ts", "tests/*.ts", "tv/*_test.py")
            for f in glob.glob(os.path.join(root, pat))))
    except OSError:
        stamp = None
    cached = globals().get("_FIXTURE_CACHE")
    if stamp is not None and cached and cached[0] == stamp:
        return set(cached[1])
    out = set()
    for pat in ("tv/test_*.py", "tests/*.spec.ts", "tests/*.ts", "tv/*_test.py"):
        for f in glob.glob(os.path.join(root, pat)):
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    src = fh.read()
            except OSError:
                continue
            out.update(re.findall(r"reel_s_\d{10,16}_\d+", src))
    if stamp is not None:
        globals()["_FIXTURE_CACHE"] = (stamp, frozenset(out))
    return out


def loose_frames(hist_dir):
    """Frames sitting DIRECTLY in hist/, belonging to no reel — and therefore to no authority.

    v2069 — MEASURED on his tree the night this was written: 3,420 loose .jpg files, 3.41 GB, which
    is more than a third of all his footage. Every deleter was blind to them by construction:
    reel_retention iterates `reel_*` directories, this module globbed `hist/reel_*`, and
    space_warden has tv/frames on its NEVER list. So a third of the disk was invisible to the three
    things whose whole job is deciding what may go — not protected, just unseen, which is worse
    because it reads as protected.

    They are two different populations and the difference decides everything:
      · `f_<ms>.jpg`      an ungrouped RECORDING. The indexer never turned it into a reel, so no
                          lane has swept it and it may hold names nothing has read.
      · `<n>_<ms>.jpg`    probe / extract artifacts from the free pixel lane.

    This REPORTS them and refuses all of them. Classifying an ungrouped recording is a different
    job — it needs the indexer, not a deleter — and until that exists "I do not know what this is"
    must resolve to KEEP. [[unknown-stays-unknown]]
    """
    import re
    out = {"recording": [], "artifact": [], "bytes": 0, "recordingBytes": 0, "artifactBytes": 0}
    try:
        names = [f for f in os.listdir(hist_dir)
                 if f.endswith(".jpg") and os.path.isfile(os.path.join(hist_dir, f))]
    except OSError as e:
        return dict(out, ok=False, say="cannot read %s: %s" % (hist_dir, e))
    for f in names:
        try:
            n = os.path.getsize(os.path.join(hist_dir, f))
        except OSError:
            continue
        out["bytes"] += n
        if re.match(r"f_\d{10,16}\.jpg$", f):
            out["recording"].append(f)
            out["recordingBytes"] += n
        else:
            out["artifact"].append(f)
            out["artifactBytes"] += n
    out["ok"] = True
    out["say"] = ("%d loose frame(s) belong to no reel (%.2f GB): %d look like an UNGROUPED "
                  "RECORDING (%.2f GB) that no lane has swept, %d look like probe artifacts "
                  "(%.2f GB). NONE is offered for deletion — a frame nothing has classified is not "
                  "a frame anything may delete."
                  % (len(names), out["bytes"] / 1e9,
                     len(out["recording"]), out["recordingBytes"] / 1e9,
                     len(out["artifact"]), out["artifactBytes"] / 1e9)) if names else \
                 "no loose frames — every frame on disk belongs to a reel"
    return out


def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    p = plan_frames(hist)
    print("\U0001f5c3  THE ONE DELETION AUTHORITY — plan only, nothing is deleted here")
    print("   sealed recordings : %d" % p["sealedSessions"])
    print("   witness frames    : %d %s" % (p["witnessFrames"],
                                            "" if p["witnessOk"] else "(INCOMPLETE — a store would not read)"))
    print("   %s" % p["say"])
    for k, n in sorted(p["heldBy"].items(), key=lambda kv: -kv[1]):
        print("     held  %5d  %s" % (n, k))
    lf = loose_frames(hist)
    print("\n\u26a0  BELONGING TO NO REEL, AND THEREFORE TO NO AUTHORITY:")
    print("   %s" % lf.get("say"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
