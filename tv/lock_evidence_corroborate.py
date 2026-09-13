#!/usr/bin/env python3
"""A LOCK'S BANKED EVIDENCE MUST NOT CLAIM MORE ATTACKS THAN ITS HARNESS DECLARES.

⚠⚠ THE ARITHMETIC THIS GUARDS IS THE ONE THAT DECIDES WHETHER HIS VAULT MAY WRITE.
`self_arming.score()` computes `wilsonByAttack = wilson_lower(min(k, attacks), attacks)` — the bar
is cleared on DISTINCT ATTACKS, never on raw attempts, because Wilson tightens with n and cannot
tell 83 independent looks from one attack applied 83 times. A banked row that overstates `attacks`
would buy a lock open on refusals nobody earned.

⚠⚠ AND IT IS COMPARED PER SOURCE, NOT PER LOCK — a distinction that cost three wrong measurements
before it was found. MEASURED 2026-09-13: `reel.route` carries 34 banked sabotage attacks against
a harness declaring 7, which looks like 5x inflation in a HARDENED lock. It is not:

    reel.route = 7 from reel_router_wilson (one per CLAIM) + 27 from rung_accounting_wilson

TWO HARNESSES BANK FOR ONE LOCK. A per-lock total is meaningless. Had that comparison shipped it
would have flagged healthy locks as fraudulent — the most damaging false alarm available here,
because it attacks the evidence his vault's permission rests on.
[[feedback-suspect-the-instrument]] [[zero-needs-a-denominator]]

⚠ TWO MORE INSTRUMENT ERRORS ON THE WAY TO THIS: summing raw `_rows()` instead of `_fold()`ed
evidence double-counted history and made all six locks "disagree"; and a grep requiring "def
score" reported four locks as having no harness when six do.

MEASURED with the corrected shape — every source whose CLAIMS can be read AGREES exactly:
    disk_report_wilson 4/4 · hover_wilson 4/4 · prune_wilson 5/5
    reel_router_wilson 7/7 · sweep_wilson 4/4 · vault_wilson 6/6
Zero sources bank more than they declare.

A source with no readable CLAIMS is UNKNOWN, never a violation — its attacks may be declared in a
shape this reader does not know, and "I cannot check" must never render as "it cheated".
"""
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

#: the locks this organ LOOKS AT. Declaring scope is not the same as covering it — see covered().
SCOPE = ("vault.apply", "printer.stream", "reel.route", "prune.reports",
         "vault.sweep_start", "prune.arm", "frame.release", "console.pixel_rescue")

#: ⚠⚠ v3073 — SURFACES IS NO LONGER A LIST OF INTENTIONS. The cross-family eye read the shipped
#: v3071 and found this organ painting EIGHT locks COVERED without asking whether any evidence was
#: readable. MEASURED on the live queue:
#:
#:     console.pixel_rescue   AGREE 0  UNKNOWN 3
#:     frame.release          AGREE 0  UNKNOWN 2
#:     printer.stream         AGREE 0  UNKNOWN 1
#:
#: Three cells claimed by an organ that had read nothing about them — a hollow cell in a guard
#: whose entire subject is overclaiming. Its other finding is the sharper one: `_declared` only
#: understands a module-level CLAIMS, and the AGGREGATE harnesses (rung_accounting 27,
#: pixel_witness 16, frame_release 12) declare their attacks as `attacks=n` on one bank() row and
#: have none. So the organ checks exactly the sources that CANNOT inflate without adding a visible
#: bank() call, and is blind to the ones that can.
#:
#: A surface is therefore covered only when at least ONE source there carries a declaration this
#: reader can actually count. The rest go back to ABSENT, which is what they always were.
#: [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
def covered(locks=None):
    """The locks this organ can actually speak about. -> tuple"""
    try:
        c = corroborate(locks or SCOPE)
    except Exception:
        return ()
    good = set()
    for r in c.get("rows") or []:
        if r.get("verdict") in ("AGREE", "OVERCLAIM"):
            good.add(str(r.get("lock")))
    return tuple(sorted(good))


