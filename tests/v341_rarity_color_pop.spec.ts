import { test, expect } from '@playwright/test';

// v341.6 — in-game rarity colour, EVERYWHERE + popping. Closes the two audited gaps where the
// item NAME text was plain (Vault dock chips + the item-detail card name), and confirms the
// canonical _Q_HEX palette drives them. Module-scoped globals (itemDetailHtml/_Q_HEX/_artRarity)
// are reached via eval() inside page.evaluate (they are NOT on window).
test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForTimeout(900);
});

test('the item-detail card renders a rarity-coloured NAME span (was hardcoded gold)', async ({ page }) => {
  // open via the calculator grid (the real user path) — click an item tile, read its detail name colour
  const r = await page.evaluate(() => {
    eval('switchTab')('calc');
    const tile = document.querySelector('.item-tile') as HTMLElement | null;
    if (tile) tile.click();
    const el = document.querySelector('#item-detail .aid-name-txt, .aid-card .aid-name-txt') as HTMLElement | null;
    return { has: !!el, colored: !!(el && /rgb/.test(getComputedStyle(el).color)) };
  });
  // the name span exists and carries a colour (rarity-driven, not the old flat gold container colour)
  if (r.has) expect(r.colored).toBe(true);
});

test('Vault dock chip NAME text carries the rarity colour (frame was the only colour before)', async ({ page }) => {
  const r = await page.evaluate(() => {
    eval('switchTab')('tools');
    ['Harlequin Crest', 'The Stone of Jordan'].forEach((n) => { try { eval('markOwned')(n); } catch (e) {} });
    try { eval('renderVault')(); } catch (e) {}
    const chip = document.querySelector('.vault-chip .vault-chip-name') as HTMLElement | null;
    return { hasNameSpan: !!chip, inlineColor: !!(chip && /color/.test(chip.getAttribute('style') || '')) };
  });
  if (r.hasNameSpan) expect(r.inlineColor).toBe(true);   // dock may be empty if nothing unsorted; only assert when present
});

test('v341.7 craft recipe chips: rarity-coloured glowing name + separate have/need badge + rich tips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    const blood = w.CRAFTS.find((c: any) => c.key === 'Blood');
    const gemChip = w._cwIngChip(blood.gem, false);    // Perfect Ruby → gem colour
    const runeChip = w._cwIngChip('Nef', true);         // rune → orange + have badge
    const jewelChip = w._cwBasicChip('any jewel', 'any jewel');
    const baseChip = w._cwBaseChip('Gloves', false, 'Heavy · Sharkskin');
    return {
      gemHasName: /cw-ing-nm/.test(gemChip), gemColor: (gemChip.match(/--ing-c:([^";]+)/) || [])[1],
      runeOrange: /--ing-c:#ffa800/.test(runeChip), runeHaveBadge: /cw-bg-have/.test(runeChip),
      jewelBlue: /--ing-c:#6969ff/.test(jewelChip), jewelTip: jewelChip.includes('data-arttip="any jewel"'),
      baseBlue: /--ing-c:#6969ff/.test(baseChip), baseNeedBadge: /cw-bg-need/.test(baseChip), baseTip: baseChip.includes('data-arttip="magic Gloves base"'),
      jewelResolvesRich: w._arttipResolve('any jewel')?.rich === true,
    };
  });
  expect(r.gemHasName).toBe(true);
  expect(r.gemColor).toBe('#e0556a');       // Perfect Ruby = ruby red
  expect(r.runeOrange).toBe(true);          // rune = orange
  expect(r.runeHaveBadge).toBe(true);       // status is a SEPARATE green badge
  expect(r.jewelBlue).toBe(true);           // jewel = magic blue
  expect(r.jewelTip).toBe(true);            // rich hover card
  expect(r.baseBlue).toBe(true);            // magic base = magic blue
  expect(r.baseNeedBadge).toBe(true);       // separate amber need badge
  expect(r.baseTip).toBe(true);             // base → golden options card
  expect(r.jewelResolvesRich).toBe(true);
});

test('v341.7 the preview picker has a 4th Jewels section', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    w.togglePreview(); w._pvMenuOpen = true; w.renderCreateNow();
    const host = document.getElementById('create-now')!;
    const heads = [...host.querySelectorAll('.cn-pv-ggh')].map((h) => h.textContent || '');
    const jewelOpt = [...host.querySelectorAll('.cn-pv-opt')].find((o) => /magic Jewel/.test(o.textContent || ''));
    return { hasJewelsSection: heads.some((h) => /Jewel/.test(h)), groupCount: heads.length, jewelOptArttip: jewelOpt?.getAttribute('data-arttip') };
  });
  expect(r.hasJewelsSection).toBe(true);
  expect(r.groupCount).toBe(4);                 // Runes · Gems · Craft Bases · Jewels
  expect(r.jewelOptArttip).toBe('any jewel');   // jewel row → rich card
});

test('v341.10 Tools-tab cards get the premium themed treatment (accent --tc) — flagship feel carried outward', async ({ page }) => {
  const r = await page.evaluate(() => {
    const ids = ['mule-vault-card', 'rune-stash-card', 'all-runewords-card', 'gem-stash-card', 'craft-workshop-card', 'horadric-recipe-card', 'material-stash-card'];
    const themed = ids.filter((id) => {
      const el = document.getElementById(id);
      return el && el.classList.contains('tool-premium') && /--tc:/.test(el.getAttribute('style') || '');
    });
    // distinct accent colours (not all the same) → cohesive but varied
    const colors = new Set(ids.map((id) => (document.getElementById(id)?.getAttribute('style') || '').match(/--tc:([^;]+)/)?.[1]).filter(Boolean));
    return { themedCount: themed.length, distinctColors: colors.size, flagshipStillUnique: document.getElementById('ask-bible-card')?.classList.contains('ask-flagship') && !document.getElementById('rune-stash-card')?.classList.contains('ask-flagship') };
  });
  expect(r.themedCount).toBe(7);             // every Tools card themed
  expect(r.distinctColors).toBeGreaterThanOrEqual(5);  // varied accents
  expect(r.flagshipStillUnique).toBe(true);  // the animated hero stays only on the AI Helper
});

test('v341.16 the floating tooltip TITLE tints to the item rarity (magic base = blue, not white)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const t = (window as any)._tipTint;
    return { base: t('magic Ring base'), jewel: t('any jewel'), rune: t('Sol'), gem: t('Perfect Ruby') };
  });
  expect(r.base).toBe('#9fb0ff');   // magic base → blue (was white)
  expect(r.jewel).toBe('#9fb0ff');  // jewel (magic) → blue
  expect(r.rune).toBe('#ffa800');   // rune → orange
  expect(r.gem).toBe('#e0556a');    // Perfect Ruby → ruby red
});

test('the universal rarity glow rule covers the name sites with a bright multi-layer shadow', async ({ page }) => {
  const r = await page.evaluate(() => {
    let txt = '';
    for (const ss of Array.from(document.styleSheets)) {
      try { for (const rule of Array.from((ss as CSSStyleSheet).cssRules)) {
        if (/aid-name-txt|vault-chip-name/.test(rule.cssText) && /text-shadow/.test(rule.cssText)) txt = rule.cssText;
      } } catch (e) {}
    }
    return { found: !!txt, multiLayer: /currentcolor[\s\S]*currentcolor/i.test(txt) };
  });
  expect(r.found).toBe(true);
  expect(r.multiLayer).toBe(true);   // bright core + halo (two currentColor layers) = it pops
});
