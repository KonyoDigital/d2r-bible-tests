#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live seat for `console.pixel_rescue` — does paint_witness tell the truth on HIS window?

Banks under src `pixel_witness_live` (kind `live`). Grok Bot fills this seat by looking;
Claude owns the tree. This file exists so the evidence is traceable (PROVES allow-list).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import paint_witness as PW  # noqa: E402
import self_arming as SA  # noqa: E402

LOCK = "console.pixel_rescue"
SRC = "pixel_witness_live"
N_LOOKS = 8


def run(n=N_LOOKS, sleep_s=0.35):
    """Look at his console n times. Each look that returns PAINTED (not false-BLANK) is a refuse.

    On a healthy painted window the dangerous lie is BLANK. UNKNOWN is not a refuse of that
    attack — it means we did not look.
    """
    rows = []
    pid = PW.console_pid()
    for i in range(n):
        got = PW.look(pid) if pid else PW.look(PW.console_pid())
        state = (got or {}).get("state")
        # refused the false-blank attack when the live window is reported PAINTED
        refused = state == PW.PAINTED
        rows.append({
            "name": "live-look-%d" % (i + 1),
            "refused": refused,
            "state": state,
            "why": (got or {}).get("why", "")[:120],
            "pid": (got or {}).get("pid"),
            "windowId": (got or {}).get("windowId"),
        })
        time.sleep(sleep_s)
    k = sum(1 for r in rows if r["refused"])
    return len(rows), k, rows


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    print("\nLIVE PIXEL WITNESS — does it call his on-screen console PAINTED?\n")
    n, k, rows = run()
    for r in rows:
        print("  %s %-14s pid=%s  %s" % (
            "PASS" if r["refused"] else "FAIL",
            r["state"], r.get("pid"), (r.get("why") or "")[:70]))
    print("\n  %d/%d live looks refused false-BLANK (wanted PAINTED)\n" % (k, n))
    if "--bank" in argv:
        if k == 0:
            print("  refusing to bank: zero refuses — that is not evidence\n")
            return 1
        row = SA.bank(LOCK, "live", SRC, n, k,
                      note="live paint_witness looks on his on-screen TV DIABLO window",
                      attacks=len({r["name"] for r in rows if r["refused"]}),
                      ref="live-painted-window")
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
