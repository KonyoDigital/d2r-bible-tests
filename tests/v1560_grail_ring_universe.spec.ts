import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1560 — 60% ON THE CLOSED ROW, 37% ONE CLICK INSIDE IT.
//
// The Grail Progress section header carries a peek (#grail-peek, filled from window.funiScan) that
// read 243 / 403 · 60%. Opening that same section revealed a ring saying 37% and "31 / 83 grails
// owned". Same heading, one click apart, a 4.9x smaller denominator — because the ring was a FOURTH
// tier filter (grail+uber) while the Forge, the peek, the console meter and the hero all count the
// chronicle's own 403.
//
// Verified live before the fix: ringUniverse 83, ringHave 31, ringPct 37 vs forge 243/403 = 60%.

const boot = async (page: any) => {
  await page.goto(URL);
  await page.waitForTimeout(2200);
};

test.describe('v1560 — one grail, one denominator', () => {
  test('★ the ring and the section header it lives under agree', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const peek = (document.getElementById('grail-peek') || ({} as any)).textContent || '';
      const ring = (document.getElementById('gp-circle-text') || ({} as any)).textContent || '';
      const s: any = (window as any).funiScan();
      return { peek: peek.replace(/\s+/g, ''), ring: ring.trim(),
        truth: Math.round(s.found / (s.chronTotal || s.total) * 100) + '%' };
    });
    expect(r.ring, 'the ring must show the chronicle percentage').toBe(r.truth);
    expect(r.peek, 'and the header peek must carry the same one').toContain(r.truth);
  });

  test('★ the detail line counts the same universe as the ring', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const s: any = (window as any).funiScan();
      return { detail: (document.getElementById('gp-detail') || ({} as any)).textContent || '',
        found: s.found, total: s.chronTotal || s.total };
    });
    expect(r.detail, 'it said "31 / 83" under a header saying 243/403')
      .toContain(r.found + ' / ' + r.total);
  });

  test('★ the hero sub-line stops printing a third number', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const s: any = (window as any).funiScan();
      return { sub: (document.getElementById('hero-sub') || ({} as any)).textContent || '', found: s.found };
    });
    if (r.sub) expect(r.sub, '"✓ 31 owned" sat inches under a header saying 243')
      .toContain('✓ ' + r.found + ' owned');
  });

  test('the TIER BREAKDOWN keeps its own sub-pools — a stated scope is not a contradiction', async ({ page }) => {
    // those rows are labelled "🔱 Uber / elite uniques" and "💍 Grail uniques", so a smaller
    // denominator there is honest. Only the unlabelled headline number had to change.
    await boot(page);
    const txt = await page.evaluate(() =>
      (document.getElementById('gp-tier-breakdown') || ({} as any)).textContent || '');
    expect(txt.length, 'the breakdown must still render').toBeGreaterThan(0);
    expect(txt).toMatch(/Uber|elite|Grail/i);
  });

  test('★ GRAIL COMPLETE cannot fire while the chronicle is unfinished', async ({ page }) => {
    // it used to celebrate at 83/83 with ~320 rows still missing, because `total` was the sub-pool
    await boot(page);
    const r = await page.evaluate(() => {
      const s: any = (window as any).funiScan();
      return { detail: (document.getElementById('gp-detail') || ({} as any)).textContent || '',
        remaining: (s.chronTotal || s.total) - s.found };
    });
    expect(r.remaining, 'this test needs an unfinished chronicle to be meaningful').toBeGreaterThan(0);
    expect(r.detail).not.toContain('GRAIL COMPLETE');
  });
});
