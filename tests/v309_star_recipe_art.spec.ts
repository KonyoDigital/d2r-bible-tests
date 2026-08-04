import { test, expect } from '@playwright/test';
import { boardTokens, assertTokens } from './_palette';

// v309: tooltip-style example items + ⭐ star tier (beats a named unique/runeword) +
// "How to craft" recipe section on crafted cards + every reference item gets real
// self-hosted base art (no broken-image box) + floating-tip name colour synced to
// the in-game quality (unique gold / rare yellow / magic blue / crafted orange / basic white).

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).EXTRA_ITEMS && (window as any).extraItemDetailHtml && (window as any).D2IO_ART);
});

test('the 6 new screenshot items are registered with clean bases + req levels', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E = (window as any).EXTRA_ITEMS;
    const names = ['Dire Hand (Crafted Blood Gloves)','Chromatic Amulet (+30 all res, magic)',
      "Jeweler's Dusk Shroud of Stability (4os caster armor)","Jeweler's Diadem of Speed (3os circlet)",
      'Godly Leech Ring (rare)','Superior Phase Blade (4× Shael, max-IAS base)'];
    return names.map(n => ({ n, has: !!E[n], rar: E[n] && E[n].rarity, req: E[n] && E[n].req, base: E[n] && E[n].base }));
  });
  for (const it of r) { expect(it.has, it.n).toBeTruthy(); expect(it.req, it.n).toBeGreaterThan(0); expect(it.base).not.toContain('req'); }
  expect(r.find(x => x.n.startsWith('Dire Hand'))!.rar).toBe('crafted');
});

test('every reference item resolves to a REAL local base picture (no base_*.png 404)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E = (window as any).EXTRA_ITEMS, A = (window as any).D2IO_ART;
    const out: any = { missing: [], placeholder: [], total: 0 };
    Object.keys(E).forEach(n => { out.total++; const u = A[n];
      if (!u) out.missing.push(n);
      else if (/base_/.test(u)) out.placeholder.push(n);
    });
    out.diademBody = A["Jeweler's Diadem of Speed (3os circlet)"];
    out.duskBody = A["Jeweler's Dusk Shroud of Stability (4os caster armor)"];
    return out;
  });
  // no item may point at a non-existent base_*.png placeholder
  expect(r.placeholder).toEqual([]);
  // the "Jeweler's" prefix must NOT hijack these into jewel art
  expect(r.diademBody).toContain('diadem');
  expect(r.duskBody).toContain('balrogskin');
});

test('a crafted card carries the "How to craft" recipe (rune + perfect gem + magic base)', async ({ page }) => {
  const html = await page.evaluate(() => (window as any).extraItemDetailHtml('Crafted Caster Gloves (jackpot)'));
  expect(html).toContain('How to craft');
  expect(html).toContain('Ort');               // caster-gloves rune
  expect(html).toContain('Perfect Amethyst');   // caster gem
  expect(html).toContain('a MAGIC Gloves');
  expect(html).toMatch(/always rolls/i);
  // Dire Hand = Blood gloves → Nef + Perfect Ruby
  const dh = await page.evaluate(() => (window as any).extraItemDetailHtml('Dire Hand (Crafted Blood Gloves)'));
  expect(dh).toContain('Nef');
  expect(dh).toContain('Perfect Ruby');
});

test('⭐ star tier: items that beat a named unique are flagged in card + list + tip', async ({ page }) => {
  const r = await page.evaluate(() => {
    const W: any = window;
    const card = W.extraItemDetailHtml('Crafted Caster Gloves (jackpot)');
    const tip = W._extraTipHtml('Crafted Caster Gloves (jackpot)');
    return {
      cardStar: /extra-star-card/.test(card),
      cardBanner: /BEAT Magefist \+ Frostburn/.test(card),
      tipBeats: /ELITE — beats Magefist/.test(tip),
      beatsField: W.EXTRA_ITEMS['Crafted Caster Gloves (jackpot)'].beats,
    };
  });
  expect(r.cardStar).toBeTruthy();
  expect(r.cardBanner).toBeTruthy();
  expect(r.tipBeats).toBeTruthy();
  expect(r.beatsField).toContain('Magefist');
});

