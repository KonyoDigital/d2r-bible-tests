#!/usr/bin/env python3
"""THE LIVE BEAT MUST REACH A REFUSAL. gh #200 follow-up.

Konyo, 2026-09-01: *"we do want to visually verify its working and coded and visually seen.. that
way all the work we do is verified and we can progress forward and not need to come back everytime
to fix these naggy things."*

⚠ WHY render_check.py CANNOT DO THIS JOB, MEASURED RATHER THAN ASSUMED. Adding his real viewport
(1120x628) to that gate was correct and is keeping — but it does not catch this class, and saying
it did would be the false green this repo keeps paying for. At 1120x628, on the same afternoon:

    render_check   taskforce  y=224   h=30    ON-SCREEN   painted 3/3 clipped 0
    the live beat  taskforce  y=1050  h=502   BELOW-FOLD

Both instruments were right. They are looking at DIFFERENT PAGES — the gate renders a seeded
fixture, the console renders his actual state with an update bar, an open state panel and a
sessions strip stacked above the same card — and at `h=30` vs `h=502` they are not even measuring
the same element. A fixture that lays out differently from the app cannot gate the app's layout.
[[feedback-blind-fixture-green-gate]] [[feedback-contradiction-is-the-finding]]

The instrument that CAN see it already exists and already works: `uiBeat.panels`, which since v2404
reports ON-SCREEN / BELOW-FOLD / OFF-SIDE / ZERO-HEIGHT instead of the old binary `shown`, because
`shown` was TRUE for a card sitting at y=1050 in a 628px window. It reports correctly, every few
seconds, and NOTHING READS IT. That is the same defect as the human-eyes ledger this morning: an
observation that reaches nothing is a diagnosis nobody made. [[the-unjoined-end]]

⚠ AND BELOW-FOLD IS NOT AUTOMATICALLY A DEFECT — this gate would be worthless and then ignored if
it cried about a page that simply scrolls. His console window is 660px by DELIBERATE DESIGN (v1464:
a runtime clamp was tried and shipped a window 174px off-screen), so content below the fold is
normal and expected. What is NOT normal is a panel with NO HEIGHT AT ALL: it clips nothing,
overflows nothing, covers nothing, and passes every geometry check ever written, which is exactly
how `inbox 0 clipped` once passed over three nodes at 0x0.

So the refusals are deliberately narrow:
  · ZERO-HEIGHT   -> RED. A panel present in the DOM with h=0 is collapsed, not scrolled away.
  · OFF-SIDE      -> RED. Horizontal is the `.util-strip` scar: clipped, not scrollable.
  · BELOW-FOLD    -> REPORTED, never failed. Grok Bot's eyes settle whether it is reachable (GB-L-5).
  · console down  -> UNKNOWN (exit 2). Not a pass. An instrument I could not reach is an empty seat.

    python3 tv/live_panel_gate.py             # the gate
    python3 tv/live_panel_gate.py --prove     # make it go RED for its own reason
"""
import json
import os
import sys

try:
    from console_safe import enable
    enable()
except Exception:
    pass

STATUS = os.environ.get("TV_CONSOLE_URL", "http://127.0.0.1:17772") + "/api/status"

#: states that mean "this panel cannot be reached by any amount of scrolling"
FATAL = ("ZERO-HEIGHT", "OFF-SIDE")


def _fetch(url=None, timeout=15.0, tries=3):
    """-> dict, or None if the console could not be reached. None is UNKNOWN, never 'clean'.

    ⚠ ONE SHORT TIMEOUT IS NOT EVIDENCE OF AN ABSENT CONSOLE, and the first cut of this gate proved
    it on the first run: a 6s budget reported "the console did not answer — an instrument I could
    not reach is an EMPTY SEAT" over a console that was alive, listening, and answered the very
    next request with a full status blob. That is a FALSE UNKNOWN, and it is corrosive in a
    specific way — a gate that cries wolf gets ignored within a week, so it costs more than having
    no gate at all.

    This endpoint is known to be slow under load: `/api/sessions` was once measured at 172s while
    being polled every 12s, which kept fourteen archive walks permanently in flight. So: retry with
    a real budget, and reserve UNKNOWN for a console that stayed silent across all of it.
    [[poll-slower-than-its-interval]] [[feedback-suspect-the-instrument]]
    """
    import urllib.request
    for _ in range(max(1, tries)):
        try:
            with urllib.request.urlopen(url or STATUS, timeout=timeout) as fh:
                return json.loads(fh.read().decode("utf-8", "replace"))
        except Exception:
            continue
    return None


def panels_of(status):
    """Pull the per-panel states out of a beat. -> {name: {'state','h','top','vh'}} or None.

    ⚠ THE BEAT FLATTENS ITS OWN STRUCTURE. `panels` is not nested per panel; v2403 writes
    `taskforce`, `taskforceH`, `taskforceTop`, `taskforceVh` as SIBLING keys, because the beat is
    serialised into a status blob that many readers already parse. Reassembling here rather than
    changing that shape keeps every existing reader working.
    """
    if not isinstance(status, dict):
        return None
    beat = status.get("uiBeat")
    if not isinstance(beat, dict):
        return None
    p = beat.get("panels")
    if not isinstance(p, dict):
        return None
    out = {}
    for k, v in p.items():
        if not isinstance(v, str):
            continue                      # the H/Top/Vh siblings are numbers; the state is a string
        out[k] = {"state": v, "h": p.get(k + "H"), "top": p.get(k + "Top"), "vh": p.get(k + "Vh")}
    return out or None


