# -*- coding: utf-8 -*-
"""v3393 — A MACHINE THAT HAS NEVER RECORDED IS NOT A BROKEN MACHINE.

MEASURED on his Windows ALT box, read live over its own loopback 2026-09-20. It had never filmed:
capture doors onair/mini/shadow ALL reported "no sealed reel from this door yet", the screen said
"No runs recorded yet", and "unattended reel" said "nothing is recording". Yet the console reported:

    reel population : cannot read C:\\...\\tv\\frames\\hist: [WinError 3]
    retention       : could not read the disk ([WinError 3])
    the river       : UNKNOWN, tombstone ledger unreadable
    THE SHELF       : a 0x0 box - "nothing is visible"

⚠⚠ THE TREE WAS ABSENT CORRECTLY. tv_diablo creates frames/ and frames/hist INSIDE _film_loop
(tv_diablo.py:1894), so a console that has never filmed HAS NO SUCH PATH BY DESIGN. I first read
this as a provisioning defect and was going to ship a whole discoverer to fix it; the code refuted
that. The real fault is that an ORDINARY EMPTY STATE WAS DRESSED AS A FAILURE - the confident-zero
defect inverted - and it is what sent him hunting a sync bug that does not exist.

⚠ A PATH MUST NOT ENTER THE NEW MESSAGE. A Windows profile can carry a non-ASCII character, and
printing it crashes a cp1255 console WHILE it reports the error. A third eye ranked that second of
five risks on this arc, and a push of mine was refused for exactly it an hour earlier.
"""
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ unittest -v prints the first docstring line, and these carry a warning sign.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import end_routes as ER          # noqa: E402
import reel_retention as RR      # noqa: E402

NEVER = "nothing has been recorded"
BROKEN = "cannot read"


class ANeverRecordedMachineIsNotABrokenOne(unittest.TestCase):

    def _absent(self):
        return os.path.join(tempfile.gettempdir(), "__no_hist_%d__" % os.getpid())

    def test_the_planner_says_never_recorded_not_cannot_read(self):
        """reel_retention.plan is the SOURCE; every consumer inherits its words."""
        p = RR.plan(hist_dir=self._absent())
        why = str(p.get("why") or "")
        self.assertIn(NEVER, why, "an absent footage tree still reports as unreadable: %r" % why[:120])
        self.assertNotIn(BROKEN, why)
        self.assertFalse(p.get("ok"), "an absent tree must not report ok")

    def test_the_walker_says_never_recorded_not_cannot_read(self):
        r = ER.report(hist_dir=self._absent())
        self.assertIn(NEVER, str(r.get("why") or ""))
        self.assertNotIn(BROKEN, str(r.get("why") or ""))

    def test_the_safety_ladder_inherits_it_rather_than_re_deriving(self):
        """end_routes._safety forwards plan()'s why - fixing the source fixed this too."""
        r = ER.report(hist_dir=self._absent())
        self.assertIn(NEVER, str(r.get("safetyWhy") or ""))

    def test_a_REAL_read_failure_still_says_cannot_read(self):
        """⚠ THE BASELINE. If everything became 'never recorded', the law would measure nothing.

        A FILE standing where hist should be raises ENOTDIR, not ENOENT, and the path EXISTS - so
        it is a genuine failure and must keep saying so. [[regression-guard]]
        """
        fd, as_file = tempfile.mkstemp()
        os.close(fd)
        try:
            p = RR.plan(hist_dir=as_file)
            why = str(p.get("why") or "")
            self.assertIn(BROKEN, why,
                          "a genuine read failure was reported as 'never recorded', which would "
                          "hide a real fault behind a reassuring sentence: %r" % why[:120])
            self.assertNotIn(NEVER, why)
        finally:
            os.remove(as_file)

    def test_no_path_reaches_the_never_recorded_message(self):
        """A non-ASCII profile path in a message kills a cp1255 console mid-report."""
        absent = self._absent()
        for why in (str(RR.plan(hist_dir=absent).get("why") or ""),
                    str(ER.report(hist_dir=absent).get("why") or "")):
            self.assertNotIn(absent, why, "the absent path leaked into the message")
            self.assertNotIn(tempfile.gettempdir(), why)

    def test_the_distinction_is_errno_not_string_matching(self):
        """Grading the exception, never the text of someone else's error."""
        src = io.open(os.path.join(HERE, "reel_retention.py"), encoding="utf-8").read()
        self.assertIn('getattr(e, "errno", None) == _errno.ENOENT', src,
                      "the never-recorded branch no longer asks the errno")


RED_PROOF = [
    {
        "why": "without the errno branch in the planner, a machine that has simply never filmed is "
               "told its footage tree is unreadable - the exact message that sent him hunting a "
               "sync defect that does not exist",
        "file": "tv/reel_retention.py",
        "find": '        if getattr(e, "errno", None) == _errno.ENOENT or not os.path.exists(hist):',
        "replace": '        if False:',
        "matches": 1,
    },
    {
        "why": "the walker has its own copy of the decision; losing it puts the failure wording "
               "back on the shelf even while the planner is correct",
        "file": "tv/end_routes.py",
        "find": '        if getattr(e, "errno", None) == _errno.ENOENT or not os.path.exists(hist):',
        "replace": '        if False:',
        "matches": 1,
    },
    {
        "why": "a path in the never-recorded message crashes a cp1255 console WHILE it reports, so "
               "a clean tree exits non-zero for a reason unrelated to the check",
        "file": "tv/reel_retention.py",
        "find": '                    "why": ("no footage tree on this machine yet — nothing has been "',
        "replace": '                    "why": (hist + " — nothing has been "',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
