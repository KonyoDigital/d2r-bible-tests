import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v293 — Item Rarity & Colours explainer in the Tools tab (#item-rarity-card): a colour-coded
// tile per rarity (Normal/Socketed-Ethereal/Magic/Rare/Crafted/Set/Unique) with mod counts and a
// crafting tie-in. Static reference card; sits just above the Crafted Items Workshop.
// v292 — the Horadric "Reroll / renew affixes" recipes (rare reroll 6 Perfect Skulls + magic reroll).

test.describe('v293 item rarity explainer + v292 renew recipes', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
    await page.evaluate(() => {
      const c = document.getElementById('item-rarity-card');
      if (c && c.classList.contains('collapsed')) (window as any).toggleCardCollapse('item-rarity-card');
    });
  });

  test('the rarity card shows all 7 colour tiles with names + mod counts', async ({ page }) => {
    const tiles = page.locator('#item-rarity-card .ir-tile');
    expect(await tiles.count()).toBe(7);
    const names = (await page.locator('#item-rarity-card .ir-name').allTextContents()).join(' | ');
    for (const r of ['Normal', 'Socketed', 'Magic', 'Rare', 'Crafted', 'Set', 'Unique']) {
      expect(names).toContain(r);
    }
    // mod-count badges present (e.g. "1–2 mods", "3–6 mods", "3 fixed + 1–4 random")
    const mods = (await page.locator('#item-rarity-card .ir-mods').allTextContents()).join(' ');
    expect(mods).toMatch(/1[–-]2 mods/);
    expect(mods).toMatch(/3[–-]6 mods/);
    // each tile is colour-driven via the --ir custom property
    const hasColor = await page.locator('#item-rarity-card .ir-tile').first().evaluate(el => /(?:--ir:)/.test(el.getAttribute('style') || ''));
    expect(hasColor).toBe(true);
    // the Unique tile name-drops the Stone of Jordan example (verbatim from the content)
    expect(await page.locator('#item-rarity-card').textContent()).toContain('Stone of Jordan');
  });

  test('the renew-affixes Horadric recipes exist (rare reroll = 6 Perfect Skulls, magic reroll = 3 Perfect Gems)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const H = (window as any).HORADRIC_RECIPES || [];
      const renew = H.filter((x: any) => /renew affixes/i.test(x.c));
      return {
        count: renew.length,
        hasRareReroll: renew.some((x: any) => /6.\s*Perfect Skull/i.test(x.in) && /Rare item/i.test(x.in)),
        hasMagicReroll: renew.some((x: any) => /3.\s*Perfect Gem/i.test(x.in) && /Magic item/i.test(x.in)),
        // no duplicate Stone-of-Jordan socket recipe left in the Sockets category
        sojInSockets: H.filter((x: any) => /Stone of Jordan/i.test(x.in)).map((x: any) => x.c),
      };
    });
    expect(r.count).toBeGreaterThanOrEqual(2);
    expect(r.hasRareReroll).toBe(true);
    expect(r.hasMagicReroll).toBe(true);
    // the SoJ recipe lives once, in the renew group (not duplicated under Sockets)
    expect(r.sojInSockets.length).toBe(1);
    expect(r.sojInSockets[0]).toMatch(/renew affixes/i);
  });

  test('the rare-reroll recipe lights up "cubeable" off the gem stash (6 Perfect Skulls)', async ({ page }) => {
    const ready = await page.evaluate(() => {
      const w = window as any;
      // hold 6 Perfect Skulls → the rare reroll should be cubeable
      for (let i = 0; i < 6; i++) w.adjustGemStash('Perfect Skull', 1);
      const H = w.HORADRIC_RECIPES.find((x: any) => /6.\s*Perfect Skull/i.test(x.in) && /Rare item/i.test(x.in));
      // _recReady is module-scoped; instead read the rendered status chip after re-render
      w.renderHoradricRecipes();
      const rows = Array.from(document.querySelectorAll('#horadric-list .hcr-row')) as HTMLElement[];
      const row = rows.find(el => /Perfect Skull/i.test(el.textContent || '') && /Rare item/i.test(el.textContent || ''));
      const cubeable = !!row && /cubeable/i.test(row.textContent || '');
      for (let i = 0; i < 6; i++) w.adjustGemStash('Perfect Skull', -1);
      return cubeable;
    });
    expect(ready).toBe(true);
  });
});
