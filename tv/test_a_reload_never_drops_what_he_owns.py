# -*- coding: utf-8 -*-
"""REG-2400 (#162 item 1 + folded #144 item 6) - A RELOAD NEVER DROPS WHAT HE OWNS.

GrokBot #230 on v3783 (292 of his real frames x 3 rounds, headless), and again on v3784: d2r_owned went 272 -> 113 on ONE
reload (the 60-frame repro: 61 -> 30), and d2r_vaultRemoved stayed null - no journal row, no undo. The names lost were the
keepers the router itself sends to MAGIC & RARE (Chaotic Grand Charm of Pestilence, Sullied Grand Charm of Blight, Death
Loop, Wraith Grasp, Havoc Finger, Jewel of Daring) and, in #144 item 6, Ancient's Pledge and Breath of the Dying - names
the page's RUNEWORDS table spells "Ancients' Pledge" and "Breath of the Dying (BotD)".

The load-time prune (_v42_sanitizeWishlistOwned) asks every catalogue whether a name is real and used to read "no
catalogue knows it" as "he does not own it", then persist() wrote that over d2r_owned. Now its filter is a QUESTION and the
owned-load doctor answers it: a name the filter would drop is put back, KEPT, named in window._ownedLoadReceipt and painted
on the Vault (#vault-owned-kept). Only an entry that is not a name is set aside, and that is said with the entry itself.

WHAT THIS LAW HOLDS, on the SHIPPED prune cut whole from bible.html (with the page's real _norm, _safeJsonParse and
RUNEWORDS table) and run in node over a fake store, through two reloads:
  * every name GrokBot lost is still owned and still in the stored d2r_owned after each reload;
  * the doctor names exactly the names no catalogue knows, and never a name a catalogue does know (Harlequin Crest,
    Enigma, and "Ancients' Pledge" spelled the table's way);
  * an entry that is not a name is set aside and said, never silently;
  * the Vault paints what the load kept in plain words, and paints nothing when nothing was kept;
  * renderVault asks the paint, and the Vault has the one place it paints into.
A missing node raises: this law does not skip.
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")

NORM = ("function _norm(s){", "\n")
SAFE = ("const _safeJsonParse = (raw, fallback) => {", "\n};\n")
RUNEWORDS = ("const RUNEWORDS = [", "\n];\n")
PRUNE = ("(function _v42_sanitizeWishlistOwned() {", "\n  // v659 — GRAIL FOUND-SEED floor")
PAINT_CALL = ("    try { if (typeof window._vaultOwnedKeptPaint === 'function') window._vaultOwnedKeptPaint(); } "
              "catch (eK) {}   /* REG-2400 — what this load kept */\n")
SLOT = '<div id="vault-owned-kept" class="vault-organize vault-owned-kept" hidden></div>'

#: what GrokBot's 292-frame run lost on one reload (#162) and what #144 item 6 lost
ROLLED = ["Chaotic Grand Charm of Pestilence", "Sullied Grand Charm of Blight", "Death Loop", "Wraith Grasp",
          "Havoc Finger", "Jewel of Daring"]
TYPED_RUNEWORDS = ["Ancient's Pledge", "Breath of the Dying"]
#: names a catalogue on the page does know - the doctor must never call these "kept"
KNOWN = ["Harlequin Crest", "Enigma", "Ancients' Pledge", "Dread Grasp"]
NOT_NAMES = [5, None, ""]


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _cut(s, pair, inclusive_end=True):
    start, end = pair
    if s.count(start) != 1:
        raise AssertionError("anchor %r matched %d times - re-point this law" % (start[:60], s.count(start)))
    i = s.index(start)
    j = s.index(end, i)
    return s[i:j + (len(end) if inclusive_end else 0)]


def _node(body, owned, wishlist=None, assign=None):
    if NODE is None:
        raise AssertionError("node is not on this machine - this gate does not skip")
    s = _src()
    prune = _cut(s, PRUNE, inclusive_end=False) + "\n})();\n"
    js = r"""
var window = globalThis;
var RAW = {}, PERSISTS = 0, WARN = [];
console.warn = function(m){ WARN.push(String(m)); };
var LS = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
           setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; } };
