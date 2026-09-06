# -*- coding: utf-8 -*-
"""v2739 — THE RESET BUTTON, AND THE TWO WAYS IT COULD HAVE BEEN A LIE.

Konyo: *"the reset button to bypass the uniques chronicle for main tab of deans console and in
generall the console just add tha tbutton with a safegaurd like i mentioned"*, and before that,
unambiguously: *"i want it no wiped"* about his sets and runewords.

=== THE TWO PROPERTIES THIS EXISTS FOR ===

1. ⛔ UNIQUES ONLY. `d2r_foundLog` carries SET-PIECE rows alongside uniques — measured while
   building the rebuild, where ignoring `d2r_setPieces` made 132 set pieces look "unreachable".
   A reset that cleared foundLog wholesale would take his set-piece dates with it and report
   success. His row says it plainly: sets (123) and runewords (99) do not move, with a gate.

2. ⚠⚠ IT IS TWO ACTS, AND ONE ACT SILENTLY UNDOES ITSELF. bible.html's boot path re-seeds every
   missing `_GRAIL_SEED` name on EVERY load, guarded only by `if (_gUn[n]) return;` — the
   `d2r_grailUnfound` registry. A reset that only deleted rows would look like it worked and the
   chronicle would refill itself on the next page load. That is the worst possible failure for a
   button whose entire promise is a clean slate, and it would look exactly like success.

⚠ THIS RUNS THE REAL JAVASCRIPT. `_uniqueResetPlan` and `_uniqueResetDo` are sliced out of
bible.html by anchor and executed in node against a synthetic store, with the roster and `_regKey`
stubbed so the LOGIC under test is mine rather than the whole 6MB file. A source grep would pin the
spelling of a fix; this pins the behaviour.
⚠ NO NODE = SKIP WITH A REASON, NEVER A PASS. [[regression-guard]]
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = os.path.join(ROOT, "bible.html")


def _fns():
    """The two functions under test, sliced from bible.html. -> str or None"""
    src = io.open(BIBLE, encoding="utf-8").read()
    i = src.find("window._uniqueResetPlan = function()")
    j = src.find("window._uniqueResetAsk = async function()")
    return None if (i < 0 or j < 0 or j <= i) else src[i:j]


HARNESS = r"""
const STORE = %(store)s;
const LS = {
  getItem: (k) => Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null,
  setItem: (k, v) => { STORE[k] = String(v); }
};
globalThis.window = globalThis;
window.LSR = LS;
window.localStorage = LS;
// the roster and the fold, stubbed: what is under test is the RESET logic, not the 6MB roster
window._gUniqueRoster = () => %(roster)s;
window._regKey = (x) => String(x || '').toLowerCase().replace(/[^a-z0-9]/g, '');
window._GRAIL_SEED = %(seed)s;
%(fns)s
const plan = window._uniqueResetPlan();
const done = plan.ok ? window._uniqueResetDo(plan) : null;
console.log(JSON.stringify({ plan: plan, done: done, store: STORE }));
"""

ROSTER = ["Shako", "Occy", "Stone of Jordan"]
#: ⚠⚠ THE FIXTURE IS SHAPED SO EACH SWEEP HAS A VICTIM ONLY IT CAN SAVE, and the first version was
#: NOT. Every seed name was also a cleared name, so removing either sweep left the other one
#: covering for it and BOTH sabotages passed 9/9 — a law that could not fail, which is worse than
#: no law because it reads as coverage. Sabotage found it; the fixture was the defect, not the code.
#:   "Occy"            cleared but NOT a seed name -> only the plan sweep can un-tick it
#:   "Stone of Jordan" a seed name with NO row     -> only the seed sweep can un-tick it
#: [[sabotage-is-usually-the-wrong-one]] [[feedback-blind-fixture-green-gate]]
SEED = {"Shako": "Jan 1, 2026 · 00:00", "Stone of Jordan": "Jan 3, 2026 · 00:00"}
STORE = {
    # two uniques and TWO SET PIECES living in the same foundLog, which is the real shape
    "d2r_foundLog": json.dumps({"Shako": "d1", "Occy": "d2",
                                "Angelic Halo": "d3", "Sigon's Shelter": "d4"}),
    "d2r_owned": json.dumps(["Shako", "Angelic Halo"]),
    "d2r_gameFound": json.dumps({"Shako": {"at": "01/01/2026, 00:00"}}),
    "d2r_setPieces": json.dumps(["Angelic Halo", "Sigon's Shelter", "Tal Rasha's Mask"]),
    "d2r_rwMade": json.dumps({"Spirit": 1, "Insight": 1}),
    "d2r_grailUnfound": "{}",
}


def _run(store=None):
    fns = _fns()
    if fns is None:
        return None, "the reset functions could not be sliced out of bible.html"
    js = HARNESS % {"store": json.dumps(store or STORE, ensure_ascii=False),
                    "roster": json.dumps(ROSTER, ensure_ascii=False),
                    "seed": json.dumps(SEED, ensure_ascii=False), "fns": fns}
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.cjs")
    io.open(p, "w", encoding="utf-8").write(js)
    try:
        out = subprocess.check_output(["node", p], stderr=subprocess.STDOUT, timeout=30)
        return json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1]), ""
    except subprocess.CalledProcessError as e:
        return None, "node refused: %s" % e.output.decode("utf-8", "replace")[:500]
    finally:
        shutil.rmtree(d, ignore_errors=True)


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — this gate runs REAL bible.html javascript, and without an "
                 "engine it is a SKIP with a declared reason, never a pass")
class TheResetTouchesUniquesOnly(unittest.TestCase):

    def test_the_functions_can_be_sliced_AT_ALL(self):
        """⚠ A gate that cannot find its subject passes having examined nothing."""
        fns = _fns()
        self.assertIsNotNone(fns, "bible.html no longer yields _uniqueResetPlan/_uniqueResetDo")
        self.assertIn("d2r_grailUnfound", fns, "the sliced code no longer touches the un-tick store")

    # ── ⛔ HIS SETS AND RUNEWORDS DO NOT MOVE ──────────────────────────────────────────────────
    def test_SETS_are_byte_for_byte_unchanged(self):
        got, why = _run()
        self.assertIsNotNone(got, why)
        self.assertEqual(STORE["d2r_setPieces"], got["store"]["d2r_setPieces"],
                         "the reset changed d2r_setPieces. His instruction was 'i want it no "
                         "wiped' about exactly this store.")

    def test_RUNEWORDS_are_byte_for_byte_unchanged(self):
        got, why = _run()
        self.assertIsNotNone(got, why)
        self.assertEqual(STORE["d2r_rwMade"], got["store"]["d2r_rwMade"],
                         "the reset changed d2r_rwMade — his 99 forged runewords")

    def test_a_SET_PIECE_row_inside_foundLog_SURVIVES(self):
        """⚠⚠ THE ONE THAT MATTERS MOST. foundLog holds both kinds, so a wholesale clear would
        take his set-piece DATES while leaving d2r_setPieces intact — the loss would be invisible
        in the store this file's other laws check."""
        got, why = _run()
        self.assertIsNotNone(got, why)
        fl = json.loads(got["store"]["d2r_foundLog"])
        self.assertIn("Angelic Halo", fl, "a set piece's row was cleared by the UNIQUES reset")
        self.assertIn("Sigon's Shelter", fl, "a set piece's row was cleared by the UNIQUES reset")
        self.assertEqual("d3", fl["Angelic Halo"], "the set piece's DATE was rewritten")

    def test_the_uniques_themselves_ARE_cleared(self):
        got, why = _run()
        self.assertIsNotNone(got, why)
        fl = json.loads(got["store"]["d2r_foundLog"])
        for n in ("Shako", "Occy"):
            self.assertNotIn(n, fl, "%s was not cleared, so the reset did nothing" % n)

    def test_vault_ownership_loses_the_uniques_and_KEEPS_the_set_piece(self):
        got, why = _run()
        self.assertIsNotNone(got, why)
        own = json.loads(got["store"]["d2r_owned"])
        self.assertNotIn("Shako", own, "the unique kept its vault ownership row")
        self.assertIn("Angelic Halo", own,
                      "the reset dropped a SET PIECE from d2r_owned — out of scope")

    # ── ⚠⚠ ACT 2: WITHOUT THIS THE RESET UNDOES ITSELF ON THE NEXT BOOT ───────────────────────
    def test_every_SEED_name_is_un_ticked_so_the_boot_path_cannot_refill_it(self):
        """The boot path walks `_GRAIL_SEED` and restores any name missing from foundLog unless it
        is in `d2r_grailUnfound`. Clearing rows alone looks like success and reverts on reload."""
        got, why = _run()
        self.assertIsNotNone(got, why)
        gun = json.loads(got["store"]["d2r_grailUnfound"])
        for n in SEED:
            self.assertIn(n, gun,
                          "%r is a _GRAIL_SEED name and is NOT in d2r_grailUnfound. The next page "
                          "load will re-seed it and the chronicle will refill itself — a reset "
                          "that reverts while reporting success." % n)

    def test_every_CLEARED_name_is_un_ticked_too(self):
        """The seed sweep only covers _GRAIL_SEED names. A unique he ticked that is NOT a seed name
        has no other guard, and if the plan sweep were dropped it would simply come back as a live
        row on the next tick cycle with nothing recording that he had cleared it."""
        got, why = _run()
        self.assertIsNotNone(got, why)
        gun = json.loads(got["store"]["d2r_grailUnfound"])
        for n in got["plan"]["names"]:
            self.assertIn(n, gun,
                          "%r was cleared and never un-ticked. Only _GRAIL_SEED names are covered "
                          "by the seed sweep; this one is not, so nothing records the reset." % n)

    def test_the_plan_counts_before_it_asks(self):
        """'Are you sure?' is equally answerable whether the cost is 0 items or 292, so it tells
        him nothing. The dialog's numbers all come from here."""
        got, why = _run()
        self.assertIsNotNone(got, why)
        p = got["plan"]
        self.assertEqual(2, p["count"], "the plan miscounted the uniques it would clear")
        self.assertEqual(1, p["owned"], "the plan miscounted the vault rows")
        self.assertEqual(1, p["inGame"], "the plan miscounted what the in-game Chronicle can restore")
        self.assertEqual(3, p["sets"], "the plan misreported the sets it is NOT touching")
        self.assertEqual(2, p["runewords"], "the plan misreported the runewords it is NOT touching")

    # ── ⚠ AN UNKNOWN ROSTER REFUSES RATHER THAN GUESSING ──────────────────────────────────────
    def test_no_roster_REFUSES_instead_of_clearing_everything(self):
        """Without the roster there is no way to tell a unique from a set piece, and the failure
        mode of guessing is wiping his sets. Refusing is the only honest answer.
        [[unknown-stays-unknown]]"""
        fns = _fns()
        js = HARNESS % {"store": json.dumps(STORE), "roster": "[]",
                        "seed": json.dumps(SEED), "fns": fns}
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.cjs")
        io.open(p, "w", encoding="utf-8").write(js)
        try:
            out = subprocess.check_output(["node", p], stderr=subprocess.STDOUT, timeout=30)
            got = json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1])
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertFalse(got["plan"]["ok"], "an empty roster produced a plan anyway")
        self.assertIn("UNKNOWN", got["plan"]["why"])
        self.assertEqual(STORE["d2r_foundLog"], got["store"]["d2r_foundLog"],
                         "the store was touched despite the refusal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
