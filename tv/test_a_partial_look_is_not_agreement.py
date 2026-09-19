# -*- coding: utf-8 -*-
"""v3349 (#104) — A LOOK THAT NEVER REACHED THE CHANGE IS NOT AN OPINION ABOUT IT.

MEASURED ON v3347, live, the day it shipped:

    payload                8,967 of 92,115 diff chars  (the rest cut)
    changed files omitted  10, INCLUDING tv/self_arming.py — the file the version exists to change
    the eye answered       "REACH: 2/2 hunks … all other listed files UNKNOWN.
                            No concrete defect is present in the bytes shown."
    the row stored         verdict=clean

`clean` means the eye looked and found nothing. That eye said, in its own first line, that it
could not look. The assurance was never earned.

=== THE INTENT WAS ALREADY RIGHT; THE STORE WAS WRONG ===
`payload_for()` has computed the omitted list since v3341 and used it to WARN THE EYE inside the
prompt. Its own comment says *"the ROW must carry it too, or a later reader sees a clean verdict
with no way to know its reach"* — and the row did carry it, as a **400-char-capped prose suffix on
`asked`**. A one-to-many fact flattened into another field and truncated, at the one moment keeping
it was free. [[one-to-one-store-for-a-one-to-many-fact]] — the fourth instance of that shape.

So this version does not compute anything new. It carries the LIST to the row and gives it a
reader. [[the-unjoined-end]]

=== `reached` IS A DIFFERENT QUESTION, AND I GOT THIS WRONG FIRST ===
I claimed `reached` was already lying on the v3347 row. It was not. `reached` means THE SEAT
ANSWERED — "an unreachable eye is an EMPTY SEAT, never agreement". A reachable eye handed two
hunks of a twelve-file change is `reached=True` and blind, which is exactly that row. Two
questions, two fields; the second one simply did not exist.

=== WHY THIS DOES NOT DECIDE THE VERDICT, YET ===
The obvious next step is to downgrade such a look from `clean` to `cannot-tell`. That is
deliberately NOT in this version. #97 measured that **22 of 36 versions (61%)** had a code file
never reach the eye, so a blanket rule would move a large population, and the radius cannot be
sized from the ledger because the data was never stored — which is the whole defect. #101 already
proved once this session that a verdict rule designed without measurement gets refuted by the
ledger (172 of 637). **Persist first, judge once there are rows to judge against.**
[[regression-guard]] §5a

⚠ PARTIAL LOOKS ARE NAMED, NEVER DISCARDED. What the eye said about the bytes it DID see is real
evidence, and dropping it would be its own lie. What must never happen is two partial looks
reading as AGREEMENT about a change neither of them saw.
"""
import inspect
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402
import second_eye_run as R  # noqa: E402


def _tmp():
    return os.path.join(tempfile.mkdtemp(), "ledger.jsonl")


class TheRowCarriesTheList(unittest.TestCase):

    def test_record_accepts_an_absent_list(self):
        self.assertIn("absent", inspect.signature(L.record).parameters,
                      "the ledger has no slot for what the eye never saw, so the reach lives only "
                      "in the prompt and dies with it")

    def test_it_is_stored_as_a_LIST_not_a_sentence(self):
        """⚠⚠ THE CASE. The old store was prose on `asked`, capped at 400 — a one-to-many fact in
        a one-to-one container. A reader cannot ask 'was tv/x.py seen?' of a sentence."""
        p = _tmp()
        L.record(version="v9001", model="m", verdict="clean", answer_head="x", path=p,
                 absent=["tv/a.py", "tv/b.py"])
        row = L._rows(p)[-1]
        self.assertIsInstance(
            row.get("absent"), list,
            "the omitted files are stored as %r. A LIST is the point: the next reader must be able "
            "to ask whether one NAMED file reached the eye, and no sentence can answer that."
            % type(row.get("absent")).__name__)
        self.assertEqual(row["absent"], ["tv/a.py", "tv/b.py"])

    def test_the_three_states_stay_apart(self):
        """⚠ [] is MEASURED-AND-EMPTY; a missing key is NOBODY-ASKED. Collapsing them turns 'we
        never checked' into 'we checked and it was fine'. [[unknown-stays-unknown]]"""
        p = _tmp()
        L.record(version="v1", model="m", verdict="clean", answer_head="x", path=p, absent=[])
        L.record(version="v2", model="m", verdict="clean", answer_head="x", path=p)
        rows = L._rows(p)
        measured_empty = [r for r in rows if r.get("version") == "v1"][0]
        never_asked = [r for r in rows if r.get("version") == "v2"][0]
        self.assertEqual(measured_empty.get("absent"), [],
                         "a look that omitted nothing must record [] — that is a MEASUREMENT")
        self.assertIsNone(never_asked.get("absent"),
                          "a look whose reach was never established must record null/absent, and "
                          "it must not be indistinguishable from one that omitted nothing")


