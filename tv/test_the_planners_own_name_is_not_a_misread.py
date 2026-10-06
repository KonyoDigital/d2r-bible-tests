# -*- coding: utf-8 -*-
"""REG-1913 - THE PLANNER'S OWN NAME IS NOT A MISREAD. Driven on the SHIPPED board.

GrokBot (#230, the v3600 brief, C11): "+ Add an item" -> Harlequin Crest gave the routing row "read as 'Harlequin Crest
(Shako)', filed as a misread of Harlequin Crest" - the planner's own display name (item, then base in brackets) called a
bad read. The law asks window.suggestMule on the real page: the planner form says the planner named it and never says
misread; a genuinely repaired read still says misread (the positive control - a door that stopped saying it at all
would pass the first case). NO CHROME AT ALL = a declared skip, never a pass.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def why(name):
    return board().run("var r = window.suggestMule(%s); OUT.why = (r && r.why) || ''; OUT.id = r && r.id;"
                       % __import__("json").dumps(name))


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class ThePlannersOwnNameIsNotAMisread(unittest.TestCase):

    def test_the_planner_form_is_named_as_the_planners(self):
        o = why("Harlequin Crest (Shako)")
        self.assertIn("the planner names it", o["why"], o)
        self.assertNotIn("misread", o["why"], "his own pick from the planner list was called a misread (REG-1913): %s" % o)

    def test_a_repaired_read_is_still_called_a_misread(self):
        o = why("Harlequinn Crest")
        if "filed as" not in o["why"]:
            self.skipTest("the fold did not repair this spelling on this build - the control reached nothing (%s)" % o)
        self.assertIn("misread", o["why"], o)


RED_PROOF = [
    {
        "why": "REG-1913 - the planner's own 'Name (Base)' is called a misread of Name again",
        "file": "bible.html",
        "find": "              var _plannerName = !!(_pm && String(_pm[1]).trim() === String(_fc));\n",
        "replace": "              var _plannerName = false;\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