#: kept for readers that want the scope; organ_matrix asks covered() instead
SURFACES = SCOPE


def _declared(src):
    """How many distinct claims this harness declares. -> int or None (unreadable)."""
    import importlib
    for cand in (src, src.replace("_live", "_wilson").replace("_crossfamily", "_wilson")
                        .replace("_xfam", "_wilson").replace("_li", "_wilson")):
        try:
            m = importlib.import_module(cand)
        except Exception:
            continue
        c = getattr(m, "CLAIMS", None)
        if c is not None:
            try:
                return len(c)
            except Exception:
                return None
    return None


def corroborate(locks=None):
    """-> {rows, checked, overclaimed, unknown, say}"""
    import collections
    import self_arming as SA
    try:
        rows, why = SA._rows()
    except Exception as e:
        return {"rows": [], "checked": 0, "overclaimed": 0, "unknown": 0,
                "say": "the proof queue could not be read (%s) — UNKNOWN" % type(e).__name__}
    if rows is None:
        return {"rows": [], "checked": 0, "overclaimed": 0, "unknown": 0,
                "say": "the proof queue could not be read (%s) — UNKNOWN" % str(why)[:80]}
    want = set(locks or SURFACES)
    banked = collections.defaultdict(int)
    for lock in sorted({str(r.get("lock")) for r in rows if r.get("lock")}):
        if lock not in want:
            continue
        # ⚠ FOLDED, as score() does. Raw rows double-count a harness's own history.
        for r in SA._fold([x for x in rows if x.get("lock") == lock]):
            a = r.get("attacks")
            if isinstance(a, int) and a > 0:
                banked[(str(r.get("src")), lock)] += a
    out_rows, over, unk = [], 0, 0
    for (src, lock), n in sorted(banked.items()):
        dec = _declared(src)
        row = {"src": src, "lock": lock, "banked": n, "declared": dec, "verdict": "", "why": ""}
        if dec is None:
            row["verdict"] = "UNKNOWN"
            row["why"] = ("%s declares its attacks in a shape this reader cannot count, so its "
                          "%d banked attack(s) are unchecked — not cheating, unmeasured" % (src, n))
            unk += 1
        elif n > dec:
            row["verdict"] = "OVERCLAIM"
            row["why"] = ("%s banked %d attack(s) for %s while declaring only %d — the Wilson "
                          "bound is computed on DISTINCT attacks, so this buys the lock open on "
                          "refusals nobody earned" % (src, n, lock, dec))
            over += 1
        else:
            row["verdict"] = "AGREE"
            row["why"] = "%s banked %d of %d declared" % (src, n, dec)
        out_rows.append(row)
    out = {"rows": out_rows, "checked": len(out_rows), "overclaimed": over, "unknown": unk,
           "say": ""}
    if not out_rows:
        out["say"] = "no lock in scope carries banked evidence — UNMEASURED, not clean"
    elif over:
        out["say"] = "%d source(s) bank more attacks than they declare" % over
    else:
        out["say"] = ("%d source(s) agree with their own declarations, %d unreadable"
                      % (len(out_rows) - unk, unk))
    return out


def report(locks=None):
    c = corroborate(locks)
    return {"rows": [{"surface": s, "organ": "corroborator", "checked": c["checked"],
                      "disagreed": c["overclaimed"], "why": c["say"]} for s in covered()],
            "detail": c["rows"], "checked": c["checked"], "overclaimed": c["overclaimed"],
            "unknown": c["unknown"], "say": c["say"]}


def main():
    r = report()
    print("lock evidence corroborator — %s" % r["say"])
    for d in r["detail"]:
        print("  %-9s %-26s %-20s banked=%-4s declared=%s"
              % (d["verdict"], d["src"][:26], d["lock"][:20], d["banked"], d["declared"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
