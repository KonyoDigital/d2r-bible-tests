"""THE HUMAN-EYES LEDGER — which briefs were SENT, which were actually LOOKED AT, and which are owed.

Konyo, 2026-09-01, on the Grok Bot harness: *"i want the loop seen"* — *"and verified"*.

WHY THIS EXISTS. The harness is: Claude writes a brief, Grok Bot drives his live console and LOOKS,
it reports what it SAW, Claude diagnoses and ships. That loop has exactly two failure modes and
both are silent:

    1. A brief is written and never run. Nothing happens, nobody notices, and the question it was
       going to settle stays open while looking answered.
    2. A brief comes back with a conclusion and no observation. That reads like evidence and is
       not — a Grok blueprint pass on this very day quoted PROJECT_VAULT_MANAGER.md ACCURATELY and
       reported the wrong gate numbers, because the document had drifted from the code. The quote
       was right and the answer was wrong. Only a separated raw observation catches that.

So this records the loop rather than trusting it. Same shape as tv/second_eye_ledger.py, and for
the same reason: an unasked or unreachable eye is an EMPTY SEAT, never agreement.

⚠ IT DECIDES NOTHING AND WRITES NO CODE. It is a record of what was asked and what came back.
⚠ AND IT IS A RUNTIME DECISION RECORD, like .second_eye.jsonl and .console_scars.json — untracked,
   in .gitignore. His console and this loop both write it; git must not carry it.
"""

import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# ⚠ THIS FILE PRINTS ⚠ AND ARROWS. Without this a non-UTF-8 console makes it crash
# while REPORTING, so a healthy tree exits non-zero for a reason unrelated to the
# thing being reported. Caught by TestToolsCanReportTheirVerdict, twice in one day.
try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

LEDGER_PATH = os.environ.get("TV_HUMAN_EYES_LEDGER") or os.path.join(HERE, ".human_eyes.jsonl")

#: the closed verdict set. A brief comes back as exactly one of these.
LOOKED, UNKNOWN, OWED = "LOOKED", "UNKNOWN", "OWED"


