# -*- coding: utf-8 -*-
"""REG-2030 - THE ORGANIZER SAYS THE MULE, THE STASH CELL AND THE PICTURE, FOR EVERY LOOSE ITEM, WITH NO CLICK. #264.

His ruling, 2026-10-08: "everything inside the stash (left side) ... and the empty space cells for farming within the
inventory should be completely organized autonomously" · "tell me which mule to mule it in and stash it in" · "with the
tooltip picture proof synced to the ledger obviously for evidence" · "without me telling it or click auto assemble".
Recon (his "check blueprints, so you dont double build"): the vault lane already places stash sightings with their frame
(vault_seen -> vault_accum -> the witnessed lane, on his 2-session rule) and the dock's organizer already named the mule
per item. What was missing, now added and held here on the SHIPPED page:
  - every row names its planned CELL in that mule, packed by the same packer the mule window and the finder use;
  - every row carries its evidence door (the frame it was read on);
  - loot in his inventory's free cells is listed too ("in your inventory"), and kit (charms, tomes, the Cube) never is;
  - every row is shown (the 60 cap hid 25 of his 85).
NO CHROME AT ALL = a declared skip, never a pass.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def _look(sid, frame, loc):
    return {"id": sid, "frame": frame, "conf": None, "at": "2026-10-07T08:00:00.000Z", "loc": loc, "scene": "stash"}


def _receipt(looks, **kw):
    r = {"kind": "owned", "source": "kai-register", "by": "law", "at": "2026-10-07T08:00:00.000Z", "looks": looks, "seen": len(looks)}
    r.update(kw)
    return r


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class TheOrganizerSaysTheMuleTheCellAndThePicture(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        names = ["Obedience", "Nokozan Relic", "Grief"] + ["Isenhart's Case (armor)"]
        prov = {n: _receipt([_look("s_1", "f_%d" % i, "stash")]) for i, n in enumerate(names)}
        # (a catalogue name the vault's pool keeps: the board files the Shako as "Harlequin Crest (Shako)", so a bare
        #  "Harlequin Crest" never reaches the pool and could not be the subject of this case)
        prov["War Traveler"] = _receipt([_look("s_1", "c_1", "inventory")], loc="inventory", carried=True, frameId="c_1",
                                           ts=1791360000000)
        prov["Gheed's Fortune"] = _receipt([_look("s_1", "c_2", "inventory")], loc="inventory", carried=True, frameId="c_2",
                                           ts=1791360000001)
        board().seed({"d2r_owned": names + ["War Traveler", "Gheed's Fortune"], "d2r_vaultProv": prov, "d2r_muleAssign": {}})
        cls.o = board().run("try { window.switchTab('vault'); } catch(e){} window.renderVault && window.renderVault();"
                            "var rows = Array.from(document.querySelectorAll('#vault-organize .vault-org-row[data-name]'));"
                            "OUT.rows = rows.map(function(r){ return { n: r.getAttribute('data-name'), cell: r.getAttribute('data-cell'),"
                            " text: r.textContent, ev: !!r.querySelector('.vd-ev') }; });"
                            "OUT.head = (document.querySelector('#vault-organize .vault-org-h') || {}).textContent || '';"
                            "OUT.more = !!document.querySelector('#vault-organize .vault-org-row[data-state=more]');")
        cls.by = dict((r["n"], r) for r in cls.o["rows"])

    def test_a_mule_bound_item_names_its_cell_and_carries_its_picture(self):
        r = self.by.get("Obedience")
        self.assertTrue(r, "Obedience is not in the organizer: %r" % self.o["rows"])
        self.assertIn("RUNEWORDS", r["text"])
        self.assertTrue(r["cell"] and "col" in r["cell"] and "row" in r["cell"], "no planned cell for a mule-bound item: %r" % r)
        self.assertTrue(r["ev"], "the row carries no evidence door (the picture it was read on)")
        g = self.by.get("Grief") or {}
        self.assertTrue(g.get("cell") and "tab" in g["cell"], "war gear has no shared-tab cell: %r" % g)

    def test_inventory_loot_is_organized_and_kit_is_not(self):
        h = self.by.get("War Traveler")
        self.assertTrue(h, "loot in his inventory's free cells is not organized: %r" % sorted(self.by))
        self.assertIn("in your inventory", h["text"])
        self.assertNotIn("Gheed's Fortune", self.by, "kit (a charm he carries) was offered a mule")

    def test_a_discard_keeps_its_advice_and_gets_no_cell(self):
        i = self.by.get("Isenhart's Case (armor)") or {}
        self.assertIn("throw-out advice", i.get("text", ""), i)
        self.assertFalse(i.get("cell"), "a discard suggestion was given a stash cell: %r" % i)
        self.assertFalse(self.o["more"], "rows are still capped")


RED_PROOF = [
    {"why": "REG-2030 - the organizer rows lose their planned stash cell",
     "file": "bible.html",
     "find": "      var cell = cells[nm] ? '<span class=\"vault-org-cell\"> · ' + _vhEsc(cells[nm]) + '</span>' : '';\n",
     "replace": "      var cell = ''; cells = {};\n",
     "matches": 1},
    {"why": "REG-2030 - the organizer rows lose their picture proof",
     "file": "bible.html",
     "find": "      var ev = (typeof window._vaultEvidenceBtn === 'function') ? window._vaultEvidenceBtn(nm) : '';\n",
     "replace": "      var ev = '';\n",
     "matches": 1},
    {"why": "REG-2030 - the loot in his inventory is left out of the organizer",
     "file": "bible.html",
     "find": "    (Array.isArray(carried) ? carried : []).forEach(function(n){ if (n) inInv[n] = 1; });\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
