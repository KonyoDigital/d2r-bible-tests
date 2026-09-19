# -*- coding: utf-8 -*-
"""v3360 (#109) — A SHIP NOTE IS PROSE, AND THE EYE'S BUDGET IS NOT FOR PROSE.

`run_gates.py` carries one `why=` per gate: a paragraph explaining what a law is for. It is
documentation, and `_strip_comments` cannot touch it because it is a string LITERAL — so the
second eye pays full price for it out of a budget that truncates at 9,000 characters.

MEASURED on v3354's payload, by share of the 6,844 chars that reached the eye:

    tv/corroborate.py        4,009   59.3%
    tv/run_gates.py          2,133   31.5%   <- almost entirely ONE `why=` ship note
    tv/control_app.py          619    9.2%
    tv/second_eye_ledger.py      0      0%   <- THE FILE THAT VERSION EXISTS TO CHANGE

#97 found the same shape on v3333 at 44.9% and named the cause; nothing acted on it.

=== ⚠⚠ MY FIRST MEASUREMENT SAID THE STRIP MADE THREE VERSIONS BLINDER. IT WAS MY OWN TOOL ===
Collapsing a multi-line `why=` onto one line pulls the NEXT `diff --git` off the start of its own
line, and every line-anchored reader stops counting that file — including the tool measuring
whether the strip helps. It reported v3346, v3345 and v3344 losing a file each. The headers were
all still there: for v3346, `tv/second_eye_run.py` sat at offset 1,362 of a 9,000-char cap, EARLIER
than before. Preserving the newline count, the same measurement over 24 versions reads:

    missed changed files   65 -> 58        6 versions better        0 worse

⚠ IT REMOVES LESS THAN IT LOOKS LIKE, and that is stated rather than rounded up: in a diff every
continuation line starts with `+`, `-` or a space, which the pattern cannot cross, so a five-line
note loses its first quoted chunk and keeps the rest. The 65 -> 58 is of THAT narrow form.

⚠ IT DOES NOT WIDEN THE CAP. v3299 ruled that cost is HIS. This only stops spending it on prose.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_run as R  # noqa: E402

#: ⚠ THE `diff --git` HEADER IS PART OF THE FIXTURE, not decoration. The strip is SCOPED to
#: run_gates.py hunks, so a fixture without a header is a no-op and every case below would pass
#: over a helper that does nothing. Three of these cases silently weakened the moment the scoping
#: landed, and the baseline case is what caught it. [[regression-guard]] §5
NOTE = (
    'diff --git a/tv/run_gates.py b/tv/run_gates.py\n'
    '@@ -1,4 +1,4 @@\n'
    '     Gate("t_x", [sys.executable, "x.py"], 120,\n'
    '          why="the first chunk of a ship note"\n'
    '              "and the second chunk"),\n'
    '     Gate("t_y", [sys.executable, "y.py"], 120, why="a one line note"),\n'
)


class AShipNoteIsNotCode(unittest.TestCase):

    def test_the_line_count_never_changes(self):
        """⚠⚠ THE CASE. Losing a newline pulls the next `diff --git` off its own line and every
        line-anchored reader stops seeing that file — which is exactly how my first measurement
        invented three regressions. [[feedback-suspect-the-instrument]]"""
        out = R._strip_ship_notes(NOTE)
        self.assertEqual(
            out.count("\n"), NOTE.count("\n"),
            "the strip changed the line count %d -> %d. In a diff that re-anchors every following "
            "`diff --git`, and a payload reader counting file headers at line start silently "
            "stops seeing files that are present."
            % (NOTE.count("\n"), out.count("\n")))

    def test_it_actually_removes_a_note(self):
        """⚠ THE BASELINE, or a helper that changes nothing would pass the line-count case.
        [[regression-guard]] §5"""
        out = R._strip_ship_notes(NOTE)
        self.assertNotIn("a one line note", out,
                         "a single-line ship note survived the strip, so the budget is still "
                         "being spent on prose")
        self.assertIn("<ship note stripped for the eye>", out,
                      "nothing was replaced — the eye cannot tell a stripped note from a missing "
                      "one unless the stub says so")

    def test_the_gate_registration_itself_is_untouched(self):
        """⚠ THE SAFETY. A `Gate(...)` entry is real code and a missing separating comma there is
        a live defect class in this repo. The strip must reach the note and nothing else."""
        out = R._strip_ship_notes(NOTE)
        for keep in ('Gate("t_x"', 'Gate("t_y"', '"x.py"', '"y.py"', "120,", "),"):
            self.assertIn(keep, out,
                          "the strip ate %r, which is registration code, not a ship note" % keep)

    def test_a_diff_marker_is_never_crossed(self):
        """⚠ THE STATED LIMIT, pinned so nobody reads the saving as larger than it is. A
        continuation line in a DIFF begins with + - or a space, and the pattern must not cross it;
        widening to do so would start eating ordinary string literals in ordinary code."""
        diff = ('diff --git a/tv/run_gates.py b/tv/run_gates.py\n'
                '+     Gate("x", [], 1,\n'
                '+          why="line one"\n'
                '+               "line two"),\n')
        out = R._strip_ship_notes(diff)
        self.assertIn('"line two"', out,
                      "the pattern crossed a diff marker. That is not a bigger saving, it is the "
                      "beginning of eating real code — and the 65 -> 58 measurement was taken of "
                      "the NARROW form, so a wider one has no measurement behind it at all.")
        self.assertEqual(out.count("\n"), diff.count("\n"))

    def test_a_why_outside_run_gates_is_left_alone(self):
        """⚠⚠ THE CROSS-FAMILY EYE FOUND THIS ON v3360, AND IT WAS A REAL DEFECT I SHIPPED.
        `why=` is a ship note ONLY in run_gates.py. MEASURED across tv/*.py: 188 occurrences sit
        outside any `Gate(` call, and many are live message strings — `why="boot"`,
        `why="a session ended"`, `why="disk too full"`. Stripping those replaces the very bytes a
        version about wording exists to change, handing the eye a stub in place of its subject —
        the defect this whole area exists to prevent, re-created by the fix for it."""
        keep = ('diff --git a/tv/control_app.py\n'
                '+        out.update(state="absent", why="the lane is not installed here")\n')
        out = R._strip_ship_notes(keep)
        self.assertIn('why="the lane is not installed here"', out,
                      "a live message string in control_app.py was replaced with a ship-note stub. "
                      "A version whose whole subject is that wording would hand the eye the stub "
                      "and nothing else.")
        drop = ('diff --git a/tv/run_gates.py\n'
                '+         why="a real ship note about a gate"\n')
        self.assertNotIn("a real ship note about a gate", R._strip_ship_notes(drop),
                         "the run_gates.py hunk is no longer stripped, so the whole saving is gone")

    def test_payload_for_actually_calls_it(self):
        """[[the-unjoined-end]] — a correct helper nothing calls changes nothing."""
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn("_strip_ship_notes(_strip_comments(out))", code,
                      "payload_for no longer strips ship notes from the python diff, so the eye "
                      "is back to paying for prose out of a budget that truncates")
        self.assertGreaterEqual(
            code.count("_strip_ship_notes("), 3,
            "the helper is called fewer than three times (its definition, the python diff and the "
            "html diff) — one of the two diffs is unstripped and the saving is half of what the "
            "measurement claims")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the newline padding collapses a multi-line note onto one line, which "
               "re-anchors the next `diff --git` and makes line-anchored readers lose a file that "
               "is present — the exact artifact that invented three regressions in my measurement",
        "file": "tv/second_eye_run.py",
        "find": "        return 'why=\"<ship note stripped for the eye>\"' + \"\\n\" * m.group(0).count(\"\\n\")",
        "replace": "        return 'why=\"<ship note stripped for the eye>\"'",
        "matches": 1,
    },
    {
        "why": "not calling the helper from payload_for leaves the eye paying full price for every "
               "ship note out of a budget that truncates at 9,000 chars",
        "file": "tv/second_eye_run.py",
        "find": "    body = _strip_ship_notes(_strip_comments(out))",
        "replace": "    body = _strip_comments(out)",
        "matches": 1,
    },
    {
        "why": "letting the pattern cross a diff marker turns a prose strip into one that eats "
               "ordinary string literals in ordinary code, with no measurement behind it",
        "file": "tv/second_eye_run.py",
"find": "r'why=\\s*(?:\"(?:[^\"\\\\]|\\\\.)*\"\\s*|\\'(?:[^\\'\\\\]|\\\\.)*\\'\\s*)+', re.S)",
        "replace": "r'why=[\\s\\S]*?\\)', re.S)",
        "matches": 1,
    },
]
