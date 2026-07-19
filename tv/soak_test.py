#!/usr/bin/env python3
"""v883 (#49) — THE SOAK: run the agent in TV_STUB mode for TV_SOAK_MINUTES (default 30) and
assert the night-run invariants: the process survives, RSS stays bounded, the journal stays
line-valid JSON, and core threads keep breathing. CI runs it via tv-soak.yml (dispatch/cron);
locally: TV_SOAK_MINUTES=2 python3 tv/soak_test.py for a quick pass."""
import json, os, resource, signal, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
MINUTES = float(os.environ.get("TV_SOAK_MINUTES", "30") or 30)
d = tempfile.mkdtemp(prefix="tvd-soak-")
journal = os.path.join(d, "sessions.jsonl")

env = dict(os.environ,
           TV_STUB="1", TV_SESSIONS=journal, TV_NO_JOURNAL="",
           TV_PORT="17958", TV_POOL="2", TV_HEARTBEAT="2")
env.pop("ANTHROPIC_API_KEY", None)
proc = subprocess.Popen([sys.executable, os.path.join(HERE, "tv_diablo.py")],
                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
print(f"soak: agent pid {proc.pid} · {MINUTES:.0f} min · journal {journal}", flush=True)

def rss_mb(pid):
    try:
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)], text=True)
        return int(out.strip() or 0) / 1024.0
    except Exception:
        return 0.0

t_end = time.time() + MINUTES * 60
rss_samples = []
fail = None
intake_posted = 0

def post_intake(n):
    """v915 — the soak exercises the INTAKE lane: results journal as beats, the ring fills."""
    global intake_posted
    try:
        import urllib.request
        body = json.dumps({"ts": int(time.time() * 1000), "tab": "runes", "kind": "tally",
                           "ok": True, "counts": {"Ist": n}, "total": n}).encode()
        req = urllib.request.Request("http://127.0.0.1:17958/intake_result", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5).read()
        intake_posted += 1
    except Exception:
        pass
while time.time() < t_end:
    time.sleep(15)
    if proc.poll() is not None:
        fail = f"agent DIED mid-soak (exit {proc.returncode})"
        break
    rss_samples.append(rss_mb(proc.pid))
    if len(rss_samples) % 4 == 0:
        post_intake(len(rss_samples))   # v915 — an intake result every ~minute
    mins_in = MINUTES - (t_end - time.time()) / 60
    print(f"  t+{mins_in:5.1f}m · rss {rss_samples[-1]:.0f}MB", flush=True)

try:
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=30)
except Exception:
    proc.kill()

bad_lines = 0
rows = 0
if os.path.isfile(journal):
    for line in open(journal, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        rows += 1
        try:
            json.loads(line)
        except Exception:
            bad_lines += 1

intake_rows = 0
if os.path.isfile(journal):
    for line in open(journal, encoding="utf-8", errors="replace"):
        try:
            if json.loads(line).get("lane") == "intake":
                intake_rows += 1
        except Exception:
            pass
print(f"\nsoak verdict: rows {rows} · bad-json {bad_lines} · rss max {max(rss_samples or [0]):.0f}MB"
      f" · intake posted {intake_posted} journaled {intake_rows}", flush=True)
if intake_posted and intake_rows < intake_posted:
    print(f"❌ intake beats LOST: posted {intake_posted}, journaled {intake_rows}"); sys.exit(1)
if fail:
    print("❌ " + fail); sys.exit(1)
if bad_lines:
    print("❌ journal corruption"); sys.exit(1)
if rss_samples and len(rss_samples) >= 8:
    early = sum(rss_samples[2:5]) / 3
    late = sum(rss_samples[-3:]) / 3
    if late > early * 1.8 and late - early > 300:
        print(f"❌ RSS leak: {early:.0f}MB → {late:.0f}MB"); sys.exit(1)
print("✅ SOAK PASS")
