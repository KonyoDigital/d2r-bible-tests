import { test, expect } from '@playwright/test';

// v234 — TZ TRACKER 48h history (KV-backed). The /api/tz Pages Function records
// each rotation into Cloudflare KV (deduped by 30-min slot, kept 48h) and returns
// it as `history`. The tab renders an expandable <details> log: huntable windows
// glow gold + route to their card, filler stays dimmed, grouped by day. Under
// file:// there's no fetch (offline) — the panel renders from cache / a note.

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v234 TZ history', () => {
  test('the expandable history exists and renders rows from data (hunt vs filler, day groups, clickable)', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push('PE ' + e.message));
    await page.goto(URL);
    await page.waitForTimeout(1100);
    await page.click('.tab[data-tab="tztracker"]');
    await page.waitForTimeout(300);

    const now = Math.floor(Date.now() / 1800000) * 1800000;
    const r = await page.evaluate((now) => {
      const hist = [
        { slot: now, zone: 'Travincal' },
        { slot: now - 1800000, zone: 'Cold Plains and The Cave' },
        { slot: now - 3600000, zone: 'River of Flame and City of the Damned' },
        { slot: now - 86400000, zone: 'Durance of Hate Level 2 and 3' }, // yesterday → new day group
      ];
      (window as any).renderTzHistory(hist);
      const body = document.getElementById('tzt-history-body')!;
      return {
        isDetails: document.getElementById('tzt-history')?.tagName === 'DETAILS',
        rows: body.querySelectorAll('.tzt-hist-row').length,
        hunts: body.querySelectorAll('.tzt-hist-row.tzt-hunt').length,
        days: body.querySelectorAll('.tzt-hist-day').length,
        nowMarked: body.querySelectorAll('.tzt-hist-row.tzt-now').length,
        count: document.getElementById('tzt-history-count')?.textContent,
        firstHuntId: body.querySelector('.tzt-hist-row.tzt-hunt')?.getAttribute('role'),
      };
    }, now);
    expect(r.isDetails).toBe(true);
    expect(r.rows).toBe(4);
    expect(r.hunts).toBe(3);              // Travincal + River(Hephasto) + Durance(Meph); Cold Plains filler
    expect(r.days).toBe(2);               // today + yesterday
    expect(r.nowMarked).toBe(1);          // the current slot row flagged
    /* v1584 replaced the word deliberately: the summary counts PRIME windows, not "huntable"
       ones. "Huntable" only counted the fourteen hardcoded bosses, so two days full of
       density-2200 tomb hours read "0 huntable" and looked like a dead log. It now reads
       "<n> slots · <n> worth running". Assert the SHAPE, not just a word, so a summary that
       silently stops counting still fails here. */
    expect(r.count).toMatch(/^\d+ slots · \d+ worth running$/);
    expect(r.firstHuntId).toBe('button'); // hunt rows are clickable
    expect(errs).toEqual([]);
  });

  test('clicking a history hunt row routes to its card', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.click('.tab[data-tab="tztracker"]');
    await page.waitForTimeout(300);
    const routed = await page.evaluate(() => {
      const now = Math.floor(Date.now() / 1800000) * 1800000;
      (window as any).renderTzHistory([{ slot: now, zone: 'Travincal' }]);
      (document.querySelector('#tzt-history-body .tzt-hist-row.tzt-hunt') as HTMLElement)?.click();
      return document.getElementById('tab-bosses')?.classList.contains('active');
    });
    expect(routed).toBe(true);
  });

  test('empty history shows a graceful recording note (no crash)', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.click('.tab[data-tab="tztracker"]');
    await page.waitForTimeout(300);
    const txt = await page.evaluate(() => {
      (window as any).renderTzHistory([]);
      return (document.getElementById('tzt-history-body')?.textContent || '').toLowerCase();
    });
    expect(txt).toContain('recording');
  });
});
