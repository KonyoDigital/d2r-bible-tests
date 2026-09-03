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


def _live_names(by_source=None):
    """Every name the resolver is actually asked about. -> set

    Pass a dict as `by_source` to also receive {source: count}, so a caller can assert this
    function's REACH and not merely its output.
    """
    import organ_matrix as OM
    seen = {} if by_source is None else by_source

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

    seen["organ_matrix.surfaces"] = len(src_surfaces)
    seen["organ_matrix.organ_coverage"] = len(src_coverage)
    seen["heart.vessels"] = len(src_heart)
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
        dead = sorted(s for s in SOURCES if reach.get(s, 0) <= 0)
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