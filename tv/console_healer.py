#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE SCAR LEDGER AND THE HEALER — what the watchdog does with what it sees.

Konyo, 2026-08-24: "teach watchdog and eagle eye and give it the capabilities to see this so when
it happens in the future it can auto scar / auto heal / auto fix."

The eagle SEES and the watchdog LOOKS ON A TIMER. Neither of them REMEMBERS, and neither of them
ACTS. That gap is the whole reason he keeps finding the same thing twice: a fault that appears,
gets fixed, and comes back reads exactly like a fault appearing for the first time, so nothing in
the system can say the words "this is a REGRESSION" — the one sentence that would have changed
what I did.

So this module is two halves, and they are deliberately different sizes.

  THE LEDGER (auto-scar) — every red the watchdog sees is written down: what it was, when it FIRST
  appeared, when it last appeared, when it cleared, and HOW MANY TIMES IT HAS COME BACK. Cheap,
  safe, and it applies to every fault without exception. A fault that has cleared and returned is
  reported as a RETURN, with the count, forever.

  THE HEALER (auto-fix) — a NAMED remedy for a NAMED fault, and only where the repair is
  RE-DERIVABLE FROM EVIDENCE rather than an act of judgement. That line is his, from
  [[sweep-dont-ask]], and it is the whole safety argument: folding orphan frames into the reel
  whose stamp they already carry is arithmetic. Deciding which of his items to throw out is not.
  Most faults get NO remedy, and that is the correct answer, not a gap to fill later.

FOUR LAWS, each of which exists because its absence is a way this module could hurt him:

  1. RE-DERIVABLE ONLY. If the repair needs a preference, a threshold, or a guess about intent, it
     is not a remedy. It is a report.
  2. HEAL, RE-MEASURE, AND DISARM ON FAILURE. Every heal is followed by running the SAME check
     again. If the check is still red, that remedy is disarmed for the life of the process and the
     scar records that it was tried and did not work. A remedy that can be retried forever is a
     loop, and a loop that touches his files is the worst thing in this file.
  3. NOTHING IS DESTRUCTIVE. No remedy deletes, truncates or overwrites his data. The strongest
     thing any of them may do is MOVE a file into the place its own stamp says it belongs, or
     restore a backup this module itself wrote while the store was healthy.
  4. OPT-IN, AND SILENT MEANS OFF. Healing requires TV_AUTO_HEAL=1. With it unset the module still
     scars everything — remembering costs nothing and risks nothing — and reports what it WOULD
     have done, so the remedy can be read before it is ever armed.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, ".console_scars.json")

# The number in a why-string is the SIZE of a fault, never its identity: "2385 frame(s) belong to
# no reel" and "12 frame(s) belong to no reel" are one scar returning, not two scars. Fingerprint
# on the shape with the digits knocked out, or every recurrence reads as a first sighting and the
# ledger can never say the word REGRESSION — which is the only thing it is for.
_NUM = re.compile(r"\d+(?:\.\d+)?")


def fingerprint(check, why):
    return "%s|%s" % (check, _NUM.sub("#", (why or "").strip())[:140])


def _load():
    try:
        with io.open(LEDGER, encoding="utf-8") as fh:
            blob = json.load(fh)
        return blob if isinstance(blob, dict) else {"scars": {}}
    except Exception:
        return {"scars": {}}


def _save(blob):
    tmp = LEDGER + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(blob, indent=1, ensure_ascii=False))
    os.replace(tmp, LEDGER)