class AgreementSaysWhenNobodySawIt(unittest.TestCase):

    def test_two_partial_looks_do_not_read_as_plain_agreement(self):
        """⚠⚠ THE ONE THAT MATTERS. Two looks agreeing about a change neither saw is not a second
        opinion; it is the same blindness twice."""
        p = _tmp()
        for _ in range(2):
            L.record(version="v9001", model="m", verdict="clean", answer_head="fine", path=p,
                     absent=["tv/subject.py"])
        a = L.agreement("v9001", path=p)
        self.assertEqual(a.get("partial"), 2,
                         "agreement() does not count how many looks were blind to part of the "
                         "change, so a reader cannot tell this from two complete looks")
        self.assertIn(
            "NEVER SAW", a["say"],
            "the sentence a human reads does not mention that both looks missed part of the "
            "change: %r. A count nobody surfaces is the same as no count." % a["say"])

    def test_complete_looks_are_left_alone(self):
        """⚠ THE BASELINE, or the clause above would fire on everything and mean nothing.
        [[regression-guard]] §5"""
        p = _tmp()
        for _ in range(2):
            L.record(version="v9002", model="m", verdict="clean", answer_head="fine", path=p,
                     absent=[])
        a = L.agreement("v9002", path=p)
        self.assertEqual(a.get("partial"), 0)
        self.assertNotIn("NEVER SAW", a["say"],
                         "two looks that saw the whole change are being warned about anyway")

    def test_a_legacy_row_is_UNKNOWN_reach_and_NOT_partial(self):
        """Every row before v3349 has no `absent`. Counting those as partial would invent a
        finding about 860 historical looks; counting them as complete would assume the thing this
        version exists because nobody knew. They are their own count."""
        p = _tmp()
        L.record(version="v9003", model="m", verdict="clean", answer_head="x", path=p)
        a = L.agreement("v9003", path=p)
        self.assertEqual(a.get("partial"), 0,
                         "a row whose reach was never recorded is being reported as a BLIND look "
                         "— that is a claim about history nobody measured")
        self.assertEqual(a.get("reachUnknown"), 1,
                         "a row whose reach was never recorded vanishes from the reader entirely, "
                         "so it reads as complete")


class TheJoinIsMade(unittest.TestCase):
    """⚠ Both halves existed for 8 versions and were never joined. Pin the wire, not the ends."""

    def test_payload_for_hands_back_the_list(self):
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            "+ body + \"\\n```\\n\", dropped, absent", code,
            "payload_for no longer returns the absent LIST alongside the prose, so the caller has "
            "only a sentence to pass on and the row is back to storing a truncated summary")

    def test_record_answer_passes_it_to_the_ledger(self):
        self.assertIn("absent", inspect.signature(R.record_answer).parameters,
                      "record_answer cannot accept the list, so it cannot forward it")
        src = io.open(os.path.join(HERE, "second_eye_run.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            "sha=sha, absent=absent)", code,
            "the LOOKED path records without the absent list. That is the unjoined end this "
            "version exists to close: computed, used in the prompt, dropped before the row.")


class HisRealLedgerIsNotAssumedComplete(unittest.TestCase):

    def test_existing_rows_are_reported_as_unknown_reach_not_as_clean_reach(self):
        """BEHAVIOURAL, against his file, and honest when it is absent."""
        if not os.path.exists(L.LEDGER_PATH):
            self.skipTest("no ledger on this machine")
        rows = L._rows()
        if len(rows) < 50:
            self.skipTest("only %d rows here; too few to say anything" % len(rows))
        with_field = [r for r in rows if r.get("absent") is not None]
        self.assertLess(
            len(with_field), len(rows),
            "every row already carries `absent`, which cannot be true of rows written before this "
            "version — if it is, the field is being back-filled with a guess rather than measured.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the list at the record call puts the row back to a truncated sentence",
        "file": "tv/second_eye_run.py",
        "find": "               sha=sha, absent=absent)",
        "replace": "               sha=sha)",
        "matches": 1,
    },
    {
        "why": "storing a bool instead of the list cannot answer whether one NAMED file was seen",
        "file": "tv/second_eye_ledger.py",
        "find": '        "absent": (list(absent) if absent is not None else None),',
        "replace": '        "absent": (bool(absent) if absent is not None else None),',
        "matches": 1,
    },
    {
        "why": "a reader that does not count partial looks lets two blind looks read as agreement",
        "file": "tv/second_eye_ledger.py",
        "find": '    _partial = [r for r in reached if r.get("absent")]',
        "replace": "    _partial = []",
        "matches": 1,
    },
    {
        "why": "counting a never-measured row as partial invents a finding about 860 old looks",
        "file": "tv/second_eye_ledger.py",
        "find": '    _unknown_reach = [r for r in reached if r.get("absent") is None]',
        "replace": "    _unknown_reach = []",
        "matches": 1,
    },
]
