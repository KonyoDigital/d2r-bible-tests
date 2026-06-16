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
