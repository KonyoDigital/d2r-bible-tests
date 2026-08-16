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

  /* v1732 — this test used to read "Catacombs L4 (tc75) reaches NO TC85 elite pool", and it
     located its subject as `ZS.find(z => z.tcMax < 85)`. Catacombs L4 was the ONLY zone below 85,
     so that find() was a de-facto name lookup. Its stored 75/75 turned out to be the stale
     figure — every other Hell TZ read mlvl 96, and a live silospen pull gave Catacombs a pool of
     79 grail items, not 7. Raising it to 96/87 left this test looking for a zone that no longer
     exists: `find` returned undefined and the subject silently vanished.

     So it is now the invariant it was always reaching for, applied to EVERY zone rather than to
     the one zone that happened to instantiate it: no zone may show an item above its own ceiling.
     A single-subject test that its own fix deletes was never pinning the rule. */
  /* The obvious replacement — "no zone pool contains an item above that zone tcMax" — was WRITTEN,
     RUN, and DELETED, because it cannot fail. `zoneGrailDrops()` builds the pool BY filtering on
     tcMax, so an item above the ceiling is unconstructible: forcing Catacombs to TC60 shrank its
     pool from 79 to 4 and still yielded zero violations. It would have shipped as a green ★★★ gate
     protecting nothing. Recorded rather than quietly dropped, because the next person to look at
     this file will have the same idea. [[feedback-blind-fixture-green-gate]]

     What the real defect actually violated is terror SATURATION: every Hell terror zone is lifted
     to mlvl 96, and Catacombs L4 alone stored 75. That is a claim about the data, not about a
     filter, so it can and does go red. */
  test('★★★ every Hell terror zone is saturated to mlvl 96 with a known ceiling', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      return {
        zones: ZS.length,
        notSaturated: ZS.filter((z) => z.mlvl !== 96).map((z) => `${z.name} = mlvl ${z.mlvl}`),
        oddCeiling: ZS.filter((z) => z.tcMax !== 87 && z.tcMax !== 85).map((z) => `${z.name} = TC${z.tcMax}`),
        below: ZS.filter((z) => z.tcMax < 87).map((z) => z.name),
      };
    });
    expect(r.zones, 'no zones were read').toBeGreaterThan(8);
    expect(r.notSaturated, 'Hell TZ zones not at mlvl 96: ' + r.notSaturated.join(', ')).toEqual([]);
    expect(r.oddCeiling, 'zone ceilings that are neither 85 nor 87: ' + r.oddCeiling.join(', ')).toEqual([]);
    /* Arcane Sanctuary is the ONE zone legitimately below the top ceiling — its dweller tops out
       at TC78, so it was deliberately left at 85 when the other six were raised to 87. It is the
       control that proves the raise was measured per-zone and not applied blanket. */
    expect(r.below, 'zones below the top ceiling').toEqual(['Arcane Sanctuary']);
  });

  /* And the specific fact that replaced the old claim, pinned so it cannot quietly revert. */
  test('★★ Catacombs L4 reaches the elite pool (it is mlvl 96 / TC87, not the stored 75/75)',
    async ({ page }) => {
    const r = await page.evaluate(() => {
      const cata = (TZ_ZONES as any[]).find((z) => /Catacombs L4/.test(z.name));
      if (!cata) return null;
      const pool = (window as any).zoneGrailDrops(cata);
      return { mlvl: cata.mlvl, tcMax: cata.tcMax, total: pool.length,
               elite: pool.filter((d: any) => d.tc >= 84).length };
    });
    expect(r, 'Catacombs L4 is gone from TZ_ZONES').not.toBeNull();
    expect(r!.mlvl).toBe(96);
    expect(r!.tcMax).toBe(87);
    expect(r!.elite, 'Catacombs reaches no elite items').toBeGreaterThan(0);
    expect(r!.total, 'Catacombs pool collapsed back toward the old 7').toBeGreaterThan(60);
  });

  test('drop block renders in the zone detail card with the trophy header, no undefined', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ZS = (TZ_ZONES as any[]);
      const tc87 = ZS.find((z) => z.tcMax >= 87)!;
      const html = (window as any).zoneDropBlockHtml(tc87);
      // CC 2026-06-01 unify: chips are now clickable (zd-item-click) → each opens
      // its canonical grail card via navigateToItem, matching the boss top-drops.
      const uberChip = (html.match(/<span class="zd-item[^"]*uber[^"]*"[^>]*>/) || [''])[0];
      return {
        hasHead: /grail-eligible uniques reachable/.test(html),
        hasTc87Lab: /TC87-only/.test(html),
        hasUberChip: /class="zd-item[^"]*\buber\b/.test(html),
        uberChipClickable: /zd-item-click/.test(uberChip) && /navigateToItem\(/.test(uberChip),
        hasUndefined: /undefined/.test(html),
      };
    });
    expect(r.hasHead).toBe(true);
    expect(r.hasTc87Lab).toBe(true);
    expect(r.hasUberChip).toBe(true);
    expect(r.uberChipClickable).toBe(true);
    expect(r.hasUndefined).toBe(false);
  });
});
