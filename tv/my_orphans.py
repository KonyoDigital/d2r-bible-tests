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
import time
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

#: Executable prefixes that belong to macOS itself. A process running out of one of these is the
#: operating system, whatever it is doing. ⚠ `/usr/local` is NOT here (node, his tools) and neither
#: is /Library/Developer/CommandLineTools (the python I run under) — excusing those would make the
#: sweep unable to see its own author.
SYSTEM_PATHS = ("/System/", "/usr/sbin/", "/usr/libexec/", "/sbin/", "/Library/Apple/")

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


def _parent_of(pid):
    """ppid of `pid`, as a string, or None. Bounded and failure-tolerant by design."""
    try:
        r = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)],
                           capture_output=True, text=True, timeout=5)
        v = (r.stdout or "").strip()
        return v or None
    except Exception:
        return None


def _listening_ports(pid):
    """Ports `pid` itself LISTENS on. -> (set, why)

    ⚠ `-a` ANDs the selectors. Without it lsof ORs them and hands back the whole machine.
    """
    try:
        r = subprocess.run(["lsof", "-nP", "-a", "-p", str(pid), "-iTCP", "-sTCP:LISTEN"],
                           capture_output=True, text=True, timeout=10)
    except Exception as e:
        return set(), "lsof could not be asked (%s)" % type(e).__name__
    out = set()
    for line in (r.stdout or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or "(LISTEN)" not in line:
            continue
        name = parts[-2]
        if ":" not in name:
            continue
        try:
            out.add(int(name.rsplit(":", 1)[1]))
        except ValueError:
            continue
    return out, "read %d listening socket(s)" % len(out)


def holds_his_port(pid):
    """Is this process listening on one of HIS ports? -> (int|None, why)

    ★ THIS FUNCTION IS THE WHOLE POINT OF THIS FILE AND IT DID NOT EXIST.
    `HIS_PORTS` was declared at the top with the comment "a process holding one of these is never
    'mine', whatever else matches" — and MEASURED 2026-09-09: `grep -c HIS_PORTS` was **1**, its
    own definition. Nothing consulted it. `_attribute` promised three positive witnesses in its
    docstring, implemented two, and closed its refusal sentence with the words "holds none of our
    ports" — an assertion about a check that was never run.

    What that cost, the same day: his live console (`control_app.py --open`, holding :17772) came
    back from `_attribute` as `ours=None` — "busy and old, and nothing can say whose it is" — which
    is the shape this tool reports as a suspect. I had separately read one `ps` sample showing it
    at 108% CPU and 17h uptime and was one command from killing it. The guard written to prevent
    exactly that would have agreed with me.

    ⚠ IT FAILS CLOSED. If lsof cannot answer, the port is UNKNOWN and the caller must treat the
    process as NOT-MINE, because the cost of a wrong "mine" is his console and the cost of a wrong
    "not mine" is a process that lives five more minutes.
    [[plumbing-with-no-tap]] [[i-own-everything-i-start]] [[unknown-stays-unknown]]
    """
    # ⚠⚠ THROUGH `_listening_ports`, NOT A SECOND lsof OF ITS OWN. The first cut of this fix
    # inlined the call here AND kept the helper for the ancestry walk — two implementations of one
    # question, which is the drift that produced the stale path resolver earlier the same day. The
    # gate caught it immediately: a test that stubs `_listening_ports` could not move this branch.
    # [[copy-drift]]
    found, why = _listening_ports(pid)
    if not found and "could not be asked" in why:
        # ⚠ FAILS CLOSED. An unanswerable lsof means the port is UNKNOWN, and the caller must treat
        # the process as NOT-MINE: a wrong "mine" costs his console, a wrong "not mine" costs a
        # process five more minutes. [[unknown-stays-unknown]]
        return None, "%s — the port is UNKNOWN, so this is NOT mine" % why
    for port in HIS_PORTS:
        if port in found:
            return port, "listening on :%d, which is HIS by definition" % port
    # ⚠⚠ AND HIS PROCESS TREE, NOT JUST HIS LISTENER. MEASURED 2026-09-09: his console holds
    # :17772 on ONE pid and runs helpers beside it that hold nothing — pid 67244 came back port=0
    # while its parent was the console. Killing a child of his console breaks his console just as
    # surely as killing the listener, so the protection has to cover the tree the port anchors.
    # The walk is bounded and stops at pid 1; a cycle or a vanished parent ends it.
    _seen, _p = set(), pid
    for _ in range(12):
        _pp = _parent_of(_p)
        if not _pp or _pp in ("0", "1") or _pp in _seen:
            break
        _seen.add(_pp)
        _up, _upWhy = _listening_ports(_pp)
        for port in HIS_PORTS:
            if port in _up:
                return port, ("its ancestor pid %s listens on :%d — killing a child of his "
                              "console breaks his console" % (_pp, port))
        _p = _pp
    return 0, ("listens on none of his ports (found %s)"
               % (", ".join(":%d" % p for p in sorted(found)) or "no listening socket"))


def _attribute(pid, cmd):
    """Whose process is this? -> (True|False|None, why)

    True  — positively OURS: registered at spawn, or naming this tree, or holding one of our ports.
    None  — UNATTRIBUTED. Busy, old, not a known system process, and nothing can say whose it is.
            ⚠ THIS IS THE HONEST ANSWER FOR THE CASE THAT MATTERS MOST. Today's real runaway —
            `python3 -c` over bible.html, 100% CPU for 52 minutes — was in no ledger, named no tree
            path, and held no port. A rule that only reported POSITIVE ownership would have said
            nothing about it at all. [[unknown-stays-unknown]]
    """
    # ⚠⚠ HIS PORTS ARE ASKED FIRST, AND THE ANSWER IS FINAL. Ownership is not a majority vote:
    # a process on :17772 is his console even if it names this tree, even if a stale ledger row
    # claims it, even if it is burning a core. Putting this after the positive witnesses would let
    # "names this tree" win — and his console's command line IS this tree.
    _hp, _hpWhy = holds_his_port(pid)
    if _hp is None or _hp:
        return False, ("NEVER MINE — %s" % _hpWhy)
    if str(pid) in _registered_pids():
        return True, "registered by claude-owns at spawn"
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_here)
    if _here in cmd or _root in cmd:
        return True, "names this tree on its command line"
    return None, ("busy and old, and nothing can say whose it is — not in the spawn ledger, does "
                  "not name this tree, and %s" % _hpWhy)


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


