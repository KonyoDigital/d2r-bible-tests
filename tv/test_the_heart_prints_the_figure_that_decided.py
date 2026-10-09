# -*- coding: utf-8 -*-
"""REG-2141 (#193, GrokBot ticks 416-419) - THE HEART PRINTS THE FIGURE THAT DECIDED.

Since ddd55279 (his 2026-09-04 ruling: "Five distinct attacks scores 0.5655, not 0.9558") a lock's state is decided per
DISTINCT ATTACK, and REG-614 made the engine's own header and sentences print that figure. The console was one layer out
and never followed: control_app's trim sends `score` = the RAW per-attempt Wilson, and all three heart renderers (the valve
diagram, the lock list, the route list) printed it with the raw k/n. Measured on his ledger 10-09: prune.reports printed
"117/125 refused · Wilson 0.879" beside its own "wilson 0.610 >= 0.510"; miniauto.run's diagram said "55/55 refused ·
0.935 >= 0.510" while 0.439 decided - a sign that flips under its badge.

  * ENGINE: every row that has a per-attack figure publishes the pair it is computed from (attacksPassed / attacks), and
    feeding that pair back through the module's own wilson_lower reproduces wilsonByAttack.
  * DRIVEN in node: the ONE console helper (_hrtLockFigure) over the rows the REAL trim produces - whatever pair it returns,
    wilson_lower reproduces the score beside it, and a row that decides per attack is printed per attack. Baseline: a
    synthetic row carrying his miniauto.run numbers (raw 0.9347, per attack 0.4385 over 3 of 3) must come back 3/3 · 0.4385.
  * COMPILER: all three render sites ask the helper.
RED_PROOF below. [[the-unjoined-end]] [[label-outlived-referent]] [[copy-drift]]
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import self_arming as SA  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
# the heart is proved by its own gate; here it only has to not refuse, so the trim runs its whole path
WATCHED = (True, "stubbed: the heart is proved by its own gate")


def _reset_memo():
    SA._HEART_SHOWN["at"] = None
    SA._HEART_SHOWN["v"] = None


def _node():
    return shutil.which("node") or shutil.which("nodejs")


def _helper_source():
    with io.open(UI, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    i = src.find("  function _hrtLockFigure(L){")
    assert i >= 0, "_hrtLockFigure is gone from control_ui.html - re-point this law"
    end = src.find("\n  }\n", i)
    assert end > i, "_hrtLockFigure has no closing brace where one is expected"
    return src[i:end + 4]


class TheEnginePublishesTheDecidingPair(unittest.TestCase):

    def setUp(self):
        _reset_memo()
        self.addCleanup(_reset_memo)

    def test_the_published_pair_reproduces_the_per_attack_figure(self):
        with mock.patch.object(SA, "_heart_says_watched", lambda **_k: WATCHED):
            rep = SA.report()
        seen = 0
        for l in rep.get("locks") or []:
            if l.get("wilsonByAttack") is None:
                continue
            seen += 1
            self.assertIsInstance(l.get("attacksPassed"), int, "%s: no attacksPassed beside wilsonByAttack: %r"
                                  % (l.get("lock"), l))
            self.assertAlmostEqual(SA.wilson_lower(l["attacksPassed"], l["attacks"]), l["wilsonByAttack"], places=3,
                                   msg="%s: %d of %d does not reproduce wilsonByAttack %.4f"
                                       % (l.get("lock"), l["attacksPassed"], l["attacks"], l["wilsonByAttack"]))
        self.assertGreater(seen, 0, "PRINT THE DENOMINATOR: no row carried a per-attack figure - this proved nothing")


@unittest.skipUnless(_node(), "node is not installed - the shipped helper cannot be driven, so this is UNKNOWN")
class TheConsolePrintsTheFigureThatDecided(unittest.TestCase):

    def setUp(self):
        _reset_memo()
        self.addCleanup(_reset_memo)

    def _figs(self, rows):
        prog = (_helper_source() + "\n"
                "console.log(JSON.stringify(" + json.dumps(rows) + ".map(function(l){ return _hrtLockFigure(l); })));\n")
        p = subprocess.run([_node(), "-"], input=prog, capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise AssertionError("node could not run the shipped helper: %s" % (p.stderr or "")[:300])
        return json.loads(p.stdout.strip().split("\n")[-1])

    def _trimmed(self):
        import control_app as ca
        with mock.patch.object(SA, "_heart_says_watched", lambda **_k: WATCHED):
            st = ca._self_arming_state()
        self.assertTrue(st.get("locks"), "PREMISE: the trim carried no locks: %r" % (st,))
        return st

    def test_baseline_his_miniauto_numbers_print_per_attack(self):
        row = {"lock": "miniauto.run", "score": 0.9347, "wilsonByAttack": 0.4385, "deciding": "wilsonByAttack",
               "attacks": 3, "attacksPassed": 3, "k": 55, "n": 55, "bar": 0.51}
        f = self._figs([row])[0]
        self.assertEqual((f["k"], f["n"], f["perAttack"]), (3, 3, True), "the 55/55 attempt pair was printed: %r" % f)
        self.assertAlmostEqual(f["score"], 0.4385, places=4, msg="the raw 0.9347 was printed beside a 0.4385 verdict")
        self.assertAlmostEqual(f["raw"], 0.9347, places=4, msg="the raw figure is no longer carried for the list row")
        # the tab chip prints toFixed(2) of this same figure, not of the raw 0.9347
        prog = (_helper_source() + "\n"
                "var l = " + json.dumps(row) + ";\n"
                "var _cf = l ? _hrtLockFigure(l) : null;\n"
                "var sc = (_cf && typeof _cf.score === 'number' && !isNaN(_cf.score)) ? _cf.score : null;\n"
                "console.log(JSON.stringify(sc));\n")
        p = subprocess.run([_node(), "-"], input=prog, capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise AssertionError("node could not run the chip formula: %s" % (p.stderr or "")[:300])
        self.assertAlmostEqual(json.loads(p.stdout.strip().split("\n")[-1]), 0.4385, places=4,
                               msg="the tab chip formula printed the raw Wilson")

    def test_every_printed_pair_reproduces_the_printed_figure(self):
        st = self._trimmed()
        for kind in ("locks", "routes"):
            rows = [r for r in (st.get(kind) or []) if isinstance(r.get("n"), int) and r["n"] > 0]
            figs = self._figs(rows)
            per = 0
            for r, f in zip(rows, figs):
                if f["score"] is None:
                    continue
                self.assertAlmostEqual(SA.wilson_lower(f["k"], f["n"]), f["score"], places=3,
                                       msg="%s %s prints %s/%s beside %.4f - the pair and the figure name different "
                                           "quantities" % (kind, r.get("lock"), f["k"], f["n"], f["score"]))
                if r.get("deciding") == "wilsonByAttack":
                    self.assertTrue(f["perAttack"], "%s %s decides per attack but prints the attempt pair: %r"
                                    % (kind, r.get("lock"), f))
                    per += 1
            self.assertGreater(per, 0, "PRINT THE DENOMINATOR: no %s row decided per attack - the law never fired" % kind)


class EveryHeartRendererAsksTheHelper(unittest.TestCase):

    def test_the_diagram_the_lock_list_and_the_route_list_ask_it(self):
        with io.open(UI, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        self.assertEqual(src.count("var _fig = _hrtLockFigure(L);"), 1, "the valve diagram no longer asks the helper")
        self.assertEqual(src.count("var _fg = _hrtLockFigure(L);"), 1, "the lock list no longer asks the helper")
        self.assertEqual(src.count("var _rf = _hrtLockFigure(r);"), 1, "the route list no longer asks the helper")
        self.assertEqual(src.count("var _cf = l ? _hrtLockFigure(l) : null;"), 1,
                         "the tab-strip chip no longer asks the helper")
        # the function's own "(L)" is not a renderer
        self.assertEqual(len(re.findall(r"(?<!function )_hrtLockFigure\((?:L|r|l)\)", src)), 4,
                         "a fifth renderer appeared - it must ask the helper too, and this count must say so")


RED_PROOF = [
    {"why": "REG-2141 - the trim drops the deciding pair, so the panel prints the raw attempts again",
     "file": "control_app.py",
     "find": "                   \"deciding\": l.get(\"deciding\"), \"attacksPassed\": l.get(\"attacksPassed\"),\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2141 - the engine stops publishing the pair its per-attack figure is computed from",
     "file": "self_arming.py",
     "find": "           \"attacksPassed\": (None if not attacks else _attacks_passed(k, n, attacks)),\n",
     "replace": "           \"attacksPassed\": None,\n",
     "matches": 1},
    {"why": "REG-2141 - the helper prints the raw figure even when the lock decided per attack",
     "file": "control_ui.html",
     "find": "    if (byAtk) return { k: L.attacksPassed, n: L.attacks, score: Number(L.wilsonByAttack), perAttack: true,\n",
     "replace": "    if (false) return { k: L.attacksPassed, n: L.attacks, score: Number(L.wilsonByAttack), perAttack: true,\n",
     "matches": 1},
    {"why": "REG-2141 - the lock list reads the raw score itself again",
     "file": "control_ui.html",
     "find": "      var _fg = _hrtLockFigure(L);",
     "replace": "      var _fg = { k: L.k, n: L.n, score: (L.score == null ? null : Number(L.score)), perAttack: false };",
     "matches": 1},
    {"why": "REG-2141 - the tab chip prints the raw per-attempt Wilson again",
     "file": "control_ui.html",
     "find": "        var _cf = l ? _hrtLockFigure(l) : null;\n",
     "replace": "        var _cf = null;\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
