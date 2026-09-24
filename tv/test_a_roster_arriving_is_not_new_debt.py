# -*- coding: utf-8 -*-
"""v3328 — A ROSTER ARRIVING IS NOT NEW DEBT, AND THIS FILE ALREADY KNEW IT.

`verdict_provenance._verdict` defines REFERENCE as a row carrying no producer key AND no clock, and
the module's line 20 says what that means: *"a roster or lookup table — no clock, so the question
does not apply"*. A store the provenance question does not apply to cannot owe an answer to it.

`_compare`'s new-arrival branch reddened everything ranking below ANSWERS, so a roster arriving was
filed as "NEW store arrives REFERENCE — new debt". MEASURED 2026-09-18 on the live tree:

    🔴 engine_index.json:   NEW store arrives SILENT    — read as real debt at the time; #219 MEASURED it
                                                       is a roster whose `entryPoints` tripped an
                                                       endswith("ts") clock test — see _has_clock
    🔴 heart_floor.json:    NEW store arrives REFERENCE — FALSE
    🔴 test_reel_refs.json: NEW store arrives REFERENCE — FALSE

Two of the three reds were rosters being asked when they were last written and by whom.

⚠⚠ THE SAME FALSE RED ALREADY BIT ONCE AND WAS PATCHED BY NAME. The ratchet's OWN baseline arrived
REFERENCE and was reported as new debt on the very first clean run; the fix excluded that one
filename inside `_split`. That closed the instance and left the class open — and the class re-fired
the moment two more rosters landed, on a gate that was otherwise reporting 12 genuine improvements.
A rule learned once and generalised to nothing. [[copy-drift]] [[the-unjoined-end]]

⚠ SILENT AND PARTIAL STILL COUNT AS DEBT, AND THE BASELINE HALF BELOW PINS IT. SILENT means the row
HAS a clock and still names no writer — the question applies and went unanswered. Exempting that
too would turn a ratchet into an off switch, which is the failure this whole file exists to
prevent. The exemption is for inapplicability, never for inconvenience.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import verdict_provenance as VP  # noqa: E402


class TestARosterArrivingIsNotNewDebt(unittest.TestCase):

    def _new(self, state):
        """One store that did not exist at the baseline, arriving in `state`."""
        return VP._compare({}, {"newcomer.json": state})

    def test_a_roster_arriving_is_not_debt(self):
        reg, gain, new, gone = self._new("REFERENCE")
        self.assertEqual(
            reg, [],
            "a REFERENCE store — no producer key and NO CLOCK — was filed as new debt: %r. The "
            "module's own line 20 calls it 'a roster or lookup table, no clock, so the question "
            "does not apply'. Reddening it asks a lookup table when it was last written." % reg)
        self.assertTrue(
            any("ROSTER" in s for s in new),
            "the roster left the red list but says nothing in its place. A row that vanishes "
            "with no sentence is silencing, not classifying. Got: %r" % new)

    def test_a_SILENT_arrival_is_STILL_debt(self):
        """⚠ THE BASELINE. Without this, exempting REFERENCE could widen into an off switch."""
        reg, gain, new, gone = self._new("SILENT")
        self.assertTrue(
            any("newcomer.json" in s for s in reg),
            "a SILENT store stopped counting as debt. SILENT means the row HAS a clock and still "
            "names no writer — the question applies and went unanswered, and it must stay red. "
            "Got reg=%r new=%r" % (reg, new))

    def test_a_PARTIAL_arrival_is_STILL_debt(self):
        reg, gain, new, gone = self._new("PARTIAL")
        self.assertTrue(
            any("newcomer.json" in s for s in reg),
            "a PARTIAL store stopped counting as debt. It names WHO but not WHICH VERSION, and "
            "that gap is real. Got reg=%r" % reg)

    def test_an_EMPTY_arrival_keeps_its_own_sentence(self):
        """UNKNOWN had the honest shape first; this change must not disturb it."""
        reg, gain, new, gone = self._new("UNKNOWN")
        self.assertEqual(reg, [], "an empty store is not debt yet")
        self.assertTrue(
            any("not debt yet" in s and "not clean either" in s for s in new),
            "the empty-store sentence changed. It was already right — a store that lost its rows "
            "did not improve, and it did not regress either. Got: %r" % new)

    def test_a_REGRESSION_between_existing_states_still_reddens(self):
        """The ratchet's whole job. Exempting an arrival must not touch a MOVE."""
        reg, gain, new, gone = VP._compare({"s.json": "ANSWERS"}, {"s.json": "SILENT"})
        self.assertTrue(
            any("s.json" in s for s in reg),
            "a store that FELL from ANSWERS to SILENT no longer reddens. That is the regression "
            "the ratchet exists for, and it is unrelated to how arrivals are classified. reg=%r"
            % reg)

    def test_the_SILENT_REFERENCE_tie_is_untouched(self):
        """SILENT and REFERENCE tie ON PURPOSE — a move between them is reported, never reddened."""
        self.assertEqual(
            VP.RANK["SILENT"], VP.RANK["REFERENCE"],
            "the deliberate tie was broken. The module's comment: ranking one over the other "
            "'would invent a distinction the census does not draw'.")
        reg, gain, new, gone = VP._compare({"s.json": "SILENT"}, {"s.json": "REFERENCE"})
        self.assertEqual(reg, [], "a SILENT->REFERENCE move reddened; it must be reported only")
        self.assertEqual(gain, [], "a SILENT->REFERENCE move was counted as an improvement")


    def test_a_clock_is_a_clock_only_at_a_word_boundary(self):
        """⚠⚠ #219 — `endswith("at"/"ts")` on the lowercased name read ANY such word as a timestamp.
        MEASURED over every store in tv/: it misfiled engine_index.json (`entryPoints`) as SILENT debt
        and gave test_provenance's fixture a clock through `what`. Real clocks still count."""
        for k in ("ts", "at", "seen_at", "tick_ts", "seenAt", "updatedTs", "lastAt", "generatedTs",
                  "updated_At", "created_AT", "seen_TS", "createdAT"):
            self.assertTrue(VP._has_clock([k]), "%r is a clock and was not read as one" % k)
        for k in ("entryPoints", "what", "heartbeat", "format", "counts", "parts", "test_eye_vs_beat"):
            self.assertFalse(VP._has_clock([k]), "%r is a word, and it was read as a clock" % k)

    def test_the_real_engine_index_is_a_ROSTER(self):
        """DRIVEN on the tracked store that this misread filed as debt for ten days."""
        row = VP._sample_row(os.path.join(HERE, "engine_index.json"))
        row = row[0] if isinstance(row, tuple) else row
        self.assertIsInstance(row, dict, "premise: engine_index.json did not yield a row")
        self.assertIn("entryPoints", row, "premise: the key that tripped the old test is gone — "
                                          "re-derive this case")
        self.assertEqual(VP._verdict(row)[0], "REFERENCE",
                         "a module roster with no clock is graded as owing a writer again")

    def test_the_reds_are_printed_LAST_so_a_log_tail_names_them(self):
        """⚠ #219 — CI said "BACKWARDS in 5 place(s)" and its tail showed only ⚪ departures: the 🔴
        lines printed first and scrolled out. DRIVEN: a baseline under which one tracked store has
        regressed; the red line must come after every other line but the verdict."""
        import contextlib, io as _io, json as _json, tempfile, shutil
        d = tempfile.mkdtemp(prefix="vp-order-")
        base = os.path.join(d, "baseline.json")
        rep = VP.census()
        # the scope comes from the committed baseline, as ratchet() does — never from git, which a
        # heart2 sandbox (a copy, not a checkout) cannot answer
        _names = _json.load(_io.open(VP.BASELINE, encoding="utf-8")).get("trackedNames") or []
        tr, lo, _why = VP._split(rep, set(_names))
        self.assertTrue(tr, "premise: no tracked store to regress")
        victim = sorted(tr)[0]
        doc = {"tracked": dict(tr, **{victim: "ANSWERS", "zz_vanished.json": "ANSWERS"}),
               "local": {}, "trackedNames": sorted(tr) + ["zz_vanished.json"], "localCount": 0}
        _io.open(base, "w", encoding="utf-8").write(_json.dumps(doc))
        real, out = VP.BASELINE, _io.StringIO()
        try:
            VP.BASELINE = base
            with contextlib.redirect_stdout(out):
                rc = VP.ratchet()
        finally:
            VP.BASELINE = real
            shutil.rmtree(d, ignore_errors=True)
        lines = [l for l in out.getvalue().splitlines() if l.strip()]
        self.assertEqual(rc, 1, "premise: the planted regression did not refuse")
        reds = [i for i, l in enumerate(lines) if "🔴" in l and "BACKWARDS" not in l]
        others = [i for i, l in enumerate(lines) if ("⚪" in l or "🟢" in l)]
        self.assertTrue(reds, "the refusal named no store at all:\n%s" % out.getvalue()[-600:])
        self.assertIn("zz_vanished.json", "\n".join(lines[r] for r in reds))
        if others:
            self.assertGreater(min(reds), max(others),
                               "a red line printed BEFORE the ⚪/🟢 lines — a log tail will cut it off")
        self.assertIn("BACKWARDS", lines[-1], "the verdict is not the last line")

