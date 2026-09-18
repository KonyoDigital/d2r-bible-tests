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


def _prepush_running(repo=None):
    """-> (running, detail). None when pgrep could not be asked."""
    try:
        r = subprocess.run(["pgrep", "-f", "hooks/pre-push"],
                           capture_output=True, text=True, timeout=10)
    except Exception as e:
        return None, "pgrep could not be asked (%s)" % type(e).__name__
    pids = [x for x in (r.stdout or "").split() if x.strip()]
    if not pids:
        return False, ""
    return True, "pid %s" % ", ".join(pids[:4])


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
    if held is None and running is None:
        return ("whether a gate is running could not be determined (%s; %s). That is UNKNOWN, "
                "not free." % (who, detail))
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
