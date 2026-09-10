# -*- coding: utf-8 -*-
"""v2782 — THE PIXEL WITNESS LOOKED AT ITSELF, AND SAID UNKNOWN FOREVER.

2026-09-08. Konyo sent a screenshot of a fully BLACK `TV DIABLO` window and asked why the same bug
was back. Running the one hand-run instrument for exactly that question:

    $ python3 tv/paint_witness.py --json
    {"state": "UNKNOWN", "pid": 60574,
     "why": "pid 60574 owns no on-screen window big enough to be his console"}

**pid 60574 did not exist.** The line was:

    pid = int(next((a for a in argv if a.isdigit()), os.getpid()))

With no argument it looked at THE INTERPRETER RUNNING THE WITNESS. That process owns no window, so
the answer was UNKNOWN — every time, forever, by construction. The module's own usage line says

    python3 tv/paint_witness.py           # look at his console once

and it had never once looked at his console. A default that measures the asker is not a
measurement, and a doc line that describes what the code does not do is a label that outlived its
referent. [[label-outlived-referent]] [[feedback-suspect-the-instrument]]

=== ⚠ WHY IT MATTERED THAT DAY ===
His window was black; the page was still alive (his own report: the hover art still painted). That
is the one state where asking the PAGE cannot help and only the PIXELS can answer — and the pixel
instrument was pointed at nothing. After the fix, pointed at his real console, it found window
37043 and measured `modalShare 0.108 across 142 distinct luminances` = PAINTED.

=== ⚠ THE PORT HAS MORE THAN ONE OWNER ===
Measured the same day: `:17772` was held by the console (pid 14222) AND by a WebKit XPC renderer
service (pid 60423) that owns no window of its own. Taking the first pid `lsof` prints would have
reproduced the original bug with a different wrong answer, so `console_pid()` takes the owner that
actually has a window. [[zero-needs-a-denominator]]

=== ⚠ THESE LAWS PARSE, THEY DO NOT GREP ===
The fix's own comment quotes the defective call by name to explain it. A substring search would go
red on the explanation of the thing it forbids — nine prose-reads in this session already.
[[source-reading-guard]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import paint_witness as PW  # noqa: E402

SRC = io.open(os.path.join(HERE, "paint_witness.py"), encoding="utf-8").read()
TREE = ast.parse(SRC)


def _fn(name):
    for n in ast.walk(TREE):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _calls_in(fn):
    """Every dotted/plain call name inside fn, from the AST. Comments cannot appear here."""
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                base = getattr(f.value, "id", "")
                out.add(("%s.%s" % (base, f.attr)).lstrip("."))
            elif isinstance(f, ast.Name):
                out.add(f.id)
    return out


class ThePixelWitnessLooksAtHisConsole(unittest.TestCase):

    # -- THE LAW ---------------------------------------------------------------------------
    def test_main_never_falls_back_to_its_OWN_pid(self):
        """*** THE EXACT LINE THAT SHIPPED. `os.getpid()` as the default made every hand-run look
        report UNKNOWN about the witness's own interpreter. Parsed, not grepped: the fix's comment
        names `os.getpid()` to explain it, and a substring law would go red on the explanation."""
        fn = _fn("main")
        self.assertIsNotNone(fn, "main() is gone - this law inspected nothing")
        self.assertNotIn("os.getpid", _calls_in(fn),
                         "the witness CLI defaults to its OWN pid again, so every hand-run look "
                         "reports UNKNOWN about the interpreter instead of his console")

    def test_main_asks_for_the_CONSOLE_pid(self):
        """The replacement must actually be console discovery, not merely the absence of the bug.
        Removing the bad default and leaving nothing would be a crash, not a fix."""
        self.assertIn("console_pid", _calls_in(_fn("main")),
                      "main() no longer discovers his console pid")

    def test_console_pid_is_UNKNOWN_when_nothing_listens(self):
        """*** [[unknown-stays-unknown]]. No listener is 'nobody is serving that port', which is
        neither a blank console nor a healthy one. It must not fall back to any pid at all."""
        self.assertIsNone(PW.console_pid(port=59999),
                          "console_pid invented a pid for a port nothing listens on")

    def test_console_pid_skips_an_owner_with_NO_WINDOW(self):
        """*** MEASURED: :17772 was held by the console AND by a WebKit XPC renderer service that
        owns no window. Taking the first pid lsof prints reproduces the original bug wearing a
        different wrong number."""
        fn = _fn("console_pid")
        self.assertIsNotNone(fn, "console_pid is gone")
        self.assertIn("window_for", _calls_in(fn),
                      "console_pid no longer checks that the port owner actually has a window, so "
                      "a renderer helper can be chosen and every look reports UNKNOWN again")

    def test_the_usage_line_still_promises_what_the_code_now_does(self):
        """The doc said 'look at his console once' while the code looked at itself. Now that the
        code does it, the promise must stay - if the usage line is ever removed, this law should be
        re-decided rather than silently drift back."""
        self.assertIn("look at his console once", SRC,
                      "the usage line moved; re-check that the CLI still targets his console")

    def test_look_still_takes_an_EXPLICIT_pid(self):
        """*** THE FALLBACK THAT MUST SURVIVE. Callers inside control_app pass a pid on purpose;
        discovery is for the CLI only. If look() ever started discovering for itself, an in-process
        caller asking about a specific window would silently be answered about another."""
        fn = _fn("look")
        self.assertIsNotNone(fn, "look() is gone")
        self.assertEqual(fn.args.args[0].arg, "pid",
                         "look() no longer takes an explicit pid as its first argument")
        self.assertNotIn("console_pid", _calls_in(fn),
                         "look() discovers its own target now, so a caller that asked about one "
                         "window can be answered about a different one")


RED_PROOF = [
    {
        'why': 'console_pid() must not hand back the FIRST pid lsof prints for :17772 — measured 2026-09-08, that port was held by his console (14222) AND by a WebKit XPC renderer service (60423) that owns no window, so taking the first owner reproduces the original "UNKNOWN forever" bug wearing a different wrong number. The line `wid, _why = window_for(pid)` inside console_pid is the whole discipline: only the owner that ACTUALLY HAS A WINDOW is returned. Replacing it with `(pid, "")` keeps console_pid importable and still returning an int, keeps the no-listener case returning None, and deletes exactly the window check — nothing else. The anchor is executable code, not a comment: the module\'s docstring and main()\'s comment both mention window discovery, and this law parses the AST of console_pid rather than grepping, so only the real call counts.  MEASURED: untampered Ran 6 tests — OK (all 6 green) via `python3 test_the_pixel_witness_looks_at_his_console.py; tampered (all 1) Ran 6 tests — FAILED (failures=1). Exactly one law red: test_console_pid_skips_an_owner_wi; reddened law test_the_pixel_witness_looks_at_his_console.ThePixelWitnessLooksAtHisC; ALONE Fresh process, `python3 -m unittest test_the_pixel_witness_looks_at_his_console.ThePixelWitnessLooksAtHisConso.',
        'file': 'paint_witness.py',
        'find': 'wid, _why = window_for(pid)',
        'replace': 'wid, _why = (pid, "")',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
