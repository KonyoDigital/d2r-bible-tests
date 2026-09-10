"""⚠⚠ A TOTAL IS ONLY AS KNOWN AS ITS LEAST-KNOWN PART.

`_retention_once()` publishes how many reels await a sweep. That number is the SUM of two lanes:
the chronicle reader and the vault. When the tag->lane map cannot be read the vault half is
unknowable — and v2880 said so on `lockedVault`, with the note "a zero here renders as 'nothing
awaits a sweep', which is a measurement nobody took" — while the SUM beside it went on publishing
a confident count that silently omitted those reels, and the SENTENCE on his screen went on
reading "0 reel(s) (0 MB) are waiting on a sweep".

Found by the second eye reviewing v2880: "unknown vault count is still published as a complete
number on the fields the screen actually reads". Reproduced by importing a `shelf_driver` with no
OWED_BY, which is exactly the failure the guarded branch was written for.

These laws hold the three surfaces to one answer: the payload fields, the lane sentence, and the
say. [[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[label-outlived-referent]]
"""
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _run(broken):
    """Drive _retention_once with the tag->lane map readable or not. -> the published dict

    ⚠⚠ IT BUILDS ITS OWN SHELF. `_retention_once` reads `TV_HIST` or falls back to
    `<HERE>/frames/hist`, and refuses at "could not read the disk" when that path does not exist —
    which is every runner and every `safe_copy` sandbox. Measured: 4 laws failed there for a reason
    unrelated to their subject and the 5th PASSED for the wrong one, because a dead machine
    produces the same None the defect does. Pointing TV_HIST at a real empty directory lets the
    pass reach the lane logic anywhere, so this gate measures the code instead of the host — and
    can be proven red in a sandbox. [[feedback-fixtures-never-touch-live-data]]
    """
    saved = sys.modules.get("shelf_driver")
    for m in ("control_app",):
        sys.modules.pop(m, None)
    if broken:
        sys.modules["shelf_driver"] = types.ModuleType("shelf_driver")   # no OWED_BY at all
    elif saved is not None:
        sys.modules["shelf_driver"] = saved
    else:
        sys.modules.pop("shelf_driver", None)
    _hist_was, _tmp = os.environ.get("TV_HIST"), tempfile.mkdtemp(prefix="totals-shelf-")
    os.environ["TV_HIST"] = _tmp
    try:
        import control_app as CA
        CA._retention_once()
        return dict(CA._RETENTION)
    finally:
        shutil.rmtree(_tmp, ignore_errors=True)
        if _hist_was is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = _hist_was
        if saved is not None:
            sys.modules["shelf_driver"] = saved
        else:
            sys.modules.pop("shelf_driver", None)
        sys.modules.pop("control_app", None)


def _reached_the_lanes(case, r):
    """⚠⚠ THE PASS CAN REFUSE LONG BEFORE IT REACHES A LANE, AND THEN EVERY FIELD IS None.

    Measured in a `safe_copy` sandbox: `_retention_once()` returned
    "could not read the disk ([Errno 2] No such file or directory: .../frames)" and never got near
    the vault. Three of these laws failed there for a reason that has nothing to do with their
    subject — and the FOURTH one PASSED, because the defect's fingerprint (a None total) is also
    what a dead machine produces. A law that cannot tell its subject from a dead machine is green
    for the wrong reason, which is worse than red.

    So: establish that the pass got far enough to have an opinion about lanes, and stand down —
    loudly — when it did not. A skip is NOT a pass. [[feedback-blind-fixture-green-gate]]
    """
    err = r.get("error")
    say = str(r.get("say") or "")
    if err or say.startswith("could not read the disk"):
        case.skipTest("the retention pass refused before it reached any lane (%s) — UNMEASURED on "
                      "this machine, not clean. Run where the frames directory exists."
                      % (str(err or say)[:80]))
    return say


class ATotalIsOnlyAsKnownAsItsParts(unittest.TestCase):

    def test_an_unreadable_lane_makes_the_TOTAL_unknown_not_smaller(self):
        """★ THE DEFECT ITSELF. The sum must not quietly drop the lane it could not read."""
        r = _run(broken=True)
        _reached_the_lanes(self, r)
        self.assertIsNone(r.get("lockedBehindASweep"),
                          "the total is a number while one of its two lanes is unreadable — it is "
                          "not a smaller total, it is an unknown one: %r" % r.get("lockedBehindASweep"))
        self.assertIsNone(r.get("lockedMb"),
                          "the MB figure survived an unreadable lane: %r" % r.get("lockedMb"))

    def test_the_unknown_total_says_WHY(self):
        """A None with no reason is the same dead end as a zero with no denominator."""
        r = _run(broken=True)
        _reached_the_lanes(self, r)
        self.assertTrue(str(r.get("lockedTotalWhy") or "").strip(),
                        "the total is None and nothing says why")

    def test_the_SENTENCE_he_reads_does_not_claim_a_number(self):
        """⚠ THE SURFACE HE ACTUALLY READS. The fields were fixed once while this kept the zero."""
        say = _reached_the_lanes(self, _run(broken=True))
        self.assertIn("UNKNOWN", say,
                      "the sentence does not say UNKNOWN anywhere: %r" % say[:150])
        for claim in ("0 reel(s) (0 MB) are waiting on a sweep",
                      "0 reel(s) (0 MB) are locked behind a sweep"):
            self.assertNotIn(claim, say,
                             "the sentence still publishes a confident zero built from a lane "
                             "nobody could read: %r" % say[:150])

    def test_the_lane_breakdown_names_the_unreadable_lane(self):
        """An omitted lane reads as a lane with nothing in it."""
        say = _reached_the_lanes(self, _run(broken=True))
        self.assertIn("vault lane could not be read", say,
                      "the vault lane is simply absent from the breakdown, so the same words "
                      "describe a clear lane and an unmeasured one: %r" % say[:150])

    # ── the other direction: it must still report real numbers when it can ────────────────────
    def test_a_readable_map_still_publishes_the_count(self):
        """⚠ A law that only ever demands None would pass while the figure stopped working."""
        r = _run(broken=False)
        _reached_the_lanes(self, r)
        if r.get("lockedTotalWhy"):
            self.skipTest("the tag->lane map is genuinely unreadable on this machine — "
                          "UNMEASURED, not clean (%s)" % str(r.get("lockedTotalWhy"))[:60])
        self.assertIsInstance(r.get("lockedBehindASweep"), int,
                              "a readable map produced no count at all")
        self.assertIsNone(r.get("lockedTotalWhy"),
                          "a readable map still published an unknown-reason")


RED_PROOF = [
    {
        "why": "restoring the raw sum makes the total publish a confident count that omits the "
               "lane it could not read — the exact defect the second eye found on v2880",
        "file": "control_app.py",
        "find": '"lockedBehindASweep": (None if _vault_unknown else len(waiting)),',
        "replace": '"lockedBehindASweep": len(waiting),',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
