import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v86 — boss-card-parity "Hell drops" GRID for the terror zones. Each TZ zone detail
// now carries the same rarest-first ranked TABLE the boss top-drops grid uses, Hell-
// framed and ranked by TC ceiling (the rarity proxy). HONESTY: NO fabricated per-kill
// 1:N odds — the silospen terrorized-zone pull is still pending, so numeric columns are
// deliberately omitted (TC ceiling + qlvl only). Rows route to the one canonical item
// card via navigateToItem, exactly like the boss grid. The categorical chip block
// (zoneDropBlockHtml) is KEPT alongside (additive — nothing cut).
test.describe('v86 TZ zones carry the rarest-first Hell drops grid', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('zoneHellGridHtml is exposed and renders a rarest-first table for a TC87 zone', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87)!;
      const h = (window as any).zoneHellGridHtml(tc87);
      const pool = (window as any).zoneGrailDrops(tc87);
      // rank-order check: the first rendered row must be a highest-TC item. The row name now
      // lives in data-arttip (the cell renders artOr()+name, not a bare <strong>); tie-robust —
      // several items can share the max TC, so assert the first row's item HAS the max TC.
      const firstName = (h.match(/zd-hg-name"\s+data-arttip="([^"]+)"/) || [, ''])[1];
      const maxTc = Math.max.apply(null, pool.map((p: any) => p.tc));
      const firstEntry = pool.find((p: any) => p.name === firstName);
      return {
        type: typeof (window as any).zoneHellGridHtml,
        hasTable: /class="drops zd-hell-grid"/.test(h),
        hasHead: /HELL terror-pool drops/.test(h),
        ranksRarestFirst: !!firstEntry && firstEntry.tc === maxTc,
        hasUndefined: /undefined/.test(h),
        // honesty: no fabricated 1:N per-kill odds in the grid
        noFakeOdds: !/1:[0-9]/.test(h),
        rowCount: (h.match(/class="zd-hg-row"/g) || []).length,
        poolLen: pool.length,
      };
    });
    expect(r.type).toBe('function');
    expect(r.hasTable).toBe(true);
    expect(r.hasHead).toBe(true);
    expect(r.ranksRarestFirst).toBe(true);
    expect(r.hasUndefined).toBe(false);
    expect(r.noFakeOdds, 'the Hell grid must NOT invent per-kill 1:N odds').toBe(true);
    // top-20 are inline; the remainder lives in the show-all <details>
    expect(r.rowCount).toBe(r.poolLen);
  });

  test('every TZ zone with a pool renders the grid inside its detail card', async ({ page }) => {
    const missing = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const bad: string[] = [];
      ZS.forEach((z) => {
        const pool = (window as any).zoneGrailDrops(z);
        if (!pool.length) return; // capped zones with no grail pool legitimately skip
        const h = (zoneDetailHtml as any)(z);
        if (!(/zd-hell-grid/.test(h) && /HELL terror-pool drops/.test(h))) bad.push(z.name);
      });
      return bad;
    });
    expect(missing, `zones missing the Hell drops grid: ${missing}`).toEqual([]);
  });

  test('grid rows route to the canonical item card via navigateToItem', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87)!;
      const h = (window as any).zoneHellGridHtml(tc87);
      const firstRow = (h.match(/<tr class="zd-hg-row"[^>]*>/) || [''])[0];
      return { wired: /navigateToItem\('/.test(firstRow), stops: /event\.stopPropagation\(\)/.test(firstRow) };
    });
    expect(r.wired).toBe(true);
    expect(r.stops).toBe(true);
  });

  test('the categorical chip block is KEPT alongside the grid (additive, nothing cut)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87)!;
      const h = (zoneDetailHtml as any)(tc87);
      return {
        hasGrid: /zd-hell-grid/.test(h),
        hasChips: /grail-eligible uniques reachable/.test(h), // zoneDropBlockHtml header
      };
    });
    expect(r.hasGrid).toBe(true);
    expect(r.hasChips).toBe(true);
  });

  test('clicking a grid row opens the item card (live)', async ({ page }) => {
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(200);
    await page.evaluate(() => {
      const box = document.getElementById('tz-zone-detail-0');
      const ZS = (TZ_ZONES as any[]);
      if (box) { box.innerHTML = (zoneDetailHtml as any)(ZS[0]); box.removeAttribute('hidden'); }
    });
    await page.waitForTimeout(150);
    const opened = await page.evaluate(() => {
      const rowEl = document.querySelector('#tz-zone-detail-0 .zd-hg-row') as HTMLElement | null;
      if (!rowEl) return { had: false, shown: false };
      rowEl.click();
      const panel = document.getElementById('item-detail');
      return { had: true, shown: !!panel && panel.classList.contains('show') };
    });
    expect(opened.had).toBe(true);
    expect(opened.shown).toBe(true);
  });

  test('no console errors rendering every zone Hell grid', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      (TZ_ZONES as any[]).forEach((z) => { (window as any).zoneHellGridHtml(z); });
    });
    expect(errors).toEqual([]);
  });
});
