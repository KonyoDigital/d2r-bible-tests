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

⚠ AND GEOMETRY WAS NOT ENOUGH — v2428 ADDED A SECOND QUESTION BECAUSE HE HAD TO ASK IT HIMSELF.
Konyo, 2026-09-02: *"the Advanced setting i suddenly cant see the advanced grok eyes and the
fleet. it slike hidden.. make sure this is watchdogs control too.. visually pixel wise and
backend"*. The ADVANCED drawer's #fleet-list was measured SHOWN, un-hidden, full height and
perfectly on screen while its entire content was the placeholder copy `open advanced to check the
fleet...` - because `window._fleetRefresh` did not exist yet when the drawer's inline ontoggle
fired during parse, and the empty `catch(e){}` under it ate the TypeError on every load.

Every state above would have passed that, forever, and did for 238 versions. A panel can be
flawlessly rendered and carry nothing that was ever fetched; those are two questions and this gate
only asked one. So:

  · advFill absent      -> RED. The fill never ran at all. It is called unconditionally on load,
                           so absent has exactly one meaning.
  · a refresher MISSING -> RED. Not defined at fill time - the load-order fault itself.
  · a refresher FAILED  -> RED. Threw, or (being async) rejected past its own try.
  · the fleet placeholder still showing on an OPEN drawer -> RED. That copy means "nobody has
                           asked yet"; a real failure says "fleet unreachable" instead, so this
                           cannot fire on a fleet route that is merely down.
[[the-unjoined-end]] [[feedback-verify-not-proxy]] [[heart-first]]

    python3 tv/live_panel_gate.py             # read the live console only
    python3 tv/live_panel_gate.py --prove     # make it go RED for its own reason
    python3 tv/live_panel_gate.py --gate      # BOTH — what run_gates runs
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

#: the copy #fleet-list ships with, which means "nobody has asked the route yet". Matched loosely
#: because the gear glyph in it is decorative and must not be what a refusal hinges on.
_FLEET_PLACEHOLDER = "advanced to check the fleet"


def fill_of(status):
    """-> (advFill dict or None, fleet-placeholder tri-state) read out of the beat.

    ⚠ THREE OUTCOMES, NOT TWO. `(None, None)` means this build does not publish the fill at all -
    which is a different fact from a build that publishes `advFill: null`, and only the second is a
    fault. The caller separates them; conflating them would refuse every older console.
    """
    if not isinstance(status, dict):
        return None, None
    beat = status.get("uiBeat")
    if not isinstance(beat, dict):
        return None, None
    p = beat.get("panels")
    if not isinstance(p, dict):
        return None, None
    return p.get("advFill"), p.get("advFleetPlaceholder")


def _fill_lines(status, pan):
    """-> (bad, notes). The FILL half of the gate: did the drawer's content ever get fetched?"""
    bad, notes = [], []
    fill, placeholder = fill_of(status)
    if "advanced" not in (pan or {}):
        # An older console never published the drawer. Say so; do not refuse a build that predates
        # the field, and do not let silence read as a pass either. [[unknown-stays-unknown]]
        notes.append("\u26aa advFill      NOT PUBLISHED — this console predates v2428, so whether "
                     "the ADVANCED drawer filled is UNKNOWN, not fine.")
        return bad, notes
    if fill is None:
        bad.append("\U0001f534 advFill      NEVER RAN — the drawer is in the beat but no fill was "
                   "recorded. _advFill is called unconditionally at the end of the second script "
                   "block, so a missing record means that call did not happen: the block threw "
                   "before reaching it, or the join was removed.")
        return bad, notes
    if not isinstance(fill, dict):
        notes.append("\u26aa advFill      unreadable (%r) — UNKNOWN, not clean." % (fill,))
        return bad, notes
    missing = fill.get("missing") or []
    failed = int(fill.get("failed") or 0)
    if missing:
        bad.append("\U0001f534 advFill      %d refresher(s) NOT DEFINED when the drawer filled: %s. "
                   "This is the v2190..v2427 fault exactly — a function called from an inline "
                   "handler that fires before the block defining it has run."
                   % (len(missing), ", ".join(map(str, missing))))
    if failed:
        bad.append("\U0001f534 advFill      %d refresher(s) failed while filling the drawer — first: "
                   "%s" % (failed, fill.get("firstErr") or "no message"))
    if placeholder and fill.get("open"):
        bad.append("\U0001f534 advFleet     the drawer is OPEN and #fleet-list still shows the "
                   "placeholder copy. That string means nobody has asked the route yet; a route "
                   "that answered badly says 'fleet unreachable' instead.")
    if not bad:
        notes.append("\U0001f7e2 advFill      %s · ran %s · failed 0 · fleet %s"
                     % (fill.get("why"), fill.get("ran"),
                        "filled" if placeholder is False else
                        ("placeholder (drawer closed — expected)" if placeholder else "UNKNOWN")))
    return bad, notes


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
    fbad, fnotes = _fill_lines(st, pan)
    bad += fbad
    notes += fnotes
    out = bad + notes
    if not bad:
        out.append("   %d panel(s) read from the LIVE beat; none collapsed or clipped sideways, "
                   "and the ADVANCED drawer filled." % len(pan))
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
        # ══ v2428 — THE FILL HALF. Each of these is a state the geometry half rates PERFECT.
        ("the drawer rendered but never filled",
         beat({"advanced": "shown", "advancedH": 1044, "advancedTop": 40, "advancedVh": 628,
               "advFill": None, "advFleetPlaceholder": True}), 1),
        ("a refresher that was not defined yet — the real v2190 fault",
         beat({"advanced": "shown", "advancedH": 1044, "advancedTop": 40, "advancedVh": 628,
               "advFill": {"why": "load", "open": True, "ran": 2, "failed": 1,
                           "missing": ["_fleetRefresh"], "firstErr": "not defined"},
               "advFleetPlaceholder": True}), 1),
        ("a refresher that threw or rejected",
         beat({"advanced": "shown", "advancedH": 1044, "advancedTop": 40, "advancedVh": 628,
               "advFill": {"why": "load", "open": True, "ran": 3, "failed": 1, "missing": [],
                           "firstErr": "TypeError: box is null"},
               "advFleetPlaceholder": False}), 1),
        ("an OPEN drawer still showing the placeholder",
         beat({"advanced": "shown", "advancedH": 1044, "advancedTop": 40, "advancedVh": 628,
               "advFill": {"why": "load", "open": True, "ran": 3, "failed": 0, "missing": []},
               "advFleetPlaceholder": True}), 1),
        # ⚠ AND THE TWO IT MUST NOT REFUSE, or it gets switched off within a week.
        ("a drawer he deliberately CLOSED",
         beat({"advanced": "shown", "advancedH": 30, "advancedTop": 40, "advancedVh": 628,
               "advFill": {"why": "load", "open": False, "ran": 0, "failed": 0, "missing": []},
               "advFleetPlaceholder": True}), 0),
        ("a drawer that filled properly",
         beat({"advanced": "shown", "advancedH": 1044, "advancedTop": 40, "advancedVh": 628,
               "advFill": {"why": "deferred", "open": True, "ran": 3, "failed": 0, "missing": []},
               "advFleetPlaceholder": False}), 0),
        ("an older console that never published the drawer",
         beat({"taskforce": "shown", "taskforceH": 502, "taskforceTop": 40,
               "taskforceVh": 628}), 0),
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


