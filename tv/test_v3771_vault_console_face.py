# -*- coding: utf-8 -*-
"""v3771 — the vault controls wear the console's gold, and an unseen place says so.

The MF / TZ / quick-set bar is position:fixed at z-index 120, so it painted over
the move list. While the Vault tab is the room, the room stacks above that bar
and under the sticky header. A holder with no location is not 'UNKNOWN · UNKNOWN'.
It reads 'Location not seen yet', asks for a screenshot, and sorts last.

RED_PROOF below. [[heart-first]] [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
"""
import json
import os
import shutil
import subprocess
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

BIBLE = os.path.join(HERE, "..", "bible.html")
NODE = os.environ.get("NODE") or shutil.which("node")

from test_v3767_copy_witness import _fn  # noqa: E402
from test_v3769_vault_move_list import PREAMBLE, move_bundle  # noqa: E402

EXTRA = [
    "_vaultRoomStack", "_vaultRoomApply", "_vaultRoomLift",
    "_vaultCoverVerdict", "_vaultMoveCovered",
]


class TestV3771VaultConsoleFace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine — this law does not skip")
        with open(BIBLE, encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.bundle = move_bundle(cls.src) + "\n" + "\n".join(_fn(cls.src, n) for n in EXTRA)

    def _run(self, body):
        prog = PREAMBLE + "\n" + self.bundle + "\n" + body
        raw = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
        self.assertEqual(raw.returncode, 0, (raw.stderr or "")[-2500:] + "\n" + (raw.stdout or "")[-800:])
        line = [ln for ln in raw.stdout.splitlines() if ln.startswith("{") or ln.startswith("[")][-1]
        return json.loads(line)

    def test_an_unseen_holder_is_labeled_and_sorted_last(self):
        o = self._run(r"""
function row(name, holder, loc, cell){
  return { name: name, copyIx: 0, witnesses: 1, task: _vaultMoveTask({
    name: name,
    from: { holder: holder, location: loc, cell: cell },
    to: { holder: 'UNI-ARMOR', location: 'stash', cell: 'stash:c1r1' },
    status: 'to-move'
  })};
}
var groups = _vaultMoveGroup([
  row("Harlequin Crest", null, null, null),
  row("Griffon's Eye", 'UNI-ARMOR', 'stash', 'stash:c0r0'),
  row('Zzznotanitem', null, 'stash', 'stash:c1r0'),
  row("Enigma", 'MAIN', 'inventory', 'inventory:c0r0')
]);
var html = _vaultMoveHtml({ tasks: [], groups: groups, locks: [] });
console.log(JSON.stringify({
  labels: groups.map(function(g){ return g.label; }),
  last: groups[groups.length - 1].label,
  unseen: groups[groups.length - 1].unseen === true,
  hint: html.indexOf('Take a screenshot so the console can see where it sits.') >= 0,
  cls: html.indexOf('vmv-unseen') >= 0,
  data: html.indexOf('data-unseen="1"') >= 0,
  collided: html.indexOf('UNKNOWN · UNKNOWN') >= 0
}));
""")
        self.assertEqual(o["labels"][0], "MAIN", o)
        self.assertEqual(o["last"], "Location not seen yet", o)
        self.assertTrue(o["unseen"], o)
        self.assertIn("UNKNOWN", o["labels"], o)
        self.assertNotIn("Location not seen yet", o["labels"][:-1], o)
        self.assertTrue(o["hint"], o)
        self.assertTrue(o["cls"], o)
        self.assertTrue(o["data"], o)
        self.assertFalse(o["collided"], o)

    def test_a_known_stash_with_no_holder_stays_unknown(self):
        o = self._run(r"""
var g = _vaultMoveGroup([{ name: 'Zzznotanitem', copyIx: 0, task: _vaultMoveTask({
  name: 'Zzznotanitem',
  from: { holder: null, location: 'stash', cell: 'stash:c0r0' },
  to: { holder: 'UNI-ARMOR', location: 'stash', cell: 'stash:c2r2' },
  status: 'to-move'
}) }])[0];
console.log(JSON.stringify({
  label: g.label, stash: g.stash, unseen: g.unseen === true,
  say: _vaultMovePlaceSay(g.rows[0].task.from)
}));
""")
        self.assertEqual(o["label"], "UNKNOWN", o)
        self.assertEqual(o["stash"], "private stash", o)
        self.assertFalse(o["unseen"], o)
        self.assertNotEqual(o["say"], "Location not seen yet", o)

    def test_an_unseen_place_says_so(self):
        o = self._run(r"""
console.log(JSON.stringify({
  bare: _vaultMovePlaceSay({ holder: null, location: null, cell: null }),
  empty: _vaultMovePlaceSay({ holder: '', location: '', cell: '' }),
  known: _vaultMovePlaceSay({ holder: 'MAIN', location: 'inventory', cell: 'inventory:c1r1' }),
  flag: _vaultMoveUnseen(null, null) === true,
  held: _vaultMoveUnseen('Mule', null) === true
}));
""")
        self.assertEqual(o["bare"], "Location not seen yet")
        self.assertEqual(o["empty"], "Location not seen yet")
        self.assertNotIn("UNKNOWN", o["known"], o)
        self.assertTrue(o["flag"])
        self.assertFalse(o["held"])

    def test_the_bar_stacks_under_the_vault_and_under_the_header(self):
        o = self._run(r"""
var z = _vaultRoomStack();
function el(){ return { style: { zIndex: '', position: '' }, classList: { contains: function(){ return false; } } }; }
var tab = el(), dock = el(), tz = el();
var on = _vaultRoomApply(tab, dock, tz, true);
var offTab = el(), offDock = el();
offDock.style.zIndex = '120';
var off = _vaultRoomApply(offTab, offDock, el(), false);
document.documentElement = { getAttribute: function(k){ return k === 'data-active-tab' ? 'vault' : null; } };
document.getElementById = function(id){
  return { 'tab-vault': tab, 'control-dock': dock, 'v42-tz-countdown': tz }[id] || null;
};
var lifted = _vaultRoomLift();
console.log(JSON.stringify({
  vault: z.vault, bar: z.bar,
  clears: on.clears, tab: tab.style.zIndex, dock: dock.style.zIndex, pos: tab.style.position,
  offClears: off.clears, offDock: offDock.style.zIndex, offPos: offTab.style.position,
  lifted: lifted.clears && lifted.on
}));
""")
        self.assertGreater(o["vault"], o["bar"], o)
        self.assertLess(o["vault"], 100, o)
        self.assertGreaterEqual(o["bar"], 1, o)
        self.assertTrue(o["clears"], o)
        self.assertEqual(o["tab"], "40", o)
        self.assertEqual(o["dock"], "20", o)
        self.assertEqual(o["pos"], "relative", o)
        self.assertTrue(o["offClears"], o)
        self.assertEqual(o["offDock"], "", o)
        self.assertEqual(o["offPos"], "", o)
        self.assertTrue(o["lifted"], o)
        self.assertIn("clears: tv > dv && tv < 100", self.src)
        self.assertIn(
            "window._vaultRoomLift(); } catch (eLift) {} /* v3771 room lift */", self.src)

    def test_a_bar_hit_inside_the_list_box_covers_it(self):
        o = self._run(r"""
console.log(JSON.stringify({
  hit: _vaultCoverVerdict([{ onBar: false }, { onBar: true }]).covered,
  clear: _vaultCoverVerdict([{ onBar: false }, { onBar: false }]).covered,
  none: _vaultCoverVerdict([]).covered
}));
""")
        self.assertTrue(o["hit"])
        self.assertFalse(o["clear"])
        self.assertFalse(o["none"])

    def test_the_controls_keep_the_console_type(self):
        self.assertIn(
            ".vault-move .vault-btn,.vault-move .vmv-mark,.vault-move .vmv-wit{font-family:var(--serif-display,serif);",
            self.src)
        self.assertIn("#vault-auto-intake{font-family:var(--serif-display,serif);", self.src)
        self.assertIn(".vmv-gh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;", self.src)
        self.assertIn("font-family:var(--serif-display,serif);", self.src[self.src.find(".vmv-gh{"):self.src.find(".vmv-gh{") + 500])
        self.assertIn(".vmv-q{min-width:180px;flex:1;font-family:var(--serif-text,Georgia,serif);", self.src)
        self.assertIn("['#control-dock .dock-inner', '#v42-tz-countdown']", self.src)
        self.assertIn(
            r'.vault-toolbar > button.vault-btn[onclick*="_vaultMoveAddOpen"]{font-family:var(--serif-display,serif);',
            self.src)

    def test_distinct_attacks_clear_the_vault_apply_wilson_bar(self):
        from confidence import confluence, wilson_lower
        import self_arming as SA
        bar = SA.LOCKS["vault.apply"]["bar"]
        kinds_bar = SA.LOCKS["vault.apply"]["kinds_bar"]
        n = len(RED_PROOF)
        w = wilson_lower(n, n)
        conf = confluence(["sabotage"], SA.KINDS)
        msg = ("vault console face: %d distinct attacks, wilson %.4f vs vault.apply bar %.3f; "
               "kinds sabotage %.2f vs %.2f" % (n, w, bar, conf, kinds_bar))
        print(msg)
        self.assertGreaterEqual(n, 10, msg)
        self.assertGreaterEqual(w, bar, msg)
        self.assertLess(conf, kinds_bar, msg)
        self.assertEqual(round(conf, 2), 1.00)


RED_PROOF = [
    {"why": "An unseen holder is labeled UNKNOWN again, so the group reads UNKNOWN · UNKNOWN.",
     "file": "bible.html",
     "find": "label: unseen ? 'Location not seen yet' : (holder == null ? 'UNKNOWN' : holder), rows: [] }; /* v3771 unseen label */",
     "replace": "label: holder == null ? 'UNKNOWN' : holder, rows: [] }; /* v3771 unseen label */",
     "matches": 1},
    {"why": "The unseen group sorts first, ahead of MAIN.",
     "file": "bible.html",
     "find": "if (g.unseen) return 3; /* v3771 unseen last */",
     "replace": "if (g.unseen) return 0; /* v3771 unseen last */",
     "matches": 1},
    {"why": "The screenshot hint is gone, so the group no longer says what to do.",
     "file": "bible.html",
     "find": "<span class=\"vmv-hint\">Take a screenshot so the console can see where it sits.</span>",
     "replace": "<span class=\"vmv-hint\"></span>",
     "matches": 1},
    {"why": "The unseen group loses its marker, so the console style and the gate cannot see it.",
     "file": "bible.html",
     "find": "(g.unseen ? ' vmv-unseen' : '')",
     "replace": "''",
     "matches": 1},
    {"why": "An unseen place is spelled UNKNOWN · UNKNOWN on the row.",
     "file": "bible.html",
     "find": "if (_vaultMoveUnseen(place.holder, place.location)) return 'Location not seen yet'; /* v3771 unseen say */",
     "replace": "if (false) return 'Location not seen yet'; /* v3771 unseen say */",
     "matches": 1},
    {"why": "Nothing is unseen, so a holder with no location stays in the UNKNOWN group.",
     "file": "bible.html",
     "find": "return !named && !stash; /* v3771 unseen place */",
     "replace": "return false; /* v3771 unseen place */",
     "matches": 1},
    {"why": "A private stash whose holder was not named is called not seen yet.",
     "file": "bible.html",
     "find": "if (location === 'stash') return 'private stash'; /* v3769 stash label */",
     "replace": "if (location === 'stash') return null; /* v3769 stash label */",
     "matches": 1},
    {"why": "The bar stacks above the vault room, so it covers the move list again.",
     "file": "bible.html",
     "find": "return { vault: 40, bar: 20 }; /* v3771 bar under vault */",
     "replace": "return { vault: 10, bar: 120 }; /* v3771 bar under vault */",
     "matches": 1},
    {"why": "The room is lifted over the header, so the sticky masthead slides under the vault.",
     "file": "bible.html",
     "find": "return { on: true, clears: tv > dv && tv < 100, vault: tv, bar: dv }; /* v3771 room clears */",
     "replace": "return { on: true, clears: tv > dv, vault: tv, bar: dv }; /* v3771 room clears */",
     "matches": 1},
    {"why": "Opening the vault does not write the room's z-index, so the fixed bar stays on top.",
     "file": "bible.html",
     "find": "setZ(tab, String(z.vault));",
     "replace": "if (false) setZ(tab, String(z.vault));",
     "matches": 1},
    {"why": "Leaving the vault leaves the bar's z-index cleared into a number that still covers rows.",
     "file": "bible.html",
     "find": "setZ(dock, '');",
     "replace": "setZ(dock, '120');",
     "matches": 1},
    {"why": "A hit on the bar inside the list box is reported as clear.",
     "file": "bible.html",
     "find": "if (list[i] && list[i].onBar) return { covered: true }; /* v3771 cover hit */",
     "replace": "if (false && list[i] && list[i].onBar) return { covered: true }; /* v3771 cover hit */",
     "matches": 1},
    {"why": "renderVault no longer lifts the room, so the paint and the stacking never meet.",
     "file": "bible.html",
     "find": "window._vaultRoomLift(); } catch (eLift) {} /* v3771 room lift */",
     "replace": "/* v3771 room lift */",
     "matches": 1},
    {"why": "The move-list buttons drop the console serif and read as a second design.",
     "file": "bible.html",
     "find": ".vault-move .vault-btn,.vault-move .vmv-mark,.vault-move .vmv-wit{font-family:var(--serif-display,serif);",
     "replace": ".vault-move .vault-btn,.vault-move .vmv-mark,.vault-move .vmv-wit{font-family:sans-serif;",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
