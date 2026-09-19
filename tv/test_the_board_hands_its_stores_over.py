# -*- coding: utf-8 -*-
"""A CONSOLE WITH NO NATIVE WINDOW COULD COUNT ITS ITEMS AND COULD NEVER NAME ONE.

Konyo, 2026-09-20, with a screenshot of his own fleet panel:

    "fleet is still not working from dean or from my side.. we cant see or cross reference
     the items we each have or both need.. so fix it becuase its still not fixed"

WHAT THE PANEL SHOWED, and the contradiction is arithmetic:

    Dean set pieces - yours vs theirs - you have 133 of 135
    YOU STILL NEED (2)          Cow King's Hooves, Vidala's Ambush        <- worked
    THEY HAVE - YOU DO NOT      "not published - no board window"        <- dead
    YOU BOTH NEED               "not published - no board window"        <- dead
    footer                      131 / 135 theirs (COUNT ONLY)

A count of 131 cannot be produced without knowing WHICH 131. Something enumerated them and
then stored only the total. [[heart-first]] section 6

=== WHY ONE HALF SURVIVED A MISSING WINDOW AND THE OTHER DID NOT ===

Both facts come from the board. They travel by DIFFERENT ROADS:

    the COUNT   board -> window.__tallyPersist -> POST /api/board_tally -> board_tally.json
                and grail_tally() falls back to that file (v2188). Works with no window.
    the LIST    console -> _ejs(window, js) -> evaluate JS inside a NATIVE pywebview window.
                No window, no answer. board_mask() had NO fallback at all.

A console opened as a PAGE IN A BROWSER against a headless server has no native window. It can
be HANDED facts over HTTP; it can never be ASKED for them. So it published a number for ever and
a list never. The sibling function had had the cure since v2188 and nobody carried it across.
[[the-unjoined-end]] [[plumbing-with-no-tap]]

=== WHAT CHANGED ===
`__tallyPersist` hands the raw ledger STORES over on the same loopback POST it already uses for
the counts; the route banks them; `_mask_from_board_store` composes the union per
`fleet_mask.LEDGERS` and mints the mask with `fleet_mask.encode` - which until now had ZERO
production callers, a guard built for exactly this and never reached.

⚠ NO ITEM NAME LEAVES THE MACHINE. Same-origin loopback in, base64 bits out. The fleet wire is
byte-for-byte the shape it already was.

⚠ THE LEDGER DEFINITION IS NOT RE-TYPED ON THE BOARD. The page hands over stores BY KEY; which
keys make up "sets" or "uniques" stays in fleet_mask.LEDGERS and is applied console-side, so the
live path and the fallback cannot answer differently about the same ledger. [[copy-drift]]

⚠ AND UNKNOWN STILL STAYS UNKNOWN. A ledger the board sent no store for returns None, never a
mask of zeros saying he owns nothing - which on this panel would read as a confident "they have
none of these" and is the one answer worse than a blank column. [[unknown-stays-unknown]]

MEASURED on his real sets roster with no window anywhere in the process: 135 names in, a board
holding 131, mask n=135 have=131, decoded back to 131 real set-piece names.
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ v3379 — MAKE STDOUT SURVIVE HIS CONSOLE BEFORE ANYTHING PRINTS. This file's messages carry
# non-ASCII, and his operator console is cp1255: without this the gate PASSES its check and then
# dies inside the print that reports it, so a clean tree exits non-zero for a reason that has
# nothing to do with the code. REG-044 / REG-054 / REG-077 are the same bug three times, and the
# pre-push gate refused this very push for it. [[windows-powershell-gotchas]]
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA
import fleet_mask as FM

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _strip_py_comments(src):
    """Grade CODE, never the prose about it. [[source-reading-guard]] section 4"""
    return "\n".join(re.sub(r"#.*$", "", ln) for ln in src.split("\n"))


def _between(src, a, b):
    """A region with a REAL end on both sides - never a byte count.
    [[source-reading-guard]] section 3 [[source-window-shortcut]]"""
    i = src.find(a)
    if i < 0:
        return ""
    j = src.find(b, i + len(a))
    return src[i:j] if j > i else src[i:]


class TheBoardHandsItsStoresOver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.roster, cls.fp = FM.load_roster_for("sets")
        # bible.html is ~6 MB; read it ONCE and only the persist function out of it.
        cls.persist = ""
        try:
            with io.open(BIBLE, encoding="utf-8") as fh:
                cls.persist = _between(fh.read(), "window.__tallyPersist = function(){",
                                       "window.__tallyPersist();")
        except Exception:
            cls.persist = ""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="storesover_")
        self._old_path = CA._board_stores_path
        CA._board_stores_path = lambda: os.path.join(self.d, "board_stores.json")
        self._old_why = dict(CA._MASK_WHY)

    def tearDown(self):
        CA._board_stores_path = self._old_path
        CA._MASK_WHY.clear()
        CA._MASK_WHY.update(self._old_why)
        shutil.rmtree(self.d, ignore_errors=True)

    def _hand_over(self, stores, who=None):
        CA.board_stores_save({"v": 1,
                              "who": who if who is not None else {"id": "abc", "p": "main", "pfx": ""},
                              "route": who if who is not None else {"id": "abc", "p": "main", "pfx": ""},
                              "stores": stores, "storeWhy": {}, "at": 1})

    # ── the defect itself, end to end, with no native window in the process ──────────────
    def test_a_console_with_no_window_can_NAME_what_it_holds(self):
        if not self.roster:
            self.skipTest("no sets roster on this venue")
        owned = list(self.roster[:131])
        self._hand_over({"d2r_setPieces": owned})
        mask, why = CA._mask_from_board_store("sets")
        self.assertTrue(mask, "no mask came back from the hand-over: %s" % why)
        self.assertEqual(mask.get("n"), len(self.roster))
        self.assertEqual(mask.get("have"), 131)
        names, dwhy = FM.decode(mask, self.roster, self.fp, side="that machine")
        self.assertIsNotNone(names, "the minted mask would not decode: %s" % dwhy)
        self.assertEqual(sorted(names), sorted(owned),
                         "the names that came back are not the names that went in")

    def test_the_mask_survives_the_wire_shape_the_fleet_already_carries(self):
        """Nothing about the PUBLISHED shape changes - only how it is obtained."""
        if not self.roster:
            self.skipTest("no sets roster on this venue")
        self._hand_over({"d2r_setPieces": list(self.roster[:5])})
        mask, _ = CA._mask_from_board_store("sets")
        self.assertEqual(sorted(mask.keys()), sorted(FM.sanitize_for_wire(mask).keys()))
        for k in ("v", "r", "n", "have", "b"):
            self.assertIn(k, mask, "the minted mask is missing %r, so the far end cannot bind it "
                                   "to a roster" % k)

    # ── UNKNOWN stays UNKNOWN ────────────────────────────────────────────────────────────
    def test_no_store_handed_over_is_UNKNOWN_never_a_mask_of_zeros(self):
        self._hand_over({"d2r_setPieces": list(self.roster or [])[:2]})
        mask, why = CA._mask_from_board_store("uniques")
        self.assertIsNone(mask, "a ledger the board sent NO store for produced a mask - on his "
                                "panel that reads as a confident 'they have none of these'")
        self.assertIn("UNKNOWN", why)

    def test_nothing_banked_at_all_is_UNKNOWN(self):
        mask, why = CA._mask_from_board_store("sets")
        self.assertIsNone(mask)
        self.assertIn("not handed", why)

    def test_a_handover_that_does_not_say_whose_it_is_is_refused(self):
        """A mask published under the wrong world is worse than no mask - v3213 and v3215 are
        both scars about exactly that, and the tally reader already holds this bar."""
        CA.board_stores_save({"v": 1, "stores": {"d2r_setPieces": list(self.roster or [])[:3]},
                              "at": 1})
        mask, why = CA._mask_from_board_store("sets")
        self.assertIsNone(mask, "an unattributed hand-over was published as this board's mask")
        self.assertIn("whose", why)

    def test_a_store_that_is_not_a_list_is_refused_not_coerced(self):
        self._hand_over({"d2r_setPieces": {"Aldur's Advance (boots)": 1}})
        mask, why = CA._mask_from_board_store("sets")
        self.assertIsNone(mask, "a malformed store was coerced into an answer")
        self.assertIn("not a list", why)

    def test_a_measured_empty_store_IS_kept(self):
        """⚠ THE OTHER DIRECTION, and it is the one that looks like safety and is not.
        Refusing an empty list would make 'he owns none of these' unsayable - a real answer this
        panel needs, and the exact collapse v3175 fixed for the mineNames side."""
        if not self.roster:
            self.skipTest("no sets roster on this venue")
        self._hand_over({"d2r_setPieces": []})
        mask, why = CA._mask_from_board_store("sets")
        self.assertTrue(mask, "a measured-empty store was refused: %s" % why)
        self.assertEqual(mask.get("have"), 0)
        names, _ = FM.decode(mask, self.roster, self.fp)
        self.assertEqual(names, [], "a decoded-empty must be [], never None")

    # ── the refusal says everything it knows ─────────────────────────────────────────────
    def test_the_refusal_names_BOTH_the_window_and_the_handover(self):
        CA._MASK_WHY["sets"] = None
        got = CA._mask_fallback("sets", "this console has no native window")
        self.assertIsNone(got)
        w = CA._MASK_WHY["sets"] or ""
        self.assertIn("no native window", w,
                      "the recorded reason dropped the LIVE failure, so the panel would blame "
                      "the hand-over for a window problem")
        self.assertIn("handed its stores over", w)

    def test_a_successful_fallback_CLEARS_the_reason(self):
        if not self.roster:
            self.skipTest("no sets roster on this venue")
        CA._MASK_WHY["sets"] = "a stale reason from a previous beat"
        self._hand_over({"d2r_setPieces": list(self.roster[:9])})
        got = CA._mask_fallback("sets", "no native window")
        self.assertTrue(got)
        self.assertIsNone(CA._MASK_WHY["sets"],
                          "the mask published fine and the panel still carries a refusal string")

    # ── reachability: EVERY refusal goes through the fallback ────────────────────────────
    def test_every_refusal_in_board_mask_routes_through_the_fallback(self):
        """⚠ A FALLBACK WIRED AT FIVE OF SIX REFUSALS IS THE DEFECT WEARING A FIX'S CLOTHES.

        Behavioural, not a grep: this makes the hand-over return a sentinel and requires
        `board_mask` - which in this process has no native window at all - to hand it back.
        """
        SENTINEL = {"v": "fp", "r": "rr", "n": 1, "have": 1, "b": "AQ"}
        old = CA._mask_from_board_store
        try:
            CA._mask_from_board_store = lambda ledger="sets": (dict(SENTINEL), "")
            got = CA.board_mask("sets")
        finally:
            CA._mask_from_board_store = old
        self.assertEqual(got, SENTINEL,
                         "board_mask refused without consulting the hand-over - a refusal path "
                         "was left unwired")

    def test_no_caller_still_reaches_the_old_give_up_name(self):
        """[[label-outlived-referent]] - a function named give_up that sometimes succeeds.

        ⚠ ANCHOR ON THE CALL, NOT THE NAME. The first cut asserted the STRING was absent and went
        red on the ship note explaining the rename - a negative assertion tripping on its own
        prose, which is [[source-reading-guard]] section 4 and is written in this very file's own
        helper. The rename is recorded on purpose; what must not survive is a CALLER.
        """
        import ast
        tree = ast.parse(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)
        self.assertNotIn("_mask_give_up", called,
                         "a caller still reaches the old name, which no longer describes what "
                         "the function does")
        self.assertIn("_mask_fallback", called,
                      "nothing calls the fallback at all - instrument failure, not a pass")

    # ── the board half ───────────────────────────────────────────────────────────────────
    def test_the_board_actually_SENDS_the_stores(self):
        if not self.persist:
            self.skipTest("bible.html is not readable from this venue")
        code = _strip_py_comments(self.persist.replace("/*", "#").replace("*/", ""))
        self.assertIn("stores: _sd.stores", code,
                      "__tallyPersist does not put the stores on the payload, so the console has "
                      "nothing to bank and the fallback can never fire")

    def test_the_ledger_definition_is_not_re_typed_on_the_board(self):
        """⚠ THE COPY-DRIFT LAW, and it fails in the direction that actually bites: the console
        asking for a store the page never offers. Every store any ledger is made of must be in
        the page's hand-over list, or that ledger is silently unanswerable."""
        if not self.persist:
            self.skipTest("bible.html is not readable from this venue")
        want = set()
        for spec in FM.LEDGERS.values():
            for k in (spec.get("stores") or [spec["store"]]):
                want.add(k)
        self.assertTrue(want, "fleet_mask declares no stores - instrument failure, not a pass")
        for k in sorted(want):
            self.assertIn("'%s'" % k, self.persist,
                          "fleet_mask composes a ledger from %r and the board never hands that "
                          "store over" % k)

    # ── the route banks the list independently of the counts ─────────────────────────────
    WHO = {"id": "abc", "p": "main", "pfx": ""}

    def test_a_handover_with_a_list_and_NO_counts_still_banks(self):
        """One missing half must not blank the other - the v3175 lesson, same panel.

        ⚠ BEHAVIOURAL, AND IT WAS NOT. The first cut read `do_POST`'s source for ORDERING, and a
        sabotage that disabled the banking outright left that text untouched: PROVEN BLIND at a
        correct match count of 1, which is the case that means the LAW is weak. The validation is
        a callable function now, so this drives it.
        """
        saved, why = CA.accept_handed_stores({"stores": {"d2r_setPieces": ["A", "B"]}}, self.WHO)
        self.assertEqual(saved, 1, "a hand-over carrying a real store was not banked (%s)" % why)
        doc = CA.board_stores_load()
        self.assertEqual((doc or {}).get("stores", {}).get("d2r_setPieces"), ["A", "B"])

    def test_a_store_the_board_could_not_read_is_DROPPED_not_banked_as_empty(self):
        saved, why = CA.accept_handed_stores(
            {"stores": {"d2r_setPieces": None, "d2r_foundLog": "nope"}}, self.WHO)
        self.assertEqual(saved, 0, "an unreadable store was banked as an answer")
        self.assertIn("no readable store", why or "")
        self.assertIsNone(CA.board_stores_load(),
                          "nothing readable arrived and a document was written anyway")

    def test_a_store_over_the_cap_is_refused_AND_named(self):
        big = ["n%d" % i for i in range(CA._BOARD_STORE_MAX + 1)]
        saved, why = CA.accept_handed_stores({"stores": {"d2r_setPieces": big}}, self.WHO)
        self.assertEqual(saved, 0)
        self.assertIn("over the cap", why or "",
                      "an oversized store was refused silently, so nobody can tell it from an "
                      "absent one")

    def test_the_route_asks_the_function_rather_than_inlining_it_again(self):
        """⚠ REACHABILITY: logic a gate cannot call is logic nothing can prove. If the handler
        re-inlines this, every behavioural law above keeps passing over dead code."""
        import inspect
        post = _strip_py_comments(inspect.getsource(CA.Handler.do_POST))
        blk = _between(post, '"/api/board_tally"', '"/api/chronicle_apply"')
        self.assertTrue(blk, "the board_tally branch could not be located - instrument failure")
        i_call = blk.find("accept_handed_stores(")
        i_ref = blk.find("no readable counts in that tally")
        self.assertGreaterEqual(i_call, 0, "the route no longer asks accept_handed_stores")
        self.assertGreaterEqual(i_ref, 0, "the no-counts refusal moved - re-anchor this law")
        self.assertLess(i_call, i_ref,
                        "the stores are taken AFTER the route can already have returned for "
                        "having no counts, so a hand-over carrying a list and no totals is lost")


