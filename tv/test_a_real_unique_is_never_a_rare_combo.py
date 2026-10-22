# -*- coding: utf-8 -*-
"""REG-2525 (V1 round 3; the review of REG-2402) - A REAL UNIQUE IS NEVER A ROLLED RARE NAME, ON THE PAGE OR ON THE CONSOLE.

REG-2402 gave RARE_NAME_POOLS the game's Gloves row - Hand, Fist, Claw, Clutches, Knuckle. The console reads that literal
by regex (control_app._kai_fullnames) and builds every RARE_NAME_PREFIXES x pool word as a "rare combo"
(_kai_rarenames), and the /kai_verdict GRAIL GATE never promotes a rare combo - a rare amulet may be a toss. 'Raven' is a
rare prefix, so the real grail unique RAVEN CLAW (a Long Bow in ITEM_CODEX, the grail seed and ITEM_TIP) became a rare
combo: a judge toss or border on it was no longer lifted to 'grail' and went into the APPEND-ONLY journal as toss (the
v2386 class), while the page's aicJudgeApply kept it - the board and the journal disagreeing (v948.19's split-brain).
Rune Master (Rune + Master) and Death Cleaver (listed in CRAFT_NAME_EXAMPLES) were already there. Reviewer, on the real
control_app functions: grail-seed names in the rare set, base [death cleaver, rune master], head adds raven claw.

THE RULE, NOT THE NAME. A generated combo never shadows a catalogued unique or set name: the console's harvest subtracts
every name the page's unique/set roster carries (ITEM_VALUE + _UNI_EXTRA, the sources _gUniqueRoster is built from, and
ITEM_CODEX's uniques and set pieces) from the combo space; the page asks the same catalogues before it calls a name rolled
(_rolledQuality -> _rareRealName). A console edit, kept to the harvest: tv/control_app.py _kai_fullnames.

WHAT THIS LAW HOLDS:
  * the console, on this tree's control_app.py and bible.html: no ITEM_CODEX unique / set name and no _GRAIL_SEED name is
    a rare combo; Raven Claw, Rune Master and Death Cleaver are known names and not rare combos; the gate (mirrored as
    tv/test_routes.py mirrors it) lifts a toss / border on Raven Claw and Rune Master to 'grail'; a real rolled combo
    (Beast Noose, Wraith Grasp) and a crafted name (Dire Hand) stay tossable, so the rule is not passing by emptying the
    combo space;
  * the page, the SHIPPED _rareRealName / _rolledQuality and the pools cut from bible.html, run in node with the real
    catalogues: Raven Claw and Rune Master are never rolled even when no other lookup knows them; Wraith Grasp is still
    a rare (gloves / ring) and Sullied Grand Charm of Blight still a magic charm.
Measured on the merged V1 tree before the fix: 'raven claw' in the rare set, gate('Raven Claw','toss') -> 'toss'.
RED_PROOF below. A missing node is the only skip for the page half; a node that fails is a failure.
"""
import io
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
except Exception:
    pass

import control_app as ca  # noqa: E402
from cb_node_harness import NODE  # noqa: E402

REPO = os.path.dirname(HERE)
PAGE = os.path.join(REPO, "bible.html")
CATALOGUES = ("window.ITEM_VALUE = ", "const _UNI_EXTRA = ", "const ITEM_CODEX = ")


def _src():
    with io.open(PAGE, encoding="utf-8") as fh:
        return fh.read()


def _literal(s, anchor):
    if s.count(anchor) != 1:
        raise AssertionError("%r matched %d times - re-point this law" % (anchor, s.count(anchor)))
    obj, _ = json.JSONDecoder().raw_decode(s, s.index(anchor) + len(anchor))
    return obj


def _real_names(s):
    """every name the page's catalogues carry as a unique or a set piece (the rule's own population, read here
    independently of the console's harvest)"""
    out = set()
    for a in CATALOGUES:
        for k, v in _literal(s, a).items():
            if a.startswith("const ITEM_CODEX") and not (isinstance(v, dict) and str(v.get("rarity", "")).lower() in ("unique", "set")):
                continue
            out.add(k)
    return out


def _grail_seed(s):
    a = "const _GRAIL_SEED = "
    if s.count(a) != 1:
        raise AssertionError("_GRAIL_SEED moved")
    return set(_literal(s, a).keys())


def _fresh_console():
    """the console's name space, harvested from THIS tree's bible.html (never a cache another law left)"""
    ca.REPO = REPO
    for k in ("_KAI_FULLNAMES", "_KAI_RARE_COMBOS", "_KAI_FULLNAMES_CASED", "_KAI_GROUND_INDEX"):
        ca.__dict__.pop(k, None)
    return ca._kai_fullnames(), ca._kai_rarenames()


def _gate(name, tier):
    """the /kai_verdict grail gate (control_app.py, the v1250 condition), mirrored exactly as tv/test_routes.py does"""
    if name and ca._kai_is_runeword_name(name):
        if tier in ("toss", "border", "grail"):
            return "keep"
    elif (name and name.lower() in ca._kai_fullnames() and name.lower() not in ca._kai_rarenames()
          and tier in ("toss", "border")):
        return "grail"
    return tier


