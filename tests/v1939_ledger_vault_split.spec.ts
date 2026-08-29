import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1939 (test-only) — A FIND GOES IN THE LEDGER. THE VAULT IS WHAT HE PHYSICALLY HAS.
 *
 * Konyo, on a charm the board had muled: "i dont think i even own this.. from what picture is this
 * here? is the ledger synced like it should be to the vault manager". The honest answer is that they
 * are NOT synced and must not be — v677 split them on purpose. d2r_foundLog is "the game says you
 * found this"; d2r_owned is "this item is physically in a stash tab". A find leaking into the vault
 * is how an item he never stashed shows up as something to mule.
 *
 * THIS HAS HAPPENED LIVE. bible.html says so at _UNI_EXTRA: "without this, toggleOwned() routes a
 * find of it into the PHYSICAL VAULT (d2r_owned) instead of the found LEDGER (d2r_foundLog) — the
 * exact ledger-vs-vault split this array exists to fix, caught live by the chronicleApply auto-apply
 * landing it in the wrong store."
 *
 * AND THE FIX WAS A NAME TABLE, WHICH IS WHY THIS GUARD IS WORTH MORE THAN THE TABLE. _UNI_EXTRA
 * lists the uniques that have no tracked boss source. A NEW unique that nobody remembers to add
 * routes wrong again, silently, and the only symptom is an item appearing in his vault that he never
 * put there. Several specs cite v677 in a comment; none of them asserted the negative — that the
 * vault does not grow — so the whole split rested on a list staying complete.
 *
 * The sample is deliberately large and drawn from BOTH sources at runtime, so it covers names added
 * after this was written rather than the handful that existed on the day.
 */
test('★★★ applying chronicle finds fills the LEDGER and never the physical vault', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const r = await page.evaluate(() => {
    const w: any = window;
    const snap = () => ({
      owned: JSON.parse(localStorage.getItem('d2r_owned') || '[]') as string[],
      fl: Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')),
      sp: JSON.parse(localStorage.getItem('d2r_setPieces') || '[]') as string[],
    });
    const fl0 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
    const roster: string[] = (typeof w._gUniqueRoster === 'function') ? w._gUniqueRoster() : [];
    // both routing families: the main roster, and the mod uniques with no tracked boss source
    const fromRoster = roster.filter((n) => !fl0[n]).slice(0, 20);
    const fromExtra = Object.keys(w._UNI_EXTRA || {}).filter((n) => !fl0[n]).slice(0, 10);
    const names = [...fromRoster, ...fromExtra];

    const before = snap();
    w.chronicleApply({ wouldAdd: { uniques: names.map((n) => ({ name: n })), sets: [] } });
    const after = snap();
    return {
      names, fromRoster: fromRoster.length, fromExtra: fromExtra.length,
      ownedBefore: before.owned.length, ownedAfter: after.owned.length,
      newlyOwned: after.owned.filter((n) => !before.owned.includes(n)),
      /* v2263 — the vault write is now DELIBERATE (v1980/v1982/v1991), so what matters is no longer
         "did the vault grow" but "did anything reach the vault WITHOUT reaching the ledger". */
      /* ⚠ THE TWO STORES KEY THE SAME ITEM DIFFERENTLY, AND THAT IS NOT A GHOST.
         Measured: apply the ROSTER form `Harlequin Crest` and the ledger gets `Harlequin Crest`
         while tvVaultRegister writes its own display label, `Harlequin Crest (Shako)`, into
         d2r_owned (it returns exactly that as `label`). A verbatim join then reports the vault
         holding a name the ledger never heard of — which is what this assertion said on CI, and
         it is a KEY-FORM divergence, not an item he never stashed.
         So join on the bare form as well: a trailing parenthetical is the vault's display suffix.
         The divergence itself is real and is recorded separately — the board's own d2rResolveItem
         answers {kind:'unknown', canonical:null} for the very string the vault stores. */
      vaultedNotLedgered: after.owned
        .filter((n) => !before.owned.includes(n))
        .filter((n) => {
          const bare = n.replace(/\s*\([^)]*\)\s*$/, '');
          return !after.fl.includes(n) && !after.fl.includes(bare);
        }),
      flDelta: after.fl.length - before.fl.length,
      spDelta: after.sp.length - before.sp.length,
      missingFromLedger: names.filter((n) => !after.fl.includes(n)),
    };
  });

  /* A SAMPLE OF ZERO WOULD PASS EVERY ASSERTION BELOW. Refuse that outright — a board whose ledger
     already holds every name it knows gives this test nothing to route, and silence would read as
     a pass. [[feedback_blind_fixture_green_gate]] */
  expect(r.names.length, 'no un-found uniques to apply — this test measured nothing')
    .toBeGreaterThanOrEqual(10);
  expect(r.fromExtra, 'no _UNI_EXTRA name was exercised — the family that caused the live bug')
    .toBeGreaterThanOrEqual(1);

  /* ⚠ v2263 — THIS SPEC'S LAW WAS OVERTURNED BY DECISION ONE DAY AFTER IT WAS WRITTEN, and it has
     been red on CI ever since while reading as an unreproduced mystery locally.

     It asserted `newlyOwned === []` and `ownedAfter === ownedBefore`. v1980 — "the sweep now mules
     what it registers" — made _chronicleApplyInner call tvVaultRegister() and toggleOwned() on
     purpose; v1982 and v1991 built on that. Measured on CI: 32 names vaulted by one apply. So the
     old assertion is not catching a leak, it is reporting a feature.

     BUT THE FEAR IS STILL REAL AND IS NOT WHAT THE OLD LINES MEASURED. Read the live bug this file
     documents above: a find of a _UNI_EXTRA name went into d2r_owned *INSTEAD OF* d2r_foundLog. The
     damage was never that the vault grew — it was that the LEDGER did not, so an item he never
     stashed became something to mule and his found-truth silently lost a name. A vault write that
     is ACCOMPANIED by a ledger write is the v1980 feature; a vault write that REPLACES one is the
     v677 bug, and only the second is worth failing over.

     Measured on an owner load 2026-08-29: the seed's own 12 vaulted names each carry a real ledger
     stamp (nine of them his own game dates), so this holds today for the right reason — and planting
     one vault-only name turns it red, which is how that was established rather than assumed. */
  expect(r.vaultedNotLedgered,
    `routed into the PHYSICAL vault while MISSING from the ledger — the v677 ghost: ${JSON.stringify(r.vaultedNotLedgered)}`)
    .toEqual([]);
  expect(r.missingFromLedger, `applied but absent from the ledger: ${JSON.stringify(r.missingFromLedger)}`)
    .toEqual([]);
  expect(r.flDelta, 'the ledger did not take every applied name').toBe(r.names.length);
  expect(r.spDelta, 'a unique landed in the SET store').toBe(0);
});
