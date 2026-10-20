# -*- coding: utf-8 -*-
"""REG-2335 - THE ITEMS-ONLY WIPE EMPTIES EVERY LOCKER (Elad 2026-10-21 01:44 IDT).

HIS WORDS: "there should be an option that resets just the items and wipes them from the mules and shared
stash/war stash/mules all emptied ... i still have these items that are stuck and not being deleted".

ROOT CAUSE: neither reset door emptied the board. Reset assignments keeps owned, and the router (_vaultSeamHome)
re-homes every owned name onto a locker; Reset vault rebuilds proven items from the evidence plan; both keep
d2r_magicFinds (the MAGIC & RARE locker reads it, not the mule map) and d2r_copies (extra copies).

THIS LAW cuts the SHIPPED scope and the new door window.vaultWipeItems from bible.html and drives it in node on the
seeded store of test_a_vault_reset_clears_only_the_mules:
  - mule map, witness rows, owned, Magic & Rare and copies are all empty after; nothing is rebuilt;
  - runes / gems / materials, set pieces, runewords, the chronicle and the roster are byte-identical;
  - the confirm is asked first and says what stays; cancel moves nothing; the receipt is clean (ok true).
RED_PROOF below (python3 tv/test_a_wipe_items_empties_every_locker.py --red-proof).
"""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except ImportError:
    _enable = None
import test_a_vault_reset_clears_only_the_mules as base  # noqa: E402

DOOR_WIPE = "  window.vaultWipeItems = async function(){\n"
KEPT = ("d2r_runeStash", "d2r_gemStash", "d2r_materialStash", "d2r_craftStash", "d2r_craftBaseStash", "d2r_statues",
        "d2r_setPieces", "d2r_rwMade", "d2r_foundLog", "d2r_grailUnfound", "d2r_chronicleInbox", "d2r_craftMade",
        "d2r_muleRoster", "d2r_tally", "d2r_unknownReads", "d2r_multiKeep")
EMPTIED = ("d2r_muleAssign", "d2r_vaultProv", "d2r_owned", "d2r_magicFinds", "d2r_copies")

BODY = base.BODY.split("(async function(){")[0] + r"""
(async function(){
  var OUT = {};
  seed(); ANSWER = false; var c0 = snap();
  await window.vaultWipeItems();
  OUT.cancel = { before: c0, after: snap(), confirms: CONFIRMS.length };
  ANSWER = true;
  var PLANS = 0; window._vaultPlanFromEvidence = async function(){ PLANS++; return { ok: true, rebuilt: [{ name: 'Hellfire Torch' }], held: [] }; };
  OUT.wipe = await run('wipe', 'vaultWipeItems');
  OUT.wipe.mem = mem(); OUT.wipe.plans = PLANS;
  process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write(String((e && e.stack) || e)); process.exit(3); });
"""


