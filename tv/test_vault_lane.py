"""The vault lane's decisions, and the ONE KEY that decides which lane may write at all.

Konyo: "make sure its not discading anything it shouldnt. and make sure its muling anything it is",
and: "something should switch on and off some sort of engine or key like that unlocks or locks".

Every scenario here runs the REAL vault_retro over his REAL reels — real frame names, real timestamps,
real still-run grouping — with only the READER's answer injected, because that is the one thing the
archive does not contain (0 of 17 reels declare an ownership surface, REG-185). So these exercise the
actual grouping, gate and merge rather than a mock of them.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _has_reels():
    return os.path.isdir(os.path.join(HERE, "frames", "hist", "reel_s_1786998496819_31092"))


@unittest.skipUnless(_has_reels(), "his sealed reels are not in this checkout")
class TestVaultDecisions(unittest.TestCase):
    """SEEING SOMETHING MORE OFTEN NEVER MEANS THROW IT AWAY. Repetition decides whether he OWNS it;
    only the reader's own junk flag can even propose a discard, and then only across three separate
    recordings. That asymmetry is deliberate: a missed keep costs one more look at the stash, a wrong
    throw costs an item that does not come back."""

    def _run(self, sid):
        import vault_simulate as vs
        scn = [s for s in vs.SCENARIOS if s["id"] == sid][0]
        return vs.run(vs.build(scn))

    def _names(self, prop, bucket):
        return sorted({r.get("name") for r in (prop.get(bucket) or []) if r.get("name")})

    def test_one_look_is_never_owned(self):
        p = self._run("seen-once")
        self.assertNotIn("Harlequin Crest", self._names(p, "owned"))
        self.assertIn("Harlequin Crest", self._names(p, "unsure"))

    def test_two_recordings_ground_it(self):
        p = self._run("two-recordings")
        self.assertIn("Harlequin Crest", self._names(p, "owned"))
        self.assertEqual(self._names(p, "throwOut"), [])

    def test_junk_in_one_recording_suggests_NOTHING(self):
        p = self._run("junk-one-recording")
        self.assertEqual(self._names(p, "throwOut"), [],
                         "it offered to bin an item on a single recording — there is no un-throw")
        whys = " ".join(str(h.get("why") or "") for h in (p.get("held") or []))
        self.assertIn("needs 3", whys)

    def test_junk_in_three_recordings_is_a_SUGGESTION_never_automatic(self):
        p = self._run("junk-three-recordings")
        self.assertIn("Cracked Sash", self._names(p, "throwOut"))
        for r in p.get("throwOut") or []:
            self.assertTrue(r.get("suggestion"), "a throw-out was not flagged as a suggestion")

    def test_REPETITION_IS_NOT_A_DISCARD(self):
        """The rule he asked about, in one assertion: the same good item in three recordings is
        MORE owned, never closer to being binned."""
        p = self._run("repetition-is-not-a-discard")
        self.assertIn("Harlequin Crest", self._names(p, "owned"))
        self.assertEqual(self._names(p, "throwOut"), [],
                         "seeing a Shako three times proposed throwing it away")

    def test_a_later_read_can_never_lower_a_count(self):
        p = self._run("merge-max")
        ral = [r for r in (p.get("owned") or []) if r["name"] == "Ral"]
        self.assertTrue(ral, "Ral did not ground at all")
        self.assertEqual(ral[0].get("count"), 5,
                         "a later read of 2 lowered the earlier 5 — an obstructed panel is not "
                         "evidence he threw something away")


class TestLaneLock(unittest.TestCase):
    """AT MOST ONE LANE IS EVER UNLOCKED — his two scenarios, plus the cases that must lock.

    Measured on his own frames before this was trusted: the pixel-level classify_stash_grid calls a
    real CHRONICLE page "stash" and _panel_open_from_features agrees it is an open panel. Only the AI
    classifier gets it right. So a cheap pixel gate cannot decide this, which is why the decision
    lives in one audited place instead of being re-derived per lane.
    """

    def _lane(self, **kw):
        import lane_lock as L
        base = {"scene": "", "stashTab": "", "chronicleTab": ""}
        base.update(kw)
        return L.lane_for(base)

    def test_stash_open_unlocks_the_vault_and_locks_the_chronicle(self):
        v = self._lane(scene="stash", stashTab="personal")
        self.assertEqual(v["lane"], "vault")
        self.assertEqual(v["surface"], "stash")
        self.assertIsNone(v["ledger"])

    def test_the_chronicle_tab_he_clicked_is_the_only_ledger_unlocked(self):
        for tab in ("uniques", "sets", "runewords"):
            v = self._lane(scene="chronicle", chronicleTab=tab)
            self.assertEqual(v["lane"], "chronicle", tab)
            self.assertEqual(v["ledger"], tab)
            self.assertIsNone(v["surface"], "the vault was left unlocked on a chronicle page")

    def test_gameplay_unlocks_nothing(self):
        self.assertIsNone(self._lane(scene="gameplay", area="Nihlathak's Temple")["lane"])

    def test_a_frame_claiming_BOTH_unlocks_nothing(self):
        """The asymmetry that makes locking correct: a Chronicle row filed as OWNERSHIP claims he owns
        an item he merely saw listed, and a stash item filed as a chronicle FIND ticks a grail row he
        never earned. Locking costs one unread page."""
        v = self._lane(scene="stash", stashTab="personal", chronicleTab="uniques")
        self.assertIsNone(v["lane"])
        self.assertIn("AMBIGUOUS", v["why"])

    def test_may_write_refuses_the_wrong_ledger(self):
        import lane_lock as L
        frame = {"scene": "chronicle", "stashTab": "", "chronicleTab": "uniques"}
        ok, why = L.may_write(frame, "chronicle", ledger="sets")
        self.assertFalse(ok, "a SETS write was allowed on the uniques tab")
        self.assertIn("uniques", why)
        ok, _ = L.may_write(frame, "chronicle", ledger="uniques")
        self.assertTrue(ok)
        ok, why = L.may_write(frame, "vault")
        self.assertFalse(ok, "the vault was allowed to write from a chronicle page")

    def test_the_runewords_tab_is_dark_end_to_end_and_that_is_recorded(self):
        """lane_lock CAN unlock runewords, and nothing upstream can ever produce it: the classifier
        prompt names only uniques and sets, _norm_chron_tab hard-rejects 'runewords', and
        chronicle_kind maps only the two. Asserted so the gap is a KNOWN dark path rather than a
        surprise the day someone wires the third ledger."""
        import tv_diablo as tv
        import chronicle_retro as cr
        self.assertEqual(tv._norm_chron_tab("runewords", "chronicle"), "",
                         "the parser now accepts runewords — update chronicle_kind and this test")
        self.assertIsNone(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "runewords"}))


@unittest.skipUnless(_has_reels(), "his sealed reels are not in this checkout")
class TestTheSimulatorCanActuallyBeRUN(unittest.TestCase):
    """v1904 — `python3 tv/vault_simulate.py` PRINTED NOTHING AND EXITED 0.

    The module's own docstring promises: "this prints the whole decision for a scenario in the words
    the Vault manager would use, so a wrong rule is visible rather than merely unasserted." It had no
    `__main__` at all. The scenarios were reachable only by importing it from this file — so the
    demonstration he asked for existed as code and could not be watched.

    A quiet exit 0 is the worst possible answer here: it is indistinguishable from a clean run.
    [[the-unjoined-end]] [[feedback-quiet-workflow-is-not-finished]]"""

    def _run(self, *args):
        import subprocess
        return subprocess.run([sys.executable, os.path.join(HERE, "vault_simulate.py")] + list(args),
                              capture_output=True, text=True, timeout=600)

    def test_it_prints_every_scenario_and_exits_clean(self):
        import vault_simulate as vs
        out = self._run()
        self.assertEqual(out.returncode, 0, out.stdout[-600:] + out.stderr[-600:])
        for scn in vs.SCENARIOS:
            self.assertIn(scn["id"], out.stdout, "the transcript skipped %r" % scn["id"])
            self.assertIn(scn["expect"], out.stdout,
                          "the transcript does not say what %r expects" % scn["id"])
        self.assertNotIn("NO FRAMES", out.stdout,
                         "a scenario exercised nothing and would have scrolled past as a pass")

    def test_the_merge_max_transcript_SHOWS_THE_COUNT(self):
        """Its whole claim is "count stays 5" — and the OWN line printed conf and witnesses only,
        so the one number under discussion was invisible. A demonstration that omits the quantity
        it is about proves nothing to the person reading it."""
        out = self._run("merge-max")
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        line = [l for l in out.stdout.split("\n") if "OWN" in l and "Ral" in l]
        self.assertTrue(line, "no OWN row for Ral: %s" % out.stdout[-400:])
        self.assertIn("x5", line[0],
                      "the count the scenario is about is not in its own transcript: %r" % line[0])

    def test_an_unknown_scenario_name_is_refused_not_ignored(self):
        out = self._run("no-such-scenario")
        self.assertEqual(out.returncode, 2)
        self.assertIn("known:", out.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
