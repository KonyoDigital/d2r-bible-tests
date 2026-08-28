#!/usr/bin/env python3
"""THE ONE HOME FOR "how sure are we, given how many times we looked".

⚠ WHY THIS FILE EXISTS RATHER THAN A SECOND COPY OF THE MATH. Wilson was written into
chronicle_retro.py and lives there as a shadow on ONE gate. Konyo, 2026-08-28: "see everywhere that
can get this logic to also eventually be coded and hardcoded itself within the system... especially
with data coming through consecutively."

Spreading it by COPYING the function into each lane is `copy-drift` by construction — one law, four
statements, and a tuning applied to one of them silently. So the math moves here ONCE and every lane
imports it. chronicle_retro re-exports its own names so nothing that already calls it changes.

WHAT THE RULE ACTUALLY BUYS, stated plainly because it is the whole argument:

    a flat count bar cannot tell 2-of-2 from 20-of-20. Wilson can.

    looks   flat bar (>=2)   wilson lower bound
      2/2      PASS               0.342
      4/4      PASS               0.510
     10/10     PASS               0.722
     20/20     PASS               0.839

That is his "especially with data coming through consecutively" in one table: the flat bar stops
learning the moment it is cleared, and the Wilson bound keeps sharpening for as long as evidence
keeps arriving. It is also honest downward: one lucky look scores 0.207 here against 1.000 under k/n, and 1-of-4
scores 0.046. (Not 0.0 — a single success is weak evidence, not absent evidence. Only n=0 is 0.0,
and that distinction is deliberate.)

WHAT IT DOES NOT BUY. Wilson measures how many looks agreed, never whether the looks were
INDEPENDENT. Four re-reads of one frozen frame by one model are one look wearing four hats, and no
statistic recovers that. `confluence` is the answer to that half — it scores the KINDS of evidence,
so cross-reel beats cross-lane beats a re-look, and two kinds beat four of the same. The two run
TOGETHER or neither means anything. [[d2r-multiwitness-corroboration]]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def wilson_lower(k, n, z=1.96):
    """Lower bound of the 95% Wilson score interval for k successes in n trials. -> float

    n == 0 returns 0.0 — no evidence is not weak evidence, it is none. That distinction is the whole
    reason this is here rather than k/n, which answers 1.0 for a single lucky look.
    """
    try:
        k = float(k); n = float(n)
    except (TypeError, ValueError):
        return 0.0
    if n <= 0 or k < 0:
        return 0.0
    if k > n:
        k = n
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p + z2 / (2.0 * n)
    margin = z * (((p * (1.0 - p) + z2 / (4.0 * n)) / n) ** 0.5)
    return max(0.0, min(1.0, (centre - margin) / denom))


def confluence(tags, tiers):
    """Weighted strength of the KINDS of evidence. -> float

    Additive on purpose and deliberately NOT capped at 1.0: two independent kinds really are worth
    more than one, and flattening that is the thing being fixed. An unknown tag scores 0 rather than
    a default — a tag nobody has weighted is a tag nobody has thought about, and a default would
    silently pay it as if someone had.

    `tiers` is passed IN rather than imported so each lane keeps its own weights: what counts as
    independent evidence for a chronicle read is not what counts for a stash sweep.
    """
    try:
        return round(sum(float(tiers.get(t, 0.0)) for t in (tags or [])), 3)
    except Exception:
        return 0.0


def shadow(k, n, tags, tiers, wilson_floor, confluence_floor, live_verdict, lane, subject=""):
    """What the Wilson+confluence rule WOULD say, beside what the live gate DID say. -> dict

    ⚠ DECIDES NOTHING, BY CONSTRUCTION. It reports `wouldPass` and `agrees`; no caller may branch on
    it. That is not timidity — it is the only way to earn the right to flip it live later. Task #34
    measured the chronicle shadow agreeing with its live gate 23 times out of 23, which is precisely
    the evidence that says "not yet": a rule that has never once disagreed has never been tested
    against the live one, so promoting it would be an unmeasured change wearing a measured face.
    [[feedback-blind-fixture-green-gate]]

    The disagreements are the product. Accumulate them (shadow_ledger), and the day the record shows
    WHERE and WHY the two part is the day there is something real to decide.
    """
    lo = wilson_lower(k, n)
    conf_w = confluence(tags, tiers)
    would = bool(lo >= wilson_floor and conf_w >= confluence_floor)
    live = bool(live_verdict)
    return {
        "lane": lane, "subject": subject, "k": int(k), "n": int(n),
        "wilson": round(lo, 4), "wilsonFloor": round(float(wilson_floor), 4),
        "confluence": conf_w, "confluenceFloor": round(float(confluence_floor), 4),
        "tags": list(tags or []), "wouldPass": would, "livePassed": live,
        "agrees": would == live,
        "why": ("%d of %d looks -> wilson %.3f (floor %.3f); confluence %.2f (floor %.2f) from %s"
                % (k, n, lo, wilson_floor, conf_w, confluence_floor,
                   ", ".join(tags or []) or "nothing")),
    }


def sharpens_with_evidence(k_n_pairs):
    """PROOF the bound actually tightens as identical-quality evidence accumulates. -> (ok, why)

    This is the property the whole argument rests on, so it is asserted rather than assumed. If a
    future z or a rewritten formula broke monotonicity, every "more looks = more certain" claim in
    the console would be false and nothing else would notice.
    """
    prev, prev_n = None, None
    for k, n in k_n_pairs:
        lo = wilson_lower(k, n)
        if prev is not None and lo <= prev:
            return False, ("%d/%d scored %.4f, no better than %d/%d at %.4f — the bound does not "
                           "sharpen, so 'more looks' buys nothing" % (k, n, lo, prev_n, prev_n, prev))
        prev, prev_n = lo, n
    return True, None


def main(argv=None):
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    print("WILSON — what more looks actually buy\n")
    print("  %-9s %-12s %s" % ("looks", "flat bar>=2", "wilson lower"))
    for n in (1, 2, 3, 4, 6, 10, 20, 50):
        print("  %-9s %-12s %.3f" % ("%d/%d" % (n, n), "PASS" if n >= 2 else "fail",
                                     wilson_lower(n, n)))
    ok, why = sharpens_with_evidence([(n, n) for n in (2, 3, 4, 6, 10, 20, 50)])
    print("\n  %s" % ("🟢 the bound sharpens monotonically with evidence"
                      if ok else "🔴 %s" % why))
    print("\n  and honest downward:  1 of 1 look -> %.3f   (k/n would say 1.000)"
          % wilson_lower(1, 1))
    print("                        1 of 4 looks -> %.3f" % wilson_lower(1, 4))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
