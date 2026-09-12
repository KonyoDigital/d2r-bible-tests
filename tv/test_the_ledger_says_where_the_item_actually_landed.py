#!/usr/bin/env python3
"""v3000 (#74) — `store` WAS A CLAIM ABOUT WHERE AN ITEM IS, WRITTEN BEFORE ANYONE LOOKED.

In the tvVaultRegister wrapper, `status` is DERIVED from the outcome and can say 'route-failed'.
Three lines below it, in the same object literal, `store: 'owned'` was asserted on EVERY row — so
one row could read `status:'route-failed'` and `store:'owned'` in the same breath. The vault is the
store whose mistakes are permanent and the one he has actually been bitten by, and this is the
field a reader consults to answer "where did it go".

MEASURED PREVIOUSLY (not re-derived when this gate was written, and labelled so rather than
re-asserted): of 360 rows carrying a `store`, 11 named a store whose contents lack that name —
owned 2/4, foundLog 8/344, assign 1/1. The STRUCTURAL defect needs no sampling: it is visible in
the source, because a literal cannot be wrong only sometimes. [[inherited-claim-is-not-evidence]]

★★ THE TRAP THIS FIX HAD TO AVOID, AND IT IS THE ONE THIS FILE HAS SPRUNG FOUR TIMES.
`_chSetHas` / `_chLsGet` already do exactly what the new reader needs. They are defined in a LATER
<script> block (#24) and neither is exported to window; the write site is block #17. Calling them
from here is a ReferenceError at runtime — a dead render that reads as perfectly correct in review.
`window.LSR` is assigned in block #1 and is what `_chLsGet` itself reads through, so the fix
borrows the TRANSPORT and not the scope. [[console-ui-two-script-blocks]]

⚠ THREE ANSWERS, NEVER TWO. A store that could not be READ is UNKNOWN (null), not "the item is not
there" (which would publish a confident wrong `store` — the same class of lie as the literal it
replaces). [[unknown-stays-unknown]]
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIBLE = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()

OPEN_ANCHOR = "    function _ownedNow(n){"
CLOSE_ANCHOR = "    function _known(n){"

STORE_OPEN = "            store: (r && r.ok)"
STORE_CLOSE = "            ledger: 'vault',"


def _store_expr():
    """-> the SHIPPED `store:` expression, wrapped as a callable. None if it moved.

    ⚠⚠ THE FIRST CUT CARRIED A COPY OF THIS EXPRESSION IN THIS FILE, AND heart2 CALLED IT BLIND.
    Restoring the flat `store: 'owned'` literal in bible.html — the defect verbatim — left every
    test GREEN, because the tests were executing the reproduction rather than the shipped bytes.
    A law that grades its own copy of the code cannot fail when the code changes.
    [[sabotage-is-usually-the-wrong-one]] [[feedback-blind-fixture-green-gate]]
    """
    a = BIBLE.find(STORE_OPEN)
    if a < 0:
        return None
    b = BIBLE.find(STORE_CLOSE, a)
    if b < a:
        return None
    body = BIBLE[a:b].strip().rstrip(",")
    if not body.startswith("store:"):
        return None
    return "function storeFor(r, nm){ return (%s); }" % body[len("store:"):].strip()


def _reader():
    """-> the shipped _ownedNow source, or None if it moved.

    ⚠ ANCHORED AT BOTH ENDS. A fixed-size window past the region reads as ABSENT and invents a
    finding — four times in one session. [[source-window-shortcut]]
    """
    a = BIBLE.find(OPEN_ANCHOR)
    if a < 0:
        return None
    b = BIBLE.find(CLOSE_ANCHOR, a)
    if b < a:
        return None
    return BIBLE[a:b]


class TheLedgerSaysWhereTheItemActuallyLanded(unittest.TestCase):

    def _store(self, owned_raw, r, nm="Shako"):
        """Execute the SHIPPED reader in node. -> the store value the row would carry."""
        src = _reader()
        if src is None:
            self.skipTest("the _ownedNow reader moved — a skip is NOT a pass")
        expr = _store_expr()
        if expr is None:
            # ⚠⚠ heart2 CALLED THIS GATE BLIND FOR EXACTLY THIS LINE. It used to skipTest, so the
            # tamper that restores `store: 'owned'` removed the anchor, 7 laws SKIPPED, and the
            # gate reported green through its own defeat. A guard that cannot reach its subject
            # has not passed — it has failed to look. [[source-reading-guard]] [[regression-guard]]
            self.fail("the shipped `store:` expression could not be located in bible.html. Either "
                      "it moved, or it is no longer a computed expression — both mean this law is "
                      "not grading anything, which is NOT a pass.")
        js = ("var window = {};\n" + src + expr + """
