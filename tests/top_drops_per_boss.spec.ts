import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// Feature: per-boss "Holy Grail — Top Drops" curated list (grail/uber items droppable
// at that boss, ranked rarest-first by best-achievable MF-adjusted odds) + a collapsed
// "Show all N droppable items" dropdown wrapping the full sortable table.
test.describe('Holy Grail — Top Drops per boss', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(false); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(2500);
  });

  test('boss detail renders top-drops list + collapsed full-table dropdown', async ({ page }) => {
    await page.evaluate(() => window.openBossDetail('mephisto'));
    await page.waitForTimeout(500);
    const ui = await page.evaluate(() => {
      const card = document.getElementById('mephisto');
      const rows = card ? [...card.querySelectorAll('.top-drop-row')] : [];
      const details = card ? card.querySelector('.all-drops-details') : null;
      return {
        hasSection: !!(card && card.querySelector('.top-drops')),
        rowCount: rows.length,
        hasDetails: !!details,
        detailsOpenByDefault: details ? (details as HTMLDetailsElement).open : null,
        fullTableInsideDetails: !!(details && details.querySelector('table.drops')),
      };
    });
    expect(ui.hasSection).toBe(true);
    expect(ui.rowCount).toBeGreaterThan(0);
    expect(ui.rowCount).toBeLessThanOrEqual(20);
    expect(ui.hasDetails).toBe(true);
    expect(ui.detailsOpenByDefault).toBe(false);
    expect(ui.fullTableInsideDetails).toBe(true);
  });

  test('top-drops are sorted rarest-first (non-increasing 1:N odds)', async ({ page }) => {
    await page.evaluate(() => window.openBossDetail('mephisto'));
    await page.waitForTimeout(500);
    const odds = await page.evaluate(() => {
      const card = document.getElementById('mephisto');
      return [...card.querySelectorAll('.top-drop-row .top-drop-odds')].map(el => {
        const txt = el.textContent || '';
        if (txt.includes('%')) return 1; // sub-100 percentage drop = least rare, sorts last
        const m = txt.match(/1:([\d,]+)/);
        return m ? parseInt(m[1].replace(/,/g, '')) : null;
      });
    });
    expect(odds.length).toBeGreaterThan(1);
    for (let i = 1; i < odds.length; i++) {
      expect(odds[i - 1]).toBeGreaterThanOrEqual(odds[i] as number);
    }
  });

  test('only grail/uber tier items appear in the top-drops list', async ({ page }) => {
    await page.evaluate(() => window.openBossDetail('mephisto'));
    await page.waitForTimeout(500);
    const result = await page.evaluate(() => {
      const card = document.getElementById('mephisto');
      const names = [...card.querySelectorAll('.top-drop-row .top-drop-name')]
        .map(el => (el.textContent || '').replace(/^[★⚡]\s*/, '').replace(/\s*🔒.*$/, '').trim());
      const boss = (typeof BOSSES !== 'undefined') ? BOSSES.find(b => b.id === 'mephisto') : null;
      const tierOf = {};
      if (boss) boss.dropTable.forEach(d => { tierOf[d.n] = d.tier; });
      return names.map(n => tierOf[n]);
    });
    expect(result.length).toBeGreaterThan(0);
    for (const tier of result) {
      expect(['grail', 'uber']).toContain(tier);
    }
  });

  test('clicking a top-drop row navigates to the item in the calculator', async ({ page }) => {
    await page.evaluate(() => { localStorage.clear(); });
    await page.reload();
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(false); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(2500);
    await page.evaluate(() => window.openBossDetail('mephisto'));
    await page.waitForTimeout(500);
    const target = await page.evaluate(() => {
      const row = document.querySelector('#mephisto .top-drop-row');
      const name = row.querySelector('.top-drop-name').textContent.replace(/^[★⚡]\s*/, '').replace(/\s*🔒.*$/, '').trim();
      (row as HTMLElement).click();
      return name;
    });
    await page.waitForTimeout(800);
    const state = await page.evaluate(() => ({
      tab: document.querySelector('.tab.active')?.getAttribute('data-tab'),
      selectedItem: eval('typeof selectedItem !== "undefined" ? selectedItem : null'),
    }));
    expect(state.tab).toBe('calc');
    expect(state.selectedItem).toBe(target);
  });
});
