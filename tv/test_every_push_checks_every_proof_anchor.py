# -*- coding: utf-8 -*-
"""Every push checks EVERY red-proof anchor — not only the laws whose test file changed.

⚠⚠ WHAT IT COST BEFORE THIS EXISTED, all in one day (2026-09-24), REG-1163:
    v3455  read_names_lane.py edited  -> test_the_lane_asks_the_item_not_the_frame[2] matched 0
    v3456  test_control.py re-indented -> test_remeasure_population[0] matched 0
    v3462  handoff.py gained timeout=  -> test_a_failed_read_never_reaches_a_zero_claim[0] matched 0
    v3464  second_eye_ledger.py edited -> test_partial_look_is_not_agreement[3] matched 0 (caught by hand)
The hook re-proves a law only when its TEST file is in the push. A red-proof lives in one test file
and anchors on a line in ANOTHER file, so an ordinary fix to that line never names the proof — and
the proof silently changes nothing while the law reads as proven. The census case
(test_every_declared_red_proof_is_well_formed) knew all four; it simply never ran at push time.

⚠ ITS REACH, STATED: this catches an anchor that matches NOTHING (INVALID). It does not catch a proof
that still matches and no longer turns the law red (BLIND) — only a full `heart2 --prove` sees that.

⚠ A PRESENCE-LAW IS NOT A REACHABILITY-LAW. The gate must run on EVERY push, so this pins that the
call sits at TOP LEVEL of the hook, not inside the `if [ -n "$_chg_live" ]` changed-tests block
where it would run only when a test file changed — the exact blind spot it exists to close.
"""
import io
import os
import sys
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()       # these print non-ASCII; a cp1255 console must not crash while REPORTING
except Exception:
    pass
HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")
CALL = 'if ! gate_run "red-proof anchors"'


class EveryPushChecksEveryProofAnchor(unittest.TestCase):

    def _lines(self):
        return io.open(HOOK, encoding="utf-8").read().split("\n")

    def test_the_hook_runs_the_anchor_census(self):
        lines = self._lines()
        hits = [i for i, l in enumerate(lines) if l.startswith(CALL)]
        self.assertEqual(len(hits), 1, "the hook does not run the red-proof anchor census exactly "
                                       "once at top level (found %d)" % len(hits))
        body = "\n".join(lines[hits[0]:hits[0] + 3])
        self.assertIn("test_every_declared_red_proof_is_well_formed", body,
                      "the gate is named but does not run the census case: %r" % body)

    @staticmethod
    def _depth_before(lines, idx):
        """Top-level block depth at line idx, read from COLUMN-0 openers/closers only.

        ⚠ THREE CUTS, EACH WRONG FOR A NAMED REASON, before this one discriminated: (1) the python
        heredoc's column-0 `for`/`if` counted as bash — heredoc bodies are now skipped; (2) Perl's
        `if (!$p) {` inside a multi-line `perl -e '...'` string counted; (3) requiring `then` on the
        same line mis-counted every continued `if ... \\` condition, reading -5. This hook indents
        every nested statement, so column 0 IS the top-level grammar here — and the baseline case
        below proves the counter can say NESTED before its "top level" is believed."""
        depth, tag = 0, None
        for l in lines[:idx]:
            if tag is not None:
                if l.strip() == tag:
                    tag = None
                continue
            m = re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", l)
            if m and "<<<" not in l:
                tag = m.group(1)
            code = l.split("#", 1)[0].rstrip()
            if re.match(r"^(if|for|while|until|case)\b", code) and not re.search(r"\b(fi|done|esac)$", code):
                depth += 1
            elif re.match(r"^(fi|done|esac)\b", code):
                depth -= 1
        return depth

    def test_it_runs_on_every_push_not_only_when_a_test_changed(self):
        lines = self._lines()
        call = [k for k, l in enumerate(lines) if l.startswith(CALL)]
        self.assertTrue(call, "no top-level call to measure")
        inner = [k for k, l in enumerate(lines) if 'tv/heart2.py" --prove $_gates' in l]
        self.assertTrue(inner, "the changed-law prove call is gone, so the baseline cannot be taken")
        self.assertGreaterEqual(self._depth_before(lines, inner[0]), 1,
                                "BASELINE: the prove call INSIDE the changed-tests block read as top "
                                "level, so this counter cannot tell nested from not")
        self.assertEqual(self._depth_before(lines, call[0]), 0,
                         "the anchor census sits inside a block, so some pushes skip it")

if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the census call removed: an anchor that matches nothing ships as a proven law again",
        "file": "hooks/pre-push",
        "find": "if ! gate_run \"red-proof anchors\"",
        "replace": "if false && ! gate_run \"red-proof anchors - disabled\"",
        "matches": 1,
    },
    {
        "why": "the census moved INSIDE a block — some pushes skip it, the blind spot it closes",
        "file": "hooks/pre-push",
        "find": "if ! gate_run \"red-proof anchors\"",
        "replace": "if [ -n \"${_chg_live:-}\" ]; then\nif ! gate_run \"red-proof anchors\"",
        "matches": 1,
    },
]
