import { test, expect } from './_net_stub';
import * as path from 'path';

// vNNNN - A SUPER-UNIQUE'S TERROR LINE MAY NOT CONTRADICT THE ZONE IT RESOLVES TO.
//
// #68 / #306 / the v43 #231 eye (8003b914): Blood Raven's card ended "Burial Grounds terrors to
// mlvl 96 / TC85" while the Burial Grounds terror zone it links to carries tcMax 87. Six more
// super-uniques (Shenk, Eldritch, Frozenstein, Endugu, Sszark, Griswold) had the same stale "/ TC85"
// over a tcMax-87 zone. The number was raised to 87 on the ZONE side long ago (v1722 raises a
// ceiling to what its rows prove and never lowers it; v49 confirms mlvl 96 => TC87); the
// hand-written super-unique prose never moved with it. Same class as v1732 (a zone's prose
// outliving the zone's own numbers), on a surface v1732 does not scan: the SUPER_UNIQUES cards,
// whose detail pool is itself computed from the resolved zone's tcMax, so the prose was
// contradicting the card's own grid. [[label-outlived-referent]]
//
// This gate reads each super-unique's resolved zone (the LIVE suTzZone join, REG-2124) and asks
// whether that super-unique's own "mlvl 96 / TCn" prose names a TC its resolved zone contradicts.
// Narrow by design: only the explicit "mlvl 96 / TCn" terror line is judged, and a super-unique
// that resolves to NO zone (The Smith, Bone Ash, Pindle - separate open questions on #68) is not
// checked here. It reads DATA (tcMax) not a hardcoded number, so it tracks the zone if tcMax moves.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('vNNNN - super-unique terror prose agrees with its resolved zone', () => {
  test('★★★ no super-unique "mlvl 96 / TCn" line names a TC its resolved zone contradicts', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      const bad: string[] = [];
      let claims = 0, resolved = 0;
      const sus = (typeof SUPER_UNIQUES !== 'undefined') ? (SUPER_UNIQUES as any[]) : [];
      const suTz = (window as any).suTzZone;
      const haveFn = (typeof suTz === 'function');
      for (const su of sus) {
        const tz = haveFn ? suTz(su) : null;
        if (tz && tz.z) resolved++;
        const prose = [su.drops, su.role, su.pool && su.pool.src].filter(Boolean).join(' ');
        for (const m of String(prose).matchAll(/mlvl\s*96\s*\/\s*TC\s*(\d{1,3})/gi)) {
          claims++;
          if (!tz || !tz.z) continue;            // no resolved zone - a separate open question
          const n = Number(m[1]);
          if (n !== tz.z.tcMax) bad.push(su.name + ': prose says mlvl 96 / TC' + n + ', but resolves to ' + tz.z.name + ' (tcMax ' + tz.z.tcMax + ')');
        }
      }
      return { bad, claims, resolved, sus: sus.length, haveFn };
    });
    expect(r.haveFn, 'suTzZone is not a function - the join could not be read').toBe(true);
    expect(r.sus, 'no super-uniques were read').toBeGreaterThan(10);
    expect(r.resolved, 'no super-unique resolved to a zone - the join is dead').toBeGreaterThan(5);
    expect(r.claims, 'no super-unique prose made an "mlvl 96 / TCn" claim - nothing was measured').toBeGreaterThan(5);
    expect(r.bad, 'super-unique terror prose contradicts its resolved zone: ' + r.bad.join(' | ')).toEqual([]);
  });
});
// Intended path: tests/v3748_su_terror_prose_matches_zone.spec.ts (rename the vNNNN prefix to the ship version the applier bumps to).