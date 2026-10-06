# -*- coding: utf-8 -*-
"""#42 lever 2 (REG-1720) — A GREEN SUITE RUN IS REUSED ONLY ON IDENTICAL BYTES.

MEASURED 2026-10-02 on v3556's landed push (17m16s): the changed-law proofs took 2 s (lever 1, REG-1710) and the two
python suites took 10m26s - 60% of every push that touches tv/*.py - re-running 2,259 cases the commit had already
passed. His words: "that will make things go so much faster wow" / "that extra percentages of wall clock saving".

So the suites run when the COMMIT is made (`--run`, in the background, from whichever checkout made it) and the push
asks (`--check`) whether a GREEN run exists for these exact bytes. It reuses one only when ALL of this holds:
  * the key is the commit's git TREE hash, and every tracked file is that commit's (the run's own records excepted) -
    a working tree that is not the commit has no key, and runs
  * the same suite, the same python (major.minor) and the same platform
  * the run is younger than MAX_AGE_S - a suite has clocks in it, and a verdict nobody can age cannot keep its age
  * the run was GREEN - only a green run is ever stored, a red one is a finding, never a shortcut
A run still in flight for the same key is WAITED for (`--check NAME --wait S`) - up to S, and NO LONGER: past the
deadline the push runs its own beside it, and the line says "a run of these bytes is still going". A hung run must not
hold a push hostage. (The #231 eye on 86e2b3da: this header said "never started twice", which the code never did.)
⚠ Only `--run` marks itself in flight. The hook's own suite run does not, so a second push of the same bytes on this
machine does not wait for the first push's suite - the pushes are serial by habit (one push at a time), not by code.

⚠ ITS REACH, STATED (the same floor heart2's proof cache states): untracked files - his footage, the stores - are
outside the key. The suites are built hermetic (fixture_tmp.contain, the isolation laws) and CI runs both suites in
full after every push: a reused verdict saves the push's wall clock, it never replaces CI. HEART2/CI-style escape:
SUITE_VERDICT_REUSE=0 makes --check answer "run it" for one push.

The store is per MACHINE and shared by every checkout of this repo (it lives in git's common dir), so a run in the
signin worktree serves the push from main over the same commit. The law: test_a_suite_run_is_reused_only_on_identical_bytes.
[[regression-guard]] [[stale-reading]] [[unknown-stays-unknown]]
"""
import argparse
import io
import json
import os
import platform
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# the hook prints this file's lines, and Windows prints in cp1255 - the one encoding rule, not a second copy of it
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

#: the suites this lane serves - the two that cost a push its minutes (the others it runs take seconds)
SUITES = ("test_agent", "test_control")
#: a verdict older than this is not reused: the suites read clocks
MAX_AGE_S = 6 * 3600
#: entries kept per store; the oldest leave first - a cache, not a ledger
STORE_MAX = 200
#: tracked files a run writes itself - a record of a run cannot change what the suite asserts
SELF_RECORDS = frozenset(("tv/.self_arming.jsonl", "tv/.heart2.json", "tv/.render_verdict.json"))
#: per-suite bound for --run (the hook's own ceiling for test_control)
RUN_TIMEOUT_S = {"test_agent": 600, "test_control": 1500}
#: suites the push hook runs through tv/shard_suite.py - --run uses the same door (REG-1754)
SHARDED = frozenset(("test_control",))


