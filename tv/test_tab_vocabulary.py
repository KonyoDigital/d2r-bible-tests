"""v2480 — the console has ONE Chronicle-tab vocabulary, and both resolvers quote it.

⚠ THE DEFECT, MEASURED BEFORE THE FIX. Two producers emit two spellings of the same tab, and each
resolver understood only its own:

    tab          ledger_kind_for_tab      chronicle_kind
    'unique'     chronicle-uniques        None                <-- disagree
    'uniques'    None                     chronicle-uniques   <-- disagree
    'sets'       chronicle-sets           chronicle-sets      (agree, by luck of spelling)

  · `ct.detect(frame)` reports "unique" — chronicle_template.py:501 documents that vocabulary and
    the template's marker box at :165 is keyed on it.
  · `claude_read(frame)` reports "uniques" — READ_PROMPT asks the model for that word verbatim
    (tv_diablo.py:402-403).

Neither is wrong for its own producer, so neither could simply be renamed: the template's geometry
is keyed on one spelling and the model is instructed in the other. Nothing was broken on the day —
each half worked — but the two halves could never be crossed, and a reader of either file would
reasonably assume the other agreed.

A THIRD ENCODING went with it: `chronicle_kind` ended with `return "chronicle-" + tab`, correct
only because "uniques"/"sets" pluralise correctly. Handed "unique" it returned "chronicle-unique",
a ledger name nothing uses.

These pin the LAWS, not the roster: a new tab word is allowed, a new tab word understood by only
half the console is not.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

import chronicle_retro as CR  # noqa: E402
import chronicle_template as CT  # noqa: E402


class BothResolversAgree(unittest.TestCase):

    def _ck(self, tab):
        return CR.chronicle_kind({"scene": "chronicle", "chronicleTab": tab})

    def test_every_alias_resolves_the_same_in_both(self):
        """The whole point. Either spelling, same answer, both sides."""
        for spelling in sorted(CT.TAB_ALIASES):
            lk = CT.ledger_kind_for_tab(spelling)
            ck = self._ck(spelling)
            self.assertEqual(
                lk, ck,
                "%r resolves to %r through ledger_kind_for_tab and %r through chronicle_kind. "
                "Two halves of one console disagreeing about the same word is the defect this "
                "file exists for." % (spelling, lk, ck))

    def test_the_two_spellings_of_uniques_are_the_same_tab(self):
        """The exact pair that disagreed: the template says 'unique', the model says 'uniques'."""
        self.assertEqual(CT.canonical_tab("unique"), CT.canonical_tab("uniques"),
                         "the template's spelling and the model's spelling are still two tabs")
        self.assertEqual(CT.ledger_kind_for_tab("unique"), "chronicle-uniques")
        self.assertEqual(CT.ledger_kind_for_tab("uniques"), "chronicle-uniques")
        self.assertEqual(self._ck("unique"), "chronicle-uniques",
                         "chronicle_kind still refuses the template's spelling")
        self.assertEqual(self._ck("uniques"), "chronicle-uniques")

    def test_the_ledger_name_is_not_built_by_concatenation(self):
        """`"chronicle-" + tab` is right only for words that pluralise correctly."""
        self.assertEqual(
            self._ck("unique"), "chronicle-uniques",
            "chronicle_kind returned a name built from the tab word rather than read from the "
            "map — for 'unique' that yields 'chronicle-unique', which no ledger uses")

    def test_runewords_canonicalises_but_has_no_ledger(self):
        """Two different facts: a word I do not know, and a tab with no ledger path."""
        self.assertEqual(CT.canonical_tab("runewords"), "runewords",
                         "runewords is a real tab and must canonicalise")
        self.assertIsNone(CT.ledger_kind_for_tab("runewords"),
                          "runewords has no ledger today — NO_LEDGER_TABS says so on purpose")
        self.assertIsNone(self._ck("runewords"))

    def test_an_unknown_word_is_None_in_both(self):
        for junk in ("bogus", "chronicle", "stash", "  ", None):
            self.assertIsNone(CT.canonical_tab(junk), "%r canonicalised to something" % (junk,))
            self.assertIsNone(CT.ledger_kind_for_tab(junk))
            self.assertIsNone(self._ck(junk))


class NeitherProducerMayOUTGROWTheVocabulary(unittest.TestCase):
    """The self-maintaining half: a new tab word must be aliased or these go red."""

    def test_every_word_the_TEMPLATE_can_report_is_aliased(self):
        src = io.open(os.path.join(HERE, "chronicle_template.py"), encoding="utf-8").read()
        m = re.search(r'tab is one of ([^\n]+)', src)
        self.assertIsNotNone(
            m, "chronicle_template no longer documents its tab vocabulary, so this guard cannot "
               "check it — restore the sentence or re-derive this test")
        words = [w.strip().strip('"').strip("'") for w in re.findall(r'"(\w+)"', m.group(1))]
        self.assertTrue(words, "no tab words parsed out of the documented vocabulary")
        for w in words:
            self.assertIsNotNone(
                CT.canonical_tab(w),
                "the template can report tab=%r and the shared vocabulary does not know it, so "
                "chronicle_kind would silently refuse every frame carrying it." % w)

    def test_every_word_the_READ_PROMPT_asks_the_model_for_is_aliased(self):
        p = os.path.join(HERE, "tv_diablo.py")
        if not os.path.isfile(p):
            self.skipTest("tv_diablo.py is not on this machine")
        src = io.open(p, encoding="utf-8", errors="replace").read()
        i = src.find("chronicleTab = ONLY when scene=chronicle")
        self.assertGreater(i, 0, "the READ_PROMPT no longer explains chronicleTab — re-derive this")
        window = src[i:i + 900]
        words = re.findall(r'\\"(\w+)\\"\s*=\s*the\s', window)
        self.assertTrue(words, "no tab words parsed out of the READ_PROMPT: %s" % window[:120])
        for w in words:
            self.assertIsNotNone(
                CT.canonical_tab(w),
                "the READ_PROMPT asks the model to answer tab=%r and the shared vocabulary does "
                "not know it, so ledger_kind_for_tab would return None for every such read." % w)

    def test_the_alias_map_has_one_canonical_form_per_concept(self):
        """An alias pointing at a word that is not itself an alias is a dead end."""
        for spelling, canon in sorted(CT.TAB_ALIASES.items()):
            self.assertIn(canon, CT.TAB_ALIASES,
                          "%r canonicalises to %r, which is not itself in the map" % (spelling, canon))
            self.assertEqual(CT.TAB_ALIASES[canon], canon,
                             "%r is not a fixed point — canonicalising twice would move again"
                             % canon)


if __name__ == "__main__":
    unittest.main(verbosity=2)
