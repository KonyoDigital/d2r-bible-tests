import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v152 — site-wide item/rune reference unification (Konyo: "items need the same format —
// emoji artOr with image + cursor floating popup"). Every item/rune list surface now carries
// the inline in-game art logo (nameLogo) AND the floating #arttip hover card (data-arttip):
//   • TZ grail-eligible unique chips (zoneDropBlockHtml)
//   • the rarest-first Hell drops grid rows (zoneHellGridHtml)
//   • the Countess rune table rows (renderRuneTable)
//   • the boss "top 15 grail picks" grid cards (gbc-grail-item)
// PLUS the RoTW section headers match the Runes/Bosses bar exactly: gold title + the italic
// subtitle TOP-anchored directly under it (no longer floating in the vertical middle).
test.describe('v152 item/rune art + floating tooltip unification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  test('TZ grail-unique chips carry inline art + a data-arttip floating card', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87);
      const h = (window as any).zoneDropBlockHtml(tc87);
      const div = document.createElement('div');
      div.innerHTML = h;
      const chips = [...div.querySelectorAll('.zd-item.zd-item-click')] as HTMLElement[];
      return {
        chipCount: chips.length,
        allHaveTip: chips.every((c) => !!c.getAttribute('data-arttip')),
        someHaveArt: chips.some((c) => !!c.querySelector('.d2art-wrap img')),
      };
    });
    expect(r.chipCount).toBeGreaterThan(5);
    expect(r.allHaveTip).toBe(true);
    expect(r.someHaveArt).toBe(true);
  });

  test('the Hell drops grid rows carry inline art + data-arttip', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87);
      const h = (window as any).zoneHellGridHtml(tc87);
      const div = document.createElement('div');
      div.innerHTML = h;
      const names = [...div.querySelectorAll('.zd-hg-name')] as HTMLElement[];
      return {
        rowCount: names.length,
        allHaveTip: names.every((n) => !!n.getAttribute('data-arttip')),
        someHaveArt: names.some((n) => !!n.querySelector('.d2art-wrap img')),
      };
    });
    expect(r.rowCount).toBeGreaterThan(5);
    expect(r.allHaveTip).toBe(true);
    expect(r.someHaveArt).toBe(true);
  });

  test('Countess rune table rows carry the bare-rune art logo + data-arttip', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('runes'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('#rune-table-target tbody tr')] as HTMLElement[];
      // single-rune rows (those that resolve to one RUNES entry) become clickable + tipped
      const tipped = rows.filter((tr) => !!tr.querySelector('td.item-name[data-arttip]'));
      return {
        rowCount: rows.length,
        tippedCount: tipped.length,
        // a tipped row resolves to a bare rune name (no "#NN" rank suffix) in data-arttip
        bareName: tipped[0]?.querySelector('td.item-name')?.getAttribute('data-arttip') || '',
        someHaveArt: tipped.some((tr) => !!tr.querySelector('td.item-name .d2art-wrap img')),
      };
    });
    expect(r.rowCount).toBeGreaterThan(5);
    expect(r.tippedCount).toBeGreaterThan(5);
    expect(r.bareName).not.toMatch(/#\d/);   // "Lo", not "Lo #28"
    expect(r.someHaveArt).toBe(true);
  });

  test('the RoTW header subtitle is TOP-anchored under a gold title (Runes parity)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('rotw'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const h = document.querySelector('#tab-rotw > .sec-h') as HTMLElement;
      const t = h.querySelector('.sec-h-t') as HTMLElement;
      return {
        headerAlign: getComputedStyle(h).alignItems,    // flex-start, not center
        titleColor: getComputedStyle(t).color,
      };
    });
    expect(r.headerAlign).toBe('flex-start');
    // gold-bright title like .boss-name (not the muted cream default)
    expect(r.titleColor).toBe('rgb(240, 192, 96)');
  });

  test('no console errors across the restyled item surfaces', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(1000);
    for (const tab of ['rotw', 'runes', 'tz', 'bosses']) {
      await page.evaluate((t) => (window as any).switchTab && (window as any).switchTab(t), tab);
      await page.waitForTimeout(200);
    }
    expect(errors).toEqual([]);
  });
});
