#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A 70-CHARACTER WINDOW MANUFACTURED A FINDING, AND THE MODULE PUBLISHED IT.

⚠⚠ WHAT HAPPENED. `printer_reach` tallied its refusals with `blocked[str(cwhy)[:70]]`. The refusal
sentence names EVERY missing contract fact in one line:

    "the sweep never extracted name (the item's name, which only ever appears in a hover
     tooltip), location (WHERE it was — the container and the cell box inside it (his slot
     identity)), provenance (…)"

Seventy characters lands part-way through the FIRST fact's explanation, so every distinct refusal
collapsed into one bucket whose text happened to end inside the word `name`. The module's own
docstring then stated, as a measurement:

    "22 carry an `extracted` record, and ALL 22 fail on the SAME single fact: `name`"

**That was false.** Re-measured untruncated, 2026-09-05: `name`, `location` AND `provenance` are
missing on **all 30** seals.

⚠ WHY THE CORRECTION MATTERS RATHER THAN BEING PEDANTRY. The two readings imply different work.
One missing fact is a reader change. `location` missing is a CAPTURE question — 0 of 1,065 deep
rows carry a cell or slot — and that is his ruling to make, not something to code around. A finding
that names the wrong blocker sends the next person to the wrong file.

⚠ AND IT IS THE SAME SHAPE AS `source_window_shortcut`: a fixed-size slice of something whose
length you did not check does not shorten the answer, it produces a different one.

