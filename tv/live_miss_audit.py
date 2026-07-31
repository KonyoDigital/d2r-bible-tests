#!/usr/bin/env python3
"""v1536 — 🔍 WHY DIDN'T IT READ MY STASH? — the live-miss audit.

    python3 tv/live_miss_audit.py                  # this machine's journal
    python3 tv/live_miss_audit.py --json           # same, machine-readable
    python3 tv/live_miss_audit.py path/to/sessions.jsonl

Konyo: *"THE AI READERS arent working properly my cuzin just did a ON AIR and it didnt read his
runestash."*

The honest problem with that report is that "the readers aren't working" can mean five completely
different failures, and they need five different fixes. This does not guess between them: it reads
the session journal — which already records every one of these steps — and says WHICH LINK BROKE.

  A. NEVER SAW THE PANEL     the agent never read scene=stash at all
                             → capture / vision lane, not the tally at all
  B. SAW IT, NEVER NAMED IT  scene=stash but the tab stayed "" or a vault tab
                             → tab identity: the model said nothing and the OCR
                               fallback did not rescue it (the Windows lane uses
                               ocr_win.ps1 + a Windows OCR language pack, which
                               is the likeliest thing to be missing on a cousin box)
  C. NAMED IT, NEVER FIRED   the tab was identified, no intake was attempted
                             → the driver or the board: a tally is fired THROUGH
                               the board window, so a closed board = no tally
  D. FIRED, CAME BACK EMPTY  an intake landed with ok=false or total 0
                             → the read itself, i.e. the prompt/crop
  E. WORKED                  a receipt with a real total

It is deliberately runnable on ANOTHER machine's journal, because that is where the failure lives.
The cousin runs one command and we stop guessing.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TALLY_TABS = ("runes", "gems", "materials")

A_NO_PANEL = "A · never saw the panel"
B_NO_TAB = "B · saw it, never named the tab"
C_NO_FIRE = "C · named it, never fired an intake"
D_EMPTY = "D · fired, came back empty"
E_OK = "E · worked"


def load(path):
    rows = []
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue          # a torn last line is normal on a live journal
    except Exception:
        return None
    return rows


def audit(rows):
    """One verdict per session per tally tab. Pure — give it rows, get findings."""
    sessions = {}
    for r in rows or []:
        sid = r.get("sessionId") or "?"
        s = sessions.setdefault(sid, {
            "sawStash": 0, "tabs": {}, "intakes": {}, "watchdogs": [], "reads": 0, "ts": r.get("ts") or 0,
        })
        lane = r.get("lane") or ""
        scene = (r.get("scene") or "").lower()
        if lane in ("deep", "known", "ocr"):
            s["reads"] += 1
        if scene == "stash":
            s["sawStash"] += 1
            tab = (r.get("stashTab") or "").lower()
            # "" and the vault tabs both mean: NOT identified as a tally tab
            s["tabs"][tab or "(unnamed)"] = s["tabs"].get(tab or "(unnamed)", 0) + 1
        ik = r.get("intake")
        if isinstance(ik, dict):
            t = (ik.get("tab") or "").lower()
            if t:
                cur = s["intakes"].setdefault(t, {"n": 0, "ok": 0, "total": 0})
                cur["n"] += 1
                if ik.get("ok"):
                    cur["ok"] += 1
                try:
                    cur["total"] = max(cur["total"], int(ik.get("total") or 0))
                except (TypeError, ValueError):
                    pass
        wd = r.get("watchdog")
        if isinstance(wd, dict):
            s["watchdogs"].append(wd)

    findings = []
    for sid, s in sessions.items():
        # a session with no reads at all is not a tally failure — say so instead of blaming the tally
        if not s["reads"] and not s["sawStash"]:
            continue
        visited = [t for t in s["tabs"] if t in TALLY_TABS]
        unnamed = s["tabs"].get("(unnamed)", 0)
        for tab in TALLY_TABS:
            got = s["intakes"].get(tab)
            if tab in visited:
                if not got:
                    findings.append((sid, tab, C_NO_FIRE,
                                     "the %s tab was identified on %d frame(s) and no intake was ever attempted"
                                     % (tab, s["tabs"].get(tab, 0))))
                elif not got["ok"] or got["total"] <= 0:
                    findings.append((sid, tab, D_EMPTY,
                                     "%d intake(s) fired for %s; best total was %d"
                                     % (got["n"], tab, got["total"])))
                else:
                    findings.append((sid, tab, E_OK, "%s tallied — total %d" % (tab, got["total"])))
            elif got and got["ok"] and got["total"] > 0:
                # tallied without the tab ever being named: the funnel rescued it (the Mac's normal path)
                findings.append((sid, tab, E_OK,
                                 "%s tallied via the funnel — total %d (the tab itself was never named)"
                                 % (tab, got["total"])))
        if not visited and s["sawStash"] and unnamed:
            findings.append((sid, "-", B_NO_TAB,
                             "the stash panel was read on %d frame(s) and the tab was NEVER identified "
                             "(%d unnamed) — no tally can fire without it" % (s["sawStash"], unnamed)))
        if not s["sawStash"] and s["reads"]:
            findings.append((sid, "-", A_NO_PANEL,
                             "%d frames were read this session and NONE was seen as a stash panel"
                             % s["reads"]))
    return {"sessions": len(sessions), "findings": findings}


def _fix_for(kind):
    return {
        A_NO_PANEL: "the capture/vision lane, not the tally — check the D2R window is being captured "
                    "and the reader is answering at all (tv/chronicle_doctor.py, then the console's read count)",
        B_NO_TAB:   "TAB IDENTITY. The model often says nothing; the OCR fallback is what rescues it. "
                    "On Windows that is tv/ocr_win.ps1 + the Windows OCR language pack — the likeliest "
                    "thing to be missing on a machine that is not Konyo's Mac. Verify: TV_OCR=1 and run "
                    "powershell -File tv/ocr_win.ps1 by hand on one frame.",
        C_NO_FIRE:  "THE BOARD. A tally is fired THROUGH the board window — if the board is closed, "
                    "or the console never got a window handle, the tab is identified and nothing fires.",
        D_EMPTY:    "the READ itself (prompt or crop), not the plumbing — the frame reached the model "
                    "and came back with nothing.",
        E_OK:       "",
    }.get(kind, "")


if __name__ == "__main__":
    import console_safe  # noqa: F401

    argv = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    path = argv[0] if argv else os.path.join(HERE, "sessions.jsonl")
    rows = load(path)
    if rows is None:
        print("⛔ could not read %s" % path)
        raise SystemExit(2)
    res = audit(rows)
    if as_json:
        print(json.dumps({"path": path, "sessions": res["sessions"],
                          "findings": [{"session": a, "tab": b, "verdict": c, "detail": d}
                                       for a, b, c, d in res["findings"]]}, indent=1))
        raise SystemExit(0)

    print("\n🔍 LIVE-MISS AUDIT — %s\n   %d session(s)\n" % (path, res["sessions"]))
    if not res["findings"]:
        # honest-absent: no findings is NOT "everything works", it is "nothing to judge"
        print("   no stash activity in this journal — nothing to judge.")
        print("   (open a stash tab while the console is watching, then run this again)")
        raise SystemExit(0)
    bad = [f for f in res["findings"] if f[2] != E_OK]
    for sid, tab, verdict, detail in res["findings"]:
        mark = "🟢" if verdict == E_OK else "🔴"
        print("  %s %-28s %s" % (mark, verdict, detail))
    print()
    if not bad:
        print("✅ every tally tab that was opened got a real total.")
        raise SystemExit(0)
    print("⛔ %d broken link(s). What to do about each:\n" % len(bad))
    for kind in dict.fromkeys(f[2] for f in bad):
        print("  %s\n    → %s\n" % (kind, _fix_for(kind)))
    raise SystemExit(1)
