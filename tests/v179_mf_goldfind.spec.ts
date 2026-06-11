import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v179 — Bridge B6 (cross-check completeness sweep). The sweep CONFIRMED runewords
// (v140 100-entry DB), cube recipes (v141/v142 tool), the MF diminishing-returns
// curve (factors 250/500/600), sunder charms (5 by type) and immunities (RotW sunder
// path, Conviction-removed) are all already complete & RotW-accurate. The one genuine
// thin spot the gapmap flagged was Gold Find / "what MF does NOT touch" — absent from
// the MF-math section. This ship adds two honesty boxes (#mf-not-touch) inside the
// existing MF-math sec-body: MF only changes the quality roll (nothing for runes/gems/
// gold/gambling/crafting/quest), and Gold Find is a separate stat. Categorical
// mechanics — zero fabricated numbers, additive only.

test.describe('v179 MF "does NOT touch" + Gold Find (Bridge B6)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(700);
  });

  test('the #mf-not-touch box exists inside the MF-math section', async ({ page }) => {
    const r = await page.evaluate(() => {
      const box = document.getElementById('mf-not-touch');
      // walk up to the enclosing sec-body, then its sec-h title
      let node: HTMLElement | null = box;
      let body: HTMLElement | null = null;
      while (node) { if (node.classList && node.classList.contains('sec-body')) { body = node; break; } node = node.parentElement; }
      const head = body ? (body.previousElementSibling as HTMLElement) : null;
      const title = head ? (head.querySelector('.sec-h-t')?.textContent || '').trim() : '';
      return { has: !!box, inSecBody: !!body, title };
    });
    expect(r.has).toBe(true);
    expect(r.inSecBody).toBe(true);
    expect(r.title).toBe('MF math');
  });

  test('the verified "MF does not affect" categories are listed', async ({ page }) => {
    const txt = await page.evaluate(() => (document.getElementById('mf-not-touch')?.textContent || '').replace(/\s+/g, ' '));
    for (const cat of ['runes', 'gems', 'jewels', 'charms', 'gold', 'gambling', 'crafting']) {
      expect(txt, `${cat} mentioned`).toMatch(new RegExp(cat, 'i'));
    }
    // the curve fact: most effective for uniques, weakest for rares
    expect(txt).toMatch(/most effective for uniques/i);
    expect(txt).toMatch(/Ist/);  // the concrete rune example
  });

  test('the Gold Find clarification is present and distinct from MF', async ({ page }) => {
    const txt = await page.evaluate(() => {
      const box = document.getElementById('mf-not-touch');
      const next = box ? (box.nextElementSibling as HTMLElement) : null;
      return (next?.textContent || '').replace(/\s+/g, ' ');
    });
    expect(txt).toMatch(/Gold Find/i);
    expect(txt).toMatch(/separate/i);
    expect(txt).toMatch(/gold piles/i);
    expect(txt).toMatch(/zero.*effect on item drops/i);
  });

  test('no console errors opening the MF-math section', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      let node = document.getElementById('mf-not-touch') as HTMLElement | null;
      let body: HTMLElement | null = null;
      while (node) { if (node.classList && node.classList.contains('sec-body')) { body = node; break; } node = node.parentElement; }
      const head = body ? (body.previousElementSibling as HTMLElement) : null;
      head && head.click();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
