#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sabotage harness for `console.pixel_rescue` — can the pixel witness be made to lie?

His ruling, 2026-09-08: *"if they are hardened and tested and prove themselves to work is this a
good place for a hardening and wilson to connect to the heart of the console specifically #34"*.

=== WHAT IS BEING EARNED ===
The right for a PIXEL verdict to trigger a rescue of his window. Today the rescue fires on `due`,
a beat read from the PAGE — and a blank page can still beat, which is exactly the state he was
looking at when his window was black and the hover art was still painting. The pixels are the only
witness that can answer there, and they may not act until they have survived being attacked.

=== ⚠⚠ WHAT COUNTS AS SUCCESS, AND IT READS BACKWARDS ===
The denominator is SABOTAGES ATTEMPTED, never agreements. A wall of inputs the witness handles
comfortably proves nothing — `self_arming` refuses to open on those by construction. Each case
below is built to make the witness say something DANGEROUS; it scores only when it refuses to.

=== THE THREE FAMILIES, AND WHY THE FIRST IS THE ONE THAT MATTERS ===
  A. FALSE BLANK — a healthy window called blank. This is the direction that costs him something:
     a wrong BLANK replaces the window he is looking at, mid-use. Weighted by count accordingly.
  B. MISSED BLANK — a genuinely dead window called painted. A witness that never fires is furniture
     and would leave him the detector, which is the whole complaint.
  C. MUST SAY UNKNOWN — pointed at nothing, or handed nothing. REG-704 is exactly this shape: the
     CLI looked at its own pid and answered UNKNOWN forever. That fix is now a permanent adversary
     rather than a one-off, because the next wrong target will be a different wrong number.

⚠ THE NUMBERS IN FAMILY A AND B ARE HIS, MEASURED, NOT INVENTED. They are the values recorded in
`paint_witness`'s own source from captures of his real window in both states, plus a known-painted
Terminal for a same-instrument reference:

    window                     modalShare   p99   brightShare
    his console, BLANK to him      0.124      33      0.0041
    his console, HEALTHY           0.069     177      0.0394
    Terminal, full of text         0.628     254      0.0581

