# -*- coding: utf-8 -*-
"""#151 - THE PUSH SAYS HOW MANY LANES IT PROVES IN, AND WHY, WHERE THE PROVING STAGE STARTS.

His words, 2026-10-21: "heart2 says '1 lane' at the TOP of the push". That day his Mac sat at 4.0 GB free and every push
proved one law at a time; heart2 said so in one line of its prove log - which hooks/pre-push deletes on success and cuts
to its last 24 lines on failure. Now the hook asks heart2.prove_workers (the function the push itself takes its lanes
from) and prints "proving N changed law(s) in K lane(s) - <its reason>" before the prove runs, or UNKNOWN when heart2
cannot say. This law runs the hook's OWN snippet against a fixture disk. RED_PROOF below. [[unknown-stays-unknown]]
"""
import contextlib
import io
import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import heart2 as H  # noqa: E402

HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")
PROVE = '    if python3 "$REPO/tv/heart2.py" --prove $_gates --push > "$_prove_log" 2>&1; then\n'


def _hook():
    with io.open(HOOK, encoding="utf-8") as fh:
        return fh.read()


def _snippet(s):
    m = re.search(r"_lanes_say=\$\(cd \"\$REPO/tv\" && python3 -c '(.*?)' \"\$\(echo", s, re.S)
    if not m:
        raise AssertionError("the hook's lane snippet is not where this law reads it")
    return m.group(1)


class _Free(object):
    def __init__(self, mb):
        self.free = int(mb * 1024 * 1024)


class ThePushSaysItsLanes(unittest.TestCase):

    def run_snippet(self, n_gates, free_mb):
        out = io.StringIO()
        with mock.patch.object(H.shutil, "disk_usage", lambda p: _Free(free_mb)), mock.patch.dict(os.environ), \
                mock.patch.object(sys, "argv", ["-c", str(n_gates)]), contextlib.redirect_stdout(out):
            os.environ.pop("HEART2_PROVE_WORKERS", None)       # the default lane count, as a plain push has it
            exec(compile(_snippet(_hook()), "pre-push-lanes", "exec"), {"__name__": "__main__"})
        return out.getvalue().strip()

    def test_a_short_disk_is_said_with_its_reason(self):
        said = self.run_snippet(6, 4096)
        self.assertTrue(said.startswith("1 lane(s) - "), "the lane line lost its count: %r" % said)
        self.assertIn("MB free", said, "the reason one lane runs is not said: %r" % said)

    def test_a_roomy_disk_says_its_lanes_plainly(self):
        said = self.run_snippet(3, 50000)
        self.assertEqual(said, "%d lane(s)" % min(3, H.PROVE_WORKERS))

    def test_it_is_said_before_the_prove_runs_and_unknown_is_a_word(self):
        s = _hook()
        line = 'echo "pre-push: [$(_pp_el)] proving $(echo $_gates | wc -w | tr -d \' \') changed law(s) in ${_lanes_say:-UNKNOWN lane(s) - heart2 could not say}"'
        self.assertEqual(s.count(line), 1, "the push does not say its lanes")
        self.assertEqual(s.count(PROVE), 1)
        self.assertLess(s.index(line), s.index(PROVE), "the lanes are said after the proving, not where it starts")


RED_PROOF = [
    {"why": "#151 - the push never says its lanes where proving starts",
     "file": "hooks/pre-push",
     "find": "    echo \"pre-push: [$(_pp_el)] proving $(echo $_gates | wc -w | tr -d ' ') changed law(s) in ${_lanes_say:-UNKNOWN lane(s) - heart2 could not say}\"\n",
     "replace": "",
     "matches": 1},
    {"why": "#151 - the lane line drops heart2's reason (the 4.0 GB day reads as a plain '1 lane')",
     "file": "hooks/pre-push",
     "find": "print(\"%d lane(s)%s\" % (n, (\" - \" + said[-1].strip()) if said else \"\"))",
     "replace": "print(\"%d lane(s)%s\" % (n, \"\"))",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
