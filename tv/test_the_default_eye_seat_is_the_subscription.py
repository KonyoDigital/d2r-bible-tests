# -*- coding: utf-8 -*-
"""v3425 — THE DEFAULT SECOND-EYE TRANSPORT IS THE CLI SUBSCRIPTION, AND IT MUST BE REACHABLE.

HIS RULING, 2026-09-23: *"make it the xAI subscription as a default"* — said the hour the paid API
lane went dark. It restates 2026-08-05: *"i rather have them by default do the CLI obviously, but
its there the MCP if its needed only."* The reason is not preference: the CLI needs no MCP
connection, so a seat still fills in a headless or cron run, and a subscription look costs nothing
per call where a metered one can simply stop being affordable.

**MEASURED the same hour:** `mcp__grok-mcp__upload_file` → PERMISSION_DENIED, *"has either used all
available credits or reached its monthly spending limit"*, while this CLI answered v3421 at 95%
reach with a schema-constrained verdict.

⚠ AND A CARVED SKILL ASSERTED THE EXACT OPPOSITE. `human-eyes-harness` carried *"the CLI is
currently out of build balance, HTTP 402; the MCP transport works"* — true when written, INVERTED
by the time it mattered, and it would have sent the next session to the dead lane and filed the
resulting silence as an empty seat. [[stale-reading]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_run as R  # noqa: E402
import console_doctor as CD  # noqa: E402

SRC = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8", errors="replace").read()
REPO = os.path.dirname(HERE)


class TestTheDefaultSeatIsTheSubscription(unittest.TestCase):

    def test_the_default_transport_is_resolved_to_an_ABSOLUTE_path(self):
        """⚠ THE G5 SCAR, EXACTLY. G5 sat PRIMARY and silently dark for WEEKS reporting
        `mode=off, cli=False, calls=0, errors=0, last_error=None` — every honesty surface clean
        BECAUSE the eye was dark. The cause was `shutil.which` searching the calling process's
        PATH, while the console runs under launchd with a bare `/usr/bin:/bin`. A bare name here
        would reintroduce that: reachable from a terminal, absent under launchd, and silent."""
        self.assertTrue(os.path.isabs(R.EYE_CLI),
                        "EYE_CLI is not an absolute path (%r) — under launchd the console gets a "
                        "bare PATH and this seat would go dark without ever saying so" % R.EYE_CLI)

    def test_the_default_ask_path_invokes_that_binary_and_no_metered_API(self):
        """The ruling has to be true of the CODE, not only of a comment beside it. `ask()` must
        exec EYE_CLI, and the default path must not reach for an HTTP/API transport that can stop
        being affordable mid-arc."""
        fn = [n for n in ast.walk(ast.parse(SRC))
              if isinstance(n, ast.FunctionDef) and n.name == "ask"]
        self.assertTrue(fn, "ask() is gone — this gate is pointed at nothing")
        names = {n.id for n in ast.walk(fn[0]) if isinstance(n, ast.Name)}
        self.assertIn("EYE_CLI", names,
                      "ask() does not reference EYE_CLI, so the default seat is no longer the "
                      "subscription CLI his ruling names")
        for banned in ("requests", "urlopen", "httpx", "openai"):
            self.assertNotIn(banned, names,
                             "the default look path reaches for %r — a metered transport, which "
                             "is the lane that went dark" % banned)

    # ---- the live row, driven ------------------------------------------------------------

    def _row(self):
        return dict(CD.CHECKS)["the eye seat can be filled"]

    def _with_cli(self, path):
        orig = R.EYE_CLI
        try:
            R.EYE_CLI = path
            return self._row()()
        finally:
            R.EYE_CLI = orig

    def test_a_present_executable_binary_is_OK(self):
        st, say = self._with_cli(sys.executable)      # a real, executable file
        self.assertEqual(st, CD.OK, "a present executable transport did not read OK: %s" % say)

    def test_an_ABSENT_binary_is_a_finding_not_a_shrug(self):
        st, say = self._with_cli(os.path.join(HERE, "no_such_eye_binary_at_all"))
        self.assertEqual(st, CD.MISSING,
                         "the default transport was missing and the row did not say so (%s) — "
                         "that is the G5 shape: every lamp green because nobody is asking" % say)

    def test_a_NON_EXECUTABLE_binary_is_named_as_such(self):
        """⚠ A DIFFERENT DEFECT FROM ABSENCE, and the say must not confuse them: an install that
        exists but cannot exec reads to a reader as an unreachable eye rather than a broken file."""
        st, say = self._with_cli(os.path.join(HERE, "second_eye_run.py"))   # exists, not +x
        if os.access(os.path.join(HERE, "second_eye_run.py"), os.X_OK):
            self.skipTest("second_eye_run.py is executable on this checkout; nothing to measure")
        self.assertEqual(st, CD.MISSING, "a non-executable transport read as fine: %s" % say)
        self.assertIn("not executable", say, "the row does not distinguish absent from unrunnable")

    def test_NO_transport_named_is_a_finding(self):
        st, say = self._with_cli("")
        self.assertEqual(st, CD.MISSING, "no transport at all read as fine: %s" % say)

    # ---- the stale claim that would send the next session to the dead lane ---------------

    def test_the_skill_no_longer_says_the_CLI_IS_OUT_OF_BALANCE(self):
        """⚠⚠ THIS CASE WENT **BLIND AT MATCH COUNT 1** IN ITS FIRST FORM, AND THE COUNT IS THE TELL.

        The tamper applied cleanly and the gate stayed green, which by the standing rule means the
        LAW was weak, not the sabotage wrong. The first form walked the whole repo for any `.md`
        carrying both halves of the claim — and a law whose truth depends on which directories a
        sandbox happened to copy is not a law, it is a coincidence. It also swept
        `.claude/worktrees/`, where stale forks of this very skill live.

        ONE NAMED FILE, by explicit path. If the file moves, this fails loudly rather than passing
        vacuously — which is the whole difference between the two forms."""
        p = os.path.join(REPO, ".claude", "skills", "human-eyes-harness", "SKILL.md")
        self.assertTrue(os.path.isfile(p),
                        "the human-eyes-harness skill is not where this law says it is (%s) — "
                        "a guard that cannot find its subject passes for the wrong reason" % p)
        body = io.open(p, encoding="utf-8", errors="replace").read()
        self.assertNotIn("out of build balance", body,
                         "the skill still says the CLI is out of build balance. Measured false on "
                         "2026-09-23: the CLI answered v3421 at 95%% reach while the METERED lane "
                         "returned PERMISSION_DENIED for spent credits. Following this routes the "
                         "next session to the transport that cannot answer, and files the "
                         "resulting silence as an empty seat.")
        self.assertNotIn("the MCP transport works", body,
                         "the skill still asserts the MCP transport works; it is the lane that "
                         "went dark, and his 2026-09-23 ruling makes the CLI the default")

    def test_the_runner_RECORDS_the_ruling_where_the_transport_is_chosen(self):
        """A ruling that lives only in a task description is a ruling the next reader will not
        find. It has to sit at the line that picks the transport."""
        self.assertIn("THE CLI SUBSCRIPTION IS THE DEFAULT TRANSPORT", SRC,
                      "the runner does not record his 2026-09-23 ruling at the site that chooses "
                      "the transport, so the next change there will not know it exists")


RED_PROOF = [
    {
        "why": "v3425 - THE G5 SCAR PUT BACK. A bare name resolves from the CALLING process's PATH, "
               "so the seat works from a terminal and is silently dark under launchd, where the "
               "console actually runs - which is how G5 sat PRIMARY and unasked for weeks.",
        "file": "second_eye_run.py",
        # re-anchored in #225/#227: the default now ASKS g5_grok_eyes._grok_bin (which finds grok.exe
        # on the Windows ALT), so the scar is put back on the one line that decides the seat
        "find": "EYE_CLI = os.environ.get(\"THIRD_EYE_CLI\") or _default_eye_cli()",
        "replace": "EYE_CLI = os.environ.get(\"THIRD_EYE_CLI\") or \"grok\"",
        "matches": 1,
    },
    {
        "why": "v3425 - THE ABSENT DEFAULT MADE FINE. If a missing transport reads OK then the one "
               "question this row exists to answer is answered wrongly, and every look after it "
               "records an EMPTY SEAT with nothing anywhere saying why.",
        "file": "console_doctor.py",
        "find": "    if not there:\n        return MISSING, (\"the default transport is not on this machine",
        "replace": "    if not there:\n        return OK, (\"the default transport is not on this machine",
        "matches": 1,
    },
    {
        "why": "v3425 - THE INVERTED CLAIM RESTORED. The carved skill said the CLI was out of "
               "balance and the MCP worked; by the time it mattered both were false, and it would "
               "have routed the next session to the lane that cannot answer.",
        "file": "../.claude/skills/human-eyes-harness/SKILL.md",
        "find": "Related: `grok-second-eye` (the same principle, on pixels, by hand) · `borrowed-surface` ·",
        "replace": "Related: `grok-second-eye` (the same principle, on pixels, by hand - and the CLI is currently out\nof build balance, HTTP 402; the MCP transport works) · `borrowed-surface` ·",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
