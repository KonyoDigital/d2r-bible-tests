# -*- coding: utf-8 -*-
"""REG-3006 + REG-3007 (#111, his ruling 2026-10-29 Q10) - A CHARM DRAWS ITS OWN PICTURE, NEVER ANOTHER CHARM'S.

art/logo_charm.png is one charm's picture: the Latent Black Cleft totem. Measured on the whole page before this, artUrl
answered it for exactly six names - the six "Renewed <sunder>" charms - because they had no key in D2IO_ART and
_fillExtraUniqueArt gave each its base's _magicArtSrc, which mapped EVERY charm to that file. His ruling: every item's
picture matches the game, everywhere. A Renewed charm is the charm itself, so it draws its plain charm's own carving in
that charm's colours (Bone Break's white stone, Flame Rift's orange totem), read off the one list of the six
(SUNDER_CHARMS) into the table every surface reads: artOr (rows, vault cells, FIND), the hover, the Forge, the console's
copy of D2IO_ART. The same file was the answer for every magic charm too (a magic Grand Charm's hover, a rolled
"... Grand Charm" name): _magicArtSrc now draws a charm by its size, the three base sprites the table holds, and a charm
whose size the words do not say gets no picture.

Driven on the whole page in node (vault_page_node), a fresh store. RED_PROOF below.
"""
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

import vault_page_node as VPN  # noqa: E402

LOGO = "art/logo_charm.png"
MAGIC = {"Grand Charm": "art/hd_charm_large.png", "Large Charm": "art/hd_charm_medium.png",
         "Small Charm": "art/hd_charm_small.png", "Lion Branded Grand Charm of Vita": "art/hd_charm_large.png",
         "Shimmering Small Charm of Good Luck": "art/hd_charm_small.png", "Fine Large Charm of Balance": "art/hd_charm_medium.png",
         "Skiller (gc)": "art/hd_charm_large.png", "charm": None}

BODY = r"""
(function(){
var SIX = SUNDER_CHARMS.map(function(s){ return s.n; });
OUT.six = SIX.map(function(p){
  var r = 'Renewed ' + p, tip = null;
  try { tip = _arttipResolve(r); } catch (e) { tip = { err: String(e) }; }
  var orHtml = '';
  try { orHtml = String(artOr(r, '', 'sm') || ''); } catch (e2) { orHtml = 'threw ' + e2; }
  return { plain: p, plainArt: artUrl(p), latentArt: artUrl('Latent ' + p), renewedArt: artUrl(r),
           table: D2IO_ART[r] || null, hover: tip && tip.artName ? artUrl(tip.artName) : null, artOr: orHtml };
});
OUT.logoNames = window.__allItemNames().filter(function(n){ return artUrl(n) === 'art/logo_charm.png'; });
OUT.logoKeys = Object.keys(D2IO_ART).filter(function(k){ return D2IO_ART[k] === 'art/logo_charm.png'; });
OUT.magic = {};
%(magic)s.forEach(function(b){ OUT.magic[b] = _magicArtSrc(b); });
OUT.jewel = _magicArtSrc('Rare Jewel');
magicFinds['Lion Branded Grand Charm of Vita'] = { q: 'magic', base: 'Grand Charm' };
var t = null; try { t = _arttipResolve('Lion Branded Grand Charm of Vita'); } catch (e3) { t = { err: String(e3) }; }
OUT.magicHover = t && (t.artSrc || (t.artName ? artUrl(t.artName) : null));
})();
"""

_RUNS = {}


def page():
    if "p" not in _RUNS:
        import json
        _RUNS["p"] = VPN.run(BODY % {"magic": json.dumps(sorted(MAGIC))}, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ARenewedSunderDrawsItsPlainCarving(unittest.TestCase):

    def test_the_premise_six_sunders_each_with_its_own_plain_and_latent_picture(self):
        o = page()
        self.assertEqual(o["__boot"]["errors"], [], o["__boot"])
        self.assertEqual(len(o["six"]), 6, "PREMISE: the page no longer lists six sunders: %r" % [r["plain"] for r in o["six"]])
        for r in o["six"]:
            self.assertTrue(r["plainArt"] and r["plainArt"] != LOGO, "PREMISE: %s has no plain carving: %r" % (r["plain"], r))
            self.assertIn("/mr_latent", r["latentArt"] or "", "the Latent %s lost its own icon: %r" % (r["plain"], r))
        self.assertEqual(len({r["plainArt"] for r in o["six"]}), 6, "PREMISE: the six plain charms share a picture")

    def test_each_renewed_charm_draws_its_plain_charms_carving_everywhere(self):
        for r in page()["six"]:
            self.assertEqual(r["renewedArt"], r["plainArt"], "Renewed %s draws %r, not its charm's %r" % (r["plain"], r["renewedArt"], r["plainArt"]))
            self.assertEqual(r["table"], r["plainArt"], "the table (the console's copy reads it) says %r for Renewed %s" % (r["table"], r["plain"]))
            self.assertEqual(r["hover"], r["plainArt"], "the hover of Renewed %s draws %r" % (r["plain"], r["hover"]))
            self.assertIn('src="%s' % r["plainArt"], r["artOr"], "a row / vault cell / FIND row of Renewed %s: %s" % (r["plain"], r["artOr"][:200]))

    def test_no_item_draws_another_charms_totem(self):
        o = page()
        self.assertEqual(o["logoNames"], [], "items still drawn as the Latent Black Cleft totem: %r" % o["logoNames"])
        self.assertEqual(o["logoKeys"], [], "table keys still holding the totem: %r" % o["logoKeys"])

    def test_a_magic_charm_draws_its_size(self):
        o = page()
        self.assertEqual(o["magic"], MAGIC, "a magic charm's picture is not its size's sprite")
        self.assertEqual(o["jewel"], "art/jewel02_graphic.png", "PREMISE: the jewel branch below the charms moved")
        self.assertEqual(o["magicHover"], "art/hd_charm_large.png", "a magic Grand Charm's hover draws %r" % o["magicHover"])


RED_PROOF = [
    {"why": "REG-3006 - the Renewed names keep no key, so each draws its base's generic art",
     "file": "bible.html",
     "find": "  if (p && Object.prototype.hasOwnProperty.call(D2IO_ART, p)) D2IO_ART['Renewed ' + p] = D2IO_ART[p];\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-3006 - every Renewed name draws the first charm's carving",
     "file": "bible.html",
     "find": "D2IO_ART['Renewed ' + p] = D2IO_ART[p];\n",
     "replace": "D2IO_ART['Renewed ' + p] = D2IO_ART[SUNDER_CHARMS[0].n];\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3007 - every charm draws the Latent Black Cleft totem again",
     "file": "bible.html",
     "find": "    if(/\\bsmall\\b|\\(sc\\)/.test(b)) return 'art/hd_charm_small.png';\n",
     "replace": "    return 'art/logo_charm.png';\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-3007 - a charm of unknown size is drawn as another charm",
     "file": "bible.html",
     "find": "    if(/\\bgrand\\b|skiller|\\(gc\\)/.test(b)) return 'art/hd_charm_large.png';\n    return null;\n",
     "replace": "    if(/\\bgrand\\b|skiller|\\(gc\\)/.test(b)) return 'art/hd_charm_large.png';\n    return 'art/logo_charm.png';\n",
     "matches": 1, "needs": "node"},
]


if __name__ == "__main__":
    unittest.main()
