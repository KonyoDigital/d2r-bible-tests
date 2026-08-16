import { test, expect } from './_net_stub';
import * as path from 'path';

// v1735 — WHEN A SECOND WITNESS NAMES A BASE THE DB KNOWS, THE CODEX MAY NOT NAME ONE IT DOESN'T.
//
// 19 of the 62 "unresolved" codex bases were not unresolvable at all. Every one of them had a
// second witness sitting in the same file — `ITEM_TIP[item].b` — naming a base BASE_DB knows
// perfectly well. Two independent sources agreed and the codex disagreed with both.
// [[d2r-multiwitness-corroboration]]
//
// TWELVE were misspellings. Each one is a real D2 item name typed slightly wrong:
//
//     AncientArmor -> Ancient Armor        succubae skull    -> Succubus Skull
//     Light Plate Boots -> Light Plated Boots                Battle Guantlets -> Battle Gauntlets
//     Espadon -> Espandon                  CedarBow          -> Cedar Bow
//     Long Siege Bow -> Large Siege Bow    Balista           -> Ballista
//     Heirophant Trophy -> Hierophant Trophy                 Stilleto -> Stiletto
//     Jo Stalf -> Jo Staff                 Hunter\92s Bow    -> Hunter's Bow
//
// The last is not a typo but a MANGLED ESCAPE — the file held the literal characters
// `Hunter\\92s Bow`, a Windows-1252 right single quote that had been escaped into the source as
// text. It renders as a stray backslash-nine-two in the middle of a base name.
//
// SEVEN more named something Diablo II has no base for. `Girdle`, `Leather Boots` and
// `Plate Boots` are not items in this game; `Gloves` and `Bracers` are slots, not bases:
//
//     Corpsemourn  Ornate Armor  -> Ornate Plate      Bladebuckle  Girdle  -> Plated Belt
//     Hotspur      Leather Boots -> Boots             Tearhaunch   Plate Boots -> Greaves
//     Chance Guards Bracers      -> Chain Gloves      The Hand of Broc (x2) Gloves -> Leather Gloves
//
// The cost: `renderCodexCard` derives `max(BASE_DB[base].reqLvl, codex.reqLvl)` (v1731), so a base
// that does not resolve means the card shows no base requirements at all. Nineteen item cards were
// quietly missing the requirements they exist to show.
//
// EVERY OCCURRENCE HAD TO MOVE TOGETHER. The misspellings were not confined to ITEM_CODEX —
// `Stilleto` appeared 7 times, `Long Siege Bow` 4, `Heirophant Trophy` 3 — and `_TIER_CHAIN`
// carried two of them. Fixing the codex alone would have broken the chain against the codex
// instead of against BASE_DB, moving the defect rather than removing it. [[copy-drift]]
// `_TIER_CHAIN` carries a v526 note that it deliberately uses DISPLAY names so it matches
// `_baseCats`/`_baseRunewords`; the rename moves it toward that intent, not away, and all twelve
// corrected names were verified present in the built chain afterwards.
//
// This gate needs no fuzzy matching. An edit-distance first draft was written and thrown away
// because it called `Ring` a misspelling of `Kris` — 3 edits apart, and a generic slot rather than
// a typo. The second witness settles it exactly. [[feedback-suspect-the-instrument]]

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1735 — the codex agrees with its second witness about the base', () => {
  test('★★★ no codex base fails to resolve while ITEM_TIP names one that does', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      const bad: string[] = [];
      let checked = 0;
      for (const [name, e] of Object.entries<any>(ITEM_CODEX)) {
        const tip = (typeof ITEM_TIP !== 'undefined' && (ITEM_TIP as any)[name])
          ? (ITEM_TIP as any)[name].b : null;
        if (!e.base || !tip) continue;
        checked++;
        if (!(BASE_DB as any)[e.base] && (BASE_DB as any)[tip]) {
          bad.push(`${name}: codex "${e.base}" but ITEM_TIP says "${tip}", which BASE_DB knows`);
        }
      }
      return { checked, bad: bad.slice(0, 8), badN: bad.length };
    });
    // non-vacuity: both literals must actually have been read and compared
    expect(r.checked, 'no item had both a codex base and an ITEM_TIP base — nothing was compared')
      .toBeGreaterThan(200);
    expect(r.bad, `${r.badN} codex bases contradicted by their own second witness: ` +
      r.bad.join(' | ')).toEqual([]);
  });

  test('★★★ no base name in the file carries the mangled Windows-1252 escape', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      // the literal characters backslash-9-2, which is how a CP1252 right single quote got
      // escaped into the source. It survives as visible garbage inside a base name.
      const hits: string[] = [];
      for (const [name, e] of Object.entries<any>(ITEM_CODEX)) {
        if (e.base && /\\9[0-9]/.test(String(e.base))) hits.push(`${name}: ${e.base}`);
      }
      for (const [name, v] of Object.entries<any>(typeof ITEM_TIP !== 'undefined' ? ITEM_TIP : {})) {
        if (v && v.b && /\\9[0-9]/.test(String(v.b))) hits.push(`ITEM_TIP ${name}: ${v.b}`);
      }
      return { hits, codexN: Object.keys(ITEM_CODEX).length };
    });
    expect(r.codexN, 'the codex was empty — nothing was scanned').toBeGreaterThan(100);
    expect(r.hits, 'base names holding a mangled escape: ' + r.hits.join(', ')).toEqual([]);
  });

  test('★★ the corrected names really are in the built tier chain', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      if (typeof _TIER_CHAIN === 'undefined' || !_TIER_CHAIN) return { missing: ['_TIER_CHAIN absent'], flatLen: 0 };
      const flat = JSON.stringify(_TIER_CHAIN);
      const names = ['Stiletto', 'Ballista', 'Espandon', 'Cedar Bow', 'Large Siege Bow', 'Jo Staff',
                     'Hierophant Trophy', 'Succubus Skull', 'Battle Gauntlets', 'Light Plated Boots',
                     'Ancient Armor', "Hunter's Bow"];
      return { missing: names.filter((n) => !flat.includes(`"${n}"`)), flatLen: flat.length };
    });
    expect(r.flatLen, '_TIER_CHAIN serialised to nothing — the check would pass vacuously')
      .toBeGreaterThan(500);
    expect(r.missing, 'renamed bases absent from the tier chain: ' + r.missing.join(', ')).toEqual([]);
  });
});
