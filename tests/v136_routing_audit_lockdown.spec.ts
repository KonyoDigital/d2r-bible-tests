import { test, expect } from './_net_stub'; // diablo2.io art stubbed — kills net-flake (audit 2026-06-12)
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v136 — routing-integrity AUDIT + bulletproof lockdown. A "renew black cleft"
// search was landing on the Bone-Break-led recipe grid because the per-charm
// recipe commands all called the generic openSunderRecipes() with no charm.
// These tests LOCK IN that EVERY sunder charm routes to ITS OWN row/card — both
// the recipe tool and the material card — so a sibling-misroute can never
// silently regress (no shipping a 90% system).
const CHARMS = ['Cold Rupture','Flame Rift','Crack of the Heavens','Rotting Fissure','Bone Break','Black Cleft'];

test.describe('v136 routing audit + lockdown', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('openSunderRecipes(charm) expands EXACTLY that charm row — all 6, no sibling', async ({ page }) => {
    for (const charm of CHARMS) {
      const open = await page.evaluate((c) => {
        (window as any).openSunderRecipes(c);
        return [...document.querySelectorAll('#sunder-recipe-grid details.sun-recipe[open]')]
          .map((d) => d.getAttribute('data-charm'));
      }, charm);
      expect(open).toEqual([charm]);
    }
  });

  test('openSunderRecipes() with NO charm opens the card without force-expanding any row', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openSunderRecipes();
      const card = document.getElementById('sunder-recipe-card');
      return {
        toolsActive: document.getElementById('tab-tools')?.classList.contains('active'),
        cardOpen: card ? !card.classList.contains('collapsed') : false,
        openRows: document.querySelectorAll('#sunder-recipe-grid details.sun-recipe[open]').length,
      };
    });
    expect(r.toolsActive).toBe(true);
    expect(r.cardOpen).toBe(true);
    expect(r.openRows).toBe(0);
  });

  test('global search "renew <charm>" routes to THAT charm recipe row — all 6', async ({ page }) => {
    for (const charm of CHARMS) {
      const open = await page.evaluate((c) => {
        const inp = document.getElementById('gsearch-input') as HTMLInputElement;
        inp.value = 'renew ' + c;
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        const items = [...document.querySelectorAll('#gsearch-results .gsearch-item')];
        const idx = items.findIndex((el) =>
          /recipe/i.test((el.querySelector('.gsearch-cat') as HTMLElement)?.textContent || '') &&
          (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.toLowerCase().includes(c.toLowerCase()));
        if (idx < 0) return ['__NO_RECIPE_RESULT__'];
        (items[idx] as HTMLElement).dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        return [...document.querySelectorAll('#sunder-recipe-grid details.sun-recipe[open]')]
          .map((d) => d.getAttribute('data-charm'));
      }, charm);
      expect(open).toEqual([charm]);
    }
  });

  test('openDrop(charm) opens THAT charm material card — no cross-contamination', async ({ page }) => {
    for (const charm of CHARMS) {
      const name = await page.evaluate((c) => {
        (window as any).openDrop(c);
        const h = document.querySelector('#item-detail .gic-name') as HTMLElement | null;
        return h?.textContent?.trim() || '';
      }, charm);
      // gic-name is "<charm> <category badge>" -> must START with the charm name
      expect(name.startsWith(charm)).toBe(true);
    }
  });

  test('global search material result for each charm routes to its own openDrop card', async ({ page }) => {
    for (const charm of CHARMS) {
      const name = await page.evaluate((c) => {
        const inp = document.getElementById('gsearch-input') as HTMLInputElement;
        inp.value = c;
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        const items = [...document.querySelectorAll('#gsearch-results .gsearch-item')];
        const idx = items.findIndex((el) =>
          /material/i.test((el.querySelector('.gsearch-cat') as HTMLElement)?.textContent || '') &&
          (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.toLowerCase().startsWith(c.toLowerCase()));
        if (idx < 0) return '__NO_MATERIAL_RESULT__';
        (items[idx] as HTMLElement).dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        const h = document.querySelector('#item-detail .gic-name') as HTMLElement | null;
        return h?.textContent?.trim() || '';
      }, charm);
      expect(name.startsWith(charm)).toBe(true);
    }
  });

  test('no console errors driving every per-charm route', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate((charms) => {
      for (const c of charms) { (window as any).openSunderRecipes(c); (window as any).openDrop(c); }
      (window as any).openSunderRecipes();
    }, CHARMS);
    await page.waitForTimeout(120);
    expect(errs).toEqual([]);
  });
});
