# -*- coding: utf-8 -*-
"""#146 step 5 (REG-1822) — THE VAULT SAYS WHERE EACH UNSORTED ITEM WOULD GO, BY NAME, AND MOVES NOTHING.

His ask (2026-10-01): "Vault organizer: proposed destination per item ... never moved by itself". The first cut printed
only the router's reason ("armor slot — Shako") and kept the mule in an attribute, so no row ever said WHICH mule; and
the throw-out review and "keep it on your MAIN" were painted as proposed homes. Driven over the SHIPPED ⟦VAULT PROPOSE⟧
block and the board's own no-home sentence (_vNoHomeWhy):

  · A MULE ON THIS BOARD IS NAMED: "→ UNI-WEAPONS — <the router's reason>", data-state proposed, data-home its id.
  · THE THROW-OUT REVIEW IS ADVICE, NOT A HOME: data-state throwout, "throw-out advice — <reason>", no data-home.
  · __keep IS NOT A MULE: data-state keep, no data-home.
  · null IS THE SHARED STASH, said in the door's own sentence; a lock on his MAIN stays (the router is not asked).
  · UNKNOWN STAYS UNKNOWN: an id with no mule on this board (the door's own "routed to ... but no mule" sentence), a
    reason the router did not give, a router that throws or is absent — each says so and names no home.
  · THE ORGANIZER moves nothing: a head line says so, at most VAULT_ORG_SHOWN rows (and how many more), no control, no
    store write, hidden when nothing is unsorted; renderVault paints it from the dock's own unsorted list plus the loot
    he carries (#264, v3620 - the cap is read from the page, never pinned here).

A missing node raises — this law does not skip. RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys  # noqa: E402
if HERE not in _sys.path:
    _sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  - REG-1834: these print non-ASCII
_console_safe_enable()

BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = os.environ.get("NODE") or shutil.which("node")

PARK = "nothing on the board recognises this name — parked in weapons, worth your eye"
LOCK = "seen in your equipment in 4 separate sessions"
TRASH = "trade value TRASH — advice only"
PROPOSE_A, PROPOSE_B = "  /* ⟦VAULT PROPOSE BEGIN⟧ */\n", "  /* ⟦VAULT PROPOSE END⟧ */\n"
NOHOME_A, NOHOME_B = "  function _vNoHomeWhy(nm, home){\n", "  window._vaultNoHomeWhy = _vNoHomeWhy;\n"
SHARED_A, SHARED_B = "  var SHARED_STASH_RE = ", "  try { window.isSharedStash = isSharedStash; }"

HARNESS = r"""
var window = globalThis, WRITES = 0, ELS = {}, CALLS = [];
window.LSR = { getItem: function(){ return null; }, setItem: function(){ WRITES++; }, removeItem: function(){ WRITES++; } };
function El(id){ this.id = id || ''; this.hidden = true; this._html = ''; }
Object.defineProperty(El.prototype, 'innerHTML', { set: function(h){ this._html = String(h); }, get: function(){ return this._html; } });
var document = { getElementById: function(id){ return ELS[id] || null; } };
ELS['vault-organize'] = new El('vault-organize');
var ROSTER = [{ id: 'uni-weap', name: 'UNI-WEAPONS' }, { id: 'uni-armor', name: 'UNI-ARMOR' }];
function muleById(id){ return ROSTER.find(function(m){ return m.id === id; }); }
function _vhEsc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){
  return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
%(shared)s
%(nohome)s
%(propose)s
var OUT = {};
%(body)s
process.stdout.write(JSON.stringify(OUT));
"""


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _cut(s, a, b):
    if s.count(a) != 1:
        raise AssertionError("anchor %r matched %d times" % (a[:60], s.count(a)))
    i = s.index(a)
    return s[i:s.index(b, i + len(a))]


def code_only(text):
    """`text` with its /* */ and // comments blanked — a guard grades CODE, never the prose that explains it."""
    text = re.sub(r"/\*.{0,6000}?\*/", " ", text, flags=re.S)
    return "\n".join(re.sub(r"(^|\s)//.*$", r"\1", ln) for ln in text.split("\n"))


def _node(body):
    if not NODE:
        raise AssertionError("node is not on this machine — this law does not skip")
    s = _src()
    prog = HARNESS % {"shared": _cut(s, SHARED_A, SHARED_B), "nohome": _cut(s, NOHOME_A, NOHOME_B),
                      "propose": _cut(s, PROPOSE_A, PROPOSE_B), "body": body}
    p = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise AssertionError("the propose harness would not run — UNKNOWN, not passing: " + (p.stderr or p.stdout)[-2000:])
    return json.loads(p.stdout)


ROUTER = r"""
window.suggestMule = function(nm){
  CALLS.push(nm);
  if (nm === 'Battlecage') return { id: 'uni-weap', why: %(park)s };
  if (nm === 'Harlequin Crest') return { id: 'uni-armor', why: 'armor slot — Shako' };
  if (nm === 'Short Sword') return { id: '__throwout', why: %(trash)s };
  if (nm === 'Annihilus') return { id: '__keep', why: 'keep in your inventory — only works on the character you are actively playing' };
  if (nm === 'Ghost') return { id: 'uni-ghost', why: 'a home this board never had' };
  if (nm === 'Ort Rune') return null;
  if (nm === 'Nope') return { id: 'uni-weap' };
  if (nm === 'Boom') throw new Error('router down');
  return { id: 'uni-weap', why: 'weapon — base: ' + nm };
};
""" % {"park": json.dumps(PARK), "trash": json.dumps(TRASH)}


class TheVaultProposesAHomeAndDoesNotMove(unittest.TestCase):

    def test_a_mule_proposal_names_the_mule(self):
        out = _node(ROUTER + r"""
          OUT.p = window.vaultPropose('Battlecage');
          OUT.line = window.vaultProposeLine('Battlecage');
          OUT.armor = window.vaultProposeLine('Harlequin Crest');
          OUT.writes = WRITES;
        """)
        self.assertEqual(out["p"]["kind"], "mule")
        self.assertEqual(out["p"]["home"], "UNI-WEAPONS")
        self.assertFalse(out["p"]["moved"])
        self.assertIn('data-state="proposed"', out["line"])
        self.assertIn('data-home="uni-weap"', out["line"])
        self.assertIn("→ UNI-WEAPONS — " + PARK, out["line"], "the proposal does not name its mule")
        self.assertIn("→ UNI-ARMOR — armor slot — Shako", out["armor"])
        self.assertEqual(out["writes"], 0)

    def test_throw_out_and_keep_are_not_homes(self):
        out = _node(ROUTER + r"""
          OUT.trash = window.vaultProposeLine('Short Sword');
          OUT.keep = window.vaultProposeLine('Annihilus');
          OUT.shared = window.vaultProposeLine('Ort Rune');
        """)
        self.assertIn('data-state="throwout"', out["trash"])
        self.assertIn("throw-out advice — " + TRASH, out["trash"])
        self.assertIn('data-state="keep"', out["keep"])
        self.assertIn("stays with your MAIN, not a mule", out["keep"])
        self.assertIn('data-state="shared"', out["shared"])
        self.assertIn("belongs in the shared stash — there is no mule for it", out["shared"])
        for k in ("trash", "keep", "shared"):
            self.assertNotIn("data-home", out[k], "%s was painted as a proposed home" % k)
            self.assertNotIn('data-state="proposed"', out[k], "%s was painted as a proposed home" % k)

    def test_unknown_names_no_home(self):
        out = _node(ROUTER + r"""
          OUT.ghost = window.vaultProposeLine('Ghost');
          OUT.nowhy = window.vaultProposeLine('Nope');
          OUT.boom = window.vaultProposeLine('Boom');
          delete window.suggestMule;
          OUT.gone = window.vaultProposeLine('Battlecage');
          OUT.blank = window.vaultPropose('  ');
        """)
        self.assertIn('routed to &quot;uni-ghost&quot; but no mule with that id exists on this board', out["ghost"])
        self.assertIn("the router gave no reason", out["nowhy"])
        self.assertIn("the router could not be asked", out["boom"])
        self.assertIn("the router is not on this page", out["gone"])
        for k in ("ghost", "nowhy", "boom", "gone"):
            self.assertIn('data-state="unknown"', out[k])
            self.assertNotIn("data-home", out[k], "an unknown answer named a home (%s)" % k)
            self.assertNotIn("UNI-WEAPONS", out[k])
        self.assertFalse(out["blank"]["ok"])

    def test_a_throw_is_not_an_absent_router(self):
        """REG-1851 — a proposal that raised says so; "the router is not on this page" is a different, wrong reason."""
        out = _node(ROUTER + r"""
          muleById = function(){ throw new Error('roster unreadable'); };
          OUT.line = window.vaultProposeLine('Battlecage');
        """)
        self.assertIn('data-state="unknown"', out["line"])
        self.assertIn("the proposal could not be worked out", out["line"])
        self.assertNotIn("the router is not on this page", out["line"])
        self.assertNotIn("data-home", out["line"])

    def test_a_locked_name_stays_and_the_router_is_not_asked(self):
        out = _node(ROUTER + r"""
          window._laneLockWhy = function(nm){ return nm === 'Harlequin Crest' ? { lane: 'equipment', why: %s } : null; };
          OUT.line = window.vaultProposeLine('Harlequin Crest');
          OUT.calls = CALLS.slice();
          OUT.open = window.vaultProposeLine('Stone of Jordan');
          OUT.openCalls = CALLS.slice();
        """ % json.dumps(LOCK))
        self.assertIn('data-state="stays"', out["line"])
        self.assertIn("stays where it is — " + LOCK, out["line"])
        self.assertNotIn("data-home", out["line"])
        self.assertEqual(out["calls"], [])
        self.assertIn('data-home="uni-weap"', out["open"])
        self.assertEqual(out["openCalls"], ["Stone of Jordan"])

    def test_the_organizer_moves_nothing_and_says_how_many(self):
        out = _node(ROUTER + r"""
          OUT.empty = window.vaultOrganizePaint([]);
          OUT.hidden = ELS['vault-organize'].hidden;
          OUT.bad = window.vaultOrganizePaint(null);
          OUT.paint = window.vaultOrganizePaint(['Battlecage', 'a < b', 'Short Sword']);
          OUT.html = ELS['vault-organize']._html;
          var many = []; for (var i = 0; i < VAULT_ORG_SHOWN + 1; i++) many.push('Item ' + i);
          OUT.cap = VAULT_ORG_SHOWN;
          OUT.many = window.vaultOrganizePaint(many);
          OUT.manyHtml = ELS['vault-organize']._html;
          OUT.writes = WRITES;
        """)
        self.assertEqual(out["empty"]["n"], 0)
        self.assertTrue(out["hidden"])
        self.assertFalse(out["bad"]["ok"])
        self.assertEqual(out["paint"]["n"], 3)
        self.assertIn("nothing moves until you move it", out["html"])
        self.assertIn('data-name="Battlecage"', out["html"])
        self.assertIn("→ UNI-WEAPONS — " + PARK, out["html"])
        self.assertIn('data-name="a &lt; b"', out["html"])
        self.assertIn('data-state="throwout"', out["html"])
        self.assertNotIn("onclick", out["html"])
        self.assertNotIn("<button", out["html"])
        cap = out["cap"]
        self.assertEqual(cap, int(re.search(r"var VAULT_ORG_SHOWN = (\d+);", _src()).group(1)), "the harness read another cap")
        self.assertEqual(out["many"]["shown"], cap)
        self.assertEqual(out["manyHtml"].count('class="vault-org-row" data-name='), cap)
        self.assertIn("%d of %d shown" % (cap, cap + 1), out["manyHtml"])
        self.assertEqual(out["writes"], 0)

    def test_the_joins(self):
        s = _src()
        code = code_only(s)
        self.assertEqual(code.count('            window.vaultOrganizePaint(unsorted, (_carried || []).map(function(c){ return c.name; })); } catch (eO) {}\n'), 1)
        dock_at = code.find("dock.innerHTML = unsorted.map(function(n){")
        self.assertGreater(dock_at, 0)
        self.assertNotIn("vaultPropose", code[dock_at:code.find(".join('');", dock_at)])
        self.assertEqual(s.count('id="vault-organize"'), 1)
        propose = code_only(_cut(s, PROPOSE_A, PROPOSE_B))
        for banned in ("setItem(", "removeItem(", "assign[", "vaultFile(", "vaultAutoAssign", "onclick"):
            self.assertNotIn(banned, propose, "the organizer reaches %s" % banned)


RED_PROOF = [
    {
        "why": "REG-1851 - a proposal that raised must say so; printing 'the router is not on this page' is a wrong reason",
        "file": "bible.html",
        "find": "    if (!pg) return span('unknown', threw ? 'the proposal could not be worked out — this page raised while asking' : 'the proposal gave no answer');\n",
        "replace": "    if (!pg) return span('unknown', 'the router is not on this page');\n",
        "matches": 1,
    },
    {
        "why": "a proposal names its mule; printing the reason alone is the defect this law was written for",
        "file": "bible.html",
        "find": "    if (pg.kind === 'mule') return span('proposed', '→ ' + pg.home + ' — ' + pg.why, pg.id);\n",
        "replace": "    if (pg.kind === 'mule') return span('proposed', pg.why, pg.id);\n",
        "matches": 1,
    },
    {
        "why": "the throw-out review is advice; without its own branch it is painted as a proposed home",
        "file": "bible.html",
        "find": "    if (id === '__throwout') return { ok: true, moved: false, kind: 'throwout', id: id, home: null, why: why };\n",
        "replace": "    if (id === '__throwout') return { ok: true, moved: false, kind: 'mule', id: id, home: 'the throw-out review', why: why };\n",
        "matches": 1,
    },
    {
        "why": "an id with no mule on this board is UNKNOWN; without the check a ghost home is named",
        "file": "bible.html",
        "find": "    if (!mule) return no(_vNoHomeWhy(nm, id));\n",
        "replace": "    if (!mule) mule = { name: id };\n",
        "matches": 1,
    },
    {
        "why": "a locked name stays; deleting the lock return offers it a mule",
        "file": "bible.html",
        "find": "    if (held && held.why) return { ok: true, moved: false, kind: 'stays', id: null, home: null, why: String(held.why) };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the dock's unsorted items must be asked; dropping the paint leaves the organizer unjoined",
        "file": "bible.html",
        "find": '            window.vaultOrganizePaint(unsorted, (_carried || []).map(function(c){ return c.name; })); } catch (eO) {}\n',
        "replace": "            void 0; } catch (eO) {}\n",   # the whole call statement goes; the try still closes
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
