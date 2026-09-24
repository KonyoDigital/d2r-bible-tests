# -*- coding: utf-8 -*-
"""#229 — A DOCTOR PASS SAYS WHICH CHECK IT IS IN.

MEASURED 2026-09-24 on his Windows ALT: the eagle's first pass read "not measured yet" for 14+ minutes
after boot, while the same checks finished standalone in 229 s (cheap) + 143 s (periodic). The stall was
inside the console process only, and nothing could name the check it sat in: a pass that never ends could
only say it had not ended. console_doctor.run() now records the running check (CURRENT) and the console's
eagle_state() publishes it with its age under `measuring`.

  · DRIVEN: a check that looks at the doctor and at eagle_state() FROM INSIDE ITSELF sees its own name;
    after the pass both are clear again (a finished pass is never "measuring").
RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402
import control_app as ca  # noqa: E402


class APassSaysWhichCheckItIsIn(unittest.TestCase):

    def setUp(self):
        self._checks = cd.CHECKS[:]
        self.seen = {}

        def probe():
            self.seen["doctor"] = cd.CURRENT.get("check")
            self.seen["console"] = (ca.eagle_state().get("measuring") or {}).get("check")
            return cd.OK, "probe"
        cd.CHECKS[:] = [("the probe that looks at itself", probe)]

    def tearDown(self):
        cd.CHECKS[:] = self._checks
        cd.CURRENT.update(check=None, since=None, tick=None)

    def test_the_running_check_is_named_while_it_runs(self):
        cd.run(include_slow=False, include_periodic=False, tick=7)
        self.assertEqual(self.seen.get("doctor"), "the probe that looks at itself",
                         "the doctor does not record the check it is running")
        self.assertEqual(self.seen.get("console"), "the probe that looks at itself",
                         "the console does not publish the check the pass sits in")

    def test_a_finished_pass_is_not_measuring(self):
        cd.run(include_slow=False, include_periodic=False, tick=7)
        self.assertIsNone(cd.CURRENT.get("check"))
        self.assertNotIn("measuring", ca.eagle_state())


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#229 - the doctor stops recording the running check: a stalled pass says only 'not measured yet' again",
        "file": "console_doctor.py",
        "find": "            CURRENT.update(check=name, since=t0, tick=tick)\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#229 - the console stops publishing the check a pass sits in (his ALT: 14 minutes of 'not measured yet')",
        "file": "control_app.py",
        "find": "        if cur.get(\"check\") and cur.get(\"since\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "#229 - a finished pass keeps saying it is measuring",
        "file": "console_doctor.py",
        "find": "    CURRENT.update(check=None, since=None, tick=None)     # the pass is over: nothing is running\n",
        "replace": "",
        "matches": 1,
    },
]
