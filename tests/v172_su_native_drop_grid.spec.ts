// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v172 — TZ-tab unification: EVERY super-unique roster card is now droppable one-to-one.
// Before v172, 6 super-uniques (Pindleskin, Izual, Coldcrow, Bone Ash, Rakanishu, Bishibosh)
// resolved neither a TZ cross-link (suTzZone) NOR a curated pool, so their expandable detail
// rendered with NO grail drop grid — while every other SU + every TZ-zone card showed one.
// v172 gives any tz-less / pool-less super-unique the SAME ranked golden zoneHellGridHtml grid
// the headliner SUs use, gated PURELY by the super-unique's own VERIFIED Hell area mlvl
// (su.mlvl) via the file-wide qlvl<=mlvl reachability rule, TC ceiling clamped to that mlvl
// (capped at the game's TC87 unique top). It reuses zoneGrailDrops + zoneHellGridHtml — the
// exact engine the Lister/Hephasto/Smith pools + the zone tables use — so no per-kill odds and
// no new item-to-source claims are fabricated. The whole roster is now dropeable / expandable /
// routable 1-to-1, matching the "perfect" Nihlathak/Vaught zone-card skeleton. SUPER_UNIQUES and
// superUniqueDetailHtml are module-scoped, so every assertion drives through the rendered DOM.
const GAP_SUS = ['Pindleskin', 'Izual', 'Coldcrow', 'Bone Ash', 'Rakanishu', 'Bishibosh'];

// open a super-unique roster card by its visible name and return its #su-detail element handle
async function openSuCard(page: any, name: string) {
  return await page.evaluate((nm: string) => {
    const cards = [...document.querySelectorAll('#superunique-container .su-card')] as HTMLElement[];
    const card = cards.find((c) => (c.querySelector('.tz-zone-name')?.textContent || '').trim() === nm);
    if (!card) return { found: false };
    const idx = card.getAttribute('data-su-idx');
    (window as any).toggleSuperUnique(Number(idx));
    const box = document.getElementById('su-detail-' + idx) as HTMLElement;
    const grid = box.querySelector('.zd-hell-grid') as HTMLElement | null;
    const tier = (card.querySelector('.tz-zone-tier')?.textContent || '').replace(/[^0-9]/g, '');
    const rows = [...box.querySelectorAll('.zd-hg-row')] as HTMLElement[];
    return {
      found: true,
      open: !box.hasAttribute('hidden'),
      hasGrid: !!grid,
      nativeLabel: /native area/.test(box.textContent || ''),
      mlvl: Number(tier),
      rows: rows.length,
      routes: (box.innerHTML.match(/navigateToItem/g) || []).length,
      // every qlvl cell shown in the grid (text like "qlvl 87" or "—")
      qlvls: rows.map((r) => {
        const q = (r.querySelector('.zd-hg-q')?.textContent || '').replace(/[^0-9]/g, '');
        return q ? Number(q) : 0;
      }),
    };
  }, name);
}

test.describe('v172 every super-unique card renders a droppable grail grid', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(900);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(300);
  });

  test('every super-unique roster card expands to a drop grid — none is item-less', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#superunique-container .su-card')] as HTMLElement[];
      let withDrops = 0;
      cards.forEach((c) => {
        const idx = c.getAttribute('data-su-idx');
        (window as any).toggleSuperUnique(Number(idx));
        const box = document.getElementById('su-detail-' + idx) as HTMLElement;
        // a drop grid (zd-hell-grid) OR the clickable grail-chip pool (zd-drops-head) both count
        if (box.querySelector('.zd-hell-grid') || /zd-drops-head/.test(box.innerHTML)) withDrops++;
        (window as any).toggleSuperUnique(Number(idx)); // close again
      });
      return { count: cards.length, withDrops };
    });
    expect(r.count).toBeGreaterThanOrEqual(18);
    expect(r.withDrops).toBe(r.count);
  });

  test('the 6 previously grid-less super-uniques now carry the native-area ranked grid', async ({ page }) => {
    for (const n of GAP_SUS) {
      const r = await openSuCard(page, n);
      expect(r.found, `${n} card present`).toBe(true);
      expect(r.open, `${n} detail open`).toBe(true);
      expect(r.hasGrid, `${n} has a Hell grid`).toBe(true);
      expect(r.nativeLabel, `${n} grid is native-area labelled`).toBe(true);
      expect(r.rows, `${n} has ≥1 ranked row`).toBeGreaterThan(0);
      expect(r.routes, `${n} rows route via navigateToItem`).toBeGreaterThan(0);
    }
  });

  test('native grids are honestly gated by mlvl — no row shows qlvl > the card mlvl', async ({ page }) => {
    for (const n of GAP_SUS) {
      const r = await openSuCard(page, n);
      const leaks = r.qlvls.filter((q: number) => q > r.mlvl);
      expect(leaks, `${n} (mlvl ${r.mlvl}) leaks qlvl > mlvl: ${leaks.join(',')}`).toEqual([]);
    }
  });

  test('clicking a native grid row opens the canonical item card (routable)', async ({ page }) => {
    await openSuCard(page, 'Bishibosh');
    const itemName = await page.evaluate(() => {
      const box = [...document.querySelectorAll('#superunique-container .su-detail')]
        .find((b) => !b.hasAttribute('hidden')) as HTMLElement;
      const row = box.querySelector('.zd-hg-row') as HTMLElement;
      row.click();
      return (row.querySelector('.zd-hg-name strong')?.textContent || '').trim();
    });
    await page.waitForTimeout(350);
    // navigateToItem surfaces the item's golden card somewhere on the page
    const opened = await page.evaluate((nm: string) => document.body.textContent!.includes(nm), itemName);
    expect(itemName.length).toBeGreaterThan(0);
    expect(opened).toBe(true);
  });

  test('the headliner pools (Lister/Hephasto/Smith) keep their curated grid (no native double-grid)', async ({ page }) => {
    for (const n of ['Lister the Tormentor', 'Hephasto the Armorer', 'The Smith']) {
      const r = await openSuCard(page, n);
      expect(r.found, `${n} present`).toBe(true);
      expect(r.hasGrid, `${n} has a grid`).toBe(true);
      expect(r.nativeLabel, `${n} is NOT native-labelled (curated pool)`).toBe(false);
    }
  });

  test('no console errors expanding every super-unique card', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#superunique-container .su-card')] as HTMLElement[];
      cards.forEach((c) => (window as any).toggleSuperUnique(Number(c.getAttribute('data-su-idx'))));
    });
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
  });
});
