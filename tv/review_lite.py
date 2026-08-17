#!/usr/bin/env python3
"""Pre-push review — the mechanical defect classes this repo has actually been bitten by.

A git hook cannot invoke the /code-review skill (that is a Claude Code command, not a shell tool),
and a model review on every push would spend subscription calls we now know are finite. So this is
the deterministic half: fast, free, and every check is a scar with a version number behind it.

The model half stays opt-in: TVD_REVIEW=1 runs `claude -p` over the diff and PRINTS its findings
without blocking, because a reviewer that blocks on taste gets disabled within a week.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
findings = []


def add(sev, what, why):
    findings.append((sev, what, why))


def read(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


# ── 1. REG-179, twice: a new console-state file that no test isolates ────────────────────────────
# A new _*_PATH is not isolated until it is named in THREE places. Both times it was missed, the
# suite wrote his live console state - once planting a fixture the board would have adopted.
ca = read(os.path.join(HERE, "control_app.py"))
paths = set(re.findall(r"^(_[A-Z0-9_]*_PATH)\s*=", ca, re.M))
tc = read(os.path.join(HERE, "test_control.py"))
rg = read(os.path.join(HERE, "run_gates.py"))
for var in sorted(paths):
    if not var.startswith("_CHRON") and "SWEPT" not in var and "AUTOREAD" not in var:
        continue
    if var not in tc:
        add("BLOCK", "%s is not isolated in test_control.py" % var,
            "a new state file is live until every suite redirects it (REG-179, twice)")
    m = re.search(re.escape(var) + r"\s*=.*?join\(HERE,\s*[\"']([^\"']+)[\"']", ca)
    fname = m.group(1) if m else None
    if fname and fname not in rg:
        add("BLOCK", "%s (%s) is not watched by run_gates _LIVE_STATE" % (var, fname),
            "the live-state guard is only as wide as that tuple")

# ── 2. v1758 / v1771: a chronicle comparison at the DEFAULT tolerance is blind ────────────────────
# jpeg_sig is a 16x16 fingerprint of the whole frame; at tol=28 two COMPLETELY different Chronicle
# pages compare as 0.00000. Any sig_diff in this module without an explicit tol is that bug again.
cr = read(os.path.join(HERE, "chronicle_retro.py"))
for i, line in enumerate(cr.split("\n"), 1):
    if "sig_diff(" not in line or line.strip().startswith("#"):
        continue
    if "def sig_diff" in line or "tol=" in line:
        continue
    # still_runs is the COARSE question ("same screen?") and is measured to be correct at the
    # default: fine grouping costs 68% more calls for one extra page (v1778). Only the READ
    # selection (_distinct) needs the chronicle tolerance.
    if "still_runs" in cr[max(0, cr.find(line) - 400):cr.find(line)]:
        continue
    add("BLOCK", "chronicle_retro.py:%d compares at the DEFAULT tolerance" % i,
        "tol=28 cannot see a Chronicle page change (v1758); pass tol=CHRON_SIG_TOL")

# ── 3. v1777: a cap too small to read one reel is a cap that blocks the feature ───────────────────
tv = read(os.path.join(HERE, "tv_diablo.py"))
m = re.search(r'_SUB_DAILY_MAX\s*=\s*max\(0,\s*int\(os\.environ\.get\("TV_VISION_DAILY_MAX",\s*"(\d+)"', tv)
if m and int(m.group(1)) < 1000:
    add("BLOCK", "TV_VISION_DAILY_MAX default is %s" % m.group(1),
        "one reel of his Chronicle scroll is ~290 pages; a smaller cap silently blocks every sweep (v1777)")

# ── 4. v1774 / v1777: a blocked reader must refuse, never answer like data ────────────────────────
for fn in ("claude_read", "claude_chronicle_read"):
    m = re.search(r"def %s\(.*?\n(.*?)(?=\ndef )" % fn, tv, re.S)
    body = m.group(1) if m else ""
    for guard in ("_is_throttled", "_sub_budget_check"):
        if guard not in body:
            add("BLOCK", "%s does not consult %s" % (fn, guard),
                "a blocked read that answers scene='gameplay' is read as 'not a Chronicle page' "
                "and skips the whole run (REG-180, REG-181)")

sev_block = [f for f in findings if f[0] == "BLOCK"]
if findings:
    print("pre-push: review-lite findings")
    for sev, what, why in findings:
        print("  %-6s %s" % (sev, what))
        print("         %s" % why)
else:
    print("pre-push: review-lite clean (%d state paths, chronicle tolerances, caps, reader guards)"
          % len(paths))

# opt-in model pass, advisory only
if os.environ.get("TVD_REVIEW") == "1":
    try:
        diff = subprocess.run(["git", "diff", "origin/main...HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=30).stdout[:60000]
        if diff.strip():
            print("pre-push: asking for a second read of the diff (advisory)…")
            r = subprocess.run(
                ["claude", "-p", "Review this diff for real defects only - logic errors, dead "
                 "wiring, guards that cannot fire. No style. Be brief; say NONE if clean.\n\n" + diff],
                capture_output=True, text=True, timeout=180)
            print((r.stdout or "").strip()[:2000] or "  (no answer)")
    except Exception as e:
        print("  advisory review skipped: %s" % e)

sys.exit(1 if sev_block else 0)
