# -*- coding: utf-8 -*-
"""#97 (reviewers, his reader switch) - AN UNREADABLE READER SWITCH STARTS NO PAID SWEEP.

g5_grok_eyes._load_state answered a MISSING switch file and an UNREADABLE one alike ({on: False, mode: off}), and reader()
then said "claude" for both - so a GROK ONLY PC whose switch file was half-written or corrupt started a PAID Claude sweep,
while _sweep_skipped_because_reader_is_grok's own docstring promised that an unreadable switch is UNKNOWN. switch_state()
tells the two apart now: an absent file is a PC that never chose (Claude, the default, still sweeps); an unreadable one
refuses the sweep with a sentence; an env override is a choice the file cannot overrule.

Driven on the real door with the switch file pointed at a temp path. RED_PROOF below.
"""
import os
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
os.environ["TVD_NO_BEACON"] = "1"
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import g5_grok_eyes as G5  # noqa: E402
import control_app as CA  # noqa: E402


class AnUnreadableReaderSwitchStartsNoPaidSweep(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="g5_switch_")
        self.path = os.path.join(self.dir, "g5_grok_eyes.state")
        for p in (mock.patch.object(G5, "_STATE_FILE", self.path),
                  mock.patch.dict(os.environ, {"TV_G5_GROK_EYES": ""})):
            p.start()
            self.addCleanup(p.stop)

    def _ask(self, body):
        if body is None:
            if os.path.exists(self.path):
                os.remove(self.path)
        else:
            with open(self.path, "w", encoding="utf-8") as fh:
                fh.write(body)
        return CA._sweep_skipped_because_reader_is_grok()

    def test_a_pc_that_never_chose_still_sweeps_with_claude(self):
        self.assertIsNone(self._ask(None), "a PC with no switch file was refused its sweep")
        self.assertEqual(G5.switch_state(), "absent")

    def test_a_readable_switch_decides_as_before(self):
        self.assertIsNone(self._ask('{"on": false, "mode": "off"}'))
        r = self._ask('{"on": true, "mode": "only"}')
        self.assertTrue(r and r.get("grokOnly"), "GROK ONLY no longer skips the sweep: %r" % r)

    def test_an_unreadable_switch_refuses_the_paid_sweep(self):
        r = self._ask('{"on": true, "mode": "on')          # half-written
        self.assertIsNotNone(r, "a half-written switch started a PAID Claude sweep (#97)")
        self.assertTrue(r.get("readerUnknown"), r)
        self.assertIn("UNKNOWN", r["why"])
        self.assertEqual(G5.switch_state(), "unreadable")
        self.assertEqual(G5.reader(), "claude", "PREMISE: reader() no longer maps an unreadable switch to claude")

    def test_an_env_override_is_a_choice_the_file_cannot_overrule(self):
        with mock.patch.dict(os.environ, {"TV_G5_GROK_EYES": "off"}):
            self.assertIsNone(self._ask('{"garbage'), "an env override was refused because the file is unreadable")


RED_PROOF = [
    {"why": "#97 - an unreadable switch reads as claude again and starts a paid sweep",
     "file": "tv/control_app.py",
     "find": "    if _sw == \"unreadable\":\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "#97 - an absent switch file is read as unreadable, so a PC that never chose can never sweep",
     "file": "tv/g5_grok_eyes.py",
     "find": "        if not os.path.exists(_STATE_FILE):\n            return \"absent\"\n",
     "replace": "",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