if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the roster branch sends every arriving lookup table back to 'new debt'",
        "file": "tv/verdict_provenance.py",
        "find": '        elif after == "REFERENCE":',
        "replace": '        elif False:',
        "matches": 1,
    },
    {
        "why": "widening the exemption to every non-ANSWERS arrival turns the ratchet off",
        "file": "tv/verdict_provenance.py",
        "find": '            new.append("%s: NEW and a ROSTER — no clock, so provenance does not apply" % store)\n        elif RANK.get(after, 0) < RANK["ANSWERS"]:\n            reg.append("%s: NEW store arrives %s — new debt" % (store, after))',
        "replace": '            new.append("%s: NEW and a ROSTER — no clock, so provenance does not apply" % store)\n        elif RANK.get(after, 0) < 0:\n            reg.append("%s: NEW store arrives %s — new debt" % (store, after))',
        "matches": 1,
    },
    {
        "why": "#219 - the clock test back on a bare suffix: entryPoints (and `what`) read as timestamps, and a module roster graded as debt again",
        "file": "tv/verdict_provenance.py",
        "find": "        if k.lower() in CLOCK_FIELDS or _CLOCK_SUFFIX.search(k):",
        "replace": "        if k.lower() in CLOCK_FIELDS or k.lower().endswith((\"at\", \"ts\")):",
        "matches": 1
    },
    {
        "why": "#219 - the reds no longer printed above the verdict, so a CI log tail shows the departures and never names what went backwards",
        "file": "tv/verdict_provenance.py",
        "find": "        for s in _red:\n            print(\"   🔴 %s\" % s)",
        "replace": "        for s in _red:\n            pass",
        "matches": 1
    },
]
