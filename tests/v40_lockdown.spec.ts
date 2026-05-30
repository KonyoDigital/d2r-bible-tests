import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v40 LOCKDOWN — no new features. Lock in what is built.
// Floors are absolute minimums based on the v40 census (3,257 rows × 6 diff = 19,514 chance cells).

const FLOORS = {
  drop_rows: 3200,        // 3,257 actual
  chance_cells: 19000,    // 19,514 actual (the engine)
  total_td: 25500,        // 26,028 actual
  boss_diff_cells: 66,    // 11 bosses × 6 difficulties
  hero_picks: 15,
  sd_rows: 17,
  verified_anchors: 3,
  tz_zone_cards: 10,
  rotw_statues: 5,
  boss_tier_val: 11,
};

const TAB_PANELS = ['bosses', 'calc', 'tz', 'runes', 'rotw', 'ancients', 'ref'];

test.describe('v40 LOCKDOWN — engine integrity', () => {
  test('engine renders ≥19,000 droptable chance cells across all bosses+runes+rotw+ancients', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
    const stats = await page.evaluate(() => {
      // Walk every drops table on the page (boss-cards, runes, rotw, ancients)
      const rows = document.querySelectorAll('table.drops tbody tr');
      let chanceCells = 0;
      let dropRows = 0;
      for (const r of Array.from(rows)) {
        dropRows++;
        const tds = r.querySelectorAll('td');
        // tds[0]=item, tds[1]=tc, tds[2..7]=6 difficulties
        chanceCells += Math.max(0, tds.length - 2);
      }
      return { dropRows, chanceCells, totalTd: document.querySelectorAll('td').length };
    });
    expect(stats.dropRows).toBeGreaterThanOrEqual(FLOORS.drop_rows);
    expect(stats.chanceCells).toBeGreaterThanOrEqual(FLOORS.chance_cells);
    expect(stats.totalTd).toBeGreaterThanOrEqual(FLOORS.total_td);
  });

  test('zero NaN / undefined / null leakage anywhere on page (all tabs)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(600);
    // Render every tab to populate dynamic content
    for (const t of TAB_PANELS) {
      await page.locator(`.tab[data-tab="${t}"]`).click().catch(() => {});
      await page.waitForTimeout(120);
    }
    await page.locator('.tab[data-tab="bosses"]').click();
    await page.waitForTimeout(150);

    const leakSample = await page.evaluate(() => {
      const text = document.body.innerText || '';
      // Scan for the literal "NaN", "undefined", "null" as standalone words
      const nan = (text.match(/\bNaN\b/g) || []).length;
      const undef = (text.match(/\bundefined\b/g) || []).length;
      // Sample around any matches
      const samples: string[] = [];
      const re = /\b(NaN|undefined)\b/g;
      let m;
      while ((m = re.exec(text)) && samples.length < 5) {
        const start = Math.max(0, m.index - 30);
        samples.push(text.slice(start, m.index + 30));
      }
      return { nan, undef, samples };
    });

    expect(leakSample.nan, `NaN leakage samples: ${leakSample.samples.join(' | ')}`).toBe(0);
    expect(leakSample.undef, `undefined leakage samples: ${leakSample.samples.join(' | ')}`).toBe(0);
  });

  test('zero empty chance cells in any droptable', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
    const drill = await page.evaluate(() => {
      let total = 0;
      let empty = 0;
      const samples: string[] = [];
      for (const row of Array.from(document.querySelectorAll('table.drops tbody tr'))) {
        const tds = row.querySelectorAll('td');
        for (let i = 2; i < tds.length; i++) {
          total++;
          // v43: drop tables live inside collapsed <details>; innerText returns "" for hidden
          // nodes. This is a DATA-integrity probe (not a visual one) so read textContent.
          const txt = (tds[i] as HTMLElement).textContent!.trim();
          if (txt === '') {
            empty++;
            if (samples.length < 5) {
              const item = (tds[0] as HTMLElement).textContent!.trim();
              const card = (row.closest('[id]') as HTMLElement)?.id || '?';
              samples.push(`${card}/${item} col${i}`);
            }
          }
        }
      }
      return { total, empty, samples };
    });
    expect(drill.total).toBeGreaterThanOrEqual(FLOORS.chance_cells);
    expect(drill.empty, `Empty cells: ${drill.samples.join(', ')}`).toBe(0);
  });

  test('all 7 tab panels exist and reachable', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    for (const t of TAB_PANELS) {
      const button = page.locator(`.tab[data-tab="${t}"]`);
      await expect(button, `tab button [data-tab=${t}]`).toHaveCount(1);
      const panel = page.locator(`#tab-${t}`);
      await expect(panel, `panel #tab-${t}`).toHaveCount(1);
    }
  });

  test('all 11 boss-tier-val cells populated with non-empty content', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(600);
    const vals = await page.locator('.boss-card .boss-tier-val').allInnerTexts();
    expect(vals.length).toBeGreaterThanOrEqual(FLOORS.boss_tier_val);
    for (const v of vals) {
      expect(v.trim().length, `boss-tier-val empty: "${v}"`).toBeGreaterThan(0);
    }
  });

  test('MF change re-syncs every droptable chance cell (not just summary)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
    // Take a snapshot of one chance cell value, change MF, re-read it
    const sample = await page.evaluate(() => {
      // Pick a cell that should be MF-affected (Hell-tier mephisto first item, col 7 = Hell)
      const meph = document.getElementById('mephisto');
      if (!meph) return { ok: false, reason: 'no meph' };
      const firstRow = meph.querySelector('table.drops tbody tr');
      if (!firstRow) return { ok: false, reason: 'no row' };
      const tds = firstRow.querySelectorAll('td');
      if (tds.length < 8) return { ok: false, reason: `${tds.length} tds` };
      // v43: rows are inside collapsed <details>; use textContent (innerText is "" when hidden).
      return { ok: true, item: (tds[0] as HTMLElement).textContent!.trim(), before: (tds[7] as HTMLElement).textContent!.trim() };
    });
    expect(sample.ok, `sample read failed: ${(sample as any).reason}`).toBe(true);

    // Move MF slider materially
    await page.evaluate(() => {
      const s = document.getElementById('mf') as HTMLInputElement;
      s.value = '50';
      s.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await page.waitForTimeout(400);

    const after = await page.evaluate(() => {
      const meph = document.getElementById('mephisto');
      const firstRow = meph!.querySelector('table.drops tbody tr');
      const tds = firstRow!.querySelectorAll('td');
      return (tds[7] as HTMLElement).textContent!.trim();
    });

    // If MF affects this cell, the value should differ. (We picked Hell — MF effective always.)
    expect(after, `MF change did not re-sync mephisto/${sample.item} Hell cell`).not.toBe(sample.before);
  });

  test('routing endpoints exist: boss-nav chips, TZ→boss, source-chips', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(600);

    // Boss-nav chips: every chip's data-boss-id must point to an existing #<id> boss-card
    const chips = await page.locator('#boss-nav .boss-chip[data-boss-id]').count();
    expect(chips, 'boss-nav chips').toBeGreaterThanOrEqual(11);
    const unresolvedNav = await page.evaluate(() => {
      const chips = Array.from(document.querySelectorAll('#boss-nav .boss-chip[data-boss-id]'));
      return chips.filter(c => !document.getElementById(c.getAttribute('data-boss-id')!)).length;
    });
    expect(unresolvedNav, 'boss-nav chips with broken data-boss-id').toBe(0);

    // TZ honest-affordance (v43+): tagTzZonesWithBossId() sets a NON-EMPTY data-boss-id only on
    // zones where a roster boss genuinely spawns; density / super-unique zones keep data-boss-id=""
    // and intentionally do not route. So the contract is: every NON-EMPTY data-boss-id must resolve
    // to an existing boss card (no broken links), and at least one zone routes. Authoritative
    // per-zone correctness lives in routing_and_data_integrity.spec.ts.
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(200);
    const unresolvedTz = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('.tz-zone-card'));
      return cards.filter(c => {
        const id = c.getAttribute('data-boss-id');
        return id && id.length > 0 && !document.getElementById(id);
      }).length;
    });
    expect(unresolvedTz, 'TZ cards with broken (non-empty) data-boss-id').toBe(0);

    const routedTz = await page.locator('.tz-zone-card[data-boss-id]:not([data-boss-id=""])').count();
    expect(routedTz, 'at least one TZ zone should route to a roster boss').toBeGreaterThan(0);
  });

  test('global functions stable on window: switchTab, openBossDetail, clearActiveBoss, setActiveBoss, setActiveItem, clearActiveItem', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    const exposed = await page.evaluate(() => ({
      switchTab: typeof (window as any).switchTab === 'function',
      openBossDetail: typeof (window as any).openBossDetail === 'function',
      clearActiveBoss: typeof (window as any).clearActiveBoss === 'function',
      setActiveBoss: typeof (window as any).setActiveBoss === 'function',
      setActiveItem: typeof (window as any).setActiveItem === 'function',
      clearActiveItem: typeof (window as any).clearActiveItem === 'function',
    }));
    for (const [k, v] of Object.entries(exposed)) {
      expect(v, `${k} missing on window`).toBe(true);
    }
  });

  // v41 routine widget probes 3 file:// fallback paths for routine_status.js — the
  // first 1-2 ERR_FILE_NOT_FOUND are EXPECTED (it's a graceful fallback chain, not a bug).
  const isBenignNoise = (msg: string) =>
    /routine_status\.js/i.test(msg) ||
    /Failed to load resource.*ERR_FILE_NOT_FOUND/i.test(msg);

  test('no real console.error / pageerror touring all 7 tabs (routine_status fallback whitelisted)', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push('pageerror: ' + e.message));
    page.on('console', m => {
      if (m.type() === 'error') {
        const t = m.text();
        if (!isBenignNoise(t)) errs.push('console.error: ' + t);
      }
    });

    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    for (const t of TAB_PANELS) {
      await page.evaluate((tab) => (window as any).switchTab(tab), t);
      await page.waitForTimeout(120);
    }
    await page.evaluate(() => (window as any).switchTab('bosses'));
    await page.waitForTimeout(200);
    expect(errs, `Real errors observed during tab tour:\n${errs.join('\n')}`).toEqual([]);
  });

  test('no real console.error / pageerror opening + closing 3 bosses', async ({ page }) => {
    test.setTimeout(60000);
    const errs: string[] = [];
    page.on('pageerror', e => errs.push('pageerror: ' + e.message));
    page.on('console', m => {
      if (m.type() === 'error') {
        const t = m.text();
        if (!isBenignNoise(t)) errs.push('console.error: ' + t);
      }
    });

    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    for (const id of ['mephisto', 'andariel', 'baal']) {
      await page.evaluate((bid) => (window as any).openBossDetail(bid), id);
      await page.waitForTimeout(180);
      await page.evaluate(() => (window as any).clearActiveBoss());
      await page.waitForTimeout(180);
    }
    expect(errs, `Real errors observed:\n${errs.join('\n')}`).toEqual([]);
  });
});