An attack built from invented numbers proves the arithmetic; one built from his own two states
proves the instrument. [[feedback-blind-fixture-green-gate]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import paint_witness as PW  # noqa: E402
import self_arming as SA  # noqa: E402

LOCK = "console.pixel_rescue"
SRC = "pixel_witness_wilson"


def _m(modal, p99, bright, distinct=140, lum=20):
    """One measured frame, in the exact shape `verdict()` consumes."""
    return {"distinct": distinct, "modalShare": modal, "modalLuminance": lum,
            "p99Luminance": p99, "brightShare": bright}


class _FakeQuartz(object):
    """Answers only what `window_for` asks. No window server anywhere."""
    kCGWindowListOptionOnScreenOnly = 1
    kCGWindowListExcludeDesktopElements = 2
    kCGNullWindowID = 0

    def __init__(self, rows):
        self._rows = rows

    def CGWindowListCopyWindowInfo(self, opts, wid):
        return self._rows


def _win(pid, w, h, num):
    return {"kCGWindowOwnerPID": pid, "kCGWindowNumber": num,
            "kCGWindowBounds": {"Width": w, "Height": h}}


def attacks():
    """Every sabotage, as (family, name, callable -> (refused, detail)).

    `refused` True means the witness did NOT fall for it.
    """
    out = []

    def verdict_is(m, want, why):
        def go():
            got, said = PW.verdict(m)
            return got == want, "%s -> %s (wanted %s) :: %s" % (why, got, want, said[:70])
        return go

    # ── A. FALSE BLANK — the direction that costs him his window ────────────────────────────
    A = [
        ("his HEALTHY console, measured", _m(0.069, 177, 0.0394), PW.PAINTED),
        ("Terminal full of text, measured", _m(0.628, 254, 0.0581), PW.PAINTED),
        # ⚠⚠ THESE THREE ARE LITERALS ON PURPOSE, AND A SABOTAGE CAUGHT ME WRITING THEM THE
        # OTHER WAY. They first read `_m(0.50, PW.INK_P99_MAX, 0.001)` — the attack input DERIVED
        # FROM THE CONSTANT IT EXISTS TO PIN. Widening INK_P99_MAX from 80 to 200 then moved the
        # input with the bar and ALL SIXTEEN attacks still passed, so the harness would have waved
        # through a change that makes his HEALTHY console (p99 177) read BLANK — the one verdict
        # that costs him the window he is looking at. A test anchored to its own subject cannot
        # see the subject move. [[feedback-suspect-the-instrument]] [[regression-guard]]
        #
        # Each of the three now pins ONE bar with a hard number, chosen so the OTHER two conditions
        # cannot mask it:
        ("p99 at his HEALTHY value, ink otherwise silent", _m(0.50, 177, 0.001), PW.PAINTED),
        ("brightShare at his HEALTHY value, p99 dark", _m(0.50, 10, 0.0394), PW.PAINTED),
        ("modal 0.97 with real ink above it", _m(0.97, 200, 0.05), PW.PAINTED),
        ("a DARK but painted window", _m(0.50, 179, 0.020), PW.PAINTED),
        ("p99 unmeasurable — the ink test must not fire", _m(0.50, None, 0.001), PW.PAINTED),
        ("brightShare unmeasurable — same", _m(0.50, 10, None), PW.PAINTED),
    ]
    for name, m, want in A:
        out.append(("false-blank", name, verdict_is(m, want, name)))

    # ── B. MISSED BLANK — a witness that never fires leaves him the detector ────────────────
    B = [
        ("his BLANK console, measured", _m(0.124, 33, 0.0041), PW.BLANK),
        ("a flat white window", _m(0.9966, 255, 1.0), PW.BLANK),
        # literal for the same reason as above — his own blank-console numbers, rounded inward
        ("both ink bars just inside, literal", _m(0.50, 40, 0.005), PW.BLANK),
    ]
    for name, m, want in B:
        out.append(("missed-blank", name, verdict_is(m, want, name)))

    # ── C. MUST SAY UNKNOWN — REG-704's shape, made permanent ───────────────────────────────
    out.append(("must-be-unknown", "handed nothing at all",
                verdict_is(None, PW.UNKNOWN, "handed nothing at all")))
    out.append(("must-be-unknown", "handed a frame that measured nothing",
                verdict_is({"distinct": None, "modalShare": 0.99}, PW.UNKNOWN,
                           "handed a frame that measured nothing")))

    def no_window():
        wid, why = PW.window_for(7, quartz=_FakeQuartz([]))
        return wid is None, "pid owns no window -> %r :: %s" % (wid, str(why)[:60])
    out.append(("must-be-unknown", "pointed at a pid with NO window (REG-704)", no_window))

    def only_helper():
        wid, why = PW.window_for(7, quartz=_FakeQuartz([_win(7, 1, 1, 100)]))
        return wid is None, "only a 1x1 helper -> %r :: %s" % (wid, str(why)[:60])
    out.append(("must-be-unknown", "only a 1x1 helper window exists", only_helper))

    def other_pid():
        wid, why = PW.window_for(7, quartz=_FakeQuartz([_win(9, 1120, 660, 200)]))
        return wid is None, "window belongs to ANOTHER pid -> %r" % (wid,)
    out.append(("must-be-unknown", "the only window belongs to a different pid", other_pid))

    return out


def run(verbose=True):
    """Attempt every sabotage. -> (n, k, rows)"""
    rows, k = [], 0
    for family, name, go in attacks():
        try:
            refused, detail = go()
        except Exception as e:
            refused, detail = False, "the witness THREW: %s: %s" % (type(e).__name__, e)
        k += 1 if refused else 0
        rows.append({"family": family, "name": name, "refused": bool(refused),
                     "detail": detail})
        if verbose:
            print("  %s %-14s %-46s %s" % ("PASS" if refused else "FELL",
                                           family, name[:46], detail[:78]))
    return len(rows), k, rows


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    print("\nSABOTAGING THE PIXEL WITNESS — can it be made to lie about his window?\n")
    n, k, rows = run()
    print("\n  %d/%d sabotages refused\n" % (k, n))
    if "--bank" in argv:
        # ⚠ ONE KIND CANNOT OPEN THIS LOCK (kinds_bar 1.8) AND THAT IS DELIBERATE. Banking here
        # moves it from UNPROVEN to a real score and leaves it LOCKED until a second and third
        # family — live, and cross-family — have also attacked it. A single family agreeing with
        # itself is the wall of agreements this whole module exists to refuse.
        row = SA.bank(LOCK, "sabotage", SRC, n, k,
                      note="adversarial verdicts built from his own two measured window states",
                      attacks=[r["name"] for r in rows if not r["refused"]] or None)
        print("  banked: %s\n" % {kk: row.get(kk) for kk in ("lock", "kind", "src", "n", "k")})
        ok, why = SA.may(LOCK)
        print("  may(%s) -> %s\n  %s\n" % (LOCK, ok, why[:200]))
    else:
        print("  (nothing banked — pass --bank to record this attempt)\n")
    return 0 if k == n else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main())
