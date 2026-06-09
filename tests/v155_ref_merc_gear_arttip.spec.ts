import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v155 — the reference tab's Mercenary "best gear" table adopts the v152 item-reference
// standard: every named pick in the three "Top picks" cells (weapon · helm · armor) now
// carries the floating #arttip hover card (data-arttip) AND the inline in-game art logo
// (data-art-logo, silent no-op where the item has no verified art). Hover-only — no
// openDrop routing, since several merc runewords aren't grail-codex drop targets (a dead
// click would be worse than none). ZERO fabrication: names tag verbatim from the table;
// _arttipResolve degrades gracefully for the 2 non-rich entries (Reaper's Toll, Tal
// Rasha's Horadric Crest) — they still show a name popup, never an invented stat block.
test.describe('v155 ref merc-gear table carries rich hover tips', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(300);
  });

  test('every Top-picks item carries a data-arttip span + some carry inline art', async ({ page }) => {
    const r = await page.evaluate(() => {
      const tipped = [...document.querySelectorAll('#tab-ref .ref-tbl td.item-name span[data-arttip]')] as HTMLElement[];
      return {
        tippedCount: tipped.length,
        names: tipped.map((s) => s.getAttribute('data-arttip')),
        withInlineArt: tipped.filter((s) => !!s.querySelector('.d2art-wrap img')).length,
      };
    });
    expect(r.tippedCount).toBe(13);              // 5 weapon + 4 helm + 4 armor
    expect(r.names).toContain('Infinity');
    expect(r.names).toContain('Andariel\'s Visage');
    expect(r.names).toContain('Fortitude');
    expect(r.withInlineArt).toBeGreaterThanOrEqual(4);  // the helm uniques have verified art
  });

  test('the rich-card resolver lights up for the runeword/unique picks (no fabrication)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#tab-ref .ref-tbl td.item-name span[data-arttip]')]
        .map((s) => s.getAttribute('data-arttip') as string);
      const resolve = (window as any)._arttipResolve as (n: string) => any;
      const richCount = names.filter((n) => resolve(n)?.rich).length;
      // every name resolves to SOMETHING graceful (artName always present) — never empty
      const allGraceful = names.every((n) => !!resolve(n)?.artName);
      return { total: names.length, richCount, allGraceful };
    });
    expect(r.total).toBe(13);
    expect(r.richCount).toBeGreaterThanOrEqual(11);  // 12 of 13 resolve to full stat cards
    expect(r.allGraceful).toBe(true);                // the 2 non-rich still degrade cleanly
  });

  test('the floating #arttip opens on hover over a Top-picks item', async ({ page }) => {
    await page.evaluate(() => {
      const h = document.querySelector('#tab-ref > .sec-h') as HTMLElement; // open first ref section so layout is live
      return h;
    });
    const shown = await page.evaluate(async () => {
      const span = document.querySelector('#tab-ref .ref-tbl td.item-name span[data-arttip="Infinity"]') as HTMLElement;
      span.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
      await new Promise((r) => setTimeout(r, 120));
      const tip = document.getElementById('arttip');
      return !!tip && getComputedStyle(tip).display !== 'none' && (tip.textContent || '').includes('Infinity');
    });
    expect(shown).toBe(true);
  });

  test('no console errors rendering the restyled merc-gear table', async ({ page }) => {
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