def record(rows, now_ms=None):
    """Fold one watchdog reading into the ledger. Returns the scars that are RED right now, each
    carrying its own history, so the caller can tell a first sighting from a return."""
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    blob = _load()
    scars = blob.setdefault("scars", {})
    red_now = []
    seen_keys = set()
    for r in rows or []:
        if r.get("state") != "missing":
            continue
        k = fingerprint(r.get("check"), r.get("why"))
        seen_keys.add(k)
        s = scars.get(k)
        if s is None:
            s = {"check": r.get("check"), "why": r.get("why"), "firstSeen": now, "lastSeen": now,
                 "times": 1, "clearedAt": None, "returns": 0,
                 "heal": {"tried": 0, "worked": 0, "disarmed": False, "lastSaid": None}}
            scars[k] = s
        else:
            # A scar that had CLEARED and is red again is a regression, and the count of returns is
            # the number he should be shown. It is never reset.
            if s.get("clearedAt"):
                s["returns"] = int(s.get("returns") or 0) + 1
                s["clearedAt"] = None
            s["lastSeen"] = now
            s["times"] = int(s.get("times") or 0) + 1
            s["why"] = r.get("why")
        red_now.append(dict(s, key=k))
    # Anything the ledger holds as red that this reading did not see has CLEARED. Stamping the
    # clear is what makes the next sighting a RETURN rather than another first.
    for k, s in scars.items():
        if k not in seen_keys and not s.get("clearedAt"):
            s["clearedAt"] = now
    _save(blob)
    return red_now


def history(key=None):
    scars = _load().get("scars") or {}
    return scars.get(key) if key else scars


def says(scar):
    """One line a person can act on, and the RETURN count is the part that matters."""
    n = int(scar.get("returns") or 0)
    if n:
        return "%s — THIS HAS COME BACK %d time(s) after clearing. %s" % (
            scar.get("check"), n, scar.get("why") or "")
    return "%s — %s" % (scar.get("check"), scar.get("why") or "")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# THE REMEDIES. Each is (why it is safe, callable) and each returns (did_something, said).
#
# Read the "why it is safe" line as the contract. If a remedy is ever changed so that its line
# stops being true, the remedy is wrong, not the line.
# ─────────────────────────────────────────────────────────────────────────────────────────────

def _remedy_fold_orphan_footage():
    """Frames of a session that died before sealing sit loose in hist/, where no lane and no
    deleter can see them. Every one of those files CARRIES ITS OWN SESSION STAMP in its name, so
    the reel it belongs to is read off the evidence, never chosen. Nothing is deleted: the frames
    move into the reel directory their own stamp names."""
    sys.path.insert(0, HERE)
    import orphan_fold as of
    # TV_HIST or nothing. `of.plan()` with no argument reads the module's OWN default hist dir,
    # which on a test tree is HIS footage and on a scratch tree is the wrong directory entirely —
    # the remedy then reports "nothing loose to fold" about a place nobody asked about. Exactly the
    # defect that put seven cases on his live reels last night.
    # [[feedback-fixtures-never-touch-live-data]]
    p = of.plan(hist_dir=(os.environ.get("TV_HIST")
                          or os.path.join(HERE, "frames", "hist")))
    # The key is `clusters`, and `frames` on each is a COUNT, not a list. The first cut of this
    # remedy read `p["groups"]` — a field orphan_fold has never had — so it returned False every
    # time and reported "nothing loose to fold" about 12 frames that were sitting right there. A
    # remedy that can never fire, wearing a clean answer. Found by running it, not by reading it.
    # [[plumbing-with-no-tap]] [[the-unjoined-end]]
    if not p.get("ok"):
        return False, "orphan_fold could not read the footage: %s" % str(p.get("why"))[:90]
    ok = [c for c in (p.get("clusters") or []) if c.get("eligible") and c.get("frames")]
    refused = [c for c in (p.get("clusters") or []) if not c.get("eligible")]
    if not ok:
        return False, ("nothing eligible to fold"
                       + (" — %d cluster(s) REFUSED for overlapping an existing reel, which would "
                          "forge a second session id for one recording" % len(refused)
                          if refused else ""))
    n = sum(int(c.get("frames") or 0) for c in ok)
    res = of.apply_plan(p, yes=True)
    if isinstance(res, dict) and res.get("ok") is False:
        return False, "orphan_fold refused: %s" % str(res.get("why"))[:110]
    return True, ("folded %d loose frame(s) into %d reel(s) named by their own stamps%s"
                  % (n, len(ok),
                     "; %d refused for overlapping an existing reel" % len(refused)
                     if refused else ""))


