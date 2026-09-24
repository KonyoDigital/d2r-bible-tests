# -*- coding: utf-8 -*-
"""#182 — AGREEMENT DECIDED AGREE/DISAGREE/SINGLE AND NEVER READ WHO LOOKED.

MEASURED BY AST before anything was changed: neither the string `model` nor the string `family`
appeared ANYWHERE in the body of `second_eye_ledger.agreement()` — checked as ALL string
constants, so a subscript could not have been hiding one. The function counted verdicts and
nothing else.

MEASURED ON HIS LIVE LEDGER, 2026-09-23, 941 rows:

    family        xai 907 · openai 22 · anthropic 2 · UNKNOWN 10
    versions with 2+ reached looks carrying a verdict        29
      SAME-FAMILY (all xai)                                  18   ← one witness asked twice
      genuinely cross-family                                  3
      cannot be told apart (an unattributable model id)        8

Of those 18, EIGHT answered `AGREE`, and `console_doctor._check_the_second_eye_was_asked_twice`
maps AGREE -> OK with no family filter. So "the looks agree" has been reported to him for one
witness asked twice. The carved rule, twice over: *two derivations of one source agreeing is one
number wearing two names*, and *same-family agreement is ONE witness, not two*.

=== WHY ECHO IS A NEW WORD AND NOT A RED ONE ===
⚠⚠ The obvious fix — make a same-family pair report DISAGREE, or MISSING, or "no look" — turns
eighteen historical versions red on one day. Those were real looks that really did agree; they
simply never corroborated each other. A row that cries wolf gets silenced inside a week, and a
silenced row costs more than the defect it was shouting about. So the same-family case gets its
OWN state. The vocabulary already had room for a fifth word — SINGLE proves it — and ECHO
withdraws exactly one claim and no others.

=== WHY AN UNKNOWN FAMILY KEEPS ITS OLD STATE ===
⚠ family None/"" is UNKNOWN, and UNKNOWN is a first-class state here. It is never read as "some
other family" (that would manufacture corroboration) and never as "the same family" (that would
manufacture an echo). A single unattributable model id WITHDRAWS the ECHO claim, leaves the
verdict-driven state alone, and is COUNTED in the sentence a human reads — with its denominator:
how many looks there were, and how many of them could be attributed at all.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]

=== WHAT THIS FILE DRIVES ===
Every law below CALLS `agreement()` against a synthetic ledger and asserts the verdict it returns.
None of them asserts arithmetic about the rule, and none of them reads the source to decide
whether the rule is right — the two source reads that ARE here (the state vocabulary, and the fact
that the decision reads the model id) use the COMPILER, not a text scan.
"""
import ast
import inspect
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import second_eye_ledger as L  # noqa: E402


def _tmp():
    return os.path.join(tempfile.mkdtemp(), "ledger.jsonl")


def _names_used(code, _seen=None):
    """Every global/attribute name a code object references, INCLUDING its nested ones. -> set

    ⚠ A comprehension, a lambda and a closure each compile to their own code object hanging off
    `co_consts`. Reading only the outer `co_names` answers a different question than the one being
    asked, and answers it confidently.
    """
    out = set(code.co_names)
    for c in code.co_consts:
        if hasattr(c, "co_names"):
            out |= _names_used(c)
    return out


def _look(path, version, model, verdict="clean"):
    """One reached, evidence-bearing look. The ONLY axis the cases vary is the model id."""
    return L.record(version=version, model=model, verdict=verdict,
                    answer_head="the eye said something", path=path)


