# -*- coding: utf-8 -*-
"""#77 — "UNKNOWN, not an empty shelf" ONCE, HOWEVER MANY LAYERS PASS THE REASON UP.

Seen 2026-09-29 in BLUEPRINT.md on a tree with no footage: the river line carried the phrase THREE times, because five
readers each prefixed it to a reason that already said it. After the fix, the same regeneration carries it once.
DRIVEN: the one helper every reader asks, nested the way the readers nest; and the five readers are parsed (ast) so
none builds the literal prefix again. RED_PROOF below.

REG-1512 (review of v3524) found two holes, both measured before this was written:
  1. the helper skipped the lead whenever the bare WORD "UNKNOWN" was anywhere in the reason, so a reason that said
     UNKNOWN about something else ("printer.stream is LOCKED - UNKNOWN: the proof queue would not parse", or the
     tombstone loader's "- UNKNOWN, not zero reels") lost the framing, and no layer in the chain said the shelf was
     UNREAD rather than EMPTY. Reproduced: printer.stream()'s why and route()'s why both carried the phrase 0 times.
  2. this law only caught ONE spelling of the prefix (a constant starting "... - %s"), and never called a reader, so an
     f-string or a `+` spelling in the router brought the stutter back with every test green, and a reader that
     dropped the helper and returned the bare reason (the opposite regression) was green too.
So TheRealReadersSayItOnce DRIVES reel_river, printer.stream() and reel_router.route() on their UNKNOWN paths, with
only their inputs stubbed (sys.modules / mock.patch - no live store, no lock file, no reel is read), and counts the
phrase in what each one RETURNS. The ast walk now looks for the phrase in any string constant, whatever the spelling.
"""
import ast
import os
import sys
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import unknown_shelf as US  # noqa: E402

PHRASE = "UNKNOWN, not an empty shelf"
READERS = ("reel_river.py", "per_reel_routes.py", "one_funnel.py", "printer.py", "reel_router.py")


class OnceHoweverDeep(unittest.TestCase):

    def test_three_layers_say_it_once(self):
        w = US.not_an_empty_shelf("")                                     # reel_river: nothing walked
        w = US.not_an_empty_shelf(w)                                      # per_reel_routes
        w = "printer.stream() could not answer: " + US.not_an_empty_shelf(w)   # printer, quoted by the router
        w = US.not_an_empty_shelf(w, "the walk did not answer")          # reel_router
        self.assertEqual(1, w.count(PHRASE), w)
        self.assertIn(US.DEFAULT, w, "the reason itself was lost on the way up")

    def test_an_empty_reason_is_never_an_empty_sentence(self):
        self.assertEqual(US.LEAD + "x", US.not_an_empty_shelf(None, "x"))
        self.assertEqual(US.LEAD + US.DEFAULT, US.not_an_empty_shelf("   "))

    def test_the_blueprint_header_is_not_doubled(self):
        self.assertEqual("UNKNOWN, not an empty shelf — a", US.says_unknown("UNKNOWN, not an empty shelf — a"))
        self.assertEqual("UNKNOWN — a", US.says_unknown("a"))


class NoReaderBuildsTheLiteralPrefix(unittest.TestCase):

    def test_the_five_readers(self):
        bad = []
        for name in READERS:
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for n in ast.walk(tree):
                # ⚠ REG-1512 — ANY constant carrying the phrase, not only one STARTING "<phrase> — %s". The first cut
                # matched 0 of f"<phrase> — {why}" and "<phrase> — " + why (both measured with this predicate), and
                # an f-string's literal half IS an ast.Constant, so this one test covers all three spellings. None of
                # the five readers carries the phrase in any constant today: the helper owns it.
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and PHRASE in n.value:
                    bad.append("%s:%d" % (name, n.lineno))
        self.assertEqual([], bad, "a reader prefixes the phrase itself again - the stutter comes back: %s" % bad)


def _raises(msg):
    def _f(*a, **k):
        raise RuntimeError(msg)
    return _f


