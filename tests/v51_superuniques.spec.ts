import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v51 — dedicated Super-Uniques reference section inside the TZ subtab. The gold-name
// bosses a TZ alert calls out (Eldritch, Shenk, Pindleskin, …) previously lived only as
// inline strings in TZ_ZONES[].unique. This builds them out as a SUPER_UNIQUES dataset
// (act/area + canonical Hell area mlvl + fixed immunities + DClone-camp eligibility)
// rendered as clickable droppable-box cards matching the zone-card pattern, with a live
// cross-link to the TZ_ZONES entry each one spawns in (no hardcoded join — suTzZone()
// matches on the zone's `unique` string so the two lists never drift). No per-kill odds
// are fabricated. This spec locks the data + render + cross-reference.
test.describe('v51 super-uniques section + TZ cross-reference', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(150);
  });

  test('section renders under the TZ tab with one card per super-unique, no undefined', async ({ page }) => {
    const r = await page.evaluate(() => {
      const data = (SUPER_UNIQUES as any[]);
      const cards = [...document.querySelectorAll('#superunique-container .su-card')];
      const tabText = (document.getElementById('tab-tz') as HTMLElement).innerText;
      return {
        dataLen: data.length,
        cardLen: cards.length,
        hasHeader: /Super-Uniques — the named bosses/.test(tabText),
        names: cards.map((c) => c.querySelector('.tz-zone-name')!.textContent!.trim()),
        hasUndefined: cards.some((c) => /undefined/.test(c.innerHTML)),
        renderFn: typeof (window as any).renderSuperUniques,
        toggleFn: typeof (window as any).toggleSuperUnique,
        suTzFn: typeof (window as any).suTzZone,
      };
    });
    expect(r.renderFn).toBe('function');
    expect(r.toggleFn).toBe('function');
    expect(r.suTzFn).toBe('function');
    expect(r.dataLen).toBeGreaterThanOrEqual(15);
    expect(r.cardLen).toBe(r.dataLen);
    expect(r.hasHeader).toBe(true);
    expect(r.hasUndefined).toBe(false);
    // the alert's headliners must all be present
    expect(r.names).toContain('Eldritch the Rectifier');
    expect(r.names).toContain('Shenk the Overseer');
    expect(r.names).toContain('Pindleskin');
  });

  test('suTzZone cross-links each super-unique to the zone whose unique-string names it', async ({ page }) => {
    const r = await page.evaluate(() => {
      const data = (SUPER_UNIQUES as any[]);
      const suTz = (window as any).suTzZone;
      const eld = data.find((s) => s.name === 'Eldritch the Rectifier');
      const endugu = data.find((s) => /Endugu/.test(s.name));
      const pindle = data.find((s) => s.name === 'Pindleskin');
      const matchZone = (s: any) => { const m = suTz(s); return m ? m.z.name : null; };
      // every entry whose tzMatch token appears in a zone unique-string must resolve
      const unmatchedButShould = data.filter((s) => {
        const m = suTz(s);
        const inAnyZone = (TZ_ZONES as any[]).some((z) => (z.unique || '').toLowerCase().includes((s.tzMatch || s.name).toLowerCase()));
        return inAnyZone && !m;
      }).map((s) => s.name);
      return {
        eldZone: matchZone(eld),
        enduguZone: matchZone(endugu),
        pindleZone: matchZone(pindle),       // Pindle is run on-demand, not in TZ_ZONES list
        unmatchedButShould,
      };
    });
    expect(r.eldZone).toMatch(/Crystalline Passage/);
    expect(r.enduguZone).toMatch(/Flayer Dungeon/);
    expect(r.pindleZone).toBeNull();
    expect(r.unmatchedButShould).toEqual([]);
  });

  test('clicking a card opens its droppable detail with cross-link + DClone note', async ({ page }) => {
    const html = await page.evaluate(() => {
      const data = (SUPER_UNIQUES as any[]);
      const si = data.findIndex((s) => s.name === 'Eldritch the Rectifier');
      (window as any).toggleSuperUnique(si);
      const box = document.getElementById('su-detail-' + si)!;
      return { open: !box.hasAttribute('hidden'), inner: box.innerHTML };
    });
    expect(html.open).toBe(true);
    expect(html.inner).toMatch(/super-unique detail/);
    expect(html.inner).toMatch(/Crystalline Passage/);          // live TZ cross-link
    expect(html.inner).toMatch(/grail uniques reachable/);      // pool count from zoneGrailDrops
    expect(html.inner).toMatch(/Diablo Walks the Earth/);        // DClone note (Eldritch is a camp spot)
    expect(html.inner).not.toMatch(/undefined/);
  });

  test('boss-backed super-uniques (Pindleskin/Nihlathak/Summoner) expose a full-table cross-link', async ({ page }) => {
    const r = await page.evaluate(() => {
      const data = (SUPER_UNIQUES as any[]);
      const detail = (window as any).superUniqueDetailHtml;
      const html = (name: string) => detail(data.find((s) => s.name === name));
      return {
        pindle: /openBossDetail\('pindle'\)/.test(html('Pindleskin')),
        nihl: /openBossDetail\('nihlathak'\)/.test(html('Nihlathak')),
        summ: /openBossDetail\('summoner'\)/.test(html('The Summoner')),
        // a non-boss super-unique must NOT fabricate a boss link
        eldNoBoss: !/openBossDetail/.test(html('Eldritch the Rectifier')),
      };
    });
    expect(r.pindle).toBe(true);
    expect(r.nihl).toBe(true);
    expect(r.summ).toBe(true);
    expect(r.eldNoBoss).toBe(true);
  });

  test('canonical data integrity: DClone campers flagged, Hell mlvls sane, no fabricated odds', async ({ page }) => {
    const r = await page.evaluate(() => {
      const data = (SUPER_UNIQUES as any[]);
      const byName = Object.fromEntries(data.map((s) => [s.name, s]));
      return {
        pindleMlvl: byName['Pindleskin'].mlvl,                 // famous mlvl-86 monster
        eldDclone: byName['Eldritch the Rectifier'].dclone,
        shenkDclone: byName['Shenk the Overseer'].dclone,
        frozenCold: byName['Frozenstein'].immune,
        mlvlRange: data.every((s) => s.mlvl >= 70 && s.mlvl <= 96),
        // honesty: every detail card carries the pending-odds caveat, never a fake 1:N
        allCaveated: data.every((s) => /pending silospen pull/.test((window as any).superUniqueDetailHtml(s))),
      };
    });
    expect(r.pindleMlvl).toBe(86);
    expect(r.eldDclone).toBe(true);
    expect(r.shenkDclone).toBe(true);
    expect(r.frozenCold).toMatch(/Cold/);
    expect(r.mlvlRange).toBe(true);
    expect(r.allCaveated).toBe(true);
  });

  test('no console errors on load with the new section', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
  });
});
