"""A2 · step 1 — the printer and the reels: can the SWEEP START refuse when it must?

`self_arming.LOCKS` labels `vault.sweep_start` in its own words as *"step 1 — the printer and the
reels"*, and it is the lock his priority names first: the lowest bar (0.510), no prerequisites, and
the one that guards an action that SPENDS MONEY — "starts a paid sweep".

⚠⚠ THIS HARNESS NEVER STARTS A SWEEP. Every attempt is a state in which `chronicle_sweep_start`
MUST refuse, and the only thing counted is whether it did. A harness for a paid door that could
itself open the door would be the most expensive kind of test in this repo. There is no attempt
here whose success path runs.

⚠ AND IT NEVER TOUCHES HIS REAL JOB STATE. `_CHRON_JOB` and the lane list are swapped for the
duration of each attempt and restored in a `finally`, so a crash mid-attempt cannot leave the
console believing a sweep is running. [[feedback-fixtures-never-touch-live-data]]

THE THREE STATES STAY THREE, exactly as hover_wilson keeps them: LEAKS (a wrong input was NOT
refused) is the only failure. UNPROVEN is a measurement nobody has taken. [[unknown-stays-unknown]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _attempt_busy(ca, n=8):
    """A sweep is already running. Starting a second one would double-spend."""
    caught = 0
    orig = dict(ca._CHRON_JOB)
    try:
        for _ in range(n):
            ca._CHRON_JOB["running"] = True
            r = ca.chronicle_sweep_start(limit=1)
            # REFUSED is ok:False. Anything that reports started is a leak of a paid door.
            if isinstance(r, dict) and r.get("ok") is False and r.get("busy") is True:
                caught += 1
    finally:
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(orig)
    return n, caught


def _attempt_no_lane(ca, n=8):
    """No primary lane. A sweep with nothing to read with would spend and learn nothing."""
    caught = 0
    orig = getattr(ca, "_chron_lanes", None)
    if orig is None:
        return 0, 0                      # the accessor moved — UNPROVEN, never a pass
    try:
        ca._chron_lanes = lambda *a, **k: []
        for _ in range(n):
            r = ca.chronicle_sweep_start(limit=1)
            if isinstance(r, dict) and r.get("ok") is False and not r.get("busy"):
                caught += 1
    finally:
        ca._chron_lanes = orig
    return n, caught


CLAIMS = (
    ("busy", "a second sweep cannot start while one is running — it would double-spend", _attempt_busy),
    ("lane", "a sweep cannot start with no lane to read with — it would spend and learn nothing", _attempt_no_lane),
)


def score():
    """-> [row]. One row per claim, in hover_wilson's exact shape so the console reads them alike."""
    try:
        import confidence
        import control_app as ca
    except Exception as e:
        return [{"claim": c, "what": w, "attempts": None, "caught": None, "wilson": None,
                 "state": "UNKNOWN",
                 "notes": ["the console module would not import (%s), so nothing was attempted — "
                           "that is UNKNOWN, not a pass" % str(e)[:70]]}
                for c, w, _ in CLAIMS]
    rows = []
    for claim, what, fn in CLAIMS:
        notes = []
        try:
            n, k = fn(ca)
        except Exception as e:
            n, k = None, None
            notes.append("the attempt itself raised (%s) — UNKNOWN, and the guard is unmeasured"
                         % str(e)[:90])
        if not n:
            state, wil = ("UNPROVEN" if n == 0 else "UNKNOWN"), None
            if n == 0:
                notes.append("no attempt could be made against this guard, so there is no evidence "
                             "in either direction")
        elif k < n:
            state = "LEAKS"
            wil = confidence.wilson_lower(k, n)
            notes.append("a state the sweep MUST refuse was accepted %d time(s) of %d — that is a "
                         "paid door opening on a wrong input" % (n - k, n))
        else:
            state, wil = "PROVEN", confidence.wilson_lower(k, n)
        rows.append({"claim": claim, "what": what, "attempts": n, "caught": k,
                     "wilson": wil, "state": state, "notes": notes})
    return rows


def bank_into_proof_queue(rows):
    """Bank each claim's aggregate under vault.sweep_start. -> {"banked", "skipped"}"""
    import self_arming as _sa
    banked, skipped = [], []
    for r in rows:
        n, k = r.get("attempts"), r.get("caught")
        if n is None or k is None:
            skipped.append("%s (%s — the probe could not answer, so it banks nothing)"
                           % (r.get("claim"), r.get("state")))
            continue
        try:
            _sa.bank("vault.sweep_start", "sabotage", "sweep_wilson", n=n, k=k,
                     ref=str(r.get("claim")), note=str(r.get("what") or "")[:200])
            banked.append("%s %d/%d" % (r.get("claim"), k, n))
        except ValueError as e:
            skipped.append("%s REFUSED: %s" % (r.get("claim"), str(e)[:120]))
    return {"banked": banked, "skipped": skipped}


def main(argv=None):
    rows = score()
    b = bank_into_proof_queue(rows)
    print("SWEEP WILSON — can the paid sweep refuse when it must?\n")
    print("  %-8s %9s %8s %8s  %s" % ("claim", "sabotages", "caught", "wilson", "state"))
    print("  " + "-" * 58)
    for r in rows:
        print("  %-8s %9s %8s %8s  %s" % (
            r["claim"], "?" if r["attempts"] is None else r["attempts"],
            "?" if r["caught"] is None else r["caught"],
            "—" if r["wilson"] is None else ("%.3f" % r["wilson"]), r["state"]))
    print()
    if b["banked"]:
        print("  banked -> vault.sweep_start: " + ", ".join(b["banked"]))
    for sk in b["skipped"]:
        print("  NOT banked: " + sk)
    for r in rows:
        for n in (r["notes"] or []):
            print("  %-8s %s" % (r["claim"], n))
    print("\n  ⚠ no sweep was started. Every attempt is a state the door MUST refuse.")
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main())