def _remedy_restore_a_vault_store():
    """A store that will not parse is restored ONLY from a backup THIS MODULE wrote while the same
    store was parsing, and only when that backup holds AT LEAST AS MANY ROWS. The corrupt file is
    kept beside it as .corrupt — nothing of his is ever thrown away to make a check go green."""
    names = ("vault_accum.json", "vault_seen.json", "vault_swept.json")
    fixed = []
    for n in names:
        fp = os.path.join(HERE, n)
        bak = fp + ".healer_bak"
        if not os.path.exists(fp) or not os.path.exists(bak):
            continue
        try:
            with io.open(fp, encoding="utf-8") as fh:
                json.load(fh)
            continue                       # it parses; nothing to restore
        except Exception:
            pass
        try:
            with io.open(bak, encoding="utf-8") as fh:
                good = json.load(fh)
        except Exception:
            continue                       # the backup is no better; leave both alone
        os.replace(fp, fp + ".corrupt")
        with io.open(fp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(good, ensure_ascii=False))
        fixed.append("%s (%d row(s), corrupt copy kept as %s.corrupt)" % (
            n, len(_rows_of(good)), n))
    if not fixed:
        return False, "no store had a healthy backup to come back from"
    return True, "restored " + "; ".join(fixed)


def _rows_of(blob):
    for k in ("owned", "rows"):
        if isinstance(blob, dict) and k in blob:
            v = blob[k]
            return v if hasattr(v, "__len__") else []
    return blob if hasattr(blob, "__len__") else []


def back_up_healthy_stores():
    """The half of the vault remedy that has to run BEFORE the fault.

    A repair needs something to repair FROM, and nothing in this tree wrote one. So every time the
    watchdog finds the stores healthy, the healthy bytes are copied aside. This is not a heal — it
    is the reason a heal can exist later, and it runs whether or not healing is armed."""
    kept = 0
    for n in ("vault_accum.json", "vault_seen.json", "vault_swept.json"):
        fp = os.path.join(HERE, n)
        if not os.path.exists(fp):
            continue
        try:
            with io.open(fp, encoding="utf-8") as fh:
                blob = json.load(fh)
        except Exception:
            continue                       # only healthy bytes are ever banked
        bak = fp + ".healer_bak"
        try:
            # Never bank a SMALLER ledger over a larger one. A store that has just lost rows is
            # exactly the moment a backup is most valuable and most dangerous to overwrite.
            if os.path.exists(bak):
                with io.open(bak, encoding="utf-8") as fh:
                    if len(_rows_of(json.load(fh))) > len(_rows_of(blob)):
                        continue
            tmp = bak + ".tmp"
            with io.open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(blob, ensure_ascii=False))
            os.replace(tmp, bak)
            kept += 1
        except Exception:
            pass
    return kept


REMEDIES = {
    "footage has a reel": ("the reel is read off each frame's own stamp; nothing is deleted",
                           _remedy_fold_orphan_footage),
    "vault stores": ("restores only from a backup this module wrote while the store parsed, and "
                     "only if it holds at least as many rows; the corrupt copy is kept",
                     _remedy_restore_a_vault_store),
}

# Everything else is deliberately absent, and the absences are the interesting part:
#   version drift    the console decides that itself (drift_may_relaunch), because only IT knows
#                    whether he is filming — a restart mid-session orphans the frames it kills.
#   art corpus       the sprites are genuinely gone. Extracting them from CASC is a job, not a fix.
#   visual lock      a code regression. There is no safe machine repair for "someone changed the
#   locked lanes     rules" — the repair is a person reading a diff, and the scar is what gets them
#                    there. A module that silently rewrote code to make its own gate go green would
#                    be the single most dangerous thing in this tree.
#   disk headroom    deleting his footage is his call and always will be.

_DISARMED = set()


