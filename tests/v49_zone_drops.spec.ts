import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v49 — per-zone grail-drop pool. Each terror-zone detail card now lists the
// TC-reachable grail/uber unique pool, derived data-driven from ITEM_CODEX:
// an item is reachable in a zone iff tier ∈ {grail,uber}, tc > 0 (event drops
// like Annihilus at tc0 are excluded), tc <= zone.tcMax and qlvl <= zone.mlvl.
// TC87 zones (WSK / Halls / River of Flame) uniquely unlock the 3 TC87-only
// trophies; tc85 zones cap at the TC85 elite ceiling; Catacombs L4 (tc75)
// reaches no elite pool at all.
test.describe('v49 zone grail-drops — data-driven pool from ITEM_CODEX', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('zoneGrailDrops / zoneDropBlockHtml are exposed', async ({ page }) => {
    const t = await page.evaluate(() => ({
      grail: typeof (window as any).zoneGrailDrops,
      block: typeof (window as any).zoneDropBlockHtml,
    }));
    expect(t.grail).toBe('function');
    expect(t.block).toBe('function');
  });

  test('a TC87 zone exposes exactly the 3 TC87-only trophies; tc85 zone has none', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87)!;
      const tc85 = ZS.find((z) => z.tcMax === 85)!;
      const pick87 = (window as any).zoneGrailDrops(tc87);
      const pick85 = (window as any).zoneGrailDrops(tc85);
      return {
        excl87: pick87.filter((d: any) => d.tc >= 86).map((d: any) => d.name).sort(),
        excl85: pick85.filter((d: any) => d.tc >= 86).length,
        len87: pick87.length,
        len85: pick85.length,
      };
    });
    expect(r.excl87).toEqual([
      "Schaefer's Hammer", "Templar's Might", "Tyrael's Might",
    ].sort());
    expect(r.excl85).toBe(0);
    // TC87 pool strictly supersets the tc85 pool
    expect(r.len87).toBeGreaterThan(r.len85);
  });

  test('Annihilus (tier=uber but tc0 event drop) is NEVER in any zone pool', async ({ page }) => {
    const bad = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const offenders: string[] = [];
      for (const z of ZS) {
        const pool = (window as any).zoneGrailDrops(z);
        if (pool.some((d: any) => d.name === 'Annihilus')) offenders.push(z.name);
      }
      return offenders;
    });
    expect(bad).toEqual([]);
  });

  test('Catacombs L4 (tc75) reaches NO TC85 elite pool', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const cata = ZS.find((z) => z.tcMax < 85);
      if (!cata) return null;
      const pool = (window as any).zoneGrailDrops(cata);
      return {
        name: cata.name,
        elite: pool.filter((d: any) => d.tc >= 84).length,
      };
    });
    expect(r).not.toBeNull();
    expect(r!.elite).toBe(0);
  });

  test('drop block renders in the zone detail card with the trophy header, no undefined', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87)!;
      const html = (window as any).zoneDropBlockHtml(tc87);
      return {
        hasHead: /grail-eligible uniques reachable/.test(html),
        hasTc87Lab: /TC87-only/.test(html),
        hasUberChip: /class="zd-item uber"/.test(html),
        hasUndefined: /undefined/.test(html),
      };
    });
    expect(r.hasHead).toBe(true);
    expect(r.hasTc87Lab).toBe(true);
    expect(r.hasUberChip).toBe(true);
    expect(r.hasUndefined).toBe(false);
  });
});
