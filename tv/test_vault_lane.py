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


def _missing_fixture_reels():
    """Which reels the SCENARIOS need that are not on disk. -> sorted list

    ⚠ v2229 — THIS PRECONDITION USED TO CHECK ONE REEL AND SPEAK FOR ALL OF THEM. It tested only
    reel_s_1786998496819_31092, so when the prune deleted reel_s_1786998671206_32230 and
    reel_s_1786998775577_33262 on 2026-08-28 this class still RAN and five cases failed with
    "Harlequin Crest not found in []" — a message that says nothing about the actual cause, which
    was that the footage underneath had been deleted an hour earlier.

    A sentinel that samples one of N is a sample, not a precondition. Ask vault_simulate what its
    scenarios actually open and name every absentee, so the skip reason IS the diagnosis.
    [[feedback-blind-fixture-green-gate]] [[regression-guard]]"""
    try:
        import vault_simulate as vs
    except Exception:
        return []                                  # cannot ask -> let the cases run and speak
    want = set()
    for scn in getattr(vs, "SCENARIOS", []):
        for r in (scn.get("reels") or []):
            want.add(str(r))
    hist = os.path.join(HERE, "frames", "hist")
    return sorted(r for r in want if not os.path.isdir(os.path.join(hist, r)))


def _has_reels():
    hist = os.path.join(HERE, "frames", "hist")
    if not os.path.isdir(hist):
        return False
    return not _missing_fixture_reels()


@unittest.skipUnless(_has_reels(),
                     "the scenario footage is not on this machine — missing: %s"
                     % (", ".join(_missing_fixture_reels()) or "frames/hist"))
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

    def test_enough_recordings_ground_it(self):
        p = self._run("enough-recordings")
        self.assertIn("Harlequin Crest", self._names(p, "owned"))
        self.assertEqual(self._names(p, "throwOut"), [])

    def test_junk_in_one_recording_suggests_NOTHING(self):
        p = self._run("junk-one-recording")
        self.assertEqual(self._names(p, "throwOut"), [],
                         "it offered to bin an item on a single recording — there is no un-throw")
        whys = " ".join(str(h.get("why") or "") for h in (p.get("held") or []))
        # derived, not pinned: the message quotes THROWOUT_MIN_WITNESSES, which moved with his
        # 3-read ruling. "needs 3" was true until it was not, and nothing said so.
        import vault_retro as _vr
        self.assertIn("needs %d" % _vr.THROWOUT_MIN_WITNESSES, whys)

    def test_junk_at_the_throw_bar_is_a_SUGGESTION_never_automatic(self):
        p = self._run("junk-at-the-throw-bar")
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


@unittest.skipUnless(_has_reels(),
                     "the scenario footage is not on this machine — missing: %s"
                     % (", ".join(_missing_fixture_reels()) or "frames/hist"))
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


class TestV1999TheLawHasACallerAtLast(unittest.TestCase):
    """v1999 — lane_lock.py declares "AT MOST ONE LANE IS EVER UNLOCKED" and had ZERO production
    callers. Only tests imported it. A module that documents a law and enforces nothing is the
    muleById defect at module scale.

    WHY IT COULD NOT JOIN THE VAULT SWEEP, so nobody tries: VAULT_READ_PROMPT never asks for
    chronicleTab, so lane_for() on that path can only ever answer "vault" — a gate that can never
    refuse. The signal exists on the CHRONICLE path, where READ_PROMPT asks for stashTab AND
    chronicleTab on every frame (tv_diablo.py:264).

    AND THE VOCABULARY WAS BLIND TO ITS OWN INPUT. VAULT_SURFACES listed
    stash/inventory/equipment/runes/gems/materials while `stashTab` carries the RotW LEFT TABS —
    "Personal·Shared·Gems·Materials·Runes". Three overlapped by luck; `personal` and `shared`, the
    two he is in most often, did not. Measured before the fix:
        chronicle_kind({scene:'chronicle', chronicleTab:'uniques', stashTab:'personal'})
          -> 'chronicle-uniques'      (should be None — the frame claims both)
    [[gate-blind-to-unexercised-input]]
    """

    def test_a_frame_claiming_BOTH_is_refused_for_every_real_stash_tab(self):
        import chronicle_retro as cr
        for tab in ("personal", "shared", "gems", "materials", "runes"):
            self.assertIsNone(
                cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "uniques", "stashTab": tab}),
                "a frame claiming the chronicle AND the %s stash tab was read as a chronicle page — "
                "the cost is not symmetrical: it ticks a grail row he never earned" % tab)

    def test_a_clean_chronicle_page_still_reads(self):
        """The lock must cost one ambiguous page, not every page."""
        import chronicle_retro as cr
        self.assertEqual(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "uniques"}),
                         "chronicle-uniques")
        self.assertEqual(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "sets"}),
                         "chronicle-sets")
        # an EMPTY stashTab is not a claim
        self.assertEqual(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "uniques",
                                            "stashTab": ""}), "chronicle-uniques")

    def test_personal_and_shared_fold_to_stash_rather_than_minting_a_new_lane(self):
        """`surface` is compared against vault_retro.LANES; a lane named "personal" is a value no
        consumer knows. Recognise the input, keep the output vocabulary."""
        import lane_lock as L
        import vault_retro as vr
        for tab in ("personal", "shared"):
            v = L.lane_for({"scene": "stash", "stashTab": tab})
            self.assertEqual(v["lane"], L.VAULT)
            self.assertEqual(v["surface"], "stash",
                             "%s must fold to a lane vault_retro recognises" % tab)
            self.assertIn(v["surface"], vr.LANES)

    def test_the_join_is_real_and_not_a_comment(self):
        """The whole point of this version. A law with no caller is prose."""
        import chronicle_retro as cr
        with open(cr.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("import lane_lock", src,
                      "chronicle_retro no longer consults the lane lock — it is prose again")

    def test_a_missing_lane_lock_reads_as_before_rather_than_refusing_everything(self):
        """An unavailable law is not a violated one. If the module vanished, the sweep must keep
        working exactly as it did before it existed — never refuse every page."""
        import sys
        import chronicle_retro as cr
        saved = sys.modules.get("lane_lock")
        sys.modules["lane_lock"] = None      # import lane_lock -> ImportError
        try:
            self.assertEqual(cr.chronicle_kind({"scene": "chronicle", "chronicleTab": "uniques"}),
                             "chronicle-uniques")
        finally:
            if saved is not None:
                sys.modules["lane_lock"] = saved
            else:
                sys.modules.pop("lane_lock", None)


if __name__ == "__main__":
    unittest.main(verbosity=1)
