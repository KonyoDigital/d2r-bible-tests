import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v39 polish — tab persistence', () => {
  test('switching tab writes d2r_activeTab to localStorage', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.waitForTimeout(150);
    const saved = await page.evaluate(() => localStorage.getItem('d2r_activeTab'));
    expect(saved).toBe('calc');
  });

  test('v680 — reload lands on TOOLS, the home tab (saved-tab restore retired by doctrine)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.locator('.tab[data-tab="runes"]').click();
    await page.waitForTimeout(150);
    await page.reload();
    await page.waitForTimeout(700);
    await expect(page.locator('.tab[data-tab="tools"]')).toHaveClass(/active/);
  });
});

test.describe('v39 polish — URL hash routing', () => {
  test('switchTab updates location.hash', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(150);
    const hash = await page.evaluate(() => location.hash);
    expect(hash).toBe('#tz');
  });

  test('v680 — a BARE tab hash normalizes to TOOLS on entry (deep-links with a subpath still route)', async ({ page }) => {
    await page.goto(BIBLE + '#calc');
    await page.waitForTimeout(700);
    await expect(page.locator('.tab[data-tab="tools"]')).toHaveClass(/active/);
  });

  test('hashchange (back/forward) routes to the new tab', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.evaluate(() => { location.hash = '#runes'; });
    await page.waitForTimeout(250);
    await expect(page.locator('.tab[data-tab="runes"]')).toHaveClass(/active/);
  });

  test('openBossDetail writes #tab/bossId hash', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).openBossDetail('mephisto'));
    await page.waitForTimeout(250);
    const hash = await page.evaluate(() => location.hash);
    expect(hash).toMatch(/^#[a-z]+\/mephisto$/);
  });

  test('clearActiveBoss strips bossId from hash', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.evaluate(() => (window as any).openBossDetail('diablo'));
    await page.waitForTimeout(200);
    expect(await page.evaluate(() => location.hash)).toMatch(/\/diablo$/);
    await page.evaluate(() => (window as any).clearActiveBoss());
    await page.waitForTimeout(200);
    const hash = await page.evaluate(() => location.hash);
    expect(hash).not.toContain('/');
    expect(hash).toMatch(/^#[a-z]+$/);
  });

  test('deep-link #bosses/baal opens the boss detail overlay', async ({ page }) => {
    await page.goto(BIBLE + '#bosses/baal');
    await page.waitForTimeout(700);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    const name = await page.locator('#boss-detail-panel .bd-name').innerText();
    expect(name.toLowerCase()).toContain('baal');
  });
});

test.describe('v39 polish — sync pulse on MF change', () => {
  // The pulse function has a 600ms internal throttle and a 700ms class-removal cycle.
  // To eliminate races, we read the .syncing count synchronously *inside the same
  // page.evaluate that calls the pulse* — no round-trips that could land outside
  // the 700ms window. We also explicitly clear _v39_pulseTimer before calling so
  // any prior throttle gate is bypassed.
  test('pulse function adds .syncing class to summary cells', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    const syncingCount = await page.evaluate(() => {
      const w = window as any;
      w._v39_pulseTimer = null; // bypass throttle
      w._v39_pulseAllSyncedCells();
      return document.querySelectorAll('.syncing').length;
    });
    expect(syncingCount).toBeGreaterThan(0);
  });

  test('.syncing class is removed after pulse window (~700ms)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    await page.evaluate(() => {
      const w = window as any;
      w._v39_pulseTimer = null;
      w._v39_pulseAllSyncedCells();
    });
    await page.waitForTimeout(1100);
    const syncingAfter = await page.locator('.syncing').count();
    expect(syncingAfter).toBe(0);
  });

  test('pulse hits summary-class cells only (not every droptable td)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    const syncingCount = await page.evaluate(() => {
      const w = window as any;
      w._v39_pulseTimer = null;
      w._v39_pulseAllSyncedCells();
      return document.querySelectorAll('.syncing').length;
    });
    // Total .syncing should be small (~60 summary cells), never the 19k droptable cell count
    expect(syncingCount).toBeGreaterThan(0);
    expect(syncingCount).toBeLessThan(500);
  });
});

test.describe('v39 polish — wrapper exposure', () => {
  test('switchTab + openBossDetail + clearActiveBoss are wrapped on window', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    const exposed = await page.evaluate(() => ({
      switchTab: typeof (window as any).switchTab === 'function',
      openBossDetail: typeof (window as any).openBossDetail === 'function',
      clearActiveBoss: typeof (window as any).clearActiveBoss === 'function',
    }));
    expect(exposed.switchTab).toBe(true);
    expect(exposed.openBossDetail).toBe(true);
    expect(exposed.clearActiveBoss).toBe(true);
  });
});
