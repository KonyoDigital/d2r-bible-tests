import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1732 — A ZONE'S PROSE MAY NOT CONTRADICT THAT ZONE'S OWN NUMBERS.
//
// Catacombs L4 stored `mlvl:75, tcMax:75` while every other Hell terror zone read mlvl 96, and a
// live silospen pull gave it a pool of 79 grail items against the 7 those figures allowed. The
// numbers were raised to 96/87. What did NOT move with them was the hand-written prose on the same
// card, which went on saying:
//
//     "Andariel (same monster, no mlvl boost)"
//     "terror doesn't help Andy much, she's already mlvl 75 Hell. Same NM SoJ rate.
//      Skip vs Pindle/Pit."
//
// directly above the card's own generated line, "Terror lifts this zone to mlvl 96 / TC87 — the
// highest ceiling in the game." Two sentences, one card, opposite claims. [[label-outlived-referent]]
//
// All three claims were false, and the bible refuted them with its own data:
//   * "no mlvl boost" / "already mlvl 75" — BOSSES has Andariel HELL TZ at mlvl 87, tcMax 87.
//   * "Same NM SoJ rate" — The Stone of Jordan is 1:2,286 in NM and 1:4,014 in Hell TZ. Not the
//     same, and the true statement is the more useful one: NM really is the better SoJ kill,
//     because the Hell pool is wider, not because terror does nothing.
//   * "Skip vs Pindle/Pit" — rested entirely on the TC75 cap that had just been disproved.
//
// The prose existed in TWO copies — the TZ_ZONES literal and a static pre-rendered card that is
// what a no-JS reader is served. Both were fixed. [[copy-drift]]
//
// This gate reads the numbers OUT of each zone and asks whether that zone's own prose asserts a
// different one. It is deliberately narrow: it only fires on an explicit "mlvl N" or "TCN" claim,
// because a gate that tried to judge prose generally would be noise.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1732 — zone prose agrees with the zone', () => {
  test('★★★ no zone note claims an mlvl or TC its own zone contradicts', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      const bad: string[] = [];
      let claims = 0;
      for (const z of (TZ_ZONES as any[])) {
        const prose = [z.why, z.unique, z.act].filter(Boolean).join(' ');
        for (const m of prose.matchAll(/mlvl\s*(\d{1,3})/gi)) {
          claims++;
          const n = Number(m[1]);
          // an ARROW is a transition, not a claim about the end state: "mlvl 75 -> 87" names both
          const arrow = /\d\s*(?:→|->|to)\s*\d/.test(prose);
          if (n !== z.mlvl && !arrow) bad.push(`${z.name}: prose says mlvl ${n}, zone is ${z.mlvl}`);
        }
        for (const m of prose.matchAll(/\bTC\s*(\d{1,3})/gi)) {
          claims++;
          const n = Number(m[1]);
          if (n > z.tcMax) bad.push(`${z.name}: prose says TC${n}, zone ceiling is TC${z.tcMax}`);
        }
      }
      return { bad, claims, zones: (TZ_ZONES as any[]).length };
    });
    expect(r.zones, 'no zones were read').toBeGreaterThan(8);
    expect(r.claims, 'no zone prose made a numeric claim — nothing was measured').toBeGreaterThan(0);
    expect(r.bad, 'zone prose contradicting its own zone: ' + r.bad.join(' | ')).toEqual([]);
  });

  /* The static twin must be read from the FILE, not the DOM. The first version of this test read
     `document.documentElement.outerHTML` and found seen=0 on every fixture, because renderTzZones()
     has already replaced the static cards by the time a test can look. It would have passed as a
     green gate measuring nothing had the non-vacuity assertion not been there. [[feedback-blind-fixture-green-gate]]
     The served no-JS html is a source-level fact, so it is checked at source level. */
  test('★★★ the static pre-rendered card carries the same figures as the live data', async () => {
    const H = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    // TZ_ZONES spans many lines, so walk to the matching bracket rather than to the next newline
    const i = H.indexOf('const TZ_ZONES = [');
    let depth = 0, j = i + 17;
    for (; j < H.length; j++) {
      if (H[j] === '[') depth++;
      else if (H[j] === ']' && --depth === 0) break;
    }
    // a JS object literal with unquoted keys — not JSON
    const ZS: any[] = Function('return ' + H.slice(i + 17, j + 1))();

    const bad: string[] = [];
    let seen = 0;
    for (const m of H.matchAll(/<div class="tz-zone-card"[\s\S]{0,1400}?<\/div>\s*<\/div>/g)) {
      const nm = /class="tz-zone-name">([^<]+)</.exec(m[0]);
      const meta = /class="tz-zone-meta"[^>]*>([^<]*)</.exec(m[0]);
      if (!nm || !meta) continue;
      const z = ZS.find((z) => z.name === nm[1].trim());
      if (!z) continue;
      seen++;
      const ml = /mlvl\s*(\d+)/i.exec(meta[1]);
      const tc = /TC\s*(\d+)\s*max/i.exec(meta[1]);
      if (ml && Number(ml[1]) !== z.mlvl) bad.push(`${z.name}: card says mlvl ${ml[1]}, data says ${z.mlvl}`);
      if (tc && Number(tc[1]) !== z.tcMax) bad.push(`${z.name}: card says TC${tc[1]}, data says TC${z.tcMax}`);
    }
    expect(seen, 'no static zone cards were found in the served html').toBeGreaterThan(5);
    expect(bad, 'static cards disagreeing with the data: ' + bad.join(' | ')).toEqual([]);
  });
});
