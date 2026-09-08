# -*- coding: utf-8 -*-
"""v2776 — HIS BOARD SHOWED 0/403 AND HE THOUGHT HIS CHRONICLE HAD BEEN DELETED.

Konyo, 2026-09-08, on his OWN console window: *"suddently my profile is missing"*, then *"all vault
items and my chronicles deleted"*. The board read `0 / 403 found`, `0 / 392 ticked`, and offered one
thing: "Claim it to make this browser your board — it imports nothing."

**NOTHING HAD BEEN DELETED.** Measured in the app's WebKit store while he was looking at the empty
screen: `d2r_owned` 169 · `d2r_foundLog` 429 · `d2r_setPieces` 125 · `d2r_rwMade` 99 — and the
server's own fleet card still read 300/403 beside it.

=== THE CAUSE ===
Ownership is decided by
    claim === '*'  ||  claim === _D2R_INSTALL  ||  automated
and `_D2R_INSTALL` MINTS A NEW ID whenever `d2r_installId` and `d2r_installIdCache` are both
missing — an eviction, a killed app, a WebKit write that never flushed. One loss and the claim stops
matching, ownership returns false, and a POPULATED board renders as an empty stranger's world.

MEASURED in his store: **three** install ids over its life (`c5c2c92d`, `77f64154`, `e07a5fe1`) and
three empty guest worlds beside his real one. It had happened at least twice before he noticed.

=== ⛔ THE PROPERTY THAT MUST SURVIVE EVERY EDIT TO THIS ===
The recovery may NEVER hand one person's ledger to another. It is safe only because a guest writes
under `I·<id8>·` and can therefore have NO bare keys: a browser holding a populated bare world is by
construction a browser that was once the owner of it. It recovers what this browser already wrote —
it never imports, inherits or seeds. `test_an_EMPTY_world_with_a_stale_claim_stays_a_GUEST` is the
law that keeps that true, and it is the one to read first if this file ever needs changing.

⚠ The decision is SLICED FROM bible.html AND EXECUTED IN NODE, not grepped. A source search would
pin a spelling; this pins the behaviour. [[source-reading-guard]]
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

# ⚠ This file prints ⚠ / ★ / ⛔ in its own failure messages. Without this, a non-UTF-8 console
# crashes while REPORTING and a clean tree exits non-zero — the gate names it by file.
try:
    from console_safe import enable
    enable()
except Exception:
    pass
BIBLE = os.path.join(ROOT, "bible.html")


def _owner_block():
    """The REAL ownership IIFE, sliced by anchor. -> str|None"""
    src = io.open(BIBLE, encoding="utf-8").read()
    a = "window._D2R_OWNER = (function(){"
    i = src.find(a)
    if i < 0:
        return None
    j = src.find("window._D2R_PFX", i)
    return src[i:j] if j > i else None


HARNESS = """
const STORE = %(store)s;
const WROTE = {};
const LS = {
  getItem: (k) => Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null,
  setItem: (k, v) => { STORE[k] = String(v); WROTE[k] = String(v); }
};
globalThis.window = globalThis;
window.localStorage = LS;
window._D2R_INSTALL = %(install)s;
/* ⚠⚠ defineProperty, NOT assignment. Node 24 ships a BUILT-IN `navigator` global as an accessor
   with no setter, so `window.navigator = {...}` is silently dropped and `navigator.webdriver` stays
   undefined — the automation branch then always reads false and the law fails on correct code. The
   first cut of this file did exactly that and I nearly went looking in bible.html.
   [[sabotage-is-usually-the-wrong-one]] — suspect the fixture first. */
Object.defineProperty(globalThis, 'navigator',
                      { value: { webdriver: %(webdriver)s }, configurable: true, writable: true });
Object.defineProperty(globalThis, 'location',
                      { value: { protocol: %(protocol)s }, configurable: true, writable: true });
%(block)s
console.log(JSON.stringify({ owner: !!window._D2R_OWNER, wrote: WROTE,
                             claimAfter: STORE['d2r_ownerClaim'] || null,
                             recovered: window.__d2rClaimRecovered || null }));
