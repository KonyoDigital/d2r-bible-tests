#!/usr/bin/env python3
"""A14 — the chronicle counter only goes up, and the PEAK is what remembers it.

His ask: *"i want to see ledgers proof and a counter for chronicles only going up never down they
can always verify proof with the ledger that way profile and data cant ever be lost!"*

⚠⚠ WHAT WAS ALREADY BUILT, AND THE ONE THING IT CANNOT DO. `console_doctor.
_check_no_ledger_ENTRY_has_silently_vanished` already compares snapshots and NAMES what went —
which is the half that matters, and it came out of 2026-08-28 when `foundLog` went 391 -> 383 and
`setPieces` 120 -> 117 overnight with nothing saying a word.

But it compares only the TWO NEWEST snapshots. A finding therefore survives exactly as long as
nobody takes two more — take three snapshots after a loss and the pairwise diff is clean again
while the items are still gone. **A counter that "only goes up" implies a STORED PEAK, not a
diff**, and that is the whole of what this file adds.

⚠ MEASURED BEFORE BUILDING IT, on his 60 real snapshots:

    key          first   high-water   latest     consecutive drops in the window: 0
    foundLog       412          416      416
    owned          169          169      169
    setPieces      120          121      121

So nothing is below its peak today and this ships GREEN. It is insurance, not a fix for a live
bug, and saying otherwise would be inventing an emergency.

⚠⚠ AND THE WINDOW BEGINS AFTER THE INCIDENT IT WAS INSPIRED BY. These snapshots start at
`foundLog` 412; the 391 -> 383 loss is OUTSIDE them. A clean window is not a clean history, and a
peak seeded from today cannot see a loss that happened before today. That limit is structural — no
amount of care here recovers it — so it is printed rather than filed away.
[[unknown-stays-unknown]] [[stale-reading]]

    python3 tv/ledger_highwater.py                    # the report
    python3 tv/ledger_highwater.py --seed             # first run: record today as the peak
    python3 tv/ledger_highwater.py --accept KEY "why" # lower a peak DELIBERATELY, with a reason
"""
import glob
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPS = os.path.expanduser("~/d2r_ledger_backups")
PEAKS = os.path.join(HERE, "ledger_peaks.json")

#: Keys tracked. Derived from what a snapshot actually carries, never invented — a key absent from
#: a snapshot is UNKNOWN for that snapshot, never zero.
KEYS = ("foundLog", "setPieces", "rwMade", "owned")

OK = "OK"
BELOW_PEAK = "BELOW_PEAK"
UNKNOWN = "UNKNOWN"


def _counts(path):
    """-> {key: int} | None. None means this snapshot could not be read at all."""
    try:
        doc = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return None
    led = doc.get("ledger") if isinstance(doc, dict) and isinstance(doc.get("ledger"), dict) else doc
    if not isinstance(led, dict):
        return None
    out = {}
    for k in KEYS:
        v = led.get(k)
        # ⚠ A KEY THAT IS ABSENT IS NOT A KEY THAT IS ZERO. An absent key simply does not appear,
        # so it can never be compared against a peak and can never invent a loss.
        if isinstance(v, (list, dict)):
            out[k] = len(v)
        elif isinstance(v, int):
            out[k] = v
    return out


def latest():
    """The newest readable snapshot. -> (name, counts, why)"""
    if not os.path.isdir(SNAPS):
        return None, None, ("no snapshot directory at %s, so nothing can be compared — that is "
                            "UNKNOWN, not an intact ledger" % SNAPS)
    files = sorted(glob.glob(os.path.join(SNAPS, "ledger_*.json")))
    for p in reversed(files):
        c = _counts(p)
        if c:
            return os.path.basename(p), c, ""
    return None, None, ("%d snapshot file(s) and not one could be parsed — UNKNOWN, and a louder "
                        "problem than a low count" % len(files))


def _peaks():
    try:
        blob = json.load(io.open(PEAKS, encoding="utf-8"))
        return blob if isinstance(blob, dict) else {}
    except Exception:
        return {}


def _write_peaks(blob):
    tmp = PEAKS + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(blob, ensure_ascii=False, indent=1))
    os.replace(tmp, PEAKS)


def report():
    """-> {"state", "rows", "why"}. Reports; never restores, never fails a build."""
    name, cur, why = latest()
    if cur is None:
        return {"state": UNKNOWN, "rows": [], "why": why, "snapshot": None}
    peaks = _peaks()
    if not peaks:
        return {"state": UNKNOWN, "rows": [], "snapshot": name,
                "why": ("no peak has ever been recorded, so nothing can be below one. Run "
                        "`--seed` to record today. ⚠ A peak seeded now cannot see a loss that "
                        "happened before now — that is structural, not a bug to fix later.")}
    rows, below = [], []
    for k in sorted(cur):
        rec = peaks.get(k)
        if not isinstance(rec, dict) or not isinstance(rec.get("peak"), int):
            rows.append({"key": k, "now": cur[k], "peak": None, "state": UNKNOWN,
                         "why": "no peak recorded for this key yet"})
            continue
        p = rec["peak"]
        if cur[k] < p:
            rows.append({"key": k, "now": cur[k], "peak": p, "state": BELOW_PEAK,
                         "why": ("down %d from the highest ever recorded (%s). It has not been "
                                 "reconciled, so it is still reported."
                                 % (p - cur[k], rec.get("at") or "unknown date"))})
            below.append(k)
        else:
            rows.append({"key": k, "now": cur[k], "peak": p, "state": OK,
                         "why": "at or above its peak"})
    return {
        "state": BELOW_PEAK if below else OK,
        "rows": rows, "snapshot": name, "below": below,
        "why": (("%d key(s) stand BELOW their highest ever count: %s. This REPORTS — putting "
                 "entries back here would hide whatever removed them." % (len(below), ", ".join(below)))
                if below else
                "every tracked key is at or above its highest ever count, in snapshot %s" % name),
    }


