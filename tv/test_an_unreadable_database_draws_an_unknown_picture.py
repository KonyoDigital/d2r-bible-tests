# -*- coding: utf-8 -*-
"""#41 rank 24 (REG-1536, 2026-09-29) — WHEN THE BUILDER'S DATABASE CANNOT BE READ, THE PICTURE IS UNKNOWN, NOT THE NAME.

The heart audit (verified list, rank 24): "If CB_DB fails to parse, the art rule quietly falls back to the item's own
name, which is the wrong picture #248 fixed." `_cbArtName` returned `(e && e.name) || '?'` when the database gave it
nothing, and both mule callers did `|| p.n` / `: e.name` — so a runeword drew whatever its own name resolves to (his
2026-09-27 screenshot: "Last Wish Thunder Maul" drew a SWORD) exactly when the database was unreadable.

WHAT THIS LAW DRIVES, in the SHIPPED blocks (⟦cb-builder-js⟧ and the mule window's _mpSlotArt, cut from bible.html
and run in node over the stand-in test_the_characters_tab_is_manual_and_separate uses):
  · THE POSITIVE CONTROL, the real database: a runeword's art name is its BASE's name (never its own), a unique's is
    its own; the mule slot draws that name.
  · THE DATABASE WOULD NOT PARSE: window._cbArtName answers NULL (never the item's own name); window._cbArtUnknown
    draws a glyph marked data-art="unknown" whose title carries DB_ERR's own sentence; the mule slot draws that glyph;
    the builder's doll says UNKNOWN. The tile path in the mule inventory reads the same null and draws the same glyph
    (its join pinned by the exact expressions, which no comment can carry).
RED_PROOF below.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

from test_the_characters_tab_is_manual_and_separate import BIBLE, NODE, _between, _run, _src   # the shipped harness

BROKEN_DB = "DBEL.textContent = '{not the database';"


def _slot_art(s):
    return "function _mpSlotArt(e, glyph){" + _between(s, "  function _mpSlotArt(e, glyph){", "\n  }\n") + "\n  }\n"


@unittest.skipIf(NODE is None, "node is not on this machine")
class AnUnreadableDatabaseDrawsAnUnknownPicture(unittest.TestCase):

    def test_with_the_real_database_a_runeword_draws_its_base_and_a_unique_its_own_name(self):
        body = _slot_art(_src()) + r"""
function art(n, glyph, size){ return '<art:' + n + ':' + size + '>'; }
seed('bHAM');
var d = window._cbDb(); OUT.dbOk = !!d;
/* the entries the builder itself makes for a pick (window._cbEntryFor): a runeword's base is its first allowed base */
var rw = null, un = null;
for (var i = 0; i < d.it.length && !(rw && un); i++){
  var it = d.it[i];
  if (!rw && it[2] === 'r'){ var er = window._cbEntryFor(it); if (er && d.b[er.base]) rw = { it: it, e: er }; }
  if (!un && it[2] === 'u'){ var eu = window._cbEntryFor(it); if (eu && d.b[eu.base]) un = { it: it, e: eu }; }
}
OUT.rw = rw ? { own: rw.it[1], base: d.b[rw.e.base][0], art: window._cbArtName(rw.e), slot: _mpSlotArt(rw.e, '◆') } : null;
OUT.un = un ? { own: un.it[1], art: window._cbArtName(un.e) } : null;
OUT.noId = _mpSlotArt({ name: 'Hand Placed' }, '◆');
"""
        out = _run(body)
        self.assertTrue(out["dbOk"])
        self.assertIsNotNone(out["rw"], "the database holds no runeword with a base on record")
        self.assertEqual(out["rw"]["base"], out["rw"]["art"], "a runeword did not draw its base (#248)")
        self.assertNotEqual(out["rw"]["own"], out["rw"]["art"])
        self.assertEqual("<art:%s:lg>" % out["rw"]["base"], out["rw"]["slot"], "the mule slot did not draw the base")
        self.assertIsNotNone(out["un"])
        self.assertEqual(out["un"]["own"], out["un"]["art"], "a unique has a picture of its own")
        self.assertEqual("<art:Hand Placed:lg>", out["noId"], "an entry with no database id draws its own name")

    def test_an_unparseable_database_answers_null_and_draws_the_unknown_glyph(self):
        body = _slot_art(_src()) + r"""
