#!/usr/bin/env python3
"""Guards for the self-arming lock. Every case asserts a REFUSAL as well as a pass.

The thing being replaced is a human flipping `_PRUNE_SAFE_TO_RUN` by hand, so the failure that
matters is not "it refused when it should have opened" — it is "IT OPENED WITHOUT EARNING IT".
Every test here is pointed at that direction.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import self_arming as SA


class _Ledger(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="arm-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.p = os.path.join(self.root, "proofs.jsonl")
        self._old = SA.LEDGER
        SA.LEDGER = self.p
        self.addCleanup(setattr, SA, "LEDGER", self._old)

    def put(self, lock, kind, refused, n=1):
        with io.open(self.p, "a", encoding="utf-8") as fh:
            for _ in range(n):
                fh.write(json.dumps({"lock": lock, "kind": kind,
                                     "refused": bool(refused), "ts": 0}) + "\n")


class TestUnprovenIsNotFailing(_Ledger):
    """The distinction the whole mechanism rests on. If these two collapse, a lock either opens on
    silence or paints its own newest surfaces red — and both get the mechanism ignored."""

    def test_no_proofs_is_UNPROVEN_and_carries_NO_score(self):
        s = SA.score("vault.apply")
        self.assertEqual(s["state"], SA.UNPROVEN)
        self.assertIsNone(s["wilson"],
                          "n=0 rendered as a NUMBER. 'nobody looked' would then be indistinguishable "
                          "from 'it scored zero', and a surface could be reported as failing when "
                          "it has simply never been tested. [[unknown-stays-unknown]]")
        self.assertIn("not a failure", s["why"])

    def test_UNPROVEN_still_does_not_permit_the_action(self):
        ok, why = SA.may("vault.apply")
        self.assertFalse(ok, "an untested surface was permitted to act")


class TestTheDenominatorIsSABOTAGES(_Ledger):
    """★ THE ONE THING THAT WOULD MAKE THIS A LIE. [[heart-first]] §5 — an invariant that always
    agrees may be perfect or INERT, and those are indistinguishable. A lock fed by an agreement
    rate opens BECAUSE nobody tested it, which is the exact failure it exists to prevent."""

    def test_a_wall_of_agreements_with_no_refusal_NEVER_opens(self):
        # 40 sabotages, and the guard failed to refuse every single time
        self.put("vault.sweep_start", "sabotage", False, n=40)
        s = SA.score("vault.sweep_start")
        self.assertEqual(s["state"], SA.LOCKED)
        self.assertEqual(s["k"], 0)
        self.assertEqual(s["n"], 40)
        self.assertEqual(s["wilson"], 0.0,
                         "40 attempts and 0 refusals must score 0.0 — this is the INERT guard, and "
                         "it must never be mistaken for an untested one")

    def test_a_refusal_is_what_counts_as_success(self):
        self.put("vault.sweep_start", "sabotage", True, n=10)
        s = SA.score("vault.sweep_start")
        self.assertEqual(s["k"], 10)
        self.assertGreater(s["wilson"], 0.72,
                           "10/10 refusals should reach the published 0.722 reference")


class TestWilsonAndConfluenceBOTH(_Ledger):
    """confidence.py's own words: 'The two run TOGETHER or neither means anything.' Wilson counts
    how many looks agreed, never whether they were INDEPENDENT — four re-runs of one sabotage by
    one harness is one proof wearing four hats."""

    def test_a_perfect_score_from_ONE_kind_is_still_LOCKED(self):
        self.put("vault.apply", "sabotage", True, n=30)      # wilson ~0.88, one kind = 1.0
        self.put("vault.sweep_start", "sabotage", True, n=30)
        s = SA.score("vault.apply")
        self.assertGreater(s["wilson"], s["bar"], "precondition: the score itself must clear")
        self.assertEqual(s["state"], SA.LOCKED,
                         "30 identical proofs opened the lock. Evidence that is all one kind is "
                         "one look wearing thirty hats.")
        self.assertIn("too alike", s["why"])

    def test_two_INDEPENDENT_kinds_open_it(self):
        self.put("vault.sweep_start", "sabotage", True, n=20)
        self.put("vault.apply", "sabotage", True, n=15)
        self.put("vault.apply", "cross-family", True, n=5)
        s = SA.score("vault.apply")
        self.assertEqual(s["state"], SA.OPEN, s["why"])
        ok, why = SA.may("vault.apply")
        self.assertTrue(ok, why)

    def test_an_UNWEIGHTED_kind_is_worth_zero_not_a_default(self):
        """A kind nobody has weighted is a kind nobody has thought about."""
        self.put("vault.sweep_start", "sabotage", True, n=20)
        self.put("vault.apply", "sabotage", True, n=20)
        self.put("vault.apply", "vibes", True, n=20)
        s = SA.score("vault.apply")
        self.assertEqual(s["state"], SA.LOCKED,
                         "an unrecognised proof kind paid as if someone had weighted it")


class TestHisOrderIsEnforced(_Ledger):
    """He gave a chain: printer+reels -> theatre+shelf -> routing -> the deleter. Proving the
    deleter in isolation proves nothing about the river feeding it."""

    def test_the_deleter_cannot_open_before_its_prerequisites(self):
        # a flawless record for the prune itself, and NOTHING upstream
        self.put("prune.arm", "sabotage", True, n=60)
        self.put("prune.arm", "cross-family", True, n=20)
        self.put("prune.arm", "live", True, n=20)
        ok, why = SA.may("prune.arm")
        self.assertFalse(ok, "the deleter armed itself with no proof of the lanes that feed it")
        self.assertIn("blocked upstream", why)
        self.assertIn("vault.sweep_start", why,
                      "the refusal must NAME the unmet prerequisite, or a high score reads as "
                      "'nearly there' when the real blocker is somewhere else entirely")


class TestItFailsCLOSED(_Ledger):
    """An unreadable proof queue is UNKNOWN, and UNKNOWN is never permission."""

    def test_an_unparseable_row_is_UNKNOWN_not_empty(self):
        self.put("vault.sweep_start", "sabotage", True, n=5)
        with io.open(self.p, "a", encoding="utf-8") as fh:
            fh.write("{not json\n")
        s = SA.score("vault.sweep_start")
        self.assertEqual(s["state"], SA.UNKNOWN,
                         "a hole in the evidence was read as a blank one — the 5 good rows would "
                         "then be the whole record, which is a smaller claim than the truth")
        ok, why = SA.may("vault.sweep_start")
        self.assertFalse(ok)
        self.assertIn("fails CLOSED", why)

    def test_an_undeclared_lock_is_never_permitted(self):
        ok, why = SA.may("something.nobody.declared")
        self.assertFalse(ok)
        self.assertIn("never permitted", why)


class TestThereIsNoHandOverride(unittest.TestCase):
    """The whole point is that Konyo stops being the arming mechanism. A `force` parameter would
    quietly restore the thing this replaces."""

    def test_may_takes_exactly_one_argument(self):
        import inspect
        sig = inspect.signature(SA.may)
        self.assertEqual(list(sig.parameters), ["lock"],
                         "may() grew a parameter. If one of them is an override, the lock is "
                         "decorative and the hand-arming is back.")

    def test_the_module_never_writes_an_unlock_flag(self):
        """⚠ THIS GUARD FAILED ON PROSE FIRST, AND THE LAW WAS NEVER WRONG.

        The first cut stripped `#` comments and asserted `_PRUNE_SAFE_TO_RUN` was absent. The
        module's own DOCSTRING says "This replaces `_PRUNE_SAFE_TO_RUN`" — so the guard went red
        on the sentence explaining the fix, which is [[source-reading-guard]] §4 exactly, and the
        third time that class has cost a wrong reading today. A `#`-stripper does not strip
        docstrings.

        Ask the COMPILER, not the text (§1): a name in a docstring is not in the AST. This also
        makes the guard STRONGER — it now catches `setattr(m, "_PRUNE_SAFE_TO_RUN", True)`-shaped
        writes that a substring search would miss entirely.
        """
        import ast, inspect
        tree = ast.parse(inspect.getsource(SA))

        FORBIDDEN_NAMES = {"_PRUNE_SAFE_TO_RUN", "SAFE_TO_RUN"}
        FORBIDDEN_CALLS = {"remove", "unlink", "rmtree", "replace", "setattr"}
        bad = []
        for node in ast.walk(tree):
            # writing a flag — assignment, augmented assignment, or an attribute set
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in tgts:
                    nm = getattr(t, "id", None) or getattr(t, "attr", None)
                    if nm in FORBIDDEN_NAMES:
                        bad.append("writes %s at line %d" % (nm, node.lineno))
            # destructive or reflective calls
            if isinstance(node, ast.Call):
                fn = node.func
                nm = getattr(fn, "attr", None) or getattr(fn, "id", None)
                if nm in FORBIDDEN_CALLS:
                    bad.append("calls %s() at line %d" % (nm, node.lineno))
        self.assertEqual(bad, [],
                         "the lock module ACTS instead of only deciding: %s. It DECIDES and "
                         "REPORTS; anything that flips a flag or deletes is a second arming path "
                         "and restores the hand-arming this replaces." % "; ".join(bad))

    def test_it_calls_confidence_rather_than_restating_the_maths(self):
        import inspect
        src = inspect.getsource(SA)
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn("from confidence import", code)
        self.assertNotIn("def wilson_lower", code,
                         "a second copy of the Wilson maths. [[copy-drift]] — two copies of one "
                         "safety routine diverge, and only one of them gets tuned.")


class TestBankingCannotOpenALockByBeingLookedAt(unittest.TestCase):
    """★ A2. THE DEFECT THIS EXISTS TO PREVENT IS THE WORST ONE AVAILABLE HERE.

    record() had ZERO callers, so every lock sat at n=0 UNPROVEN by construction however many
    sabotages actually ran. hover_wilson already scores the autopilot's four claims on real
    sabotage attempts and threw every result away.

    But score() counts ROWS (n = len(mine)), and hover_wilson hands out a rolling (n, k) AGGREGATE.
    Append that on each run and n goes 4, 8, 12, 16 — and the lock OPENS BECAUSE SOMEBODY LOOKED AT
    IT. On prune.arm, which deletes footage with no undo, that is the most expensive defect this
    repo could ship. Every case below defends one edge of that.
    """

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.led = os.path.join(self.tmp, "ledger.jsonl")
        os.environ["TV_SELF_ARMING_LEDGER"] = self.led
        self.addCleanup(os.environ.pop, "TV_SELF_ARMING_LEDGER", None)

    def test_banking_TWICE_does_not_double_the_evidence(self):
        """The load-bearing one. Run the harness ten times; the lock must be exactly as proven as
        it was after the first run, because the same four sabotages were attempted each time."""
        for _ in range(10):
            SA.bank("miniauto.run", "sabotage", "hover_wilson", n=4, k=4, note="four claims")
        sc = SA.score("miniauto.run")
        self.assertEqual((sc["k"], sc["n"]), (4, 4),
                         "ten reads of the same evidence produced %d/%d. A lock that grows stronger "
                         "by being looked at is not a lock." % (sc["k"], sc["n"]))

    def test_a_LATER_bank_from_the_same_source_REPLACES_the_earlier_one(self):
        """A harness that gains a fifth sabotage must be able to say so — and one that loses a
        sabotage must be able to say that too, downward."""
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=4, k=4)
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=5, k=4)
        sc = SA.score("miniauto.run")
        self.assertEqual((sc["k"], sc["n"]), (4, 5))
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=2, k=1)
        sc = SA.score("miniauto.run")
        self.assertEqual((sc["k"], sc["n"]), (1, 2),
                         "evidence could not go DOWN. A harness whose sabotages started leaking "
                         "must be able to weaken its own lock, or the ledger is a ratchet")

    def test_an_UNDECLARED_source_is_refused(self):
        with self.assertRaises(ValueError) as cm:
            SA.bank("prune.arm", "sabotage", "some_new_harness", n=99, k=99)
        self.assertIn("not a declared evidence source", str(cm.exception))

    def test_a_source_may_not_bank_where_it_does_NOT_prove(self):
        """render_check proves the RENDER GATE. It says nothing about whether footage may be
        deleted, and prune.arm has no undo."""
        with self.assertRaises(ValueError) as cm:
            SA.bank("prune.arm", "sabotage", "render_check", n=40, k=40)
        self.assertIn("does not prove", str(cm.exception))
        self.assertEqual(SA.score("prune.arm")["n"], 0,
                         "the refusal still wrote a row — a refusal that banks anyway is not a "
                         "refusal")

    def test_more_refusals_than_attempts_is_an_INSTRUMENT_FAULT_not_a_great_score(self):
        with self.assertRaises(ValueError):
            SA.bank("miniauto.run", "sabotage", "hover_wilson", n=3, k=7)

    def test_single_attempts_still_ACCUMULATE_and_mix_with_aggregates(self):
        """record() rows are events and must keep adding up; only banked aggregates fold. If this
        broke, every row ever written by record() would silently change meaning."""
        SA.record("miniauto.run", "fixture", True)
        SA.record("miniauto.run", "fixture", True)
        SA.record("miniauto.run", "fixture", False)
        sc = SA.score("miniauto.run")
        self.assertEqual((sc["k"], sc["n"]), (2, 3))
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=4, k=4)
        sc = SA.score("miniauto.run")
        self.assertEqual((sc["k"], sc["n"]), (6, 7),
                         "aggregates and single attempts did not add up together")

    def test_a_kind_counts_only_where_something_was_actually_REFUSED(self):
        """confluence() weighs KINDS. A kind under which every sabotage LEAKED is not independent
        corroboration — it is a second witness saying nothing."""
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=6, k=0)
        self.assertEqual(SA.score("miniauto.run")["kinds"], [],
                         "a kind that refused nothing was counted as evidence")

    def test_an_UNDECLARED_TIER_is_refused_rather_than_silently_scoring_zero(self):
        """FOUND ON THE FIRST REAL RUN, and it is the quiet kind. `kind` is the TIER confluence
        weighs, not a free label. Banking the four hover claims under their own names gave kinds
        ['coordinate', 'read', 'slot'] scoring 0.00 against a bar of 1.00 — so the lock stayed shut
        FOREVER while its Wilson figure read 0.935 and every number on the page looked healthy.
        A lock nobody can explain is worse than a loud refusal."""
        with self.assertRaises(ValueError) as cm:
            SA.bank("miniauto.run", "coordinate", "hover_wilson", n=48, k=48)
        self.assertIn("not a declared evidence tier", str(cm.exception))
        self.assertEqual(SA.score("miniauto.run")["n"], 0, "the refusal still wrote a row")

    def test_two_claims_sharing_a_TIER_do_not_fold_into_one(self):
        """ALSO FOUND ON THE FIRST REAL RUN. All four hover claims are `sabotage` tier, so
        (lock, kind, src) is the SAME key for every one of them. Folding on that kept only the last
        row written — coordinate's 48/48 was thrown away and slot's 2/2 kept. n fell from 55 to 2
        and nothing said so. `ref` is what keeps them apart."""
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=48, k=48, ref="coordinate")
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=5, k=5, ref="read")
        SA.bank("miniauto.run", "sabotage", "hover_wilson", n=2, k=2, ref="slot")
        sc = SA.score("miniauto.run")
        self.assertEqual((sc["k"], sc["n"]), (55, 55),
                         "three distinct sabotage families collapsed to %d/%d — they share a tier "
                         "and were folded into one another" % (sc["k"], sc["n"]))
        # and re-running the same three still must not double them
        for _ in range(4):
            SA.bank("miniauto.run", "sabotage", "hover_wilson", n=48, k=48, ref="coordinate")
        self.assertEqual(SA.score("miniauto.run")["n"], 55)


class AnUnprovableLockSaysSoAndTheClaimIsCHECKED(unittest.TestCase):
    """⚠⚠ A LOCK THAT DECLARES ITSELF UNPROVABLE IS MAKING A CLAIM ABOUT ANOTHER FILE.

    `vault.forget` sits at n=0 forever because `vault_forget()` has NO refusal path — seven lines,
    one return, always ok — so there is no state in which it must say no and nothing a sabotage
    could attempt. That is deliberate (its docstring: an optimisation he cannot clear is a cage),
    and it is why the panel must not imply a harness is merely missing.

    But "this door has no refusal path" is a statement about `control_app.vault_forget`, sitting in
    a different file, and the day someone gives it one the declaration becomes a LIE that reads as
    documentation — a right sentence under a word that stopped being true. So it is CHECKED, by
    structure rather than by prose. [[label-outlived-referent]] [[source-reading-guard]]
    """

    def _fn(self, name):
        import ast
        here = os.path.dirname(os.path.abspath(__file__))
        src = io.open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None

    def test_every_unprovable_lock_names_a_function_that_really_cannot_refuse(self):
        import ast
        declared = [(k, v) for k, v in SA.LOCKS.items() if v.get("unprovable")]
        self.assertTrue(declared, "no lock declares itself unprovable — has vault.forget changed?")
        for lock, spec in declared:
            fname = spec.get("unprovable_fn")
            self.assertTrue(
                fname, "%s claims it cannot be proven but names no function, so the claim cannot "
                       "be checked and will rot silently" % lock)
            fn = self._fn(fname)
            self.assertTrue(fn, "%s names %s(), which no longer exists in control_app"
                                % (lock, fname))
            returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
            raises = [n for n in ast.walk(fn) if isinstance(n, ast.Raise)]
            self.assertEqual(
                len(returns), 1,
                "%s() now has %d return statements. %s is declared UNPROVABLE on the grounds that "
                "the door has no refusal path, so a second exit means either it CAN now refuse — "
                "in which case it is provable by sabotage and the declaration is a lie — or the "
                "function grew a shape nobody re-checked." % (fname, len(returns), lock))
            self.assertFalse(
                raises,
                "%s() can now raise, which is a refusal path by another name. %s claims it has "
                "none." % (fname, lock))
            # and it must not report failure through its payload either
            for node in ast.walk(fn):
                if isinstance(node, ast.Constant) and node.value is False:
                    parent_keys = [k for k in ast.walk(fn) if isinstance(k, ast.Dict)]
                    for d in parent_keys:
                        for key, val in zip(d.keys, d.values):
                            if (isinstance(key, ast.Constant) and key.value == "ok"
                                    and isinstance(val, ast.Constant) and val.value is False):
                                self.fail("%s() can return ok:False — that IS a refusal, so %s is "
                                          "provable and must not claim otherwise" % (fname, lock))

    def test_the_field_SURVIVES_the_status_trim(self):
        """⚠ THE TRIM IS A WHITELIST, AND A NEW FIELD IS DROPPED BY DEFAULT.

        `_self_arming_state()` rebuilds each lock row with a fixed set of keys "trimmed for a
        poll". `provable` was not in it, so the report carried the distinction and the BADGE never
        received it — measured on a freshly started console: the new `why` arrived and
        `provable` came back None. Built on both ends and joined on neither, which is this repo's
        most repeated defect. [[the-unjoined-end]]
        """
        import ast
        here = os.path.dirname(os.path.abspath(__file__))
        src = io.open(os.path.join(here, "control_app.py"), encoding="utf-8").read()
        fn = None
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.FunctionDef) and node.name == "_self_arming_state":
                fn = node
        self.assertTrue(fn, "_self_arming_state is gone — who publishes the locks now?")
        keys = set()
        for d in [n for n in ast.walk(fn) if isinstance(n, ast.Dict)]:
            for k in d.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
        for need in ("state", "why", "provable", "n"):
            self.assertIn(need, keys,
                          "the status trim drops %r, so the console cannot render it however "
                          "correct self_arming.report() is" % need)

    def test_the_RENDERER_tells_them_apart_too(self):
        """The last joint. report() -> _self_arming_state() -> the badge; break any one and the
        distinction dies silently at that step. It died at the third: the renderer printed
        'untested' whenever n===0, so an unprovable door and an untested one read identically on
        screen however correct the two layers behind them were. [[the-unjoined-end]]"""
        here = os.path.dirname(os.path.abspath(__file__))
        ui = io.open(os.path.join(here, "control_ui.html"), encoding="utf-8").read()
        self.assertIn(
            "provable === false", ui,
            "the console's lock renderer never reads `provable`, so the field is published and "
            "unused — plumbing with no tap, and the badge still says 'untested' for a door that "
            "can never be sabotaged")

    def test_the_panel_tells_UNTESTED_apart_from_UNPROVABLE(self):
        """Both are n=0 and neither is a failure, but only one is waiting on work."""
        rows = {r["lock"]: r for r in SA.report()["locks"]}
        forget = rows.get("vault.forget")
        self.assertTrue(forget, "vault.forget is no longer reported")
        self.assertEqual(forget["state"], SA.UNPROVEN)
        self.assertIs(forget.get("provable"), False,
                      "vault.forget is reported as still-provable, so the panel is telling him a "
                      "harness is owed for a door that can never be sabotaged")
        self.assertIn("cannot be proven", forget["why"])
        self.assertNotIn(
            "no sabotage has been attempted", forget["why"],
            "vault.forget still uses the nobody-has-tested-it sentence, which reads as a missing "
            "harness rather than a door with no refusal path")
        # a lock with real evidence must NOT be mislabelled
        for name, r in rows.items():
            if r.get("n"):
                self.assertNotIn("provable", [k for k in r if k == "provable" and r[k] is False],
                                 "%s has evidence and is marked unprovable" % name)



class TheLedgerIsCheckedONREADNotOnlyOnWrite(unittest.TestCase):
    """v2581 — bank()'s validations guarded the DOOR and not the ROOM.

    Every check bank() makes lived only in bank(). Anything else that appended a line to the
    ledger — a stray script, a hand edit, a half-finished writer — bypassed all of them, and
    score() then read it as evidence. Worse, score() DEFAULTS a missing count:
    `int(r.get("n", 1) or 0)` and `int(r.get("k", 1 if r.get("refused") else 0) or 0)`, so a
    three-key row {lock, kind, refused: true} was silently worth n=1 k=1 of whatever tier it
    named — and `kinds` is a SET, so one such row buys that tier's whole confluence weight.

    ⚠ Measured against his 51 real rows BEFORE this shipped: zero would fail. It costs nothing
    that is honest.

    ⚠ A bad row fails the WHOLE read, as an unparseable line already does. Dropping just the bad
    row would let a forgery be silently discarded while the rest scored on, and the lock would
    open on a ledger nobody could see had been edited. UNKNOWN is LOCKED, so this fails closed.
    """

    def _ledger(self, *rows):
        d = tempfile.mkdtemp(prefix="sa_read_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, "led.jsonl")
        with io.open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return p

    def _good(self, **kw):
        row = {"lock": "prune.arm", "kind": "sabotage", "src": "prune_wilson",
               "ref": "offspelling", "n": 10, "k": 10, "refused": True,
               "ts": int(time.time() * 1000)}
        row.update(kw)
        return row

    def _read(self, path):
        was = os.environ.get("TV_SELF_ARMING_LEDGER")
        try:
            os.environ["TV_SELF_ARMING_LEDGER"] = path
            return SA._rows()
        finally:
            if was is None:
                os.environ.pop("TV_SELF_ARMING_LEDGER", None)
            else:
                os.environ["TV_SELF_ARMING_LEDGER"] = was

    def test_an_honest_row_still_reads(self):
        """BASELINE — or the check bought its safety by refusing everything."""
        rows, why = self._read(self._ledger(self._good()))
        self.assertEqual(len(rows or []), 1, why)

    def test_the_three_key_row_score_would_have_DEFAULTED_is_refused(self):
        """The forgery that costs nothing to write: no n, no k, no src."""
        rows, why = self._read(self._ledger(
            self._good(), {"lock": "prune.arm", "kind": "live", "refused": True}))
        self.assertIsNone(rows, "a row with no counts and no source was accepted as evidence")
        self.assertIn("could not have been banked", why)

    def test_every_forgery_class_is_refused(self):
        for label, row in (
                ("an undeclared source", self._good(src="my_own_harness")),
                ("a source proving another lock", self._good(lock="miniauto.run")),
                ("an unweighted kind", self._good(kind="vibes")),
                ("k greater than n", self._good(n=5, k=9)),
                ("a boolean count", self._good(n=True, k=True)),
                ("a timestamp in the future",
                 self._good(ts=int((time.time() + 86400) * 1000))),
        ):
            rows, why = self._read(self._ledger(self._good(), row))
            self.assertIsNone(rows, "%s was accepted: %s" % (label, why))

    def test_a_refused_read_makes_may_say_NO(self):
        """UNKNOWN must be LOCKED — a ledger that cannot be trusted opens nothing."""
        p = self._ledger(self._good(), self._good(kind="vibes"))
        was = os.environ.get("TV_SELF_ARMING_LEDGER")
        try:
            os.environ["TV_SELF_ARMING_LEDGER"] = p
            self.assertEqual(SA.score("prune.arm")["state"], SA.UNKNOWN)
            ok, why = SA.may("prune.arm")
            self.assertFalse(ok, "a forged ledger let the deleter through: %s" % why)
        finally:
            if was is None:
                os.environ.pop("TV_SELF_ARMING_LEDGER", None)
            else:
                os.environ["TV_SELF_ARMING_LEDGER"] = was


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
