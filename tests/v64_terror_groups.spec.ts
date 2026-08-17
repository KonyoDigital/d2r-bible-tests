// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v64 — TERROR_GROUPS act-region grouping + nested super-unique ID-card roster. The flat
// TZ_ZONES list is now bucketed under per-act group headers (presentation-only over the
// single TZ_ZONES source — every zone keeps its original index for routing). Inside each
// zone's drop detail, every super-unique that suTzZone()-resolves to that zone renders as a
// clickable mini ID-card that routes (jumpToSuperUnique) to the SAME canonical super-unique
// detail the #superunique-container cards open — closing the previously-untested routing
// gap. This spec locks the grouping, the index-preservation, the nesting, and the routing.
test.describe('v64 terror groups + nested super-unique routing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(150);
  });

  test('TERROR_GROUPS buckets every TZ zone under act-region headers, no zone lost', async ({ page }) => {
    const r = await page.evaluate(() => {
      const groups = (TERROR_GROUPS as any[]);
      const heads = [...document.querySelectorAll('#tz-zones-container .tz-group-head')];
      const cards = [...document.querySelectorAll('#tz-zones-container .tz-zone-card')];
      // sum of every zone matched by exactly one group must equal TZ_ZONES.length
      const matchCounts = (TZ_ZONES as any[]).map((z) =>
        groups.filter((g) => g.match(z)).length);
      return {
        groupLen: groups.length,
        headLen: heads.length,
        cardLen: cards.length,
        zoneLen: (TZ_ZONES as any[]).length,
        everyZoneMatchedOnce: matchCounts.every((c) => c === 1),
        headActs: heads.map((h) => h.querySelector('.tz-group-act')!.textContent!.trim()),
        cardFn: typeof (window as any).tzZoneCardHtml,
        rosterFn: typeof (window as any).zoneSuRosterHtml,
        hasUndefined: heads.some((h) => /undefined/.test(h.innerHTML)),
      };
    });
    expect(r.groupLen).toBeGreaterThanOrEqual(5);
    expect(r.cardLen).toBe(r.zoneLen);              // every zone still rendered
    expect(r.headLen).toBeGreaterThanOrEqual(4);    // at least one head per populated act
    expect(r.everyZoneMatchedOnce).toBe(true);      // no zone double-bucketed or orphaned
    expect(r.headActs).toContain('Act 1');
    expect(r.headActs).toContain('Act 5');
    expect(r.cardFn).toBe('function');
    expect(r.rosterFn).toBe('function');
    expect(r.hasUndefined).toBe(false);
  });

  test('grouping is presentation-only: each card keeps its TZ_ZONES index for routing', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#tz-zones-container .tz-zone-card')] as HTMLElement[];
      // every card's data-zone-idx must resolve to the zone whose name it shows
      const mismatches = cards.filter((c) => {
        const zi = parseInt(c.getAttribute('data-zone-idx') || '-1', 10);
        const name = c.querySelector('.tz-zone-name')!.textContent!.trim();
        return !(TZ_ZONES as any[])[zi] || (TZ_ZONES as any[])[zi].name !== name;
      }).map((c) => c.querySelector('.tz-zone-name')!.textContent!.trim());
      const idxs = cards.map((c) => parseInt(c.getAttribute('data-zone-idx') || '-1', 10)).sort((a, b) => a - b);
      return { mismatches, idxs, zoneLen: (TZ_ZONES as any[]).length };
    });
    expect(r.mismatches).toEqual([]);
    // the rendered indices are exactly 0..N-1 (every zone, each once)
    expect(r.idxs).toEqual([...Array(r.zoneLen).keys()]);
  });

  test('zone detail nests a clickable ID-card per super-unique that spawns there', async ({ page }) => {
    const r = await page.evaluate(() => {
      // Bloody Foothills + Frigid Highlands zone hosts Shenk + Eldritch
      const zi = (TZ_ZONES as any[]).findIndex((z) => /Bloody Foothills/.test(z.name));
      (window as any).toggleZoneDetail(zi);
      const box = document.getElementById('tz-zone-detail-' + zi)!;
      const suCards = [...box.querySelectorAll('.zd-su-card')] as HTMLElement[];
      return {
        zi,
        open: !box.hasAttribute('hidden'),
        count: suCards.length,
        names: suCards.map((c) => c.querySelector('.zd-su-card-name')!.textContent!.trim()),
        routes: suCards.every((c) => /jumpToSuperUnique\(\d+\)/.test(c.getAttribute('onclick') || '')),
        stopsProp: suCards.every((c) => /stopPropagation/.test(c.getAttribute('onclick') || '')),
        hasUndefined: /undefined/.test(box.innerHTML),
      };
    });
    expect(r.open).toBe(true);
    expect(r.count).toBeGreaterThanOrEqual(2);
    expect(r.names.join(' ')).toMatch(/Shenk/);
    expect(r.names.join(' ')).toMatch(/Eldritch/);
    expect(r.routes).toBe(true);          // each mini-card routes via jumpToSuperUnique
    expect(r.stopsProp).toBe(true);       // and won't collapse the zone box
    expect(r.hasUndefined).toBe(false);
  });

  test('clicking a nested SU card routes to its canonical super-unique detail', async ({ page }) => {
    // open the Bloody Foothills zone, click the nested Eldritch ID-card
    const zi = await page.evaluate(() =>
      (TZ_ZONES as any[]).findIndex((z) => /Bloody Foothills/.test(z.name)));
    await page.evaluate((zi) => (window as any).toggleZoneDetail(zi), zi);
    await page.waitForTimeout(120);
    const eldSi = await page.evaluate(() =>
      (SUPER_UNIQUES as any[]).findIndex((s) => s.name === 'Eldritch the Rectifier'));
    await page.locator(`#tz-zone-detail-${zi} .zd-su-card[data-su-idx="${eldSi}"]`).click();
    await page.waitForTimeout(250);
    const r = await page.evaluate((eldSi) => {
      const det = document.getElementById('su-detail-' + eldSi)!;
      return { open: !det.hasAttribute('hidden'), inner: det.innerHTML };
    }, eldSi);
    expect(r.open).toBe(true);                              // canonical SU card opened
    expect(r.inner).toMatch(/super-unique detail/);
    expect(r.inner).toMatch(/Eldritch the Rectifier/);
  });

  test('jumpToSuperUnique is exposed and routes by index (coverage for the routing helper)', async ({ page }) => {
    const r = await page.evaluate(async () => {
      const fn = (window as any).jumpToSuperUnique;
      const si = (SUPER_UNIQUES as any[]).findIndex((s) => s.name === 'Shenk the Overseer');
      fn(si);
      await new Promise((res) => setTimeout(res, 200));
      const det = document.getElementById('su-detail-' + si)!;
      return {
        type: typeof fn,
        byNameType: typeof (window as any).jumpToSuperUniqueByName,
        open: !det.hasAttribute('hidden'),
        onTzTab: !document.getElementById('tab-tz')!.hasAttribute('hidden'),
      };
    });
    expect(r.type).toBe('function');
    expect(r.byNameType).toBe('function');
    expect(r.open).toBe(true);
    expect(r.onTzTab).toBe(true);
  });

  test('no console errors on load with grouped TZ + nested rosters', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(200);
    // open a couple of details to exercise the nested roster render path
    await page.evaluate(() => {
      const zi = (TZ_ZONES as any[]).findIndex((z) => /Bloody Foothills/.test(z.name));
      (window as any).toggleZoneDetail(zi);
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
