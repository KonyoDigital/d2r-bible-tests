import { test, expect } from '@playwright/test';

// v232 — live TZ TRACKER tab. A 12th nav tab with a custom emblem logo that
// reads the live rotation from the same-origin /api/tz Pages Function (proxying
// d2runewizard). Only the HUNTABLE zones (the Telegram-alert allowlist) are
// clickable and route to their bible card; filler zones render dimmed. Under
// file:// the fetch is skipped (graceful offline state) so the suite never sees
// a failed request.

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v232 TZ tracker', () => {
  test('the tab + emblem + title exist and open with a graceful offline state (no console errors)', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push('PAGEERR ' + e.message));
    await page.goto(URL);
    await page.waitForTimeout(1200);
    const nav = await page.evaluate(() => ({
      btn: !!document.querySelector('.tab[data-tab="tztracker"]'),
      panel: !!document.getElementById('tab-tztracker'),
      emblem: !!document.querySelector('.tzt-emblem'),
      title: (document.querySelector('.tzt-title')?.textContent || '').trim(),
    }));
    expect(nav.btn).toBe(true);
    expect(nav.panel).toBe(true);
    expect(nav.emblem).toBe(true);
    expect(nav.title).toBe('Terror Zone Tracker');

    await page.click('.tab[data-tab="tztracker"]');
    await page.waitForTimeout(400);
    const r = await page.evaluate(() => ({
      active: document.getElementById('tab-tztracker')?.classList.contains('active'),
      offline: (document.getElementById('tztracker-body')?.textContent || '').toLowerCase().includes('online site'),
    }));
    expect(r.active).toBe(true);
    expect(r.offline).toBe(true);            // file:// → graceful offline note, no fetch
    expect(errs).toEqual([]);
  });

  test('huntable zones are clickable + route; filler zones are inert', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.click('.tab[data-tab="tztracker"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      (window as any).renderTzTracker({ current: 'Travincal', next: 'Cold Plains and The Cave', ts: 1700000000000 });
      const hunt = document.querySelector('#tztracker-body .tzt-hunt');
      const filler = document.querySelector('#tztracker-body .tzt-filler');
      return {
        huntName: hunt?.querySelector('.tzt-z-name')?.textContent,
        huntId: hunt?.getAttribute('data-tz-hunt'),
        huntClickable: hunt?.getAttribute('role') === 'button',
        fillerName: filler?.querySelector('.tzt-z-name')?.textContent,
        fillerInert: filler?.getAttribute('role') !== 'button',
        updated: (document.getElementById('tzt-updated')?.textContent || '').startsWith('updated'),
      };
    });
    expect(r.huntName).toBe('Travincal');
    expect(r.huntId).toBe('travincal');
    expect(r.huntClickable).toBe(true);
    expect(r.fillerName).toBe('Cold Plains and The Cave');
    expect(r.fillerInert).toBe(true);
    expect(r.updated).toBe(true);
  });

  test('hunt-map matches the real (grouped) zone names for every act boss + key S-tier', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    const r = await page.evaluate(() => {
      const M = (z: string) => (window as any).tzHuntMatch(z)?.id || null;
      return {
        meph: M('Durance of Hate Level 2 and Level 3'),
        duriel: M("Tal Rasha's Tombs"),
        anda: M('The Cathedral and Catacombs Levels 1 to 4'),
        diablo: M('Chaos Sanctuary'),
        baal: M('Worldstone Keep Levels 1, 2 and 3, Throne of Destruction and Worldstone Chamber'),
        trav: M('Travincal'),
        countess: M('The Forgotten Tower'),
        pindle: M("Nihlathak's Temple, Halls of Anguish, Halls of Pain and Halls of Vaught"),
        cows: M('The Secret Cow Level'),
        pit: M('Tamoe Highland and The Pit'),
        arcane: M('Arcane Sanctuary'),
        filler: M('Cold Plains and The Cave'),
        filler2: M('Great Marsh'),
      };
    });
    expect(r.meph).toBe('mephisto');
    expect(r.duriel).toBe('duriel');
    expect(r.anda).toBe('andariel');
    expect(r.diablo).toBe('diablo');
    expect(r.baal).toBe('baal');
    expect(r.trav).toBe('travincal');
    expect(r.countess).toBe('countess');
    expect(r.pindle).toBe('pindle');
    expect(r.cows).toBe('cows');
    expect(r.pit).toBe('pit');
    expect(r.arcane).toBe('arcane');
    expect(r.filler).toBeNull();
    expect(r.filler2).toBeNull();
  });

  test('clicking a boss hunt zone routes to its boss detail card', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.click('.tab[data-tab="tztracker"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      (window as any).renderTzTracker({ current: 'Durance of Hate Level 3', next: 'Travincal', ts: Date.now() });
      (document.querySelector('#tztracker-body .tzt-hunt[data-tz-hunt="mephisto"]') as HTMLElement)?.click();
      return {
        bossesActive: document.getElementById('tab-bosses')?.classList.contains('active'),
        meph: (document.getElementById('boss-detail-panel')?.textContent || '').includes('Mephisto'),
      };
    });
    expect(r.bossesActive).toBe(true);
    expect(r.meph).toBe(true);
  });
});
