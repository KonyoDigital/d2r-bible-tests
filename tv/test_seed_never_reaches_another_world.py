# -*- coding: utf-8 -*-
"""v2740 — WHOSE FINDS A CONSOLE MAY INHERIT, PINNED IN ALL THREE STATES.

Konyo: *"as long as it doesnt seed my profile again .. it can base its own console and evidence and
logic can automatically end up there based on his own ledger you feel me? but not mine .. all his
own individual consoles data based on the unified logic and architecture already built"*.

The hardcoded `_GRAIL_SEED` is 245 of HIS finds. Whether it lands on a given browser is decided by
one expression:

    bible.html:4008   window._seedsBelongHere = (!window._isCousinShell
                                                 && window._D2R_LEDGER === window._SEED_LEDGER);
    bible.html:3941   window._isCousinShell   = !window._D2R_OWNER;

THREE STATES, and until this file there was no test asserting ANY of them — the whole property
rested on two `window.X =` lines and a comment:

  1. GUEST (unclaimed)         -> refused, whatever the ledger resolves to
  2. CLAIMED **and NAMED**     -> refused, because the resolver's first branch is `if (n) return n`
  3. CLAIMED **and UNNAMED**   -> ACCEPTED: :3990's has-a-chronicle heuristic answers 'KonyoEndgame'

State 3 is the only way in. bible.html:10245 already names it: "a claimed stranger holding Konyo's
245 finds, with the floors free to re-seed him forever." It survives for boards claimed before
v2692, because the naming rule is "write a name ONLY when none is set" — an exemption that exists
to protect HIS own unnamed-with-data board from being renamed out of its own chronicle.

=== ⚠⚠ AND THE RESET DID NOT CLOSE IT, WHICH WAS THE UNMEASURED PART ===
Simulated with the REAL resolver sliced from source, on a claimed+unnamed board:

    BEFORE reset   ledger='KonyoEndgame'      seedsBelongHere=True    foundLog=3  grailUnfound=0
    AFTER  reset   ledger='KonyoEndgame'      seedsBelongHere=True    foundLog=1  grailUnfound=2

The un-tick registry saved the names that existed. It could not save a name added to `_GRAIL_SEED`
LATER, because a registry written today cannot contain one. And the surviving SET-PIECE row was
enough to keep the has-a-chronicle heuristic answering 'KonyoEndgame'.
v2740 makes the reset name the ledger when the board is genuinely seedable and unnamed:

    AFTER  reset   ledger='Ledger-deadbeef'   seedsBelongHere=False   foundLog=1  grailUnfound=2

⚠ THIS RUNS THE REAL JAVASCRIPT — resolver, belonging rule and reset are sliced out of bible.html
by anchor and executed in node. A source grep would pin a spelling; this pins the decision.
⚠ NO NODE = SKIP WITH A REASON, NEVER A PASS.
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


def _slice(src, a, b, inclusive=False):
    i = src.find(a)
    if i < 0:
        return None
    j = src.find(b, i + len(a))
    if j < 0:
        return None
    return src[i:j + (len(b) if inclusive else 0)]


def _regions():
    src = io.open(BIBLE, encoding="utf-8").read()
    out = {
        "resolver": _slice(src, "window._SEED_LEDGER = 'KonyoEndgame';", "})();", inclusive=True),
        "belong": _slice(src, "window._seedsBelongHere =", "\n"),
        "reset": _slice(src, "window._uniqueResetPlan = function()",
                        "window._uniqueResetAsk = async function()"),
    }
    return None if any(v is None for v in out.values()) else out


HARNESS = """
const STORE = %(store)s;
const LS = { getItem:(k)=>Object.prototype.hasOwnProperty.call(STORE,k)?STORE[k]:null,
             setItem:(k,v)=>{STORE[k]=String(v);} };
