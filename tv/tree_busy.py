# -*- coding: utf-8 -*-
"""v3330 (#72) — IS THE TREE BEING GRADED RIGHT NOW? One definition, so nobody has to remember.

His ruling, from the #46 false-alarm incident: "do not write while a gate runs" must be a REFUSAL,
not a habit. The rule is already written down in CLAUDE.md, in regression-guard, and in every
staged apply-script — as PROSE, four times over. Prose is what fails.

⚠ WHY IT MATTERS, and it is not tidiness: `hooks/pre-push` grades the WORKING TREE, not the commit
(REG-1131). A version banked while the gate is mid-run gets a green verdict about bytes that are
not the ones shipping. That is the most expensive kind of wrong answer this repo produces, because
it looks exactly like a correct one.

TWO INDEPENDENT SIGNALS, because each misses a case the other catches:

  1. THE GATE LOCK. `run_gates._claim_the_tree` takes an exclusive flock on
     `<tmpdir>/d2r_gates_<resolved-tree-key>.lock`, keyed on `os.path.realpath(REPO)` so his two
     worktrees never collide. flock deliberately: the kernel drops it when the process dies, so a
     crashed run cannot leave a stale lock that refuses every future one — its own comment says
     "a pid file would need reaping logic, and reaping logic is how a lock starts lying."
     We try the SAME lock non-blocking and release it immediately; failure means a gate holds it.

  2. A RUNNING pre-push HOOK. The hook does more than run_gates — renders, console demos,
     Playwright smoke — and holds the tree across all of it, including stretches where the gate
     lock is not held. Checking only the lock would call the tree free during the smoke.

⚠⚠ ITS REACH, STATED RATHER THAN IMPLIED. This cannot be forced on an ad-hoc edit. A python
heredoc that writes bible.html directly will never consult a module it does not import, and a
guard that claimed otherwise would read as complete while being optional. What it CAN do is stand
at the one chokepoint every ship passes — `bump_version.py` — so the damaging case becomes
structurally impossible even when the discipline slips. [[the-unjoined-end]]
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# This module PRINTS its reason (main() writes the busy sentence to stderr) and those sentences
# carry non-ASCII. On a cp1255 console that crash happens WHILE REPORTING, so a tree that is
# merely busy would exit non-zero for a reason unrelated to the check — the report killing the
# messenger. Caught by the pre-push encoding gate, which refused this version for exactly it.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
REPO = os.path.dirname(HERE)


def _lock_path(repo=None):
    """The exact path run_gates locks. Keyed on the RESOLVED tree, same as the holder."""
    key = os.environ.get("D2R_GATE_LOCK_KEY") or os.path.realpath(repo or REPO)
    safe = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_")[-80:]
    return os.path.join(tempfile.gettempdir(), "d2r_gates_%s.lock" % safe)


def _gate_lock_held(repo=None):
    """-> (held, who). `held` is None when the question could not be asked at all."""
    try:
        import fcntl
    except Exception:
        return None, "fcntl is unavailable on this platform, so the gate lock cannot be asked"
    p = _lock_path(repo)
    if not os.path.exists(p):
        return False, ""
    try:
        fh = open(p, "a+")
    except Exception as e:
        return None, "the gate lock file could not be opened (%s)" % type(e).__name__
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # We got it, so nobody else holds it. Release AT ONCE — holding it here would make this
        # check the very collision it exists to prevent.
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        return False, ""
    except OSError:
        try:
            fh.seek(0)
            who = (fh.read() or "").strip()
        except Exception:
            who = ""
        return True, (who or "an unnamed gate run")
    finally:
        try:
            fh.close()
        except Exception:
            pass


#: Interpreters that can legitimately be RUNNING the hook. The hook path appearing anywhere else
#: on a command line is a MENTION, not an invocation.
_RUNNERS = ("sh", "bash", "zsh", "dash", "ksh", "perl")


def _is_hook_invocation(cmd):
    """Does this command line RUN the pre-push hook, or merely NAME it?

    ⚠⚠ THE SECOND EYE FOUND THIS (v3331). The first cut was `pgrep -f "hooks/pre-push"`, which
    matches ANY process whose argv contains that substring: `vi hooks/pre-push`, `less
    hooks/pre-push`, a shell whose history line mentions it. Every one of those would have read
    as a running gate and refused EVERY bump, permanently — a guard that fails closed on an
    ordinary editor session is an off switch, not a check. [[strictness-that-closes-the-lane]]
    This is the same correction test-venue already carries for the Playwright scan: match an
    INVOCATION, and pin a mention as a negative fixture.
    """
    toks = (cmd or "").split()
    if not toks:
        return False
    # `git push ...` is what spawns the hook in the first place, and it cannot be confused with
    # an editor. Named in the reason string so a false positive here is diagnosable.
    if os.path.basename(toks[0]) == "git" and "push" in toks[1:3]:
        return True
    for i, t in enumerate(toks):
        if not t.endswith("hooks/pre-push"):
            continue
        if i == 0:
            return True                       # the hook executed directly
        prev = os.path.basename(toks[i - 1])
        return prev in _RUNNERS or prev.startswith("python")
    return False


def _prepush_running(repo=None):
    """-> (running, detail). None when pgrep could not be asked — never False on failure."""
    try:
        r = subprocess.run(["pgrep", "-fl", "hooks/pre-push|git"],
                           capture_output=True, text=True, timeout=10)
    except Exception as e:
        return None, "pgrep could not be asked (%s)" % type(e).__name__
    hits = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        pid, _, cmd = line.partition(" ")
        if _is_hook_invocation(cmd):
            hits.append(pid)
    if not hits:
        return False, ""
    return True, "pid %s" % ", ".join(hits[:4])


def why(repo=None):
    """-> None when the tree is free to write, else ONE sentence naming the holder.

    ⚠ UNKNOWN IS NOT FREE. If neither signal can be asked, this returns a sentence saying so
    rather than None. A writer that cannot find out whether a gate is running must not assume the
    happy answer — that is the confident-zero shape this repo keeps paying for.
    [[unknown-stays-unknown]]
    """
    held, who = _gate_lock_held(repo)
    if held:
        return ("a gate run holds this tree (%s). It grades the WORKING TREE, so writing now "
                "makes its verdict describe bytes that are not the ones shipping." % who)
    running, detail = _prepush_running(repo)
    if running:
        return ("a pre-push hook is running (%s). It grades the WORKING TREE across renders, "
                "console demos and the Playwright smoke — writing now makes its green verdict "
                "about bytes that are not shipping." % detail)
    # ⚠⚠ `or`, NOT `and` — THE SECOND EYE FOUND THIS TOO (v3331). The first cut required BOTH
    # signals to be unaskable before saying UNKNOWN. So a blind flock plus a pgrep that cleanly
    # found nothing fell straight through to `return None` = FREE, with the PRIMARY signal dark.
    # That is the exact confident-zero this module was written to prevent, inside the module that
    # prevents it. One signal silent is enough to refuse. [[unknown-stays-unknown]]
    _dark = []
    if held is None:
        _dark.append(who or "the gate lock could not be read")
    if running is None:
        _dark.append(detail or "the process list could not be read")
    if _dark:
        return ("whether a gate is running could not be determined (%s). That is UNKNOWN, "
                "not free." % "; ".join(_dark))
    return None


def main(argv=None):
    w = why()
    if w:
        sys.stderr.write("tree is BUSY: %s\n" % w)
        return 1
    sys.stdout.write("tree is free\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
