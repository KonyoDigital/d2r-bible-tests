# -*- coding: utf-8 -*-
"""#42 lever 4 — RUN ONE SUITE AS N PARALLEL SHARDS, AND REFUSE ANY ANSWER THAT DID NOT RUN EVERY CASE.

MEASURED 2026-10-02 on the v3560 push: the pre-push gate took 17m15s and test_control was ~10 min of it - 2,260 cases in
ONE process - while test_agent took 10 s. Running agent beside control would save 10 s; splitting control is the lever.
Its test servers already bind free ports ("127.0.0.1", 0) and its scratch is contained per process (fixture_tmp), so a
shard is just another process running a subset of its classes.

    python3 tv/shard_suite.py test_control [--shards 4]

· The CLASS is the unit (setUpClass state never splits). Classes are dealt to shards by their last measured cost
  (tv/.suite_class_cost.json, written after every green sharded run), largest first onto the lightest shard; a class
  with no measurement costs the median.
· THE VERDICT IS THE UNION. Green only when every shard exited 0 AND the cases run across shards equal the cases the
  loader found - a shard that crashed at import, ran nothing, or lost a class is RED, never "fewer tests passed".
· Each shard gets its own TV_PORT / TV_CONTROL_PORT so no two shards share a fixed port (#144).
· A class that sets SHARD_ALONE = True (it holds a wall-clock budget) runs in ONE process AFTER the parallel shards
  finish - the push of v3562 went red when four shards and his game slowed the doctor's cheap pass past its budget.
· Exit 0 green, 1 red. The last lines of a red shard are printed, and the whole of it kept beside the cost file.
[[regression-guard]] [[unknown-stays-unknown]] [[test-venue]]
"""
import io
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COST = os.path.join(HERE, ".suite_class_cost.json")
SHARD_TIMEOUT_S = 1500          # the whole suite's own ceiling (suite_verdict.RUN_TIMEOUT_S) bounds each shard too
PORT_BASE = 17981               # shard i uses PORT_BASE+2i (agent) and +2i+1 (control); never 17772 / 17971 / 17972
_LIVE = []                      # the shard processes of the run in progress, so a TERM ends them too (never orphans)

_RUNNER = r'''
import io, json, os, sys, time, unittest
sys.path.insert(0, os.environ["SHARD_HERE"])
sys.argv = [os.environ["SHARD_SUITE"] + ".py"]
mod = __import__(os.environ["SHARD_SUITE"])
names = sorted(json.loads(os.environ["SHARD_CLASSES"]))   # the serial run's order: a shard adds no new ordering
loader = unittest.defaultTestLoader
suite = unittest.TestSuite(loader.loadTestsFromTestCase(getattr(mod, n)) for n in names)
cost, last = {}, [time.time()]
class R(unittest.TextTestResult):
    def startTest(self, t):
        c = type(t).__name__; cost[c] = cost.get(c, 0.0) + time.time() - last[0]; last[0] = time.time()
        super().startTest(t)
    def stopTest(self, t):
        c = type(t).__name__; cost[c] = cost.get(c, 0.0) + time.time() - last[0]; last[0] = time.time()
        super().stopTest(t)
res = unittest.TextTestRunner(stream=sys.stderr, resultclass=R, verbosity=1).run(suite)
json.dump({"ran": res.testsRun, "failures": len(res.failures), "errors": len(res.errors),
           "skipped": len(res.skipped), "ok": res.wasSuccessful(), "cost": cost}, open(os.environ["SHARD_OUT"], "w"))
sys.exit(0 if res.wasSuccessful() else 1)
'''


