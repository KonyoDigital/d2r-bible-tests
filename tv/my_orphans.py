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
        out.append({"pid": pid, "ppid": ppid, "cpu": cpu, "minutes": round(mins, 1),
                    "cmd": cmd[:150]})
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
