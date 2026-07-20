#!/usr/bin/env python3
"""v919 — REAL EYES: prove the SUBSCRIPTION intake lane reads a REAL screenshot.

The stub/CI lanes prove the wiring; this proves THE EYES: a golden fixture JPG through the
REAL locked pipeline (functions/api/intake.js via tv/intake_local.mjs's fetch-shim on the
locally-authorized `claude -p`), asserted against the frozen golden truth.

DELIBERATELY NOT in CI / pre-push / tv-tests (costs a real vision call, needs the Mac's
claude login). Run on demand:

    INTAKE_REAL=1 python3 tv/prove_real_intake.py

Exit codes:  0 PASS · 2 SKIP (gated off / no claude / auth-or-plan wall) · 1 FAIL.
Grok (REAL EYES R1): a website-proxy 200 must NEVER count as local-subscription proof —
this script talks to the node runner DIRECTLY, so the control proxy's fallback can't
fake-green it.
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOLD_DIR = os.path.join(ROOT, "tests", "golden", "intake")
FIXTURE = "chronicle_uniques_A.jpg"
MIN_HITS = 3


def skip(msg):
    print("SKIP:", msg)
    sys.exit(2)


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def main():
    if os.environ.get("INTAKE_REAL") != "1":
        skip("gated — run with INTAKE_REAL=1 (real vision call on the Mac's claude login)")
    claude_bin = os.environ.get("TVD_CLAUDE_BIN", "claude")
    if not shutil.which(claude_bin):
        skip("no `%s` on PATH — subscription lane unavailable" % claude_bin)

    goldens = json.load(open(os.path.join(GOLD_DIR, "goldens.json")))
    expected = set(goldens.get(FIXTURE) or [])
    if len(expected) < MIN_HITS:
        fail("golden truth for %s has <%d names — fixture set broken" % (FIXTURE, MIN_HITS))
    # vocab: every golden name across the set (18 names — the real board sends ~400;
    # Grok R3: the proof doesn't need the full vocabulary to prove the eyes work)
    vocab = sorted({n for names in goldens.values() for n in names})

    img_b64 = base64.b64encode(open(os.path.join(GOLD_DIR, FIXTURE), "rb").read()).decode()
    payload = {"path": "/api/intake",
               "body": {"image": img_b64, "media_type": "image/jpeg",
                        "kind": "grail", "names": vocab}}

    t0 = time.time()
    pr = subprocess.run(["node", os.path.join(HERE, "intake_local.mjs")],
                        input=json.dumps(payload).encode(), capture_output=True, timeout=240)
    wall = time.time() - t0
    if pr.returncode != 0 or not pr.stdout:
        err = pr.stderr.decode("utf-8", "replace")[-400:]
        if any(t in err.lower() for t in ("not logged in", "login", "rate limit", "credit", "usage limit")):
            skip("claude auth/plan wall: " + err[-160:])
        fail("runner rc=%d stderr: %s" % (pr.returncode, err))

    out = json.loads(pr.stdout.decode("utf-8", "replace"))
    if out.get("lane") != "subscription":
        fail("lane=%r — not the subscription lane" % out.get("lane"))
    if int(out.get("status") or 0) != 200:
        fail("status=%s body=%s" % (out.get("status"), str(out.get("body"))[:300]))
    body = json.loads(out.get("body") or "{}")
    found = []
    for k in ("found", "items", "names"):
        v = body.get(k)
        if isinstance(v, list):
            found = [str(x) for x in v]
            break
    if not found and isinstance(body.get("tally"), dict):
        found = list(body["tally"].keys())
    hits = sorted(expected.intersection(found))
    if len(found) > len(expected) + 2:
        fail("over-read / vocab dump: %d names for a %d-name fixture" % (len(found), len(expected)))
    print("REAL EYES: %ds wall · %d read · %d/%d golden hits · sample %s"
          % (wall, len(found), len(hits), len(expected), hits[:5]))
    if len(hits) < MIN_HITS:
        fail("only %d golden hits (<%d) — the eyes did not really read %s"
             % (len(hits), MIN_HITS, FIXTURE))

    # optional wire: if the live agent is up, land the proof as a real intake beat too
    try:
        counts = {n: 1 for n in hits[:5]}
        req = urllib.request.Request(
            "http://127.0.0.1:17771/intake_result",
            data=json.dumps({"kind": "grail", "ok": True, "total": len(hits),
                             "counts": counts, "errors": 0,
                             "frameId": "real_eyes_%d" % int(time.time())}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            print("wire: intake beat journaled (%s)" % r.read()[:60].decode("utf-8", "replace"))
    except Exception:
        print("wire: agent not up — vision proof only (that's fine)")
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
