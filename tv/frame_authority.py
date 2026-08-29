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
    absent = 0
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
            absent += 1
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
    # v2080 — `ok` alone is not enough for a FRAME deleter, and splitting absent from unreadable
    # exposed that. `ok` answers "is my picture complete"; a tree where NO durable store exists has
    # a complete picture of nothing, and every frame then reads as "witnessed nothing" — which for
    # this module means DELETABLE. That released frames the pre-split code held, and put the
    # frame-level authority in direct contradiction with reel_retention, which holds the very same
    # reel because its sweep read rows that reached no store.
    # `haveIndex` is the missing fact: is there anything here that COULD name a witness. Without
    # one, "not a witness" is unprovable rather than false, and this module's own rule is that
    # everything errs toward keeping. [[unknown-stays-unknown]]
    return {"frames": frames, "sessions": sessions, "ok": ok, "perStore": seen,
            "haveIndex": absent < len(DURABLE_STORES)}


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


# ══ v2272 — WHAT A SEAL MUST CERTIFY BEFORE ITS PIXELS ARE DISPOSABLE ═══════════════════════════
#
# Konyo, 2026-08-29: "make sure that it isnt deleting evidence.. and only pruning literally where it
# can read tooltips.. but not only tooltips are analyzed in a reel.. there is location of the item
# its been read also like where it is exactly and where it was seen.. and everything thats detail
# related should be extracted and tallied.. and then pruned"
#
# THAT IS STRICTLY MORE THAN SEALING MEANS TODAY. A seal row is
# {ts, rows, promptVer, agentVer, why} — it certifies WHICH READER ran, which is a statement about
# the NAME lane and nothing else. frame_verdict then treats "sealed + not a witness" as disposable.
# So a frame whose LOCATION was never extracted is deletable today, and location is exactly what he
# just said must be taken first.
#
# The fix is not a new flag to trust. It is to make the seal declare WHAT IT EXTRACTED, and to hold
# every frame whose seal does not cover the contract. No seal on disk declares it yet, so this holds
# everything — which is the correct direction and is what he asked for. Arming stops being someone
# flipping _PRUNE_SAFE_TO_RUN and becomes the sweep truthfully saying it took the location too.
#
# ⚠ THE FACTS ARE NAMED, NOT COUNTED. "3 things were extracted" is satisfiable by extracting the
# same thing three times. [[unknown-stays-unknown]]
EXTRACTION_CONTRACT = ("name", "location", "provenance")

_CONTRACT_WHY = {
    "name":       "the item's name, which only ever appears in a hover tooltip",
    "location":   "WHERE it was — the container and the cell box inside it (his slot identity)",
    "provenance": "where it was SEEN — which reel and which frame, so a row can be shown its proof",
}


def seal_covers_extraction(row, contract=EXTRACTION_CONTRACT):
    """Does this seal certify that everything detail-bearing was taken? -> (bool, why)

    A seal must carry an `extracted` list naming the facts it took. Anything missing — including a
    seal that names nothing, which is every seal written before this contract existed — HOLDS.
    An unstated fact is an unextracted one; "the sweep probably got it" is not a record.
    """
    if not isinstance(row, dict):
        return False, "the seal is not a record at all"
    got = row.get("extracted")
    if got is None:
        return False, ("this seal predates the extraction contract — it certifies a reader "
                       "(promptVer %s) but never says WHAT it took, and an unstated fact is an "
                       "unextracted one" % (row.get("promptVer") or "?"))
    if not isinstance(got, (list, tuple, set)):
        return False, "the seal's `extracted` is %s, not a list of facts" % type(got).__name__
    have = {str(x) for x in got}
    missing = [f for f in contract if f not in have]
    if missing:
        return False, ("the sweep never extracted %s" % ", ".join(
            "%s (%s)" % (f, _CONTRACT_WHY.get(f, "")) for f in missing))
    return True, "the sweep took %s before anything here became disposable" % ", ".join(contract)


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
    if not wit.get("haveIndex", True):
        return False, ("no durable store exists yet (%s), so nothing here can prove a frame IS a "
                       "witness — and 'unprovable' is not 'no'. Every predicate in this module errs "
                       "toward keeping." % ", ".join(DURABLE_STORES))
    if sess not in (sealed or {}):
        return False, ("recording %s is not sealed — the sweep has not said it read everything "
                       "here, so these pixels may be the only copy of a name" % sess)
    if os.path.basename(frame_path) in (wit.get("frames") or set()):
        return False, ("this frame is a WITNESS behind a row in his vault — it is the only way to "
                       "ever show him why that row is there")
    # v2272 — A FIFTH HOLD, and it is his rule: extracted FIRST, then pruned. Sealing says which
    # reader ran; it has never said what was taken. Until a seal declares the contract, these pixels
    # may still be the only record of WHERE the item was.
    _cov, _why = seal_covers_extraction((sealed or {}).get(sess))
    if not _cov:
        return False, ("recording %s is sealed, but %s — his rule is that everything detail-bearing "
                       "is extracted and tallied BEFORE anything is pruned" % (sess, _why))
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
           # v2080 — `witnessOk` answers "is my picture complete", which is TRUE of a picture of
           # nothing. A reader shown ok:true and 0 witnesses would conclude "measured, none" when
           # the fact is "there is no index yet". Both travel. [[unknown-stays-unknown]]
           "haveIndex": wit.get("haveIndex", True),
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


# ⚠⚠ v2229 — A TEST'S FIXTURES DO NOT ALL LIVE IN FILES CALLED test_*.py, AND THAT COST FOOTAGE.
# On 2026-08-28, within an hour of the prune being armed to act above the disk floor, it deleted
# reel_s_1786998671206_32230 (80.5 MB, 71 pages) and reel_s_1786998775577_33262 (42.4 MB, 35 pages)
# as "read and sealed by BOTH lanes". Both are named as SCENARIO fixtures in tv/vault_simulate.py —
# the module that DEFINES what test_vault_lane.py runs — and vault_simulate.py matched none of the
# four globs, so test_referenced_reels never saw them. Five cases went red immediately.
#
# reel_s_1786998496819_31092 survived the same pass ONLY because test_vault_lane.py happens to name
# it directly in its skipUnless. That is luck, not protection.
#
# This is the THIRD time this class has been paid for. The docstring below records the first two,
# and both fixes widened the LEDGERS the deleter consults; the reach of the SCAN was never the
# suspect. A guard fails on its own reach before it fails on the code.
#
# So: every .py under tv/ and everything under tests/. The scan is keyed on (size, mtime) and cost
# 28 ms over the old set; widening it is cheap and the failure it prevents is irreversible. Holding
# a reel too long costs disk. The other direction costs footage that does not come back.
# [[source-reading-guard]] [[feedback-blind-fixture-green-gate]]
_FIXTURE_GLOBS = ("tv/*.py", "tests/*.spec.ts", "tests/*.ts", "tests/*.py")


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
            for pat in _FIXTURE_GLOBS
            for f in glob.glob(os.path.join(root, pat))))
    except OSError:
        stamp = None
    cached = globals().get("_FIXTURE_CACHE")
    if stamp is not None and cached and cached[0] == stamp:
        return set(cached[1])
    out = set()
    for pat in _FIXTURE_GLOBS:
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
