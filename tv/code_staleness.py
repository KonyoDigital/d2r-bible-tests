#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IS THIS PROCESS STILL RUNNING THE CODE THAT IS ON DISK? — the stale-image watchdog.

⚠⚠ HIS ASK, 2026-09-05, three times because it is the right question: *"stale in-memory so for
this a safeguard on it? is that possible just like we have regression watchdog? so for a
stale-in-memory registry safeguard watchdog for it too?"*

WHAT HAPPENED, AND IT IS THE CASE THIS EXISTS FOR. His console booted 2026-09-04 08:43 and was
still serving that process image sixteen hours later, across v2621 → v2633. In that window a new
evidence source (`reel_router_wilson`) was declared in `self_arming.PROVES` **on disk** and rows
carrying it were appended to `.self_arming.jsonl`. The running console validated those rows
against the registry **it had loaded at boot**, did not recognise the source, and published:

    ".self_arming.jsonl has a row that could not have been banked:
     src 'reel_router_wilson' is not a declared evidence source"

Every word of that is a definite accusation, and **it was false**. The row was banked correctly;
the reader was old. Read under the code on disk the same ledger is clean — `reel.route` OPEN,
56/56, wilson 0.9358.

⚠⚠ SO THE DEFECT IS NOT THE STALENESS. Long-running processes go stale; that is what they do. The
defect is that an unrecognised source and a FORBIDDEN source produced the same sentence, so a
process that simply had not been restarted accused its own ledger of forgery. *"I do not know this
source"* and *"this source may not exist"* are different facts, and the difference is exactly
whether the reader's registry can be trusted to be complete. [[unknown-stays-unknown]]

⚠ AND NOTHING WAS WATCHING. Sixteen hours of drift, thirteen ships, and the only reason it surfaced
is that he looked at a blank window and asked. The console has a version drift watcher, and its own
panel said `ON DISK — UNKNOWN — the drift watcher has not run yet`. A watcher that has never run is
not a watcher. [[feedback-blind-fixture-green-gate]]

WHAT THIS DOES. It records each watched module's identity the first time it is asked, and answers
FRESH / STALE / UNKNOWN afterwards. It is deliberately tiny and has no thread of its own: a
watchdog that needs its own lane is one more thing that can quietly stop.

