# -*- coding: utf-8 -*-
"""REG-1657 — A STASH READ IS NEVER CALLED A FABRICATION FOR WHAT THE BAG BESIDE IT HOLDS.

The vault's free cross-check counts occupied cells with vault_corpus.inventory_lattice - which crops the player's
INVENTORY - and compares them with the names a paid read returned. But the vault reads STASH panels. MEASURED
2026-10-01 across every surveyed reel on his Mac: panel kinds read = stash 2002 · shared 407 · personal 121 ·
materials 41 · runes 12 · gems 4 · inventory 0. Every comparison was between two different panels. While the lattice
was blind (REG-1648) it never ran; working again, reel 82142 - an EMPTY bag beside a stash tooltip naming one real
item - would have shown "the read named 1 item(s) but only 0 square(s) are filled, so at least one name did not come
from this picture" on his board: a fabrication claim about a correct read.

  · DRIVEN: cross_panel_verdict - an over-read on any panel but the inventory (or a panel nobody can tell) is
    "other-panel"; an inventory over-read stays an over-read; agree and under-read are untouched.
  · DRIVEN: "other-panel" is NOT settled - vault_seal_is_definitive refuses it, so no seal loosens and the footage
    stays readable - and why_not_definitive says it as what it is, never "named MORE than the panel can hold".
  · The sweep asks it at the one place a verdict is made, after reconcile_verdict and before the over-read list.

REG-1659 — the same two panels, on the board. A frame whose read named nothing still had its BAG counted, and the
row was named by the screen: "stash · <frame> - N square(s) are visibly full and the read named none of them ... Film
that tab once with the tooltip up". With the lattice re-lit (REG-1648) every such stash frame would ask him to film a
stash tab for squares that are his inventory.
  · The sweep's glimpse row carries the panel that was COUNTED (read from its code: the sweep runs paid reads).
  · DRIVEN in node, the real page code cut by its markers - the helper AND the loop that files it: the row is named
    "your inventory · <frame>", never by the screen; an older payload with no panel is the inventory too (every row
    ever came from that one crop); it never says "the read named none of them" or "Film that tab".
No node on this PC = the page half SKIPS with its reason; a skip is not a pass.
RED_PROOF below. [[unknown-stays-unknown]] [[feedback-contradiction-is-the-finding]] [[label-outlived-referent]]
"""
import ast
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_ledgers as _fx_ledgers  # noqa: E402
_fx_ledgers.redirect()

import control_app as ca  # noqa: E402


class TheVerdictKnowsWhichPanelWasCounted(unittest.TestCase):

    def test_a_stash_family_over_read_is_other_panel(self):
        for surface in ("stash", "shared", "personal", "materials", "runes", "gems", "Stash ", None, ""):
            self.assertEqual(ca.cross_panel_verdict("over-read", surface), "other-panel",
                             "a %r read was called a fabrication for what the bag holds" % (surface,))

    def test_an_inventory_over_read_is_still_an_over_read(self):
        for surface in ("inventory", "Inventory", " inventory "):
            self.assertEqual(ca.cross_panel_verdict("over-read", surface), "over-read",
                             "the one real fabrication signal was silenced")

    def test_the_other_verdicts_are_untouched(self):
        for v in ("agree", "under-read"):
            for surface in ("stash", "inventory", None):
                self.assertEqual(ca.cross_panel_verdict(v, surface), v)


class OtherPanelIsSaidButNotSettled(unittest.TestCase):
    REC = [{"frame": "f_1.jpg", "surface": "stash", "named": 1, "occupied": 0, "verdict": "other-panel"}]

    def test_it_does_not_loosen_a_seal(self):
        self.assertFalse(ca.vault_seal_is_definitive(1, self.REC, [], []),
                         "a cross-panel read was taken as settled - a seal loosened on a comparison of two panels")

    def test_it_is_said_as_what_it_is(self):
        why = " · ".join(ca.why_not_definitive(1, self.REC, [], []))
        self.assertIn("a panel the pixel layer does not count (stash)", why)
        self.assertNotIn("named MORE than the panel can hold", why, "the explanation accuses: %r" % why)

    def test_the_explanation_agrees_with_the_verdict(self):
        for rec in (self.REC, [dict(self.REC[0], verdict="agree")], [dict(self.REC[0], verdict="under-read")]):
            definitive = ca.vault_seal_is_definitive(1, rec, [], [])
            why = ca.why_not_definitive(1, rec, [], [])
            self.assertEqual(definitive, not why, "verdict %s and explanation %r disagree for %r"
                             % (definitive, why, rec[0]["verdict"]))