"""


def _run(store, install="e07a5fe1", webdriver="false", protocol="'http:'"):
    blk = _owner_block()
    assert blk, "could not slice the ownership block out of bible.html"
    js = HARNESS % {"store": json.dumps(store), "install": json.dumps(install),
                    "webdriver": webdriver, "protocol": protocol, "block": blk}
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "t.js")
        io.open(p, "w", encoding="utf-8").write(js)
        out = subprocess.check_output(["node", p], stderr=subprocess.STDOUT, timeout=30)
        return json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1])
    finally:
        shutil.rmtree(d, True)


POPULATED = {"d2r_owned": json.dumps(["Shako", "Occy"]),
             "d2r_foundLog": json.dumps({"Shako": 1, "Occy": 1, "Nagelring": 1})}


@unittest.skipIf(shutil.which("node") is None, "node is absent — UNMEASURED, not passing")
class APopulatedWorldSurvivesALostClaim(unittest.TestCase):

    # ── ⚠⚠ THE FAULT HE HIT ─────────────────────────────────────────────────────────────────
    def test_a_populated_world_with_a_STALE_claim_is_still_HIS(self):
        """★★ His exact state: the claim names an id this browser no longer has, and the bare keys
        are full. Before the fix this returned false and rendered 0/403 over 429 finds."""
        st = dict(POPULATED, d2r_ownerClaim="77f64154-an-id-this-browser-lost")
        r = _run(st, install="e07a5fe1")
        self.assertTrue(r["owner"],
                        "a browser holding a populated world is being told it is a stranger — this "
                        "is the state that made him believe his chronicle had been deleted")

    def test_the_recovery_re_pins_to_STAR_not_to_the_current_id(self):
        """⚠⚠ THE HALF THAT STOPS IT RECURRING. Re-pinning to `_D2R_INSTALL` would restore him
        today and break him again on the next re-mint — the same trap, re-armed. '*' is the
        documented escape hatch and is immune to id churn."""
        st = dict(POPULATED, d2r_ownerClaim="an-old-id")
        r = _run(st, install="e07a5fe1")
        self.assertEqual("*", r["claimAfter"],
                         "the recovery re-pinned the claim to something other than '*' (%r), so the "
                         "next install-id re-mint hides his board again" % r["claimAfter"])
        self.assertNotEqual("e07a5fe1", r["claimAfter"])

    def test_the_recovery_SAYS_it_happened(self):
        """⚠ A silent recovery is how nobody ever learns the id churned. [[unknown-stays-unknown]]"""
        st = dict(POPULATED, d2r_ownerClaim="an-old-id")
        r = _run(st, install="e07a5fe1")
        self.assertIsNotNone(r["recovered"], "the recovery left no trace at all")
        self.assertGreater(r["recovered"].get("entries") or 0, 0,
                           "the recovery does not record HOW MUCH world it found, so the reason it "
                           "fired cannot be checked afterwards")

    # ── ⛔ AND IT MUST NEVER LEAK A LEDGER ───────────────────────────────────────────────────
    def test_an_EMPTY_world_with_a_stale_claim_stays_a_GUEST(self):
        """⛔⛔ READ THIS ONE FIRST BEFORE CHANGING ANYTHING ABOVE. Dean's browser, or any stranger's,
        holds NO bare keys — every guest writes under `I·<id8>·`. If an empty world could recover,
        the fix would hand Konyo's board to whoever opened it."""
        r = _run({"d2r_ownerClaim": "an-old-id"}, install="e07a5fe1")
        self.assertFalse(r["owner"],
                         "an EMPTY world with a stale claim resolved as OWNER — this fix would hand "
                         "one person's ledger to another")
        self.assertIsNone(r["claimAfter"] if r["claimAfter"] != "an-old-id" else None,
                          "a stranger's claim was rewritten")

    def test_an_empty_world_is_not_rescued_by_EMPTY_containers(self):
        """⚠ THE FIXTURE THAT MATTERS. `d2r_owned: '[]'` is a container with nothing in it — the
        shape a freshly-reset board leaves behind. Counting KEYS instead of ENTRIES would make every
        reset board resolve as the owner. [[zero-needs-a-denominator]]"""
        st = {"d2r_ownerClaim": "an-old-id", "d2r_owned": "[]", "d2r_foundLog": "{}"}
        r = _run(st, install="e07a5fe1")
        self.assertFalse(r["owner"],
                         "empty containers counted as a world, so any reset board now claims "
                         "ownership of itself")

    def test_an_array_of_BLANKS_is_not_a_world(self):
        """⚠ ATTRIBUTION CORRECTED 2026-09-08 — the v2776 "cross-family review" this law used to
        credit is RETRACTED: its prompt's code fence carried an un-evaluated `open(...).read()`
        expression, so the model reviewed prose and never saw the code. The seven candidate inputs
        it named were still TESTED here by hand, and six of them already counted 0 — `[]`, `{}`,
        `0`, `null`, non-JSON and a bare number. `["",""]` counted 2, which is what a half-failed
        write leaves behind, and that measurement is what this law rests on. A world of blanks is
        not a world. The finding survives; the claim that another family found it does not.
        [[unknown-stays-unknown]] [[inherited-claim-is-not-evidence]]"""
        st = {"d2r_ownerClaim": "an-old-id",
              "d2r_owned": json.dumps(["", "  ", None]),
              "d2r_foundLog": json.dumps({"": 1, "   ": 1})}
        r = _run(st, install="e07a5fe1")
        self.assertFalse(r["owner"],
                         "an array of blank entries counted as a populated world, so a store that "
                         "holds nothing real now claims ownership of itself")

    # ── ⚠⚠ v2779 — FROM THE FIRST REVIEW THIS SESSION WHOSE PROMPT ACTUALLY CARRIED THE CODE ──
    def test_a_JSON_STRING_counts_its_CHARACTERS_and_must_not(self):
        """★★ THE ONE THAT MATTERED, and it needed a reviewer who could see the code to find it.

        `JSON.parse('"abc"')` is the STRING "abc". A string has `.length`, and a string is
        INDEXABLE — so the old guard `if (_p && _p.length != null)` took the array branch and
        walked the letters. Measured in node before the fix: **3**. Three characters, counted as
        three item names, enough on their own to recover a world out of nothing.

        `Array.isArray` is the fix. A string is not an array however much it quacks like one."""
        st = {"d2r_ownerClaim": "an-old-id", "d2r_owned": json.dumps("abc")}
        r = _run(st, install="e07a5fe1")
        self.assertFalse(r["owner"],
                         "a bare JSON string in a world key was counted by its CHARACTERS, so "
                         "'abc' recovered a three-entry world that does not exist")

    def test_elements_that_are_not_NAMES_are_not_entries(self):
        """★ The same review's second real finding. The old element test only asked "does this
        stringify to something?" — and `String(false)` is "false", `String(0)` is "0",
        `String({})` is "[object Object]". Each counted 1. None of them is an item name."""
        for label, payload in (("a zero", [0]), ("a false", [False]),
                               ("an empty object", [{}]), ("an empty array", [[]])):
            st = {"d2r_ownerClaim": "an-old-id", "d2r_owned": json.dumps(payload)}
            r = _run(st, install="e07a5fe1")
            self.assertFalse(r["owner"],
                             "%s counted as an owned item, so a store holding no names at all "
                             "claimed ownership" % label)

    def test_a_crafted___proto___key_is_not_a_world(self):
        """⚠ `JSON.parse` defines a literal "__proto__" as an OWN property, so `Object.keys` lists
        it. Without the exclusion, `{"__proto__":1}` is a one-entry world by itself."""
        st = {"d2r_ownerClaim": "an-old-id", "d2r_foundLog": json.dumps({"__proto__": 1})}
        r = _run(st, install="e07a5fe1")
        self.assertFalse(r["owner"], "a lone __proto__ key counted as a real entry")

    # ── ⛔ THE DIRECTION THAT ACTUALLY HURT HIM — A TIGHTENING MUST NOT EMPTY A REAL BOARD ────
    def test_his_REAL_STORE_SHAPES_still_recover(self):
        """⛔⛔ THE ASYMMETRY THAT DECIDES THIS WHOLE GUARD. A false POSITIVE shows an empty board
        to someone who has no world — annoying. A false NEGATIVE shows HIS POPULATED BOARD AS AN
        EMPTY STRANGER'S, which is the failure he actually reported: *"all vault items and my
        chronicles deleted"*. Every tightening above is only safe because these still count.

        The shapes are measured from his real backed-up world (list-of-str, dict of str->str) and
        reproduced here with INVENTED names — the store shape is the law, his ledger is not this
        repo's business and this repo is PUBLIC."""
        st = {"d2r_ownerClaim": "an-old-id",
              "d2r_owned": json.dumps(["Fleshrender", "Gloom's Trap"]),
              "d2r_foundLog": json.dumps({"Wormskull": "Jun 22, 2026 - 02:00"}),
              "d2r_setPieces": json.dumps(["Aldur's Advance (boots)"]),
              "d2r_rwMade": json.dumps({"Authority": "Jun 24, 2026 - 17:05"})}
        r = _run(st, install="e07a5fe1")
        self.assertTrue(r["owner"],
                        "his own store shapes no longer recover — the tightening went too far and "
                        "a populated board reads as an empty stranger's world")
        self.assertEqual((r.get("recovered") or {}).get("entries"), 5,
                         "the entry count moved; re-measure against a real world before trusting it")

    def test_an_OBJECT_element_is_still_admitted(self):
        """⚠ THE FALSE-ZERO GUARD ON THE TIGHTENING ITSELF. Requiring `typeof el === 'string'`
        alone would have read an older `[{name: ...}]` array as empty. An object element with any
        own key still counts; only `{}` does not."""
        st = {"d2r_ownerClaim": "an-old-id",
              "d2r_owned": json.dumps([{"name": "Shako", "at": 1}])}
        r = _run(st, install="e07a5fe1")
        self.assertTrue(r["owner"],
                        "an array of record OBJECTS read as empty, so an older store shape would "
                        "render his board as a stranger's")

    # ── ⚠ THE THREE PATHS THAT MUST BE UNCHANGED ────────────────────────────────────────────
    def test_star_still_wins(self):
        r = _run({"d2r_ownerClaim": "*"}, install="whatever")
        self.assertTrue(r["owner"], "the documented '*' escape hatch stopped working")

    def test_a_MATCHING_claim_still_wins_and_writes_nothing(self):
        r = _run({"d2r_ownerClaim": "e07a5fe1"}, install="e07a5fe1")
        self.assertTrue(r["owner"])
        self.assertEqual({}, r["wrote"],
                         "the happy path now writes to localStorage on every single load")

    def test_no_claim_at_all_is_unchanged(self):
        """⚠ An unclaimed browser is still decided by the automation heuristic, untouched."""
        self.assertFalse(_run({}, webdriver="false", protocol="'http:'")["owner"])
        self.assertTrue(_run({}, webdriver="true", protocol="'file:'")["owner"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
