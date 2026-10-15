// v3746 (REG-2251) — AFFIX PERFECTION-KEEP. His 2026-10-15 law (AUTO_MULE_AFFIX_KEEPLIST.md): a magic/rare
// item is muled when a COVETED affix rolls near its MAX — roll >= 0.85x max, top-tier (S) a touch looser at
// 0.80 — however low the rest of the item scores. The coveted SET is his curated reference (affix name + the
// stat it rolls + a value tier); the MAX is READ FROM DATA — the CB_DB affix table already on the page
// (window._cbDb().af, the rows the generator writes from the RotW install), never a hardcoded number. These
// lock the law: a near-max coveted roll is KEPT and lifts a would-be TOSS to KEEP; a low roll of the SAME
// affix is not; the keep max really came from CB_DB (not a constant); a roll past the band stays UNKNOWN;
// and the perfection lift never inflates the transparent affix score (the v466 contract).
// Browser suite — GitHub CI ONLY, never his Mac.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v3746 affix perfection-keep (REG-2251)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() =>
      (window as any)._aicVerdict && (window as any)._aicPerfectKeep && (window as any)._cbDb);
  });

  test('a near-max coveted LIFE roll is KEPT, and its max is READ FROM CB_DB (not hardcoded)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w: any = window;
      const norm = (s: string) => String(s || '').toLowerCase().replace(/’/g, "'");
      // read the life-affix max straight from the data source the page already carries
      const d = w._cbDb();
      let lifeMax = 0;
      (d.af || []).forEach((a: any) => {
        if (['of the whale', 'of vita'].indexOf(norm(a[2])) >= 0) {
          (a[11] || []).forEach((l: any) => (l[1] || []).forEach((rg: any) => {
            if (typeof rg[1] === 'number') lifeMax = Math.max(lifeMax, Math.max(rg[0], rg[1]));
          }));
        }
      });
      const vNear = w._aicVerdict({ q: 'magic', base: 'Grand Charm', name: 'Amulet of the Whale', mods: ['+' + lifeMax + ' to Life'] });
      const vLow = w._aicVerdict({ q: 'magic', base: 'Grand Charm', name: 'Amulet of the Whale', mods: ['+1 to Life'] });
      const pkNear = w._aicPerfectKeep({ mods: ['+' + lifeMax + ' to Life'] });
      return {
        lifeMax,
        pkMax: pkNear.best && pkNear.best.max, pkKey: pkNear.best && pkNear.best.key,
        vNearTier: vNear.tier, vNearPerfect: !!(vNear.perfect && vNear.perfect.keep),
        vLowTier: vLow.tier, vLowPerfect: !!(vLow.perfect && vLow.perfect.keep),
      };
    });
    expect(r.lifeMax).toBeGreaterThan(0);        // CB_DB really carries the life band
    expect(r.pkMax).toBe(r.lifeMax);             // the keep max is READ FROM DATA, not a constant
    expect(r.pkKey).toBe('life');
    expect(r.vNearPerfect).toBe(true);
    expect(r.vNearTier).toBe('keep');            // a near-max life roll LIFTS a would-be toss to keep
    expect(r.vLowPerfect).toBe(false);
    expect(r.vLowTier).not.toBe('keep');         // a low roll of the SAME affix is not kept
  });

  test("a near-max Jeweler's SOCKET roll (4os) is KEPT; a low socket roll of the same affix is not", async ({ page }) => {
    const r = await page.evaluate(() => {
      const w: any = window;
      const v4 = w._aicVerdict({ q: 'magic', base: 'Monarch', name: "Jeweler's Monarch", mods: ['Socketed (4)'] });
      const pk4 = w._aicPerfectKeep({ mods: ['4 Sockets'] });
      const pk2 = w._aicPerfectKeep({ mods: ['2 Sockets'] });
      return {
        max: pk4.best && pk4.best.max, key: pk4.best && pk4.best.key,
        tier: v4.tier, perfect: !!(v4.perfect && v4.perfect.keep),
        low2keep: pk2.keep,
      };
    });
    expect(r.max).toBe(4);                        // Jeweler's sockets max, read from CB_DB
    expect(r.key).toBe('sockets');
    expect(r.perfect).toBe(true);
    expect(r.tier).toBe('keep');
    expect(r.low2keep).toBe(false);               // a 2-socket roll is not near the 4 max
  });

  test('a roll BEYOND the affix band is not claimed as that affix (unknown stays unknown)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w: any = window;
      const over = w._aicPerfectKeep({ mods: ['+500 to Life'] });   // 500 >> any life band
      const none = w._aicPerfectKeep({ mods: ['+50 to Mana'] });    // no coveted stat at all
      return { overKeep: over.keep, noneKeep: none.keep };
    });
    expect(r.overKeep).toBe(false);
    expect(r.noneKeep).toBe(false);
  });

  test('perfection keep lifts the TIER only — it never inflates the affix score (v466 contract)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w: any = window;
      const v = w._aicVerdict({ q: 'magic', base: 'Grand Charm', mods: ['+100 to Life'] });
      return { tier: v.tier, score: v.score, hasPerfect: !!v.perfect };
    });
    expect(r.tier).toBe('keep');     // lifted by perfection
    expect(r.score).toBe(5);         // +life weight only — the perfection layer must not touch the score
    expect(r.hasPerfect).toBe(true); // the verdict carries its perfection read
  });
});
