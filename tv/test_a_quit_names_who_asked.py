# -*- coding: utf-8 -*-
"""A QUIT MUST SAY WHO ASKED, BECAUSE HIS CONSOLE DIED AND NOBODY COULD NAME THE CAUSE.

★ Grok Bot, driving the native seat as a user and ranking four traps worst-first:

    "Mule 2->3 arrow -> native window closed (`window gone (api-quit)` in log). No Esc sent."

His console was killed by clicking a UI arrow, and the log line was the same one a deliberate
exit writes. I could NOT reproduce it: `/api/quit` has exactly ONE caller in the page (the Escape
empty-stack handler) and the board iframe has none. So either an Escape reached that handler by a
path neither of us can see, or something POSTed the route directly.

⚠ IT CANNOT BE FIXED BLIND, SO IT IS MADE DIAGNOSABLE. Every quit now carries the name of whoever
asked; an unnamed one is recorded as UNATTRIBUTED. Since the Escape handler is the only page
caller, an UNATTRIBUTED line in his log is itself the finding — it means something else killed the
console, and the next occurrence carries its own evidence instead of being a mystery.

A cause nobody can name is a cause nobody can fix. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

APP = os.path.join(HERE, "control_app.py")
UI = os.path.join(HERE, "control_ui.html")


def _py_code():
    """control_app.py with `#` comment lines out — prose must not satisfy a law here."""
    with io.open(APP, encoding="utf-8", errors="replace") as f:
        src = f.read()
    return re.sub(r"(?m)^\s*#.*$", " ", src)


def _js_code():
    with io.open(UI, encoding="utf-8", errors="replace") as f:
        src = f.read()
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", src)


class AQuitNamesWhoAsked(unittest.TestCase):

    def _route(self):
        src = _py_code()
        i = src.find('if path == "/api/quit":')
        self.assertGreater(i, -1, "the /api/quit route is gone — re-anchor this law")
        # ⚠ /api/quit is the LAST route in the file, so there is no following `if path == "` to
        # anchor against. The first cut asserted there was one and aborted every law with
        # "could not find the end of the route" — a law that refuses to read is not a strict law,
        # it is a broken one. Bounded by the next route OR the end of the file, whichever comes
        # first, so the slice is still both-ends anchored. [[source-reading-guard]]
        j = src.find('if path == "', i + 10)
        if j < 0:
            j = len(src)
        return src[i:j]

    def test_the_route_reads_an_attribution(self):
        blk = self._route()
        self.assertIn('"from"', blk,
                      "/api/quit does not read WHO asked, so a console death is indistinguishable "
                      "from a deliberate exit after the fact — which is why Grok Bot could only "
                      "report it as a mystery")

    def test_an_unnamed_quit_is_recorded_as_UNATTRIBUTED(self):
        """⚠ NOT a default that reads like a cause. 'api-quit' alone looked like an explanation and
        explained nothing; UNATTRIBUTED says plainly that nobody claimed it. [[unknown-stays-unknown]]"""
        blk = self._route()
        self.assertIn("UNATTRIBUTED", blk,
                      "an unnamed quit falls back to something that reads like a cause. The whole "
                      "point is that an unclaimed quit must ANNOUNCE that it is unclaimed")

    def test_the_attribution_reaches_the_thing_that_PRINTS(self):
        """★ THE JOINT. Reading `from` and then discarding it would be a fix that ships and
        attributes nothing — the shape this session has hit four times."""
        blk = self._route()
        self.assertIn("_request_console_exit(_qwho", blk,
                      "the attribution is read and then NOT passed to the exit path, so the line "
                      "in his log still says nothing about who asked")
        self.assertNotIn('_request_console_exit("api-quit"', blk,
                         "the exit is still requested with the old fixed string, so the "
                         "attribution never reaches the log")

    def test_the_only_page_caller_NAMES_itself(self):
        """If the one legitimate caller did not name itself, every quit would read UNATTRIBUTED
        and the signal would be worthless — a flag that is always on."""
        js = _js_code()
        i = js.find("'/api/quit'")
        self.assertGreater(i, -1, "the page no longer calls /api/quit — re-anchor this law")
        self.assertIn("escape-empty-stack", js[i:i + 400],
                      "the Escape handler does not name itself, so a legitimate exit is also "
                      "recorded as UNATTRIBUTED and the signal cannot distinguish anything")


if __name__ == "__main__":
    unittest.main(verbosity=2)
