# -*- coding: utf-8 -*-
"""v3361 (#98) — THE HOOK ASKS THE CONSOLE WHETHER IT IS STALE, IT DOES NOT TIME ITS PID.

`hooks/pre-push` compared the LISTENER PROCESS START to `tv/control_app.py`'s mtime and warned on
every push where the file was newer. MEASURED 2026-09-19 on his live console, in one minute:

    process started        Fri Sep 18 23:37:38
    control_app.py mtime   2026-09-19 16:48:34      (+17 hours -> the heuristic WARNS)
    /api/status            moduleFreshness {known: true, stale: false,
                                            say: "this server is the file on disk"}

A process can re-exec, a supervisor can reload it, and a module can be imported long after boot —
so process age is not module age. **v3288 built `module_freshness()` for exactly this reason**, and
its own docstring says the PID heuristic "can be fooled by a supervisor or a re-exec". The
first-hand answer has existed since then, on `/api/status`, and this hook went on using the
heuristic anyway: an answer built, published, and never asked for. [[the-unjoined-end]]

⚠ THREE STATES, NOT TWO. Unreachable console, or `known: false`, is UNKNOWN — and UNKNOWN must not
print a warning. A warning that fires when nothing was measured is exactly the noise this block has
been making on every push for weeks. [[unknown-stays-unknown]]

⚠ AND THE HEURISTIC WAS NOT MERELY NOISY, IT WAS BACKWARDS-CAPABLE: a console restarted a second
before the push would pass it while running a module imported hours earlier from a since-rewritten
file. Process age can be wrong in BOTH directions; import age cannot.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

HOOK = os.path.join(ROOT, "hooks", "pre-push")


def _hook():
    with io.open(HOOK, encoding="utf-8") as fh:
        raw = fh.read()
    # grade the SHELL, not the comments explaining it — the block below is documented at length
    # and every name this law bans appears in that prose. [[source-reading-guard]] §4
    return "\n".join(re.sub(r"(?m)^\s*#.*$", "", l) for l in raw.split("\n"))


class TheHookAsksTheConsole(unittest.TestCase):

    def test_it_reads_moduleFreshness(self):
        """⚠⚠ THE CASE. The first-hand signal, from the only thing that can answer first-hand."""
        code = _hook()
        self.assertIn("moduleFreshness", code,
                      "the hook does not read moduleFreshness, so it is guessing about staleness "
                      "again instead of asking the module that measured it at import")
        self.assertIn("/api/status", code,
                      "nothing asks the console for its own state")

    def test_it_no_longer_times_the_listener_process(self):
        """⚠ The heuristic itself, banned by its own signature rather than by a comment."""
        code = _hook()
        self.assertNotIn("ps -o lstart= -p", code,
                         "the hook still reads the listener's process start time. Process age is "
                         "not module age: measured on his console, a 17-hour-old process was "
                         "serving a module loaded AFTER the file was last written.")
        self.assertNotIn('strptime(sys.argv[1].strip(), "%a %b %d %H:%M:%S %Y")', code,
                         "the lstart parser survives, so the heuristic can be re-wired in one line")

    def test_unknown_never_prints_a_warning(self):
        """⚠⚠ THE ONE THAT KEEPS IT HONEST. A warning fired on an unmeasured state is the noise
        this whole change exists to remove. [[unknown-stays-unknown]]"""
        code = _hook()
        # ⚠ THE CASE LABEL, NOT THE BARE WORD. My first anchor was `code.find("unknown|")`, which
        # lands inside the EMBEDDED PYTHON that prints the token, ~40 lines above the shell branch
        # that reacts to it — so the window graded the stale branch and reported the unknown one
        # missing. The law caught it by failing rather than passing over a bad window, which is
        # the only reason it took one run. [[source-reading-guard]] §3
        i = code.find("unknown\\|*)")
        self.assertGreater(i, -1, "the hook has no UNKNOWN case branch at all — an unreachable "
                                  "console must be a third state, not silently one of the others")
        j = code.find(";;", i)
        self.assertGreater(j, i, "could not bound the unknown branch; refusing to grade a slice "
                                 "whose far end is a guess")
        seg = code[i:j]
        self.assertIn("UNKNOWN", seg,
                      "the unknown branch does not say UNKNOWN in the words he reads")
        self.assertNotIn("Restart it with", seg,
                         "the UNKNOWN branch tells him to restart the console — that is advice "
                         "derived from a measurement nobody took")

    def test_the_stale_branch_still_says_what_to_do(self):
        """⚠ THE BASELINE. Quieting the false warning must not quiet the true one.
        [[regression-guard]] §5"""
        code = _hook()
        i = code.find("stale\\|*)")
        self.assertGreater(i, -1, "there is no stale CASE branch left — the warning was removed "
                                  "rather than corrected, so a genuinely stale console says nothing")
        j = code.find(";;", i)
        self.assertGreater(j, i, "could not bound the stale branch")
        seg = code[i:j]
        self.assertIn("tvd-scan.sh", seg,
                      "the stale branch no longer names the command that fixes it")

    def test_the_console_side_answer_still_exists(self):
        """[[the-unjoined-end]] — the hook is now the CONSUMER; pin the producer too, or this
        law passes while the thing it reads has been deleted."""
        import control_app
        self.assertTrue(hasattr(control_app, "module_freshness"),
                        "control_app.module_freshness is gone, so the hook reads a key nothing "
                        "publishes and every push will read UNKNOWN forever")
        r = control_app.module_freshness()
        for k in ("known", "stale", "say"):
            self.assertIn(k, r, "module_freshness stopped reporting %r, which the hook branches on" % k)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "going back to the listener's process start makes the hook warn on every push again "
               "— measured false on his console, where a 17-hour-old process was serving a module "
               "loaded after the file was last written",
        "file": "hooks/pre-push",
        "find": "    _fresh=\"$(curl -s -m 5 http://127.0.0.1:17772/api/status 2>/dev/null | python3 -c '",
        "replace": "    _con_started=\"$(ps -o lstart= -p 1 2>/dev/null)\"\n    _fresh=\"$(curl -s -m 5 http://127.0.0.1:17772/api/status 2>/dev/null | python3 -c '",
        "matches": 1,
    },
    {
        "why": "letting UNKNOWN fall through to the stale branch prints a warning about a state "
               "nobody measured, which is the noise this version removes",
        "file": "hooks/pre-push",
        "find": "      unknown\\|*)\n        echo \"pre-push: [$(_pp_el)] ⚠ whether the console on :17772 runs the current server is UNKNOWN\"",
        "replace": "      unknown\\|*)\n        echo \"pre-push: [$(_pp_el)] ⚠ the console on :17772 is running code OLDER than tv/control_app.py.\"\n        echo \"          Restart it with 'bash tv/tvd-scan.sh'.\"\n        echo \"pre-push: [$(_pp_el)] (was UNKNOWN)\"",
        "matches": 1,
    },
    {
        "why": "dropping the stale branch quiets the TRUE warning along with the false one, so a "
               "console genuinely serving old server code says nothing at all",
        "file": "hooks/pre-push",
        "find": "        echo \"          Restart it with 'bash tv/tvd-scan.sh' to make this gate mean what it says.\"",
        "replace": "        echo \"          (restart advice removed)\"",
        "matches": 1,
    },
]
