#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A15 clause 1 — ONE START POINT: *"every reel enters at the same place. No lane has its own
front door."*

⚠⚠ MEASURED ON THE ARTIFACT, NOT ON A SOURCE GREP, and that choice is the whole design. A grep for
`makedirs` or `index.json` answers a question about NAMES in my own search, and this repo has paid
for that twice in one task: A7's writer count returned ZERO twice — once from a filename-adjacency
grep, once from an AST walk — and both zeros were measuring the instrument, not the codebase.
[[source-reading-guard]] fails on its own reach. His forty reels cannot.

So the question is put to the shelf: **every reel that exists carries the record its maker wrote,
and a second front door would leave a second kind of record.**

    CORE = sessionId · n · frames        the recorder's birth record (tv_diablo, atomic tmp->replace)
    rebuilt                              the REPAIR door (reel_index.ensure_reel_index)
    synthetic / reel-instead-of-sessionId  the FIXTURE door (vault_fixture_reels)

MEASURED 2026-09-04 on his shelf — 40 reels:

    core present                    40 of 40      <-- one start point, on the artifact
    born through the REPAIR door     2 of 40
    born through the FIXTURE door    0 of 40      <-- fixtures never touched his live footage
    core MISSING                     0 of 40

⚠ THREE WRITERS EXIST AND ONLY ONE IS A FRONT DOOR. `reel_index` never rewrites an index that
already parses — it exists so a reel that lost its index does not play BLACK — and
`vault_fixture_reels` writes a tree it is handed. A15's clause is about where a reel ENTERS, and
neither of those two mints a reel from footage. Reporting them as violations would be the
cry-wolf defect A10 is named for; reporting them as invisible would hide a real asymmetry.

⚠ THE ASYMMETRY, MEASURED RATHER THAN ASSUMED. A repaired index is THINNER — it carries the core
and nothing else, because `reconstruct_index` derives (f, ts) from frame names and cannot recover
what the recorder observed. I suspected that loses the per-frame `blank` markings and re-feeds dead
frames to a paid reader. **The shelf refutes the harm:** only 3 of 40 reels carry a `blank` flag on
any row at all, 5 frames in total, and neither repaired reel is one of them. So it is a real
difference in the record and NOT evidence of live damage — both halves stated, because publishing
only the first would be a wolf and only the second would be a whitewash.

    python3 tv/one_start_point.py
    python3 tv/one_start_point.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: The recorder's birth record. Every reel it mints carries these three, and they are the fields a
#: rebuild can also derive — which is exactly why the two doors are distinguishable only by the
#: MARK below, never by the core.
CORE = ("sessionId", "n", "frames")

#: The repair door stamps this. `reel_index.ensure_reel_index` writes it when it reconstructs an
#: index from frame names; it is the only way to tell a repaired reel from an early one.
REPAIR_MARK = "rebuilt"

#: The fixture door stamps this, and keys its record on `reel` rather than `sessionId`. Two
#: independent tells, because one of them is a single word a future edit could drop.
FIXTURE_MARK = "synthetic"


def _hist_dir():
    """-> (path, why). The shelf, asked of the recorder rather than hardcoded here."""
    try:
        import tv_diablo as TD
        p = getattr(TD, "HIST_DIR", "")
        if p and os.path.isdir(p):
            return p, ""
        return "", ("the recorder names %r as the shelf and it is not a directory" % p) if p \
            else "the recorder does not name a shelf"
    except Exception as e:
        return "", "the recorder would not import (%s)" % str(e)[:80]


def _door_of(idx):
    """Which door wrote this birth record? -> (door, why)

    ⚠ UNKNOWN IS A DOOR. A record that carries neither the core nor a mark was written by something
    this probe has not been taught, and calling that "the recorder" because it is the common case
    would be exactly the default-as-measurement defect. [[unknown-stays-unknown]]
    """
    if not isinstance(idx, dict):
        return "UNREADABLE", "the index is %s, not an object" % type(idx).__name__
    if idx.get(FIXTURE_MARK) or ("reel" in idx and "sessionId" not in idx):
        return "fixture", "carries %r / keys on `reel` — vault_fixture_reels built it" % FIXTURE_MARK
    # ⚠⚠ THE CORE IS A SHAPE, NOT A SET OF KEY NAMES, AND THE FIRST CUT CHECKED ONLY THE NAMES.
    # A cold cross-family review of v2533 found it: `{"sessionId": "x", "n": 3, "frames": None}`
    # was attributed to THE RECORDER, because "frames" was present. Reproduced — `frames` as 0,
    # as "98" and as None all returned "recorder". Nothing that mints a reel writes any of those,
    # so a broken index was being read as a healthy birth record and the shelf still said ONE_DOOR.
    # Key presence standing in for a measurement is [[unknown-stays-unknown]] wearing a dict.
    missing = []
    for k in CORE:
        if k not in idx:
            missing.append("%s absent" % k)
        elif k == "frames" and not isinstance(idx[k], list):
            missing.append("frames is %s, not a list" % type(idx[k]).__name__)
        elif k == "sessionId" and not str(idx[k] or "").strip():
            missing.append("sessionId is empty")
        elif k == "n" and (isinstance(idx[k], bool) or not isinstance(idx[k], int)):
            # ⚠ `isinstance(True, int)` is True in Python, so a bare int check lets `n: true`
            # through as a frame count. Named rather than left to a reader to spot.
            missing.append("n is %s, not a number" % type(idx[k]).__name__)
    if missing:
        return "UNKNOWN", ("no mark, and the core does not hold its shape (%s) — nothing here "
                           "knows what wrote it" % "; ".join(missing))
    if idx.get(REPAIR_MARK):
        return "repair", "carries %r — reel_index rebuilt it from the frame names" % REPAIR_MARK
    return "recorder", "the full core with no repair or fixture mark"