def _cpu_sample():
    """{pid: pcpu} from one ps, or None if ps could not be asked. -> dict|None

    ⚠⚠ NONE, NOT `{}`. The swallow ratchet caught this the day it shipped — RANK 1, "a failed read
    handed back as DATA", baseline 74 -> 75, `tv/my_orphans.py 0 -> 1`. An empty dict from a failed
    `ps` is indistinguishable from a real sample of a machine with no processes, and this feeds the
    runaway sweep: a caller comparing against `{}` finds nothing busy and reports a clean machine.
    That is the exact shape of the defect this sweep exists to catch, inside the sweep itself.
    [[unknown-stays-unknown]]
    """
    try:
        raw = subprocess.run(["ps", "-Ao", "pid,pcpu"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    out = {}
    for line in raw.splitlines()[1:]:
        p = line.split()
        if len(p) >= 2:
            try:
                out[p[0]] = float(p[1])
            except ValueError:
                pass
    return out


#: The previous CPU sample and when it was taken. ⚠ THE SECOND SAMPLE COMES FROM THE PREVIOUS
#: CALL, NOT FROM A SLEEP. The first cut slept 4 s inside this function to get its second reading —
#: and `suspects()` runs on the watchdog's TEN-MINUTE TIMER and at every console boot, so the
#: pre-push gate refused the ship with `armed migration (4359 ms, again 4324 ms)`. A supervisor
#: that costs four seconds every ten minutes to answer "is anything running away" is itself the
#: kind of cost it exists to find. Consecutive calls are separated by real time — far more than a
#: sleep would buy — so the samples are better AND free. [[poll-slower-than-its-interval]]
_LAST_SAMPLE = {"at": 0.0, "cpu": {}}


def suspects(busy=BUSY_PCT, old_min=OLD_MIN, settle=0.0):
    """Processes that are BOTH busy and old — the shape a runaway has. -> list of dicts

    ⚠⚠ TWO CPU SAMPLES, NOT ONE, AND THAT IS THE HALF THAT NEARLY COST HIS CONSOLE.
    `ps` %CPU is a DECAYING AVERAGE, not an instantaneous load. MEASURED 2026-09-09 on his console:
    **108.4%**, then 9.0%, then 5.6% — three reads seconds apart, one process, nothing changed. I
    acted on the first, called it "an unbounded process pinning a core for 17 hours", and was one
    command from killing :17772.

    A runaway is busy in BOTH samples. A burst is busy in one. The row now carries both figures and
    `cpu` is the MINIMUM, so a spike cannot promote itself into a verdict.
    [[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]
    """
    out = []
    _now = time.time()
    _prev, _prevAt = _LAST_SAMPLE.get("cpu") or {}, float(_LAST_SAMPLE.get("at") or 0.0)
    _cur = _cpu_sample()
    if _cur is None:
        # the instrument could not be read — that is UNKNOWN, and the previous sample is NOT
        # replaced with an absence that would then look like a quiet machine next time.
        return [{"pid": None, "ours": None,
                 "why": "`ps` could not be asked for a CPU sample, so nothing can be judged about "
                        "runaways right now. This is UNMEASURED, not clean."}]
    _LAST_SAMPLE["cpu"], _LAST_SAMPLE["at"] = _cur, _now
    # ⚠ `settle` REMAINS, so a caller that genuinely wants an immediate second reading can ask for
    # one — but it is OFF by default, because the timer path must stay cheap.
    if settle:
        time.sleep(settle)
        _prev, _prevAt = _cpu_sample(), _now
    _gap = _now - _prevAt
    # ⚠⚠ NO PRIOR SAMPLE IS *UNKNOWN*, NOT "NOTHING IS WRONG". On the first call of a process there
    # is nothing to compare against, and a single decaying average is exactly what nearly cost his
    # console. So the pass reports that it could not judge rather than returning a confident empty
    # list. [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    if not _prev or _gap < 1.0:
        return [{"pid": None, "ours": None,
                 "why": ("only ONE cpu sample is available%s — a single `ps` %%CPU is a decaying "
                         "average, not a load, so no runaway verdict is possible yet. Ask again in "
                         "a moment and this becomes measurable."
                         % ("" if not _prev else " (the previous one is %.1fs old)" % _gap))}]
    _first = _prev
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
        # BOTH samples must clear the bar. An absent first sample means the process is younger
        # than this call, which cannot be a 20-minute runaway.
        cpu0 = _first.get(pid)
        cpu = min(cpu, cpu0) if cpu0 is not None else 0.0
        if cpu < busy or mins < old_min:
            continue
        if any(k in cmd for k in KNOWN):
            continue
        # ⚠⚠ v2847 — AN OS DAEMON IS NEVER MINE, AND A NAME LIST WOULD NOT HAVE COVERED IT.
        # MEASURED the first time this ran: `coreaudiod` — 22.8% and 23.5% across BOTH samples,
        # seven days old — was reported as "busy and old, and nothing can say whose it is". It is
        # busy because he is on a call. It also sits right at the 20% bar, so consecutive runs
        # disagreed about it, which is exactly how a watcher teaches him to ignore it.
        # A PATH RULE, not another name in KNOWN: anything executing out of the OS's own
        # directories belongs to macOS. `/usr/local` is deliberately NOT here — node and his own
        # tools live there — and neither is the CommandLineTools python I run under, so this
        # excuses the system without excusing me. [[unknown-stays-unknown]] [[label-outlived-referent]]
        _bin = cmd.split(None, 1)[0] if cmd else ""
        if _bin.startswith(SYSTEM_PATHS):
            continue
        # ⚠⚠ WHOSE IS IT? Until now this dict was labelled "ours" having tested nothing — `ppid` was
        # parsed on the line above and never read, and the only filter was a substring list that
        # flagged PID 1. Three POSITIVE witnesses are asked, and the answer travels with the row.
        _own, _ownWhy = _attribute(pid, cmd)
        out.append({"pid": pid, "ppid": ppid, "cpu": cpu,
                    "cpuFirst": cpu0, "cpuSecond": float(pcpu), "samples": 2,
                    "minutes": round(mins, 1),
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
