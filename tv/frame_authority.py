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
    try:
        with open(os.path.join(root, fn), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


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
        blob = _load(root, fn)
        if blob is None:
            ok = False
            seen[fn] = None
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
