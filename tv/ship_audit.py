#!/usr/bin/env python3
"""THE EAGLE EYE POINTED AT MYSELF — what am I allowed to CLAIM right now?

Konyo, 2026-08-24, after a night of green gates over broken code: *"i want you to have a mission. to
intelligently and architecturally code yourself your own self improvement module."*

WHY THIS EXISTS, and it is not a general good idea — it is five specific failures from one night:

  · I ran ONE suite and called it a verdict. CI runs 45 gates; hooks/pre-push runs 2. CI was red for
    THREE consecutive ships and I reported each as clean.
  · A prune deleted three test fixtures. Nothing went red — those cases skipTest when footage is
    absent, so real checks became PERMANENT SKIPS. Twice before, the same way.
  · Seven of my own guards read his LIVE tv/frames/hist. They passed here and ERRORED on the runner.
  · Guards went green that could not fail, and sabotages "passed" that had changed nothing.
  · Four visual regressions shipped and HE was the only detector.

Every one of those is a CLAIM I made that outran my evidence. So this does not test the product —
`tv/run_gates.py` does that. This tests THE CLAIM. It answers one question and refuses to guess:

    given the state of this tree, this receipt, and this CI — what may honestly be said?

DESIGN RULES, each earned:
  · UNKNOWN is a first-class answer. "I could not tell" never resolves to "fine".
  · Evidence must be DURABLE and STAMPED WITH A SHA. A gate that passed against different bytes is
    not evidence about these bytes. [[stale-reading]]
  · It reports; it never fixes, commits, pushes or reruns anything.

Usage:
    python3 tv/ship_audit.py --gates        run all 45 gates, record a receipt for THIS sha
    python3 tv/ship_audit.py --saw-pixels PATH [--surface NAME]   record that a render was LOOKED at
    python3 tv/ship_audit.py --third-eye PATH                     record a different-family review
    python3 tv/ship_audit.py                what may I claim? (exit 1 if any claim is refused)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RECEIPT = os.path.join(HERE, ".ship_receipt.json")

# a commit touching any of these can regress something a person LOOKS at
VISUAL_SURFACES = ("bible.html", "tv/control_ui.html")


def _sh(*argv, **kw):
    """Run a command; return (rc, stdout). Never raises — an unreadable answer is UNKNOWN."""
    try:
        p = subprocess.run(argv, cwd=kw.get("cwd", REPO), capture_output=True, text=True,
                           timeout=kw.get("timeout", 60))
        return p.returncode, (p.stdout or "").strip()
    except Exception as e:
        return 127, "could not run %s: %s" % (argv[0], str(e)[:90])


def _load():
    try:
        with open(RECEIPT, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d):
    tmp = RECEIPT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, RECEIPT)


def _head():
    rc, out = _sh("git", "rev-parse", "HEAD")
    return out if rc == 0 else None


def _dirty():
    rc, out = _sh("git", "status", "--porcelain")
    return None if rc else [l for l in out.split("\n") if l.strip()]


def record_gates():
    """Run the FULL gate set and stamp the result against this exact sha."""
    sha = _head()
    print("▶ running the full gate set against %s …" % (sha or "?")[:12], flush=True)
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, "run_gates.py")],
                       cwd=REPO, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    print(out[-2500:])
    m = re.search(r"✅ (\d+) gate\(s\) passed", out)
    passed = bool(m)
    n_gates = int(m.group(1)) if m else None
    ms = re.search(r"(\d+) CASE\(S\) DID NOT RUN", out)
    skips = int(ms.group(1)) if ms else (0 if passed else None)
    d = _load()
    prev = d.get("gates") or {}
    d["gates"] = {"sha": sha, "ts": int(time.time() * 1000), "passed": passed,
                  "gates": n_gates, "skips": skips, "took_s": round(time.time() - t0, 1),
                  "prevSkips": prev.get("skips")}
    _save(d)
    print("\n▶ receipt written: passed=%s gates=%s skips=%s sha=%s"
          % (passed, n_gates, skips, (sha or "?")[:12]))
    return 0 if passed else 1


def record_evidence(kind, path, surface=None):
    """Record that a render was LOOKED at, or that a different family reviewed it."""
    sha = _head()
    if not os.path.isfile(path):
        print("refusing: %s does not exist — evidence must be a file that is really there" % path)
        return 1
    d = _load()
    rows = d.setdefault(kind, [])
    rows.append({"sha": sha, "ts": int(time.time() * 1000), "path": os.path.abspath(path),
                 "bytes": os.path.getsize(path), "surface": surface})
    d[kind] = rows[-40:]
    _save(d)
    print("recorded %s: %s (%d bytes) against %s" % (kind, path, os.path.getsize(path), (sha or "?")[:12]))
    return 0


def _ci_for(sha):
    """CI verdicts for a sha -> (rows, why). Empty is UNKNOWN, never 'green'."""
    rc, out = _sh("gh", "run", "list", "--limit", "20", "--json",
                  "headSha,conclusion,status,name", timeout=90)
    if rc != 0:
        return None, "gh could not answer (%s)" % out[:70]
    try:
        rows = json.loads(out)
    except Exception:
        return None, "gh returned something this could not parse"
    mine = [r for r in rows if (r.get("headSha") or "").startswith(sha[:12])]
    return mine, None


def audit():
    claims_ok, claims_no = [], []

    def ok(c, why):
        claims_ok.append((c, why))

    def no(c, why):
        claims_no.append((c, why))

    sha = _head()
    if not sha:
        print("refusing: this is not a git tree")
        return 1
    d = _load()
    short = sha[:12]
    print("\U0001f985 SHIP AUDIT — what may be claimed about %s" % short)
    print("   (this tests the CLAIM, not the product. run_gates.py tests the product.)\n")

    # 1 — the working tree
    dirty = _dirty()
    if dirty is None:
        no("nothing", "could not read the working tree")
    elif dirty:
        no("“shipped” / “done”",
           "%d uncommitted file(s) — what is on disk is not what is committed: %s"
           % (len(dirty), ", ".join(x[3:] for x in dirty[:4])))
    else:
        ok("the tree is clean", "nothing uncommitted")

    # 2 — is HEAD actually on origin?
    rc, _ = _sh("git", "merge-base", "--is-ancestor", "HEAD", "origin/main")
    if rc == 0:
        ok("“pushed”", "origin/main contains HEAD")
    else:
        no("“shipped” / “landed”",
           "origin/main does NOT contain HEAD — it exists only on this machine")

    # 3 — gates, and against WHICH bytes
    g = d.get("gates") or {}
    if not g:
        no("“all gates pass”", "no gate receipt at all — run --gates")
    elif g.get("sha") != sha:
        no("“all gates pass”",
           "the receipt is for %s, not %s — a gate that passed against different bytes is not "
           "evidence about these" % ((g.get("sha") or "?")[:12], short))
    elif not g.get("passed"):
        no("“all gates pass”", "the last full run FAILED")
    else:
        ok("“all %s gates pass”" % g.get("gates"), "receipt matches this sha")

    # 4 — skips are not passes
    if g.get("skips") is None:
        no("“fully covered”", "the skip count is UNKNOWN for this run")
    elif g.get("skips"):
        prev = g.get("prevSkips")
        delta = "" if prev is None else (" (was %s)" % prev)
        no("“fully covered”",
           "%s case(s) DID NOT RUN%s — a gate that passes while its cases skip is not covering "
           "them" % (g["skips"], delta))
        if prev is not None and g["skips"] > prev:
            no("“no coverage was lost”",
               "skips went %s → %s: something that used to run does not any more" % (prev, g["skips"]))
    else:
        ok("“every case ran”", "0 skips")

    # 5 — CI, read rather than assumed
    rows, why = _ci_for(sha)
    if rows is None:
        no("“CI is green”", "CI is UNREAD: %s" % why)
    elif not rows:
        no("“CI is green”", "CI has no run for this sha yet — unread is not green")
    else:
        bad = [r for r in rows if r.get("conclusion") not in ("success", None, "")]
        pend = [r for r in rows if r.get("status") != "completed"]
        if bad:
            no("“CI is green”",
               "%d workflow(s) not successful: %s"
               % (len(bad), ", ".join((r.get("name") or "?")[:28] for r in bad[:3])))
        elif pend:
            no("“CI is green”", "%d workflow(s) still running" % len(pend))
        else:
            ok("“CI is green”", "%d workflow(s) succeeded for this sha" % len(rows))

    # 6 — did this commit touch something a person LOOKS at?
    rc, changed = _sh("git", "show", "--name-only", "--pretty=format:", "HEAD")
    touched = [f for f in (changed or "").split("\n") if f.strip()]
    visual = [f for f in touched if f in VISUAL_SURFACES]
    if visual:
        pix = [r for r in (d.get("pixels") or []) if r.get("sha") == sha]
        eye = [r for r in (d.get("thirdEye") or []) if r.get("sha") == sha]
        if pix:
            ok("“I looked at it”", "%d render(s) recorded for this sha" % len(pix))
        else:
            no("“verified visually”",
               "this commit changes %s and NO render was recorded — he must not be the detector"
               % ", ".join(visual))
        if eye:
            ok("“a different family reviewed it”", "%d review(s) recorded" % len(eye))
        else:
            no("“reviewed”",
               "no different-family review recorded for this sha — an unreachable eye is an "
               "EMPTY SEAT, never agreement")
    else:
        ok("no visual claim needed", "this commit touches no rendered surface")

    print("MAY CLAIM:")
    for c, w in claims_ok:
        print("   ✓ %-34s %s" % (c, w))
    print("\nMAY NOT CLAIM:")
    if not claims_no:
        print("   (nothing is refused)")
    for c, w in claims_no:
        print("   ✗ %-34s %s" % (c, w))
    print("\n%s" % ("✅ every claim above is backed by evidence stamped with this sha."
                    if not claims_no else
                    "⚠ %d claim(s) REFUSED. Say the smaller true thing, or go and earn the bigger one."
                    % len(claims_no)))
    return 1 if claims_no else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="What may be claimed about this tree?")
    ap.add_argument("--gates", action="store_true", help="run all gates and record a receipt")
    ap.add_argument("--saw-pixels", default=None, metavar="PATH", help="record a render you LOOKED at")
    ap.add_argument("--surface", default=None, help="which surface the render shows")
    ap.add_argument("--third-eye", default=None, metavar="PATH", help="record a different-family review")
    a = ap.parse_args(argv)
    if a.gates:
        return record_gates()
    if a.saw_pixels:
        return record_evidence("pixels", a.saw_pixels, a.surface)
    if a.third_eye:
        return record_evidence("thirdEye", a.third_eye)
    return audit()


if __name__ == "__main__":
    sys.exit(main())
