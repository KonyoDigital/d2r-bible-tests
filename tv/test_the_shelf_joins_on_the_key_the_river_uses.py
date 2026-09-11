# -*- coding: utf-8 -*-
"""#58 — THE CARD AND THE RIVER MUST NAME THE SAME KEY.

`_shRiverLoad` builds SHELF_RIVER keyed by the reel id minus its `reel_` prefix — a SESSION ID
like `s_1784984019250_95276`. Three sites then looked the map up with `c.getAttribute('data-n')`,
which is the card's ORDINAL: "1", "3", "6". The two key spaces never intersect, so every lookup
returned undefined and EVERY reel rendered as "— not stamped".

MEASURED on his live console 2026-09-11, one page load, one moment:

    /api/river   60 reels stamped · 122 stamps · everStamped true · unparsed 0
    the grid     INTAKE 0 · TRIAGE 0 · STATION 0 · PRINTER 0 · JOIN 0 · CAPTURE 0 · ROUTED 0
                 — not stamped 530
    after the join was wired to the session id:
                 TRIAGE 2 · STATION 21 · PRINTER 5 · JOIN 21 · CAPTURE 34 · ROUTED 24
                 — not stamped 423

A comment sat directly above the map build saying "a reel id is 'reel_' + the session id the card
carries in data-n". It was wrong for the whole life of the feature, and it is why nobody looked
again — a comment that retires the defect in the reader's mind. [[measured-true-read-wrong]]

⚠ AND AN EMPTY MAP IS TRUTHY. `SHELF_RIVER = {}` passes `if (!SHELF_RIVER) return null`, so the
"the river could not be read" path never fired: a join matching NOTHING rendered exactly like a
river where nothing is stamped. [[unknown-stays-unknown]] [[the-unjoined-end]]

⚠ THIS LAW DOES NOT HARDCODE THE ATTRIBUTE NAME. It reads whichever attribute the lookups use and
then demands the card builder emit THAT one, so a rename moves both halves or the gate goes red.
Pinning the literal string `data-sid` would have been a law about today's spelling, not about the
joint. [[regression-guard]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

_LOOKUP = re.compile(r"SHELF_RIVER\[\s*c\.getAttribute\(\s*'([a-z-]+)'\s*\)\s*\]")
_CARD_START = "return '<div class=\"sh-card'"
_CARD_END = "data-search=\"'"


def _card_builder(case):
    """The `.sh-card` opening-tag expression, by anchors at both ends."""
    i = UI.find(_CARD_START)
    case.assertGreater(i, 0, "the .sh-card builder is gone — this law lost its target")
    j = UI.find(_CARD_END, i)
    case.assertGreater(j, i, "the card builder's closing anchor is gone")
    return UI[i:j + len(_CARD_END)]


class TheTwoHalvesNameOneKey(unittest.TestCase):

    def test_every_lookup_uses_the_same_attribute(self):
        found = _LOOKUP.findall(UI)
        self.assertGreater(len(found), 0,
                           "no SHELF_RIVER[c.getAttribute(...)] lookup found at all — this law has "
                           "lost its target and is measuring nothing")
        self.assertEqual(1, len(set(found)),
                         "the river map is looked up with %d DIFFERENT attributes: %s. One of them "
                         "is wrong and the screen cannot say which."
                         % (len(set(found)), sorted(set(found))))

    def test_the_card_emits_the_attribute_the_lookup_asks_for(self):
        """The defect verbatim: the map keyed by session id, read by ordinal."""
        attr = _LOOKUP.findall(UI)[0]
        card = _card_builder(self)
        self.assertIn('%s="' % attr, card,
                      "the river is looked up with %r, and the .sh-card builder never emits that "
                      "attribute. Every lookup returns undefined, so every reel renders as "
                      "'— not stamped' while the backend reports them stamped. The builder emits: "
                      "%s" % (attr, sorted(set(re.findall(r'(data-[a-z-]+)="', card)))))

    def test_the_attribute_carries_the_session_id_not_the_ordinal(self):
        """`data-n` is the card's position in the list — it is not a key into anything."""
        attr = _LOOKUP.findall(UI)[0]
        self.assertNotEqual("data-n", attr,
                            "the river map is keyed by session id (reel id minus 'reel_') and is "
                            "being read with data-n, the card's ORDINAL. The two key spaces never "
                            "intersect: 0 of 530 cards matched on his console")
        card = _card_builder(self)
        m = re.search(re.escape(attr) + r'="\'\s*\+\s*([A-Za-z_.()\s|\']+?)\s*\+', card)
        self.assertIsNotNone(m, "could not read what %r is filled from in the card builder" % attr)
        self.assertIn("sessionId", m.group(1),
                      "%r is filled from %r, not from the session id — the river's keys are "
                      "session ids, so anything else cannot match" % (attr, m.group(1).strip()))

    def test_the_map_is_still_keyed_by_the_reel_id(self):
        """[[the-unjoined-end]] — the fix must not be 'rekey the map to the ordinal', which would
        make the lookups agree and the river wrong."""
        self.assertIn("replace(/^reel_/, '')", UI,
                      "the map is no longer keyed by the reel id with its prefix stripped, so the "
                      "two halves may now agree with each other and disagree with /api/river")


RED_PROOF = [
    {
        "why": "putting any one lookup back on data-n reproduces the measured defect — the map is "
               "keyed by session id and read by ordinal, so 0 of 530 cards match",
        "file": "control_ui.html",
        "find": "var r = SHELF_RIVER[c.getAttribute('data-sid')];\n        var old = c.querySelector('.shc-river');",
        "replace": "var r = SHELF_RIVER[c.getAttribute('data-n')];\n        var old = c.querySelector('.shc-river');",
        "matches": 1,
    },
    {
        "why": "dropping data-sid from the card builder leaves the lookups asking for an attribute "
               "no card carries — every reel renders as not stamped again",
        "file": "control_ui.html",
        "find": 'data-sid="\' + esc(sm.sessionId || \'\') + \'" ',
        "replace": "",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
