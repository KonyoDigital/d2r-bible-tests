import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v449 — the magic small/grand-charm reference cards (FHR / resist / MF / life / FRW
// small charms + class skillers) live in EXTRA_ITEMS and route via openDrop, but were
// never folded into the global search index, so "FHR charm" / "faster hit recovery"
// returned nothing. This wires them into v42BuildCommands keyed by what they ROLL, plus
// an FCR clarifier (charms can't roll Faster Cast Rate). Pure search-wiring; the cards
// already existed.
test.describe('v449 charm affixes are searchable by what they roll', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  async function search(page: any, q: string) {
    await page.fill('#gsearch-input', q);
    await page.waitForTimeout(200);
    return page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
      .map((el) => ({
        lab: (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
        cat: (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
      })));
  }

  test('"faster hit recovery charm" surfaces the FHR small-charm card', async ({ page }) => {
    // bare "faster hit recovery" legitimately returns every FHR source (runewords, gear);
    // adding "charm" scopes it to charms — the way a user actually phrases the search.
    const hits = await search(page, 'faster hit recovery charm');
    expect(hits.some((h) => /Small Charm of Balance/.test(h.lab))).toBe(true);
  });

  test('"fhr charm" surfaces the FHR small charm', async ({ page }) => {
    const hits = await search(page, 'fhr charm');
    expect(hits.some((h) => /FHR|Balance/.test(h.lab) && /charm/i.test(h.cat))).toBe(true);
  });

  test('"resist charm" and "mf charm" and "life charm" each surface a small charm', async ({ page }) => {
    const res = await search(page, 'resist charm');
    expect(res.some((h) => /Shimmering Small Charm|All Res|Resist/.test(h.lab))).toBe(true);
    const mf = await search(page, 'mf charm');
    expect(mf.some((h) => /Good Luck|MF/.test(h.lab))).toBe(true);
    const life = await search(page, 'life charm');
    expect(life.some((h) => /Vita|Life/.test(h.lab))).toBe(true);
  });

  test('"skiller" surfaces a grand-charm skiller', async ({ page }) => {
    const hits = await search(page, 'skiller');
    expect(hits.some((h) => /Skiller|Grand Charm/.test(h.lab))).toBe(true);
  });

  test('"fcr charm" returns the not-a-charm-affix clarifier (instead of nothing)', async ({ page }) => {
    const hits = await search(page, 'fcr charm');
    expect(hits.some((h) => /not a charm affix/i.test(h.lab))).toBe(true);
  });

  test('picking an FHR small charm opens its reference card', async ({ page }) => {
    await page.fill('#gsearch-input', 'faster hit recovery charm');
    await page.waitForTimeout(220);
    await page.locator('#gsearch-results .gsearch-item', { hasText: 'Balance' }).first().click();
    await page.waitForTimeout(250);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail');
      return { shown: panel?.classList.contains('show'), text: panel?.textContent || '' };
    });
    expect(r.shown).toBe(true);
    expect(r.text).toMatch(/Faster Hit Recovery/i);
  });

  test('no console errors when driving the charm-affix search', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push(e.message));
    await search(page, 'faster hit recovery');
    await search(page, 'fcr charm');
    await search(page, 'skiller');
    expect(errs).toEqual([]);
  });
});