def check(status=None):
    """-> (code, lines). 0 green · 1 a real finding · 2 UNKNOWN (which is not a pass)."""
    st = status if status is not None else _fetch()
    # the down-sentinel must produce the SAME message a real unreachable console does, or the
    # sabotage proves the exit code and not the reason.
    if isinstance(st, _Down):
        st = None
    if st is None:
        return 2, ["⚪ UNKNOWN — the console did not answer on %s. That is not a clean console: "
                   "an instrument I could not reach is an EMPTY SEAT, never agreement. Open the "
                   "console and run this again." % STATUS]
    pan = panels_of(st)
    if pan is None:
        return 2, ["⚪ UNKNOWN — the console answered but carries no uiBeat.panels. Either the page "
                   "has not beaten yet, or this build predates the v2404 third state. Absence of a "
                   "reading is not a good reading."]
    bad, notes = [], []
    for name in sorted(pan):
        d = pan[name]
        s = d["state"]
        if s in FATAL:
            bad.append("🔴 %-10s %-12s h=%s top=%s in a %spx viewport — this cannot be reached by "
                       "scrolling. %s" % (name, s, d["h"], d["top"], d["vh"],
                                          "A panel with no height clips nothing and overflows "
                                          "nothing, so every geometry check passes over it."
                                          if s == "ZERO-HEIGHT" else
                                          "Horizontal overflow is clipped, not scrolled."))
        elif s == "OFF-VIEW":
            # v2406 — a fact about which tab is open, not about health. See the beat's note:
            # display:none produces height 0, and treating that as a collapse made this gate refuse
            # his live console on its first real run.
            notes.append("⚪ %-10s OFF-VIEW     not on the visible view — display:none by design, "
                         "no layout boxes at all. Nothing is claimed about it." % name)
        elif s == "BELOW-FOLD":
            notes.append("🟡 %-10s BELOW-FOLD   h=%s top=%s in a %spx viewport — reported, NOT "
                         "failed: his window is 660px by design and a page that scrolls is a page "
                         "working. Whether he can actually find it is a question for eyes (GB-L-5)."
                         % (name, d["h"], d["top"], d["vh"]))
        else:
            notes.append("🟢 %-10s %s" % (name, s))
    out = bad + notes
    if not bad:
        out.append("   %d panel(s) read from the LIVE beat; none collapsed or clipped sideways."
                   % len(pan))
    return (1 if bad else 0), out


def prove():
    """Founding rule 2 — seen RED for its own reason, on fixtures, never on his console."""
    def beat(panels):
        return {"uiBeat": {"panels": panels}}
    cases = [
        ("a collapsed panel",
         beat({"tally": "ZERO-HEIGHT", "tallyH": 0, "tallyTop": 0, "tallyVh": 628}), 1),
        ("a panel clipped sideways",
         beat({"forge": "OFF-SIDE", "forgeH": 181, "forgeTop": 40, "forgeVh": 628}), 1),
        ("below the fold on a scrolling page",
         beat({"taskforce": "BELOW-FOLD", "taskforceH": 502, "taskforceTop": 1050,
               "taskforceVh": 628}), 0),
        ("everything on screen",
         beat({"taskforce": "shown", "taskforceH": 502, "taskforceTop": 40,
               "taskforceVh": 628}), 0),
        ("a console that did not answer", None, 2),
        ("a build with no panels in its beat", {"uiBeat": {"n": 3}}, 2),
        # ⚠ v2406 — THE FALSE RED THAT ACTUALLY HAPPENED, pinned so it cannot come back. On its
        # first run against his live console this gate refused over `tally ZERO-HEIGHT`, which was
        # #hd-tallybar sitting display:none off its own view — healthy, by design, and reported as
        # a defect. A gate that refuses a working console is how a gate gets switched off.
        ("a panel that is simply not on this tab",
         beat({"tally": "OFF-VIEW", "tallyH": 0, "tallyTop": 0, "tallyVh": 628}), 0),
    ]
    bad = 0
    print("PROVING THE LIVE-PANEL GATE — on fixtures, never on his console.\n")
    for why, fixture, want in cases:
        code, lines = check(fixture) if fixture is not None else check(_SENTINEL_DOWN)
        ok = code == want
        bad += 0 if ok else 1
        print("   %s %-38s want %d  got %d" % ("🟢" if ok else "🔴", why, want, code))
        if not ok:
            for l in lines:
                print("        %s" % l)
    print()
    if bad:
        print("🔴 %d case(s) wrong — this gate may not be trusted." % bad)
        return 1
    print("🟢 red for a collapsed or sideways-clipped panel, green for a page that merely scrolls, "
          "UNKNOWN for a console it could not read.")
    return 0


class _Down(object):
    """A stand-in for 'the console did not answer' that check() treats as unreachable.

    ⚠ `None` already means 'go and fetch it live', so the down case cannot be expressed by passing
    None — the sabotage would quietly hit his real console and pass or fail for the wrong reason.
    A sabotage that reaches production is not a sabotage. [[fixtures-never-touch-live-data]]
    """


_SENTINEL_DOWN = _Down()


def main(argv):
    if "--prove" in argv:
        return prove()
    code, lines = check()
    for l in lines:
        print(l)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