def _stub(name, **fns):
    """A stand-in module for sys.modules, so an `import X` INSIDE a reader gets this and never the real one."""
    m = types.ModuleType(name)
    for k, v in fns.items():
        setattr(m, k, v)
    return m


#: The lock refusal self_arming really gives when the proof queue will not parse (the reviewer's case 1).
LOCKED = "UNKNOWN: the proof queue would not parse, and an unreadable proof queue fails CLOSED"
#: The two sentences _sources() really writes into `whys` when the river owner raises and the ledger is a list:
#: `_safe()`'s "<fn> would not answer (...)" and `_load_tombstones()`'s own non-record sentence (case 2).
RIVER_RAISED = "river would not answer (disk I/O error)"
TOMB_LIST = "the tombstone ledger is list, not a record — UNKNOWN, not zero reels"


class TheRealReadersSayItOnce(unittest.TestCase):
    """REG-1512 — the readers themselves, driven on their UNKNOWN paths, each counted in what it RETURNS.

    Only the seams are stubbed: reel_story and self_arming through sys.modules (the readers import them inside the
    function), printer._sources and the router's two ledger reads through mock.patch. Nothing on disk is opened.
    """

    def setUp(self):
        import printer
        import reel_river
        import reel_router
        self.P, self.RR, self.RT = printer, reel_river, reel_router

    def _lock(self, ok=True, why=""):
        return mock.patch.dict(sys.modules, {"self_arming": _stub("self_arming",
                                                                  may_on_merit=lambda *a, **k: (ok, why))})

    def _no_ledgers(self):
        # route()'s UNKNOWN path also publishes the closure ledger and the outlet; both are separate stores
        # and neither decides `why`, so they answer UNKNOWN here instead of opening his.
        return (mock.patch.object(self.RT, "_closed_ledger",
                                  return_value={"n": None, "readable": False, "why": "stubbed"}),
                mock.patch.object(self.RT, "_routed_by_a_lane", return_value=(None, "stubbed")))

    def _route(self):
        a, b = self._no_ledgers()
        with a, b:
            return self.RT.route()

    def test_the_helper_leads_a_reason_that_says_UNKNOWN_about_something_else(self):
        for why in ("printer.stream is LOCKED — " + LOCKED, TOMB_LIST,
                    "printer.stream() could not answer: printer.stream is LOCKED — " + LOCKED):
            w = US.not_an_empty_shelf(why)
            self.assertTrue(w.startswith(US.LEAD), "the word UNKNOWN about a lock or a ledger swallowed the "
                                                   "shelf's framing: %r" % w)
            self.assertEqual(1, w.count(PHRASE), w)
        # the suffix spelling extract_gap / reel_templates / river_walk use already says it - not twice
        w = US.not_an_empty_shelf("reel_river would not answer (x) — UNKNOWN, not an empty shelf")
        self.assertEqual(1, w.count(PHRASE), w)

    def test_reel_river_with_no_rows(self):
        # the real _story() runs; only reel_story.story() is replaced, and it raises with UNKNOWN in its text
        with mock.patch.dict(sys.modules, {"reel_story": _stub(
                "reel_story", story=_raises("the retention plan is UNKNOWN: its lock would not read"))}):
            rv = self.RR.river()
        self.assertFalse(rv["ok"])
        self.assertEqual(1, rv["why"].count(PHRASE), "reel_river: %r" % rv["why"])
        self.assertTrue(rv["why"].startswith(US.LEAD), "reel_river: %r" % rv["why"])
        self.assertIn("reel_story would not answer", rv["why"], "the reason itself was lost")

    def test_printer_with_no_owner_answering(self):
        src = {"river": None, "door": None, "routes": None, "tombstones": None}
        with self._lock(), mock.patch.object(self.P, "_sources", return_value=(src, [RIVER_RAISED, TOMB_LIST])):
            r = self.P.stream()
        self.assertEqual("UNKNOWN", r["state"], r["why"])
        self.assertEqual(1, r["why"].count(PHRASE), "printer.stream(): %r" % r["why"])
        self.assertTrue(r["why"].startswith(US.LEAD), "printer.stream(): %r" % r["why"])
        self.assertIn(RIVER_RAISED, r["why"])
        self.assertIn(TOMB_LIST, r["why"])

    def test_router_over_printer_over_river_says_it_once(self):
        # the real nesting, three readers deep: reel_river's no-rows answer is the printer's src["river"], and
        # the router quotes the printer. Each layer would add the phrase if the one below had not.
        with mock.patch.dict(sys.modules, {"reel_story": _stub("reel_story", story=_raises("disk I/O error"))}):
            rv = self.RR.river()
        with self._lock(), mock.patch.object(self.P, "_sources", return_value=({"river": rv}, [])):
            rep = self._route()
        self.assertFalse(rep["ok"])
        self.assertIn("printer.stream() could not answer", rep["why"], "the router did not quote the printer")
        self.assertEqual(1, rep["why"].count(PHRASE), "route(): %r" % rep["why"])
        self.assertIn("disk I/O error", rep["why"], "the reason itself was lost on the way up")

    def test_router_over_a_locked_printer(self):
        with self._lock(False, LOCKED):
            rep = self._route()
        self.assertIn("printer.stream is LOCKED", rep["why"])
        self.assertEqual(1, rep["why"].count(PHRASE), "route(): %r" % rep["why"])
        self.assertTrue(rep["why"].startswith(US.LEAD), "route(): %r" % rep["why"])

    def test_router_whose_walk_said_nothing(self):
        a, b = self._no_ledgers()
        with a, b, mock.patch.object(self.RT, "_evidence", return_value=(None, "")):
            rep = self.RT.route()
        self.assertEqual(US.LEAD + "the walk did not answer and said nothing", rep["why"])


