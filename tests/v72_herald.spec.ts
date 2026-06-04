import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v72 — Herald of Terror dedicated ID card in the RotW tab. A rich, picture-bearing
// boss-style card (the same gbc/boss-detail template as Mephisto) that documents the
// only Sunder source in RotW. The 6 Latent Sunder rows are rendered from the SAME
// SPECIAL_DROPS data + the verified D2IO_ART icons (zero new/fabricated data); each
// charm name opens its full material card via openDrop, and the global search resolves
// "herald" straight to the card.
test.describe('v72 Herald of Terror ID card', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="rotw"]');
    await page.waitForTimeout(150);
  });

  test('the card renders in the RotW tab with the boss-detail identity block', async ({ page }) => {
    const card = page.locator('#herald-card');
    // collapsed by default (Konyo's request) — drop it open via its header first
    await expect(card).toBeHidden();
    await page.locator('#tab-rotw .sec-h', { hasText: 'Herald of Terror' }).evaluate((e: any) => e.click());
    await expect(card).toBeVisible();
    await expect(card.locator('.gbc-name')).toHaveText(/Herald of Terror/);
    await expect(card.locator('.gbc-subtitle')).toHaveText(/Sunder/i);
    // it sits ABOVE the Worldstone Shards section (first section in the tab)
    const order = await page.evaluate(() => {
      const tab = document.getElementById('tab-rotw')!;
      const heads = [...tab.querySelectorAll('.sec-h')].map((h) => h.textContent || '');
      return heads;
    });
    expect(order[0]).toMatch(/Herald of Terror/);
    expect(order.some((h) => /Worldstone Shards/.test(h))).toBe(true);
  });

  test('the header emblem renders the verified Bone Break charm graphic (not a bare emoji)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const card = document.getElementById('herald-card')!;
      const img = card.querySelector('.gbc-header .d2art-img') as HTMLImageElement | null;
      return {
        hasImg: !!img,
        src: img?.getAttribute('src') || '',
        hasFallback: !!card.querySelector('.gbc-header .d2art-fallback'),
      };
    });
    expect(r.hasImg).toBe(true);
    expect(r.src).toMatch(/bonebreakcharm_graphic\.png$/);
    expect(r.hasFallback).toBe(true); // 👹 emoji still embedded for the error path
  });

  test('renderHeraldCard fills all 6 Sunder rows with verified D2IO_ART icons + openDrop links', async ({ page }) => {
    const r = await page.evaluate(() => {
      const tb = document.getElementById('herald-sunder-rows')!;
      const rows = [...tb.querySelectorAll('tr')];
      const names = rows.map((tr) => (tr.querySelector('.zd-item-click') as HTMLElement)?.textContent?.replace(/\s*→\s*$/, '').trim());
      const imgs = rows.map((tr) => (tr.querySelector('.d2art-img') as HTMLImageElement)?.getAttribute('src') || '');
      const breaks = rows.map((tr) => (tr.querySelector('td.brk') as HTMLElement)?.textContent?.trim());
      return {
        count: rows.length,
        names,
        allImgs: imgs.every((s) => /^https:\/\/diablo2\.io\/styles\/zulu\/theme\/images\/items\/.*_graphic\.png$/.test(s)),
        bonebreakImg: imgs[0],
        breaks,
        fnType: typeof (window as any).renderHeraldCard,
      };
    });
    expect(r.count).toBe(6);
    expect(r.fnType).toBe('function');
    expect(r.names).toEqual([
      'Bone Break', 'Black Cleft', 'Crack of the Heavens', 'Cold Rupture', 'Flame Rift', 'Rotting Fissure',
    ]);
    expect(r.allImgs).toBe(true);                       // every charm shows real art
    expect(r.bonebreakImg).toMatch(/bonebreakcharm_graphic\.png$/);
    expect(r.breaks).toEqual(['Physical', 'Magic', 'Lightning', 'Cold', 'Fire', 'Poison']);
  });

  test('clicking a charm name opens its full material card', async ({ page }) => {
    await page.evaluate(() => {
      const tr = document.querySelectorAll('#herald-sunder-rows tr')[0];
      (tr.querySelector('.zd-item-click') as HTMLElement).click();
    });
    await page.waitForTimeout(150);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail');
      return {
        shown: panel?.classList.contains('show'),
        name: panel?.querySelector('.material-card .gic-name')?.textContent?.trim() || '',
        hasArt: !!panel?.querySelector('.material-card .gic-header .d2art-img'),
      };
    });
    expect(r.shown).toBe(true);
    expect(r.name).toMatch(/Bone Break/);
    expect(r.hasArt).toBe(true);
  });

  test('global search resolves "herald" to the RotW card', async ({ page }) => {
    await page.fill('#gsearch-input', 'herald');
    await page.waitForTimeout(220);
    const cats = await page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
      .map((el) => ({
        lab: (el.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
        cat: (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
      })));
    expect(cats.some((x) => /Herald of Terror/.test(x.lab))).toBe(true);
  });

  test('no console errors across the Herald flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="rotw"]');
    await page.waitForTimeout(150);
    await page.evaluate(() => {
      (window as any).renderHeraldCard();
      const tr = document.querySelectorAll('#herald-sunder-rows tr')[2];
      (tr.querySelector('.zd-item-click') as HTMLElement).click();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
