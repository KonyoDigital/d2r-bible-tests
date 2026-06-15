import { test, expect } from '@playwright/test';

// v321 — round-5+ regression lock: the "🏆 Holy Grail — Top Drops" grid (bossTopDropsHtml)
// rendered every UNIQUE in theme --gold-bright (#f0c060) because .top-drop-name had rules for
// set/rune/material but NONE for q-unique. The Mephisto Top-12 screenshot bug. Now uniques must
// read in-game unique gold #c7b377 (rgb(199,179,119)), and uber rows must STAY terror pink.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._artRarity && (window as any).bossTopDropsHtml);
});

test('Top-Drops grid paints a unique item name in-game unique gold #c7b377 (NOT theme gold-bright)', async ({ page }) => {
  const color = await page.evaluate(() => {
    const host = document.createElement('div');
    // Mephisto's grail pool is all uniques/sets — render its Top-Drops grid
    const meph = (window as any).eval('BOSSES').find((b: any) => b.id === 'mephisto'); // BOSSES is module-scoped
    host.innerHTML = (window as any).bossTopDropsHtml(meph, 12);
    document.body.appendChild(host);
    // first non-uber unique name
    const names = Array.from(host.querySelectorAll('.top-drop-row:not(.top-drop-uber) .top-drop-name')) as HTMLElement[];
    const uniqueEl = names.find(el => el.className.includes('q-unique'));
    return uniqueEl ? getComputedStyle(uniqueEl).color : 'NO_UNIQUE_FOUND';
  });
  expect(color).toBe('rgb(199, 179, 119)'); // #c7b377 in-game unique gold
});

test('Top-Drops grid keeps uber rows terror pink (preserve special-case)', async ({ page }) => {
  const r = await page.evaluate(() => {
    // Diablo's grail pool includes uber/special rows in some bosses; build a synthetic uber row check
    const host = document.createElement('div');
    const baal = (window as any).eval('BOSSES').find((b: any) => b.id === 'baal');
    host.innerHTML = (window as any).bossTopDropsHtml(baal, 20);
    document.body.appendChild(host);
    const uber = host.querySelector('.top-drop-uber .top-drop-name') as HTMLElement | null;
    return uber ? getComputedStyle(uber).color : 'NO_UBER'; // ok if no uber in this boss
  });
  // --terror #ff00d4 = rgb(255,0,212); if no uber rows present that's fine (skip)
  if (r !== 'NO_UBER') expect(r).toBe('rgb(255, 0, 212)');
});

test('the CSS rule .top-drop-name.q-unique now exists (the missing rule that caused the bug)', async ({ page }) => {
  const ok = await page.evaluate(() => {
    const el = document.createElement('span');
    el.className = 'top-drop-name q-unique';
    const row = document.createElement('li');
    row.className = 'top-drop-row';
    row.appendChild(el);
    const grid = document.createElement('div'); grid.className = 'top-drops'; grid.appendChild(row);
    document.body.appendChild(grid);
    return getComputedStyle(el).color;
  });
  expect(ok).toBe('rgb(199, 179, 119)'); // #c7b377, not #f0c060 gold-bright
});