RED_PROOF = [
    {
        "why": "2026-09-29 (#77) - the helper leads every reason with the phrase, so nested readers stutter",
        "file": "tv/unknown_shelf.py",
        "find": "    return w if PHRASE in w else LEAD + w\n",
        "replace": "    return LEAD + w\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (#77) - the router builds the literal prefix again",
        "file": "tv/reel_router.py",
        "find": "        rep[\"why\"] = _us.not_an_empty_shelf(why, \"the walk did not answer and said nothing\")\n",
        "replace": "        rep[\"why\"] = \"UNKNOWN, not an empty shelf — %s\" % why\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1512) - the helper skips the lead on the bare WORD, so a lock's or a ledger's UNKNOWN "
               "swallows the shelf's framing (the v3524 review's finding 1)",
        "file": "tv/unknown_shelf.py",
        "find": "    return w if PHRASE in w else LEAD + w\n",
        "replace": "    return w if \"UNKNOWN\" in w else LEAD + w\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1512) - the router builds the prefix as an f-string, the spelling the first ast walk "
               "matched 0 times; the driven chain counts the phrase twice",
        "file": "tv/reel_router.py",
        "find": "        rep[\"why\"] = _us.not_an_empty_shelf(why, \"the walk did not answer and said nothing\")\n",
        "replace": "        rep[\"why\"] = f\"UNKNOWN, not an empty shelf — {why}\"\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1512) - the printer concatenates the prefix onto a river reason that already says it",
        "file": "tv/printer.py",
        "find": "                        why=_us.not_an_empty_shelf(\"; \".join(_bits), \"no owner answered and none said "
                "why\"))\n",
        "replace": "                        why=\"UNKNOWN, not an empty shelf — \" + \"; \".join(_bits))\n",
        "matches": 1,
    },
    {
        "why": "2026-09-29 (REG-1512) - the opposite regression: reel_river drops the helper and returns the bare "
               "reason, so nothing says the shelf was unread (every static test stays green)",
        "file": "tv/reel_river.py",
        "find": "                \"why\": __import__(\"unknown_shelf\").not_an_empty_shelf(why)}\n",
        "replace": "                \"why\": why or \"no reel reached this probe\"}\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