def historic_peaks():
    """The highest value each key ever reached across EVERY readable snapshot. -> (dict, int)

    ⚠⚠ SEEDING FROM THE LATEST SNAPSHOT WAS A DEFECT AND I CAUGHT IT ON THE FIRST RUN. If the
    ledger had already dropped before the peak file existed, `latest()` would record the REDUCED
    number as the peak and the loss would be invisible for ever — the precise failure this module
    exists to prevent, built into its own first act. The peak has to come from the whole history
    that is available, not from today.
    """
    out, read = {}, 0
    if not os.path.isdir(SNAPS):
        return out, 0
    for path in sorted(glob.glob(os.path.join(SNAPS, "ledger_*.json"))):
        c = _counts(path)
        if not c:
            continue
        read += 1
        for k, v in c.items():
            if k not in out or v > out[k]:
                out[k] = v
    return out, read


def seed():
    """Record the HIGHEST value ever seen as the peak for every key. -> dict"""
    name, cur, why = latest()
    if cur is None:
        return {"ok": False, "why": why}
    cur, n_read = historic_peaks()
    if not cur:
        return {"ok": False, "why": "no snapshot could be read, so there is no history to seed from"}
    peaks = _peaks()
    now = time.strftime("%Y-%m-%d %H:%M")
    for k, v in cur.items():
        rec = peaks.get(k)
        old = rec.get("peak") if isinstance(rec, dict) else None
        # ⚠ SEEDING MAY ONLY RAISE. Re-running --seed after a loss must not quietly lower the bar
        # to match the loss — that would turn the one mechanism that remembers into one that
        # forgets on request.
        if isinstance(old, int) and v <= old:
            continue
        peaks[k] = {"peak": v, "at": now, "from": "%d snapshot(s), highest ever" % n_read}
    _write_peaks(peaks)
    return {"ok": True, "peaks": peaks,
            "why": "seeded from the HIGHEST value across %d snapshot(s), not from today" % n_read}


def accept(key, reason):
    """Lower a peak DELIBERATELY, recording why. -> dict

    ⚠ A RATCHET WITH NO RECONCILE PATH GOES PERMANENTLY RED THE FIRST TIME HE REMOVES SOMETHING ON
    PURPOSE — and a row that is always red is a row he learns to skip, which is the defect CF-10
    records three instances of. So the peak CAN come down, only by an explicit act, and the act is
    recorded with its reason beside the number it replaced.
    """
    if not str(reason or "").strip():
        return {"ok": False, "why": "a reason is required — lowering a peak without one is the "
                                    "same as not having a peak"}
    name, cur, why = latest()
    if cur is None or key not in cur:
        return {"ok": False, "why": why or "%r is not a key in the newest snapshot" % key}
    peaks = _peaks()
    prev = (peaks.get(key) or {}).get("peak")
    peaks[key] = {"peak": cur[key], "at": time.strftime("%Y-%m-%d %H:%M"), "from": name,
                  "acceptedFrom": prev, "reason": str(reason)[:300]}
    _write_peaks(peaks)
    return {"ok": True, "why": "peak for %s lowered %s -> %d, recorded" % (key, prev, cur[key])}


def main(argv):
    if "--seed" in argv:
        r = seed()
        print(json.dumps(r, ensure_ascii=False, indent=1) if "--json" in argv else r["why"])
        return 0
    if "--accept" in argv:
        i = argv.index("--accept")
        rest = argv[i + 1:]
        if len(rest) < 2:
            print("usage: --accept KEY \"why this loss is intended\"")
            return 0
        print(accept(rest[0], " ".join(rest[1:]))["why"])
        return 0
    r = report()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print("\nLEDGER HIGH-WATER — the count only goes up\n")
    print("  newest snapshot: %s" % (r.get("snapshot") or "none"))
    for row in r["rows"]:
        mark = {OK: "  ", BELOW_PEAK: "⚠ ", UNKNOWN: "? "}.get(row["state"], "  ")
        print("%s%-12s now %-6s peak %-6s %s"
              % (mark, row["key"], row["now"], row["peak"], row["why"]))
    print("\n  %s" % r["state"])
    print("  %s" % r["why"])
    print("\n  ⚠ THE SNAPSHOT WINDOW BEGINS AFTER THE LOSS THAT INSPIRED THIS. It starts at")
    print("     foundLog 412; the 2026-08-28 drop to 383 is outside it. A clean window is not a")
    print("     clean history, and a peak cannot see a loss older than itself.")
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