def _drive(src=None):
    s = src if src is not None else base._src()
    prog = base.HARNESS + base._pieces(s) + base._door(s, DOOR_WIPE) + BODY
    r = subprocess.run([base.NODE, "-"], input=prog, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise AssertionError("the shipped wipe would not execute - UNKNOWN, not passing: %s" % (r.stderr or r.stdout)[-900:])
    return json.loads(r.stdout)


def _empty(raw):
    return raw is None or not json.loads(raw)


class _Base(object):
    o = None

    def test_every_item_store_is_empty_after(self):
        w = self.o["wipe"]
        for k in EMPTIED:
            self.assertFalse(_empty(w["before"]["store"].get(k)), "seed did not populate %s" % k)
            self.assertTrue(_empty(w["after"]["store"].get(k)), "the wipe left items in %s" % k)
        self.assertEqual({}, w["mem"]["magicFinds"], "MAGIC & RARE still holds items in memory")
        self.assertEqual({}, w["mem"]["copies"], "extra copies still counted in memory")
        self.assertEqual([], w["mem"]["owned"], "owned items still held")
        self.assertEqual(0, w["assignLeft"])

    def test_nothing_is_rebuilt(self):
        self.assertEqual(0, self.o["wipe"]["plans"], "the items-only wipe asked the evidence plan to rebuild")

    def test_runes_gems_materials_and_testimony_stay(self):
        w = self.o["wipe"]
        for k in KEPT:
            self.assertEqual(w["before"]["store"].get(k), w["after"]["store"].get(k), "the wipe touched %s" % k)

    def test_confirm_first_and_cancel_moves_nothing(self):
        c = self.o["cancel"]
        self.assertEqual(1, c["confirms"])
        self.assertEqual(c["before"], c["after"])
        conf = self.o["wipe"]["confirm"] or ""
        self.assertIn("runes / gems / materials", conf)
        self.assertIn("Magic & Rare", conf)

    def test_receipt_is_clean(self):
        rc = self.o["wipe"]["receipt"]
        self.assertEqual("vaultWipeItems", rc.get("door"))
        self.assertEqual([], rc.get("touched"))
        self.assertIs(True, rc.get("ok"), rc)


@unittest.skipIf(base.NODE is None, "node is absent - UNMEASURED, not passing")
class AWipeItemsEmptiesEveryLocker(_Base, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_the_doctor_row_judges_the_wipe_on_its_keeps(self):
        import vault_evidence as ve
        rc = self.o["wipe"]["receipt"]
        got = ve.reset_receipt(rc, rc["keepsBefore"], rc["keepsAfter"])
        self.assertTrue(got.get("ok"), got)
        self.assertIn("Wipe items never rebuilds", got.get("why") or "")
        bad = dict(rc["keepsAfter"], d2r_runeStash="0:0")
        self.assertFalse(ve.reset_receipt(rc, rc["keepsBefore"], bad).get("ok"), "a wipe that touched the runes read clean")




RED_PROOF = [
    {"why": "REG-2335 - the wipe leaves MAGIC & RARE (the stuck charms in his screenshot)",
     "file": "bible.html", "matches": 1,
     "find": "'owned', 'magic', 'copies'])\n",
     "replace": "'owned', 'copies'])\n"},
    {"why": "REG-2335 - the wipe leaves the extra copies",
     "file": "bible.html", "matches": 1,
     "find": "'owned', 'magic', 'copies'])\n",
     "replace": "'owned', 'magic'])\n"},
    {"why": "REG-2335 - the wipe leaves owned (the router re-homes every owned name onto a locker)",
     "file": "bible.html", "matches": 1,
     "find": "'folder', 'owned', 'magic', 'copies'])\n",
     "replace": "'folder', 'magic', 'copies'])\n"},
    {"why": "REG-2335 - the wipe rebuilds from the evidence like Reset vault (the torches came back)",
     "file": "bible.html", "matches": 1,
     "find": "    if (!R || R.door !== 'vaultClearHistory') return;\n",
     "replace": "    if (!R || (R.door !== 'vaultClearHistory' && R.door !== 'vaultWipeItems')) return;\n"},
    {"why": "REG-2335 - the door runs through Reset vault's list (keeps Magic & Rare, rebuilds)",
     "file": "bible.html", "matches": 1,
     "find": "    var R = await _vaultResetRun('vaultWipeItems');\n",
     "replace": "    var R = await _vaultResetRun('vaultClearHistory');\n"},
    {"why": "REG-2335 - the magic step forgets the in-memory Magic & Rare (re-persisted on the next save)",
     "file": "bible.html", "matches": 1,
     "find": "clear: function(){ Object.keys(magicFinds).forEach(function(k){ delete magicFinds[k]; }); ",
     "replace": "clear: function(){ "},
    {"why": "REG-2335 - the copies step forgets the in-memory copy counts",
     "file": "bible.html", "matches": 1,
     "find": "clear: function(){ Object.keys(copies).forEach(function(k){ delete copies[k]; }); ",
     "replace": "clear: function(){ "},
    {"why": "REG-2335 - the self-check watches the stores this door clears, so a clean wipe reads as a touched keep",
     "file": "bible.html", "matches": 1,
     "find": "    return S.keeps.filter(function(k){ return !mine[k.store]; });\n",
     "replace": "    return S.keeps.slice();\n"},
    {"why": "REG-2335 - the wipe runs without asking him",
     "file": "bible.html", "matches": 1,
     "find": "    if (!(await uiConfirm(_vaultResetConfirm('vaultWipeItems')))) return;\n",
     "replace": ""},
    {"why": "REG-2335 - the wipe leaves the mule map (every mule and WAR mule keeps its filings)",
     "file": "bible.html", "matches": 1,
     "find": "vaultWipeItems:    Object.freeze(['assign', ",
     "replace": "vaultWipeItems:    Object.freeze(["},
    {"why": "REG-2335 - the confirm stops saying runes / gems / materials stay",
     "file": "bible.html", "matches": 1,
     "find": "      + '\\n\\nClears: ' + w.clears.join(' · ') + '. Nothing is rebuilt from the evidence.'\n      + '\\n\\nStays untouched (runes / gems / materials and the rest): ' + w.keeps.join(' · ') + '.'\n",
     "replace": "      + '\\n\\nClears: ' + w.clears.join(' · ') + '. Nothing is rebuilt from the evidence.'\n"},
]


def red_proof():
    s = base._src()
    bad = 0
    for m in RED_PROOF:
        assert s.count(m["find"]) == 1, m["why"]
        try:
            o = _drive(s.replace(m["find"], m["replace"]))
            T = type("T", (_Base, unittest.TestCase), {"o": o})
            res = unittest.TestResult()
            for n in [a for a in dir(_Base) if a.startswith("test_")]:
                T(n).run(res)
            red = bool(res.failures or res.errors)
        except AssertionError:
            red = True
        print(("RED   " if red else "GREEN?! ") + m["why"])
        bad += 0 if red else 1
    return bad


if __name__ == "__main__":
    if "--red-proof" in sys.argv:
        sys.exit(red_proof())
    unittest.main()
