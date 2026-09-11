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

    def test_no_lookup_site_escapes_this_law(self):
        """★ THE SECOND EYE'S FINDING on v2963. `_LOOKUP` only sees
        `SHELF_RIVER[c.getAttribute('…')]` — single quotes, no local, no fallback. Double quotes,
        a local (`var k = c.getAttribute('data-n'); SHELF_RIVER[k]`), or a `|| ''` between `)` and
        `]` all slip past findall, and the REMAINING sites still agree on data-sid, so the law
        passes while the painter is back on the ordinal. A gate that claims to read whichever
        attribute the lookups use must not read only the ones spelled like today.
        [[source-reading-guard]]"""
        total = UI.count("SHELF_RIVER[")
        graded = len(_LOOKUP.findall(UI))
        self.assertEqual(total, graded,
                         "%d site(s) index SHELF_RIVER[ but only %d are graded — %d escape this "
                         "law. An ungraded site can hold the ordinal while every graded one agrees "
                         "on the session id: the measured bug in a different spelling."
                         % (total, graded, total - graded))

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
        # ★ THE SECOND EYE'S FINDING on v2963: assertIn("sessionId", ...) also accepts
        # `TH.sessionId` — the THEATRE's currently-open session — which would stamp every card
        # with one id. The card must be filled from its own row. [[label-outlived-referent]]
        self.assertIn("sm.sessionId", m.group(1),
                      "%r is filled from %r, not from the session id — the river's keys are "
                      "session ids, so anything else cannot match" % (attr, m.group(1).strip()))

    def test_the_map_is_still_keyed_by_the_reel_id(self):
        """[[the-unjoined-end]] — the fix must not be 'rekey the map to the ordinal', which would
        make the lookups agree and the river wrong.

        ★ THE SECOND EYE'S FINDING on v2963, and it was right: this asked only whether the
        characters `replace(/^reel_/, '')` appear ANYWHERE in a 1.7 MB page. Swap the operand —
        `String(x.n || '').replace(/^reel_/, '')` — and every river row keys as '', zero cards
        match, the grid reads "— not stamped" again while /api/river still reports stamps, and
        the string is still in the file so this test passed. It also carried NO red-proof, so
        heart2 could never notice it was blind to the one defect it exists to forbid.
        So grade the DERIVATION inside the map-build region. [[source-reading-guard]]"""
        i = UI.find("var m = {};")
        self.assertGreater(i, 0, "the map build is gone — this law lost its target")
        j = UI.find("SHELF_RIVER = m;", i)
        self.assertGreater(j, i, "could not find the end of the map build")
        region = UI[i:j]
        self.assertIn("x.reel", region,
                      "the river map's key is no longer derived from the REEL ID. /api/river keys "
                      "by reel id, so the two halves can now agree with each other and still "
                      "disagree with the backend")
        self.assertIn("replace(/^reel_/, '')", region,
                      "the reel_ prefix is no longer stripped inside the map build, so the keys "
                      "carry a prefix the card's session id never has")


class ASharedIdPlacesNothing(unittest.TestCase):
    """#58 / v2964 — the join was right and the KEY IS NOT UNIQUE.

    MEASURED on his console: 530 cards carry 419 distinct session ids, and one id is worn by
    ELEVEN cards with eleven different t0/t1/reads/verdicts — eleven different runs, not one run
    drawn eleven times. Of the river's 60 reels, 27 match exactly one card and 31 match many,
    and those 31 were painting a real station onto 80 cards the river never stamped.

    80 of 107 stamps were a right number under a name that is not its referent. The ambiguity is
    UPSTREAM — the river keys by reel id, a reel id is `reel_` + the session id, and the session
    id does not identify a run — so the UI cannot resolve it and must not invent.
    """

    def setUp(self):
        i = UI.find("  function _shStationOf(c){")
        self.assertGreater(i, 0, "_shStationOf is gone — this law lost its target")
        j = UI.find("\n  }", i)
        self.assertGreater(j, i, "could not find the end of _shStationOf")
        self.region = UI[i:j + 4]

    def test_a_station_is_withheld_when_the_id_is_shared(self):
        self.assertIn("_shSidCount(c) > 1", self.region,
                      "_shStationOf no longer asks how many cards wear this session id, so one "
                      "reel's station is painted onto every sibling run sharing its id — 80 of "
                      "107 stamps were wrong this way")
        after = self.region[self.region.find("_shSidCount(c) > 1"):]
        self.assertIn("return null", after.split("\n")[0] + after.split("\n")[1],
                      "the shared-id branch does not return null, so the guard reads as a check "
                      "and behaves as a no-op")

    def test_the_ambiguous_are_not_filed_as_never_stamped(self):
        """Two different facts: 'the river never stamped this' and 'it stamped one of the runs
        wearing this id and cannot say which'. Only the second is a data defect he can act on."""
        self.assertIn("shared id, cannot place", UI,
                      "the ambiguous cards have no bucket of their own, so they fall into "
                      "'not stamped' and a real upstream defect — a session id worn by 11 runs — "
                      "becomes invisible")
        self.assertIn("_shSidAmbiguous", UI,
                      "nothing distinguishes an ambiguous card from an unstamped one")

    def test_the_census_cannot_outlive_one_render(self):
        """thShelf rebuilds the grid with innerHTML, so a cached census would be a stale
        denominator deciding whether a stamp is withheld. [[stale-reading]]"""
        i = UI.find("  function _shSort(){")
        self.assertGreater(i, 0)
        head = UI[i:i + 700]
        self.assertIn("_SH_SID_N = null", head,
                      "the shared-id census is never reset at the top of _shSort, so it survives "
                      "a rebuild and counts a card set that no longer exists")


RED_PROOF = [
    {
        "why": "swapping the map key's operand off the reel id makes every river row key as '', so "
               "zero cards match and the grid reads not-stamped again while /api/river still "
               "reports stamps - the sabotage the eye showed would have stayed green",
        "file": "control_ui.html",
        "find": "var key = String(x.reel || '').replace(/^reel_/, '');",
        "replace": "var key = String(x.n || '').replace(/^reel_/, '');",
        "matches": 1,
    },
    {
        "why": "dropping the shared-id guard restores the measured defect: one reel's station painted onto every sibling run wearing its id, 80 wrong stamps of 107",
        "file": "control_ui.html",
        "find": "    if (_shSidCount(c) > 1) return null;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "folding the ambiguous cards back into 'not stamped' hides an upstream defect — a session id worn by 11 different runs — behind a bucket that means something else",
        "file": "control_ui.html",
        "find": '\\u2014 shared id, cannot place',
        "replace": '\\u2014 not stamped',
        "matches": 1,
    },
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
