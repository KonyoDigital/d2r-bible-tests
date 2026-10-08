# -*- coding: utf-8 -*-
"""#289 (REG-2063) - THE RIVER'S STAMP LOG AND RETENTION'S TOMBSTONE LEDGER NEVER SHARE ONE NAME ON ONE SCREEN.

GrokBot ticks 419-422 on #230: the River header read "there is no tombstone ledger on this venue - retention has no record
here" while the TOMBSTONE chip beside it said "In the river LEDGER, 11 carry TOMBSTONE as their most recent stamp", and he
was asked which one is true. Both were: the header is river_mouth() on retention's DELETION record (reel_tombstones.json,
runtime state, absent on that PC), the chip counts the river's own STAMP LOG. Two records, both called "the ledger".

  * the chip names its record as the river's own stamp log and says it is not retention's tombstone ledger;
  * the backend sentence is left alone: three laws and a predicate key on its "no tombstone ledger" phrase.
Pure text over the shipped control_ui.html (the sentence is assembled inline in the chip's tip builder).
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")
CHIP = "say += '. In the river\\u2019s own stamp log (not retention\\u2019s tombstone ledger), ' + rHere + ' carry ' + lab"


class TwoTombstoneRecordsNeverShareOneName(unittest.TestCase):

    def test_the_chip_names_the_stamp_log(self):
        with open(UI, encoding="utf-8") as f:
            s = f.read()
        self.assertEqual(s.count(CHIP), 1, "the TOMBSTONE chip no longer names its record as the river's stamp log")
        self.assertEqual(s.count("'. In the river LEDGER, '"), 0, "the chip calls the stamp log 'the river LEDGER' again")


RED_PROOF = [
    {"why": "REG-2063 - the chip calls the river's stamp log 'the river LEDGER' again, beside a header about retention's ledger",
     "file": "control_ui.html",
     "find": "say += '. In the river\\u2019s own stamp log (not retention\\u2019s tombstone ledger), ' + rHere",
     "replace": "say += '. In the river LEDGER, ' + rHere",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
