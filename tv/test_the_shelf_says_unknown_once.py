# -*- coding: utf-8 -*-
"""#77 — "UNKNOWN, not an empty shelf" ONCE, HOWEVER MANY LAYERS PASS THE REASON UP.

Seen 2026-09-29 in BLUEPRINT.md on a tree with no footage: the river line carried the phrase THREE times, because five
readers each prefixed it to a reason that already said it. After the fix, the same regeneration carries it once.
DRIVEN: the one helper every reader asks, nested the way the readers nest; and the five readers are parsed (ast) so
none builds the literal prefix again. RED_PROOF below.
"""
import ast
import os
import sys
import unittest

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
            tree = ast.parse(open(os.path.join(HERE, name), encoding="utf-8").read())
            for n in ast.walk(tree):
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith(PHRASE + " — %s"):
                    bad.append("%s:%d" % (name, n.lineno))
        self.assertEqual([], bad, "a reader prefixes the phrase itself again - the stutter comes back: %s" % bad)


RED_PROOF = [
    {
        "why": "2026-09-29 (#77) - the helper leads every reason with the phrase, so nested readers stutter",
        "file": "tv/unknown_shelf.py",
        "find": "    return w if \"UNKNOWN\" in w else LEAD + w\n",
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
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
