# -*- coding: utf-8 -*-
"""V1 MERGE JOIN (V1a's frame verdict x V1b's quarantine) - A STORE THE DOOR QUARANTINED IS UNKNOWN TO THE VERDICT.

Two tracks of the V1 vault batch were each right on their own and wrong together:
  * V1a (REG-2401): a screenshot that read something records what it put in the vault, and one verdict
    (⟦INTAKE SEEN VERDICT⟧) asks whether that is still his: owned -> 'seen'; gone with no removal on record -> 'gone'
    (read again, so a silent loss heals); and "what is owned cannot be read -> 'unknown', skipped and SAID, never
    guessed". Its reader of owned (_intakeSeenAsk().held) knew one unreadable shape: `owned` not defined at all.
  * V1b (REG-2410): a d2r_owned or d2r_magicFinds that will not read is QUARANTINED at the door - its bytes kept aside -
    and the page runs on the store's DEFAULT in memory (an empty Set, an empty map), so it never bricks.
Merged, the verdict read that default as his vault: every recorded screenshot read 'gone' - the 12 s poll said "N read
items no longer in your vault, with no removal on record" and a manual Scan offered "♻ Read again N" - exactly while the
board says the store would not read. With only d2r_magicFinds quarantined the vault is not held, so a pick of that offer
paid for an AI read of screenshots whose items were never lost.

NOW held() answers UNKNOWN (null) for a store the door quarantined: d2r_owned quarantined -> every name is UNKNOWN;
d2r_magicFinds quarantined -> a name owned is still held, any other is UNKNOWN. The verdict then says 'unknown' (skipped),
never 'gone'. With nothing quarantined a name that left with no removal on record is still 'gone' (the premise case: the
verdict keeps healing a real silent loss).

WHAT IS DRIVEN: the store door window.LSR and the boot's shape readers (tv/store_door_harness.py: the bytes are
quarantined by the shipped _storeRead), and the whole ⟦INTAKE SEEN VERDICT⟧ block, cut from bible.html, in node. The
removal journal answers "no removal on record" (a stand-in: this law asks the held side, not the journal side).
RED_PROOF below. A missing node is the only skip; a node that fails is a failure.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import store_door_harness as D  # noqa: E402

VERDICT_BEGIN = "  /* ⟦INTAKE SEEN VERDICT BEGIN⟧"
VERDICT_END = "  /* ⟦INTAKE SEEN VERDICT END⟧ */"
SHOT = "f_1790549355102.jpg"


def _pieces(s):
    verdict = D.between(s, VERDICT_BEGIN, VERDICT_END)
    return (D.stage(s) + D.boot(s)
            + "window._removedAfter = function(){ return null; };   /* no removal on record */\n"
            + verdict + "\n")


def _run(seed, held):
    rec = {"held": held, "unr": [], "at": 1790549355102, "world": "main"}
    body = ("var seen = %s, F = { name: %s, lastModified: 1 };\n"
            "var ask = window._intakeSeenAsk(), v = window._intakeSeenVerdict(seen, F, ask);\n"
            "OUT.state = v.state; OUT.gone = v.gone || []; OUT.unknown = v.unknown || [];\n"
            "OUT.held = {}; %s.forEach(function(n){ OUT.held[n] = ask.held(n); });\n"
            "OUT.quarantined = window.LSR.quarantined().map(function(q){ return q.key; }).sort();\n"
            % (json.dumps({SHOT: rec}), json.dumps(SHOT), json.dumps(held)))
    return D.page(_pieces(D.src()), body, seed=seed)


@unittest.skipIf(D.NODE is None, "node is absent - this law runs the SHIPPED verdict; UNMEASURED, not passing")
class AFrameVerdictReadsAQuarantinedStoreAsUnknown(unittest.TestCase):

    def test_owned_that_will_not_read_makes_every_name_unknown_never_gone(self):
        o = _run({"d2r_owned": '["Grief","Death Lo', "d2r_magicFinds": "{}"}, ["Grief", "Death Loop"])
        self.assertEqual(o["quarantined"], ["d2r_owned"], "PREMISE: the door did not quarantine owned that will not parse")
        self.assertEqual(o["held"], {"Grief": None, "Death Loop": None},
                         "the verdict read the page's default owned as his vault: %r" % o["held"])
        self.assertEqual(o["state"], "unknown",
                         "a screenshot reads '%s' (gone %r) while owned would not read - the poll says his items left "
                         "the vault and a Scan offers to read it again" % (o["state"], o["gone"]))
        self.assertEqual(o["gone"], [])

    def test_magic_and_rare_that_will_not_read_leaves_owned_names_held_and_the_rest_unknown(self):
        o = _run({"d2r_owned": '["Shako"]', "d2r_magicFinds": '{"Sullied Grand Charm of Blight":{"q":"mag'},
                 ["Shako", "Sullied Grand Charm of Blight"])
        self.assertEqual(o["quarantined"], ["d2r_magicFinds"], "PREMISE: the door did not quarantine Magic & Rare")
        self.assertEqual(o["held"], {"Shako": True, "Sullied Grand Charm of Blight": None},
                         "the verdict read the default Magic & Rare map as his: %r" % o["held"])
        self.assertEqual(o["state"], "unknown", "a keeper of a quarantined Magic & Rare store reads '%s'" % o["state"])
        self.assertEqual(o["unknown"], ["Sullied Grand Charm of Blight"])

    def test_with_nothing_quarantined_a_silent_loss_is_still_gone(self):
        o = _run({"d2r_owned": '["Shako"]', "d2r_magicFinds": "{}"}, ["Shako", "Grief"])
        self.assertEqual(o["quarantined"], [])
        self.assertEqual(o["held"], {"Shako": True, "Grief": False})
        self.assertEqual(o["state"], "gone", "PREMISE: a name that left with no removal on record no longer reads 'gone' "
                                             "- the verdict stopped healing a silent loss")
        self.assertEqual(o["gone"], ["Grief"])


RED_PROOF = [
    {"why": "V1 merge join - a quarantined owned is read as his (empty) vault again: every screenshot reads 'gone'",
     "file": "bible.html", "matches": 1,
     "find": "        if (_qd('d2r_owned')) return null;\n",
     "replace": ""},
    {"why": "V1 merge join - a quarantined Magic & Rare store is read as an empty map: its keepers read 'gone'",
     "file": "bible.html", "matches": 1,
     "find": "        if (_qd('d2r_magicFinds')) return null;\n",
     "replace": ""},
    {"why": "V1 merge join - the verdict never asks the door which stores it quarantined",
     "file": "bible.html", "matches": 1,
     "find": "                                     return !!(e && e.kind === 'quarantine'); } catch (eQ) { return false; } };\n",
     "replace": "                                     return false; } catch (eQ) { return false; } };\n"},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