def _rows(path=None):
    """Every row in the ledger. -> list, or None when the file could not be READ.

    ⚠ None IS NOT []. A missing ledger legitimately has no rows — that is `[]`. A ledger that
    EXISTS and could not be opened is UNKNOWN, and returning `[]` for it would tell every caller
    "no briefs have been sent" about a file that might be full of them.

    Caught by tv/swallow_census.py the same day this file was written: `except OSError: return []`
    took the RANK-1 count from 74 to 75 and turned the ratchet red. In the module whose entire job
    is recording a loop honestly. [[unknown-stays-unknown]]
    """
    p = path or LEDGER_PATH
    if not os.path.exists(p):
        return []                       # measured: there is no ledger yet, so there are no rows
    out = []
    try:
        with io.open(p, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    continue            # one bad line is not a bad file
    except OSError:
        return None                     # it EXISTS and would not open — nobody could ask
    return out


def send(brief, claim, why="", path=None):
    """Record that a brief was HANDED OVER. -> the row.

    ⚠ SENDING IS NOT LOOKING. This row is an OWED, and it stays owed until an observation lands
    against it. That is the whole point: a brief nobody ran must be visible as unanswered rather
    than quietly absent. [[unknown-stays-unknown]]
    """
    row = {"ts": int(time.time() * 1000), "kind": "brief", "brief": str(brief),
           "claim": str(claim), "why": str(why)}
    p = path or LEDGER_PATH
    try:
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        return None
    return row


def observed(brief, saw, verdict, conclusion="", shot="", path=None):
    """Record what came BACK. -> the row.

    `saw`        what was on the screen, in its own words. THE RAW OBSERVATION.
    `verdict`    LOOKED or UNKNOWN. Nothing else.
    `conclusion` what it thinks that means — OPTIONAL, and deliberately a separate field.

    ⚠ `saw` AND `conclusion` ARE SEPARATE ON PURPOSE AND MUST STAY SO. On 2026-09-01 a reading
    that was quoted accurately produced a wrong answer because the source had drifted. If the two
    travel in one field, the other side cannot tell which half to trust. [[copy-drift]]

    ⚠ AND UNKNOWN IS A REAL ANSWER, NOT A FAILURE. "I could not see it" closes the brief honestly.
    What must never happen is an absent observation reading as a clean one.
    """
    v = str(verdict).upper()
    if v not in (LOOKED, UNKNOWN):
        v = UNKNOWN
    row = {"ts": int(time.time() * 1000), "kind": "observation", "brief": str(brief),
           "saw": str(saw), "verdict": v, "conclusion": str(conclusion), "shot": str(shot)}
    p = path or LEDGER_PATH
    try:
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        return None
    return row


def state(path=None):
    """Every brief, and whether it was answered. -> list, newest first, or None if UNREADABLE.

    ⚠ None propagates rather than flattening to []. A caller that cannot tell "no briefs" from
    "could not read the ledger" is the defect one layer up.
    """
    rows = _rows(path)
    if rows is None:
        return None
    briefs, obs = {}, {}
    for r in rows:
        b = str(r.get("brief") or "")
        if not b:
            continue
        if r.get("kind") == "brief":
            # ⚠ v2396 — THE LATEST BRIEF WINS, not the first. The first cut used setdefault, so
            # re-sending an id kept the ORIGINAL claim and silently discarded the new one while it
            # sat in the file. A record whose file and whose read disagree is worse than no record.
            # Found by a cross-family review of the shipped v2395.
            briefs[b] = r
        elif r.get("kind") == "observation":
            obs[b] = r
    out = []
    for b, br in briefs.items():
        o = obs.get(b)
        out.append({
            "brief": b,
            "claim": br.get("claim"),
            "sentTs": br.get("ts"),
            "verdict": (o.get("verdict") if o else OWED),
            "saw": (o.get("saw") if o else None),
            "conclusion": (o.get("conclusion") if o else None),
            "answeredTs": (o.get("ts") if o else None),
        })
    # ⚠⚠ AN OBSERVATION FOR A BRIEF NOBODY SENT MUST NOT VANISH. The first cut iterated only the
    # BRIEFS, so an observation whose id did not match one — a typo, a rename, an agent answering
    # something it invented — was dropped from every query with no error and no warning. That is
    # data loss with no author, in the module whose entire job is recording a loop honestly, and
    # three brief ids were hand-typed on the day it shipped.
    # They surface as ORPHAN: something was seen, and nothing asked for it.
    for b, o in obs.items():
        if b in briefs:
            continue
        out.append({
            "brief": b, "claim": None, "sentTs": None,
            "verdict": o.get("verdict"), "saw": o.get("saw"),
            "conclusion": o.get("conclusion"), "answeredTs": o.get("ts"),
            "orphan": True,
        })
    return sorted(out, key=lambda r: -(r.get("sentTs") or r.get("answeredTs") or 0))


def owed(path=None):
    """Briefs handed over and never answered. -> list, or None if the ledger is unreadable."""
    st = state(path)
    if st is None:
        return None
    return [r for r in st if r["verdict"] == OWED]


def proven(path=None):
    """Has the loop EVER completed end to end? -> (bool, why)

    ⚠ THIS IS THE 'verified' HALF OF HIS ASK, AND IT IS DELIBERATELY STRICT. A harness that has
    been designed, documented and never run is exactly the shape of every defect found today: built
    at both ends, joined at neither, and indistinguishable from a working one until somebody looks.
    One completed round trip — a brief sent, an observation returned carrying what was SEEN — is
    the minimum that makes this real. [[the-unjoined-end]]
    """
    st = state(path)
    if st is None:
        return False, ("the ledger exists and could not be read — this is UNKNOWN, not an "
                       "unexercised loop, and the two must not be confused")
    if not st:
        return False, "no brief has ever been sent — the loop is designed, not exercised"
    # ⚠ AN ORPHAN DOES NOT PROVE THE LOOP. Something was seen, but nothing asked for it — so no
    # brief was answered and no round TRIP completed. It is a finding in its own right, not a win.
    done = [r for r in st
            if r["verdict"] == LOOKED and (r.get("saw") or "").strip() and not r.get("orphan")]
    if not done:
        n_owed = len([r for r in st if r["verdict"] == OWED])
        n_unk = len([r for r in st if r["verdict"] == UNKNOWN])
        return False, ("%d brief(s) sent, %d still OWED, %d came back UNKNOWN — no round trip has "
                       "completed with an actual observation" % (len(st), n_owed, n_unk))
    return True, ("the loop has completed %d time(s); most recent: %s"
                  % (len(done), done[0]["brief"]))


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if "--json" in argv:
        ok, why = proven()
        print(json.dumps({"state": state(), "owed": owed(), "proven": ok, "why": why}, indent=2))
        return 0
    st = state()
    print("THE HUMAN-EYES LEDGER — %s\n" % LEDGER_PATH)
    if st is None:
        print("  ⚠ the ledger exists and could not be READ. That is UNKNOWN — not an empty loop.")
        return 0
    if not st:
        print("  no briefs recorded. The loop is designed and has never run.")
    else:
        print("  %-26s %-9s %s" % ("brief", "verdict", "what was seen"))
        print("  " + "-" * 78)
        for r in st:
            print("  %-26s %-9s %s" % (r["brief"][:26], r["verdict"],
                                       (r["saw"] or "—")[:44]))
    ok, why = proven()
    print()
    print("  LOOP VERIFIED: %s — %s" % ("YES" if ok else "NO", why))
    orph = [r for r in st if r.get("orphan")]
    if orph:
        print()
        print("  ⚠ %d ORPHAN observation(s) — something was seen and NOTHING ASKED FOR IT:" % len(orph))
        for r in orph:
            print("     %-26s %s" % (r["brief"][:26], (r.get("saw") or "")[:44]))
    o = owed()
    if o:
        print()
        print("  ⚠ %d brief(s) OWED — handed over and never answered:" % len(o))
        for r in o:
            print("     %-26s %s" % (r["brief"][:26], (r["claim"] or "")[:50]))
    # ⚠ EXIT 0 ALWAYS unless --gate. This is a record, not a build gate; an owed brief is work to
    # do, and turning it into a red build is how a real signal becomes furniture.
    if "--gate" in argv and not ok:
        print("\n  (--gate) the loop has never completed a round trip")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