test('_artRarity exposes EXTRA_ITEMS rarity so the floating tip name colour syncs in-game', async ({ page }) => {
  const r = await page.evaluate(() => {
    const f = (window as any)._artRarity;
    return {
      crafted: f('Crafted Caster Gloves (jackpot)'),
      magic: f('Chromatic Amulet (+30 all res, magic)'),
      rare: f('Godly Leech Ring (rare)'),
      basic: f('Superior Phase Blade (4× Shael, max-IAS base)'),
    };
  });
  expect(r.crafted).toBe('crafted');
  expect(r.magic).toBe('magic');
  expect(r.rare).toBe('rare');
  expect(r.basic).toBe('basic');
});

// v1632 (test-quality audit): this test used to pin five rgb() LITERALS restated from the
// stylesheet — shape 1. Two ways that was already wrong:
//   · tip-r-magic was pinned to rgb(111, 111, 255) while --q-magic is the extracted
//     FontColorBlue — one point off in every channel, i.e. latent RED ON CORRECT CODE, the
//     exact v1621 shape (a pinned literal defending a value instead of a rule).
//   · the app adds EIGHT tip-r-* classes (bible.html:23132) but only five were probed, so
//     set / rw / rune were unguarded — a wrongly wired token there was invisible.
// Now every expectation READS the live :root token the stylesheet itself names
// (#arttip.tip-r-X .att-name{color:var(--…)}, bible.html:28446-28453) and asserts the
// RELATIONSHIP. The fixture mirrors the real tip structure (img + .att-name + .att-desc);
// it is only built when the page has not rendered one yet.
test('the floating-tip name is painted from each quality\'s live token, and the qualities stay distinct', async ({ page }) => {
  const t = await boardTokens(page);
  assertTokens(t, 'unique', 'set', 'magic', 'rare', 'orange', 'normal', 'runeword', 'rune');

  const r = await page.evaluate(() => {
    let tip = document.getElementById('arttip');
    if (!tip) { tip = document.createElement('div'); tip.id = 'arttip'; tip.innerHTML = '<img alt=""><div class="att-name"></div><div class="att-desc"></div>'; document.body.appendChild(tip); }
    const lab = tip.querySelector('.att-name') as HTMLElement;
    lab.textContent = 'X';
    // the exact class list the app itself cycles through when it re-tints the tip
    const classes = ['tip-r-unique','tip-r-set','tip-r-magic','tip-r-rare','tip-r-rw','tip-r-rune','tip-r-crafted','tip-r-basic'];
    const out: Record<string,string> = {};
    for (const c of classes) { tip.className = c; out[c] = getComputedStyle(lab).color; }
    return out;
  });

  // each surface must equal the token its own CSS rule names — no literal anywhere
  expect(r['tip-r-unique'],  'tip-r-unique .att-name must be --q-unique').toBe(t.unique);
  expect(r['tip-r-set'],     'tip-r-set .att-name must be --q-set').toBe(t.set);
  expect(r['tip-r-magic'],   'tip-r-magic .att-name must be --q-magic').toBe(t.magic);
  expect(r['tip-r-rare'],    'tip-r-rare .att-name must be --q-rare').toBe(t.rare);
  expect(r['tip-r-rw'],      'tip-r-rw .att-name must be --q-runeword').toBe(t.runeword);
  expect(r['tip-r-rune'],    'tip-r-rune .att-name must be --rune (its OWN orange)').toBe(t.rune);
  expect(r['tip-r-crafted'], 'tip-r-crafted .att-name must be --q-orange').toBe(t.orange);
  expect(r['tip-r-basic'],   'tip-r-basic .att-name must be --q-normal').toBe(t.normal);

  // v1622 shape: eight green "== my own token" assertions all still pass if the palette
  // collapses. The qualities a player must tell apart at a glance must be DISTINCT colours.
  const distinct = [r['tip-r-unique'], r['tip-r-set'], r['tip-r-magic'], r['tip-r-rare'], r['tip-r-crafted'], r['tip-r-basic']];
  expect(new Set(distinct).size, 'unique/set/magic/rare/crafted/basic must be six different colours').toBe(6);
  // rune is its own orange, NOT the crafted orange (the two were conflated before v1628)
  expect(r['tip-r-rune']).not.toBe(r['tip-r-crafted']);
  // runeword is deliberately the unique gold — pin the alias so a silent divergence is caught
  expect(r['tip-r-rw'], 'a completed runeword is painted like a unique, not like a crafted item').toBe(r['tip-r-unique']);
});