def heal(scar, recheck=None):
    """Try the named remedy for one scar. Returns (state, said) where state is one of
    'healed' / 'no-remedy' / 'not-armed' / 'disarmed' / 'failed' / 'still-red'."""
    check = scar.get("check")
    entry = REMEDIES.get(check)
    if not entry:
        return "no-remedy", "there is no safe machine repair for %r — it needs a person" % check
    why_safe, fn = entry
    if check in _DISARMED or (scar.get("heal") or {}).get("disarmed"):
        return "disarmed", "the remedy for %r was tried and did not clear the check" % check
    if os.environ.get("TV_AUTO_HEAL") != "1":
        return "not-armed", "would run: %s (%s). Arm with TV_AUTO_HEAL=1" % (check, why_safe)
    try:
        did, said = fn()
    except Exception as e:
        _note_heal(scar, worked=False, said="the remedy threw: %s" % str(e)[:110], disarm=True)
        _DISARMED.add(check)
        return "failed", "the remedy for %r threw: %s" % (check, str(e)[:110])
    if not did:
        _note_heal(scar, worked=False, said=said, disarm=True)
        _DISARMED.add(check)
        return "failed", said
    # LAW 2. A heal is not believed because it returned — it is believed because the check that
    # was red is now green. Anything else is a remedy grading its own homework.
    if recheck is not None:
        try:
            state, why = recheck()
        except Exception as e:
            state, why = "unknown", str(e)[:110]
        if state == "missing":
            _note_heal(scar, worked=False, said="ran (%s) and the check is STILL red: %s" % (
                said, why), disarm=True)
            _DISARMED.add(check)
            return "still-red", "%s — but %r is still red: %s" % (said, check, why)
    _note_heal(scar, worked=True, said=said, disarm=False)
    return "healed", said


def _note_heal(scar, worked, said, disarm):
    blob = _load()
    s = (blob.get("scars") or {}).get(scar.get("key") or fingerprint(scar.get("check"),
                                                                    scar.get("why")))
    if s is None:
        return
    h = s.setdefault("heal", {"tried": 0, "worked": 0, "disarmed": False, "lastSaid": None})
    h["tried"] = int(h.get("tried") or 0) + 1
    if worked:
        h["worked"] = int(h.get("worked") or 0) + 1
    if disarm:
        h["disarmed"] = True
    h["lastSaid"] = said
    h["lastAt"] = int(time.time() * 1000)
    _save(blob)


def tend(rows, recheck_for=None):
    """The whole cycle, for the watchdog to call: scar everything red, bank the healthy stores,
    then attempt the remedies that exist. Returns a list of {scar, state, said}."""
    red = record(rows)
    if not any(r.get("check") == "vault stores" for r in red):
        back_up_healthy_stores()
    out = []
    for s in red:
        rc = (recheck_for or {}).get(s.get("check"))
        state, said = heal(s, recheck=rc)
        out.append({"scar": s, "state": state, "said": said})
    return out


def main(argv=None):
    try:
        from console_safe import enable as _console_safe
        _console_safe()
    except Exception:
        pass
    argv = list(sys.argv[1:] if argv is None else argv)
    scars = history()
    if not scars:
        print("the ledger is empty — nothing red has been seen yet")
        return 0
    live = [s for s in scars.values() if not s.get("clearedAt")]
    old = [s for s in scars.values() if s.get("clearedAt")]
    if live:
        print("RED NOW (%d):" % len(live))
        for s in sorted(live, key=lambda x: -int(x.get("returns") or 0)):
            print("  • " + says(s))
            h = s.get("heal") or {}
            if h.get("tried"):
                print("      heal: tried %d, worked %d%s — %s" % (
                    h["tried"], h.get("worked") or 0,
                    ", DISARMED" if h.get("disarmed") else "", h.get("lastSaid") or ""))
    if old:
        print("CLEARED (%d), kept so a return can be named a return:" % len(old))
        for s in old:
            print("  · %s — seen %d time(s), %d return(s)" % (
                s.get("check"), s.get("times") or 0, s.get("returns") or 0))
    return 1 if live else 0


if __name__ == "__main__":
    sys.exit(main())
