# -*- coding: utf-8 -*-
"""HIS CROSS-REFERENCE READ 160/398 BESIDE A BOARD THAT SAYS 292/403 — TWO WRONG HALVES.

Konyo: *"the crossreference ... isnt really synced to the uniques"*, and later, flatly:
*"which one is it really?!!? is it 398 or 403 make a unifed logic"*.

BOTH HALVES WERE WRONG, FOR DIFFERENT REASONS.

=== THE NUMERATOR — a store that answers a different question ===
`fleet_mask.LEDGERS["uniques"]["store"]` was `d2r_owned` — the VAULT store — while
control_app.py:1997 repointed the uniques TALLY to the chronicle pair at v2717 and renamed the old
measure `vaultUniques`. Nothing updated the spec. So the panel answered "what is in his vault"
under a label meaning "what his Chronicle records". SETS was immune because both its sides read
`d2r_setPieces`, which is exactly why one tab was right and the other wrong.

⚠ AND IT IS A UNION, NOT ONE STORE. `bible.html:42994`'s `_ownedNames()` IS the definition of
"found" on his board: `d2r_owned` together with `keys(d2r_foundLog)`, commented "found = ledger +
LEGACY owned". Pointing at `d2r_foundLog` alone would be correct only IF the two happened to be
nested today — a coincidence, not a definition, and the legacy store is precisely where a
long-running grail keeps its oldest finds.

=== THE DENOMINATOR — a number the page itself says means nothing ===
The panel rendered `rosterN` = `len(roster)` = 398. bible.html:3755 had already ruled:
    403  chronTotal — HIS PINNED RULING, the game's own Chronicle count
    392  funiScan().total — the carded roster after his v2680 one-tally-per-sunder ruling
    398  "produced by neither, and NO array on the page is this size"
⚠⚠ BUT `rosterN` CANNOT SIMPLY BECOME 403. `fleet_mask.decode()` REFUSES any mask whose `n` does
not equal `len(roster)` — that equality is what proves both machines packed the same roster into
the same bit positions. Changing it would make every mask on the fleet undecodable. So 403 gets
its OWN field and `rosterN` keeps its job.

=== ⚠⚠ AND THE FIX HAD A LANDMINE AIMED AT ITSELF ===
`corroborate`'s count-and-mask invariant held a SECOND, hardcoded copy of the ledger->store map
with "uniques" simply absent — so the exclusion was accidental rather than stated. Its LEFT side is
dynamic and would start counting uniques the moment this fix shipped; its RIGHT side, frozen in a
literal, would not. The invariant would have gone RED because the code got MORE correct. It now
asks `ledger_authority.surface_pairs()` — one authority, no second copy. [[copy-drift]]

⚠ Fixing that, I referenced `la` in the right closure where it is imported only in the left, and my
own `except Exception: return None` SWALLOWED the NameError — right went 1 -> None while left went
1 -> 2. Caught by watching the numbers, not by anything failing. Same shape as the `qs` defect in
/api/river the same day.
"""
import ast
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import fleet_mask as FM  # noqa: E402
import ledger_authority as LA  # noqa: E402

CA_SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
CORR = io.open(os.path.join(HERE, "corroborate.py"), encoding="utf-8").read()


def _py_code(src):
    """Python source with comments stripped — never grade prose. [[source-reading-guard]]"""
    return re.sub(r"(?m)^\s*#[^\n]*", "", src)


def _js_code(src):
    src = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), src, flags=re.S)
    return re.sub(r"(?m)//[^\n]*", lambda m: " " * len(m.group(0)), src)


