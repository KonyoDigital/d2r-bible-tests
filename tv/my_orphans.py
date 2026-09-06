#!/usr/bin/env python3
"""WHAT DID I LEAVE RUNNING? — asked as a step, because he should never be the one who notices.

2026-08-29: he wrote "my pc is super hot.. something is open that isnt closed". A `python3 -c` I
had launched was at 99.7% CPU with an elapsed time of 1 DAY 4 HOURS — a
`glob('~/Library/Application Support/**', recursive=True)`, which over a tree that size never
finishes. It burned a core for 28 hours and the only alarm was the temperature of his laptop.

This reports. IT KILLS NOTHING — killing needs a human look at what the process actually is, and
`pkill -f` is banned on this machine because :17772 is his live console and a pattern cannot tell
his process from mine. [[process-port-discipline]] [[unbounded-search-orphans]]
"""
import io
import json
import os
import subprocess
import sys

# Long-lived and busy by design; not mine and not news.
# ⚠ THIS LIST IS WHAT KEEPS THE SWEEP FROM BECOMING FURNITURE. macOS runs several daemons that are
# legitimately busy for hours — knowledge-agent and contactsd both showed up at >20% CPU on the
# first real run — and a check that flags Apple's own processes every time is one nobody reads by
# the end of the week. Anything added here must be something I did NOT start.
KNOWN = ("xprotect", "mds_stores", "WindowServer", "claude.exe", "Terminal", "spotlight",
         "mdworker", "sysmond", "winedevice", "WhatsApp", "WebKit", "control_app.py",
         "backupd", "photoanalysisd", "cloudd", "bird",
         "knowledge-agent", "contactsd", "suggestd", "corespotlightd", "AppleSpell",
         "com.apple.", "trustd", "syncdefaultsd", "accountsd", "distnoted",
         # v2281 — HIS GAME IS NOT AN ORPHAN. Measured 2026-08-30 while he was playing: D2R.exe at
         # 334% CPU for 100 minutes, flagged as "busy and old" by a sweep whose whole purpose is to
         # catch MY runaway processes. A watcher that cries about the thing the machine exists to
         # run teaches him to ignore it, which is how a real 28-hour core-burner gets missed.
         # CrossOver hosts it, so both spellings appear in the command line.
         "D2R.exe", "Diablo II Resurrected", "CrossOver", "wineserver")

BUSY_PCT = float(os.environ.get("TV_ORPHAN_CPU") or 20.0)
OLD_MIN = int(os.environ.get("TV_ORPHAN_MIN") or 20)


#: Ports that are HIS by definition. A process holding one of these is never "mine", whatever else
#: matches — his console, his Chrome, TradingView, his desktop app.
HIS_PORTS = (17772, 17781, 17955, 9222, 9223, 8848)

#: Where `claude-owns` records what it started. ⚠ INCOMPLETE BY NATURE: 53 rows, last written a day
#: before this was needed, and today's 52-minute runaway was never in it. Registration is a claim
#: about INTENT that has to be made at spawn — so its ABSENCE proves nothing at all.
_SPAWN_LEDGER = os.path.expanduser("~/.claude/claude_spawned.jsonl")


def _registered_pids():
    """Pids `claude-owns` recorded at spawn. -> set (empty if the ledger cannot be read).

    ⚠ AN EMPTY SET IS NOT "NOTHING IS OURS". It is "the ledger said nothing", and the caller must
    not read one as the other — which is exactly why attribution below has a third answer.
    """
    out = set()
    try:
        with io.open(_SPAWN_LEDGER, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                p = row.get("pid")
                if p is not None:
                    out.add(str(p))
    except Exception:
        return set()
    return out


def _attribute(pid, cmd):
    """Whose process is this? -> (True|False|None, why)

    True  — positively OURS: registered at spawn, or naming this tree, or holding one of our ports.
    None  — UNATTRIBUTED. Busy, old, not a known system process, and nothing can say whose it is.
            ⚠ THIS IS THE HONEST ANSWER FOR THE CASE THAT MATTERS MOST. Today's real runaway —
            `python3 -c` over bible.html, 100% CPU for 52 minutes — was in no ledger, named no tree
            path, and held no port. A rule that only reported POSITIVE ownership would have said
            nothing about it at all. [[unknown-stays-unknown]]
    """
    if str(pid) in _registered_pids():
        return True, "registered by claude-owns at spawn"
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_here)
    if _here in cmd or _root in cmd:
        return True, "names this tree on its command line"
    return None, ("busy and old, and nothing can say whose it is — not in the spawn ledger, does "
                  "not name this tree, holds none of our ports")


def _elapsed_minutes(et):
    """`ps` elapsed -> minutes. Formats: MM:SS, HH:MM:SS, D-HH:MM:SS."""
    days = 0
    if "-" in et:
        d, et = et.split("-", 1)
        days = int(d)
    parts = [int(x) for x in et.split(":")]
    if len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        h, m, s = parts[0], parts[1], parts[2]
    return days * 1440 + h * 60 + m + (s / 60.0)


def suspects(busy=BUSY_PCT, old_min=OLD_MIN):
    """Processes that are BOTH busy and old — the shape a runaway has. -> list of dicts"""
    out = []
    try:
        raw = subprocess.run(["ps", "-Ao", "pid,ppid,pcpu,etime,command"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception as e:
        return [{"pid": None, "why": "could not ask ps: %s" % e}]
    for line in raw.splitlines()[1:]:
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, ppid, pcpu, et, cmd = parts
        try:
            cpu = float(pcpu)
            mins = _elapsed_minutes(et)
        except (TypeError, ValueError):
            continue
        if cpu < busy or mins < old_min:
            continue
        if any(k in cmd for k in KNOWN):
            continue
        # ⚠⚠ WHOSE IS IT? Until now this dict was labelled "ours" having tested nothing — `ppid` was
        # parsed on the line above and never read, and the only filter was a substring list that
        # flagged PID 1. Three POSITIVE witnesses are asked, and the answer travels with the row.
        _own, _ownWhy = _attribute(pid, cmd)
        out.append({"pid": pid, "ppid": ppid, "cpu": cpu, "minutes": round(mins, 1),
                    "cmd": cmd[:150], "ours": _own, "whose": _ownWhy})
    return out


def main(argv=None):
    rows = suspects()
    if not rows:
        print("🟢 nothing of mine is both busy and old — no orphan burning a core.")
        return 0
    print("🔴 %d process(es) BUSY (>%.0f%% CPU) and OLD (>%d min) — one of these is why his machine "
          "is hot:" % (len(rows), BUSY_PCT, OLD_MIN))
    for r in rows:
        print("   pid %-7s %5.1f%% CPU  %8.1f min  %s" % (r["pid"], r["cpu"], r["minutes"], r["cmd"]))
    print("   ⚠ LOOK before killing: `ps -o command -p <pid>`, then `kill <pid>`. Never pkill -f — "
          ":17772 is his live console and a pattern cannot tell it from mine.")
    return 1


if __name__ == "__main__":
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
