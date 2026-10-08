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

    def _may_with(self, census):
        import json as _json
        p = os.path.join(tempfile.mkdtemp(prefix="stalecensus_"), ".heart2.json")
        with open(p, "w") as f:
            _json.dump(census, f)
        with mock.patch.dict(os.environ, {"TV_HEART_CENSUS": p}):
            # frame.release - an act with no undo, so it waits on a stale census (an ordinary act refuses on merit, v3042)
            return SA.may("frame.release")

    def test_a_stale_proof_census_names_the_proof_not_the_heart_panel(self):
        """REG-2073 (#284, GrokBot tick 422 K17) - REG-2017 named the MISSING branch; the STALE branches three lines below
        still said 'the heart census is STALE' beside a Heart panel reading 'census taken 14 s ago'."""
        for census, what in (({"partial": True, "sliceOwed": 3, "blind": []}, "still being proven"),
                             ({"gatesFingerprint": "0000dead", "blind": []}, "the gate files have changed")):
            ok, why = self._may_with(census)
            self.assertFalse(ok, "a lock opened on a stale proof census (%s)" % what)
            self.assertIn(what, why, "premise: the %r branch answered: %r" % (what, why))
            self.assertIn("PROOF census is STALE (not the Heart panel's live census)", why,
                          "a stale lock does not tell its census from the Heart panel's (%s): %r" % (what, why))
            self.assertIn(SA._HEART_STALE_PHRASE, why, "the phrase its readers match on is gone: %r" % why)


RED_PROOF = [
    {"why": "REG-2073 - a lock shut on a census still being proven calls it 'the heart census' again",
     "file": "tv/self_arming.py",
     "find": '            return False, ("the heart2 PROOF census is STALE (not the Heart panel\'s live census): it is still being proven "\n',
     "replace": '            return False, ("the heart census is STALE: it is still being proven "\n',
     "matches": 1},
    {"why": "REG-2017 - the lock says 'the heart has never run here' again, beside a Heart panel showing a fresh census",
     "file": "tv/self_arming.py",
     "find": '        return False, ("this PC\'s gates have never been PROVEN here (no heart2 proof census - not the Heart panel\'s live "\n',
     "replace": '        return False, ("the heart has never run here (no heart2 proof census - "\n',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