class TheCrossReferenceAsksOneQuestion(unittest.TestCase):

    # ── ⚠⚠ THE LAW: ONE QUESTION, PROVEN BY THE REPO'S OWN DETECTOR ───────────────────────────
    def test_every_ledger_reads_the_SAME_store_on_both_sides(self):
        """`surface_pairs()` exists to detect exactly this and reported uniques
        `sameQuestion: false` for weeks with nothing acting on it. It is the proof, not a proxy."""
        pairs = {str(p.get("ledger")): p for p in (LA.surface_pairs() or [])}
        self.assertTrue(pairs, "surface_pairs answered nothing — fix this guard first")
        bad = {k: (v.get("tallyStore"), v.get("maskStore"))
               for k, v in pairs.items() if not v.get("sameQuestion")}
        self.assertEqual({}, bad,
                         "a ledger's mask and tally still read different stores, so their numbers "
                         "are not comparable and the panel prints one label over two questions: %r"
                         % bad)

    def test_the_union_is_declared_on_EVERY_ledger(self):
        """⚠ A field present on one entry and absent on another is how a caller learns to write
        `.get("stores") or [spec["store"]]` in three places and forget it in a fourth."""
        for led, spec in FM.LEDGERS.items():
            self.assertIn("stores", spec, "%s declares no `stores`" % led)
            self.assertIsInstance(spec["stores"], list, "%s.stores is not a list" % led)
            self.assertIn(spec["store"], spec["stores"],
                          "%s's primary store is not among its stores — the string the detector "
                          "compares and the list the mask reads have diverged" % led)

    def test_uniques_reads_the_legacy_store_TOO(self):
        """The union is the whole point: `_ownedNames()` is `d2r_owned` + `keys(d2r_foundLog)`,
        and the legacy store is where the oldest finds live."""
        self.assertIn("d2r_owned", FM.LEDGERS["uniques"]["stores"],
                      "the legacy store was dropped, so a find recorded only there is invisible "
                      "to the mask while the board still counts it")
        self.assertEqual("d2r_foundLog", FM.LEDGERS["uniques"]["store"],
                         "the primary store is no longer the tally's store")

    # ── the mask must actually READ the union ────────────────────────────────────────────────
    def test_board_mask_reads_the_STORES_not_the_single_store(self):
        code = _py_code(CA_SRC)
        self.assertIn('spec.get("stores") or [spec["store"]]', code,
                      "board_mask still interpolates one store, so the union is declared and not "
                      "read — the spec would promise what the code does not do")
        self.assertIn('"var KS=%s;"', code, "the injected JS no longer takes a list of keys")

    def test_absent_and_unparseable_and_none_are_THREE_states(self):
        """A store this board never wrote is not an error (the legacy one is absent on a fresh
        install). One that exists and will not parse IS a fault. And no store at all is UNKNOWN —
        a board that wrote neither has not said he owns nothing."""
        code = _py_code(CA_SRC)
        self.assertIn("if(rawv==null||rawv===''){continue;}", code, "absent is not skipped")
        self.assertIn("bad.push(K)", code, "an unparseable store is not reported")
        self.assertIn("no store present on this board", code,
                      "a board with neither store returns a mask of zeros rather than UNKNOWN")

    # ── ⚠⚠ rosterN IS LOAD-BEARING AND MUST NOT BECOME THE DISPLAY NUMBER ────────────────────
    def test_rosterN_is_still_the_ROSTER_length(self):
        """decode() refuses a mask whose n != len(roster). If rosterN became 403 every mask on the
        fleet would be refused as a roster mismatch."""
        code = _py_code(CA_SRC)
        self.assertIn('out["rosterN"] = len(roster)', code,
                      "rosterN is no longer the roster length — masks will fail to decode")

    def test_the_denominator_he_reads_comes_from_the_BOARD_and_never_falls_back(self):
        import control_app as CA
        n, why = CA._fleet_show_total("uniques")
        self.assertEqual(403, n, "the shown denominator is not his pinned chronTotal")
        n2, why2 = CA._fleet_show_total("__no_such_ledger__")
        self.assertIsNone(n2, "an unknown ledger produced a confident denominator")
        self.assertTrue(why2, "an unknown denominator carries no reason")
        code = _py_code(CA_SRC)
        i = code.find("def _fleet_show_total")
        j = code.find("\ndef ", i + 1)
        self.assertNotIn("rosterN", code[i:j],
                         "the shown denominator falls back to the roster length, which silently "
                         "reinstates the defect and looks correct doing it")

    def test_the_panel_renders_showN_not_rosterN(self):
        js = _js_code(UI)
        self.assertIn("_fxDen(j)", js, "the panel no longer calls the denominator helper")
        self.assertNotIn("j.rosterN", js,
                         "the panel still prints rosterN — the number bible.html says is "
                         "'produced by neither, and NO array on the page is this size'")
        self.assertIn("function _fxDen(j)", js, "the helper is used but not declared")

    def test_the_helper_lives_in_the_SAME_script_block_as_its_caller(self):
        """⚠ A call across this file's two script blocks is a dead render and has cost four
        versions. Both must sit inside the second block."""
        blocks = [m.start() for m in re.finditer(r"(?m)^<script>", UI)]
        self.assertGreaterEqual(len(blocks), 2, "expected two script blocks")
        decl = UI.find("function _fxDen(j)")
        use = UI.find("_fxDen(j) + ' yours")
        self.assertGreater(decl, blocks[1], "_fxDen is declared in the FIRST block")
        self.assertGreater(use, blocks[1], "its caller is in the FIRST block")

    # ── ⚠⚠ THE LANDMINE MUST STAY DISARMED ───────────────────────────────────────────────────
    def test_corroborate_does_not_re_declare_the_ledger_store_map(self):
        code = _py_code(CORR)
        self.assertNotIn('"runewords": "d2r_rwMade"}', code,
                         "corroborate holds its own hardcoded ledger->store map again. That map "
                         "had 'uniques' absent, so the day the real fix shipped its LEFT side "
                         "would count uniques and its RIGHT side would not — the invariant going "
                         "RED because the code got more correct.")
        self.assertIn("la.surface_pairs()", code,
                      "the right side no longer asks the one authority")

    def test_la_is_imported_in_the_closure_that_uses_it(self):
        """⚠ It was not, and my own `except Exception: return None` swallowed the NameError —
        right went 1 -> None while left went 1 -> 2, which reads exactly like 'nothing to
        compare'. A name bound in a sibling scope plus a try that hides the raise."""
        i = CORR.find("_same = {str(p.get(\"ledger\"))")
        self.assertGreater(i, 0, "the surface_pairs read is gone")
        j = CORR.rfind("    def right():", 0, i)
        self.assertGreater(j, 0, "could not find the enclosing closure")
        self.assertIn("import ledger_authority as la", CORR[j:i],
                      "`la` is not imported in the closure that uses it")

    def test_it_still_parses(self):
        ast.parse(CA_SRC)
        ast.parse(CORR)


if __name__ == "__main__":
    unittest.main(verbosity=2)