⚠ NOTHING HERE TOUCHES HIS STORES. Every case drives the pure tally logic or reads the seal store
read-only through `frame_authority`.
"""
import contextlib
import io as _io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_authority as FA  # noqa: E402
import printer_reach as PR  # noqa: E402


#: TWO SEALS WHOSE REFUSALS ARE BYTE-IDENTICAL FOR 70 CHARACTERS AND DIFFER AFTER — the collapse
#: itself, driven through the real contract instead of two strings typed to look like it. MEASURED
#: 2026-09-05 by asking `seal_covers_extraction`: the empty-`extracted` refusal runs 274 chars, the
#: `["location"]` one 186, and `a[:70] == b[:70]` is True — both end inside
#: "the sweep never extracted name (the item's name, which only ever appea".
_REFUSED_LATE = {
    "s_all":  {"ts": 1, "rows": 2, "promptVer": "vpX", "extracted": []},
    "s_some": {"ts": 1, "rows": 2, "promptVer": "vpX", "extracted": ["location"]},
}


@contextlib.contextmanager
def _corpus(seals):
    """A shelf ON DISK — triage store and seal store — read by the module's OWN readers.

    ⚠⚠ THREE CASES BELOW ASKED `PR.report()` BARE AND SKIPPED WHEN IT SAID NOTHING, WHICH MADE
    THEM PERMANENT SKIPS EVERYWHERE BUT HIS MAC. Both stores are untracked — `.gitignore:147` for
    `tv/retro_triage.json`, and `tv/vault_swept.json` is simply never committed — so on a runner
    `_triage()` cannot open the file, `report()` returns UNKNOWN, and every guard here reported
    `skipped 'nothing is blocked on this tree'`. MEASURED on a `git archive HEAD` export:
    `OK (skipped=2)`, two of seven, on every CI run this file has ever had. A skip counted as a
    pass is the defect this repo has been bitten by most. [[regression-guard]]

    `frame_authority._load` joins a ROOT with `SEAL_STORE`, so the fixture is a directory and
    `sealed_sessions` is asked for it through its own documented `root=` seam.
    """
    d = tempfile.mkdtemp(prefix="reach_facts_")
    real_triage, real_seals = PR.TRIAGE, FA.sealed_sessions
    try:
        triage = {"reel_%s" % k: {"panels": 3, "frames": 40} for k in seals} or {"reel_s_x": {"panels": 3}}
        with _io.open(os.path.join(d, "retro_triage.json"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(triage))
        with _io.open(os.path.join(d, FA.SEAL_STORE), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(seals))
        PR.TRIAGE = os.path.join(d, "retro_triage.json")
        FA.sealed_sessions = lambda root=None: real_seals(d)
        yield
    finally:
        PR.TRIAGE, FA.sealed_sessions = real_triage, real_seals
        shutil.rmtree(d, ignore_errors=True)


class TheRefusalIsNotCutInHalf(unittest.TestCase):

    def test_the_tally_key_is_the_WHOLE_reason(self):
        """★ RED for the original defect, GRADED ON BEHAVIOUR NOT ON TEXT.

        ⚠ My first cut of this asserted `"[:70]" not in inspect.getsource(...)` and FAILED — on the
        comment that DESCRIBES the defect, and on an unrelated `str(e)[:70]` in an error message.
        That is the third guard I have written in two versions that grades prose instead of code,
        and the second to be defeated by its own explanation. A guard must drive the thing.
        [[source-reading-guard]]

        The behaviour: a blocked reason is keyed by its FULL sentence, so a bucket key longer than
        70 characters proves the cut is gone. The live refusals run to ~200 characters.
        """
        with _corpus(_REFUSED_LATE):
            r = PR.report()
        blocked = r.get("blocked") or {}
        self.assertTrue(blocked,
                        "the constructed corpus has two seals the contract refuses and nothing "
                        "was tallied, so this case is measuring the fixture: %s" % r.get("why"))
        longest = max(len(k) for k in blocked)
        self.assertGreater(longest, 70,
                           "every blocked reason is <= 70 chars, which is what the truncation "
                           "produced; longest key is %d" % longest)
        # ★ AND THE COLLAPSE ITSELF: two refusals identical for 70 characters must stay two rows.
        self.assertEqual(
            len(blocked), 2,
            "two seals whose refusals differ only AFTER character 70 collapsed into %d bucket(s) "
            "— that is the truncation back, and it is what made this module publish 'ALL 22 fail "
            "on the SAME single fact: name'." % len(blocked))

    def test_two_reasons_differing_late_stay_DISTINCT(self):
        a = "the sweep never extracted name (the item's name, which only ever appears in a tooltip)"
        b = "the sweep never extracted name (the item's name, which only ever appears in a HAT)"
        self.assertEqual(a[:70], b[:70], "the fixture no longer reproduces the collapse")
        blocked = {}
        for why in (a, b):
            blocked[why] = blocked.get(why, 0) + 1
        self.assertEqual(len(blocked), 2,
                         "two different refusals still collapse into one bucket")

    def test_the_docstring_STATES_the_corrected_measurement(self):
        """⚠ A corrected number under an uncorrected sentence is label-outlived-referent. The prose
        has to move with the measurement.

        ⚠⚠ AND THIS CASE ORIGINALLY ASSERTED THE WRONG THING — that the false claim is ABSENT.
        It failed, correctly: the correction QUOTES the false claim in order to retract it, and a
        retraction that may not name what it retracts is a worse document. Assert the presence of
        the truth, never the absence of a string.
        """
        import inspect
        doc = inspect.getdoc(PR) or ""
        self.assertIn("USED TO READ", doc,
                      "the docstring does not mark the corrected line as a correction, so a reader "
                      "cannot tell which of the two numbers is current")
        for fact in FA.EXTRACTION_CONTRACT:
            self.assertIn(fact, doc,
                          "the corrected measurement does not name %r — it was the omission of "
                          "`location` that made this look like a one-fact problem" % fact)


class EveryMissingFactIsCounted(unittest.TestCase):

    def test_report_carries_a_per_fact_tally(self):
        r = PR.report()
        self.assertIn("missingByFact", r)
        self.assertIsInstance(r["missingByFact"], dict)

    def test_it_names_ALL_THREE_facts_not_just_name(self):
        """★★ THE CORRECTED MEASUREMENT. If this ever shows only `name`, the truncation is back
        or the contract changed — either way the docstring above is wrong again."""
        with _corpus(_REFUSED_LATE):
            r = PR.report()
        m = r.get("missingByFact") or {}
        self.assertTrue(m,
                        "the constructed corpus refuses both its seals and no fact was counted, "
                        "so the per-fact tally is not joined to the refusal path")
        self.assertEqual(set(m), set(FA.EXTRACTION_CONTRACT),
                         "the per-fact tally does not cover the whole contract: %r" % (m,))
        self.assertGreater(m.get("location", 0), 0,
                           "`location` shows as satisfied — if that is true the capture question is "
                           "answered and the docstring must say so")

    def test_the_key_is_present_on_EVERY_return_shape(self):
        """⚠ REG-546's own law, restated in this file: 'every return carries the same keys'. A
        shape that changes with the verdict is not a shape, and the UNKNOWN paths are exactly the
        ones a consumer hits when nothing was established."""
        import inspect
        src = inspect.getsource(PR.report)
        returns = src.count('"blocked"')
        tallies = src.count('"missingByFact"')
        self.assertEqual(returns, tallies,
                         "%d returns carry `blocked` but only %d carry `missingByFact` — a "
                         "consumer reading it breaks on the paths that mean nothing was "
                         "established" % (returns, tallies))


class TheStateStaysHonest(unittest.TestCase):
    """⚠ The correction must not quietly change the verdict. 0 seals satisfy the contract either
    way; only the REASON was wrong."""

    def test_it_still_reports_UNREACHABLE_not_a_cheerful_zero(self):
        """⚠⚠ THIS GUARD NAMED THE RIGHT LAW AND COULD NOT REACH ITS OWN CASE. It was gated on
        `if r.get("state") == PR.UNREACHABLE`, asked of the LIVE tree — and on a runner the triage
        store is untracked, so `report()` returns UNKNOWN first and the body never ran at all. On
        his Mac the body DOES run — and cannot fail: the only way to reach UNREACHABLE with an
        empty `blocked` is a corpus of zero seals, and his shelf has thirty. So on one venue the
        assertion never executed and on the other it could never go red. Right guard, unreachable
        case, both ways.
        [[the-unjoined-end]] [[gate-blind-to-unexercised-input]]
        """
        with _corpus(_REFUSED_LATE):
            r = PR.report()
        self.assertEqual(
            r.get("state"), PR.UNREACHABLE,
            "two seals exist and the contract refuses both, which is the MEASURED finding, and it "
            "reported %r instead" % r.get("state"))
        self.assertTrue(r.get("blocked"),
                        "UNREACHABLE with no blocked reasons is a zero through a filter that "
                        "rejected everything, reported as if it measured something")
        # the live ask stays, because on his Mac it is free — but it may never be the only path.
        self.assertIn(PR.report().get("state"),
                      (PR.UNREACHABLE, PR.UNKNOWN, PR.CLEAN, PR.CONTRADICTION))

    def test_a_corpus_of_NO_SEALS_is_UNKNOWN_not_a_filter_that_refused_everything(self):
        """★ THE CASE THE GUARD ABOVE COULD NEVER SEE. `frame_authority._load_state` answers
        ABSENT with `({}, "absent")` — deliberate since v2079, because for a FRAME DELETER "there
        is nothing to read" and "I could not read it" are opposite facts. `sealed_sessions` then
        returns `({}, True)`, and `report()` read that as a corpus of zero seals and announced

            UNREACHABLE — "NOT ONE of the 0 seals satisfies the extraction contract ... Zero
            contradictions here measures the CONTRACT REFUSING EVERY SEAL"   Blocking reasons:

        A filter that rejected NOTHING, reported as a filter that rejected EVERYTHING, with the
        reasons list empty. MEASURED 2026-09-05 on a tracked-files-only checkout: state=UNREACHABLE,
        counts seals=0, blocked={}. Every tree that has never run a vault sweep hits it.

        ⚠ REG-543 drew the line at *was anything established*, not *could anything be compared* —
        both fail here. Thirty refused seals establish something hard-won: the shelf was read and
        the blocker is a CAPTURE question. Zero seals establish nothing at all, and letting that
        wear UNREACHABLE re-merges the two facts the split separated. [[unknown-stays-unknown]]
        """
        with _corpus({}):
            r = PR.report()
        self.assertEqual(
            r.get("state"), PR.UNKNOWN,
            "a corpus with no seals reported %r. Nothing was established — the contract was never "
            "asked to admit anything." % r.get("state"))
        self.assertNotIn(
            "REFUSING EVERY SEAL", r.get("why") or "",
            "it claims the contract refused every seal, and there were no seals to refuse")
        self.assertFalse(r.get("blocked"),
                         "it reports blocking reasons for seals that do not exist: %r"
                         % (r.get("blocked"),))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
