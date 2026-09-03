# -*- coding: utf-8 -*-
"""A8 — the templates must be what the routing filters WITH, not a pass beside it.

His ask: *"the templates also need to be within the printer filtering and routing correctly and
discarding"* — and the testable form TASKS.md gives it: **if a template can be removed without the
routing changing, it is not wired in.**

⚠⚠ MEASURED, AND IT WAS THE INVERSE. `resolve_tab` named ANY tab present in the marker dict,
including one with no template band at all — handed `{"tab_marker": {"hardcore": 0.05}}` it answered
`hardcore`, a tab `TAB_BANDS` has never heard of. `geometry_signals` only ever produces keys from
TAB_BANDS today, so nothing was wrong on this tree; the router's correctness rested on an upstream
convention it did not check. That is the shape that breaks the day a band is renamed, a dict is
merged, or an artefact adds a key. [[the-unjoined-end]]

⚠ A tab that can be ROUTED WITHOUT A TEMPLATE is the opposite of what A8 asks for.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import chronicle_template as CT   # noqa: E402

LIT = (CT._TAB_MARKER_MIN + CT._TAB_MARKER_MAX) / 2.0


class OnlyATabWithATemplateMayBeNamed(unittest.TestCase):

    def test_a_tab_with_no_template_band_is_never_named(self):
        tab, why = CT.resolve_tab({"tab_marker": {"hardcore": LIT}})
        self.assertIsNone(
            tab,
            "resolve_tab named %r, a tab TAB_BANDS has never heard of. The template is then not "
            "the mechanism the routing filters with — it is a convention the router trusts "
            "without checking." % tab)
        self.assertIn("NO TEMPLATE BAND", why,
                      "it refused without saying the tab had no template, so a reader cannot tell "
                      "this refusal from an unreadable band")

    def test_every_banded_tab_can_still_be_named(self):
        """⚠ BASELINE: a filter that refuses everything would pass the test above and be useless."""
        for t in sorted(CT.TAB_BANDS):
            tab, _why = CT.resolve_tab({"tab_marker": {t: LIT}})
            self.assertEqual(tab, t,
                             "%r has a template band and could not be named — the filter is now "
                             "refusing legitimate reads" % t)

    def test_a_stray_key_no_longer_makes_a_real_read_ambiguous(self):
        """⚠ THIS IS A DELIBERATE BEHAVIOUR CHANGE AND IT IS PINNED SO IT IS NOT MISTAKEN FOR ONE.

        Before: an undeclared key counted as a second lit window, so the whole read went AMBIGUOUS
        and refused — safe, and it threw away a legitimate answer. Now the undeclared key is
        dropped with its reason and the real marker wins.
        """
        tab, why = CT.resolve_tab({"tab_marker": {"sets": LIT, "hardcore": LIT}})
        self.assertEqual(tab, "sets", "a real marker was lost to an undeclared sibling: %s" % why)
        self.assertIn("hardcore", why,
                      "the dropped key is not named in the reason, so the drop is invisible")

    def test_two_REAL_tabs_lit_is_still_ambiguous(self):
        """The drop must not have widened into 'pick one'. A Sets page tallied as Uniques writes a
        wrong count into his grail truth — that refusal is the whole point of the check."""
        tab, why = CT.resolve_tab({"tab_marker": {"sets": LIT, "unique": LIT}})
        self.assertIsNone(tab, "two REAL tabs lit and it named %r anyway" % tab)
        self.assertIn("ambiguous", why.lower())

    def test_a_contaminated_window_is_still_excluded(self):
        tab, why = CT.resolve_tab({"tab_marker": {"sets": CT._TAB_MARKER_MAX + 1.0}})
        self.assertIsNone(tab)
        self.assertIn("CONTAMINATED", why)

    def test_removing_a_template_makes_its_tab_unnameable(self):
        """A8's own test, run literally: take a template away and the routing must change."""
        real = dict(CT.TAB_BANDS)
        try:
            CT.TAB_BANDS.pop("sets")
            tab, why = CT.resolve_tab({"tab_marker": {"sets": LIT}})
            self.assertIsNone(
                tab,
                "the `sets` template was REMOVED and the routing still named `sets`. That is the "
                "definition of a template that is not wired in.")
        finally:
            CT.TAB_BANDS.clear()
            CT.TAB_BANDS.update(real)
        self.assertEqual(CT.resolve_tab({"tab_marker": {"sets": LIT}})[0], "sets",
                         "the template was not restored, so this test damaged the module")

    def test_every_ledger_tab_has_a_template(self):
        """A tab the ledger knows but the templates cannot see would route to a ledger kind that
        nothing can ever produce."""
        missing = [t for t in CT._LEDGER_KIND_BY_TAB if t not in CT.TAB_BANDS]
        self.assertFalse(
            missing,
            "%s have a ledger kind but no template band, so nothing can ever route to them"
            % missing)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
