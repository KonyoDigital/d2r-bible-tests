# -*- coding: utf-8 -*-
"""#202 - HIS RULING 2026-10-27 ~21:00: AUTO INTAKE REGISTERS AN ITEM ONLY ON ITS SECOND SESSION.

His words: "auto intake needs two witnesses at least by the code it should be already built that way no no its the 2
sessions to file to a mule is the same logic in registering that item".

Measured at v3812: the inner tvVaultRegister called _ownedAdd on every call, so ONE frame read made an item his; only the
filing waited for 2 sessions. Now a READ of a name he does not own is held in d2r_vaultSighted until VAULT_WITNESS_MIN
distinct sessions have seen it, counted by the filing's own rule (_vaultLookCounts: its own session, its own frame, over
the floor when scored; s_1 and its re-look s_1#2 are one session). Then it registers - and files - in the same call.

Driven on the whole page in node through the real door (window.tvVaultRegister):
  - one session: refused one-session, not owned, held with its look, listed as pending;
  - the same session on another frame: still held;
  - a second session: owned, and the hold is cleared;
  - a 0.40 look is not a session; s_1 and s_1#2 are one;
  - his hand registers at once; a name he owns is a re-read; a call with NO witness (a restore of what he had) is not
    a read and is not held;
  - an unreadable hold store holds every read and is never written over; his hand still works.
RED_PROOF below.
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

SEED = r"""
localStorage.setItem('d2r_ownerClaim', '*');
localStorage.setItem('d2r_owned', JSON.stringify(["The Gnasher"]));
localStorage.setItem('d2r_vaultProv', JSON.stringify({}));
localStorage.setItem('d2r_muleAssign', JSON.stringify({}));
"""

BODY = r"""
(function(){
var W = window, S1 = 's_1791232871109_10831', S2 = 's_1791239851249_40429', S3 = 's_1791247000000_55555';
function look(s, f, conf){ return { session: s, frame: f, lane: 'stash', conf: conf == null ? 0.9 : conf, cell: 'stash:c3r4' }; }
function reg(nm, looks){ var r = W.tvVaultRegister(nm, { lane: 'stash', location: 'stash', cell: 'stash:c3r4', witnesses: looks, sessions: looks });
  return r ? { ok: !!r.ok, refused: r.refused || null, pending: r.pending || null } : null; }
function held(nm){ try { var m = JSON.parse(localStorage.getItem('d2r_vaultSighted') || '{}'); return m[nm] ? m[nm].looks.length : 0; } catch (e) { return -1; } }
W._vaultAutoIntakeSet && W._vaultAutoIntakeSet(true);
OUT.one = reg('Treachery', [look(S1, 'f_1791233980015.jpg')]);
OUT.oneOwned = owned.has('Treachery'); OUT.oneHeld = held('Treachery');
OUT.pending = (W._vaultIntakePending() || []).filter(function(e){ return e.name === 'Treachery'; });
OUT.popLine = String(W._vaultPopHtml({ owned: 1, filed: 0, carried: 0, orphans: 0, loose: 0, sp: 0, pending: 1 })).replace(/<[^>]+>/g, '');
OUT.popUnknown = String(W._vaultPopHtml({ owned: 1, filed: 0, carried: 0, orphans: 0, loose: 0, sp: 0, pending: null })).replace(/<[^>]+>/g, '');
OUT.again = reg('Treachery', [look(S1, 'f_1791233980999.jpg')]);
OUT.againOwned = owned.has('Treachery'); OUT.againHeld = held('Treachery');
OUT.two = reg('Treachery', [look(S2, 'f_1791239854075.jpg')]);
OUT.twoOwned = owned.has('Treachery'); OUT.twoHeld = held('Treachery');
/* a look under the floor is not a session; a re-look of the same session is the same session */
OUT.low1 = reg('Lidless Wall', [look(S1, 'f_1.jpg', 0.9)]);
OUT.low2 = reg('Lidless Wall', [look(S2, 'f_2.jpg', 0.40)]);
OUT.lowOwned = owned.has('Lidless Wall');
OUT.low3 = reg('Lidless Wall', [look(S3, 'f_3.jpg', 0.8)]);
OUT.low3Owned = owned.has('Lidless Wall');
OUT.relook1 = reg('Skin of the Vipermagi', [look(S1, 'f_4.jpg')]);
OUT.relook2 = reg('Skin of the Vipermagi', [look(S1 + '#2', 'f_5.jpg')]);
OUT.relookOwned = owned.has('Skin of the Vipermagi');
/* his hand, a re-read of his own item, and a restore with no witness */
var h = W.tvVaultRegister('Stormshield', { by: 'hand', at: new Date().toISOString(), where: 'the law' });
OUT.hand = !!(h && h.ok) && owned.has('Stormshield');
/* his hand on a row the reader brought (the inbox's "Vault only" on a read row carries its frame) */
var hf = W.tvVaultRegister('Bul-Kathos\' Wedding Band', { by: 'hand', at: new Date().toISOString(), where: 'the law', frame: 'f_9.jpg', session: S1 });
OUT.handFramed = !!(hf && hf.ok);
var a = W.tvVaultRegister('The Gnasher', { lane: 'stash', sessions: [look(S1, 'f_6.jpg')] });
OUT.already = !!(a && a.ok);
var b = W.tvVaultRegister('Arreat’s Face');
OUT.bare = !!(b && b.ok);
/* an unreadable hold store */
localStorage.setItem('d2r_vaultSighted', '{broken');
OUT.broken = reg('Shaftstop', [look(S1, 'f_7.jpg')]);
OUT.brokenOwned = owned.has('Shaftstop');
OUT.brokenBytes = localStorage.getItem('d2r_vaultSighted');
var h2 = W.tvVaultRegister('Lightsabre', { by: 'hand', at: new Date().toISOString(), where: 'the law' });
OUT.handBroken = !!(h2 && h2.ok);
})();
"""
_RUNS = {}


def page():
    if "p" not in _RUNS:
        _RUNS["p"] = VPN.run(BODY, prelude=SEED, timeout=300)
    return _RUNS["p"]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AutoIntakeRegistersOnTwoSessions(unittest.TestCase):

    def test_the_page_booted(self):
        self.assertEqual(page()["__boot"]["errors"], [], page()["__boot"])

    def test_one_session_is_held_not_owned(self):
        o = page()
        self.assertEqual((o["one"]["ok"], o["one"]["refused"]), (False, "one-session"), o["one"])
        self.assertEqual(o["one"]["pending"], {"sessions": 1, "need": 2}, o["one"])
        self.assertFalse(o["oneOwned"], "ONE session made the item his (#202)")
        self.assertEqual(o["oneHeld"], 1)
        self.assertEqual([(e["name"], e["sessions"]) for e in o["pending"]], [("Treachery", 1)], o["pending"])
        self.assertIn("1 seen once (not yours yet", o["popLine"], "the vault does not say what is waiting on a 2nd session")
        self.assertIn("seen once UNKNOWN", o["popUnknown"])
        self.assertEqual(o["again"]["refused"], "one-session", "the same session on another frame counted twice")
        self.assertFalse(o["againOwned"])
        self.assertEqual(o["againHeld"], 2)

    def test_the_second_session_registers_and_clears_the_hold(self):
        o = page()
        self.assertTrue(o["two"]["ok"], "the second session did not register it: %r" % o["two"])
        self.assertTrue(o["twoOwned"])
        self.assertEqual(o["twoHeld"], 0, "the hold outlived the registration")

    def test_a_low_look_or_a_re_look_is_not_a_second_session(self):
        o = page()
        self.assertEqual(o["low2"]["refused"], "one-session", "a 0.40 look counted as a session: %r" % o["low2"])
        self.assertFalse(o["lowOwned"])
        self.assertTrue(o["low3"]["ok"] and o["low3Owned"], o["low3"])
        self.assertEqual(o["relook2"]["refused"], "one-session", "s_1#2 counted as a second session: %r" % o["relook2"])
        self.assertFalse(o["relookOwned"])

    def test_his_hand_a_re_read_and_a_restore_are_not_held(self):
        o = page()
        self.assertTrue(o["hand"], "his hand was held")
        self.assertTrue(o["handFramed"], "his hand on a read row (with its frame) was held as a one-session read")
        self.assertTrue(o["already"], "a read of an item he owns was held")
        self.assertTrue(o["bare"], "a register with no witness (a restore of what he had) was held")

    def test_an_unreadable_hold_store_holds_every_read_and_is_never_written(self):
        o = page()
        self.assertEqual(o["broken"]["refused"], "hold-unknown", o["broken"])
        self.assertFalse(o["brokenOwned"])
        self.assertEqual(o["brokenBytes"], "{broken", "the unreadable store was written over")
        self.assertTrue(o["handBroken"], "his hand was refused because the seen-once store would not read")


RED_PROOF = [
    {"why": "#202 - the vault stops saying what it saw once and is waiting on",
     "file": "bible.html",
     "find": "    else if (typeof p.pending === 'number' && p.pending > 0)\n",
     "replace": "    else if (false)\n", "matches": 1, "needs": "node"},
    {"why": "#202 - one read makes an item his again",
     "file": "bible.html", "find": "        if (_h202 && _h202.hold) return _h202.answer; /* #202 two sessions register */\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#202 - the bar is one session again",
     "file": "bible.html", "find": "    if (n >= VAULT_WITNESS_MIN) return { hold: false, witness: Object.assign({}, w, { sessions: merged }), looks: merged, sessions: n };\n",
     "replace": "    if (n >= 1) return { hold: false, witness: Object.assign({}, w, { sessions: merged }), looks: merged, sessions: n };\n",
     "matches": 1, "needs": "node"},
    {"why": "#202 - the hold outlives the registration",
     "file": "bible.html", "find": "      try { window._vaultIntakeHoldForget(name); } catch (eHf2) {} /* #202 held looks are his now */\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "#202 - a re-look of the same session counts as a second session",
     "file": "bible.html", "find": "if (sid) seen[String(sid).split('#')[0]] = 1; });\n",
     "replace": "if (sid) seen[String(sid)] = 1; });\n", "matches": 1, "needs": "node"},
    {"why": "#202 - an unreadable hold store is read as empty and written over",
     "file": "bible.html", "find": "    try { var m = JSON.parse(raw); return (m && typeof m === 'object' && !Array.isArray(m)) ? m : null; } catch (e2) { return null; }\n",
     "replace": "    try { var m = JSON.parse(raw); return (m && typeof m === 'object' && !Array.isArray(m)) ? m : {}; } catch (e2) { return {}; }\n",
     "matches": 1, "needs": "node"},
    {"why": "#202 - his hand is held too",
     "file": "bible.html", "find": "      if (_isRead202 && !(_w0.by === 'hand' || _w0.source === 'hand') && !owned.has(name)) {\n",
     "replace": "      if (_isRead202 && !owned.has(name)) {\n", "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
