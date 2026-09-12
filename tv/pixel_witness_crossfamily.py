#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-family seat for `console.pixel_rescue`.

Cold attacks on `paint_witness.verdict` designed outside `pixel_witness_wilson`'s sabotage
list (different model family / eye). Banks under src `pixel_witness_crossfamily`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import paint_witness as PW  # noqa: E402
import self_arming as SA  # noqa: E402

LOCK = "console.pixel_rescue"
SRC = "pixel_witness_crossfamily"


def _m(modal, p99, bright, distinct, lum=20):
    return {"distinct": distinct, "modalShare": modal, "modalLuminance": lum,
            "p99Luminance": p99, "brightShare": bright}


def attacks():
    """(family, name, callable -> (refused, detail)). refused=True means witness did NOT fall."""
    out = []

    def verdict_is(m, want, label):
        def go():
            got, said = PW.verdict(m)
            return got == want, "%s -> %s (wanted %s) :: %s" % (label, got, want, (said or "")[:70])
        return go

    # X1 — near-healthy modal with chrome-like distinct, but ink bars scream blank
    # (sibling of A3; post-INK_MAX_DISTINCT=64 this must stay PAINTED / not false BLANK)
    out.append(("false-blank", "xfam-rich-dim-ink",
                verdict_is(_m(0.07, 70, 0.01, 120), PW.PAINTED,
                           "rich distinct=120 but p99 under old ink bar")))

    # X2 — checkerboard-ish: high distinct, low modal — must be PAINTED
    out.append(("false-blank", "xfam-checker-noise",
                verdict_is(_m(0.05, 200, 0.04, 200), PW.PAINTED,
                           "high-distinct noise frame")))

    # X3 — almost-all-one-color but just under blank modal bar — still BLANK path careful
    out.append(("missed-blank", "xfam-near-flat-white",
                verdict_is(_m(0.985, 255, 0.002, 3), PW.BLANK,
                           "near-flat white should still read blank")))

    # X4 — dark gradient blank (his measured blank-ish shape) — BLANK
    out.append(("missed-blank", "xfam-dark-gradient-blank",
                verdict_is(_m(0.124, 33, 0.0041, 12), PW.BLANK,
                           "dark gradient blank-shaped frame")))

    # X5 — empty measure — UNKNOWN
    out.append(("must-be-unknown", "xfam-empty-measure",
                verdict_is(None, PW.UNKNOWN, "handed None")))

    # X6 — distinct reported only as 0 with nonsense shares — UNKNOWN or not false PAINTED
    def x6():
        got, said = PW.verdict({"distinct": None, "modalShare": 0.5, "p99Luminance": 100,
                                "brightShare": 0.05})
        return got == PW.UNKNOWN, "distinct None -> %s :: %s" % (got, (said or "")[:70])
    out.append(("must-be-unknown", "xfam-distinct-none", x6))

    # X7 — single luminance covering everything — BLANK
    out.append(("missed-blank", "xfam-one-luminance",
                verdict_is(_m(1.0, 16, 0.0, 1), PW.BLANK,
                           "one luminance covers 100%")))

    # X8 — healthy-shaped but slightly dimmer p99 — must stay PAINTED (no false rescue)
    out.append(("false-blank", "xfam-healthy-dimmer",
                verdict_is(_m(0.069, 150, 0.03, 140), PW.PAINTED,
                           "healthy-shaped slightly dimmer")))

    return out


def run(verbose=True):
    rows = []
    for family, name, fn in attacks():
        refused, detail = fn()
        rows.append({"family": family, "name": name, "refused": bool(refused), "detail": detail})
        if verbose:
            print("  %s %-14s %-28s %s" % (
                "PASS" if refused else "FELL", family, name[:28], detail[:78]))
    n = len(rows)
    k = sum(1 for r in rows if r["refused"])
    return n, k, rows


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    print("\nCROSS-FAMILY PIXEL WITNESS — cold attacks outside the wilson sabotage list\n")
    n, k, rows = run()
    print("\n  %d/%d cross-family sabotages refused\n" % (k, n))
    if "--bank" in argv:
        if k != n:
            print("  refusing to bank a partial run — fix falls first\n")
            return 1
        row = SA.bank(LOCK, "cross-family", SRC, n, k,
                      note="cold cross-family verdict attacks (Grok seat fill)",
                      attacks=len({r["name"] for r in rows}),
                      ref="xfam-cold-verdict")
        print("  banked: %s\n" % {kk: row.get(kk) for kk in ("lock", "kind", "src", "n", "k")})
        ok, why = SA.may(LOCK)
        print("  may(%s) -> %s\n  %s\n" % (LOCK, ok, why[:220]))
    else:
        print("  (nothing banked — pass --bank to record)\n")
    return 0 if k == n else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main())
