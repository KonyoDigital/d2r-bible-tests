// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v175 — droppable-grid coverage LOCKDOWN. This is a consistency ratchet, not a
// feature: it pins the invariant that EVERY entity with a real multi-item RNG
// grail pool surfaces the SAME golden Top-Drops grid (one source = bossTopDropsHtml
// off BOSSES[].dropTable + the live effChance engine), while entities that honestly
// have NO rare pool (The Summoner: 0 grail rows) — or whose "drop" is a single
// guaranteed item (Über Diablo → the Annihilus ALWAYS drops, so a rarest-first odds
// grid would be LESS honest, not more) — are allowlisted with their reason. A NEW
// grail-pool boss that ships grid-less, or a regression that blanks an existing
// boss grid, fails this. The cow event card's inline grid (v174) and every
// super-unique's grid (v172) are cross-checked here so the whole "dropeable"
// surface is locked from one place.

// bosses whose lack of a multi-item rarity grid is intentional + honest
const GRIDLESS_OK: Record<string, string> = {
  summoner: 'no grail/uber drops in pool — nothing to rank',
  dclone: 'single guaranteed drop (Annihilus ALWAYS drops) — a rarity grid would misrepresent it',
};

test.describe('v175 droppable golden-grid coverage lockdown', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('every boss with a multi-item grail pool renders the Top-Drops grid', async ({ page }) => {
    const rows = await page.evaluate(() => {
      const B = (BOSSES as any[]);
      return B.map((b) => {
        const grail = (b.dropTable || []).filter((d: any) => d.tier === 'grail' || d.tier === 'uber').length;
        let html = '';
        try { html = (window as any).bossTopDropsHtml(b, 20); } catch (e) { html = 'ERR'; }
        return { id: b.id, grail, rendersGrid: /top-drop-row/.test(html), err: html === 'ERR' };
      });
    });
    for (const r of rows) {
      expect(r.err, `${r.id} bossTopDropsHtml threw`).toBe(false);
      if (r.grail >= 2) {
        // a real RNG pool MUST surface the golden grid
        expect(r.rendersGrid, `${r.id} (grail=${r.grail}) is grail-rich but renders NO grid`).toBe(true);
      } else {
        // grid-less is only allowed for explicitly-reasoned entities
        if (!r.rendersGrid) {
          expect(Object.keys(GRIDLESS_OK), `${r.id} is grid-less but NOT on the honest allowlist`).toContain(r.id);
        }
      }
    }
  });

  test('the gridless allowlist is honest — each allowlisted boss really has <2 grail rows', async ({ page }) => {
    const counts = await page.evaluate((ids: string[]) => {
      const B = (BOSSES as any[]);
      return ids.map((id) => {
        const b = B.find((x) => x.id === id);
        return { id, found: !!b, grail: b ? (b.dropTable || []).filter((d: any) => d.tier === 'grail' || d.tier === 'uber').length : -1 };
      });
    }, Object.keys(GRIDLESS_OK));
    for (const c of counts) {
      expect(c.found, `${c.id} allowlisted but not a real boss id`).toBe(true);
      expect(c.grail, `${c.id} allowlisted as gridless but has ${c.grail} grail rows`).toBeLessThan(2);
    }
  });

  test('the cow event card surfaces the inline grail grid (v174 single-source link)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const host = document.getElementById('cow-grail-grid');
      return {
        present: !!host,
        rows: host ? host.querySelectorAll('.top-drop-row').length : 0,
        routes: host ? /openBossDetail\('cows'\)/.test(host.innerHTML) : false,
      };
    });
    expect(r.present).toBe(true);
    expect(r.rows).toBeGreaterThan(0);
    expect(r.routes).toBe(true);
  });

  test('every super-unique roster card is droppable — none is grid-less (v172 cross-check)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#superunique-container .su-card')] as HTMLElement[];
      let withDrops = 0;
      cards.forEach((c) => {
        const idx = c.getAttribute('data-su-idx');
        (window as any).toggleSuperUnique(Number(idx));
        const box = document.getElementById('su-detail-' + idx) as HTMLElement;
        if (box.querySelector('.zd-hell-grid') || /zd-drops-head/.test(box.innerHTML)) withDrops++;
        (window as any).toggleSuperUnique(Number(idx));
      });
      return { count: cards.length, withDrops };
    });
    expect(r.count).toBeGreaterThanOrEqual(18);
    expect(r.withDrops).toBe(r.count);
  });

  test('no console errors across the full droppable-surface audit', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      (BOSSES as any[]).forEach((b) => { try { (window as any).bossTopDropsHtml(b, 20); } catch (e) {} });
      (window as any).renderCowGrailGrid && (window as any).renderCowGrailGrid();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