def _load_plan(suite, here=HERE):
    """The suite's TestCase classes, their case counts, and which must run ALONE. -> ({name: n}, [name, ...])"""
    code = ("import json, os, sys, unittest\nsys.path.insert(0, %r)\nsys.argv = [%r]\n"
            "mod = __import__(%r)\nout = {}\nalone = []\n"
            "for name in dir(mod):\n"
            "    obj = getattr(mod, name)\n"
            "    if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj.__module__ == mod.__name__:\n"
            "        n = unittest.defaultTestLoader.loadTestsFromTestCase(obj).countTestCases()\n"
            "        if n:\n            out[name] = n\n"
            "            if getattr(obj, 'SHARD_ALONE', False) is True:\n                alone.append(name)\n"
            "full = unittest.defaultTestLoader.loadTestsFromModule(mod).countTestCases()\n"
            "print('SHARD_CLASSES ' + json.dumps({'counts': out, 'alone': alone, 'full': full}))\n") % (here, suite + ".py", suite)
    p = subprocess.run([sys.executable, "-c", code], cwd=here, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    for ln in (p.stdout or "").splitlines():
        if ln.startswith("SHARD_CLASSES "):
            got = json.loads(ln[len("SHARD_CLASSES "):])
            return got["counts"], sorted(got["alone"]), got.get("full")
    raise RuntimeError("the suite would not load to be counted: %s" % ((p.stderr or "")[-400:],))


def classes_of(suite, here=HERE):
    """The suite's TestCase classes and their case counts, as the loader sees them. -> {name: n}"""
    return _load_plan(suite, here)[0]


def _costs(suite, path=COST):
    """Last measured seconds per class. -> dict, {} when never measured, None when the file will not read.

    None is not "nothing is slow": the dealer then deals by the median, exactly as for a class never measured."""
    if not os.path.exists(path):
        return {}
    try:
        with io.open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None
    got = d.get(suite) if isinstance(d, dict) else None
    return {k: float(v) for k, v in (got or {}).items() if isinstance(v, (int, float))}


def deal(classes, k, costs):
    """Largest-first onto the lightest shard. -> [[class, ...], ...] (k lists, none empty when classes >= k)"""
    known = [c for c in classes if c in costs]
    med = statistics.median([costs[c] for c in known]) if known else 1.0
    # a measured 0.00 (a class under 5 ms) never moved the lightest shard's load, so every such class piled onto one
    # (183 of 483 in one shard, the v3562 eye). Ties go to the shard holding FEWER classes.
    w = {c: float(costs.get(c, med) or 0.0) for c in classes}
    shards = [[] for _ in range(max(1, int(k)))]
    load = [0.0] * len(shards)
    for c in sorted(classes, key=lambda c: (-w[c], c)):
        i = min(range(len(shards)), key=lambda j: (load[j], len(shards[j])))
        shards[i].append(c)
        load[i] += w[c]
    return [s for s in shards if s]


def run(suite, k=4, here=HERE, cost_path=COST, _classes=None, _env=None):
    """Run `suite` as k shards. -> (ok, report dict)"""
    t0 = time.time()
    if _classes is not None:
        found, alone, full = _classes, [], None
    else:
        found, alone, full = _load_plan(suite, here)
    expected = sum(found.values())
    together = sorted(c for c in found if c not in alone)
    plan = deal(together, k, _costs(suite, cost_path) or {})
    tmp = tempfile.mkdtemp(prefix="shard_%s_" % suite)
    procs = []
    _started, _overran = {}, set()      # each shard's budget runs from ITS start; who was ended for overrunning it

    def _start(i, names):
        env = dict(os.environ if _env is None else _env)
        env.update({"SHARD_HERE": here, "SHARD_SUITE": suite, "SHARD_CLASSES": json.dumps(names),
                    "SHARD_OUT": os.path.join(tmp, "shard%d.json" % i),
                    "TV_PORT": str(PORT_BASE + 2 * i), "TV_CONTROL_PORT": str(PORT_BASE + 2 * i + 1),
                    "SHARD_INDEX": str(i)})
        log = io.open(os.path.join(tmp, "shard%d.log" % i), "w", encoding="utf-8")
        _grp = ({"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if os.name == "nt"
                else {"start_new_session": True})
        procs.append((i, names, log, subprocess.Popen([sys.executable, "-c", _RUNNER], cwd=here, env=env,
                                                      stdout=log, stderr=subprocess.STDOUT, **_grp)))
        _LIVE.append(procs[-1][3])
        _started[i] = time.time()

    for i, names in enumerate(plan):
        _start(i, names)
    if alone:
        # the classes that hold a wall-clock budget run AFTER the parallel shards, in one quiet process
        for _i, _n, _log, _p in list(procs):
            try:
                _p.wait(timeout=max(1, SHARD_TIMEOUT_S - (time.time() - _started[_i])))
            except subprocess.TimeoutExpired:
                # the #231 code seat on 22a2f0c3: an overrunning shard was left running and the quiet pass started
                # beside it - the very neighbour it exists to avoid. It is ended (it has failed its budget) first.
                _end_one(_p)
                _overran.add(_i)
        _start(len(plan), alone)
    shards, ok, ran = [], True, 0
    for i, names, log, p in procs:
        try:
            rc = p.wait(timeout=max(1, SHARD_TIMEOUT_S - (time.time() - _started[i])))
        except subprocess.TimeoutExpired:
            _end_one(p)
            rc = "TIMEOUT"
        if i in _overran:
            rc = "TIMEOUT"
        log.close()
        try:
            with io.open(os.path.join(tmp, "shard%d.json" % i), encoding="utf-8") as fh:
                res = json.load(fh)
        except Exception:
            res = None                                   # crashed before it could answer: RED, never "0 failures"
        want = sum(found[n] for n in names)
        got = res.get("ran") if res else None
        sok = rc == 0 and bool(res) and res.get("ok") is True and got == want
        ok = ok and sok
        ran += got or 0
        shards.append({"shard": i, "classes": len(names), "want": want, "ran": got, "rc": rc, "ok": sok,
                       "failures": res and res.get("failures"), "errors": res and res.get("errors"),
                       "log": os.path.join(tmp, "shard%d.log" % i), "cost": (res or {}).get("cost") or {}})
    # two checks, two jobs: each shard ran what it was DEALT (above); every class the loader FOUND was dealt (here)
    # by NAME, never by sum (the #231 code seat on 37e9a984): a plan that dropped one class and dealt another of the
    # same size twice summed equal and read green
    _dealt = sorted(n for _i, names, _l, _p in procs for n in names)
    if _dealt != sorted(found):
        ok = False
    # ⚠ AND THE CLASSES ARE THE WHOLE SUITE (the v3562 eye): `python3 suite.py` loads the MODULE - a load_tests hook or
    # a TestCase imported from elsewhere adds cases no class walk sees. Shards that cover less than the loader would run
    # are a different, smaller verdict. And a suite with nothing in it is never green.
    why_not = ""
    if expected == 0:
        why_not = "the suite has no cases to run - an empty run is not a green one"
    elif full is not None and full != expected:
        why_not = ("the module loads %d case(s) and the classes hold %d - a load_tests hook or an imported TestCase "
                   "is outside the shards" % (full, expected))
    if why_not:
        ok = False
    rep = {"suite": suite, "ok": ok, "expected": expected, "ran": ran, "shards": shards,
           "seconds": round(time.time() - t0, 1), "dir": tmp, "whyNot": why_not}
    if ok:
        # #171 - a green run's scratch (shard logs + answers) goes with it; a RED run's is kept, because its logs are
        # the evidence main() prints and names
        import shutil
        shutil.rmtree(tmp, True)
        rep["dir"] = None
    if ok:
        merged = _costs(suite, cost_path) or {}
        for s in shards:
            merged.update({c: round(v, 2) for c, v in s["cost"].items()})
        try:
            d = {}
            if os.path.exists(cost_path):
                with io.open(cost_path, encoding="utf-8") as fh:
                    d = json.load(fh)
            d[suite] = merged
            tmpf = "%s.%d.tmp" % (cost_path, os.getpid())
            with io.open(tmpf, "w", encoding="utf-8") as fh:
                json.dump(d, fh, indent=0, sort_keys=True)
            os.replace(tmpf, cost_path)
        except Exception:
            pass                                          # a cost file is a scheduling hint, never the verdict
    return ok, rep


def _end_one(p):
    """End one shard AND whatever it started (its own process group), then reap it. Never raises."""
    try:
        if p.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=30)
        else:
            import signal as _sg
            os.killpg(p.pid, _sg.SIGKILL)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
    try:
        p.wait(timeout=30)
    except Exception:
        pass


def _end_shards(signum=None, frame=None):
    """The gate's timeout TERMs this process; its shards - and what they started - go with it. -> exits 128+signum"""
    for p in list(_LIVE):
        _end_one(p)
    if signum is not None:
        sys.exit(128 + int(signum))


def main(argv):
    import argparse
    import signal
    try:
        signal.signal(signal.SIGTERM, _end_shards)
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="run one suite as N parallel shards")
    ap.add_argument("suite")
    ap.add_argument("--shards", type=int, default=int(os.environ.get("SUITE_SHARDS", "4")))
    a = ap.parse_args(argv)
    ok, rep = run(a.suite, a.shards)
    for s in rep["shards"]:
        print("  shard %d: %d class(es), ran %s of %s, rc=%s%s" % (s["shard"], s["classes"], s["ran"], s["want"], s["rc"],
                                                                 "" if s["ok"] else "  ❌ RED"))
    print("%s %s: %s of %s case(s) across %d shard(s) in %.1fs" % (
        "✅" if ok else "❌", rep["suite"], rep["ran"], rep["expected"], len(rep["shards"]), rep["seconds"]))
    if rep.get("whyNot"):
        print("   ❌ " + rep["whyNot"])
    if not ok:
        for s in rep["shards"]:
            if not s["ok"]:
                try:
                    tail = io.open(s["log"], encoding="utf-8", errors="replace").read()[-2500:]
                except Exception:
                    tail = "(no log)"
                print("── shard %d (last lines; whole log: %s) ──\n%s" % (s["shard"], s["log"], tail))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        from console_safe import enable as _console_safe_enable
        _console_safe_enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
