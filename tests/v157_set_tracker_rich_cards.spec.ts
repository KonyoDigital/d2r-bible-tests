import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v157 — the Item-Set tracker cards (#set-tracker .set-card) adopt the rich gradient-header
// first-glance of the TZ/Runes cards (Konyo: "i want the bottom of the page also like this"):
// a compact emblem + gold-bright set name + N/M progress line across the card top, while the
// per-piece collect checklist body is unchanged. The header text node (.set-card-name) stays a
// PURE set name (no emblem text leaks in) so v145's titleName gateway resolver still works, and
// the per-piece data-arttip hover (v134) is untouched. ZERO fabrication — ITEM_SETS unchanged.
test.describe('v157 set-tracker cards mirror the rich gradient-header first-glance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
    await page.evaluate(() => (window as any).toggleCardCollapse && (window as any).toggleCardCollapse('set-tracker-card'));
    await page.waitForTimeout(400);
  });

  test('every set-card has the rich header (emblem + name block + progress)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#set-tracker .set-card')] as HTMLElement[];
      return {
        count: cards.length,
        withHeader: cards.filter((c) => !!c.querySelector('.set-card-header')).length,
        withEmblem: cards.filter((c) => !!c.querySelector('.set-card-header .sec-h-art.set-card-emblem')).length,
        withBlock: cards.filter((c) => !!c.querySelector('.set-card-header .set-card-title-block')).length,
        nameInBlock: cards.filter((c) => !!c.querySelector('.set-card-title-block > .set-card-name')).length,
        progressInBlock: cards.filter((c) => /\d+ \/ \d+ pieces/.test(c.querySelector('.set-card-title-block > .set-card-progress')?.textContent || '')).length,
        piecesStillThere: cards.filter((c) => !!c.querySelector('.set-pieces .set-piece')).length,
      };
    });
    expect(r.count).toBeGreaterThanOrEqual(8);
    expect(r.withHeader).toBe(r.count);
    expect(r.withEmblem).toBe(r.count);
    expect(r.withBlock).toBe(r.count);
    expect(r.nameInBlock).toBe(r.count);
    expect(r.progressInBlock).toBe(r.count);
    expect(r.piecesStillThere).toBe(r.count);  // checklist body intact under the bar
  });

  test('the name is gold-bright + the header is a gradient bar; emblem text does not leak into the name', async ({ page }) => {
    const r = await page.evaluate(() => {
      const card = document.querySelector('#set-tracker .set-card') as HTMLElement;
      const header = card.querySelector('.set-card-header') as HTMLElement;
      const name = card.querySelector('.set-card-name') as HTMLElement;
      const emblem = card.querySelector('.set-card-emblem') as HTMLElement;
      // v145 titleName: strip ↗ ✓ and trim — must equal a real set name (no emblem glyph)
      const titleName = (name.textContent || '').replace(/[↗✓]/g, '').trim();
      const isAgg = (window as any).isSetAggregate as (n: string) => boolean;
      return {
        nameColor: getComputedStyle(name).color,
        hasGradient: /gradient/.test(getComputedStyle(header).backgroundImage),
        nameResolves: typeof isAgg === 'function' ? isAgg(titleName) : true,
        emblemIsSibling: emblem.parentElement === header && !name.contains(emblem),
      };
    });
    expect(r.nameColor).toBe('rgb(0, 255, 0)');   // v321: set-card-name = --q-set (in-game green)
    expect(r.hasGradient).toBe(true);
    expect(r.nameResolves).toBe(true);               // first card is a codex-backed set → titleName clean
    expect(r.emblemIsSibling).toBe(true);            // emblem outside .set-card-name (no titleName pollution)
  });

  test('toggling a piece still re-renders + the rich header survives', async ({ page }) => {
    const r = await page.evaluate(() => {
      const checked = () => document.querySelectorAll('#set-tracker .set-piece.checked').length;
      const before = checked();
      const piece = document.querySelector('#set-tracker .set-piece') as HTMLElement;
      piece.click();
      const afterFirst = checked();
      // header still present post re-render
      const headers = document.querySelectorAll('#set-tracker .set-card .set-card-header').length;
      const cards = document.querySelectorAll('#set-tracker .set-card').length;
      // toggle back to leave state clean
      (document.querySelector('#set-tracker .set-piece') as HTMLElement).click();
      return { before, afterFirst, headers, cards };
    });
    expect(r.afterFirst).toBe(r.before + 1);
    expect(r.headers).toBe(r.cards);     // every card kept its rich header after the re-render
  });

  test('no console errors rendering the restyled set-tracker', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
    await page.evaluate(() => (window as any).toggleCardCollapse && (window as any).toggleCardCollapse('set-tracker-card'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
