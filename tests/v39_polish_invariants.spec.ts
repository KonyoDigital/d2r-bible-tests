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
  // the 700ms window.
  //
  // #80 (REG-1518) — THE THROTTLE IS A `let`, NOT A WINDOW PROPERTY. The old bypass wrote
  // `w._v39_pulseTimer = null`, a property nobody reads: the binding the pulse checks is the
  // script's top-level `let`, which only an indirect eval can reach from here. So the bypass is
  // `(0, eval)(...)`, and the same read reports whether the throttle really is clear before the call.
  test('pulse function adds .syncing class to summary cells', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    const r = await page.evaluate(() => {
      const w = window as any;
      (0, eval)('_v39_pulseTimer = null;'); // bypass throttle — the real binding, see above
      const clear = (0, eval)('_v39_pulseTimer') === null;
      w._v39_pulseAllSyncedCells();
      return { clear, syncingCount: document.querySelectorAll('.syncing').length };
    });
    expect(r.clear, 'premise: the throttle must be clear before the call').toBe(true);
    expect(r.syncingCount).toBeGreaterThan(0);
  });

  test('MF slider input triggers the pulse on a synced cell', async ({ page }) => {
    // #271 (the #231 eye on 46c8cda9) - the May cut deleted this case, so an MF slider whose input
    // listener never pulses passed every remaining case (they all call the pulse directly). This drives
    // the slider itself: seed one synced cell, clear the throttle, fire `input` on #mf, and require the
    // class ON within two animation frames - the listener pulses on a single rAF.
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    await page.waitForTimeout(500); // _v39_whenReady hooks the slider after load
    const r = await page.evaluate(async () => {
      const seed = document.createElement('span');
      seed.className = 'stat-value';
      seed.id = 'v39-mf-seeded-cell';
      seed.textContent = '0';
      document.body.appendChild(seed);
      (0, eval)('_v39_pulseTimer = null;');
      const mf = document.getElementById('mf') as HTMLInputElement | null;
      if (!mf) return { slider: false, seeded: false };
      mf.value = String(Math.min(Number(mf.max) || 1000, Number(mf.value) + 1));
      mf.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise(res => requestAnimationFrame(() => requestAnimationFrame(res)));
      return { slider: true, seeded: seed.classList.contains('syncing') };
    });
    expect(r.slider, 'premise: the page has its MF slider (#mf)').toBe(true);
    expect(r.seeded, 'moving the MF slider did not pulse the synced cells').toBe(true);
  });

  test('.syncing class is removed after pulse window (~700ms)', async ({ page }) => {
    // #80 (REG-1518) — the old shape (pulse, sleep 1100ms, expect 0) could never fail: a pulse that
    // early-returns on its throttle, or finds no summary cell, ALSO leaves 0. So this seeds one synced
    // cell the way the page defines them — a `.stat-value`, one of _v39_pulseAllSyncedCells' own
    // targets — and requires the class ON (read synchronously, in the evaluate that pulsed) before it
    // may find it OFF.
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    const during = await page.evaluate(() => {
      const w = window as any;
      const seed = document.createElement('span');
      seed.className = 'stat-value';
      seed.id = 'v39-seeded-synced-cell';
      seed.textContent = '0';
      document.body.appendChild(seed);
      (0, eval)('_v39_pulseTimer = null;'); // bypass throttle — the real binding, see above
      const clear = (0, eval)('_v39_pulseTimer') === null;
      w._v39_pulseAllSyncedCells();
      return {
        clear,
        seeded: seed.classList.contains('syncing'),
        total: document.querySelectorAll('.syncing').length,
      };
    });
    expect(during.clear, 'premise: the throttle must be clear before the call').toBe(true);
    expect(during.seeded, 'the seeded synced cell never received .syncing — the pulse did not fire, so a later 0 would prove nothing').toBe(true);
    expect(during.total, 'no cell carries .syncing right after the pulse — it never fired, so a later 0 proves nothing').toBeGreaterThan(0);
    await page.waitForTimeout(1100);
    const after = await page.evaluate(() => ({
      seeded: document.getElementById('v39-seeded-synced-cell')!.classList.contains('syncing'),
      total: document.querySelectorAll('.syncing').length,
    }));
    expect(after.seeded, 'the seeded cell still carries .syncing after the pulse window').toBe(false);
    expect(after.total).toBe(0);
  });

  test('pulse hits summary-class cells only (not every droptable td)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForFunction(() => typeof (window as any)._v39_pulseAllSyncedCells !== 'undefined', { timeout: 3000 });
    const r = await page.evaluate(() => {
      const w = window as any;
      (0, eval)('_v39_pulseTimer = null;'); // bypass throttle — the real binding, see above
      const clear = (0, eval)('_v39_pulseTimer') === null;
      w._v39_pulseAllSyncedCells();
      return { clear, syncingCount: document.querySelectorAll('.syncing').length };
    });
    expect(r.clear, 'premise: the throttle must be clear before the call').toBe(true);
    // Total .syncing should be small (~60 summary cells), never the 19k droptable cell count
    expect(r.syncingCount).toBeGreaterThan(0);
    expect(r.syncingCount).toBeLessThan(500);
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
