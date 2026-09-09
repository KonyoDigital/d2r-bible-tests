# -*- coding: utf-8 -*-
"""THE JS SYNTAX GATE READ ITS OWN DOCUMENT'S PROSE AS A BROWSER ERROR, AND IT COST SIX PUBLICATIONS.

`js_syntax_gate`'s browser path runs Chrome with `--dump-dom` and `--enable-logging=stderr`. Those
are two different streams and they mean two different things:

    stdout  = the WHOLE rendered document
    stderr  = the console

It concatenated them and grepped the result for `SyntaxError:`. So **any page that merely QUOTES an
error message reports itself as broken.**

MEASURED 2026-09-09: `bible.html` contains exactly **one** match, and it is a code COMMENT written
in v2824 explaining a bug — *"a NEWLINE throws `SyntaxError: Invalid or unexpected token`, taking
the whole routing ledger down"*. The file parses perfectly: `node --check` passes every block, and
the browser path passes too once it stops reading the body.

★ **IT WAS INVISIBLE ON THE MACHINE THAT WRITES THE CODE.** `--dump-dom` never answers over
loopback on his Mac (measured at v1490), so the NODE parser runs locally — and a parser does not
grep prose. On CI the browser answers, the dump lands in stdout, and the grep hits the sentence.
Green where it is written, red where it ships: `Publish — gates, review, then deploy` failed on
v2825, v2828, v2830, v2832, v2833 and v2835-v2837 while the page was fine.

This file already carries a scar one layer up — v1808, *"a timeout is not a syntax verdict"* — for
reporting a slow runner as a broken page. This is the same shape: something that is not a verdict,
filed as one. [[feedback-comments-vs-code]] [[source-reading-guard]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import js_syntax_gate as G  # noqa: E402

SRC = io.open(os.path.join(HERE, "js_syntax_gate.py"), encoding="utf-8").read()


class TheConsoleIsStderr(unittest.TestCase):

    def test_the_error_scan_does_not_read_stdout(self):
        """stdout is the page. Scanning it makes the document its own accuser."""
        i = SRC.find("_ERR.finditer(")
        self.assertGreater(i, 0, "the error scan is gone")
        line = SRC[SRC.rfind("\n", 0, i) + 1: SRC.find("\n", i)]
        self.assertIn("_console", line,
                      "the error scan does not read the console stream: %s" % line.strip())
        # ⚠⚠ PRESENCE IS NOT EXCLUSION — heart2 called the first version BLIND. It asserted only
        # that `_console` appears, which `_ERR.finditer(_console + _dom)` satisfies perfectly while
        # putting the whole page straight back into the scan. The law must say the PAGE IS NOT
        # THERE, not that the console is. [[regression-guard]] — pin the law, not a token.
        for page in ("_dom", "blob", "r.stdout"):
            self.assertNotIn(page, line,
                             "the page body is back in the error scan via %r, so any document that "
                             "QUOTES an error message fails itself — which is what blocked six "
                             "publications: %s" % (page, line.strip()))

    def test_the_context_window_reads_the_console_too(self):
        i = SRC.find("ctx = ")
        self.assertGreater(i, 0)
        line = SRC[SRC.rfind("\n", 0, i) + 1: SRC.find("\n", i)]
        self.assertIn("_console", line,
                      "the reported context is sliced out of the page rather than the console, so "
                      "the message a human reads is a chunk of the document: %s" % line.strip())

    def test_stdout_and_stderr_are_kept_apart(self):
        self.assertIn("_console = r.stderr", SRC, "the console stream is not bound on its own")
        self.assertIn("_dom = r.stdout", SRC, "the document stream is not bound on its own")

    def test_the_crash_check_asks_the_console(self):
        i = SRC.find('"CONSOLE" not in')
        self.assertGreater(i, 0, "the crashed-renderer check is gone")
        line = SRC[SRC.rfind("\n", 0, i) + 1: SRC.find("\n", i)]
        self.assertIn("_console", line,
                      "the crashed-renderer check looks for CONSOLE in the page body, which any "
                      "document could contain: %s" % line.strip())


class ThePagesAreAllowedToQuoteAnError(unittest.TestCase):
    """The regression, stated as the property rather than as one file's contents."""

    def test_a_page_quoting_a_syntax_error_is_not_a_syntax_error(self):
        for rel in ("bible.html", "tv/control_ui.html"):
            path = os.path.join(os.path.dirname(HERE), rel)
            if not os.path.isfile(path):
                continue
            body = io.open(path, encoding="utf-8", errors="replace").read()
            hits = list(G._ERR.finditer(body))
            # The point is NOT that a page must never quote one — it is that quoting one must be
            # harmless. This records how many do, so the number is visible rather than assumed.
            if hits:
                snippet = body[max(0, hits[0].start() - 50):hits[0].end() + 20].replace("\n", " ")
                self.assertNotIn("stdout", "".join(
                    SRC[SRC.rfind("\n", 0, SRC.find("_ERR.finditer(")) + 1:
                        SRC.find("\n", SRC.find("_ERR.finditer("))]),
                    "%s quotes an error message (%r) AND the gate scans stdout — that page fails "
                    "itself" % (rel, snippet[:90]))

    def test_both_surfaces_pass_the_gate_right_now(self):
        """⚠ THE NODE PATH, DELIBERATELY — `check()` drives a real browser and took 196s, which is
        over Heart 2.0's 180s clean-run budget, so the whole gate came back UNPROVABLE for a
        TIMING reason while its laws were perfectly sound. A law nobody can prove is a law nobody
        should trust, and a 3-minute gate is one nobody runs. `check_with_node` parses both files
        deterministically with no browser, no loopback and no server — and it is the path that
        would have caught a genuine syntax error all along. The BROWSER path is exercised where it
        belongs: in CI, on every push."""
        problems, why = G.check_with_node()
        if why:
            self.skipTest("no node here: %s" % why)
        self.assertEqual([], problems,
                         "the shipped surfaces do not parse: %r" % problems)


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "putting the page body back into the error scan is the defect verbatim — bible.html "
               "quotes a SyntaxError in a comment and would fail itself, as it did six times",
        "file": "js_syntax_gate.py",
        "find": "                for m in _ERR.finditer(_console):",
        "replace": "                for m in _ERR.finditer(_console + _dom):",
        "matches": 1,
    },
    {
        "why": "slicing the reported context out of the document hands a human a chunk of the page "
               "instead of the console message that was supposed to explain the failure",
        "file": "js_syntax_gate.py",
        "find": "                    ctx = _console[max(0, m.start() - 200):m.start() + 300]",
        "replace": "                    ctx = _dom[max(0, m.start() - 200):m.start() + 300]",
        "matches": 1,
    },
    {
        "why": "asking the page body whether the renderer crashed lets any document that contains "
               "the word CONSOLE vouch for a renderer that died",
        "file": "js_syntax_gate.py",
        "find": '                if r.returncode not in (0, None) and "CONSOLE" not in _console:',
        "replace": '                if r.returncode not in (0, None) and "CONSOLE" not in _dom:',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
