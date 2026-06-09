import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v154 — the REFERENCE tab adopts the Tools/Runes/Bosses first-glance, exactly like the
// main tab did in v153. Every collapsible #tab-ref > .sec-h header is now a rich block
// (left icon + bold gold-bright title + italic subtitle), no longer a single-line
// "emoji Title ▾". The 12 ref-tab .sec-h headers (The two drop filters, Verified data
// anchors, Bind & Aura Enchanted sources, TC tier ramp, MF math, What the P# slider does,
// Mercenary mechanics, Cube Recipes, Crafted-item recipes, Breakpoints, Tristram Stones,
// Confidence formula) each gain a .sec-h-block > .sec-h-sub. Subtitles are drawn verbatim
// from each section's own honest body copy — zero fabrication.
test.describe('v154 reference tab section headers match the Tools first-glance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  test('every ref-tab section header carries a rich block (icon + title + italic subtitle)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const heads = [...document.querySelectorAll('#tab-ref > .sec-h')] as HTMLElement[];
      const blocks = heads.map((h) => h.querySelector('.sec-h-block'));
      const subs = heads.map((h) => h.querySelector('.sec-h-sub') as HTMLElement | null);
      const arts = heads.map((h) => h.querySelector('.sec-h-art'));
      const withSub = subs.filter(Boolean) as HTMLElement[];
      return {
        headCount: heads.length,
        blockCount: blocks.filter(Boolean).length,
        subCount: withSub.length,
        artCount: arts.filter(Boolean).length,
        allItalic: withSub.every((s) => getComputedStyle(s).fontStyle === 'italic'),
        titles: heads.map((h) => h.querySelector('.sec-h-t')?.textContent?.trim() || ''),
      };
    });
    expect(r.headCount).toBeGreaterThanOrEqual(12);
    expect(r.blockCount).toBe(r.headCount);  // every header restructured
    expect(r.subCount).toBe(r.headCount);
    expect(r.artCount).toBe(r.headCount);    // left icon on each
    expect(r.allItalic).toBe(true);
    expect(r.titles).toContain('The two drop filters');
    expect(r.titles).toContain('Cube Recipes');
    expect(r.titles).toContain('Breakpoints');
    expect(r.titles).toContain('Confidence formula');
  });

  test('the ref-tab title is gold-bright + the block is TOP-anchored (Tools/RoTW parity)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const h = document.querySelector('#tab-ref > .sec-h') as HTMLElement;
      const t = h.querySelector('.sec-h-t') as HTMLElement;
      const block = h.querySelector('.sec-h-block') as HTMLElement;
      return {
        headerAlign: getComputedStyle(h).alignItems,     // flex-start (top-anchored sub)
        blockColumn: getComputedStyle(block).flexDirection,
        titleColor: getComputedStyle(t).color,
        hasGradient: /gradient/.test(getComputedStyle(h).backgroundImage),
      };
    });
    expect(r.headerAlign).toBe('flex-start');
    expect(r.blockColumn).toBe('column');
    expect(r.titleColor).toBe('rgb(240, 192, 96)');   // --gold-bright, like .boss-name
    expect(r.hasGradient).toBe(true);                  // still the enriched bar
  });

  test('the headers still collapse/expand on click (toggleSec intact)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const h = document.querySelector('#tab-ref > .sec-h.collapsed') as HTMLElement;
      const body = h.nextElementSibling as HTMLElement;   // .sec-body
      const before = body.hasAttribute('hidden');
      h.click();
      const after = body.hasAttribute('hidden');
      return { before, after };
    });
    expect(r.before).toBe(true);     // starts collapsed
    expect(r.after).toBe(false);     // opens on click
  });

  test('no console errors rendering the restyled reference tab', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