RED_PROOF = [
    {
        'why': 'THE WHOLE DEFECT: cut the fallback out of the one function every refusal funnels '
               'through, and a console with no native window is back to publishing a count and '
               'never a list. test_a_console_with_no_window_can_NAME_what_it_holds and '
               'test_every_refusal_in_board_mask_routes_through_the_fallback must fail.',
        'file': 'control_app.py',
        'find': '        m, bwhy = _mask_from_board_store(key)',
        'replace': '        m, bwhy = None, "disabled"',
        'matches': 1,
    },
    {
        'why': 'THE DIRECTION THAT COSTS SOMETHING. Let a ledger with no handed-over store mint a '
               'mask anyway and it encodes to all zeros, which the far end renders as a confident '
               '"they have none of these". test_no_store_handed_over_is_UNKNOWN_never_a_mask_of_zeros '
               'must fail.',
        'file': 'control_app.py',
        'find': '    if not seen:\n        return None, ("the board handed over no store for %s',
        'replace': '    if False:\n        return None, ("the board handed over no store for %s',
        'matches': 1,
    },
    {
        'why': 'drop the attribution bar and an unattributed hand-over publishes as this board\'s '
               'mask - the v3213/v3215 scar, which is a mask of the WRONG WORLD reported as ok. '
               '⚠ THE FIRST ANCHOR MATCHED TWICE (the tally reader holds the same bar), so the '
               'tamper was INVALID rather than the law being weak - anchored on the line plus its '
               'own refusal text, which occurs once. '
               'test_a_handover_that_does_not_say_whose_it_is_is_refused must fail.',
        'file': 'control_app.py',
        'find': '    if not isinstance(route, dict) or not route.get("id"):\n        return None, "the banked hand-over does not say whose board wrote it"',
        'replace': '    if False:\n        return None, "the banked hand-over does not say whose board wrote it"',
        'matches': 1,
    },
    {
        'why': 'coerce a malformed store instead of refusing it and the union silently loses '
               'names. test_a_store_that_is_not_a_list_is_refused_not_coerced must fail.',
        'file': 'control_app.py',
        'find': '        if not isinstance(v, list):\n            return None, "the banked store %s is not a list" % key',
        'replace': '        if not isinstance(v, list):\n            continue',
        'matches': 1,
    },
    {
        'why': 'report only the second failure and the panel blames the hand-over for a window '
               'problem. test_the_refusal_names_BOTH_the_window_and_the_handover must fail.',
        'file': 'control_app.py',
        'find': '    _MASK_WHY[key] = ("%s; and the board has not handed its stores over either (%s)"\n                      % (live, bwhy or "no reason given"))[:400]',
        'replace': '    _MASK_WHY[key] = ("the board has not handed its stores over (%s)"\n                      % (bwhy or "no reason given"))[:400]',
        'matches': 1,
    },
    {
        'why': 'refuse EVERY hand-over and the console banks nothing, so the fallback has nothing to '
               'mint from and the panel is back to a count with no names. ⚠ THE FIRST TAMPER HERE '
               'CAME BACK BLIND AT A CORRECT COUNT OF 1: the law read do_POST source for ORDERING '
               'and disabling the banking moved no text, so the LAW was weak, not the sabotage - '
               'the validation was extracted into accept_handed_stores so a gate can drive it. '
               'test_a_handover_with_a_list_and_NO_counts_still_banks must fail.',
        'file': 'control_app.py',
        'find': '    if not clean:\n        return 0, (why or "no readable store in that hand-over")',
        'replace': '    if True:\n        return 0, (why or "no readable store in that hand-over")',
        'matches': 1,
    },
    {
        'why': 'THE BOARD HALF. Stop putting the stores on the payload and the console has '
               'nothing to bank - the console-side fix would look complete and deliver nothing, '
               'which is this whole territory. test_the_board_actually_SENDS_the_stores must fail.',
        'file': '../bible.html',
        'find': '        stores: _sd.stores,',
        'replace': '        stores: null,',
        'matches': 1,
    },
    {
        'why': 'drop the legacy uniques store from the board hand-over list. fleet_mask composes '
               'uniques from d2r_foundLog UNION d2r_owned, so the console would ask for a store '
               'the page never sends and the oldest finds would vanish from the cross-reference. '
               'test_the_ledger_definition_is_not_re_typed_on_the_board must fail.',
        'file': '../bible.html',
        'find': "        var KS = ['d2r_setPieces', 'd2r_foundLog', 'd2r_owned'];",
        'replace': "        var KS = ['d2r_setPieces', 'd2r_foundLog'];",
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
