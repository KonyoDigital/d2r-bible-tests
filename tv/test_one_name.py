"""ONE CONCEPT, MANY RENDERINGS — and it must reproduce every live resolver EXACTLY.

⚠⚠ THE DANGER IS NOT THAT THIS FILE IS WRONG. It is that adopting it silently changes what a
consumer receives. Three resolvers exist and they disagree on 6 of 9 inputs — each correct for its
own consumers, because the template's ledger map, route_totals.ROUTES and lane_lock's surfaces key
on three different forms. A single resolver that "tidies" them to one string breaks all three, and
would do it quietly: the call sites keep compiling and start missing.

So the law is agreement, not replacement. For every spelling any surface can produce, one_name's
rendering for that surface must EQUAL what the live function returns today. If a resolver later
changes its mind, this goes red and someone decides deliberately — which is the whole point of
having one place.

⚠ AND IT MUST ANSWER THE QUESTION A1 AND A3 COULD NOT ASK: is `chronicle.runeword` the same thing
as `runeword`? Nothing in the console could say so, which is why FLOWING was unreachable and why 9
matrix cells read ABSENT while the organ was watching them.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

import one_name as ON  # noqa: E402

#: ⚠ TWO KINDS OF INPUT, AND FEEDING ONE TO THE OTHER'S RESOLVER PROVES NOTHING. TAB spellings are
#: what the tab resolvers are for; DOTTED surface names belong to the route/organ vocabulary. My
#: first cut fed "chronicle.runeword" to lane_lock._canon_tab and called the mismatch a
#: disagreement — but that resolver has no business knowing a surface name, and it ECHOES anything
#: it does not recognise. The reproduction tests use TABS only; the dotted names are for
#: same_thing(), which is precisely the question that spans the two vocabularies.
#:
#: ⚠ WORTH RECORDING RATHER THAN SILENTLY WORKING AROUND: lane_lock._canon_tab returns its INPUT
#: for a word it does not know, so a caller cannot tell resolved from unrecognised. That is the
#: unknown-echoed-as-answer shape. It is pre-existing and its callers may depend on it, so this
#: names it instead of changing it. [[unknown-stays-unknown]]
TABS = ("unique", "uniques", "set", "sets", "runeword", "runewords",
        "UNIQUE", " set ", "Runewords")
SURFACES = ("chronicle.runeword", "fleet.sets", "roster.unique")
INPUTS = TABS


class TheParityTestsAreTransitionalAndThisSaysSo(unittest.TestCase):
    """⚠⚠ A COLD CROSS-FAMILY REVIEW NAMED THE EXACT WAY THIS DECAYS, AND IT IS RIGHT.

    Asked whether asserting parity with the live resolvers was sound or just froze the mess:

        "Sound for the transition, but only if treated as temporary. However, if those assertions
         are never replaced by a single canonical implementation that the three resolvers delegate
         to, the tests DO freeze the mess: future changes will have to update both the concept
         table and the three original functions plus their tests."

    Exactly so. Parity is scaffolding, not the building. Every resolver still holding its own map
    is a place the next divergence starts, and the parity tests would then dutifully enforce the
    divergence. This test names what is still owed, so the debt is visible in the suite rather than
    remembered — and it FAILS if a resolver is retired without the list being updated, which stops
    the list rotting into fiction.

    CUT OVER SO FAR:  organ_matrix._same_thing -> one_name (v2493, measured 132 agree / 0 differ)
    """

    #: resolvers that still carry their own map. Shrinking this is the point of the exercise.
    OWED = ("chronicle_template", "route_totals", "lane_lock")

    def test_the_remaining_resolvers_are_named_and_still_there(self):
        import importlib
        still = []
        for mod in self.OWED:
            try:
                m = importlib.import_module(mod)
            except Exception:
                continue
            src = __import__("inspect").getsource(m)
            if "import one_name" in src:
                continue          # it delegates now — the list is stale, deliberately
            still.append(mod)
        self.assertEqual(
            sorted(still), sorted(self.OWED),
            "the cut-over list no longer matches reality: %s still hold their own map, the list "
            "says %s. Update OWED when a resolver delegates, or this becomes a fiction that reads "
            "as progress." % (sorted(still), sorted(self.OWED)))


class ItReproducesEveryLiveResolver(unittest.TestCase):

    def test_it_matches_chronicle_template(self):
        import chronicle_template as CT
        for x in INPUTS:
            live = CT.canonical_tab(x)
            if live is None:
                continue          # that resolver does not know this word; nothing to reproduce
            self.assertEqual(
                ON.form(x, "template"), live,
                "one_name says %r for %r on the template surface; the live resolver says %r. "
                "Adopting this would silently change what its consumers receive."
                % (ON.form(x, "template"), x, live))

    def test_it_matches_route_totals(self):
        import route_totals as RT
        for x in INPUTS:
            live = RT.canonical(x)
            if live is None:
                continue
            self.assertEqual(
                ON.form(x, "route"), live,
                "one_name says %r for %r on the route surface; route_totals says %r"
                % (ON.form(x, "route"), x, live))

    def test_it_matches_lane_lock(self):
        import lane_lock as LL
        fn = getattr(LL, "_canon_tab", None)
        if fn is None:
            raise unittest.SkipTest("lane_lock exposes no _canon_tab — UNKNOWN, not a pass")
        for x in INPUTS:
            try:
                live = fn(x)
            except Exception:
                continue
            if live is None:
                continue
            self.assertEqual(
                ON.form(x, "lane"), live,
                "one_name says %r for %r on the lane surface; lane_lock says %r"
                % (ON.form(x, "lane"), x, live))


class ItAnswersTheQuestionNothingCouldAsk(unittest.TestCase):

    def test_a_dotted_surface_name_resolves_to_its_concept(self):
        """A1's FLOWING and A3's 9 MISNAMED cells are both this question, unasked."""
        for surface, plain in (("chronicle.runeword", "runeword"),
                               ("fleet.sets", "set"),
                               ("roster.unique", "uniques")):
            self.assertTrue(
                ON.same_thing(surface, plain),
                "%r and %r are the same thing and one_name cannot say so — which is exactly why "
                "the organ matrix reported ABSENT for a surface the organ was watching"
                % (surface, plain))

    def test_different_concepts_are_never_the_same_thing(self):
        """A resolver that says yes too easily is worse than none — it invents coverage."""
        for a, b in (("chronicle.set", "unique"), ("runeword", "sets"), ("uniques", "runewords")):
            self.assertFalse(ON.same_thing(a, b), "%r and %r are NOT the same thing" % (a, b))

    def test_two_unknowns_are_not_the_same_thing(self):
        """The trap in every naive implementation: None == None reads as a match."""
        self.assertFalse(ON.same_thing("zzz_not_a_tab", "qqq_also_not"),
                         "two words it does not know came back as the same thing")
        self.assertFalse(ON.same_thing(None, None))
        self.assertFalse(ON.same_thing("", ""))

    def test_an_unknown_word_is_None_and_never_echoed_back(self):
        """Echoing the input makes an unknown look resolved."""
        self.assertIsNone(ON.concept("zzz_not_a_tab"))
        self.assertIsNone(ON.form("zzz_not_a_tab", "route"))
        self.assertIsNone(ON.form("set", "no_such_surface"),
                          "an unknown SURFACE must be None, not a default rendering")

#: ⚠⚠ THE COLLISION CENSUS — a RATCHET, because `_shape` is genuinely fuzzy and the docstring now
#: says so. It strips every non-alphanumeric, so `user_id` and `userid` land on one shape. A cold
#: review of the shipped code named that, and the measurement is what settles how much it matters:
#: across 100 live names there are exactly THREE colliding shapes and all three are the same thing
#: written in two house styles. That is a fact about today, not a property of the function.
#:
#: So the census may only SHRINK. A new collision is not assumed wrong — it is assumed UNREVIEWED,
#: which is a different thing and needs a person to say which of the two it is. The alternative is
#: a resolver that quietly merges two unrelated subsystems the first time someone adds a name.
#: [[unknown-stays-unknown]]
SHAPE_COLLISIONS = {
    "armedmigration": ("armed migration", "armed_migration"),
    "boardjoin":      ("board join", "board_join"),
    # ⚠ THESE TWO GREW THE MOMENT THE CENSUS COULD ACTUALLY SEE THE HEART, which is the ratchet
    # doing its job rather than a defect: `tvd-shadow-watch` and `tvd-version-drift` are the LANE
    # names, and `shadow watch` / `version drift` are what console_doctor calls the same concerns.
    # Reviewed and correct — and they are also the whole of A1's naming overlap: 2 of 11 lanes are
    # named by an organ under another spelling, the other 9 by nobody.
    "shadowwatch":    ("shadow watch", "shadowWatch", "tvd-shadow-watch"),
    "versiondrift":   ("tvd-version-drift", "version drift"),
}

#: Each source this census reads, and the fact that it must contribute SOMETHING.
#:
#: ⚠⚠ CARVED FROM A SABOTAGE THAT WENT GREEN. Disabling the heart block entirely left this file
#: passing, because the reviewed collisions all happened to come from another source — so the
#: census could lose a whole source and never say so. It had in fact ALREADY lost one: the heart
#: block asked for `heart.snapshot()`, which does not exist, so behind its `hasattr` guard it
#: contributed ZERO names on every run since it was written. A guard must fail on its own REACH,
#: not only on its subject. [[source-reading-guard]]
SOURCES = ("organ_matrix.surfaces", "organ_matrix.organ_coverage", "heart.vessels")


def _keep_names(names):
    """A source's OWN names, trimmed, minus the falsy ones. -> set

    ⚠⚠ IT LIVES HERE BECAUSE AS A CLOSURE IT COULD NOT BE PUT TO A CASE. A cold review found that
    the emptiness test used the STRIPPED value while the stored one was UNSTRIPPED, so `" foo "`
    entered the pool with its padding. That matters: `_shape` deletes whitespace, so `" foo "` and
    `"foo"` share a shape and would surface as a NEW unreviewed collision — this census failing for
    a reason entirely of its own making.

    Sabotaging it back went GREEN, because nothing in his stores has a padded name today. A guard
    that can only fire while the live corpus happens to contain an example is blind, and hoisting
    this out of `_live_names` is what makes the law checkable on constructed input instead.
    [[gate-blind-to-unexercised-input]]
    """
    return {str(n).strip() for n in names if str(n or "").strip()}


#: ⚠ NOT None. A spy that reports "I could not take this reading" with the same value the subject
#: might legitimately have passed cannot tell a broken instrument from a real defect.
_UNSNAPPABLE = object()


def _orphan_names(pool, reach, sources):
    """Names in the pool that no DECLARED source accounts for. -> sorted list

    ⚠⚠ IT LIVES HERE FOR THE SAME REASON `_keep_names` DOES: as inline arithmetic inside a test
    method it could not be sabotaged, and my first attempt to guard it was a tautology — it
    recomputed the rule locally, so breaking the real one left the file green.

    The rule sums only the DECLARED sources. Summing all of `reach.values()` let an UNDECLARED
    source account for its own contribution: it writes a fourth key, its names land in `accounted`,
    and this check goes quiet. The `undeclared` assertion would still catch it — but then two
    checks rest on one of them, and this stops being independent evidence.
    """
    # ⚠ A BARE STRING IS NOT A POOL OF ONE NAME. `set("abc")` is {"a","b","c"}, so a caller
    # passing a single name instead of a collection would have this comparing CHARACTERS and
    # reporting nonsense as orphans. Cheap to refuse, and impossible to spot in the output.
    if isinstance(pool, str):
        raise TypeError("pool is a string (%r); a pool of one name is still a collection" % pool[:40])
    accounted = set()
    for s in sources:
        # ⚠ `or ()` treats an explicit EMPTY SET as absent. It does not change this result — no
        # names are added either way — but the distinction is real and is kept where it matters:
        # the `dead` check reads the sets directly, so a source recording "I contributed nothing"
        # is caught there rather than here.
        accounted |= set(reach.get(s) or ())
    return sorted(set(pool) - accounted)


def _live_names(by_source=None):
    """Every name the resolver is actually asked about. -> set

    Pass a dict as `by_source` to also receive {source: count}, so a caller can assert this
    function's REACH and not merely its output.
    """
    import organ_matrix as OM
    seen = {} if by_source is None else by_source
    # ⚠⚠ IT IS AN OUT-PARAMETER AND MUST START EMPTY. A cold review: "a pre-existing key in
    # `reach` that belongs to SOURCES and holds a non-empty set will make both the `unrecorded`
    # and `dead` assertions pass even if the corresponding source later contributes nothing (or is
    # never executed). Pre-existing entries can also inflate `accounted` and mask a genuine
    # orphan." Every caller in the tree passes a fresh dict today, so nothing was wrong on this
    # tree — and a contract that only holds while every caller is careful is not a contract.
    seen.clear()

    # ⚠ ONE RULE, ONE PLACE. Hoisting `_keep` to module level so it could be put to a case left
    # the original body sitting UNREACHABLE below a `return` — two copies of the same rule, in a
    # file whose whole subject is two sources disagreeing, written while fixing exactly that.
    # The alias stays only so the call sites below read as they did. [[copy-drift]] §1
    _keep = _keep_names

    src_surfaces = _keep(OM.surfaces())
    src_coverage = set()
    for _o, (names, _w) in OM.organ_coverage().items():
        if names:
            src_coverage |= _keep(names)
    # ⚠ ABSENT AND BROKEN ARE DIFFERENT FACTS, and one bare `except Exception: pass` reported
    # them identically — so a heart that raised silently removed every organ and lane name from
    # this census, and the census went on passing. A source that is MISSING is a smaller pool; a
    # source that is BROKEN is an unknown one. [[unknown-stays-unknown]]
    try:
        import heart
    except ImportError:
        heart = None                       # genuinely not here — a smaller pool, honestly
    src_heart = set()
    if heart is not None:
        # ⚠⚠ IT WAS ASKING FOR A FUNCTION THAT DOES NOT EXIST. This read `heart.snapshot()` behind
        # a `hasattr` guard — and heart has no `snapshot`, so the guard was False every single run
        # and this source contributed ZERO names, silently, for as long as it existed. A hasattr
        # guard around a name that is simply wrong is not defensive, it is a way of never finding
        # out. The real accessor is vessels(), and it publishes 21 vessels and 14 locks.
        # [[plumbing-with-no-tap]]
        # ⚠ vessels() itself is called UNGUARDED, deliberately: if the module imports, a failure
        # inside it is a BROKEN source and must fail this test. That is the distinction this
        # function was rewritten to make, and catching here would erase it again.
        v = heart.vessels()
        for r in (v.get("vessels") or []):
            if isinstance(r, dict):
                src_heart |= _keep([r.get("name"), r.get("watcher")])
        for r in (v.get("locks") or []):
            if isinstance(r, dict):
                src_heart |= _keep([r.get("lock")])

    # ⚠⚠ THE SETS, NOT THE COUNTS — because counts cannot be reconciled against the pool. A cold
    # review found the hole in v2504's own fix: the undeclared/unrecorded pair compares KEYS, so a
    # fourth source that CONTRIBUTES NAMES and records nothing is invisible to both assertions.
    # Confirmed by construction: undeclared=[] unrecorded=[] and both pass, while the pool carries
    # a name no recorded source accounts for. Recording the sets lets the caller assert the pool
    # IS exactly what the declared sources supplied — a silent contributor then breaks equality
    # rather than hiding in it. [[the-unjoined-end]]
    seen["organ_matrix.surfaces"] = src_surfaces
    seen["organ_matrix.organ_coverage"] = src_coverage
    seen["heart.vessels"] = src_heart
    return src_surfaces | src_coverage | src_heart


class TheShapeRuleDoesNotQuietlyMergeThings(unittest.TestCase):

    def test_the_dead_line_stays_dead(self):
        """A line that cannot change the answer is a claim, not a mechanism.

        The removed camelCase substitution inserted a "-" that the next line deleted. If someone
        re-adds a normalisation step, it has to change at least one result or it is decoration.
        """
        import re as _re
        def without_prefix_only(s):
            return _re.sub(r"[^a-z0-9]", "",
                           _re.sub(r"^tvd[-_]", "", str(s or "")).lower())
        for probe in ("shadowWatch", "tvd-shadow-watch", "XMLHttpRequest", "a1B2c3",
                      "tvd_stash_watch", "chronicle.runeword", "ALLCAPS", "mixed_Case-Thing"):
            self.assertEqual(
                ON._shape(probe), without_prefix_only(probe),
                "_shape(%r) now does something beyond stripping the tvd prefix and folding case. "
                "That may be right — but it is a behaviour change to the thing that decides "
                "whether two subsystems are the same, and it needs its own evidence." % probe)

    def test_a_name_is_stored_the_way_it_was_tested(self):
        """`" foo "` must not enter the pool with its padding.

        The emptiness test stripped and the store did not, so a padded name kept its padding —
        and since `_shape` deletes whitespace, `" foo "` and `"foo"` share a shape and would be
        reported as a NEW unreviewed collision. Sabotaging this back left the census GREEN,
        because nothing in his stores is padded today; the law is checked on constructed input
        for exactly that reason. [[gate-blind-to-unexercised-input]]
        """
        got = _keep_names([" foo ", "foo", "\tbar\n", "", "   ", None])
        self.assertEqual(
            got, {"foo", "bar"},
            "_keep_names kept padding or a blank: %r. A padded name collides with its own trimmed "
            "form under _shape and reads as an unreviewed merge." % (sorted(got),))

    def test_an_unaskable_organ_does_not_crash_the_census(self):
        """⚠ REFUTES a cold review that called the `if names:` guard a no-op.

        Its claim: "_keep already returns an empty set on any falsy or empty names, so the guard
        merely skips a no-op." It does not — `_keep_names(None)` raises TypeError, and
        `organ_matrix.organ_coverage()` returns `(None, why)` for an organ that CANNOT BE ASKED.
        Today every organ answers with a set, so removing the guard leaves the census green — the
        guard protects a state his tree does not currently produce, which is exactly when a guard
        stops being exercised and starts being deleted by someone tidying up.
        """
        with self.assertRaises(TypeError):
            _keep_names(None)
        self.assertEqual(_keep_names([]), set(),
                         "an EMPTY list is a different input from None and must not raise")

    def test_a_source_recording_an_EMPTY_contribution_is_still_dead(self):
        """The `dead` check earns its place only if a present-but-empty entry fails.

        A source that records nothing at all is caught by the unrecorded assertion. A source that
        records an EMPTY SET is not — its key is present — and that is precisely the shape the
        heart source had for its whole existence: reachable, recorded, and contributing zero.
        """
        reach = {s: {"x"} for s in SOURCES}
        reach[SOURCES[-1]] = set()
        dead = sorted(s for s in SOURCES if not reach.get(s))
        self.assertEqual(
            dead, [SOURCES[-1]],
            "a source recording an EMPTY contribution was not reported dead. Its key is present, "
            "so the unrecorded assertion passes it, and nothing else would notice.")

    def test_a_string_pool_is_refused(self):
        """`set("abc")` is {"a","b","c"} — a caller passing one name instead of a collection
        would have the rule comparing CHARACTERS and reporting nonsense as orphans, which is
        impossible to spot in the output. Cheap to refuse."""
        with self.assertRaises(TypeError):
            _orphan_names("shadowWatch", {}, SOURCES)
        self.assertEqual(_orphan_names(["shadowWatch"], {}, SOURCES), ["shadowWatch"],
                         "a real one-name collection must still work")

    def test_the_census_ACTUALLY_CALLS_the_orphan_rule(self):
        """⚠⚠ EXTRACTING THE RULE PROVED IT WORKS, NOT THAT ANYTHING USES IT.

        A cold review put it exactly: "the test only shows that the helper behaves correctly when
        called directly. It does not prove the real census code actually calls `_orphan_names`
        rather than an equivalent inline expression. If the production site duplicated the logic,
        the helper test would still pass and the integration would be untested."

        That is the same unjoined shape the helper was extracted to escape — the rule moved, and
        nothing asserted the caller followed. So this REPLACES the rule with one that reports a
        sentinel orphan and requires the census assertion to notice.
        """
        import unittest as _ut
        real = globals()["_orphan_names"]
        # ⚠⚠ CAPTURE THE ARGUMENTS, NOT JUST THE FACT OF A FAILURE. A cold review of the first
        # version: matching a fragment of an assertion message "matches a substring anywhere in
        # any failure message... if another assertion's message is edited to include that phrase,
        # the assertion passes while proving nothing about which specific check failed" — and an
        # assertion EARLIER in the census could fail first, leaving this test satisfied by a
        # failure that never reached the orphan check.
        #
        # Recording the call answers both, and more than either: it proves the rule was called AND
        # what it was called WITH. A patch that ignores its arguments cannot tell a correct call
        # from an incorrect one.
        calls = []
        try:
            def _spy(pool, reach, sources):
                # ⚠ THE SPY MUST NOT BE ABLE TO FAIL THE THING IT IS WATCHING. A cold review: if
                # a conversion inside it raises — an unhashable item in `pool`, a `reach` that is
                # not dict-like — the census ERRORS, and this test then fails its own
                # assertFalse(result.errors) even though the call it was checking for DID happen.
                # An instrument that can break the measurement reports its own failure as the
                # subject's. Snapshot defensively; a snapshot that could not be taken is recorded
                # as None rather than raising. [[feedback-suspect-the-instrument]]
                # ⚠⚠ A DISTINCT SENTINEL, BECAUSE None MEANT TWO OPPOSITE THINGS. v2518 recorded
                # None when a conversion failed — and None is also a value the census could
                # legitimately pass. A cold review: "the assertion cannot distinguish 'spy failed
                # to snapshot' from 'the code under test passed None'", and the message blamed THE
                # SPY either way, misattributing a real defect to the instrument. Two meanings on
                # one value, in the fix written to stop exactly that. [[unknown-stays-unknown]]
                def _snap(fn, x):
                    try:
                        return fn(x)
                    except Exception:
                        return _UNSNAPPABLE
                # ⚠⚠ KEEP THE RAW VALUE BESIDE THE SNAPSHOT. A sentinel alone did NOT separate
                # the two cases — it moved the conflation: when the census passed None, `set(None)`
                # raised INSIDE the spy, so the failure was recorded as "the spy could not take
                # this reading" and the message blamed the instrument for a defect in the CALL.
                # Proven by sabotage: passing None or a non-mapping produced the wrong accusation.
                # The raw value is what says which of the two it is.
                calls.append({"pool": _snap(set, pool), "reach": _snap(dict, reach),
                              "sources": _snap(tuple, sources),
                              # ⚠ A REPR TAKEN NOW, BESIDE THE REFERENCE. The raw values are
                              # stored by REFERENCE, and the whole reason a snapshot exists is
                              # that references change: a caller doing
                              # `_orphan_names(pool, ...); pool.clear()` leaves the contract check
                              # passing (a list is still a list) while the failure message prints
                              # `pool=[]` — the wrong value, in the sentence a reader trusts most.
                              "rawRepr": {"pool": repr(pool)[:120], "reach": repr(reach)[:120],
                                          "sources": repr(sources)[:120]},
                              "raw": {"pool": pool, "reach": reach, "sources": sources}})
                return ["sentinel-orphan"]
            globals()["_orphan_names"] = _spy
            case = TheShapeRuleDoesNotQuietlyMergeThings(
                "test_no_unreviewed_shape_collision_has_appeared")
            result = _ut.TestResult()
            case.run(result)
        finally:
            globals()["_orphan_names"] = real
        # ⚠ FAILURES ONLY, NOT ERRORS. A cold review: "an error usually means an exception during
        # setup, teardown, or an unexpected crash... the test would then pass even though the
        # census never reached the patched rule, just because something else blew up." Accepting
        # errors would let an import failure or a live-data hiccup stand in for the proof.
        self.assertFalse(
            result.errors,
            "the census ERRORED rather than failing an assertion: %s. That is not evidence about "
            "the orphan rule — it is something else breaking, and counting it would let any crash "
            "vouch for this join."
            % "".join(t for _c, t in result.errors)[:200])
        self.assertTrue(
            result.failures,
            "the orphan rule was replaced with one that reports a sentinel on every input, and "
            "the census test still PASSED. It is not calling this rule — the extraction proved a "
            "helper works while the real check does something else.")
        # ⚠ AND THE SENTINEL MUST APPEAR IN THE ORPHAN ASSERTION'S OWN MESSAGE, not merely
        # somewhere in the text. Same review: the string "could appear in a traceback, repr of the
        # test object, a log line, or an error message about the patching itself" — so a bare
        # substring search over the whole blob would accept the right answer for the wrong reason.
        # THE PRIMARY EVIDENCE: it was called, and called with the census's own values.
        self.assertTrue(
            calls,
            "the orphan rule was never called at all. The census is computing its own answer — "
            "the extraction proved a helper works while the real check does something else.")
        self.assertEqual(
            len(calls), 1,
            "the orphan rule was called %d times; the census should ask once" % len(calls))
        got = calls[0]
        # ⚠ THE CALL IS JUDGED ON THE RAW VALUE, THE INSTRUMENT ON THE SNAPSHOT. Judging both on
        # the snapshot blames whichever one the reader happens to assume.
        _raw = got["raw"]
        _contract = (("pool", (set, frozenset, list, tuple)),
                     ("reach", dict),
                     ("sources", (list, tuple, set, frozenset)))
        for _k, _ty in _contract:
            self.assertIsInstance(
                _raw[_k], _ty,
                "the census called the rule with %s=%s. That is a defect in THE CALL, not in this "
                "instrument — the rule iterates it and would misbehave."
                % (_k, got["rawRepr"][_k]))
        # ⚠ ONLY `pool` CAN LEGITIMATELY REACH THE SENTINEL, and asserting it for all three was a
        # guard that cannot fire — the thing v2520 removed one version ago, reappearing here. Once
        # the contract above passes, `dict(a_dict)` and `tuple(an_iterable)` always succeed; only
        # `set(pool)` can still raise, on a list of UNHASHABLE items such as [[]]. A permanently
        # unreachable assertion reads as a live one and is worse than none.
        self.assertIsNot(
            got["pool"], _UNSNAPPABLE,
            "THE SPY could not snapshot `pool` even though the call passed a %s (%s). That is a "
            "failure of this instrument — the likely cause is unhashable items, and reported as "
            "anything else it would read as the code under test being wrong."
            % (type(_raw["pool"]).__name__, got["rawRepr"]["pool"]))
        self.assertEqual(
            set(got["sources"]), set(SOURCES),
            "the rule was called with %r instead of the declared SOURCES. Called with the wrong "
            "list, it would account for names no declared source supplied." % (got["sources"],))
        self.assertTrue(
            got["pool"],
            "the rule was called with an EMPTY pool, so it could not have found anything and the "
            "call proves nothing")
        self.assertTrue(
            set(got["reach"]) >= set(SOURCES),
            "the rule was called with reach=%r, which does not carry every declared source"
            % (sorted(got["reach"]),))

        blob = "".join(t for _c, t in result.failures)
        self.assertIn("sentinel-orphan", blob,
                      "the census failed, but the sentinel never reached it")
        self.assertIn(
            "declared source accounts for", blob,
            "the census failed and the sentinel is somewhere in the text, but NOT in the orphan "
            "assertion's own message — so the failure has not been shown to come from that check")

    def test_an_undeclared_source_cannot_account_for_its_own_names(self):
        """The orphan rule must be independent evidence, not a duplicate of the undeclared check.

        ⚠ MY FIRST GUARD FOR THIS WAS A TAUTOLOGY — it recomputed the rule inside the test, so
        breaking the real one left the file green. It drives `_orphan_names` now.

        ⚠ AND ONE COLD-REVIEW FINDING IS REFUTED HERE RATHER THAN FIXED: it warned that a caller's
        pre-existing entry in `reach` could vouch for a dead source. It cannot — all three declared
        keys are assigned UNCONDITIONALLY before the function returns, so any prior value for them
        is overwritten. `seen.clear()` stays as hygiene over the out-parameter, not as a fix.
        """
        reach = {s: set() for s in SOURCES}
        reach["mystery.source"] = {"smuggled-name"}
        self.assertEqual(
            _orphan_names({"smuggled-name"}, reach, SOURCES), ["smuggled-name"],
            "a name contributed by an UNDECLARED source was treated as accounted for. The orphan "
            "check is then only as good as the undeclared check, and stops being evidence of its "
            "own.")
        self.assertEqual(
            _orphan_names({"real"}, {SOURCES[0]: {"real"}}, SOURCES), [],
            "BASELINE: a name a DECLARED source supplied was reported as an orphan, so this rule "
            "would fire on every healthy run and teach him to skip it")

    def test_no_unreviewed_shape_collision_has_appeared(self):
        reach = {}
        pool = _live_names(reach)
        # ⚠ THE INSTRUMENT'S REACH IS CHECKED BEFORE ITS FINDINGS. A census reading three sources
        # of which one silently returns nothing is not a smaller census, it is a blind one — and
        # `heart` was exactly that for its whole existence.
        # ⚠ AND A NAME THAT IS BLANK IS NOT A NAME. A sabotage that made _keep() pass falsy
        # values through left this file GREEN: an empty string collapses to a single pool entry
        # and one entry is never a collision, while the reach counts go UP — so a source
        # contributing nothing but blanks would report itself healthy. That is precisely the
        # false ALIVE signal the reach check exists to prevent, so it is asserted rather than
        # trusted to _keep. [[unknown-stays-unknown]]
        blank = [p for p in pool if not str(p).strip()]
        self.assertFalse(
            blank,
            "%d blank name(s) reached the pool. They cannot collide with anything, so they are "
            "invisible to the census while still counting toward every source's reach — a source "
            "emitting only blanks would look alive." % len(blank))
        # ⚠⚠ AND THE DECLARED LIST MUST MATCH WHAT WAS ACTUALLY RECORDED, BOTH WAYS. Same review:
        # "adding a fourth source requires three coordinated edits... nothing in the test will
        # notice the omission; the new source can silently contribute zero names forever." That is
        # this file's own defect one level up — SOURCES is a promise about reach, and a promise
        # nothing checks is how the heart source sat dead behind a hasattr guard in the first
        # place. [[the-unjoined-end]]
        # ⚠ AND THE POOL MUST BE EXACTLY WHAT THE DECLARED SOURCES SUPPLIED. The key comparison
        # below catches a source declared-but-not-read and read-but-not-declared; it cannot catch
        # a source that quietly adds names and records nothing, which is the same silence the
        # heart source sat in behind its hasattr guard.
        # ⚠ ONLY THE DECLARED SOURCES COUNT AS ACCOUNTING FOR A NAME. Summing ALL of
        # reach.values() let an UNDECLARED source account for its own contribution: it writes a
        # fourth key, its names land in `accounted`, and the orphan check goes quiet. The
        # `undeclared` assertion below would still catch it — but then two checks rely on one of
        # them, and the orphan check stops being independent evidence. A cold review constructed
        # exactly that case.
        orphan = _orphan_names(pool, reach, SOURCES)
        self.assertFalse(
            orphan,
            "%d name(s) are in the pool that NO declared source accounts for: %s. Something is "
            "contributing to this census without recording that it did, so it can go dead and the "
            "reach check will not notice." % (len(orphan), orphan[:5]))
        undeclared = sorted(set(reach) - set(SOURCES))
        unrecorded = sorted(set(SOURCES) - set(reach))
        self.assertFalse(
            undeclared,
            "_live_names() reads source(s) that SOURCES does not declare: %s. They are exempt from "
            "the reach check below, so one of them can go dead and nothing here will say so."
            % undeclared)
        self.assertFalse(
            unrecorded,
            "SOURCES declares source(s) that _live_names() never records: %s. The reach check "
            "would read them as 0 and fail forever, or worse, be quietly relaxed to accommodate "
            "them." % unrecorded)
        dead = sorted(s for s in SOURCES if not reach.get(s))
        self.assertFalse(
            dead,
            "%d source(s) contributed NOTHING to this census: %s. That is not a smaller pool, it "
            "is a region of the console this test can no longer see — and it reads as a pass. "
            "Reach measured: %s" % (len(dead), dead, reach))
        shapes = {ON._shape(n) for n in pool}
        # ⚠⚠ THE BASELINE WAS A SIZE, AND A SIZE IS NOT A SUBJECT. `len(pool) > 20` passes on any
        # pool that is merely not tiny — including one that has lost every name this census was
        # written to watch. A cold review put it exactly: "if _live_names() fails to return one or
        # more of the colliding names, a genuine new collision simply never appears in `live` and
        # the test passes." That is the same shape as the guard that iterated the classification it
        # was meant to check: the instrument decides its own scope.
        #
        # So the baseline names its SUBJECTS. Every reviewed collision must still be present as a
        # shape, or this census has stopped watching the thing it was written for and says so
        # rather than going quiet. [[gate-blind-to-unexercised-input]]
        missing = sorted(k for k in SHAPE_COLLISIONS if k not in shapes)
        self.assertFalse(
            missing,
            "BASELINE LOST: %d reviewed collision(s) no longer appear in the live pool at all: %s. "
            "Either those names were renamed — in which case update SHAPE_COLLISIONS deliberately "
            "— or _live_names() stopped reaching a source it used to read, and this census is now "
            "blind in exactly the region it was built to watch. Passing here would be an UNKNOWN "
            "wearing a green tick." % (len(missing), missing))
        self.assertGreater(len(pool), 20,
                           "BASELINE: only %d names in play, too few for this census to be "
                           "measuring anything. UNKNOWN, not a pass." % len(pool))
        groups = {}
        for n in pool:
            groups.setdefault(ON._shape(n), set()).add(n)
        live = {k: v for k, v in groups.items() if len(v) > 1}

        new = {k: sorted(v) for k, v in live.items() if k not in SHAPE_COLLISIONS}
        self.assertFalse(
            new,
            "%d NEW shape collision(s) — two or more names the resolver now treats as one thing, "
            "and nobody has said whether that is right: %s\n"
            "If they ARE the same thing in two house styles, add them to SHAPE_COLLISIONS. If "
            "they are DIFFERENT things, _shape is merging them and the coverage table will report "
            "one as watched because the other is." % (len(new), new))

        for shape, expected in SHAPE_COLLISIONS.items():
            got = live.get(shape)
            if got is None:
                continue      # a name disappeared; the census may shrink, that is the ratchet
            extra = got - set(expected)
            self.assertFalse(
                extra,
                "the known collision %r has GROWN to include %s. A census entry is permission for "
                "the pair that was reviewed, not for the shape." % (shape, sorted(extra)))


if __name__ == "__main__":
    unittest.main(verbosity=2)