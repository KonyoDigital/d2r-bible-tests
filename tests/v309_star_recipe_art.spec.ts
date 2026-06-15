import { test, expect } from '@playwright/test';

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

test('the floating-tip name is painted in each quality\'s exact in-game colour', async ({ page }) => {
  const r = await page.evaluate(() => {
    // ensure the #arttip element exists, then read the computed .att-name colour per rarity class
    let tip = document.getElementById('arttip');
    if (!tip) { tip = document.createElement('div'); tip.id = 'arttip'; tip.innerHTML = '<img alt=""><div class="att-name"></div><div class="att-desc"></div>'; document.body.appendChild(tip); }
    const lab = tip.querySelector('.att-name') as HTMLElement;
    lab.textContent = 'X';
    const classes = ['tip-r-unique','tip-r-rare','tip-r-magic','tip-r-crafted','tip-r-basic'];
    const out: Record<string,string> = {};
    for (const c of classes) {
      tip.className = c;
      out[c] = getComputedStyle(lab).color;
    }
    return out;
  });
  expect(r['tip-r-unique']).toBe('rgb(199, 179, 119)');  // #c7b377
  expect(r['tip-r-rare']).toBe('rgb(255, 255, 100)');    // #ffff64
  expect(r['tip-r-magic']).toBe('rgb(111, 111, 255)');   // #6f6fff
  expect(r['tip-r-crafted']).toBe('rgb(255, 168, 0)');   // #ffa800
  expect(r['tip-r-basic']).toBe('rgb(207, 207, 207)');   // #cfcfcf
});
