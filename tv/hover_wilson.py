"""HOVER WILSON — the autopilot scores its own claims, and proves each one can be caught wrong.

Konyo, 2026-09-01: *"for the hover mode and automatic MINI mode i want wilson score there, and it
self collaborates itself and self improves too, and self proves those coordinates and tooltip and
analyzing... only after you fix the list completely we will do it — and test it."*

WHAT THE AUTOPILOT ACTUALLY CLAIMS. MINI(AUTOMATIC) hovers a cell and reads the tooltip that
appears. That is not one claim, it is four, and they fail independently:

    COORDINATE   the point I moved to is inside the cell I meant
    ANCHOR       the tooltip that appeared belongs to the cursor I placed
    READ         two reads of the same frame say the same thing
    SLOT         reads from different reels agree about which cell it was

Each is scored separately, because a lane that is 100% right about coordinates and 60% right about
tooltips is not "80% good" — averaging them hides which half to fix.

⚠ THE DENOMINATOR IS SABOTAGE ATTEMPTS, NOT RUNS. This is the rule the vault lane cost us: a check
that always agrees may be perfect or INERT, and those are indistinguishable from the agreement
rate alone. `vault_autoreel_tick` ran every 45 seconds for months at a 100% agreement rate and had
never swept anything. So the numerator here is "times a deliberately WRONG input was caught", and
the denominator is "times we tried". A claim nobody has tried to break scores UNPROVEN.
[[heart-first]] rule 5

⚠ AND UNPROVEN MUST NOT READ AS FAILING. A low score names work to do; it is not an alarm. A gate
that turned amber on its own newest checks would be switched off inside a week, which is the same
defect as a gate that is green forever.

⚠ THIS RUNS ON GEOMETRY, NOT ON HIS SCREEN. Every probe below is arithmetic over slot_identity's
own functions with synthetic rectangles. It moves no cursor, opens no window and reads no frame,
so it is safe to run in CI and safe to run while he is playing. The LIVE test — does the pointer
actually land on the item, does the tooltip actually name it — is a separate thing he has asked
for explicitly and has not authorised yet.
"""

import math
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS ⚠ AND ARROWS. Without this a non-UTF-8 console makes it crash
# while REPORTING, so a healthy tree exits non-zero for a reason unrelated to the
# thing being reported. Caught by TestToolsCanReportTheirVerdict, twice in one day.
try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

import slot_identity as SI


def wilson_lower(k, n, z=1.96):
    """Wilson lower bound on k successes of n. -> float in [0,1], or None if n == 0.

    None means NOBODY HAS ASKED — never 0.0. A claim with no attempts and a claim that failed
    every attempt must not render as the same number. [[unknown-stays-unknown]]
    """
    if not n:
        return None
    p = float(k) / float(n)
    d = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n)
    return max(0.0, (centre - margin) / d)


# ══ THE FOUR CLAIMS ═════════════════════════════════════════════════════════════════════════
# Each returns (attempts, caught, notes). "caught" = the claim REFUSED a deliberately wrong
# input. Each probe must be able to come back with caught < attempts, or it is not a probe.

