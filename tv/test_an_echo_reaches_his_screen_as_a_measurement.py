# -*- coding: utf-8 -*-
"""#182, second half — THE ORGAN THAT READS `agreement()` MAPPED ECHO ONTO **UNKNOWN**.

v3439 gave `second_eye_ledger.agreement()` a fifth state, ECHO: two or more looks that agree and
every one of them MEASURED to be the same family — one witness asked twice, which is not
corroboration. Measured on his 942-row ledger: of the versions asked twice, the same-family pairs
are the large majority.

`console_doctor._check_the_second_eye_was_asked_twice` maps DISAGREE -> MISSING, AGREE -> OK,
SINGLE -> MISSING, and everything else falls through to `return UNKNOWN, ...`. So ECHO reached his
screen as UNKNOWN — the word the console draws as **CAN'T ASK** — carrying the ledger's own correct
sentence underneath it.

    ✅ not a false OK   ✅ not a false red   ❌ WRONG IN KIND

ECHO is a MEASUREMENT: both looks reached, both carried a verdict, and the family was re-derived
from the model id. UNKNOWN means nobody could look. Collapsing a measured fact into "nobody could
look" is the exact lie this repo refuses everywhere else. [[unknown-stays-unknown]]

=== WHY THE FIX IS `MISSING` AND NOT A FIFTH DOCTOR STATE ===
⚠⚠ MEASURED BY DRIVING `control_app.eagle_partition()`, NOT BY READING IT. The eagle buckets on
four literal strings — `missing` into bad/mine/byDesign, `unknown` or `unmeasured` into unk. A word
it has never heard is counted by **nothing** and folds into "all clear across N check(s)", while
`control_ui.html` still DRAWS the row (it hides only `state === 'ok'`) under its fallback word
'UNKNOWN' and files it under WAITING ON YOU. Uncounted and shown as HIS, at the same time. That is
the same shape as the UNMEASURED row that tripped `test_UNKNOWN_is_never_folded_into_all_clear` and
stopped the live site deploying for a whole day while the code was right throughout.

`TheEagleUnderstandsWhateverThisRowReturns` below is that measurement turned into a LAW, with a
baseline proving it can distinguish: a made-up state must land in NO bucket, or the law is measuring
nothing.

=== WHAT THIS FILE DRIVES ===
Every case CALLS `_check_the_second_eye_was_asked_twice()` and asserts the verdict it returns. None
asserts arithmetic about the mapping, and none reads its source. The stub records whether it was
REACHED, because the row answers UNKNOWN from four earlier return statements — an assertion of
UNKNOWN that never got as far as `agreement()` would pass vacuously and prove nothing.
[[a-probe-licenses-only-what-it-tested]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


# ── the fixture ─────────────────────────────────────────────────────────────────────────────────
def _verdict_dict(state, say, families, fam_unknown=0, looks=2, verdicts=None):
    """A payload shaped exactly like `agreement()`'s real return. No key invented."""
    return {"version": "v9182", "looks": looks, "empty": 0, "state": state,
            "verdicts": list(verdicts if verdicts is not None else ["clean"] * looks),
            "partial": 0, "reachUnknown": 0, "cut": 0,
            "families": list(families), "familyKnown": len(families) * (looks // max(1, len(families) or 1)),
            "familyUnknown": fam_unknown,
            "sameFamily": (looks >= 2 and len(families) == 1 and fam_unknown == 0),
            "say": say}


ECHO = _verdict_dict(
    "ECHO",
    "2 looks at v9182 say the same thing (clean) and every one of them is xai — that is ONE "
    "witness asked 2 times, not corroboration. Two derivations of one source agreeing is one "
    "number wearing two names.",
    ["xai"])
#: ⚠ THE BASELINE. A GENUINE cross-family pair. If this stops reading OK the fix has become a
#: guard that accuses everything, which is worse than the defect it was built for.
CROSS_AGREE = _verdict_dict(
    "AGREE", "2 looks at v9182 AGREE (clean) · 2 look(s), 2 naming a family (anthropic 1, xai 1)",
    ["anthropic", "xai"])
DISAGREE = _verdict_dict(
    "DISAGREE", "2 looks at ONE payload DISAGREE (clean, findings) — the eye is not steady here",
    ["xai"], verdicts=["clean", "findings"])
SINGLE = _verdict_dict(
    "SINGLE", "v9182 was looked at ONCE (clean) — asked twice is his #56 ruling", ["xai"], looks=1,
    verdicts=["clean"])
#: a SIXTH word nobody has taught this row about. It must still reach him as UNKNOWN — that is
#: what the fall-through is FOR, and the ECHO branch must not have eaten it.
STRANGER = _verdict_dict("QUORUM", "a state added later and never wired here", ["xai"])


class _DrivesTheRow(unittest.TestCase):
    """Common machinery: patch the ledger module the row imports, and PROVE the stub was reached."""

    def _doctor(self):
        try:
            import console_doctor as cd
        except Exception as e:                       # pragma: no cover — reported, never assumed
            self.skipTest("console_doctor will not import here (%s: %s) — the join is UNMEASURED, "
                          "which is not a pass" % (type(e).__name__, str(e)[:120]))
        return cd

    def _ledger(self):
        try:
            import second_eye_ledger as L
        except Exception as e:                       # pragma: no cover — reported, never assumed
            self.skipTest("second_eye_ledger will not import here (%s: %s) — UNMEASURED, not a "
                          "pass" % (type(e).__name__, str(e)[:120]))
        return L

    def _drive(self, payload, version="v9182"):
        """-> (state, say). Raises if the row never actually consulted the stub.

        ⚠⚠ THE REACHED FLAG IS THE PREMISE, NOT DECORATION. `_check_the_second_eye_was_asked_twice`
        returns UNKNOWN from FOUR places before `agreement()` is ever called — a failed import, a
        raising `current_version`, an empty version, a raising reader. A case that asserts UNKNOWN
        would be satisfied by every one of them while the mapping under test never ran.
        """
        cd, L = self._doctor(), self._ledger()
        seen = {"n": 0, "asked": None}

        def _agreement(v, path=None):
            seen["n"] += 1
            seen["asked"] = v
            return dict(payload)

        old = (L.current_version, L.agreement, L.agreement_census)
        L.current_version = lambda *a, **k: version
        L.agreement = _agreement
        L.agreement_census = lambda *a, **k: {"say": "3 of 877 version(s) were asked twice"}
        try:
            state, say = cd._check_the_second_eye_was_asked_twice()
        finally:
            L.current_version, L.agreement, L.agreement_census = old
        self.assertEqual(
            1, seen["n"],
            "the row returned (%r, %r) WITHOUT calling agreement() even once, so this case proves "
            "nothing about the mapping — it measured one of the four early UNKNOWN returns."
            % (state, say))
        self.assertEqual(version, seen["asked"],
                         "the row asked about %r, not the version under test" % (seen["asked"],))
        return state, say


class EveryStateReachesHimAsItself(_DrivesTheRow):
    """THE MAPPING, DRIVEN. One case per state, and the cross-family baseline first."""

    def test_BASELINE_a_genuine_cross_family_AGREE_still_reads_OK(self):
        """⚠ THE GUARD THAT ACCUSES EVERYTHING IS NOT A GUARD. Two looks, two DIFFERENT families,
        same verdict — that is the corroboration his #56 ruling asked for, and it must still pass.
        Without this case, mapping every multi-look state to MISSING would go green."""
        cd = self._doctor()
        state, say = self._drive(CROSS_AGREE)
        self.assertEqual(
            cd.OK, state,
            "a genuine CROSS-FAMILY agreement no longer reads OK (%r). The #182 fix has become a "
            "row that accuses every pair, which gets silenced faster than the defect it names. "
            "say=%r" % (state, say))

    def test_an_ECHO_reads_MISSING_and_never_UNKNOWN(self):
        """The defect this file is named for: a MEASURED fact leaving as 'nobody could ask'."""
        cd = self._doctor()
        state, say = self._drive(ECHO)
        self.assertNotEqual(
            cd.UNKNOWN, state,
            "ECHO still reaches his screen as UNKNOWN — the console draws that word as CAN'T ASK. "
            "Two looks reached, both carried a verdict and both families were re-derived from the "
            "model id: that is a MEASUREMENT, and UNKNOWN means nobody could look. say=%r" % say)
        self.assertNotEqual(
            cd.OK, state,
            "ECHO reads OK, which asserts the corroboration #182 measured was never earned — and "
            "an `ok` row is not drawn on the panel at all, so his screen would show nothing. "
            "say=%r" % say)
        self.assertEqual(
            cd.MISSING, state,
            "ECHO reads %r. It must be MISSING: the corroborating look was genuinely not taken, "
            "this check is in MINE so MISSING never reaches the count he acts on, and MISSING is "
            "one of the four states the eagle can bucket at all. say=%r" % (state, say))

    def test_the_ECHO_row_carries_what_was_measured_and_whose_move_it_is(self):
        """A lamp with no reason is furniture; a refusal that names no action is a complaint."""
        state, say = self._drive(ECHO)
        self.assertIn(
            "not corroboration", say,
            "the doctor row dropped the ledger's own explanation, so he is shown a red word with "
            "no reason: %r" % say)
        self.assertIn(
            "MINE", say,
            "the row does not say whose move this is. It is in console_doctor.MINE precisely so a "
            "look I failed to take never bills him — the sentence has to say so: %r" % say)
        self.assertIn(
            "DIFFERENT model family", say,
            "the row names no action. 'One witness asked twice' with no next step reads as a "
            "complaint nobody can close: %r" % say)
        self.assertIn(
            "asked twice", say,
            "the row's own denominator sentence (the census tail) did not travel with the "
            "verdict: %r" % say)

    def test_an_ECHO_with_no_sentence_still_names_what_it_is(self):
        """⚠ THE FALLBACK IS A SENTENCE TOO. `a.get("say")` can be empty on a hand-written or an
        older payload, and `"" or X` takes X — so the fallback is what he reads on exactly the
        rows nobody wrote prose for. It must not degrade to a bare word."""
        blank = dict(ECHO)
        blank["say"] = ""
        cd = self._doctor()
        state, say = self._drive(blank)
        self.assertEqual(cd.MISSING, state, "the blank-say ECHO changed state: %r" % say)
        for must in ("SAME family", "one witness asked twice", "not corroboration"):
            self.assertIn(
                must, say,
                "the ECHO fallback sentence does not contain %r, so a row with no stored prose "
                "reaches him without saying what was measured: %r" % (must, say))

    def test_a_DISAGREE_still_reads_MISSING(self):
        cd = self._doctor()
        state, say = self._drive(DISAGREE)
        self.assertEqual(cd.MISSING, state,
                         "two looks disagreeing is a finding about the INSTRUMENT and must stay "
                         "red: %r / %r" % (state, say))

    def test_a_SINGLE_still_reads_MISSING(self):
        cd = self._doctor()
        state, say = self._drive(SINGLE)
        self.assertEqual(cd.MISSING, state,
                         "one look is the omission this check was born for: %r / %r" % (state, say))

    def test_a_state_NOBODY_HAS_WIRED_still_falls_through_to_UNKNOWN(self):
        """⚠ THE FALL-THROUGH IS LOAD-BEARING AND THE ECHO BRANCH MUST NOT HAVE EATEN IT. A sixth
        word added to the ledger later is one this row has never been taught; UNKNOWN is the
        honest answer to it, and rounding it to OK or to MISSING would be a confident verdict
        about a state nobody here has read. [[unknown-stays-unknown]]"""
        cd = self._doctor()
        state, say = self._drive(STRANGER)
        self.assertEqual(
            cd.UNKNOWN, state,
            "a state this row has never heard of now reads %r. An unwired sixth word must reach "
            "him as UNKNOWN, not as a verdict: %r" % (state, say))


class TheEagleUnderstandsWhateverThisRowReturns(_DrivesTheRow):
    """⚠⚠ THE HALF THAT COST A DAY OF DEPLOYS. A doctor state the watchdog cannot bucket is not a
    cosmetic choice — it is counted by nothing and folds into "all clear", while the panel draws
    the row anyway. This drives the real partition instead of trusting the four literals."""

    NAME = "second eye asked twice"

    def _partition(self):
        try:
            import control_app as ca
        except Exception as e:                       # pragma: no cover — reported, never assumed
            self.skipTest("control_app will not import here (%s: %s) — the eagle's bucketing is "
                          "UNMEASURED, which is not a pass" % (type(e).__name__, str(e)[:120]))
        return ca.eagle_partition

    @staticmethod
    def _buckets(part, state, name):
        rows = [{"check": "filler", "state": "ok", "why": ""},
                {"check": name, "state": state, "why": "driven"}]
        p = part(rows)
        # the four lists eagle_partition returns, plus the identical tuple `_eagle_once` uses for
        # its own `unk` — counted here so the law covers the figure on the bottom bar too.
        return {k: len([r for r in p[k] if r.get("check") == name])
                for k in ("bad", "mine", "byDesign", "unk")}

    def test_BASELINE_a_made_up_state_lands_in_NO_bucket(self):
        """The case must be able to FAIL. If every string landed somewhere, the law below would be
        green no matter what this row returned. [[regression-guard]] §5"""
        part = self._partition()
        b = self._buckets(part, "corroborated-once", self.NAME)
        self.assertEqual(
            {"bad": 0, "mine": 0, "byDesign": 0, "unk": 0}, b,
            "a state nobody taught the eagle was bucketed anyway (%r), so the law below cannot "
            "distinguish a understood state from an invented one and is measuring nothing." % b)

    def test_the_four_known_states_are_bucketed_as_the_docstring_claims(self):
        """Pins the premise the ECHO choice rests on, so a future widening of the eagle's
        vocabulary shows up here rather than silently making this file's reasoning stale."""
        part = self._partition()
        cd = self._doctor()
        self.assertEqual(1, self._buckets(part, cd.MISSING, self.NAME)["mine"],
                         "a MISSING row on a MINE check no longer lands in `mine`")
        self.assertEqual(0, self._buckets(part, cd.MISSING, self.NAME)["bad"],
                         "a MISSING row on this check now bills HIM — it is in MINE precisely so "
                         "a look I failed to take never reaches the count he acts on")
        self.assertEqual(1, self._buckets(part, cd.UNKNOWN, self.NAME)["unk"],
                         "an UNKNOWN row is no longer counted as not-measured")
        self.assertEqual(1, self._buckets(part, cd.UNMEASURED, self.NAME)["unk"],
                         "an UNMEASURED row is no longer counted as not-measured")
        self.assertEqual({"bad": 0, "mine": 0, "byDesign": 0, "unk": 0},
                         self._buckets(part, cd.OK, self.NAME),
                         "an `ok` row is being counted somewhere, which would make this row red "
                         "on a healthy console")

    def test_the_state_an_ECHO_returns_is_one_the_eagle_can_actually_COUNT(self):
        """⚠ THE JOIN. Whatever the row decides for ECHO, the watchdog must see it. A state that
        reaches no bucket is folded into 'all clear across N check(s)' while control_ui still
        draws the row under WAITING ON YOU with the word 'UNKNOWN' — uncounted and shown as his,
        at the same time."""
        part = self._partition()
        state, say = self._drive(ECHO)
        b = self._buckets(part, state, self.NAME)
        self.assertGreater(
            sum(b.values()), 0,
            "the ECHO verdict is the state %r, and the eagle buckets it into NOTHING (%r). It is "
            "therefore folded into 'all clear' by every figure on the bottom bar, while the panel "
            "still draws it. This is the UNMEASURED-vs-unknown fold that stopped the site "
            "deploying for a day. say=%r" % (state, b, say))

    def test_an_ECHO_does_not_reach_the_count_HE_acts_on(self):
        """His #35 ruling, and the reason the eight historical echoes are not wolf-crying: asking
        the eye twice is my job, so this row may render red and must never enter `needsYou`."""
        part = self._partition()
        state, _say = self._drive(ECHO)
        b = self._buckets(part, state, self.NAME)
        self.assertEqual(
            0, b["bad"],
            "an ECHO now bills HIM (bad=%d). He cannot act on a look I did not take; this check "
            "is in console_doctor.MINE for exactly that reason." % b["bad"])


class HisRealLedgerDrivesItEndToEnd(_DrivesTheRow):
    """⚠ NOT A FIXTURE. Stubs only `current_version`; the REAL `agreement()` reads the REAL rows."""

    def _echo_version(self):
        L = self._ledger()
        if not os.path.exists(L.LEDGER_PATH):
            self.skipTest("no ledger on this machine — UNMEASURED, not a pass")
        rows = L._rows()
        if not rows:
            self.skipTest("the ledger is empty here — UNMEASURED, not a pass")
        seen = []
        for r in rows:
            v = L.norm_version(r.get("version") or "")
            if v and v not in seen:
                seen.append(v)
        for v in seen:
            if L.agreement(v).get("state") == "ECHO":
                return v
        self.skipTest("no version on this ledger reads ECHO, so the end-to-end path could not be "
                      "driven — UNMEASURED, not a pass")

    def test_a_REAL_echo_version_reaches_the_row_as_MISSING(self):
        cd = self._doctor()
        v = self._echo_version()
        L = self._ledger()
        old = (L.current_version, L.agreement_census)
        L.current_version = lambda *a, **k: v
        try:
            # the census is the live one too — only the "which version" answer is replaced.
            state, say = cd._check_the_second_eye_was_asked_twice()
        finally:
            L.current_version, L.agreement_census = old
        self.assertEqual(
            cd.MISSING, state,
            "%s is a genuine same-family pair on his own ledger and the row answers %r: %r"
            % (v, state, say))
        self.assertIn("not corroboration", say,
                      "the real ledger sentence did not travel to the row: %r" % say)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# Each `find` was measured to occur EXACTLY ONCE in tv/console_doctor.py, and each was executed
# and seen RED before this file was finished.
RED_PROOF = [
    {
        "why": "deleting the ECHO branch is #182's second half exactly: a MEASURED same-family "
               "pair falls through to `return UNKNOWN` and reaches his screen as CAN'T ASK.",
        "file": "tv/console_doctor.py",
        "find": "    if st == \"ECHO\":\n        return MISSING, ((a.get(\"say\") or",
        "replace": "    if st == \"ECHO_DISABLED\":\n        return MISSING, ((a.get(\"say\") or",
        "matches": 1,
    },
    {
        "why": "mapping ECHO to OK is the ORIGINAL #182 defect — 'the looks agree' reported for "
               "one witness asked twice — and an `ok` row is not even drawn on the panel.",
        "file": "tv/console_doctor.py",
        "find": "    if st == \"ECHO\":\n        return MISSING, ((a.get(\"say\") or",
        "replace": "    if st == \"ECHO\":\n        return OK, ((a.get(\"say\") or",
        "matches": 1,
    },
    {
        "why": "a fifth doctor state is counted by NO eagle bucket and folds into 'all clear', "
               "while control_ui still draws the row under WAITING ON YOU as 'UNKNOWN'. This is "
               "the choice the docstring's measurement exists to refuse.",
        "file": "tv/console_doctor.py",
        "find": "    if st == \"ECHO\":\n        return MISSING, ((a.get(\"say\") or",
        "replace": "    if st == \"ECHO\":\n        return \"echo\", ((a.get(\"say\") or",
        "matches": 1,
    },
    {
        "why": "dropping the action clause leaves a red row that names no next step. The row is "
               "in MINE; a complaint nobody can close is furniture.",
        "file": "tv/console_doctor.py",
        "find": "                         + \" · the half that is missing is MINE to take: one more look from a \"\n"
                "                           \"DIFFERENT model family, recorded as its own ledger row\"\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "widening the AGREE arm to swallow ECHO restores the false OK from the other "
               "direction and would make the cross-family baseline indistinguishable from an echo.",
        "file": "tv/console_doctor.py",
        "find": "    if st == \"AGREE\":\n        return OK, a.get(\"say\", \"the looks agree\") + tail",
        "replace": "    if st in (\"AGREE\", \"ECHO\"):\n        return OK, a.get(\"say\", \"the looks agree\") + tail",
        "matches": 1,
    },
]