class ASameFamilyPairIsAnEcho(unittest.TestCase):
    """⚠⚠ THE CASE. 18 of his 29 multi-look versions land here."""

    def test_two_xai_looks_that_agree_report_ECHO(self):
        p = _tmp()
        _look(p, "v9001", "grok-4")
        _look(p, "v9001", "grok-3-mini")
        a = L.agreement("v9001", path=p)
        self.assertEqual(
            a["state"], "ECHO",
            "two looks from the SAME family, both clean, reported %r. That is one witness asked "
            "twice being presented as corroboration — the exact claim console_doctor turns into "
            "an OK lamp. got=%r" % (a["state"], a))
        self.assertIn(
            "not corroboration", a["say"],
            "the sentence a human reads does not say what is wrong with it: %r" % a["say"])
        self.assertIn(
            "xai", a["say"],
            "the say does not NAME the one family that looked, so a reader cannot check the "
            "claim: %r" % a["say"])

    def test_three_looks_from_one_family_are_still_ONE_witness(self):
        """Asking the same eye a third time does not buy a third opinion."""
        p = _tmp()
        for m in ("grok-4", "grok-4", "grok-3"):
            _look(p, "v9008", m)
        a = L.agreement("v9008", path=p)
        self.assertEqual(a["state"], "ECHO",
                         "three same-family looks reported %r — repetition read as confluence, "
                         "which is n inflated by asking again" % a["state"])
        self.assertEqual(a["looks"], 3, "the look count was lost: %r" % (a,))

    def test_the_AUTHOR_family_asked_twice_is_also_an_ECHO(self):
        """⚠ Two anthropic looks are the family that WROTE the code. `looked_at()` excludes them
        from the push gate; `agreement()` walks the rows directly, so the only thing standing
        between two author looks and an OK lamp is this state."""
        p = _tmp()
        _look(p, "v9009", "claude-opus-5")
        _look(p, "v9009", "claude-sonnet-4")
        a = L.agreement("v9009", path=p)
        self.assertEqual(a["state"], "ECHO",
                         "two looks from the family that authored the code reported %r"
                         % a["state"])


class ACrossFamilyAgreementIsStillAnAgreement(unittest.TestCase):
    """⚠⚠ THE BASELINE. Without it this is a guard that accuses everything, and a guard that
    accuses everything carries no information. [[regression-guard]] §5"""

    def test_xai_plus_openai_agreeing_reads_AGREE(self):
        p = _tmp()
        _look(p, "v9002", "grok-4")
        _look(p, "v9002", "gpt-5")
        a = L.agreement("v9002", path=p)
        self.assertEqual(
            a["state"], "AGREE",
            "a GENUINE cross-family agreement — the thing the whole second-eye lane exists to "
            "produce — reported %r. A rule that cannot tell two witnesses from one has not fixed "
            "the defect, it has replaced it with a louder one. got=%r" % (a["state"], a))
        self.assertNotIn(
            "not corroboration", a["say"],
            "two different families are being told they did not corroborate: %r" % a["say"])

    def test_the_two_shapes_do_not_share_a_state(self):
        """Driven side by side, because the whole finding is that they were indistinguishable."""
        p = _tmp()
        _look(p, "v9010", "grok-4")
        _look(p, "v9010", "grok-3")
        _look(p, "v9011", "grok-4")
        _look(p, "v9011", "gpt-5")
        same = L.agreement("v9010", path=p)["state"]
        cross = L.agreement("v9011", path=p)["state"]
        self.assertNotEqual(
            same, cross,
            "a same-family pair and a cross-family pair both report %r, which is the defect this "
            "file exists for stated in one line" % same)


class AnEchoNeverSwallowsAnInstrumentFinding(unittest.TestCase):
    """⚠ DISAGREE outranks ECHO. One family answering two ways about one payload is an unsteady
    INSTRUMENT, and that is the louder finding — measured on his ledger, 10 of the 29 multi-look
    versions are exactly that shape."""

    def test_two_xai_looks_that_differ_still_report_DISAGREE(self):
        p = _tmp()
        _look(p, "v9004", "grok-4", verdict="clean")
        _look(p, "v9004", "grok-3", verdict="findings")
        a = L.agreement("v9004", path=p)
        self.assertEqual(
            a["state"], "DISAGREE",
            "a same-family pair that DISAGREED was filed as %r. The new state ate an existing "
            "finding, which is a regression wearing a fix's clothes. got=%r" % (a["state"], a))
        self.assertIn("INSTRUMENT", a["say"],
                      "the say no longer names what the finding is about: %r" % a["say"])

    def test_a_cross_family_disagreement_is_unchanged(self):
        p = _tmp()
        _look(p, "v9003", "grok-4", verdict="clean")
        _look(p, "v9003", "gpt-5", verdict="findings")
        self.assertEqual(L.agreement("v9003", path=p)["state"], "DISAGREE")

    def test_ONE_look_is_still_SINGLE_and_never_ECHO(self):
        """⚠ One look is not an echo of anything. Collapsing it would silently re-label the
        largest population in the ledger."""
        p = _tmp()
        _look(p, "v9005", "grok-4")
        a = L.agreement("v9005", path=p)
        self.assertEqual(
            a["state"], "SINGLE",
            "a version looked at ONCE reported %r — a single look has nothing to echo" % a["state"])

    def test_no_look_at_all_is_still_NONE(self):
        p = _tmp()
        a = L.agreement("v9099", path=p)
        self.assertEqual(a["state"], "NONE", "an empty ledger reported %r" % a["state"])