def start_points(hist=None):
    """Ask the shelf how many front doors it has. -> dict

    States: ONE_DOOR (every reel entered through the recorder, repairs aside) ·
    MULTIPLE_DOORS (something other than the recorder minted a reel) · UNKNOWN (nothing to read).
    """
    # ⚠⚠ REG-546 — EVERY RETURN CARRIES THE SAME KEYS, and these did not: `walked` was on the
    # normal return and absent from both UNKNOWN returns, so a caller reading it broke on exactly
    # the paths that mean NOTHING WAS ESTABLISHED. Caught by the cross-probe SHAPE law on its first
    # run — the sixth instance in a day of a fix shipping the class it was fixing, and the first
    # one found by a machine instead of by someone reading the next line.
    def _unknown(w):
        return {"ok": False, "state": "UNKNOWN", "rows": [], "counts": {}, "walked": 0, "why": w}

    why = ""
    if hist is None:
        hist, why = _hist_dir()
    if not hist or not os.path.isdir(hist):
        return _unknown("UNKNOWN, not zero doors — %s"
                        % (why or "no shelf was found, so nothing was asked"))
    rows = []
    for name in sorted(os.listdir(hist)):
        d = os.path.join(hist, name)
        if not (name.startswith("reel_") and os.path.isdir(d)):
            continue
        p = os.path.join(d, "index.json")
        if not os.path.isfile(p):
            rows.append({"reel": name, "door": "UNKNOWN",
                         "why": "no index.json — the reel exists and nothing records its birth"})
            continue
        try:
            idx = json.loads(io.open(p, encoding="utf-8").read())
        except Exception as e:
            rows.append({"reel": name, "door": "UNREADABLE",
                         "why": "the index would not parse (%s)" % str(e)[:70]})
            continue
        door, dwhy = _door_of(idx)
        fr = idx.get("frames") if isinstance(idx.get("frames"), list) else []
        rows.append({"reel": name, "door": door, "why": dwhy, "frames": len(fr),
                     "blankFlagged": sum(1 for r in fr
                                         if isinstance(r, dict) and r.get("blank"))})
    counts = {}
    for r in rows:
        counts[r["door"]] = counts.get(r["door"], 0) + 1
    if not rows:
        return _unknown("the shelf holds no reels, so the question could not be put to it")
    # ⚠ A REPAIR IS NOT A SECOND FRONT DOOR, and counting it as one is the cry-wolf defect A10 is
    # named for. `reel_index` never mints a reel from footage — it restores an index a reel already
    # had, and refuses outright to rewrite one that parses. A fixture reel on his LIVE shelf is a
    # different matter: that is footage this pipeline did not record, wearing a reel's clothes.
    foreign = counts.get("fixture", 0) + counts.get("UNKNOWN", 0) + counts.get("UNREADABLE", 0)
    state = "ONE_DOOR" if not foreign else "MULTIPLE_DOORS"
    return {
        "ok": True, "state": state, "rows": rows, "counts": counts,
        "walked": len(rows),
        "why": ("%d reel(s) on the shelf: %d minted by the recorder, %d restored by the repair "
                "door, %d foreign. %s"
                % (len(rows), counts.get("recorder", 0), counts.get("repair", 0), foreign,
                   ("ONE START POINT — every reel carries the recorder's core (%s), and a repair "
                    "is not a second front door: reel_index restores an index a reel already had "
                    "and refuses to rewrite one that parses."
                    % " · ".join(CORE)) if not foreign else
                   ("MORE THAN ONE DOOR — %d reel(s) on his live shelf were not minted by the "
                    "recorder. A15 says no lane has its own front door." % foreign))),
    }


def main(argv):
    r = start_points()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0
    print("\nA15 clause 1 — ONE START POINT: does every reel enter at the same place?\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    print("  %s" % r["state"])
    for door in sorted(r["counts"]):
        print("     %-11s %3d" % (door, r["counts"][door]))
    thin = [x for x in r["rows"] if x["door"] == "repair"]
    if thin:
        print()
        print("  ⚠ THE REPAIRED RECORDS ARE THINNER, and that is a real difference, not a fault:")
        for x in thin:
            print("     %-34s %d frame(s), %d flagged blank"
                  % (x["reel"], x.get("frames", 0), x.get("blankFlagged", 0)))
        flagged = sum(1 for x in r["rows"] if x.get("blankFlagged"))
        print("     A rebuild derives (f, ts) from frame names and cannot recover what the")
        print("     recorder OBSERVED. Measured before claiming harm: %d of %d reel(s) carry a"
              % (flagged, r["walked"]))
        print("     `blank` flag on any row at all, so the loss is real and its damage is not.")
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
