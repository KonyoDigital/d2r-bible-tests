#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3408 — EVERY EYE IS A CLI SEAT ON HIS OWN SUBSCRIPTION, AND IT STANDS OUTSIDE THE REPO.

His ruling, 2026-09-22: *"GROK CLI should be intertwined in the console as the seocndary option
while as CLAUDE CLI you subscription is the primary make sur eit is and no API there is bouncing
regardless"*.

THE TRIGGER, measured the same hour: an API-key seat answered
`PERMISSION_DENIED — has either used all available credits or reached its monthly spending limit`
mid-ship, while the pre-push gate was demanding a second-eye look. An API seat that bounces is an
EMPTY SEAT, and an empty seat blocks a push while proving nothing. A subscription CLI does not
meter that way.

⚠ THE TREE WAS ALREADY RIGHT AND THAT IS EXACTLY WHY THIS EXISTS. The sweep found ZERO shipped
modules calling a model API — `control_app._claude_env()` strips ANTHROPIC_API_KEY, `g5_grok_eyes`
strips six API vars and says `lane: subscription-cli`, `second_eye_run` spawns `~/.grok/bin/grok`.
Nothing needed repairing. What was missing is the LAW, so nobody re-introduces one; a correct
state nothing pins is a state that drifts. [[the-unjoined-end]] [[copy-drift]]

⚠ AND THE SECOND HALF IS SAFETY, NOT BILLING. A CLI eye is an AGENT with tools. Pointed at this
checkout it can EDIT IT — witnessed 2026-09-22, a Grok CLI session writing to tv/ while a ship was
mid-flight, caught by Konyo rather than by any guard. The payload is a DIFF and the prompt says to
judge only what is shown, so a working directory inside the repo is not something the review needs;
it is only something a reviewer can damage.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ HIS WINDOWS CONSOLE IS cp1255: a bare print of ⚠ or an em dash crashes the script
# WHILE REPORTING, so a clean tree exits non-zero for a reason unrelated to the check.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

REPO = os.path.dirname(HERE)

# The hosts that mean "a metered API key", as opposed to a signed-in CLI.
API_HOSTS = ("api.x.ai", "api.openai.com", "api.anthropic.com")


def _is_a_url_to(code, host):
    """True when the host appears as a URL, not merely as a NAME.

    ⚠⚠ TWO CUTS OF THIS LAW ACCUSED ITS OWN ENFORCEMENT BEFORE IT WORKED.
      1. `host in code` flagged console_doctor, whose v3408 heart row lists all three hosts in a
         loop that REFUSES them — the guard reading a ban as the crime. [[source-reading-guard]] §4
      2. "names a host AND the file contains urlopen" flagged it again, because that module
         legitimately calls urlopen against its OWN 127.0.0.1 loopback. File-level co-occurrence
         is not a relationship between two things, it is two things in one file.

    A ban list holds a BARE hostname. A call holds a URL — a scheme in front of it or a path
    behind it. That is the distinction the law actually means.

    ⚠ STATED REACH, not implied: a URL assembled at runtime from a bare host plus a separate path
    would pass this. That shape does not exist in this tree today and the law says so rather than
    claiming a completeness it does not have.
    """
    return ("//" + host) in code or (host + "/") in code


def _code(path):
    """Source with # comments stripped, so a guard never grades its own explanation.

    ⚠ Four guards in this repo have gone red on the sentence describing their own fix. This file
    BANS strings that its own docstring necessarily contains. [[source-reading-guard]] §4
    """
    with io.open(path, encoding="utf-8") as fh:
        raw = fh.read()
    out = "\n".join(l.split("#", 1)[0] for l in raw.split("\n"))
    out = re.sub(r'""".{0,12000}?"""', "", out, flags=re.S)
    return re.sub(r"'''.{0,12000}?'''", "", out, flags=re.S)


def _shipped_modules():
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("test_"):
            continue
        yield os.path.join(HERE, name)


class TestNoShippedModuleReachesAModelApiByKey(unittest.TestCase):

    def test_no_module_REACHES_a_model_API_host(self):
        """⚠⚠ NAMING A HOST IS NOT REACHING IT, AND THE FIRST CUT COULD NOT TELL THE DIFFERENCE.

        It flagged `console_doctor.py -> api.x.ai / api.openai.com / api.anthropic.com` — the
        v3408 heart row, whose entire body is a loop that REFUSES those hosts. The guard accused
        the code that enforces it, which is [[source-reading-guard]] §4 in its purest form: a
        negative assertion has to be true of the whole searched text, including the enforcement
        you just wrote.

        So the law asks the question it actually means: does this module both NAME a metered host
        AND carry the means to call one? A ban list is a name with no call under it.
        """
        offenders, scanned = [], 0
        for p in _shipped_modules():
            scanned += 1
            code = _code(p)
            hit = [h for h in API_HOSTS if _is_a_url_to(code, h)]
            if hit:
                offenders.append("%s -> %s" % (os.path.basename(p), ", ".join(hit)))
        self.assertEqual(offenders, [],
                         "a shipped module REACHES a metered API instead of his subscription CLI, "
                         "so the seat can answer 'out of credits' and block a ship: %s" % offenders)
        print("modules scanned: %d, modules that reach a metered API: 0" % scanned)

    def test_the_REACH_law_can_still_see_a_real_offender(self):
        """⚠ A guard loosened to stop accusing its own ban must still catch the thing it bans.

        Without this, narrowing the rule to "names a host AND can call one" could be narrowed
        again to nothing and stay green forever. [[regression-guard]] §5 — assert the BASELINE.
        """
        planted = 'x = urlopen("https://api.x.ai/v1/chat")'
        self.assertTrue([h for h in API_HOSTS if _is_a_url_to(planted, h)],
                        "the law can no longer recognise a plain metered API call, so its green "
                        "means nothing")
        ban_only = 'for host in ("api.x.ai", "api.openai.com"):\n    if host in cli: return MISSING'
        self.assertFalse([h for h in API_HOSTS if _is_a_url_to(ban_only, h)],
                         "a ban list is still being read as a call — the guard accuses the code "
                         "that enforces it")
        loopback = 'r = urlopen("http://127.0.0.1:17772/api/status")'
        self.assertFalse([h for h in API_HOSTS if _is_a_url_to(loopback, h)],
                         "a module that calls its OWN loopback is not reaching a metered API")

    def test_the_vision_lane_STRIPS_every_api_secret_it_names(self):
        """g5_grok_eyes' own contract line is `NOT: XAI_API_KEY / api.x.ai Bearer calls`."""
        import g5_grok_eyes as G
        strip = tuple(getattr(G, "_API_STRIP", ()) or ())
        self.assertTrue(strip, "_API_STRIP is empty, so vision can ride a console token again")
        for want in ("XAI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            self.assertIn(want, strip,
                          "%s is no longer stripped, so a key in the environment silently becomes "
                          "the seat and the subscription lane stops being the lane" % want)