class TheSweepAsksIt(unittest.TestCase):
    """_vault_sweep_run is ~600 lines and runs paid reads; the join is read from its code, in order."""

    def test_after_the_reconcile_and_before_the_over_read_list(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        calls = {}
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) and node.value.func.id in ("reconcile_verdict",
                                                                                       "cross_panel_verdict"):
                calls.setdefault(node.value.func.id, []).append(node.lineno)
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) \
                    and isinstance(node.test.left, ast.Name) and node.test.left.id == "_verdict":
                calls.setdefault("over-read-check", []).append(node.lineno)
        self.assertEqual(len(calls.get("cross_panel_verdict", [])), 1, "the sweep never asks which panel was counted")
        self.assertLess(min(calls["reconcile_verdict"]), calls["cross_panel_verdict"][0])
        self.assertLess(calls["cross_panel_verdict"][0], min(calls["over-read-check"]),
                        "the over-read list is filled before the panel is asked about")


class TheIncompleteReasonIsThePureFunctions(unittest.TestCase):
    """REG-1661 — the sweep's INCOMPLETE reason (what a retirement quotes) is why_not_definitive's own words."""

    def test_the_reason_a_retirement_quotes_comes_from_the_pure_function(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        assigns = [n for n in ast.walk(fn) if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_whynot" for t in n.targets)]
        self.assertEqual(len(assigns), 1, "PREMISE: the sweep builds its incomplete reason once")
        calls = [c for c in ast.walk(assigns[0].value) if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Name) and c.func.id == "why_not_definitive"]
        self.assertEqual(len(calls), 1, "the incomplete reason re-derives the conditions instead of asking the pure "
                                        "function - an other-panel read retires as '0 of 28 never cross-checked'")
        text = ast.get_source_segment(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read(),
                                      assigns[0]) or ""
        self.assertNotIn("were never cross-checked", text, "a hand-written copy of a condition is back")

    def test_the_other_panel_case_says_what_it_is(self):
        rec = [dict(frame="f_%d.jpg" % i, surface="stash", named=0, occupied=3, verdict="under-read") for i in range(27)]
        rec.append(dict(frame="f_x.jpg", surface="stash", named=1, occupied=0, verdict="other-panel"))
        why = "; ".join(ca.why_not_definitive(28, rec, [], []))
        self.assertIn("a panel the pixel layer does not count (stash)", why)
        self.assertNotIn("never cross-checked", why)


class TheGlimpseNamesThePanelItCounted(unittest.TestCase):
    """REG-1659 — the board's glimpse row says where the full squares ARE."""

    def test_the_sweep_records_the_counted_panel(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        rows = [c.args[0] for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "append" and isinstance(c.func.value, ast.Name) and c.func.value.id == "_glimpsed"
                and c.args and isinstance(c.args[0], ast.Dict)]
        self.assertEqual(len(rows), 1, "PREMISE: the sweep builds exactly one glimpse row")
        got = {k.value: v for k, v in zip(rows[0].keys, rows[0].values) if isinstance(k, ast.Constant)}
        self.assertIn("panel", got, "the glimpse row does not say which panel its squares were counted on")
        self.assertTrue(isinstance(got["panel"], ast.Name) and got["panel"].id == "_LATTICE_PANEL",
                        "the glimpse row's panel is not the lattice's own panel")

    NODE = shutil.which("node")

    def _drive(self, glimpsed):
        if not self.NODE:
            self.skipTest("no node on this PC - the page half is UNMEASURED here, not passing")
        with io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
        a = src.index("/* \u27e6GLIMPSE ROW BEGIN\u27e7 */")
        b = src.index("/* \u27e6GLIMPSE ROW END\u27e7 */", a)
        script = ("var recs = [];\nvar _rec = function(name, status, why, frame){ recs.push({name: name, status: status, "
                  "why: why, frame: frame}); };\nvar out = {};\nvar payload = " + json.dumps({"glimpsed": glimpsed})
                  + ";\n" + src[a:b] + "\nprocess.stdout.write(JSON.stringify({recs: recs, out: out}));\n")
        r = subprocess.run([self.NODE, "-"], input=script, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        if r.returncode != 0:
            raise AssertionError("the page code did not run - UNKNOWN, not passing: %s" % r.stderr[-400:])
        return json.loads(r.stdout)

    def test_a_stash_frame_files_its_squares_under_the_inventory(self):
        got = self._drive([{"frame": "f_1.jpg", "surface": "stash", "panel": "inventory", "occupied": 33, "free": 7},
                           {"frame": "f_2.jpg", "surface": "shared", "panel": "inventory", "occupied": 0, "free": 40}])
        self.assertEqual(len(got["recs"]), 1, "an empty bag filed a row, or a full one filed none: %r" % got)
        rec = got["recs"][0]
        self.assertEqual(rec["name"], "your inventory · f_1.jpg", "the row is named by the screen: %r" % rec["name"])
        self.assertEqual(rec["status"], "glimpsed")
        self.assertIn("33 square(s) in your inventory", rec["why"])
        for wrong in ("the read named none", "Film that tab", "stash"):
            self.assertNotIn(wrong, rec["why"], "the row still points at the stash: %r" % rec["why"])
        self.assertEqual(got["out"].get("glimpsedTotal"), 33)

    def test_an_older_payload_is_the_inventory_too(self):
        got = self._drive([{"frame": "f_3.jpg", "surface": "personal", "occupied": 22, "free": 18}])
        self.assertEqual(got["recs"][0]["name"], "your inventory · f_3.jpg",
                         "a row from before the panel was recorded was named by its screen")

    def test_a_panel_it_does_not_know_is_said_as_itself(self):
        got = self._drive([{"frame": "f_4.jpg", "surface": "stash", "panel": "stash", "occupied": 2, "free": 98}])
        self.assertEqual(got["recs"][0]["name"], "the stash · f_4.jpg")


RED_PROOF = [
    {"why": "REG-1657 - a stash read is called a fabrication again for what the bag beside it holds",
     "file": "control_app.py",
     "find": "    if verdict == \"over-read\" and str(surface or \"\").strip().lower() != _LATTICE_PANEL:\n"
             "        return \"other-panel\"\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1657 - the sweep stops asking which panel was counted",
     "file": "control_app.py",
     "find": "                                _verdict = cross_panel_verdict(_verdict, surface)   # REG-1657\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1657 - a cross-panel read is taken as settled: a seal loosens on a comparison of two panels",
     "file": "control_app.py",
     "find": "    return all(str(r.get(\"verdict\") or \"\") in (\"under-read\", \"agree\") for r in rec)\n",
     "replace": "    return all(str(r.get(\"verdict\") or \"\") in (\"under-read\", \"agree\", \"other-panel\") for r in rec)\n",
     "matches": 1},
    {"why": "REG-1657 - a cross-panel read goes unexplained",
     "file": "control_app.py",
     "find": "    other = [r for r in rec if str(r.get(\"verdict\") or \"\") == \"other-panel\"]\n",
     "replace": "    other = []\n",
     "matches": 1},
    {"why": "REG-1659 - the sweep's glimpse row forgets which panel its squares were counted on",
     "file": "control_app.py",
     "find": "                                        \"panel\": _LATTICE_PANEL,\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1659 - the board names the glimpse row by the screen again: his bag reads as a stash tab",
     "file": "bible.html",
     "find": "          var p = String((g && g.panel) || 'inventory').trim().toLowerCase();\n"
             "          var where = (p === 'inventory') ? 'your inventory' : ('the ' + p);\n",
     "replace": "          var where = (g && g.surface) || 'stash';\n",
     "matches": 1},
    {"why": "REG-1659 - the loop files the row under the screen, not the helper's name (the join is cut)",
     "file": "bible.html",
     "find": "          _rec(row.name, 'glimpsed', row.why, g.frame);\n",
     "replace": "          _rec((g.surface || 'stash') + ' · ' + (g.frame || '?'), 'glimpsed', row.why, g.frame);\n",
     "matches": 1},
    {"why": "REG-1661 - the incomplete reason re-derives the conditions again and drifts from the pure function",
     "file": "control_app.py",
     "find": "                           else (\"; \".join(why_not_definitive(_read_ok[0], _reconciled, _over_read, _pix_err))\n",
     "replace": "                           else (\"%d of %d read frame(s) were never cross-checked\" % (_read_ok[0] - len(_reconciled), _read_ok[0])\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
