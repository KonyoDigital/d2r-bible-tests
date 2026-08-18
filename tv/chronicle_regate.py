"""Re-gate the stored evidence and re-publish the result — WITH A FRESH STAMP.

Re-running the GATE is free; re-running the READS is not. So the ledger gets re-judged whenever the
rules change (a fold added, a threshold moved, a second lane recorded) without spending a single
call. That part already existed. What did not, and what this file is for, is the last inch:

    THE BOARD DEDUPES ADOPTION ON THE SWEEP STAMP.

`_chronAutoAdopt` reads `proposal.startedTs`, falls back to the console's `startedTs`/`restoredFrom`,
compares it against `d2r_chronAdopted`, and returns "this sweep was already adopted" when they match.
`_chron_result_save()` stamps `savedTs` with the current time on every write, so a sweep that runs
normally always presents a new stamp and always adopts.

A re-gate done by hand does not go through that function. On 2026-08-18 the ledger was re-gated in
place after a second lane grounded six held names — 255 grounded became 261 — and the file kept its
ORIGINAL savedTs. Every number in it was correct and the board would have refused all six, quietly,
with a message that reads like success. Nothing would have looked broken: the console would report
261, the board would show 255, and the two would disagree forever with no error anywhere.

That is the-unjoined-end in its purest form — both halves right, the joint silent. So the re-gate
lives here, stamps like the console does, and says out loud what changed.

    python3 tv/chronicle_regate.py            # show what a re-gate would change; writes nothing
    python3 tv/chronicle_regate.py --write    # re-gate and re-publish with a fresh stamp
"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EVIDENCE = os.path.join(HERE, "chron_evidence.json")
RESULT = os.path.join(HERE, "chron_last_result.json")


def regate(evidence_path=EVIDENCE, result_path=RESULT):
    """-> (payload, summary). Pure: builds the new payload, writes nothing."""
    import chronicle_resolve as _res
    import chronicle_retro as _cr

    with open(evidence_path, "r", encoding="utf-8") as fh:
        evidence = json.load(fh)
    roster = _res.load_roster()
    folded, fold_report = _res.fold_proposal(evidence, roster)
    gate = _cr.strict_gate()
    applied = _cr.apply_proposal(folded, {"uniques": [], "sets": []}, gate=gate)

    payload = {}
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    result = payload.get("result") or {}
    before_g = len((result.get("wouldAdd") or {}).get("uniques") or [])
    before_h = len(result.get("held") or [])

    def seen_of(name, ledger="uniques"):
        return [{"reel": s.get("reel"), "frame": s.get("frame"), "lane": s.get("lane") or "claude"}
                for s in (folded.get(ledger, {}).get(name) or [])[:6]]

    result["wouldAdd"] = {"uniques": [
        {"name": n,
         "why": (gate.verdicts.get(n) or {}).get("why", ""),
         "witnesses": (gate.verdicts.get(n) or {}).get("witnesses", []),
         "seen": seen_of(n)}
        for n in applied["uniques"]["added"]]}
    result["held"] = [
        {"ledger": h["ledger"], "name": h["name"],
         "why": (gate.verdicts.get(h["name"]) or {}).get("why", ""),
         "sightings": len(h["sightings"]),
         "seen": [{"reel": s.get("reel"), "frame": s.get("frame"), "lane": s.get("lane") or "claude"}
                  for s in (h["sightings"] or [])[:6]]}
        for h in applied["held"]]
    result["fold"] = fold_report
    lanes = set(result.get("lanes") or [])
    for sightings in folded.get("uniques", {}).values():
        for s in sightings or []:
            lanes.add(s.get("lane") or "claude")
    result["lanes"] = sorted(lanes)
    payload["result"] = result
    # THE WHOLE POINT OF THIS FILE. Stamp exactly as _chron_result_save does, so the board sees a
    # sweep it has not adopted. A re-gate that changes the answer and keeps the stamp is invisible.
    payload["savedTs"] = int(time.time() * 1000)

    summary = {
        "groundedBefore": before_g, "groundedAfter": len(applied["uniques"]["added"]),
        "heldBefore": before_h, "heldAfter": len(applied["held"]),
        "retired": len(fold_report.get("retired") or []),
        "folded": len(fold_report.get("folded") or {}),
        "lanes": result["lanes"],
        "allNamesOnRoster": all(n in set(roster.values()) for n in applied["uniques"]["added"]),
    }
    return payload, summary


def main(argv):
    import console_safe  # noqa: F401
    console_safe.enable()
    sys.path.insert(0, HERE)
    payload, s = regate()
    print("grounded %d -> %d   held %d -> %d   (folded %d, retired %d)"
          % (s["groundedBefore"], s["groundedAfter"], s["heldBefore"], s["heldAfter"],
             s["folded"], s["retired"]))
    print("lanes: %s   every grounded name on the roster: %s" % (s["lanes"], s["allNamesOnRoster"]))
    if not s["allNamesOnRoster"]:
        print("REFUSING to write: a grounded name is not a roster name, which cannot tick on the board")
        return 1
    if "--write" not in argv:
        print("(dry run — pass --write to re-publish with a fresh stamp)")
        return 0
    tmp = RESULT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, default=str)
    os.replace(tmp, RESULT)
    print("wrote %s  savedTs=%d  — the board will see a sweep it has not adopted" % (RESULT, payload["savedTs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
