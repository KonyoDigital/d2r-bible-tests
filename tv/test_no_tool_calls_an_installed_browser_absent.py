# -*- coding: utf-8 -*-
"""#161 (REG-3064) - NO TOOL CALLS AN INSTALLED-BUT-SLOW CHROME "ABSENT".

REG-3060 gave the launcher its grace, one retry and a named cause, and REG-3061 made a browser LAW that could not get its
Chrome a venue fault. Four tools on the same launcher still said otherwise when Chrome was installed and would not start:
a11y_check and coldread printed "no Chrome on :N"; crest_loudness printed "no Chrome on :N" and exited 77, which its gate
declares as a skip - so an installed, failing browser read like the declared venue-without-a-browser, a pass in all but
name; and overlap_ratchet exited 1, a red, for the same fault. Now each asks render_check.no_browser_say(), which calls a
missing binary absent and an installed one a VENUE FAULT with the launcher's cause; the two gates exit VENUE_EXIT (3) for
it, which run_gates reads with the mark as VENUE (tv/test_a_law_that_cannot_measure_is_unknown_never_red.py). A missing
Chrome keeps its declared skip.

Driven: each tool's own entry with the launcher stubbed to say no, Chrome's path pointed at a file that exists (installed)
or does not (absent), and the launcher's last cause set. No browser is started. RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import render_check as RC  # noqa: E402
import run_gates as RG  # noqa: E402

CAUSE = ":41001 was alive and never answered /json/version in 40 s; :51002 exited with code 1"


class _Fixture(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="no-tool-absent-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.installed = os.path.join(self.tmp, "chrome")
        with io.open(self.installed, "w") as fh:
            fh.write("#")
        self.absent = os.path.join(self.tmp, "no-chrome-here")
        p = mock.patch.object(RC, "_chrome_up", lambda *a, **k: False)
        p.start()
        self.addCleanup(p.stop)
        saved = dict(RC._CHROME_START)
        self.addCleanup(lambda: (RC._CHROME_START.clear(), RC._CHROME_START.update(saved)))
        RC._CHROME_START.update(attempts=[], why=CAUSE)

    def chrome_at(self, path):
        p = mock.patch.object(RC, "CHROME", path)
        p.start()
        self.addCleanup(p.stop)

    def said(self, fn, *args):
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fn(*args)
        return rc, buf.getvalue()


class TheReasonNeverCallsAnInstalledBrowserAbsent(_Fixture):

    def test_the_one_rule(self):
        self.chrome_at(self.installed)
        absent, why = RC.no_browser_say()
        self.assertFalse(absent)
        self.assertIn(RC.VENUE_MARK, why)
        self.assertIn(CAUSE, why)
        self.chrome_at(self.absent)
        absent, why = RC.no_browser_say()
        self.assertTrue(absent)
        self.assertNotIn(RC.VENUE_MARK, why)

    def test_a_law_follows_the_one_rule_too(self):
        # REG-3119 (the second eye on v3840): require_chrome raised the INSTALLED VenueFault with no binary at all.
        self.chrome_at(self.installed)
        with self.assertRaises(RC.VenueFault) as cm:
            RC.require_chrome()
        self.assertIn(RC.VENUE_MARK, str(cm.exception))
        self.assertIn("INSTALLED", str(cm.exception))
        self.chrome_at(self.absent)
        with self.assertRaises(AssertionError) as cm:
            RC.require_chrome()
        self.assertNotIsInstance(cm.exception, RC.VenueFault, "an absent Chrome was called a venue that would not start")
        self.assertNotIn(RC.VENUE_MARK, str(cm.exception))
        self.assertNotIn("INSTALLED", str(cm.exception))
        self.assertIn(self.absent, str(cm.exception))

    def test_the_exits_agree(self):
        import overlap_ratchet as OR
        self.assertEqual((RC.VENUE_EXIT, OR.VENUE_EXIT), (RG.VENUE_EXIT, RG.VENUE_EXIT))
        self.assertEqual((RC.VENUE_MARK, OR.VENUE_MARK), (RG.VENUE_MARK, RG.VENUE_MARK))


class EachToolSaysWhichItWas(_Fixture):

    def test_a11y_check(self):
        import a11y_check as A
        self.chrome_at(self.installed)
        rc, out = self.said(A.main)
        self.assertEqual(rc, 2)
        self.assertIn(RC.VENUE_MARK, out)
        self.assertNotIn("no Chrome on", out, "an installed Chrome that would not start was called absent")

    def test_coldread(self):
        import coldread as C
        self.chrome_at(self.installed)
        rc, out = self.said(C.main, ["coldread", "HEAD", os.path.join(self.tmp, "shots")])
        self.assertEqual(rc, 2)
        self.assertIn(RC.VENUE_MARK, out)
        self.assertNotIn("no Chrome on", out, "an installed Chrome that would not start was called absent")

    def test_crest_loudness_is_venue_not_its_declared_skip(self):
        import crest_loudness as CL
        self.chrome_at(self.installed)
        rc, out = self.said(CL.main)
        self.assertEqual(rc, RG.VENUE_EXIT, "an installed Chrome that would not start took the declared skip: %r" % out)
        self.assertEqual(RG.gate_status(rc, out), "VENUE")
        self.chrome_at(self.absent)
        rc, out = self.said(CL.main)
        self.assertEqual((rc, RG.gate_status(rc, out)), (RG.SKIP_EXIT, "SKIP"), "PREMISE: no Chrome at all keeps its skip")

    def test_overlap_ratchet_is_venue_not_red(self):
        import overlap_ratchet as OR
        self.chrome_at(self.installed)
        got, why = OR.measure()
        self.assertIsNone(got)
        self.assertEqual(OR._unmeasured_exit(why), RG.VENUE_EXIT, "an installed Chrome that would not start read RED")
        self.assertEqual(RG.gate_status(OR._unmeasured_exit(why), "⚪ UNKNOWN — %s" % why), "VENUE")
        self.chrome_at(self.absent)
        got, why = OR.measure()
        self.assertEqual(OR._unmeasured_exit(why), OR.SKIP_EXIT, "PREMISE: no Chrome at all keeps its declared skip")
        self.assertEqual(OR._unmeasured_exit("the page answered and the count failed"), 1,
                         "PREMISE: a real failure after the browser answered is still red")


RED_PROOF = [
    {"why": "REG-3119 - a law with no Chrome binary at all is called a venue whose INSTALLED Chrome would not start",
     "file": "render_check.py",
     "find": "    if chrome_absent:\n        raise AssertionError(",
     "replace": "    if False:\n        raise AssertionError(",
     "matches": 1},
    {"why": "REG-3064 - an installed Chrome that would not start is called absent again",
     "file": "render_check.py",
     "find": "    if not os.path.exists(CHROME):\n        return True, \"no Chrome on this machine (looked for %s)\" % CHROME\n",
     "replace": "    if True:\n        return True, \"no Chrome on this machine (looked for %s)\" % CHROME\n",
     "matches": 1},
    {"why": "REG-3064 - a11y_check calls an installed Chrome absent again",
     "file": "a11y_check.py",
     "find": "        print(\"⚪ UNKNOWN — %s. A skip is not a pass.\" % rc.no_browser_say()[1])\n",
     "replace": "        print(\"⚪ UNKNOWN — no Chrome on :%d. A skip is not a pass.\" % rc.PORT)\n",
     "matches": 1},
    {"why": "REG-3064 - coldread calls an installed Chrome absent again",
     "file": "coldread.py",
     "find": "        print(\"⚪ UNKNOWN — %s. A skip is not a pass.\" % rc.no_browser_say()[1])\n",
     "replace": "        print(\"⚪ UNKNOWN — no Chrome on :%d. A skip is not a pass.\" % rc.PORT)\n",
     "matches": 1},
    {"why": "REG-3064 - crest_loudness takes its declared 'no Chrome' skip for an installed Chrome that would not start",
     "file": "crest_loudness.py",
     "find": "        if not _absent:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-3064 - overlap_ratchet reads an installed Chrome that would not start as a red again",
     "file": "overlap_ratchet.py",
     "find": "    return VENUE_EXIT if VENUE_MARK in str(why or \"\") else 1\n",
     "replace": "    return 1\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