function art(n, glyph, size){ return '<art:' + n + ':' + size + '>'; }
seed('bHAM');
OUT.db = window._cbDb();
OUT.name = window._cbArtName({ id: 'rw-last-wish', base: 'thm', name: 'Last Wish Thunder Maul' });
OUT.plain = window._cbArtName({ name: 'Last Wish Thunder Maul' });
OUT.unk = window._cbArtUnknown('sm');
OUT.slot = _mpSlotArt({ id: 'rw-last-wish', base: 'thm', name: 'Last Wish Thunder Maul' }, '◆');
try { window.openCharBuilder('bHAM'); OUT.doll = String(ELS['cb-win']._html); } catch (e) { OUT.doll = 'THREW ' + (e && e.message); }
"""
        out = _run(body, raw_patch=BROKEN_DB)
        self.assertIsNone(out["db"], "the fixture did not break the database")
        self.assertIsNone(out["name"], "the art name fell back to the item's own name: %r" % out["name"])
        self.assertIsNone(out["plain"])
        self.assertIn('data-art="unknown"', out["unk"])
        self.assertIn("picture UNKNOWN", out["unk"])
        self.assertIn("would not parse", out["unk"], "the glyph does not carry DB_ERR's own reason")
        self.assertIn('data-art="unknown"', out["slot"], "the mule slot drew a name instead of the UNKNOWN glyph: %r" % out["slot"][:80])
        self.assertNotIn("Last Wish", out["slot"])
        self.assertIn("UNKNOWN", out["doll"], "the builder's doll did not say UNKNOWN: %r" % out["doll"][:120])

    def test_the_inventory_tile_reads_the_same_null_and_draws_the_same_glyph(self):
        """The tile renderer sits inside the mule window's inventory paint and cannot be cut alone; its join to the
        null answer is pinned by the two exact expressions (a comment cannot carry an assignment)."""
        src = io.open(BIBLE, encoding="utf-8").read()
        self.assertEqual(1, src.count("if (_ar === null) _anUnk = true; else _an = _ar || p.n;"),
                         "the tile no longer reads the builder's null answer")
        self.assertEqual(1, src.count("(_anUnk ? window._cbArtUnknown(p.w > 1 && p.h > 1 ? '' : 'sm') : art(_an, '◆', p.w > 1 && p.h > 1 ? '' : 'sm'))"),
                         "the tile no longer draws the UNKNOWN glyph on a null answer")


RED_PROOF = [
    {
        "why": "#41 rank 24 - an unreadable database falls back to the item's own name again (the wrong picture #248 fixed)",
        "file": "../bible.html",
        "find": "    if (!_cbDb()) return null;\n    var it = e && _cbItem(e.id), own = !!(it && (it[2] === 'u' || it[2] === 's'));",
        "replace": "    var it = e && _cbItem(e.id), own = !!(it && (it[2] === 'u' || it[2] === 's'));",
        "matches": 1,
    },
    {
        "why": "#41 rank 24 - the UNKNOWN glyph loses its mark and its reason",
        "file": "../bible.html",
        "find": "d2art-failed cb-art-unknown\" data-art=\"unknown\" title=\"'\n      + esc('picture UNKNOWN — ' + (DB_ERR || 'the builder database could not be read')) + '\">",
        "replace": "d2art-failed\">",
        "matches": 1,
    },
    {
        "why": "#41 rank 24 - the mule slot draws the item's own name on a null answer",
        "file": "../bible.html",
        "find": "    return n === null ? window._cbArtUnknown('lg') : art(n, glyph, 'lg');",
        "replace": "    return art(n === null ? e.name : n, glyph, 'lg');",
        "matches": 1,
    },
    {
        "why": "#41 rank 24 - the inventory tile falls back to p.n on a null answer",
        "file": "../bible.html",
        "find": "if (_ar === null) _anUnk = true; else _an = _ar || p.n;",
        "replace": "_an = _ar || p.n;",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if NODE is None:
        sys.stderr.write("⚪ SKIP — node is not on this machine, so the art rule was not driven. UNMEASURED, declared (77).\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
