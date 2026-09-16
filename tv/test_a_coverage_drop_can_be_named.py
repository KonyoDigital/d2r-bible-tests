# -*- coding: utf-8 -*-
"""A COVERAGE DROP MUST BE ABLE TO SAY *WHAT* LEFT.

MEASURED 2026-09-16. The pre-push render gate refused with three heart targets down 1-3 nodes:

    🔴 coverage heart  1120x628 measured 95 node(s), was 96. Something this gate used to watch
       is gone. If that is intended, say so and re-bless; if it is not, this is the defect.

Every one of those readings was GREEN on pixels — 0 render failures, nothing clipped, nothing
off-screen, every node painting at all five widths. Only the COUNT moved. And `render_coverage.json`
stored counts and nothing else, so there was no way, from the file, to learn which node had gone.

⚠⚠ THAT IS THE DEFECT, NOT THE DROP. A refusal nobody can answer gets re-blessed blind, and a
ratchet re-blessed blind is the thing that excuses the next real collapse. The gate's own message
asks "if that is intended, say so" — and nothing in the repo could tell you whether it was.
[[zero-needs-a-denominator]] [[unknown-stays-unknown]] [[regression-guard]]

So v3201 records a weak signature per node — tag, first class, 40 characters of text — beside the
count, and a drop prints the multiset difference. Deliberately WEAK so ordinary copy edits do not
churn it, and deliberately DIAGNOSTIC: nothing fails because a signature changed. The ratchet is
still the count.

⚠ AND IT TELLS THE TRUTH WHEN IT CANNOT HELP. On the very run that introduced it there was no
recorded baseline, so it printed "no signatures were recorded for this target at this width, so
WHAT left is UNKNOWN" rather than inventing an answer. That refusal is asserted below, because a
diagnostic that fabricates on a cold start is worse than none.
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

RC = os.path.join(HERE, "render_check.py")
COVERAGE = os.path.join(HERE, "render_coverage.json")


def _src():
    with io.open(RC, encoding="utf-8") as fh:
        return fh.read()


def _py_only(src):
    """Strip only `#` comment lines. -> the source a Python assertion may read.

    ⚠⚠ THE FIRST CUT OF THIS HELPER STRIPPED TRIPLE-QUOTED STRINGS, "to remove docstrings", AND
    IT DELETED THE VERY CODE UNDER TEST. `render_check.py` keeps its browser probe in a
    triple-quoted JS literal, so a docstring stripper removes the whole probe and two assertions
    went red against a file that plainly contained what they were looking for. A prose filter that
    cannot tell a docstring from a heredoc of real code is the [[source-reading-guard]] trap
    running backwards: instead of prose satisfying a guard, prose-removal HID the code from it.

    So: `#` lines only, and every JS assertion below anchors on an expression precise enough that
    a comment cannot satisfy it — which is the same protection, bought without deleting anything.
    """
    return re.sub(r"(?m)^\s*#.*$", " ", src)


class ACoverageDropCanBeNamed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = _src()
        cls.code = _py_only(cls.src)

    def test_the_probe_emits_a_signature_per_node(self):
        self.assertIn("var _sig = nodes.map(", self.code,
                      "the probe no longer collects a signature per node, so a drop is back to "
                      "being un-nameable")
        self.assertIn("sig:_sig", self.code,
                      "the signatures are collected and then not returned")

    def test_the_signature_is_sliced_by_CODE_POINT_not_code_unit(self):
        """⚠ THIS COST A FULL 19-TARGET RENDER. `.slice(0, 40)` cuts UTF-16 code units, and this
        console's text is full of emoji, so a cut inside a surrogate pair left a LONE SURROGATE
        that rode through the probe and the JSON round-trip and then killed the bless at the very
        last step: "UnicodeEncodeError: 'utf-8' codec can't encode character '\\ud83d'"."""
        self.assertIn("Array.from((n.textContent", self.code,
                      "the node text is being sliced by code unit again — an emoji cut in half "
                      "leaves a lone surrogate that kills the bless AFTER the whole render is paid")
        self.assertNotIn("').trim().slice(0, 40)", self.code,
                         "the raw code-unit slice is back")

    def test_the_python_side_can_never_be_killed_by_one_bad_character(self):
        """a page may contain a lone surrogate of its own; one character must not cost a render."""
        self.assertIn('encode("utf-8", "replace").decode("utf-8")', self.code,
                      "the signature writer is no longer total — an unencodable character from "
                      "any page takes the whole bless down at the write step")

    def test_a_drop_prints_what_went_missing(self):
        self.assertIn('say("     gone: %s"', self.code,
                      "a coverage drop no longer names the signatures that vanished")
        self.assertIn("_left.remove(_x)", self.code,
                      "the difference is not a multiset difference, so a row that appears twice "
                      "and loses one copy would report as unchanged")

    def test_it_says_UNKNOWN_rather_than_guessing_on_a_cold_start(self):
        self.assertIn("no signatures were recorded for this target at this width", self.code,
                      "with no baseline the drop message invents an answer instead of saying it "
                      "cannot help — a diagnostic that fabricates on a cold start is worse than "
                      "none")

    def test_nothing_FAILS_on_a_signature_change(self):
        """the ratchet is the COUNT. A signature is a hint, and a hint that can refuse a push
        would churn on every copy edit and be disabled within a week."""
        self.assertGreater(self.code.find('say("     gone: %s"'), 0)
        self.assertIn("if isinstance(_was_sig, list) and isinstance(_now_sig, list):", self.code,
                      "the naming block no longer guards on having BOTH lists, so a missing "
                      "baseline could raise inside a gate whose job is to report")

    def test_the_recorded_signatures_actually_match_the_floors(self):
        """[[the-unjoined-end]] — a `nodes` map that does not line up with `floor` is decoration."""
        if not os.path.isfile(COVERAGE):
            self.skipTest("render_coverage.json has never been written")
        d = json.load(io.open(COVERAGE, encoding="utf-8"))
        floor, nodes = d.get("floor") or {}, d.get("nodes") or {}
        self.assertTrue(nodes, "no signatures are recorded at all, so no drop can ever be named")
        checked, bad = 0, []
        for name, widths in sorted(nodes.items()):
            for w, sig in sorted(widths.items()):
                f = (floor.get(name) or {}).get(w)
                if not isinstance(f, int) or not isinstance(sig, list):
                    continue
                checked += 1
                # the floor may sit BELOW what a run measured (it only rises on a clean full run,
                # and it may be lowered by hand). It must never sit ABOVE: that would mean the
                # names describe fewer nodes than the count demands, and the diff would be junk.
                if f > len(sig):
                    bad.append("%s %s: floor %d > %d recorded signatures" % (name, w, f, len(sig)))
        print("   floor/signature pairs checked: %d" % checked)
        self.assertGreater(checked, 0, "nothing was compared, so a pass here is UNMEASURED")
        self.assertEqual([], bad, "the recorded names cannot explain the floor: %r" % (bad[:4],))


RED_PROOF = [
    ("render_check.py", "var _sig = nodes.map(", "var _sigX = nodes.map(",
     "test_the_probe_emits_a_signature_per_node"),
    ("render_check.py", 'say("     gone: %s"', 'say("     goneX: %s"',
     "test_a_drop_prints_what_went_missing"),
    ("render_check.py", 'encode("utf-8", "replace").decode("utf-8")', 'encode("utf-8").decode()',
     "test_the_python_side_can_never_be_killed_by_one_bad_character"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
