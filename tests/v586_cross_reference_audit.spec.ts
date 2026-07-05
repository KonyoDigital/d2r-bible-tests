import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v586 — CROSS-REFERENCE AUDIT locks (2026-07-06). Full sweep of diablo2.io (415 uniques),
// classic.battle.net (380 uniques, 32 sets, 75 runewords, 33 runes) and theamazonbasin.com
// RotW wiki (100 runewords, 33 runes, RotW uniques) against the platform. Everything agreed
// except the fixes locked here. RotW mod deltas (Bane's/Horazon's sets, Warlock items,
// Latent/Renewed sunders) are intentional and were NOT "fixed".

test.beforeEach(async ({ page }) => { await page.goto(URL); await page.waitForTimeout(1600); });

test('base-item corrections: Viperfork=Mancatcher, HoZ=Gilded Shield, Iron Pelt=Trellised', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E: any = (window as any).EXTRA_ITEMS || (typeof EXTRA_ITEMS !== 'undefined' ? EXTRA_ITEMS : {});
    return {
      viper: E['Viperfork'].base,
      hoz: E['Herald of Zakarum'].base,
      iron: E['Iron Pelt'].base,
      typoGone: !JSON.stringify(Object.values(E).map((x: any) => x.base)).includes('Tresllised'),
    };
  });
  expect(r.viper).toBe('Mancatcher');       // was "war fork" (exceptional tier — req 71 = elite Mancatcher)
  expect(r.hoz).toBe('Gilded Shield');      // was "Aerin Shield" (its normal-tier cousin)
  expect(r.iron).toBe('Trellised Armor');   // was the "Tresllised" typo
  expect(r.typoGone).toBe(true);
});

test('rune armor/shield mods: Sur & Jah unswapped, Dol & Um canonical wording', async ({ page }) => {
  const r = await page.evaluate(() => {
    const rs: any[] = (typeof RUNES !== 'undefined') ? (RUNES as any) : [];
    const by: any = {}; rs.forEach((x: any) => { by[x.n] = x; });
    return { sur: by['Sur'], jah: by['Jah'], dol: by['Dol'], um: by['Um'] };
  });
  // vanilla + RotW truth: armor = % max, SHIELD = flat +50 (they were merged/swapped)
  expect(r.sur.a).toBe('+5% Maximum Mana');
  expect(r.sur.s).toBe('+50 Mana');
  expect(r.jah.a).toBe('+5% Maximum Life');
  expect(r.jah.s).toBe('+50 Life');
  // Replenish Life is a flat stat, All Res carries no % on the +N
  expect(r.dol.a).toBe('Replenish Life +7');
  expect(r.um.a).toBe('All Resistances +15');
  expect(r.um.s).toBe('All Resistances +22');
});

test('RotW Warlock uniques carry their full Amazon Basin stat blocks', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E: any = (typeof EXTRA_ITEMS !== 'undefined') ? EXTRA_ITEMS : {};
    const s = (n: string) => (E[n] && E[n].stats) || [];
    return {
      arsTor: s("Ars Tor'Baalos").length, arsAl: s("Ars Al'Diabolos"),
      dreadfang: s('Dreadfang').join('|'), bloodpact: s('Bloodpact Shard').join('|'),
      measured: s('Measured Wrath').join('|'), sling: s('Sling').join('|'),
    };
  });
  expect(r.arsTor).toBeGreaterThanOrEqual(9);                       // was 1 line
  expect(r.arsAl.join('|')).toContain('Apocalypse (Warlock only)'); // class mods present
  expect(r.dreadfang).toContain('Mirrored Blades');
  expect(r.bloodpact).toContain('Bind Demon');
  expect(r.measured).toContain('Summon Tainted');
  expect(r.sling).toContain('Town Portal (oskill)');
});

test('the 6 RotW Colossal Jewels exist, render cards, and never rot in a throw-out pile', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    const E: any = (typeof EXTRA_ITEMS !== 'undefined') ? EXTRA_ITEMS : {};
    const names = ["Defender's Bile", "Defender's Fire", "Guardian's Light",
                   "Guardian's Thunder", "Protector's Frost", "Protector's Stone"];
    return names.map((n) => ({
      n, present: !!E[n], base: E[n] && E[n].base,
      stats: E[n] ? E[n].stats.length : 0,
      card: w.extraItemDetailHtml ? String(w.extraItemDetailHtml(n)).length > 200 : true,
      route: (w.suggestMule(n) || {}).id,
    }));
  });
  for (const e of r) {
    expect(e.present, e.n).toBe(true);
    expect(e.base).toBe('Colossal Jewel');
    expect(e.stats).toBeGreaterThanOrEqual(7);
    expect(e.card, e.n + ' renders a card').toBe(true);
    expect(e.route, e.n + ' routes as a keeper, not junk').not.toBe('__throwout');
  }
});

test('audit invariants that came back CLEAN stay locked: 100 runewords, 34 sets, sunder tips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      rwCount: Object.keys(w.RUNEWORD_TIP || {}).length,
      setCount: (w.__allSets ? w.__allSets() : []).length,
      sunder: Object.keys((typeof SUNDER_TIP !== 'undefined') ? SUNDER_TIP : {}).length,
      // spot-lock two rune recipes the AB sweep verified (all 100 matched)
      enigma: (w.RUNEWORD_TIP['Enigma'] || {}).rec,
      botd: (w.RUNEWORD_TIP['Breath of the Dying'] || {}).rec,
    };
  });
  expect(r.rwCount).toBe(100);
  expect(r.setCount).toBe(34);                 // 32 vanilla (piece-perfect vs battle.net) + Bane's + Horazon's (RotW)
  expect(r.sunder).toBeGreaterThanOrEqual(12); // Latent+Renewed ×6 — matches the AB wiki sunder data
  expect(r.enigma).toEqual(['Jah', 'Ith', 'Ber']);
  expect(r.botd).toEqual(['Vex', 'Hel', 'El', 'Eld', 'Zod', 'Eth']);
});
