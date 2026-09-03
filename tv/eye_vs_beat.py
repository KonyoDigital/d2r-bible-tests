#!/usr/bin/env python3
"""A13 — an eye that says the screen is blank while the console says a panel is SHOWN.

His ask: *"i want this part of the workflow.. what about the visual harness with grok bot where is
that?"* — and the half of A13 still unbuilt, in TASKS.md's own words: *"an observation with verdict
LOOKED that CONTRADICTS the console's own beat raises a blocker... not a note in a file."*

⚠⚠ THE JOIN COULD NOT BE MADE AFTER THE FACT, AND THAT IS WHY THE ONE REAL CATCH REACHED NOTHING.
On 2026-09-01 at 16:21:45 the eye reported his webview **blank white** while the beat published
`taskforce shown H=502 top=1050` in a 660px window. That finding sat in an untracked jsonl and
raised no blocker — and it could not have, because **the console publishes a beat and stores no
history of it.** An observation carries a timestamp; the beat exists only live. Nothing can
reconcile the two later.

So the beat is captured AT THE MOMENT OF OBSERVATION and stored on the row. That is the join, and
it only works forward: the 13 rows already in the ledger have no beat, and they are reported
UNKNOWN — never "no contradiction". A count of zero over rows that carry no evidence is measuring
the absence of the evidence. [[unknown-stays-unknown]] [[the-unjoined-end]]

⚠ AND IT DOES NOT TRY TO READ THE OBSERVATION'S PROSE. `saw` is free text written by whoever
looked; deciding in general whether it agrees with a beat is not something this file can do
honestly. It checks ONE mechanical contradiction — the exact shape of the case above:

    the eye says the screen showed NOTHING, and the beat claims a panel is shown with height > 0

Everything else is reported as NEEDS-A-READER, which is a state, not a pass. A gate that guessed at
prose would produce confident nonsense, and a row that cries wolf is one he learns to skip.

    python3 tv/eye_vs_beat.py
    python3 tv/eye_vs_beat.py --json
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CONTRADICTION = "CONTRADICTION"
AGREES = "AGREES"
NEEDS_READER = "NEEDS-A-READER"
NO_BEAT = "NO-BEAT-CAPTURED"

#: Ways an eye says "there was nothing on the screen". Deliberately narrow — every one of these is
#: a phrase that cannot coexist with a panel reported as shown at a real height.
_BLANK = re.compile(
    r"\b(blank|empty|white\s+screen|nothing\s+(?:was\s+)?(?:on|rendered|drawn|visible)|"
    r"no\s+content|showed\s+nothing|all\s+white)\b", re.I)


def capture_beat(fetch=None):
    """What the console is CLAIMING right now. -> (panels, why)

    ⚠ A console that is not running is UNKNOWN, never an empty beat. An absent claim cannot
    contradict anything, and recording it as `{}` would make every future observation look
    agreed-with.
    """
    try:
        import live_panel_gate as LPG
    except Exception as e:
        return None, "live_panel_gate will not import (%s)" % str(e)[:70]
    try:
        status = (fetch or LPG._fetch)()
    except Exception as e:
        return None, "the console did not answer (%s)" % str(e)[:70]
    if not status:
        return None, "the console did not answer, so it is claiming nothing that can be checked"
    try:
        pan = LPG.panels_of(status)
    except Exception as e:
        return None, "the beat could not be read (%s)" % str(e)[:70]
    if not pan:
        return None, "the console answered but published no panels — UNKNOWN, not an empty screen"
    return pan, ""


def _shown_panels(panels):
    """Panels the beat claims are SHOWN with a real height. -> [(name, h)]

    ⚠⚠ IT READS BOTH SHAPES, AND MY FIRST CUT READ ONLY THE FIXTURE ONE. `live_panel_gate.prove()`
    builds beats FLAT — `{"tally": "ZERO-HEIGHT", "tallyH": 0}` — and I wrote this against those,
    because they were the examples in front of me. The LIVE `panels_of()` returns them NESTED:

        {"advanced": {"state": "shown", "h": 1309, "top": 232, "vh": 628}, ...}

    So against his running console this returned [] while the beat plainly claimed `advanced`
    shown at h=1309 — and the check reported AGREES on the exact contradiction shape it exists to
    catch. Reading the fixture and assuming it is the world is how a guard passes the one case it
    was written for. [[feedback-blind-fixture-green-gate]]
    """
    out = []
    for k, v in (panels or {}).items():
        state, h = None, None
        if isinstance(v, dict):                       # the LIVE shape
            state, h = v.get("state"), v.get("h")
        elif isinstance(v, str):                      # the FIXTURE shape
            state, h = v, panels.get(k + "H")
        if not isinstance(state, str) or state.strip().lower() != "shown":
            continue
        if isinstance(h, (int, float)) and h > 0:
            out.append((k, h))
    return sorted(out)


def judge(row):
    """One ledger row against the beat stored on it. -> dict"""
    saw = str(row.get("saw") or "")
    verdict = str(row.get("verdict") or "").upper()
    beat = row.get("beatAt")
    base = {"ts": row.get("ts"), "brief": row.get("brief"), "verdict": verdict}
    if verdict != "LOOKED":
        return dict(base, state=NEEDS_READER,
                    why="verdict is %r — only a LOOKED observation claims to have seen anything"
                        % (verdict or "none"))
    if not isinstance(beat, dict) or not beat:
        return dict(base, state=NO_BEAT,
                    why=("no beat was captured with this observation, so there is nothing to "
                         "contradict. UNKNOWN — not agreement."))
    shown = _shown_panels(beat)
    if _BLANK.search(saw) and shown:
        return dict(base, state=CONTRADICTION, shown=shown,
                    why=("the eye reported the screen as blank while the console claimed %d "
                         "panel(s) shown at a real height: %s"
                         % (len(shown), ", ".join("%s H=%s" % (n, h) for n, h in shown[:4]))))
    if _BLANK.search(saw):
        return dict(base, state=AGREES,
                    why="the eye saw nothing and the beat claims no panel is shown — they agree")
    return dict(base, state=NEEDS_READER,
                why=("the observation is prose and does not say the screen was blank. Whether it "
                     "agrees with the beat is a reading, not something this check can decide."))


_UNSET = object()


def report(rows=_UNSET):
    """-> {"state", "rows", "why"}. Reports; never fails a build.

    ⚠⚠ `rows=None` USED TO MEAN TWO THINGS AND THEY ARE OPPOSITES. It was both the default
    ("read the ledger yourself") and the ledger's own UNREADABLE sentinel — so a caller that
    read the ledger, got None because it could not be parsed, and passed it here received a
    clean OK. Two meanings on one value, and the harmless-looking one wins. Caught by its own
    test. [[unknown-stays-unknown]]
    """
    if rows is _UNSET:
        try:
            import human_eyes_ledger as HEL
            rows = HEL._rows()
        except Exception as e:
            return {"state": "UNKNOWN", "rows": [],
                    "why": "the human-eyes ledger could not be read (%s)" % str(e)[:80]}
    if rows is None:
        return {"state": "UNKNOWN", "rows": [],
                "why": "the ledger is UNREADABLE — that is not an absence of observations"}
    obs = [r for r in rows if isinstance(r, dict) and r.get("kind") == "observation"]
    out = [judge(r) for r in obs]
    hits = [o for o in out if o["state"] == CONTRADICTION]
    nobeat = [o for o in out if o["state"] == NO_BEAT]
    return {
        "state": CONTRADICTION if hits else "OK",
        "rows": out, "contradictions": len(hits), "noBeat": len(nobeat),
        "why": (("%d observation(s) contradict the console's own beat" % len(hits)) if hits else
                ("no contradiction among %d observation(s) — but %d of them carry NO CAPTURED BEAT "
                 "and could never have contradicted anything. That is the absence of evidence, "
                 "not evidence of absence." % (len(out), len(nobeat)))),
    }


def main(argv):
    r = report()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print("\nEYE vs BEAT — what was looked at against what the console claimed\n")
    for o in r["rows"]:
        mark = {CONTRADICTION: "⚠ ", NO_BEAT: "? ", AGREES: "  ", NEEDS_READER: "  "}.get(o["state"], "  ")
        print("%s%-14s %-16s %s" % (mark, o["state"], str(o.get("brief"))[:16], o["why"][:96]))
    print("\n  %s\n  %s" % (r["state"], r["why"]))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
