# -*- coding: utf-8 -*-
"""#172 PHASE B - A SOURCE AUDIT RUNS IN A SHORT-LIVED CHILD, SO ITS PARSE MEMORY LEAVES WITH THE CHILD.

MEASURED 2026-10-27 (#172, a private console on a no-.git copy of his main tree, 150 s, tracemalloc): the console spent
its memory PARSING ITS OWN SOURCE. chronicle_routes.routes() read ~1,400 tv/*.py, held 45.8 MB of decommented text and
ast.parsed them all (939k objects); health_engine._lane_spans() ast.parsed the 49k-line control_app.py (930k objects).
ast.parse builds C-level arenas tracemalloc does not see, and the freed big blocks stay resident: vmmap on his Mac showed
1.2 GB of freed-but-resident MALLOC_LARGE 55 s after a start, and the ALT kept 1.28 GB private on 7.9 GB. Phase A
(REG-2638, v3812) memoised the per-file parses; this is the first parse after an update.

    python3 audit_child.py routes        # derives chronicle_routes.routes() and writes its own disk cache
    python3 audit_child.py lane_spans    # derives health_engine's lane spans and writes LANE_SPANS_CACHE

The child writes the SAME cache the console reads, keyed on the same source stamps, then exits - and its memory with it.

⚠ ONLY A CONSOLE SPAWNS (frame_ref.on_console_path(), set by control_app.main()). Every law, the gate, CI and a CLI run
derive in their own process exactly as before: a law may monkeypatch a module, and a child cannot see a monkeypatch.
⚠ FAILS OPEN: a child that times out, exits non-zero or writes nothing leaves the caller to derive in-process as it
always did, and the failure is recorded here - on / worked / lastTs / say, the heart's vocabulary - never read as clean.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable     # a child on a cp1255 console must never crash while it reports
    _enable()
except Exception:
    pass

#: the marker a child carries, so a child never spawns a child
CHILD_ENV = "TVD_AUDIT_CHILD"
#: a cold route census measured 16.1 s on his Mac (v2692); the ALT is slower. Past this the console derives itself.
TIMEOUT_S = 180
AUDITS = ("routes", "lane_spans")

#: what each audit last did in THIS console: {name: {runs, hits, fails, lastTs, lastMs, lastOk, say}}
STATE = {}


def wanted():
    """Does this process send a cold source audit to a child? -> bool. A console only, and never a child itself."""
    if os.environ.get(CHILD_ENV) == "1":
        return False
    try:
        import frame_ref as _fr
        return bool(_fr.on_console_path())
    except Exception:
        return False


def _row(name):
    return STATE.setdefault(name, {"runs": 0, "hits": 0, "fails": 0, "lastTs": None, "lastMs": None,
                                   "lastOk": None, "say": "not asked since this console started"})


def hit(name):
    """The cache already held the answer: nothing was spawned."""
    _row(name)["hits"] += 1


def run(name, timeout=TIMEOUT_S, _spawn=None):
    """Derive audit `name` in a short-lived child. -> (ok, why). Never raises; the caller reads the cache after."""
    r = _row(name)
    if name not in AUDITS:
        return False, "no audit named %r" % (name,)
    env = dict(os.environ)
    env[CHILD_ENV] = "1"
    t0 = time.time()
    try:
        p = (_spawn or subprocess.run)([sys.executable, os.path.abspath(__file__), name], cwd=HERE, env=env,
                                       capture_output=True, text=True, timeout=timeout,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        ok = p.returncode == 0
        # REG-2733 - the child's OWN sentence first: on the ALT (Python 3.12) stderr carried SyntaxWarnings from the files
        # it parsed, and the last of them stood in for "the routes were derived but their cache was not written"
        _said = ((p.stdout or "").strip().splitlines() or (p.stderr or "").strip().splitlines() or ["-"])[-1][:160]
        why = ("derived in a child process (%.1f s)" % (time.time() - t0) if ok else
               "the child exited %s: %s" % (p.returncode, _said))
    except subprocess.TimeoutExpired:
        ok, why = False, "the child did not finish in %d s" % timeout
    except Exception as e:
        ok, why = False, "the child could not be started (%s)" % type(e).__name__
    r["runs"] += 1
    r["lastTs"] = int(time.time() * 1000)
    r["lastMs"] = int((time.time() - t0) * 1000)
    r["lastOk"] = ok
    if not ok:
        r["fails"] += 1
    r["say"] = why if ok else (why + " - this console derived it itself, in its own memory")
    return ok, why


def status():
    """The heart's vocabulary for the doctor: on / worked / lastTs / say per audit. lastOk None = never asked."""
    on = wanted()
    out = {"on": on, "audits": {}}
    for name in AUDITS:
        r = dict(_row(name))
        r["worked"] = r["runs"] - r["fails"]
        out["audits"][name] = r
    return out


def _write_lane_spans(he):
    """The child's half: write the spans it just derived, keyed on the stat they were derived from, where the engine reads
    them (health_engine._lane_spans_disk). health_engine itself never writes - it reports. -> bool"""
    snap = getattr(he, "_LANE_SPAN_CACHE", None) or {}
    p = he._lane_spans_cache_path()
    if not p or snap.get("val") is None or not snap.get("key"):
        return False
    try:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"key": [int(snap["key"][0]), int(snap["key"][1])],
                       "val": {k: list(v) for k, v in snap["val"].items()}}, fh)
        os.replace(tmp, p)              # atomic: a half-written cache is never readable
        return True
    except Exception:
        return False


def _child(name):
    if name == "routes":
        import chronicle_routes as _cr
        d = _cr.routes()
        if _cr.cached() is None:
            print("the routes were derived but their cache was not written (an unkeyable source?)")
            return 3
        print(json.dumps({"ok": True, "audit": name, "routes": len((d or {}).get("routes") or [])}))
        return 0
    if name == "lane_spans":
        import health_engine as _he
        spans, _src = _he._lane_spans()
        if not _write_lane_spans(_he):
            print("the lane spans were derived but their cache could not be written")
            return 3
        print(json.dumps({"ok": True, "audit": name, "lanes": len(spans)}))
        return 0
    print("no audit named %r" % name)
    return 2


if __name__ == "__main__":
    os.environ[CHILD_ENV] = "1"
    sys.exit(_child(sys.argv[1] if len(sys.argv) > 1 else ""))