def probe_coordinate(container="stash"):
    """CLAIM: the point I aim at a cell round-trips back to that cell.

    Proved by sabotage: take the honest centre of (c,r), shift it by a full cell, and require
    cell_of() to name a DIFFERENT cell. A converter that ignored its arguments would return the
    same cell for both and be caught here.
    """
    attempts = caught = 0
    notes = []
    # ⚠ HIS REAL FRAME SIZE, NOT A ROUND NUMBER. The first cut probed at 1920x1080 and got
    # UNPROVEN — because panel_box_for correctly REFUSES 1.778 aspect: "outside 1.45-1.62 the
    # horizontal fractions move and nothing here has been measured there yet". That refusal is
    # right and his footage is not 16:9. Measured across 42 of his real frames: 2940x1912, aspect
    # 1.538, squarely inside the band. Probing at a size his camera never produces measures the
    # probe's imagination. [[feedback-fixtures-never-touch-live-data]] in reverse — a fixture so
    # unlike the real input that it exercises nothing.
    box, _why = SI.panel_box_for(2940, 1912, container=container)
    if not box:
        return 0, 0, ["panel_box_for refused his real frame size for %r: %s" % (container, _why)]
    cols, rows = SI.GRIDS.get(container, (0, 0))
    if not cols or not rows:
        return 0, 0, ["no grid for %r" % container]
    cw = float(box[2]) / cols
    ch = float(box[3]) / rows
    for c in range(min(cols, 6)):
        for r in range(min(rows, 4)):
            pt, _ = SI.point_of_cell(c, r, box, container)
            if not pt:
                continue
            # honest direction: it must land where we meant
            got, _ = SI.cell_of(pt, box, container)
            if got != (c, r):
                notes.append("honest round-trip FAILED for (%d,%d): got %r" % (c, r, got))
                continue
            # sabotage: one full cell to the right must NOT be this cell
            attempts += 1
            bad = (pt[0] + cw, pt[1])
            gotb, _ = SI.cell_of(bad, box, container)
            if gotb != (c, r):
                caught += 1
            else:
                notes.append("a point one FULL CELL away still resolved to (%d,%d)" % (c, r))
            # sabotage: one full cell down
            attempts += 1
            bad2 = (pt[0], pt[1] + ch)
            gotc, _ = SI.cell_of(bad2, box, container)
            if gotc != (c, r):
                caught += 1
            else:
                notes.append("a point one full ROW away still resolved to (%d,%d)" % (c, r))
    return attempts, caught, notes


def probe_anchor():
    """CLAIM: the tooltip rectangle tells me which cursor position it belongs to.

    Sabotage: move the rectangle by a large offset and require the recovered anchor to move with
    it. An implementation that returned a constant would be caught.
    """
    attempts = caught = 0
    notes = []
    if not hasattr(SI, "anchor_from_tooltip_rect"):
        return 0, 0, ["anchor_from_tooltip_rect is absent — nothing to probe"]
    # ⚠ THE RECT IS (left, top, RIGHT, BOTTOM), NOT (x, y, w, h). The first cut passed
    # (400,300,260,180) and was refused with "has no area — a tooltip that occupies nothing is not
    # evidence", because right < left. The refusal was correct and the caller was wrong; a probe
    # that reads its own bad input as a finding is worse than no probe.
    base = (400, 300, 660, 480)
    try:
        a0, _w0 = SI.anchor_from_tooltip_rect(base)
    except Exception as e:
        return 0, 0, ["anchor_from_tooltip_rect raised %s" % type(e).__name__]
    if not a0:
        return 0, 0, ["anchor_from_tooltip_rect refused the base rectangle: %s" % _w0]
    for dx, dy in ((250, 0), (0, 250), (-180, 120), (330, -90)):
        attempts += 1
        moved = (base[0] + dx, base[1] + dy, base[2] + dx, base[3] + dy)
        try:
            a1, _ = SI.anchor_from_tooltip_rect(moved)
        except Exception:
            a1 = None
        if a1 and (abs(a1[0] - a0[0] - dx) < 2 and abs(a1[1] - a0[1] - dy) < 2):
            caught += 1
        else:
            notes.append("moving the tooltip by (%d,%d) did not move the anchor with it" % (dx, dy))
    return attempts, caught, notes


def probe_read():
    """CLAIM: two reads of one frame must AGREE to be written.

    Sabotage: hand it pairs that differ in exactly one way each, and require a refusal every time.
    """
    attempts = caught = 0
    notes = []
    box = (0, 0, 1000, 800)
    def s(**kw):
        d = {"frame": "f_1.jpg", "name": "Shako", "point": (120, 120),
             "panelBox": box, "container": "stash", "tab": "personal"}
        d.update(kw)
        return d
    cases = [
        ("different NAME", s(), s(name="Harlequin Crest")),
        ("different FRAME", s(), s(frame="f_2.jpg")),
        ("different CELL", s(), s(point=(700, 600))),
        ("an empty name", s(), s(name="")),
        ("a missing frame", s(), s(frame="")),
    ]
    for why, a, b in cases:
        attempts += 1
        try:
            ok, _ = SI.double_read_agrees(a, b)
        except Exception:
            ok = True                      # a crash is not a refusal
        if not ok:
            caught += 1
        else:
            notes.append("a pair with %s was ACCEPTED as an agreeing double read" % why)
    # and the honest direction must still pass, or the check is merely broken
    try:
        ok, _ = SI.double_read_agrees(s(), s())
    except Exception:
        ok = False
    if not ok:
        notes.append("⚠ two IDENTICAL reads were refused — this check refuses everything, which "
                     "scores perfectly here and is useless in production")
    return attempts, caught, notes