%(norm)s
%(safe)s
%(runewords)s
var SUNDER_CHARMS = [], BASE_CLASS = { "Monarch": "shield" };
/* the catalogues the prune asks, as small as the case needs: a unique the registry holds, a roster */
var ITEM_REGISTRY = { "Harlequin Crest": { n: "Harlequin Crest" }, "The Stone of Jordan": { n: "The Stone of Jordan" } };
var _UNI_EXTRA = {}, _GRAIL_SEED = {}, _EXTRA_ITEM_SET = new Set();
window._gUniqueRoster = function(){ return ["Harlequin Crest", "The Stone of Jordan"]; };
function findSetPiece(){ return null; }
var wishlist, owned, magicFinds;
function persist(){
  PERSISTS++;
  LS.setItem('d2r_wishlist', JSON.stringify(Array.from(wishlist)));
  LS.setItem('d2r_owned', JSON.stringify(Array.from(owned)));
  LS.setItem('d2r_magicFinds', JSON.stringify(magicFinds));
}
/* ONE PAGE LOAD: read the stores the way bible.html does at :21331, then the shipped prune */
function pageLoad(){
  wishlist = new Set(_safeJsonParse(LS.getItem('d2r_wishlist'), []));
  owned = new Set(_safeJsonParse(LS.getItem('d2r_owned'), []));
  magicFinds = _safeJsonParse(LS.getItem('d2r_magicFinds'), {}) || {};
  %(prune)s
}
/* the Vault's paint target */
function El(){ this.hidden = true; this.innerHTML = ''; }
var SLOT = new El();
var document = { getElementById: function(id){ return id === 'vault-owned-kept' ? SLOT : null; } };
RAW['d2r_owned'] = JSON.stringify(%(owned)s);
RAW['d2r_wishlist'] = JSON.stringify(%(wishlist)s);
RAW['d2r_muleAssign'] = JSON.stringify(%(assign)s);
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
""" % {"norm": _cut(s, NORM), "safe": _cut(s, SAFE), "runewords": _cut(s, RUNEWORDS), "prune": prune,
       "owned": json.dumps(owned), "wishlist": json.dumps(wishlist or []), "assign": json.dumps(assign or {}),
       "body": body}
    # the program goes in on STDIN - a law never hands node its program on argv
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if r.returncode != 0:
        raise AssertionError("the cut prune did not run in node: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


class AReloadNeverDropsWhatHeOwns(unittest.TestCase):

    def _his_store(self):
        return KNOWN + ROLLED + TYPED_RUNEWORDS + NOT_NAMES

    def test_every_name_grokbot_lost_survives_two_reloads(self):
        got = _node("""
pageLoad();
OUT.first = { owned: Array.from(owned), stored: JSON.parse(RAW['d2r_owned']), receipt: window._ownedLoadReceipt,
              persists: PERSISTS };
pageLoad();
OUT.second = { owned: Array.from(owned), stored: JSON.parse(RAW['d2r_owned']), receipt: window._ownedLoadReceipt,
               persists: PERSISTS };
OUT.warn = WARN;
""", self._his_store(), assign={"Dread Grasp": "magic-rare"})
        for load in ("first", "second"):
            g = got[load]
            for n in ROLLED + TYPED_RUNEWORDS + KNOWN:
                self.assertIn(n, g["owned"], "%s reload: %r left owned - the reload dropped what he owns" % (load, n))
                self.assertIn(n, g["stored"], "%s reload: %r is gone from the stored d2r_owned" % (load, n))
        self.assertEqual(got["first"]["persists"], 1, "the load wrote d2r_owned without a reason it can name")
        self.assertEqual(got["second"]["persists"], 1, "a clean second load rewrote d2r_owned")

    def test_the_doctor_names_what_no_catalogue_knows_and_nothing_else(self):
        got = _node("pageLoad(); OUT.r = window._ownedLoadReceipt; OUT.warn = WARN;",
                    self._his_store(), assign={"Dread Grasp": "magic-rare"})
        r = got["r"]
        self.assertEqual(sorted(r["kept"]), sorted(ROLLED + TYPED_RUNEWORDS),
                         "the doctor's kept list is not the names no catalogue knows: %r" % r["kept"])
        for n in KNOWN:
            self.assertNotIn(n, r["kept"], "%r is a name a catalogue knows - it is not a refusal" % n)
        self.assertTrue(r["refused"])
        self.assertEqual(r["names"], len(KNOWN + ROLLED + TYPED_RUNEWORDS))
        said = [w for w in got["warn"] if w.startswith("[bible] KEPT ")]
        self.assertEqual(len(said), 1, "the refusal was not said in the console: %r" % got["warn"])
        for n in ROLLED + TYPED_RUNEWORDS:
            self.assertIn(n, said[0])

    def test_an_entry_that_is_not_a_name_is_set_aside_and_said(self):
        got = _node("pageLoad(); OUT.r = window._ownedLoadReceipt; OUT.stored = JSON.parse(RAW['d2r_owned']); "
                    "OUT.warn = WARN;", self._his_store())
        self.assertEqual(got["r"]["notNames"], NOT_NAMES, "a non-name entry was not named")
        self.assertEqual([x for x in got["stored"] if not isinstance(x, str) or not x], [])
        dropped = [w for w in got["warn"] if w.startswith("[bible] dropped ")]
        self.assertEqual(len(dropped), 1, got["warn"])
        self.assertIn("NOT NAMES, SET ASIDE", dropped[0], "setting aside a non-name entry was not said")
        for n in ROLLED + TYPED_RUNEWORDS:
            self.assertNotIn(n, dropped[0].split("WISHLIST")[0], "%r is named as dropped" % n)

    def test_the_vault_says_what_the_load_kept_and_nothing_when_nothing_was(self):
        got = _node("""
