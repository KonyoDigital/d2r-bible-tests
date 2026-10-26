# -*- coding: utf-8 -*-
"""REG-2353 (#42 R16) - THE PUSH-TIME PROVER'S OWN RECORD: what each `heart2.py --prove ... --push` forecast, what it did.

hooks/pre-push deletes its prove log the moment heart2 exits 0, so a push that PASSED left no account of what it proved,
reused, narrowed or re-ran - and tonight's v3783 series (six attempts, ~355 minutes of proving) could be reconstructed
only from logs that happened to survive. Every --push run now appends ONE line (a JSON record) here: per proof the path
forecast before it ran (hit / narrow / full, and why it cannot be banked) beside the path it took, its verdict and its
seconds; the run's wall clock, the inherited HEART2_* seams, the runs a signal ended, the prove-once violations and
the summary heart2 printed (exit code, failures, stop, names that matched no gate).

WHERE: one file per MACHINE, in git's common dir - shared by the main checkout and every worktree, never in a work tree,
so never in `git status`, never copied into a sandbox, never one `git add -A` from this PUBLIC repo. A tree with no git
dir keeps it beside heart2's verdict cache. HEART2_PUSHES_PATH points it anywhere (a law's seam).

THE WRITER: one routine, under an exclusive lock where the platform has one (said in the record when it does not), an
append of ONE line, fsync'd; past KEEP lines the oldest are dropped by a tmp + os.replace rewrite. It writes only a file
named like NAME (or a law's fixture of that name) - the same refusal heart2's cache and red memory keep - and a record it
cannot write is said, never raised: a record costs a line in the log, never a push.
`python3 tv/heart2.py --pushes [N]` prints the last N.
"""
import io
import json
import os
import threading
import time

NAME = "heart2_pushes.jsonl"
KEEP = 200                     # records kept; the oldest leave first
_TRIM_AT = 2 * KEEP            # lines past which the file is rewritten down to KEEP
_LOCK = threading.Lock()


def _git_common_dir(repo):
    """The git COMMON dir of `repo` without running git (a worktree's `.git` file -> its `commondir`). -> path | None"""
    g = os.path.join(repo, ".git")
    try:
        if os.path.isdir(g):
            return g
        if not os.path.isfile(g):
            return None
        with io.open(g, encoding="utf-8") as fh:
            line = fh.read().strip()
        if not line.startswith("gitdir:"):
            return None
        gd = line.split(":", 1)[1].strip()
        gd = gd if os.path.isabs(gd) else os.path.join(repo, gd)
        cd = os.path.join(gd, "commondir")
        if os.path.isfile(cd):
            with io.open(cd, encoding="utf-8") as fh:
                rel = fh.read().strip()
            gd = rel if os.path.isabs(rel) else os.path.join(gd, rel)
        gd = os.path.normpath(gd)
        return gd if os.path.isdir(gd) else None
    except (OSError, ValueError):
        return None


def path(repo=None, cache_path=None, env=None):
    """Where this machine's record lives. -> path"""
    env = os.environ if env is None else env
    if env.get("HEART2_PUSHES_PATH"):
        return env["HEART2_PUSHES_PATH"]
    here = os.path.dirname(os.path.abspath(__file__))
    common = _git_common_dir(repo or os.path.dirname(here))
    if common:
        return os.path.join(common, NAME)
    return os.path.join(os.path.dirname(cache_path) if cache_path else here, "." + NAME)


def _locked(fh):
    """Take an exclusive lock on an open file. -> how ("flock", "msvcrt") | None (no lock on this platform - said)"""
    try:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        return "flock"
    except ImportError:
        pass
    try:
        import msvcrt
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        return "msvcrt"
    except Exception:
        return None