⚠ IT CHANGES NOTHING AND BLOCKS NOTHING. It reports. Nothing here reloads a module, restarts a
process or touches a button — a console that silently re-imported itself under him would be far
worse than one running known-old code and saying so.
"""
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))

FRESH = "FRESH"        # the file on disk is the file this process loaded
STALE = "STALE"        # disk has moved on — this process is running an older image
UNKNOWN = "UNKNOWN"    # never snapshotted, or the file could not be read. NOT "fresh".

#: modules whose IN-MEMORY state can be outgrown by disk, and what goes wrong when it is.
#: ⚠ The point is not "which files change" — every file changes. It is which ones hold a REGISTRY
#: that another process writes against, so that being old turns into a WRONG ANSWER rather than
#: merely an old one.
WATCHED = {
    "self_arming": "holds PROVES/LOCKS. Another process banks into `.self_arming.jsonl` against "
                   "the registry ON DISK; a stale reader calls those rows forgeries.",
    "store_owners": "holds STORES. A module declared on disk reads as an undeclared toucher here.",
    "run_gates": "holds GATES. A gate added on disk is invisible to a stale runner, which then "
                 "reports a smaller suite as if it were the whole one.",
    "control_app": "serves the console. Stale here means the page, the API and every lane are an "
                   "older build than the tree — which is how sixteen hours of drift went unseen.",
}

_LOCK = threading.Lock()
_SEEN = {}      # module -> (path, mtime_ns, size)


def _identity(path):
    """What this file is, right now. -> (mtime_ns, size) | None

    ⚠ mtime AND size together. mtime alone is famously forgeable — a checkout can restore an old
    timestamp, and same-second edits are invisible at one-second resolution. This is not a
    security boundary, it is a drift detector, and the pair is enough to catch the case that
    actually happens: a file rewritten by an edit or a pull.
    """
    try:
        st = os.stat(path)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _module_path(name):
    """Where the loaded module came from. -> path | None

    ⚠ IT ASKS THE LOADED MODULE, NOT THE DIRECTORY. Resolving `HERE/<name>.py` would compare disk
    against disk and report FRESH forever — the classic guard that measures itself. If the module
    is not imported, there is nothing in memory to be stale and the answer is UNKNOWN.
    """
    mod = sys.modules.get(name)
    p = getattr(mod, "__file__", None) if mod is not None else None
    if not p:
        return None
    return p[:-1] if p.endswith(".pyc") else p


def snapshot(name):
    """Record what this process is currently running for `name`. -> bool (recorded)

    Call it once, as early as the module is first used. Calling it again is a no-op: re-snapping
    would quietly adopt whatever is on disk NOW as the baseline, which turns the watchdog into a
    thing that can never report STALE. That is the failure this whole file is about.
    """
    p = _module_path(name)
    if not p:
        return False
    ident = _identity(p)
    if ident is None:
        return False
    with _LOCK:
        if name in _SEEN:
            return False
        _SEEN[name] = (p, ident[0], ident[1])
    return True


def state(name):
    """Is this process's `name` still the one on disk? -> (state, why)"""
    with _LOCK:
        seen = _SEEN.get(name)
    if seen is None:
        return UNKNOWN, ("nothing snapshotted %s, so whether this process is running the file on "
                         "disk was never established — which is not the same as it being current"
                         % name)
    path, mtime, size = seen
    now = _identity(path)
    if now is None:
        return UNKNOWN, "%s is no longer readable at %s" % (name, os.path.basename(path))
    if now == (mtime, size):
        return FRESH, "unchanged since this process loaded it"
    return STALE, ("%s on disk has changed since this process loaded it (size %d -> %d) — this "
                   "process is running the OLDER image. %s"
                   % (name, size, now[1], WATCHED.get(name, "")))


def report():
    """Every watched module. -> dict

    `anyStale` is the one a caller should branch on, and it is deliberately NOT a bare boolean —
    a caller that cannot tell "nothing is stale" from "nothing was measured" would fail exactly
    the way the thing this watches failed.
    """
    rows, counts = [], {FRESH: 0, STALE: 0, UNKNOWN: 0}
    for name in sorted(WATCHED):
        st, why = state(name)
        rows.append({"module": name, "state": st, "why": why,
                     "matters": WATCHED[name], "loaded": name in sys.modules})
        counts[st] += 1
    return {"ok": True, "rows": rows, "counts": counts,
            "anyStale": counts[STALE] > 0,
            "measured": counts[FRESH] + counts[STALE],
            "why": ("%d module(s) are older in this process than on disk" % counts[STALE])
                   if counts[STALE] else
                   ("nothing was measured — no module was snapshotted, so freshness is UNKNOWN"
                    if counts[FRESH] == 0 else "every watched module matches disk")}


def registry_may_be_incomplete(name="self_arming"):
    """May this process's copy of `name`'s registry be missing entries that exist on disk? -> bool

    ⚠⚠ THIS IS THE ONE THAT CHANGES AN ANSWER, and it is why the module exists rather than being
    a nice report. `self_arming` judges every ledger row against PROVES. When PROVES is stale, an
    unrecognised source is NOT evidence of a forged row — it is evidence that the reader is old.
    Callers use this to answer UNKNOWN instead of accusing.

    Returns True on UNKNOWN as well as STALE, deliberately: "I never checked whether my registry
    is current" is not grounds for confidence either.
    """
    st, _why = state(name)
    return st in (STALE, UNKNOWN)


def main(argv):
    for name in sorted(WATCHED):
        snapshot(name)
    rep = report()
    print("\nIS THIS PROCESS RUNNING THE CODE ON DISK?\n")
    mark = {FRESH: "🟢", STALE: "🔴", UNKNOWN: "⚪"}
    for r in rep["rows"]:
        print("  %s %-14s %-8s %s" % (mark[r["state"]], r["module"], r["state"], r["why"][:82]))
    print("\n  %s\n" % rep["why"])
    return 1 if rep["anyStale"] else 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