var RAW = %s;
window.LSR = { getItem: function(){ if (RAW === '__THROW__') throw new Error('boom'); return RAW; } };
console.log(JSON.stringify(storeFor(%s, %s)));
""" % (json.dumps(owned_raw), json.dumps(r), json.dumps(nm)))
        d = tempfile.mkdtemp(prefix="storefield_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            out = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED by this gate and is not on PATH. ⚠⚠ THIS USED TO "
                      "skipTest, and MEASURED 2026-09-12 with node hidden: the gate printed "
                      "'OK (skipped=13)' and EXITED 0, so the runner read it as a PASS while 13 "
                      "of its 21 laws never ran — including every law that guards the shipped "
                      "block. A venue without node is a venue where these laws are absent, not "
                      "one where they hold. run_gates only counts a skip as failure when the "
                      "GATE exits 77; unittest exits 0 when its tests skip, so the skip was "
                      "invisible to the harness too. [[regression-guard]] [[test-venue]]")
        if out.returncode != 0:
            self.fail("the shipped reader would not execute: %s" % (out.stderr or "")[:300])
        return json.loads(out.stdout.strip().splitlines()[-1])

    OWNED = json.dumps(["Shako", "Occulus"])

    # ── the lie it exists to end ──────────────────────────────────────────────────────────────
    def test_a_failed_route_never_claims_a_store(self):
        """The headline defect: status 'route-failed' and store 'owned' in the same row."""
        self.assertIsNone(self._store(self.OWNED, {"ok": False, "why": "refused"}),
                          "nothing landed, so the row may not name a store")

    def test_a_throwout_is_not_called_owned(self):
        """A throw-out is the one decision with no undo and the one most worth his eye."""
        self.assertEqual(
            self._store(self.OWNED, {"ok": True, "mode": "throwout", "name": "Shako"}),
            "throwout-review")

    def test_a_name_the_store_does_not_hold_is_not_called_owned(self):
        self.assertIsNone(
            self._store(json.dumps(["Occulus"]), {"ok": True, "mode": "new", "name": "Shako"}),
            "the register reported ok, but d2r_owned does not hold the name — the row must not "
            "say it does")

    # ── and it must still say 'owned' when that is true ───────────────────────────────────────
    def test_a_real_arrival_is_owned(self):
        self.assertEqual(
            self._store(self.OWNED, {"ok": True, "mode": "new", "name": "Shako"}), "owned")

    def test_a_repeat_sighting_is_owned(self):
        self.assertEqual(
            self._store(self.OWNED, {"ok": True, "mode": "already", "name": "Shako"}), "owned")

    def test_the_comparison_matches_the_chronicle_helper(self):
        """_chSetHas compares trimmed and lowercased on an array. Diverging would make this row
        disagree with every other store check in the file."""
        self.assertEqual(
            self._store(json.dumps(["  shako "]), {"ok": True, "mode": "new", "name": "Shako"}),
            "owned")

    # ── not knowing must never resolve to a verdict ───────────────────────────────────────────
    def _owned_now(self, raw, nm="Shako"):
        """Call the SHIPPED _ownedNow directly, so true/false/null are distinguishable."""
        src = _reader()
        if src is None:
            self.skipTest("the reader moved — a skip is NOT a pass")
        js = ("var window = {};\n" + src + """