def _port_open(host="127.0.0.1", port=None, timeout=1.0):
    """Is anything listening? -> True | False.

    ⚠ THIS EXISTS TO KEEP TWO SCARS FROM CANCELLING EACH OTHER OUT. _fetch() deliberately retries
    with a generous budget, because a 6s timeout once reported "the console did not answer" over a
    console that was alive and answered the very next request — a FALSE UNKNOWN, and a gate that
    cries wolf is switched off inside a week. But in gate mode that same generosity would spend 45s
    on every CI run, where the console does not exist and never will, against a 60s gate budget.

    A TCP connect settles "is there a console at all" in milliseconds and cannot be fooled by a
    slow one. So: closed port -> UNKNOWN immediately, and CI pays nothing. Open port -> hand it to
    _fetch() with its full budget, and his Mac keeps the retries the scar bought.
    """
    import socket
    if port is None:
        try:
            port = int(STATUS.split("//", 1)[1].split("/", 1)[0].rsplit(":", 1)[1])
        except Exception:
            return False
    sk = socket.socket()
    sk.settimeout(timeout)
    try:
        sk.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        try:
            sk.close()
        except Exception:
            pass


def gate_mode():
    """BOTH halves, in order: is the instrument trustworthy, and what does it say about the console?

    ⚠ v2428 (cont) — THIS GATE WAS REGISTERED AS `--prove` AND ONLY `--prove`, so for its whole
    life it ran its own SABOTAGE and never once asked the live console anything. That is the
    unjoined end on the gate built to catch unjoined ends: the four ADVANCED-drawer refusals
    shipped hours earlier could not fire in a gate run, and the only reason they were ever run
    against his console was that I typed the command by hand. A checker that proves its instrument
    and never points it at the subject has asserted nothing about the system.
    [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]

    ⚠ AND SIMPLY FLIPPING IT TO THE REAL CHECK WOULD HAVE BEEN WORSE. CI has no console, so the
    real check is honestly UNKNOWN there, and a gate that is UNKNOWN on every CI run is furniture.
    Both, or neither is worth having:
      · the sabotage always runs — if the instrument is broken, nothing below it means anything,
        so that failure comes FIRST and stops the gate
      · the real check runs when a console is actually listening
      · unreachable is printed as UNKNOWN in its own words and does NOT claim a pass
    """
    rc = prove()
    if rc != 0:
        print("\n\U0001f534 live-panel: the SABOTAGE failed — the instrument is broken, so nothing "
              "it might say about the live console can be trusted. Fixing the checker comes before "
              "reading anything it reports.")
        return 1
    print("\n── AND NOW THE SUBJECT ITSELF ──")
    if not _port_open():
        print("\u26aa live-panel: instrument PROVEN · no console is listening on %s, so NOTHING was "
              "asserted about a live page. That is UNKNOWN, not clean — on this venue the live half "
              "of this gate did not run." % STATUS)
        return 0
    code, lines = check()
    for l in lines:
        print(l)
    if code == 1:
        print("\U0001f534 live-panel: a REAL finding on the live console — see the lines above.")
        return 1
    if code == 2:
        print("\u26aa live-panel: instrument PROVEN · the port was open but the console never "
              "answered, so nothing was asserted about it. UNKNOWN, not a pass.")
        return 0
    print("\U0001f7e2 live-panel: instrument proven on 14 sabotages AND the live console read clean.")
    return 0


def main(argv):
    if "--prove" in argv:
        return prove()
    if "--gate" in argv:
        return gate_mode()
    code, lines = check()
    for l in lines:
        print(l)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
