# -*- coding: utf-8 -*-
"""#158.6 (REG-2814, GrokBot on his real frames; his circlet ruling, #144 item 3) - A RARE CIRCLET WITH NO STATS READ NEEDS A
TOOLTIP LOOK; IT IS NOT FILED AS IF JUDGED.

GrokBot: a rare circlet read off a ground label (the name, mods []) went straight to MAGIC & RARE. His circlet ruling keeps a
circlet for what it rolled (+2 class skills, FCR, FRW), so a circlet nobody saw the lines of cannot have been judged.
MEASURED on the whole page in node before the fix: suggestMule answered "RARE circlet - keep (+skills/FCR/res + facet
sockets)" for mods [] exactly as for a circlet whose lines were read, and the one filing door (vaultFile, no mule named)
filed it with that sentence.

Now the router answers Unsorted with "needs a tooltip look" when no stat line was read (blank lines are no lines), the filing
door refuses with that sentence, and a circlet whose lines were read is judged as before; a white or magic circlet is still
vendor advice. Driven on the whole page in node (vault_page_node, fresh empty storage). RED_PROOF below.
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

BODY = r"""
(function(){
function route(n){ var s = suggestMule(n); return s ? { id: s.id === undefined ? null : s.id, unsorted: !!s.unsorted, why: String(s.why || '') } : null; }
function file(n){ var r = window.vaultFile(n, { by: 'hand', at: new Date(1).toISOString(), where: 'the law' }, {});
  return r ? { ok: !!r.ok, refused: r.refused || null, why: String(r.why || '') } : null; }
magicFinds['Grim Circlet'] = { q: 'rare', base: 'Circlet', mods: [], at: 1 };
magicFinds['Blank Tiara'] = { q: 'rare', base: 'Tiara', mods: ['', '   '], at: 1 };
magicFinds['Storm Diadem'] = { q: 'rare', base: 'Diadem', mods: ['+2 to Sorceress Skill Levels', '20% Faster Cast Rate'], at: 1 };
magicFinds['Sharp Coronet'] = { q: 'magic', base: 'Coronet', mods: [], at: 1 };
['Grim Circlet', 'Blank Tiara', 'Storm Diadem', 'Sharp Coronet'].forEach(function(n){ owned.add(n); });
OUT.noMods = route('Grim Circlet'); OUT.blankMods = route('Blank Tiara');
OUT.readMods = route('Storm Diadem'); OUT.magic = route('Sharp Coronet');
OUT.fileNoMods = file('Grim Circlet'); OUT.fileReadMods = file('Storm Diadem');
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ACircletWithNoStatsReadNeedsALook(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, timeout=400)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_no_stat_read_is_unsorted_and_says_it_needs_a_look(self):
        for k in ("noMods", "blankMods"):
            r = self.o[k]
            self.assertEqual((r["id"], r["unsorted"]), (None, True), "%s: a circlet with no stat read was judged: %r" % (k, r))
            self.assertIn("needs a tooltip look", r["why"])

    def test_the_filing_door_refuses_it_with_that_sentence(self):
        f = self.o["fileNoMods"]
        self.assertEqual((f["ok"], f["refused"]), (False, "unsorted"), "it was filed as if judged: %r" % f)
        self.assertIn("needs a tooltip look", f["why"])

    def test_a_circlet_whose_lines_were_read_is_judged_as_before(self):
        self.assertEqual(self.o["readMods"]["id"], "magic-rare", self.o["readMods"])
        self.assertTrue(self.o["fileReadMods"]["ok"], self.o["fileReadMods"])
        self.assertEqual(self.o["magic"]["id"], "__throwout", "PREMISE: a magic circlet is vendor advice (his ruling)")


RED_PROOF = [
    {"why": "REG-2814 - a rare circlet with no stats read is kept in MAGIC & RARE as if judged again",
     "file": "bible.html",
     "find": "          if (!_cmods.length)\n            return {id:null, unsorted:true, why:'RARE circlet with no stats read (a ground label)",
     "replace": "          if (false)\n            return {id:null, unsorted:true, why:'RARE circlet with no stats read (a ground label)",
     "matches": 1, "needs": "node"},
    {"why": "REG-2814 - blank lines count as stats read",
     "file": "bible.html",
     "find": "            .filter(function(x){ return typeof x === 'string' && x.trim(); });\n",
     "replace": "            .filter(function(x){ return x != null; });\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
