# -*- coding: utf-8 -*-
"""REG-1275 (#165) — A FRESH INSTALL IS NOT A LOST STORE.

The loss detector (v2988) calls an empty ledger a LOSS when one of three one-time keys already exists - its own
comment promised "a fresh install is unaffected, by construction". But the SAME boot writes all three first
(d2r_installIdCache, d2r_chronSyncMerged_v1, d2r_pieceAlias_v2). MEASURED in a fresh profile: the very first load
recorded d2r_storeEmptied, the seed floor refused, and kept refusing on every later load - a brand-new board stayed
at 0 found for ever, with a false 'store lost its contents' on the record. It is the root of v659's and v1560's
Routine I reds. Fixed by reading "has this board run before" FIRST, before this boot writes anything.

  · COMPILER-ORDER (the property is WHERE the reading happens): the snapshot is taken in bible.html before every one
    of the three writes, and the detector reads the snapshot, not the keys.
  · The behaviour (fresh install floors; a store that ran and then emptied is still caught) is driven in a real
    browser by tests/v3503_a_fresh_install_is_not_a_lost_store.spec.ts on CI.
RED_PROOF below.
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _code():
    with io.open(BIBLE, encoding="utf-8") as f:
        src = f.read()
    # strip /* ... */ comments (bounded) so prose quoting a key cannot stand in for the code
    return re.sub(r"/\*.{0,4000}?\*/", " ", src, flags=re.S)


class AFreshInstallIsNotALostStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.code = _code()

    def test_the_snapshot_is_taken_before_every_write(self):
        snap = self.code.find("window.__d2rHadRunAtBoot = !!(")
        self.assertGreater(snap, -1, "no boot-time snapshot of 'has this board run before'")
        for key in ("d2r_installIdCache", "d2r_chronSyncMerged_v1", "d2r_pieceAlias_v2"):
            writes = [m.start() for m in re.finditer(r"setItem\(\s*'%s'" % key, self.code)]
            self.assertTrue(writes, "premise: this boot writes %s" % key)
            self.assertLess(snap, min(writes), "%s is written BEFORE the snapshot - a fresh install reads its own first "
                            "boot as history and is filed as a lost store" % key)

    def test_the_detector_reads_the_snapshot(self):
        i = self.code.find("var _hadRun =")
        self.assertGreater(i, -1, "premise: the loss detector's _hadRun")
        self.assertIn("window.__d2rHadRunAtBoot", self.code[i:i + 300],
                      "the detector re-reads the keys this boot already wrote")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1275 - the detector re-reads the keys this boot wrote: every fresh install is a 'lost store' again",
        "file": "bible.html",
        "find": "      var _hadRun = (typeof window.__d2rHadRunAtBoot === 'boolean') ? window.__d2rHadRunAtBoot\n",
        "replace": "      var _hadRun = (false) ? window.__HAD\n",
        "matches": 1,
    },
]
