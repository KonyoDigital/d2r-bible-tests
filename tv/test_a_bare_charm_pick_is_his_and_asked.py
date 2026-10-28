# -*- coding: utf-8 -*-
"""REG-2965 (integration int-4: REG-2839 meets REG-2895) - A MAGIC CHARM HE PICKED AND LEFT BARE IS HIS, AND ASKED.

REG-2839 files a magic planner pick he leaves bare, once, at Done. REG-2895's one charm rule names no home for a charm
whose affix it cannot read (his rule: a doubt is asked, never guessed). Meeting on one branch, measured on the whole page in
node: the planner's route said "stays unfiled" and the pick's caller then dropped its register record and never owned it -
a bare magic Small Charm was lost, and REG-2839's law went red. Now:

  * the pick is owned and its register record kept; it stays unfiled (no mule is guessed for it) and the status says the
    rule's question - "until you say which charm it is";
  * the pick counts as kept, so its register record is not dropped behind it (and a later clear of the pick sees it);

Driven on the whole page in node (vault_page_node), fixtures only. RED_PROOF below.
"""
import json
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
import test_a_magic_pick_files_once_with_its_mods as MP  # noqa: E402  (its fixture world)

BODY = r"""
(function(){
var W = window, DB = W._cbDb();
function code(n){ return Object.keys(DB.b).find(function(c){ return DB.b[c][0] === n; }); }
function owned_(){ return JSON.parse(W.LSR.getItem('d2r_owned') || '[]'); }
function mf(){ return JSON.parse(W.LSR.getItem('d2r_magicFinds') || '{}'); }
function st(){ var e = document.getElementById('vault-status'); return e ? String(e.textContent || '') : ''; }
W.vaultPlannerOpen(''); W._cbChoose('b:' + code('Small Charm')); W._cbQuality('m'); W.vaultPlannerClose(); H.flush(60, 3);
OUT.bare = { owned: owned_().indexOf('Small Charm') >= 0, record: !!mf()['Small Charm'], filed: W._vaultFiledOn('Small Charm'),
             status: st() };
OUT.errors = H.errors.slice();
})();
"""


class ABareCharmPickIsHisAndAsked(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VPN.NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        cls.o = VPN.run(BODY, prelude=MP.PRELUDE, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["errors"], [])

    def test_the_bare_charm_is_owned_kept_unfiled_and_asked(self):
        b = self.o["bare"]
        self.assertTrue(b["owned"], "a bare magic charm pick was lost: %r" % b)
        self.assertTrue(b["record"], "its register record was dropped: %r" % b)
        self.assertIsNone(b["filed"], "a home was guessed for a charm the rule cannot read: %r" % b)
        self.assertIn("until you say which charm it is", b["status"], b)


RED_PROOF = [
    {"why": "REG-2965 - the asked charm is never owned, so the pick is lost",
     "file": "bible.html",
     "find": "            window._ownedAdd(nm, { source: 'hand', by: 'the Vault planner', where: VP_WHERE });\n        } catch (eCo) {}\n",
     "replace": "            void 0;\n        } catch (eCo) {}\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2965 - the asked charm is not kept, so its register record is dropped",
     "file": "bible.html",
     "find": "    var kept = routed && (routed.filed || routed.mode === 'already' || routed.mode === 'asked');   /* REG-2965 - an asked charm is kept */\n",
     "replace": "    var kept = routed && (routed.filed || routed.mode === 'already');   /* REG-2965 - an asked charm is kept */\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2965 - the route says only 'stays unfiled', so nothing asks which charm it is",
     "file": "bible.html",
     "find": "      if (_chQ && _chQ.unsorted){\n",
     "replace": "      if (false){\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main()