class AnUnattributableLookIsUnknownNeverAssumed(unittest.TestCase):
    """⚠⚠ family None/"" is UNKNOWN. Never assumed cross-family, never assumed same."""

    def test_a_look_with_no_recognisable_family_BLOCKS_the_echo_claim(self):
        p = _tmp()
        _look(p, "v9006", "grok-4")
        _look(p, "v9006", "some-internal-runner")
        a = L.agreement("v9006", path=p)
        self.assertNotEqual(
            a["state"], "ECHO",
            "a pair containing ONE unattributable model id was declared a same-family echo. "
            "Nobody measured that: the unknown id could name any family, and assuming it names "
            "the same one manufactures the finding. [[unknown-stays-unknown]] got=%r" % (a,))
        self.assertIn(
            "UNKNOWN", a["say"],
            "the sentence does not say that one of the looks could not be attributed, so the "
            "state reads as settled when it is not: %r" % a["say"])

    def test_a_wholly_unattributable_pair_keeps_its_verdict_driven_state(self):
        """⚠ AND IT IS NOT QUIETLY DOWNGRADED EITHER. Ten of his 941 rows carry no recognisable
        family; moving them off AGREE would assume they are one witness, which is the mirror of
        the defect. The honest move is to keep the state and SAY the provenance is unknown."""
        p = _tmp()
        _look(p, "v9007", "")
        _look(p, "v9007", "")
        a = L.agreement("v9007", path=p)
        self.assertEqual(
            a["state"], "AGREE",
            "two unattributable looks were moved off AGREE to %r. That assumes they are the same "
            "family, which nobody measured — and tv/test_two_looks_are_two_rows.py pins this "
            "exact shape as AGREE." % a["state"])
        self.assertIn("UNKNOWN", a["say"],
                      "an AGREE where NOBODY knows who looked reads as settled: %r" % a["say"])

    def test_the_say_carries_its_denominator(self):
        """⚠ how many looks, and how many of them could be attributed at all."""
        p = _tmp()
        _look(p, "v9012", "grok-4")
        _look(p, "v9012", "mystery-box")
        a = L.agreement("v9012", path=p)
        self.assertIn("2 look(s)", a["say"],
                      "the say does not state how many looks it is talking about: %r" % a["say"])
        self.assertIn("1 naming a family", a["say"],
                      "the say does not state how many of the looks could be attributed, so the "
                      "reader cannot size the claim: %r" % a["say"])
        self.assertEqual(a.get("familyKnown"), 1, "got=%r" % (a,))
        self.assertEqual(a.get("familyUnknown"), 1, "got=%r" % (a,))


class TheDecisionReadsTheModelIdNotTheStoredField(unittest.TestCase):
    """⚠⚠ v2143.1's founding rule, applied to the new axis. A hand-written row claiming
    family:"xai" once satisfied the gate this ledger exists to make forgery-proof."""

    def test_a_forged_family_field_cannot_manufacture_a_cross_family_pair(self):
        p = _tmp()
        _look(p, "v9013", "grok-4")
        _look(p, "v9013", "grok-3")
        # hand-write a third row whose stored `family` lies about its model id
        import json
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"version": "v9013", "model": "grok-2", "family": "openai",
                                 "reached": True, "verdict": "clean",
                                 "answerHead": "x"}) + "\n")
        a = L.agreement("v9013", path=p)
        self.assertEqual(
            a["state"], "ECHO",
            "a row whose stored `family` field says openai while its model id says grok bought a "
            "cross-family agreement. The stored field is evidence for a human; the DECISION must "
            "come from family_of(). got=%r" % (a,))
        self.assertEqual(a.get("families"), ["xai"],
                         "the forged family reached the reported family list: %r" % (a,))

    def test_the_function_actually_calls_family_of(self):
        """THE COMPILER, NOT A TEXT SCAN. The defect was measured by AST — no `model`, no
        `family` anywhere in the body — so the repair is checked the same way.

        ⚠ AND THE FIRST CUT OF THIS PROBE WAS THE THING THAT WAS BROKEN, not the code. It read
        `L.agreement.__code__.co_names` and came back RED against a function that demonstrably
        calls family_of: on this interpreter a list COMPREHENSION compiles to its own nested code
        object, so the name it calls lives in `co_consts[i].co_names` and never in the outer
        function's. A one-level read would have declared the fix missing — and, worse, would have
        gone green the day someone rewrote the comprehension as a loop, measuring the syntax
        rather than the call. Walk the nest. [[feedback-suspect-the-instrument]]
        """
        names = _names_used(L.agreement.__code__)
        self.assertIn(
            "family_of", names,
            "agreement() does not reference family_of anywhere, at any nesting depth, so whatever "
            "it is deciding, it is not deciding it from who looked. names=%r" % (sorted(names),))