globalThis.window = globalThis;
window.localStorage = LS; window.LSR = LS;
window._D2R_OWNER = %(owner)s;
window._isCousinShell = !window._D2R_OWNER;
window._D2R_INSTALL = 'deadbeefcafe';
window.navigator = { webdriver:false };
window.location = { protocol:'http:' };
window._gUniqueRoster = () => %(roster)s;
window._regKey = (x)=>String(x||'').toLowerCase().replace(/[^a-z0-9]/g,'');
window._GRAIL_SEED = %(seed)s;
%(reset)s
function decide(){
  %(resolver)s
  %(belong)s
  return { ledger: window._D2R_LEDGER, belong: window._seedsBelongHere };
}
const before = decide();
let after = null;
if (%(do_reset)s) { const p = window._uniqueResetPlan(); if (p.ok) window._uniqueResetDo(p); after = decide(); }
console.log(JSON.stringify({before: before, after: after, store: STORE}));
"""

ROSTER = ["Shako", "Occy", "Stone of Jordan"]
#: ⚠⚠ SHAPED SO EACH SWEEP HAS A VICTIM ONLY IT CAN SAVE. The first fixture had every seed name
#: also present in foundLog, so the plan sweep covered for the seed sweep's removal and the
#: "drop the seed sweep" sabotage passed 8/8. "Stone of Jordan" is a seed name with NO row, so only
#: the seed sweep can un-tick it. [[sabotage-is-usually-the-wrong-one]]
SEED = {"Shako": "d", "Stone of Jordan": "d"}


def _store(**over):
    s = {"d2r_foundLog": json.dumps({"Shako": "d1", "Occy": "d2", "Angelic Halo": "d3"}),
         "d2r_owned": json.dumps(["Shako"]),
         "d2r_setPieces": json.dumps(["Angelic Halo"]),
         "d2r_rwMade": "{}", "d2r_gameFound": "{}", "d2r_grailUnfound": "{}"}
    s.update(over)
    return s


def _run(owner, store, do_reset=False):
    r = _regions()
    if r is None:
        return None, "the resolver / belonging rule / reset could not be sliced from bible.html"
    js = HARNESS % {"store": json.dumps(store, ensure_ascii=False),
                    "owner": "true" if owner else "false",
                    "roster": json.dumps(ROSTER), "seed": json.dumps(SEED),
                    "reset": r["reset"], "resolver": r["resolver"], "belong": r["belong"],
                    "do_reset": "true" if do_reset else "false"}
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
class TheSeedNeverReachesAnotherWorld(unittest.TestCase):

    def test_the_regions_can_be_sliced_AT_ALL(self):
        """⚠ A gate that cannot find its subject passes having examined nothing."""
        r = _regions()
        self.assertIsNotNone(r, "bible.html no longer yields the resolver / belonging rule / reset")
        self.assertIn("_seedsBelongHere", r["belong"])
        self.assertIn("KonyoEndgame", r["resolver"])

    # ── STATE 1 — a guest is refused whatever the ledger says ─────────────────────────────────
    def test_a_GUEST_never_receives_the_seed(self):
        got, why = _run(False, _store())
        self.assertIsNotNone(got, why)
        self.assertFalse(got["before"]["belong"],
                         "an UNCLAIMED browser was offered the owner's 245 seeded finds. A guest "
                         "world must build its own chronicle from its own ledger.")

    # ── STATE 2 — a named board is refused ────────────────────────────────────────────────────
    def test_a_CLAIMED_but_NAMED_board_never_receives_the_seed(self):
        got, why = _run(True, _store(d2r_ledgerName="Ledger-abc12345"))
        self.assertIsNotNone(got, why)
        self.assertEqual("Ledger-abc12345", got["before"]["ledger"],
                         "the resolver ignored an explicit ledger name — its FIRST branch is "
                         "`if (n) return n`, and everything here rests on that")
        self.assertFalse(got["before"]["belong"],
                         "a board with a ledger of its own was offered the owner's seed")

    # ── STATE 3 — the only way in, and the reset must close it ────────────────────────────────
    def test_a_CLAIMED_and_UNNAMED_board_IS_seedable_before_the_reset(self):
        """⚠ Asserting the DEFECT exists, so the law below cannot pass vacuously. If this ever goes
        false the hazard is gone and the next law is measuring nothing. [[feedback-blind-fixture-green-gate]]"""
        got, why = _run(True, _store())
        self.assertIsNotNone(got, why)
        self.assertEqual("KonyoEndgame", got["before"]["ledger"])
        self.assertTrue(got["before"]["belong"],
                        "state 3 no longer reproduces — re-derive this file's premise before "
                        "trusting the law below")

    def test_the_RESET_shuts_the_seed_door_for_good(self):
        """⚠⚠ THE ONE HE ASKED FOR. Before v2740 the reset left ledger='KonyoEndgame' and
        seedsBelongHere=true: the un-tick registry saved the names that existed and could not save
        a name added to _GRAIL_SEED later."""
        got, why = _run(True, _store(), do_reset=True)
        self.assertIsNotNone(got, why)
        self.assertTrue(got["before"]["belong"], "the fixture did not start in the seedable state")
        self.assertFalse(got["after"]["belong"],
                         "after the reset this board can STILL receive the owner's seed. The "
                         "un-tick registry only covers names that exist today; a name added to "
                         "_GRAIL_SEED later would land on his console as that person's progress.")
        self.assertTrue(str(got["after"]["ledger"]).startswith("Ledger-"),
                        "the reset did not give the board a ledger of its own, which is the only "
                        "thing that closes the door permanently")

    # ── ⚠ AND IT MUST NOT RENAME A BOARD THAT ALREADY NAMED ITSELF ────────────────────────────
    def test_the_reset_NEVER_renames_a_board_that_has_its_own_ledger(self):
        """Renaming someone out of their own chronicle is the v2680 damage v2685 had to revert.

        ⚠⚠ THE FIXTURE HAS TO BE **HIS OWN BOARD**, AND THE FIRST ONE WAS NOT.
        It used `Deans-Own-Ledger`, which makes `_seedsBelongHere` FALSE — so the guarded branch was
        never entered and an "overwrite even when named" sabotage passed 8/8. The only board that is
        BOTH seedable AND named is the one explicitly named `KonyoEndgame`: Konyo's own. That is
        also the board where an overwrite would do the real damage, so it is the only fixture that
        tests anything here. [[sabotage-is-usually-the-wrong-one]]
        """
        got, why = _run(True, _store(d2r_ledgerName="KonyoEndgame"), do_reset=True)
        self.assertIsNotNone(got, why)
        self.assertTrue(got["before"]["belong"],
                        "the fixture is not seedable, so the rename guard is never reached and "
                        "this law would pass without testing it")
        self.assertEqual("KonyoEndgame", got["store"].get("d2r_ledgerName"),
                         "the reset renamed HIS OWN board out of its own ledger — the v2680 damage")

    def test_a_DIFFERENT_named_board_is_also_left_alone(self):
        got, why = _run(True, _store(d2r_ledgerName="Deans-Own-Ledger"), do_reset=True)
        self.assertIsNotNone(got, why)
        self.assertEqual("Deans-Own-Ledger", got["store"].get("d2r_ledgerName"))

    def test_the_reset_does_NOT_write_an_identity_on_a_board_that_is_already_safe(self):
        """A guest is already refused the seed, so stamping an identity there would be a change
        with no defect behind it — and an identity write nobody needed."""
        got, why = _run(False, _store(), do_reset=True)
        self.assertIsNotNone(got, why)
        self.assertIsNone(got["store"].get("d2r_ledgerName"),
                          "the reset named a GUEST board, which was never seedable to begin with")

    # ── the un-tick registry is the second, independent guard ─────────────────────────────────
    def test_the_untick_registry_still_covers_every_seed_name(self):
        """Belt and braces: even a board that stayed seedable must not have these names refilled."""
        got, why = _run(True, _store(), do_reset=True)
        self.assertIsNotNone(got, why)
        gun = json.loads(got["store"]["d2r_grailUnfound"])
        for n in SEED:
            self.assertIn(n, gun, "%r is a seed name and is not un-ticked" % n)


if __name__ == "__main__":
    unittest.main(verbosity=2)