def _git(args, cwd=None):
    """-> stdout str, or None when git could not answer."""
    try:
        p = subprocess.run(["git"] + list(args), cwd=cwd or REPO, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
    except Exception:
        return None
    if p.returncode != 0:
        return None
    return p.stdout


def store_path(cwd=None):
    """The store, in git's COMMON dir - one per machine, shared by main and every worktree. -> path | None"""
    common = _git(["rev-parse", "--git-common-dir"], cwd=cwd)
    if not common:
        return None
    common = common.strip()
    if not os.path.isabs(common):
        common = os.path.join(cwd or REPO, common)
    return os.path.join(os.path.abspath(common), "suite_verdicts.json")


def env_key():
    """the python and platform a verdict was measured on"""
    return "py%d.%d-%s" % (sys.version_info[0], sys.version_info[1], sys.platform)


def ran_cases(out):
    """How many cases a run executed, from its own output. -> int | None

    REG-1915 - a SHARDED run (shard_suite.py) summarises the union as "<ran> of <want> case(s) across <k> shard(s)", and
    this read only unittest's "Ran N tests": a green sharded run printed "(? cases)", and a red one printed ONE shard's
    "Ran 1333 tests" (its tail) as if it were the suite's 2,260. The union line wins whenever it is there; a plain run
    keeps reading "Ran N"; and several plain "Ran" lines (several shards' tails) are never passed off as the whole."""
    import re
    m = None
    for m in re.finditer(r"(\d+) of (\d+) case\(s\) across \d+ shard", out or ""):
        pass
    if m:
        return int(m.group(1))
    rans = []
    for line in (out or "").splitlines():
        if line.startswith("Ran ") and " test" in line:
            try:
                rans.append(int(line.split()[1]))
            except Exception:
                pass
    return rans[0] if len(rans) == 1 else None


def tree_key(cwd=None):
    """-> (key | None, why). The commit's tree hash, ONLY when the working tree's tracked files are that commit's."""
    tree = _git(["rev-parse", "HEAD^{tree}"], cwd=cwd)
    if not tree:
        return None, "git could not name this commit's tree"
    st = _git(["status", "--porcelain", "--untracked-files=no"], cwd=cwd)
    if st is None:
        return None, "git could not say whether the working tree is the commit"
    moved = []
    try:
        import self_prove as _sp                # REG-1865 - the console's own tracked records are not his edits
        _theirs = _sp._edits_beyond_own_records
    except Exception:
        _theirs = None
    for line in st.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _theirs is not None and not _theirs(line):
            continue
        if path and path not in SELF_RECORDS:
            moved.append(path)
    if moved:
        return None, ("%d tracked file(s) differ from the commit (%s) - the bytes a run would grade are not the "
                      "commit's, so there is no key" % (len(moved), ", ".join(moved[:3])))
    return "%s|%s" % (tree.strip(), env_key()), "the commit's tree, unchanged"


def _load(path):
    """-> the store dict; {} when there is no store yet (measured empty); None when it exists and cannot be read -
    UNKNOWN, never an empty store (a corrupt store must not read as 'no runs', and reuse refuses on it)."""
    if not os.path.exists(path):
        return {}
    try:
        with io.open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def _save(path, d):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def record(name, key, ok, cases=None, seconds=None, venue=None, path=None, now=None):
    """Store a run. ONLY a green run is stored. -> bool (stored)"""
    path = path or store_path()
    if not (path and key and ok is True and name in SUITES):
        return False
    d = _load(path) or {}       # an unreadable store is replaced: a cache, so the loss costs a re-run, never a pass
    runs = [r for r in (d.get("runs") or []) if isinstance(r, dict)
            and not (r.get("suite") == name and r.get("key") == key)]
    runs.append({"suite": name, "key": key, "ok": True, "cases": cases, "seconds": seconds,
                 "venue": venue or REPO, "at": float(now if now is not None else time.time())})
    d["runs"] = runs[-STORE_MAX:]
    d.setdefault("inflight", {}).pop("%s|%s" % (name, key), None)
    _save(path, d)
    return True


def reusable(name, key, path=None, now=None, max_age_s=None):
    """-> (run dict | None, why). A green run of NAME on KEY, young enough to keep its verdict."""
    if os.environ.get("SUITE_VERDICT_REUSE", "1") == "0":
        return None, "SUITE_VERDICT_REUSE=0 - reuse closed for this run"
    if not key:
        return None, "no key - the working tree is not a commit"
    path = path or store_path()
    if not path:
        return None, "no store (git could not name its common dir)"
    now = float(now if now is not None else time.time())
    limit = MAX_AGE_S if max_age_s is None else max_age_s
    store = _load(path)
    if store is None:
        return None, "the verdict store exists and could not be read - UNKNOWN, so the suite runs"
    best = None
    for r in (store.get("runs") or []):
        if not isinstance(r, dict) or r.get("suite") != name or r.get("key") != key or r.get("ok") is not True:
            continue
        at = r.get("at")
        if not isinstance(at, (int, float)) or isinstance(at, bool):
            continue                        # a verdict nobody can age cannot keep its age
        if now - at > limit or now - at < -60:
            continue
        if best is None or at > best.get("at"):
            best = r
    if best is None:
        return None, "no green run of %s on these exact bytes in the last %d h" % (name, limit // 3600)
    return best, "a green run of %s on these exact bytes, %d min old" % (name, int((now - best["at"]) // 60))


def _inflight_set(name, key, pid, path):
    d = _load(path) or {}       # as record(): an unreadable store is replaced
    d.setdefault("inflight", {})["%s|%s" % (name, key)] = {"pid": int(pid), "started": time.time()}
    _save(path, d)


def _inflight_clear(name, key, path):
    d = _load(path)
    if d is None:
        return
    if d.get("inflight", {}).pop("%s|%s" % (name, key), None) is not None:
        _save(path, d)


def _pid_alive(pid):
    # ⚠⚠ REG-1725 - os.kill(pid, 0) IS A CTRL-C ON WINDOWS (signal 0 == CTRL_C_EVENT), not a probe. This law runs
    # inside the ALT's prover, so the probe interrupted the prover itself: three slices died of KeyboardInterrupt and
    # each was booked "ended without a census", which backs the river off 3 h. Windows asks the one safe door.
    if os.name == "nt":
        try:
            import self_prove as _sp
            return _sp.pid_alive(pid)
        except Exception:
            return True                     # unknown: the wait is bounded, and a run is never started beside it
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def inflight(name, key, path=None):
    """-> the live in-flight run of NAME on KEY, or None (a dead pid is not in flight)"""
    path = path or store_path()
    if not (path and key):
        return None
    f = ((_load(path) or {}).get("inflight") or {}).get("%s|%s" % (name, key))   # unreadable: nothing known in flight
    if not isinstance(f, dict):
        return None
    # REG-1730 (the v3557 eye) - A RUN THAT WAS KILLED NEVER CLEARS ITS RECORD, AND ITS PID GETS REUSED. A record older
    # than the run's own bound (the run would have been ended by then) names some other process now, never this run -
    # so it is not in flight, and the push does not wait out --wait for a stranger.
    _st = f.get("started")
    # REG-1735 (the v3558 eye) - and a record nobody can age (no numeric start), or one dated in the future (a clock that
    # stepped), cannot keep a push waiting either: a verdict nobody can age cannot keep its age.
    if not isinstance(_st, (int, float)) or isinstance(_st, bool):
        return None
    _age = time.time() - float(_st)
    if _age > RUN_TIMEOUT_S.get(name, 1500) + 120 or _age < -60:
        return None
    if f.get("pid") and _pid_alive(f["pid"]):
        return f
    return None


def run(name, cwd=None):
    """Run one suite here and store the verdict if green. -> (ok bool, line)"""
    key, why = tree_key(cwd)
    path = store_path(cwd)
    src = os.path.join(cwd or REPO, "tv", name + ".py")
    if key and path:
        _inflight_set(name, key, os.getpid(), path)
    # REG-1754 (#160) - THE SAME DOOR AS THE HOOK. The push runs test_control as parallel shards (tv/shard_suite.py,
    # ~2 min); --run ran the file serially (~574 s), so a run started ahead of a push finished AFTER the push's own
    # sharded run would have, and pre-running bought nothing. Same suite, same union verdict, its own ports.
    argv = ([sys.executable, os.path.join(cwd or REPO, "tv", "shard_suite.py"), name] if name in SHARDED
            else [sys.executable, src])
    t0 = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd or REPO, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=RUN_TIMEOUT_S.get(name, 1500))
        out = (p.stdout or "") + (p.stderr or "")
        ok = p.returncode == 0
    except subprocess.TimeoutExpired:
        out, ok = "timed out", False
    finally:
        if key and path:
            _inflight_clear(name, key, path)
    secs = round(time.time() - t0, 1)
    cases = ran_cases(out)
    # REG-1722 - THE KEY IS TAKEN BEFORE THE RUN AND AGAIN AFTER (heart2's proof cache does the same): a file edited
    # while the suite ran means the run graded bytes that are not the commit's, so nothing is stored for it.
    after, _awhy = tree_key(cwd)
    moved = bool(key) and after != key
    stored = ok and not moved and record(name, key, True, cases=cases, seconds=secs, venue=cwd or REPO, path=path)
    if moved:          # REG-1733 (the #231 eye on 100d1203) - a RED run whose tree moved said "the commit's tree, unchanged"
        why = "the tree moved while it ran (%s) - nothing stored" % (_awhy if not after else "a different commit")
    if not ok:                              # a red run names what failed, never only "RED"
        for line in [l for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))][:12]:
            print("   " + line, flush=True)
        # 2026-10-02 - AND SAYS WHY. A name alone sent a load-sensitive budget case to be re-run by hand just to read
        # its message. Each failure's assertion line is printed, and the whole output is kept beside the store.
        for line in [l for l in out.splitlines() if l.startswith(("AssertionError", "TimeoutError"))][:12]:
            print("     " + line[:300], flush=True)
        _log = _red_log(name, out, path)
        if _log:
            print("   the whole red output: %s" % _log, flush=True)
    return ok, "%s %s in %ss (%s cases)%s" % (name, "GREEN" if ok else "RED", secs, cases if cases is not None else "?",
                                               "" if stored else (" - not stored: %s" % why if (not key or moved) else
                                                                  (" - not stored" if ok else "")))


def _red_log(name, out, path):
    """Keep a red run's whole output beside the store. -> the log path, or None when it could not be written."""
    if not path:
        return None
    try:
        p = os.path.join(os.path.dirname(path), "suite_verdict_%s.red.log" % name)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(out)
        return p
    except Exception:
        return None


def check(name, wait_s=0, cwd=None, now=None):
    """-> (reuse bool, line). Waits up to WAIT_S for a run of the same key that is still in flight."""
    key, why = tree_key(cwd)
    if not key:
        return False, "%s: runs - %s" % (name, why)
    path = store_path(cwd)
    deadline = time.time() + max(0, int(wait_s))
    while True:
        r, rwhy = reusable(name, key, path=path, now=now)
        if r:
            return True, ("%s: REUSED %s (%s cases, %ss, run in %s) - CI still runs it in full"
                          % (name, rwhy, r.get("cases") if r.get("cases") is not None else "?", r.get("seconds"),
                             os.path.basename(str(r.get("venue") or "")) or "?"))
        f = inflight(name, key, path=path)
        if not f or time.time() >= deadline:
            return False, "%s: runs - %s%s" % (name, rwhy, " (a run of these bytes is still going)" if f else "")
        time.sleep(10)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", nargs="+", choices=SUITES, help="run these suites here and store green verdicts")
    ap.add_argument("--check", choices=SUITES, help="exit 0 when a green run on these exact bytes can be reused")
    ap.add_argument("--wait", type=int, default=0, help="with --check: wait this long for an in-flight run")
    ap.add_argument("--record", choices=SUITES, help="store a green run the caller just made (the hook's own run)")
    a = ap.parse_args(argv)
    if a.run:
        bad = 0
        for n in a.run:
            ok, line = run(n)
            print(line, flush=True)
            bad += 0 if ok else 1
        return 1 if bad else 0
    if a.check:
        ok, line = check(a.check, wait_s=a.wait)
        print(line, flush=True)
        return 0 if ok else 1
    if a.record:
        key, why = tree_key()
        stored = record(a.record, key, True)
        print("%s: %s" % (a.record, "stored for these exact bytes" if stored else "not stored - %s" % why), flush=True)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
