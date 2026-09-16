# -*- coding: utf-8 -*-
"""NAMING A REEL MUST NOT PUT IT BACK PAST ITS OWN SEAL — THIS BURNED A CORE FOR 2h46m.

⚠⚠ THE REEL IDS BELOW ARE SYNTHETIC (epoch 1500000000000 = 2017, a stamp no recording can
carry). THE REAL IDS ARE IN BUGS.md, DELIBERATELY NOT IN THIS FILE. `frame_authority.
test_referenced_reels()` scans test files for reel ids and retention then holds anything it finds
as "the TEST SUITE opens this reel by name" — forever. Writing his real ids here made 4 of his
reels permanently undeletable the moment this gate was saved, which is precisely the opposite of
the river rule it was written to defend. That file already records the same mistake at v2071
(3.15 GB held for a false reason) AND prescribes this remedy; I wrote the gate without reading
it. [[carved-skill-unloaded-is-unapplied]] [[feedback-fixtures-never-touch-live-data]]

`_vault_sweep_run` filters out every reel whose seal is still valid, then honoured `reel_dir`
with:

    dirs = [d for d in dirs if basename(d) == want] or ([reel_dir] if isdir(reel_dir) else [])

The `or` fires **precisely when the seal removed the reel** — so a TARGETED sweep ignored a seal
that an untargeted one obeys. The autoread watchdog aims at a reel every tick (v2225 made it aim
on purpose), so every tick re-read a finished reel, found the same nothing, re-sealed it with the
SAME promptVer, and retention owed it again on the next pass.

MEASURED 2026-09-16 on his live console: **3,052 re-sweeps of one reel**
(reel_s_1500000000001_12001), 388 of the next, 1,748 retention passes inside 20k lines of log,
and the process pegged at **104% CPU for 2h46m**. Nearly all of it was 0 paid reads, so it burned
the machine rather than his subscription — which is exactly why no cost alarm ever fired. What he
saw was the sweep panel forever mid-read on something weeks old, and he asked about it.

⚠ AND THE LOG NAMED THE WRONG CAUSE. It printed *"sealed with no rows by an OLDER vault reader
(now vp2017)"* while the seal on disk said promptVer **vp2017** — the current one — so
`_vault_still_sealed` returned True for it. Anyone reading that line hunts a stale prompt version
that does not exist. The message is pinned below too. [[label-outlived-referent]]

⚠ WHY THIS GATE CALLS A FUNCTION INSTEAD OF GREPPING. The decision was inline in a 1,070-line
thread body with no return value, so nothing could reach it. v3225 lifted it into
`_sweep_pick_named`, which is pure. A gate that greps for the absence of `or [reel_dir]` passes
the moment someone rewrites the line while keeping the behaviour — it pins spelling, not law.
[[source-reading-guard]] [[regression-guard]]
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

import control_app as CA


SEALED_NOW = {"promptVer": "vp2017", "rows": 0, "ts": 1}     # current reader, found nothing
SEALED_OLD = {"promptVer": "vp0001", "rows": 0, "ts": 1}     # an older eye — reopening is right
PRODUCTIVE = {"promptVer": "vp2017", "rows": 12, "ts": 1}    # sealed AND it found things


def _still(rec, prompt_ver=None):
    """Stand-in for _vault_still_sealed: a seal holds unless an older reader made it barren."""
    if not rec:
        return False
    return bool(rec.get("rows")) or rec.get("promptVer") == "vp2017"


class TestANamedReelDoesNotDefeatItsSeal(unittest.TestCase):

    def setUp(self):
        self.tmp = os.path.join(HERE, ".t_seal_reel")
        if not os.path.isdir(self.tmp):
            os.makedirs(self.tmp)
        self.reel = os.path.join(self.tmp, "reel_s_1500000000001_12001")
        if not os.path.isdir(self.reel):
            os.makedirs(self.reel)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _pick(self, dirs, rec, force=False):
        return CA._sweep_pick_named(dirs, self.reel, force, lambda d: rec, still_sealed=_still)

    # ── THE LAW ──────────────────────────────────────────────────────────────────────────────
    def test_a_valid_seal_survives_being_named(self):
        """THE DEFECT EXACTLY: dirs is empty because the seal removed it. Naming must not undo that."""
        picked, refusal = self._pick([], SEALED_NOW)
        self.assertEqual(
            picked, [],
            "a reel sealed by the CURRENT reader was swept anyway because the caller named it — "
            "this is the 3,052-re-sweep loop that pinned a core at 104%% for 2h46m")
        self.assertIsNotNone(refusal, "it declined but said nothing — a silent skip is unreadable")
        self.assertTrue(refusal.get("alreadySealed"),
                        "the refusal must carry a FLAG, not only prose: v2225 records a watchdog "
                        "that keyed on `'unavailable' in why` and so could not tell a permanent "
                        "refusal from a transient one. Got: %r" % (refusal,))
        self.assertIn("vp2017", refusal.get("sealedBy", ""),
                      "the refusal must name WHICH reader sealed it, or the next reader repeats "
                      "my mistake of hunting a stale promptVer that does not exist")

    def test_a_productive_seal_also_survives(self):
        """A seal with rows is the strongest kind — re-reading it can only duplicate work."""
        picked, refusal = self._pick([], PRODUCTIVE)
        self.assertEqual(picked, [], "a reel sealed WITH 12 rows was re-read on being named")
        self.assertTrue(refusal.get("alreadySealed"))
        self.assertIn("12 row", refusal.get("why", ""),
                      "the refusal should say how much the seal already banked, so a human can "
                      "tell 'done and empty' from 'done and full'")

    # ── AND THE THREE WAYS IT MUST STILL SAY YES, or the fix is just a mute button ───────────
    def test_an_unsealed_named_reel_is_still_swept(self):
        picked, refusal = self._pick([], None)
        self.assertEqual(picked, [self.reel],
                         "a reel with NO seal was refused — the fix has broken the feature it "
                         "was meant to protect (v2225: sweep the reel the caller named)")
        self.assertIsNone(refusal)

    def test_an_older_readers_barren_seal_reopens(self):
        """v2002's law: a seal is not a life sentence once the vault prompt improves."""
        picked, refusal = self._pick([], SEALED_OLD)
        self.assertEqual(picked, [self.reel],
                         "a rows==0 seal from an OLDER reader must reopen — otherwise a prompt "
                         "improvement can never reach the reels it was written for")
        self.assertIsNone(refusal)

    def test_force_overrules_a_valid_seal(self):
        picked, refusal = self._pick([], SEALED_NOW, force=True)
        self.assertEqual(picked, [self.reel],
                         "force must still overrule the seal — a human overriding on purpose is "
                         "not the loop this gate exists to stop")
        self.assertIsNone(refusal)

    def test_a_reel_present_in_the_list_is_taken_unchanged(self):
        """The ordinary path: the seal never removed it, so naming just narrows the list."""
        other = os.path.join(self.tmp, "reel_other")
        picked, refusal = self._pick([other, self.reel], SEALED_NOW)
        self.assertEqual(picked, [self.reel],
                         "naming a reel that IS eligible must select exactly it")
        self.assertIsNone(refusal)

    def test_a_reel_that_is_not_a_directory_is_named_as_unknown(self):
        """UNKNOWN is a first-class answer — it must not silently become 'nothing to do'."""
        picked, refusal = CA._sweep_pick_named([], os.path.join(self.tmp, "reel_ghost"),
                                               False, lambda d: None, still_sealed=_still)
        self.assertEqual(picked, [])
        self.assertTrue(refusal.get("unknownReel"),
                        "a reel path that does not exist must say so, not read as a valid "
                        "empty sweep [[unknown-stays-unknown]]")

    # ── THE MESSAGE THAT LIED ────────────────────────────────────────────────────────────────
    def test_the_reopen_line_cannot_claim_an_older_reader_for_a_current_seal(self):
        """It printed 'sealed by an OLDER vault reader (now vp2017)' about a vp2017 seal."""
        import io
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as _f:
            src = _f.read()
        needle = '_reopened = [os.path.basename(d) for d in dirs'
        i = src.find(needle)
        self.assertNotEqual(i, -1, "the reopen tally moved — re-anchor this gate")
        j = src.find("if _reopened:", i)
        self.assertNotEqual(j, -1, "could not find the end of the reopen tally [[source-reading-guard]]")
        blk = src[i:j]
        self.assertEqual(src.count(needle), 1,
                         "anchor matched %d times, so this gate is measuring an unknown one of "
                         "them [[sabotage-is-usually-the-wrong-one]]" % src.count(needle))
        self.assertIn(
            "not _vault_still_sealed", blk,
            "the 'reopened by an older reader' list must be filtered to reels whose seal has "
            "ACTUALLY lapsed. Unfiltered, it printed that sentence about seals written by the "
            "current reader — the false message that sent me hunting a stale promptVer. "
            "Block read:\n%s" % blk)


if __name__ == "__main__":
    unittest.main(verbosity=2)