var RAW = %s;
window.LSR = { getItem: function(){ if (RAW === '__THROW__') throw new Error('boom'); return RAW; } };
console.log(JSON.stringify(_ownedNow(%s)));
""" % (json.dumps(raw), json.dumps(nm)))
        d = tempfile.mkdtemp(prefix="ownednow_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            out = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED by this gate and is not on PATH. ⚠⚠ THIS USED TO "
                      "skipTest, and MEASURED 2026-09-12 with node hidden: the gate printed "
                      "'OK (skipped=13)' and EXITED 0, so the runner read it as a PASS while 13 "
                      "of its 21 laws never ran — including every law that guards the shipped "
                      "block. A venue without node is a venue where these laws are absent, not "
                      "one where they hold. run_gates only counts a skip as failure when the "
                      "GATE exits 77; unittest exits 0 when its tests skip, so the skip was "
                      "invisible to the harness too. [[regression-guard]] [[test-venue]]")
        if out.returncode != 0:
            self.fail("the shipped reader would not execute: %s" % (out.stderr or "")[:300])
        return json.loads(out.stdout.strip().splitlines()[-1])

    def test_an_unreadable_store_is_unknown_not_a_denial(self):
        """⚠⚠ THIS MUST ASK THE HELPER, NOT THE ROW. My first version asserted the ROW's `store`
        was null when the store could not be read — and heart2 called it BLIND, correctly: the
        expression tests `=== true`, so false and null both produce null and the tamper changed
        nothing observable. The three-valued contract only exists at the helper, so that is where
        it has to be graded. false here would mean "the item is NOT in his vault" on a read that
        never happened. [[unknown-stays-unknown]]"""
        self.assertIsNone(self._owned_now("__THROW__"),
                          "a store that threw on read is UNKNOWN (null); false would assert the "
                          "item is absent from a read that never succeeded")
        self.assertIs(self._owned_now(json.dumps(["Shako"])), True,
                      "and a real hit must still be true, or the fix is just a way of never "
                      "saying owned")
        self.assertIs(self._owned_now(json.dumps(["Occulus"])), False,
                      "a store read fine that lacks the name is a measured FALSE, not unknown")

    def test_a_store_of_the_wrong_shape_is_unknown(self):
        self.assertIsNone(self._store(json.dumps({"a": 1}),
                                      {"ok": True, "mode": "new", "name": "Shako"}))

    # ── the cross-block trap ──────────────────────────────────────────────────────────────────
    def test_the_reader_does_not_call_a_helper_from_another_script_block(self):
        """⚠⚠ `_chSetHas`/`_chLsGet` are block #24; this site is block #17 and neither is on
        window. Borrowing them is a ReferenceError at runtime and looks correct in review. This
        file has shipped that defect four times."""
        src = _reader()
        if src is None:
            self.skipTest("the reader moved — a skip is NOT a pass")
        # ⚠ COMMENTS STRIPPED FIRST. The first cut asserted the NAME was absent and went red on the
        # reader's own comment, which names the helper precisely to say it is NOT being called. A
        # law about a CALL must not be satisfiable by prose — mine has tripped on mine before.
        # [[sabotage-is-usually-the-wrong-one]] [[source-reading-guard]]
        code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code = re.sub(r"//[^\n]*", "", code)
        for helper in ("_chSetHas", "_chLsGet", "_chMapHas", "_chNameKeys"):
            self.assertNotIn(helper + "(", code,
                             "%s lives in a later <script> block and is not exported to window; "
                             "calling it here is a dead render" % helper)
        self.assertIn("window.LSR", src,
                      "the reader must go through window.LSR — assigned in the FIRST block, and "
                      "what _chLsGet itself reads through")

    def test_the_store_is_computed_from_the_outcome_not_asserted(self):
        """⚠ MY FIRST VERSION MATCHED ONE EXACT STRING and heart2 walked straight past it: the
        tamper wrote `store: 'owned', _dead: ...`, which is the same lie in different bytes. The
        law is not "that one literal is absent" — it is "this value is DERIVED from what happened".
        """
        a = BIBLE.find(STORE_OPEN[:len("            store:")])
        self.assertGreater(a, -1, "no `store:` field in the ledger row at all")
        b = BIBLE.find(STORE_CLOSE, a)
        self.assertGreater(b, a, "the ledger row lost its `ledger:` field")
        val = BIBLE[a:b].split("store:", 1)[1].strip().rstrip(",")
        self.assertFalse(val.startswith("'") or val.startswith('"'),
                         "`store` is a bare literal (%s) — it asserts where the item is before "
                         "anyone looked, which is the defect this gate exists for" % val[:40])
        for token in ("r.ok", "_ownedNow"):
            self.assertIn(token, val,
                          "`store` must be derived from the register's OUTCOME; %r does not "
                          "mention %s" % (val[:60], token))


RED_PROOF = [
    {
        "why": "restoring the flat literal is the defect verbatim: a route-failed row claiming the "
               "item is in his vault",
        "file": "bible.html",
        "find": "            store: (r && r.ok)",
        "replace": "            store: 'owned', _dead: (r && r.ok)",
        "matches": 1,
    },
    {
        "why": "returning false instead of null when the store cannot be read turns 'nobody could "
               "look' into 'the item is not there', which is a confident wrong store",
        "file": "bible.html",
        "find": "      } catch(e){ return null; }                       /* could not read \\u2014 UNKNOWN, never false */",
        "replace": "      } catch(e){ return false; }",
        "matches": 1,
    },
    {
        "why": "reading raw localStorage instead of window.LSR bypasses the transport every other "
               "store check in this file uses",
        "file": "bible.html",
        "find": "        var raw = (window.LSR && window.LSR.getItem) ? window.LSR.getItem('d2r_owned') : null;",
        "replace": "        var raw = localStorage.getItem('d2r_owned');",
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠ his console is cp1255 and cannot encode the arrows and stars above; without this a CORRECT
    # tree reports FAILURE because the process dies inside its own print.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