def probe_slot():
    """CLAIM: agreement about the CELL is a witness the NAME alone cannot fake.

    Sabotage: same name, two different cells in one reel, and require slot-conflict rather than
    same-slot. A tagger that always said `same-slot` would be caught.
    """
    attempts = caught = 0
    notes = []
    box = (0, 0, 1000, 800)
    def s(reel, pt):
        return {"reel": reel, "lane": "claude", "point": pt, "panelBox": box,
                "container": "stash", "tab": "personal"}
    attempts += 1
    t = SI.slot_tags([s("A", (120, 120)), s("A", (700, 600))])
    if "slot-conflict" in t and "same-slot" not in t:
        caught += 1
    else:
        notes.append("one item in TWO cells of one reel did not raise slot-conflict (got %r)" % t)
    attempts += 1
    t2 = SI.slot_tags([s("A", (120, 120)), s("B", (700, 600))])
    if "same-slot" not in t2:
        caught += 1
    else:
        notes.append("two DIFFERENT cells across reels were scored same-slot (got %r)" % t2)
    # honest direction
    t3 = SI.slot_tags([s("A", (120, 120)), s("B", (122, 118))])
    if "same-slot" not in t3:
        notes.append("⚠ two reads of the SAME cell did not earn same-slot — the tagger refuses "
                     "everything, which scores perfectly here and is useless in production")
    return attempts, caught, notes


CLAIMS = (
    ("coordinate", "the point I aim at a cell resolves back to that cell", probe_coordinate),
    ("anchor", "the tooltip rectangle identifies the cursor it belongs to", probe_anchor),
    ("read", "two reads of one frame must agree to be written", probe_read),
    ("slot", "agreement about the cell is a witness the name cannot fake", probe_slot),
)


def score():
    """Score every claim. -> list of dicts, one per claim."""
    out = []
    for key, what, fn in CLAIMS:
        try:
            n, k, notes = fn()
        except Exception as e:
            out.append({"claim": key, "what": what, "attempts": None, "caught": None,
                        "wilson": None, "state": "UNKNOWN",
                        "notes": ["the probe itself raised %s: %s" % (type(e).__name__, str(e)[:70])]})
            continue
        w = wilson_lower(k, n)
        # ⚠ THREE STATES. UNPROVEN is not FAILING — it is "nobody has tried to break this yet".
        if not n:
            state = "UNPROVEN"
        elif k == n:
            state = "PROVEN"
        else:
            state = "LEAKS"
        out.append({"claim": key, "what": what, "attempts": n, "caught": k,
                    "wilson": (round(w, 3) if w is not None else None),
                    "state": state, "notes": notes})
    return out


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    rows = score()
    if "--json" in argv:
        import json
        print(json.dumps(rows, indent=2))
        return 0
    print("HOVER WILSON — the autopilot's four claims, each scored on SABOTAGE ATTEMPTS\n")
    print("  %-12s %9s %8s %8s  %s" % ("claim", "sabotages", "caught", "wilson", "state"))
    print("  " + "-" * 62)
    for r in rows:
        print("  %-12s %9s %8s %8s  %s" % (
            r["claim"],
            "?" if r["attempts"] is None else r["attempts"],
            "?" if r["caught"] is None else r["caught"],
            "—" if r["wilson"] is None else ("%.3f" % r["wilson"]),
            r["state"]))
    leaks = [r for r in rows if r["state"] == "LEAKS"]
    unp = [r for r in rows if r["state"] in ("UNPROVEN", "UNKNOWN")]
    print()
    for r in rows:
        for n in (r["notes"] or []):
            print("  %-12s %s" % (r["claim"], n))
    print()
    print("  %d claim(s) proven · %d leaking · %d unproven"
          % (len(rows) - len(leaks) - len(unp), len(leaks), len(unp)))
    print("  ⚠ this scores GEOMETRY only. Whether the pointer lands on the item on HIS screen, "
          "and whether the tooltip names it, is the LIVE test and has not been run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
