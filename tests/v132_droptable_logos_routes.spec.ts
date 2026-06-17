import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v132 — unified drop-row logos + stash routing. Every boss drop-table item name
// (the full filterable table, the boss-card Top Drops list, AND the golden boss
// detail card's Top Drops grid) now renders its in-game art via the shared
// nameLogo() helper — art shown ONLY when one is registered (no empty box for
// art-less items). The rune-stash + material-stash + cube-up result names are now
// clickable -> openDrop() routes to their own card.
test.describe('v132 drop-table logos + stash routing (unified synced route)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(true); } catch (e) {} }).catch(() => {});
    await page.waitForTimeout(800);
  });

  test('nameLogo helper exists and only renders art for registered names', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w: any = window;
      return {
        fn: typeof w.nameLogo,
        soj: w.nameLogo('The Stone of Jordan'),
        bogus: w.nameLogo('Zzz Not A Real Item'),
      };
    });
    expect(r.fn).toBe('function');
    expect(r.soj).toContain('d2art-img');
    expect(r.bogus).toBe('');
  });

  test('boss-card full drop table item names show their art logo', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBossDetail('mephisto');
      const card = document.getElementById('mephisto');
      const probe = (n: string) => !!card?.querySelector(`tr[data-item="${n}"] td.item-name .d2art-img`);
      return ['The Stone of Jordan', 'Nagelring', 'Metalgrid'].map(probe);
    });
    expect(r.every(Boolean)).toBe(true);
  });

  test('boss-card Top Drops list + golden detail-card Top Drops show logos', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBossDetail('mephisto');
      const card = document.getElementById('mephisto');
      const list = [...(card?.querySelectorAll('.top-drop-name') || [])];
      const detail = [...document.querySelectorAll('#boss-detail-panel tr')];
      return {
        listWithArt: list.filter(e => e.querySelector('.d2art-img')).length,
        listTotal: list.length,
        detailWithArt: detail.filter(e => e.querySelector('.d2art-img')).length,
      };
    });
    expect(r.listTotal).toBeGreaterThan(0);
    expect(r.listWithArt).toBeGreaterThanOrEqual(Math.ceil(r.listTotal * 0.5));
    expect(r.detailWithArt).toBeGreaterThan(0);
  });

  test('rune-stash names route to their rune card', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#rune-stash-grid .rs-name')];
      return {
        count: names.length,
        allRouted: names.every(n => /openDrop\(/.test(n.getAttribute('onclick') || '')),
        allStop: names.every(n => /stopPropagation/.test(n.getAttribute('onclick') || '')),
      };
    });
    expect(r.count).toBeGreaterThan(0);
    expect(r.allRouted).toBe(true);
    expect(r.allStop).toBe(true);
  });

  test('material-stash names route to their card', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#material-stash-grid .mat-name .zd-item-click')];
      return {
        count: names.length,
        allRouted: names.every(n => /openDrop\(/.test(n.getAttribute('onclick') || '')),
      };
    });
    expect(r.count).toBeGreaterThan(0);
    expect(r.allRouted).toBe(true);
  });

  test('clicking a rune-stash name opens that rune card; no console errors', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const opened = await page.evaluate(() => {
      const el = document.querySelector('#rune-stash-grid .rs-name[onclick*="openDrop"]') as HTMLElement | null;
      el?.click();
      return !!document.getElementById('item-detail')?.querySelector('.rune-card');
    });
    expect(opened).toBe(true);
    expect(errs).toEqual([]);
  });
});