class TheVocabularyIsDeclared(unittest.TestCase):
    """⚠ A state a reader has never heard of is the unjoined end this repo keeps paying for."""

    def test_ECHO_is_in_the_declared_state_set(self):
        self.assertIn("ECHO", L.AGREEMENT_STATES)

    def test_every_state_the_function_can_RETURN_is_declared(self):
        """Read off the function's own AST, so a sixth state added later and forgotten here goes
        red instead of travelling unannounced to console_doctor."""
        tree = ast.parse(inspect.getsource(L.agreement))
        found = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "state"
                        and isinstance(v, ast.Constant) and isinstance(v.value, str)):
                    found.add(v.value)
        self.assertTrue(found, "no literal state could be read out of agreement()'s AST at all")
        self.assertEqual(
            found, set(L.AGREEMENT_STATES),
            "agreement() can return %r while AGREEMENT_STATES declares %r. A caller reads the "
            "declared set; a state missing from it reaches that caller unannounced."
            % (sorted(found), sorted(L.AGREEMENT_STATES)))


class TheJoinToTheOrganThatReadsIt(unittest.TestCase):
    """⚠⚠ THE HALF THAT IS EASY TO FORGET. A new state that its only reader still maps to OK has
    changed nothing at all. console_doctor is NOT edited by this law — it is DRIVEN."""

    def _doctor(self):
        try:
            import console_doctor as cd
        except Exception as e:                      # pragma: no cover - reported, never assumed
            self.skipTest("console_doctor will not import here (%s: %s) — the join could not be "
                          "measured, which is UNKNOWN and not a pass"
                          % (type(e).__name__, str(e)[:120]))
        return cd

    def test_an_ECHO_never_reaches_him_as_OK(self):
        cd = self._doctor()
        echo = {"version": "v9001", "looks": 2, "empty": 0, "state": "ECHO",
                "verdicts": ["clean", "clean"], "partial": 0, "reachUnknown": 0, "cut": 0,
                "families": ["xai"], "familyKnown": 2, "familyUnknown": 0, "sameFamily": True,
                "say": "2 looks say the same thing and every one of them is xai — that is ONE "
                       "witness asked 2 times, not corroboration."}
        old = (L.current_version, L.agreement, L.agreement_census)
        L.current_version = lambda *a, **k: "v9001"
        L.agreement = lambda v, path=None: dict(echo)
        L.agreement_census = lambda *a, **k: {"say": "census stub"}
        try:
            state, say = cd._check_the_second_eye_was_asked_twice()
        finally:
            L.current_version, L.agreement, L.agreement_census = old
        self.assertNotEqual(
            state, cd.OK,
            "the organ reports OK — 'the looks agree' — for one witness asked twice. That is the "
            "defect #182 names, surviving the fix because the reader was never taught the new "
            "word. say=%r" % say)
        self.assertIn(
            "not corroboration", say,
            "the doctor row does not carry the ledger's own explanation, so he is shown a lamp "
            "with no reason: %r" % say)


