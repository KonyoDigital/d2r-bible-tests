# -*- coding: utf-8 -*-
"""v2718 — A WEEK-OLD FAILURE WAS PRINTED AS THE PRESENT STATE OF HIS SECOND EYE.

Found 2026-09-06 by the cross-family read he INSISTED on before I ruled any design item out —
*"that OBVIOUSLY needs to happen before you rule it out"*. Asked whether raw machine output leaks
into a user surface, the second eye answered STILL A PROBLEM and quoted the panel back:

    "grok exit 1: Internal error: { \"message\": \"API error (status 402 Payment Required)...
     subscription CLIs\" sitting directly in the user-facing ADVANCED panel"

And the sentence above it read, in the PRESENT TENSE:

    "the Grok balance is exhausted — the second eye cannot read until it is topped up"

MEASURED THE SAME MINUTE: 14 successful Grok reads that day, and `grok -p` answered ALIVE. The
balance was fine. The panel's own text dated the error at "7d ago" and asserted it as now.

=== THE HOLE, AND IT IS NARROW ===
v2292 already split this BY TENSE (remembered -> hover, live -> the line) and v2119 already fixed
the `dailyUsed === 0` version. But `_stale` was decided ONLY by comparing the `N/M today` numbers
INSIDE the error string against the live budget. A 402 carries no such numbers, matches nothing,
and a week-old failure printed as current.

⚠⚠ MEANWHILE `_age` WAS COMPUTED FOUR LINES ABOVE, RENDERED INTO THE LINE, AND NEVER ASKED. The
age of the thing was on screen and was not used for the one judgement age exists to make. That is
[[stale-reading]] with the measurement already in hand. [[label-outlived-referent]]

⚠ WHY A THRESHOLD AND NOT "ANY AGE": a failure minutes old IS the current state and must stay on
the line — the v1501 scar this whole block was built for. An hour is the bar: long enough that a
real outage still reads live, short enough that nothing a week old can claim the present tense.
"""
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")


def _node():
    """-> a node binary, or FAIL. A skip here would be recorded as a PASS."""
    for exe in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
        try:
            if subprocess.run([exe, "-v"], capture_output=True).returncode == 0:
                return exe
        except Exception:
            continue
    raise AssertionError(
        "GATE CANNOT RUN: node is not available, so nothing here was graded. That is a FAILURE, "
        "not a skip — a skipped gate exits 0 and is recorded as a pass."
    )


def _region(start, end, what):
    """The real source between two anchors, bound at BOTH ends.

    Not a fixed window: a window past the region reads as absent and would grade a truncated
    fragment. [[source-window-shortcut]]
    """
    s = io.open(UI, encoding="utf-8").read()
    try:
        i = s.index(start)
        j = s.index(end, i)
    except ValueError:
        raise AssertionError(
            "GUARD CANNOT GRADE: %s is not where this test expects it (%r .. %r). It was renamed "
            "or moved — fix this test before trusting any verdict it prints." % (what, start[:40], end[:40])
        )
    return s[i:j]


class TheEyesBannerAgesOut(unittest.TestCase):

    def setUp(self):
        self.stale_src = _region("        var _ageMs = _et ?",
                                 "        var _m = /(\\d+)\\/(\\d+) today/",
                                 "the staleness decision")
        self.line_src = _region("        var _rawErr = String(g5s.last_error",
                                "        if (_stale) { more.push(_errLine",
                                "the error line builder")

    def _decide(self, age_ms):
        """Run the REAL staleness code against one age. -> the _stale string ('' means LIVE)."""
        js = ("function decide(ageMs){ var _et = ageMs===null?null:(Date.now()-ageMs); var _stale='';\n"
              + self.stale_src + "\n return _stale; }\n"
              "console.log(JSON.stringify(decide(%s)));\n"
              % ("null" if age_ms is None else str(int(age_ms))))
        t = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        t.write(js); t.close()
        try:
            r = subprocess.run([_node(), t.name], capture_output=True, text=True, timeout=30)
        finally:
            os.unlink(t.name)
        if r.returncode != 0:
            raise AssertionError("the staleness code did not run: %s" % (r.stderr or "")[:300])
        import json as _j
        return _j.loads(r.stdout.strip().splitlines()[-1])

    def test_a_WEEK_old_error_is_a_memory_not_the_present_tense(self):
        """The defect itself: this is what was printed as his second eye's current state."""
        self.assertTrue(
            self._decide(7 * 24 * 3600 * 1000),
            "a SEVEN DAY OLD error is still being reported as live. That is what put 'the Grok "
            "balance is exhausted' on his panel while 14 reads were succeeding that same day."
        )

    def test_a_FRESH_error_still_reads_as_live(self):
        """⚠ THE OTHER DIRECTION, and the reason this is a threshold and not 'any age'. A real
        outage minutes old is the FIRST thing he needs on the line. Pushing everything to the
        hover would be the v1501 scar again, from the opposite side."""
        for mins in (1, 5, 59):
            self.assertEqual(
                self._decide(mins * 60 * 1000), "",
                "an error %d minute(s) old was demoted to a memory — a live outage must stay on "
                "the line, or the panel goes quiet exactly when it matters" % mins
            )

    def test_the_boundary_is_an_hour_and_it_is_crossed(self):
        """A threshold nobody crosses is a threshold nobody has tested."""
        self.assertEqual(self._decide(59 * 60 * 1000), "", "59 minutes should still read live")
        self.assertTrue(self._decide(61 * 60 * 1000), "61 minutes should read as a memory")

    def test_an_error_with_NO_timestamp_is_not_assumed_old(self):
        """Nobody-recorded is not the same fact as old. It stays visible rather than being hidden
        on an assumption. [[unknown-stays-unknown]]"""
        self.assertEqual(
            self._decide(None), "",
            "an error with no timestamp was demoted to a memory. Its age is UNKNOWN, and hiding "
            "it on a guess is how a live failure goes quiet."
        )

    def test_raw_machine_output_never_reaches_the_line(self):
        """The second eye's other finding: a JSON blob in a surface a person reads."""
        js = ("function build(err){ var _age='7d ago', more=[], g5s={last_error:err};\n"
              + self.line_src + "\n return {line:_errLine, more:more}; }\n"
              "console.log(JSON.stringify(build('grok exit 1: Internal error: "
              "{ \"message\": \"API error (status 402 Payment Required): Grok\" }')));\n")
        t = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        t.write(js); t.close()
        try:
            r = subprocess.run([_node(), t.name], capture_output=True, text=True, timeout=30)
        finally:
            os.unlink(t.name)
        self.assertEqual(r.returncode, 0, "the line builder did not run: %s" % (r.stderr or "")[:300])
        import json as _j
        got = _j.loads(r.stdout.strip().splitlines()[-1])
        line = got["line"]
        for bad in ('{', '"message"', 'http_status'):
            self.assertNotIn(bad, line,
                             "raw machine output reached the visible line: %r" % line[:160])
        self.assertTrue(got["more"], "the raw payload was DISCARDED rather than moved to the "
                                     "hover — it is still evidence, it just is not a headline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
