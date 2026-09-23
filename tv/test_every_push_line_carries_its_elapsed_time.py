# -*- coding: utf-8 -*-
"""#193 — every line the pre-push hook prints carries the time it was printed at.

⚠ WHAT IT COST BEFORE THIS EXISTED. The hook's `pre-push:` lines were untimed, so the duration of
any single gate could only ever be BOUNDED from outside by polling `ps`, never read off the log.
The v3447-v3451 push — the first after heart2's red-proofs were parallelised, the one run that most
needed a per-gate number — could only report the prover as "<=20 min, against 24 and 26 serially".
On 2026-09-24 two pushes in a row were refused on starvation (render at 300s, then test_control at
589s of a 600s bound) and neither log could say how long the stages before them had taken.
[[unknown-stays-unknown]] — a duration nobody can ask of the artifact is an estimate wearing a
measurement's confidence.

⚠ AND THE STOPWATCH GLYPH HAD NEVER RENDERED. The two starvation lines wrote `\\u23f1` inside a bash
double-quoted string; bash has no \\u escape there, so the refusal printed the six literal
characters — measured in the v3462 push log. Text that is not text, in the one message he reads
when a push fails.

These cases DRIVE the hook's own function in bash and read the hook's echo lines with comments
stripped. RED_PROOF below.
"""
import io
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")


def _hook():
    return io.open(HOOK, encoding="utf-8").read()


def _code(src):
    # a whole-line comment is prose; the hook's echo lines are never comments
    return "\n".join(l for l in src.split("\n") if not l.lstrip().startswith("#"))


class EveryPushLineIsTimed(unittest.TestCase):

    def test_no_status_line_is_printed_without_its_elapsed_time(self):
        lines = _code(_hook()).split("\n")
        stamped = [l for l in lines if 'echo "pre-push: [$(_pp_el)] ' in l]
        bare = [l.strip() for l in lines
                if 'echo "pre-push: ' in l and 'echo "pre-push: [$(_pp_el)] ' not in l]
        self.assertEqual(bare, [],
                         "%d hook line(s) still print untimed, so the gate they report can only be "
                         "bounded from outside, never measured: %r" % (len(bare), bare[:5]))
        self.assertGreaterEqual(len(stamped), 30,
                                "only %d stamped status lines — the hook's status lines were not "
                                "found at all, so 'none bare' above would pass vacuously"
                                % len(stamped))

    def test_the_stamp_is_the_real_elapsed_time(self):
        src = _hook()
        m = re.search(r"^_PP_T0=\$SECONDS\n(_pp_el\(\) \{[^\n]*\}\n)", src, re.M)
        self.assertIsNotNone(m, "the hook no longer defines _PP_T0 and _pp_el where they are read")
        out = subprocess.run(["bash", "-c", m.group(1) + "_PP_T0=$((SECONDS - 125)); _pp_el"],
                             capture_output=True, universal_newlines=True, timeout=20).stdout
        self.assertIn(out.strip(), ("2m05s", "2m06s"),
                      "125 seconds after the hook started, its own stamp printed %r" % out)

    def test_no_escape_sequence_is_printed_as_literal_text(self):
        hits = [l.strip() for l in _code(_hook()).split("\n")
                if "echo" in l and re.search(r"\\u[0-9a-fA-F]{4}", l)]
        self.assertEqual(hits, [],
                         "bash has no \\u escape inside double quotes, so these print the literal "
                         "characters on his terminal: %r" % hits)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a stamp that prints nothing is the untimed log this law exists to end",
        "file": "hooks/pre-push",
        "find": "printf '%dm%02ds' $((s / 60)) $((s % 60)); }",
        "replace": "printf ''; }",
        "matches": 1,
    },
    {
        "why": "one status line back to untimed — the gate it reports can only be bounded again",
        "file": "hooks/pre-push",
        "find": "echo \"pre-push: [$(_pp_el)] ✅ tv suites green.\"",
        "replace": "echo \"pre-push: ✅ tv suites green.\"",
        "matches": 1,
    },
    {
        "why": "the stopwatch back to a bash-inert \\u escape: six literal characters on his screen",
        "file": "hooks/pre-push",
        "find": "echo \"pre-push: [$(_pp_el)] ⏱ ${label} HUNG",
        "replace": "echo \"pre-push: [$(_pp_el)] \\u23f1 ${label} HUNG",
        "matches": 1,
    },
]