def append(record, where=None, say=None):
    """Append one record. -> the path written | None (said through `say`, never raised)"""
    where = where or path()
    if os.path.basename(where) not in (NAME, "." + NAME):
        if say:
            say("  REG-2353: refusing to write the push record to %s - it is only ever named %s"
                % (os.path.basename(where), NAME))
        return None
    try:
        line = json.dumps(record, sort_keys=True, default=str, ensure_ascii=False)
    except Exception as e:
        if say:
            say("  REG-2353: the push record would not serialise (%s) - not written" % type(e).__name__)
        return None
    try:
        with _LOCK:
            os.makedirs(os.path.dirname(os.path.abspath(where)), exist_ok=True)
            with io.open(where + ".flock", "a+", encoding="utf-8") as lk:
                how = _locked(lk)
                with io.open(where, "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
                    fh.flush()
                    os.fsync(fh.fileno())
                _trim(where)
        if how is None and say:
            say("  REG-2353: no file lock on this platform - the push record was appended without one")
        return where
    except Exception as e:
        if say:
            say("  REG-2353: the push record could not be written (%s) - the run's verdict stands" % type(e).__name__)
        return None


def _trim(where):
    """Past _TRIM_AT lines, keep the newest KEEP (tmp + os.replace, so a kill leaves the old file or the new one)."""
    try:
        if os.path.getsize(where) < 4096:
            return
        with io.open(where, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        if len(lines) <= _TRIM_AT:
            return
        tmp = "%s.%d.%d.tmp" % (where, os.getpid(), threading.get_ident())
        try:
            with io.open(tmp, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines[-KEEP:]) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, where)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    except OSError:
        pass


def read(where=None, n=None):
    """The newest `n` records, oldest first. -> ([record], unreadable line count) | (None, why)"""
    where = where or path()
    if not os.path.exists(where):
        return [], 0
    try:
        with io.open(where, encoding="utf-8", errors="replace") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except OSError as e:
        return None, "the record would not read (%s)" % type(e).__name__
    out, bad = [], 0
    for ln in lines:
        try:
            r = json.loads(ln)
        except ValueError:
            bad += 1
            continue
        if isinstance(r, dict):
            out.append(r)
        else:
            bad += 1
    return (out[-int(n):] if n else out), bad


def table(records):
    """One line per record, for `heart2.py --pushes`. -> [str]. `posix-only`: proofs caught only by cases that skip off
    POSIX (REG-2357) - each files BLIND on a Windows census; `?` on a record written before it was counted.
    REG-2436: `mode` - push (hooks/pre-push's --push run) or census (his heart's own prover, with the proof memory); a
    record from before the census wrote one is a push. `audit`: served PROVENs re-proved / contradicted (REG-2434) -
    `-` where nothing was audited (NOT AUDITED, never clean), `?` on a record from before it was counted."""
    out = ["  when              mode    exit  wall    proofs  forecast h/n/f   actual h/n/f/notrun   audit  violations  "
           "killed  posix-only  gates"]
    for r in records:
        f, a = r.get("forecast") or {}, r.get("actual") or {}
        v = r.get("proveOnceViolations")
        po = r.get("posixOnlyCatch")
        ad, cc = r.get("auditedCount", "?"), r.get("cacheContradictions")
        out.append("  %-16s  %-6s  %-4s  %-6s  %-6s  %-15s  %-20s  %-5s  %-10s  %-6s  %-10s  %s" % (
            time.strftime("%m-%d %H:%M", time.localtime((r.get("at") or 0) / 1000.0)) if r.get("at") else "?",
            r.get("mode") or "push",
            r.get("exit", "?"),
            "%dm%02ds" % divmod(int(r.get("wallS") or 0), 60) if r.get("wallS") is not None else "?",
            r.get("proofs", "?"),
            "%s/%s/%s" % (f.get("hit", "?"), f.get("narrow", "?"), f.get("full", "?")),
            "%s/%s/%s/%s" % (a.get("hit", "?"), a.get("narrow", "?"), a.get("full", "?"), a.get("notRun", "?")),
            "?" if ad == "?" else "-" if not ad and not cc else "%s/%s" % (ad, len(cc or [])),
            "UNKNOWN" if v is None else len(v),
            r.get("signalKilled", "?"),
            len(po) if isinstance(po, list) else "?",
            ",".join((r.get("gates") or [])[:4]) + (" +%d" % (len(r.get("gates")) - 4) if len(r.get("gates") or []) > 4
                                                   else "")))
    return out