class TheConsoleKeepsARealUniqueOutOfTheRareCombos(unittest.TestCase):

    def test_no_catalogued_unique_or_set_name_and_no_grail_seed_name_is_a_rare_combo(self):
        s = _src()
        full, rare = _fresh_console()
        self.assertGreater(len(rare), 1000, "PREMISE: the console generated no rare combos (%d) - this law would pass on "
                                            "an empty space" % len(rare))
        real = {n.lower() for n in _real_names(s)}
        seed = {n.lower() for n in _grail_seed(s)}
        self.assertGreater(len(real), 300, "PREMISE: the catalogues read back %d names" % len(real))
        hit = sorted((real | seed) & rare)
        self.assertEqual(hit, [], "real uniques / set pieces / grail-seed names read as rolled rare combos - the grail "
                                  "gate will journal a toss on them: %s" % hit)
        for n in ("raven claw", "rune master", "death cleaver"):
            self.assertIn(n, full, "%s is no longer a known name on the console" % n)
            self.assertNotIn(n, rare, "%s is a rare combo again" % n)

    def test_the_grail_gate_lifts_a_toss_on_raven_claw_and_still_lets_a_rare_be_tossed(self):
        _fresh_console()
        for n in ("Raven Claw", "Rune Master"):
            self.assertEqual(_gate(n, "toss"), "grail", "%s: a toss was not lifted to grail (journaled as toss)" % n)
            self.assertEqual(_gate(n, "border"), "grail", "%s: a border was not lifted to grail" % n)
        self.assertEqual(_gate("Windforce", "toss"), "grail", "PREMISE: a plain unique no longer promotes")
        for n in ("Beast Noose", "Wraith Grasp", "Dire Hand"):
            self.assertEqual(_gate(n, "toss"), "toss", "%s: a rolled / crafted name must stay tossable" % n)
        self.assertIn("wraith grasp", ca._kai_rarenames(), "the Gloves row's combos are gone - the rule emptied the pools")


@unittest.skipIf(NODE is None, "node is absent - the page half runs the SHIPPED _rolledQuality; UNMEASURED, not passing")
class ThePageNeverCallsARealUniqueRolled(unittest.TestCase):

    def _run(self, body):
        s = _src()
        i = s.index("window.RARE_NAME_POOLS = RARE_NAME_POOLS;")
        a = s.rfind("\nconst RARE_NAME_POOLS = {", 0, i)
        if a < 0:
            raise AssertionError("RARE_NAME_POOLS moved - re-point this law")
        pools = s[a:s.index("\n", i)]
        start = "var _MAGIC_SMALL_RE = /^"
        if s.count(start) != 1:
            raise AssertionError("_MAGIC_SMALL_RE moved")
        j = s.index(start)
        k = s.index("\nfunction _rolledQuality(name){\n", j)
        rq = s[k:]
        depth, m = 0, rq.index("{")
        for e in range(m, len(rq)):
            if rq[e] == "{":
                depth += 1
            elif rq[e] == "}":
                depth -= 1
                if depth == 0:
                    rq = rq[:e + 1]
                    break
        cat = {}
        for anc in CATALOGUES:
            obj = _literal(s, anc)
            if anc.startswith("const ITEM_CODEX"):
                cat["codex"] = {n: {"rarity": v.get("rarity")} for n, v in obj.items() if isinstance(v, dict)}
            elif anc.startswith("window.ITEM_VALUE"):
                cat["value"] = obj
            else:
                cat["extra"] = obj
        js = ("var window = globalThis;\n" + pools + "\n"
              + "window.ITEM_VALUE = " + json.dumps(cat["value"]) + ";\nwindow._UNI_EXTRA = " + json.dumps(cat["extra"]) + ";\n"
              + "var ITEM_CODEX = " + json.dumps(cat["codex"]) + ";\n"
              + "function d2rItemLookup(){ return null; }   /* no other lookup knows the name: the rule must */\n"
              + s[j:k] + rq + "\nvar OUT = {};\n" + body + "\nprocess.stdout.write(JSON.stringify(OUT));\n")
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped _rolledQuality would not run in node: %s" % (r.stderr or r.stdout)[-1500:])
        return json.loads(r.stdout)

    def test_a_catalogued_unique_is_never_rolled_and_a_rolled_name_still_is(self):
        o = self._run("['Raven Claw', 'Rune Master', 'Wraith Grasp', 'Sullied Grand Charm of Blight', 'Death Loop']"
                      ".forEach(function(n){ var q = _rolledQuality(n); OUT[n] = q ? q.q : null; });")
        self.assertIsNone(o["Raven Claw"], "the page calls the grail unique Raven Claw a rolled rare")
        self.assertIsNone(o["Rune Master"], "the page calls the unique Rune Master a rolled rare")
        self.assertEqual(o["Wraith Grasp"], "rare", "PREMISE: a rolled rare is no longer read as one")
        self.assertEqual(o["Death Loop"], "rare", "PREMISE: a rolled ring is no longer read as one")
        self.assertEqual(o["Sullied Grand Charm of Blight"], "magic", "PREMISE: a magic charm is no longer read as one")


RED_PROOF = [
    {"why": "REG-2525 - the console's harvest lets a generated combo shadow a catalogued unique again (Raven Claw "
            "journaled as toss)",
     "file": "tv/control_app.py", "matches": 1,
     "find": "        rare_combos -= _real\n",
     "replace": "        rare_combos -= set()\n"},
    {"why": "REG-2525 - the console reads only one catalogue (ITEM_CODEX's set pieces and the roster's extras are rare "
            "combos again)",
     "file": "tv/control_app.py", "matches": 1,
     "find": "        for _anchor in (\"window.ITEM_VALUE = \", \"const _UNI_EXTRA = \", \"const ITEM_CODEX = \"):\n",
     "replace": "        for _anchor in (\"const _NO_CATALOGUE_ = \",):\n"},
    {"why": "REG-2525 - the page calls a catalogued unique rolled when no other lookup knows it",
     "file": "bible.html", "matches": 1,
     "find": "  try { if (_rareRealName(nm)) return null; } catch(e){}\n",
     "replace": ""},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