class TestTheEyeIsACliSeat(unittest.TestCase):

    def test_the_eye_is_an_executable_path_not_a_url(self):
        import second_eye_run as R
        self.assertTrue(R.EYE_CLI, "there is no eye configured at all")
        for host in API_HOSTS:
            self.assertNotIn(host, R.EYE_CLI,
                             "the eye is an API endpoint, not a CLI on his subscription")
        self.assertTrue(R.EYE_CLI.startswith("/") or os.sep in R.EYE_CLI,
                        "EYE_CLI does not look like a path to a binary: %r" % R.EYE_CLI)

    def test_the_eye_gets_longer_than_the_slowest_REAL_answer_measured(self):
        """⚠ MEASURED, not chosen: a 22,519-char v3404 payload ran PAST 300 s and was killed, and
        the ledger recorded an empty seat — correct, and it blocked the ship anyway."""
        import second_eye_run as R
        self.assertGreaterEqual(
            R.EYE_TIMEOUT_S, 600,
            "the eye's bound is %.0fs, at or under the 300s that was MEASURED to be too short for "
            "a real answer. A bound below what the instrument takes measures the bound, not the "
            "instrument — and every timeout it causes is filed as an empty seat, which blocks a "
            "push for a look nobody waited for" % R.EYE_TIMEOUT_S)

    def test_the_eye_does_NOT_stand_inside_the_repo(self):
        """⚠ A CLI eye is an AGENT with tools. Inside the checkout it can edit the thing it grades."""
        import second_eye_run as R
        cwd = os.path.abspath(getattr(R, "EYE_CWD", "") or "")
        self.assertTrue(cwd, "the eye has no working directory of its own, so it inherits the repo")
        self.assertFalse(
            cwd.startswith(os.path.abspath(REPO) + os.sep) or cwd == os.path.abspath(REPO),
            "the eye runs INSIDE the repo (%s), so a reviewing agent can write to the tree it is "
            "reviewing — which happened on 2026-09-22 and was caught by Konyo, not by a guard" % cwd)

    def test_ask_actually_HANDS_the_cwd_to_the_subprocess(self):
        """⚠ [[the-unjoined-end]] — a directory computed and never passed is the same as none."""
        code = _code(os.path.join(HERE, "second_eye_run.py"))
        i = code.find("def ask(")
        self.assertGreater(i, -1, "ask() is gone")
        blk = code[i:code.find("\ndef ", i + 1)]
        self.assertIn("cwd=EYE_CWD", blk,
                      "EYE_CWD is computed and never handed to Popen, so the eye still inherits "
                      "whatever directory the caller happened to be standing in")


RED_PROOF = [
    {
        "why": "v3408 — WITHOUT cwd=EYE_CWD THE EYE INHERITS THE REPO. A CLI eye is an agent with "
               "tools; standing in this checkout it can write to the very tree it is grading. "
               "Measured 2026-09-22: a Grok CLI session was editing tv/ mid-ship and Konyo was the "
               "one who noticed. The value being computed is not the fix — handing it over is.",
        "file": "second_eye_run.py",
        "find": "stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=EYE_CWD)",
        "replace": "stdout=subprocess.PIPE, stderr=subprocess.PIPE)",
        "matches": 1,
    },
    {
        "why": "v3408 — A BOUND BELOW THE INSTRUMENT MEASURES THE BOUND. Back at 300 s the eye is "
               "killed on a real payload (MEASURED: 22,519 chars of v3404 ran past it), the ledger "
               "files an EMPTY SEAT, and the pre-push gate then refuses the ship for want of a "
               "look nobody waited for. Correct bookkeeping, useless outcome.",
        "file": "second_eye_run.py",
        "find": 'EYE_TIMEOUT_S = float(os.environ.get("THIRD_EYE_TIMEOUT_S") or 1200)',
        "replace": 'EYE_TIMEOUT_S = float(os.environ.get("THIRD_EYE_TIMEOUT_S") or 300)',
        "matches": 1,
    },
    {
        "why": "v3408 — DROP ONE NAME FROM _API_STRIP AND A KEY IN THE ENVIRONMENT SILENTLY "
               "BECOMES THE SEAT. The vision lane's whole contract line is `NOT: XAI_API_KEY / "
               "console API tokens / api.x.ai Bearer calls`, and that is enforced by stripping, "
               "not by the comment saying so.",
        "file": "g5_grok_eyes.py",
        "find": '    "XAI_API_KEY", "G5_XAI_KEY", "G4_XAI_KEY",',
        "replace": '    "G5_XAI_KEY", "G4_XAI_KEY",',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
