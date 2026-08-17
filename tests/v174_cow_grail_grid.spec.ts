// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v174 — the Secret Cow Level event card now surfaces the SAME golden "Holy Grail —
// Top Drops" grid the Hell Bovines boss card shows, INLINE (#cow-grail-grid), built
// by the shared bossTopDropsHtml() helper off the SAME BOSSES "cows" dropTable + the
// live effChance engine — one source of truth, zero fabricated odds. This makes the
// cow event card itself "dropeable" like the unified zone cards, while still routing
// to the full per-difficulty boss card. The bossTopDropsHtml extraction is verbatim,
// so the boss-card top-drops (top_drops_per_boss.spec) are unchanged.

test.describe('v174 Cow Level inline grail Top-Drops grid', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200); // let _v39_whenReady(renderCowGrailGrid) run
  });

  test('the event card renders an inline golden Top-Drops grid sourced from BOSSES cows', async ({ page }) => {
    const r = await page.evaluate(() => {
      const host = document.getElementById('cow-grail-grid')!;
      const rows = [...host.querySelectorAll('.top-drop-row')] as HTMLElement[];
      const cows = (BOSSES as any).find((b: any) => b.id === 'cows');
      const grailNames = new Set(cows.dropTable.filter((d: any) => d.tier === 'grail' || d.tier === 'uber').map((d: any) => d.n));
      const names = rows.map((r) => (r.querySelector('.top-drop-name')!.textContent || '').replace(/^[★⚡\s]+/, '').replace(/\s*🔒.*$/, '').trim());
      return {
        hasGrid: !!host.querySelector('.top-drops'),
        rowCount: rows.length,
        allGrail: names.every((n) => grailNames.has(n)),
        routesToBoss: /openBossDetail\('cows'\)/.test(host.innerHTML),
      };
    });
    expect(r.hasGrid).toBe(true);
    expect(r.rowCount).toBeGreaterThan(0);
    expect(r.rowCount).toBeLessThanOrEqual(12);
    expect(r.allGrail).toBe(true);    // every previewed item is a real grail/uber cow drop
    expect(r.routesToBoss).toBe(true); // still routes to the canonical boss card
  });

  test('inline preview rows are sorted rarest-first (non-increasing 1:N)', async ({ page }) => {
    const odds = await page.evaluate(() => {
      const host = document.getElementById('cow-grail-grid')!;
      return [...host.querySelectorAll('.top-drop-row .top-drop-odds')].map((el) => {
        const txt = el.textContent || '';
        if (txt.includes('%')) return 1;
        const m = txt.match(/1:([\d,]+)/);
        return m ? parseInt(m[1].replace(/,/g, '')) : null;
      });
    });
    expect(odds.length).toBeGreaterThan(1);
    for (let i = 1; i < odds.length; i++) expect(odds[i - 1]).toBeGreaterThanOrEqual(odds[i] as number);
  });

  test('the inline grid is the SAME data as the Hell Bovines boss card (single source)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cows = (BOSSES as any).find((b: any) => b.id === 'cows');
      // first 12 of the boss-card top-drops == the inline preview (same helper, same data)
      const bossTop = (window as any).bossTopDropsHtml(cows, 12);
      const tmp = document.createElement('div'); tmp.innerHTML = bossTop;
      const bossNames = [...tmp.querySelectorAll('.top-drop-name')].map((e) => (e.textContent || '').trim());
      const inlineNames = [...document.querySelectorAll('#cow-grail-grid .top-drop-name')].map((e) => (e.textContent || '').trim());
      return { bossNames, inlineNames };
    });
    expect(r.inlineNames.length).toBeGreaterThan(0);
    expect(r.inlineNames).toEqual(r.bossNames);
  });

  test('clicking an inline row navigates to the item in the calculator', async ({ page }) => {
    await page.evaluate(() => { localStorage.clear(); });
    await page.reload();
    await page.waitForTimeout(1200);
    const target = await page.evaluate(() => {
      const row = document.querySelector('#cow-grail-grid .top-drop-row') as HTMLElement;
      const name = (row.querySelector('.top-drop-name')!.textContent || '').replace(/^[★⚡\s]+/, '').replace(/\s*🔒.*$/, '').trim();
      row.click();
      return name;
    });
    await page.waitForTimeout(700);
    const state = await page.evaluate(() => ({
      tab: document.querySelector('.tab.active')?.getAttribute('data-tab'),
      selectedItem: eval('typeof selectedItem !== "undefined" ? selectedItem : null'),
    }));
    expect(state.tab).toBe('calc');
    expect(state.selectedItem).toBe(target);
  });

  test('no console errors rendering the cow grail grid', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => (window as any).renderCowGrailGrid && (window as any).renderCowGrailGrid());
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