pageLoad(); window._vaultOwnedKeptPaint(); OUT.kept = { hidden: SLOT.hidden, html: SLOT.innerHTML };
RAW['d2r_owned'] = JSON.stringify(['Harlequin Crest']);
pageLoad(); window._vaultOwnedKeptPaint(); OUT.clean = { hidden: SLOT.hidden, html: SLOT.innerHTML };
""", self._his_store())
        k = got["kept"]
        self.assertFalse(k["hidden"], "the Vault kept the refusal hidden")
        self.assertIn("a reload never drops what you own", k["html"])
        self.assertIn("no catalogue on this page knows", k["html"])
        for n in ROLLED:
            self.assertIn('data-name="%s"' % n, k["html"], "%r is kept but not shown on the Vault" % n)
        self.assertIn("Ancient&#39;s Pledge", k["html"], "a name with an apostrophe is not escaped on the Vault")
        self.assertIn("not an item name", k["html"], "the set-aside entries are not said on the Vault")
        self.assertTrue(got["clean"]["hidden"], "the Vault shows a refusal on a load that refused nothing")
        self.assertEqual(got["clean"]["html"], "")

    def test_the_doctor_compares_before_with_after_and_keeps_both(self):
        # the doctor is defined by the load itself, so the load runs first (on a store with nothing to refuse)
        got = _node("pageLoad(); OUT.d = window._ownedLoadDoctor(['a', 'b', 5, 'a'], new Set(['a', 'c']));",
                    ["Harlequin Crest"])
        d = got["d"]
        self.assertEqual(d["keep"], ["a", "b", "c"], "the doctor lost a name from before or after: %r" % d["keep"])
        self.assertEqual(d["receipt"]["kept"], ["b"])
        self.assertEqual(d["receipt"]["notNames"], [5])

    def test_render_vault_paints_it_into_the_one_place_on_the_vault(self):
        s = _src()
        self.assertEqual(s.count(PAINT_CALL), 1, "renderVault no longer paints what the load kept")
        self.assertEqual(s.count(SLOT), 1, "the Vault has no single place for what the load kept")
        hand = s.index('<div id="vault-hand-left"')
        self.assertLess(hand, s.index(SLOT), "the kept list moved away from the hand-add note it sits beside")


RED_PROOF = [
    {"why": "REG-2400 - a reload drops an owned name no catalogue knows again (the doctor's answer is not applied)",
     "file": "bible.html",
     "find": "  owned = new Set(_old.keep);\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2400 - the refusal goes silent: a kept name is never named",
     "file": "bible.html",
     "find": "      if (!has(n)) kept.push(n);       /* the filter would have dropped it: refused - it stays, and it is named */\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2400 - the doctor keeps only what the filter kept (its before is the filter's after)",
     "file": "bible.html",
     "find": "      seenN[n] = 1; keep.push(n);\n",
     "replace": "      seenN[n] = 1; if (has(n)) keep.push(n);\n",
     "matches": 1},
    {"why": "REG-2400 - the Vault never shows what the load kept",
     "file": "bible.html",
     "find": "    el.hidden = false; el.innerHTML = h; return R;\n",
     "replace": "    el.hidden = true; el.innerHTML = ''; return R;\n",
     "matches": 1},
    {"why": "REG-2400 - renderVault no longer paints the kept list",
     "file": "bible.html",
     "find": "    try { if (typeof window._vaultOwnedKeptPaint === 'function') window._vaultOwnedKeptPaint(); } "
             "catch (eK) {}   /* REG-2400 — what this load kept */\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