class HisRealLedgerIsDrivenNotAssumed(unittest.TestCase):
    """BEHAVIOURAL, against the file on this machine, and honest when it is not here."""

    def _versions(self):
        if not os.path.exists(L.LEDGER_PATH):
            self.skipTest("no ledger on this machine")
        rows = L._rows()
        if len(rows) < 50:
            self.skipTest("only %d rows here; too few to say anything" % len(rows))
        seen = {}
        for r in rows:
            v = L.norm_version(r.get("version") or "")
            if v:
                seen.setdefault(v, []).append(r)
        return seen

    def test_ECHO_is_REACHABLE_on_his_own_data(self):
        """⚠ A state nothing can ever reach is a branch that never runs — the 0.22 threshold over
        a signal maxing at 0.133, one file away."""
        seen = self._versions()
        states = {}
        for v, rs in seen.items():
            keep = [r for r in rs
                    if r.get("reached") is not False and str(r.get("verdict") or "").strip()]
            if len(keep) >= 2:
                states[v] = L.agreement(v)["state"]
        if not states:
            self.skipTest("no version on this machine carries two reached looks with a verdict")
        self.assertIn(
            "ECHO", set(states.values()),
            "not one of the %d multi-look versions on his ledger reads ECHO. Measured 2026-09-23 "
            "the honest figure was 18 of 29, so either the data changed shape or the branch "
            "cannot be reached. states=%r" % (len(states), sorted(set(states.values()))))

    def test_every_ECHO_is_self_consistent(self):
        """An ECHO must be able to show its work: one family named, nothing unattributable, and
        every verdict the same. Otherwise the label is a guess."""
        seen = self._versions()
        bad = []
        for v in sorted(seen):
            a = L.agreement(v)
            if a["state"] != "ECHO":
                continue
            if (len(a.get("families") or []) != 1 or a.get("familyUnknown") != 0
                    or len(set(a.get("verdicts") or [])) != 1):
                bad.append((v, a.get("families"), a.get("familyUnknown"), a.get("verdicts")))
        self.assertEqual([], bad,
                         "%d version(s) are labelled ECHO without satisfying what ECHO claims: %r"
                         % (len(bad), bad[:4]))

    def test_the_census_reports_the_echo_count_beside_the_disagreement_count(self):
        """⚠ Kept apart: one is an unsteady instrument, the other a corroboration never taken.
        Folding them together would hide both. [[zero-needs-a-denominator]]"""
        if not os.path.exists(L.LEDGER_PATH):
            self.skipTest("no ledger on this machine")
        c = L.agreement_census()
        self.assertIn("echoed", c, "the census cannot say how many pairs are one eye asked twice")
        self.assertIn("SAME-FAMILY", c["say"],
                      "the census sentence never mentions the echo population: %r" % c["say"])
        self.assertIn("UPPER BOUND", c["say"],
                      "the census lost its own upper-bound qualification")
        self.assertLessEqual(
            c["echoed"] + c["disagreed"], c["recent"],
            "more recent versions are echoes-plus-disagreements than were examined, so the "
            "denominator is wrong: %r" % (c,))


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# Each `find` was measured to occur EXACTLY ONCE in tv/second_eye_ledger.py, and each one was
# executed and seen RED before this file was finished. The question each answers is whether
# deleting that text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": "dropping the same-family test puts every pair back on AGREE, which is #182 "
               "exactly: eighteen of his twenty-nine multi-look versions reporting that one "
               "witness asked twice corroborated itself.",
        "file": "tv/second_eye_ledger.py",
        "find": "    _same_family = (len(_spoke) >= 2 and len(_distinct) == 1 and _fam_unknown == 0)",
        "replace": "    _same_family = False",
        "matches": 1,
    },
    {
        "why": "letting an unattributable model id count towards the echo claim assumes the "
               "unknown look came from the SAME family. Nobody measured that, and it is the "
               "mirror of the defect being fixed. [[unknown-stays-unknown]]",
        "file": "tv/second_eye_ledger.py",
        "find": "    _same_family = (len(_spoke) >= 2 and len(_distinct) == 1 and _fam_unknown == 0)",
        "replace": "    _same_family = (len(_spoke) >= 2 and len(_distinct) == 1)",
        "matches": 1,
    },
    {
        "why": "reading the row's own `family` field instead of re-deriving it from the model id "
               "is v2143.1's forgery, one axis over: a hand-written line claiming another family "
               "buys a cross-family agreement it never earned.",
        "file": "tv/second_eye_ledger.py",
        "find": "    _fams = [family_of(r.get(\"model\")) for r in _spoke]",
        "replace": "    _fams = [r.get(\"family\") for r in _spoke]",
        "matches": 1,
    },
]
