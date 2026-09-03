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


if __name__ == "__main__":
    unittest.main(verbosity=2)
