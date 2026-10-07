# -*- coding: utf-8 -*-
"""REG-2017 (#260) - A LOCK SHUT FOR WANT OF A PROOF SAYS WHICH CENSUS IT MEANS.

GrokBot, tick 405 (2026-10-07): its fleet tip read "reel.route is LOCKED - the heart has never run here" seconds after its
own Heart panel showed "census taken 15 s ago" on the same console. Both were true about different instruments: the lock
reads heart2 --prove's PROOF census (.heart2.json); the Heart panel shows its live corroborator walk. Driven: the real
self_arming.may() with no proof census on disk names the proof and says it is not the Heart panel's census.
"""
import os
import sys
import tempfile
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import self_arming as SA  # noqa: E402


class TheProverCensusIsNamedApartFromTheHearts(unittest.TestCase):

    def test_a_missing_proof_census_names_the_proof_not_the_heart_panel(self):
        absent = os.path.join(tempfile.mkdtemp(prefix="nocensus_"), ".heart2.json")
        with mock.patch.dict(os.environ, {"TV_HEART_CENSUS": absent}):
            ok, why = SA.may("reel.route")
        self.assertFalse(ok, "a lock opened with no proof census on disk")
        self.assertIn("never been PROVEN", why, "the lock does not say it is the PROOF that never ran (REG-2017)")
        self.assertIn("not the Heart panel's live census", why, "the lock does not tell its census from the Heart panel's")
        self.assertNotIn("the heart has never run here", why, "the old two-instruments-one-word sentence is back")


RED_PROOF = [
    {"why": "REG-2017 - the lock says 'the heart has never run here' again, beside a Heart panel showing a fresh census",
     "file": "tv/self_arming.py",
     "find": '        return False, ("this PC\'s gates have never been PROVEN here (no heart2 proof census - not the Heart panel\'s live "\n',
     "replace": '        return False, ("the heart has never run here (no heart2 proof census - "\n',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
