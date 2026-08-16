import { test, expect } from './_net_stub';
import * as path from 'path';

// v1743 — A NAME THAT REACHES A SCREEN IS A NAME.
//
// The unique roster carried `bloodcrescent` — no space, no capitals — where every drop table in the
// file says `Blood Crescent`. It looked harmless and it was not:
//
//   * `funiScan` folds names with `_regKey` to borrow a ROUTE, so the item found its 65 sources and
//     computed 1.04h — the FASTEST time on the board;
//   * but v1716's rule "THE NAME HE TICKS MUST NOT CHANGE" deliberately keeps the ROSTER spelling
//     for display and for every ledger read;
//   * so the grail bridge published his **#1 farming target under a name that is not an item**, and
//     F·Uniques — which resolves by the real name — never showed it at all.
//
// That is why the Sessions bridge and F·Uniques disagreed about what the fastest grail was: one of
// them was ranking something the other could not see. [[label-outlived-referent]]
//
// FIXED AT THE SOURCE — two map keys (`ITEM_VALUE` and the trade-value list) — plus a one-time
// ledger migration, because the same v1716 comment records the scar for renaming an item without
// one: "3 found uniques flipped to missing the moment the object came back under the other name."
// If he had ever ticked it under the old spelling, the tick moves with the name.
//
// WHY THIS GATE IS NARROW. The roster has TWELVE names that differ from their registry match, and
// every one of them is legitimate — curly apostrophes (Atma’s, Seraph’s, The Cat’s Eye, Saracen’s),
// disambiguating qualifiers (Harlequin Crest (Shako), Gull (dagger), Crescent Moon (amulet),
// Athena's Wrath (set piece)), and a leading article (The Cranium Basher, The Iron Jang Bong, The
// Mahim-Oak Curio). `_regKey` exists precisely to bridge those, and they must NOT be flagged.
// `bloodcrescent` was different in kind: not a rendering of the name, but a name that had lost its
// capitals and its spaces. A name that reaches a screen starts with a capital — that is the line,
// and it separates the one defect from the twelve non-defects cleanly.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1743 — the roster spells items the way they are displayed', () => {
  test('★★★ no roster name is un-capitalised', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    const r = await page.evaluate(() => {
      const w: any = window;
      const roster: string[] = w._gUniqueRoster ? w._gUniqueRoster() : [];
      return { n: roster.length, bad: roster.filter((x) => /^[a-z]/.test(String(x))) };
    });
    // non-vacuity: the roster must actually have been read
    expect(r.n, 'the unique roster came back empty').toBeGreaterThan(300);
    expect(r.bad, 'roster names that lost their capitalisation: ' + r.bad.join(', ')).toEqual([]);
  });

  test('★★★ Blood Crescent is one item, under its real name, on every surface', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const w: any = window;
      const fu = w.funiScan();
      const bridge = JSON.parse(w.LSR.getItem('d2r_grailFarm') || 'null') || [];
      const arr = Array.isArray(bridge) ? bridge : (bridge.items || []);
      const named = (re: RegExp, list: any[], key: string) => list.filter((x) => re.test(String(x[key] || '')));
      return {
        missingProper: named(/^blood crescent$/i, fu.missing || [], 'n').map((x: any) => ({ n: x.n, srcs: (x.sources || []).length })),
        missingTypo: named(/^bloodcrescent$/i, fu.missing || [], 'n').length,
        bridgeProper: named(/^blood crescent$/i, arr, 'name').length,
        bridgeTypo: named(/^bloodcrescent$/i, arr, 'name').length,
        resolves: w.d2rResolveItem ? !!w.d2rResolveItem('Blood Crescent') : null,
      };
    });
    expect(r.missingTypo, 'the squashed name is back in the scan').toBe(0);
    expect(r.bridgeTypo, 'the squashed name is back in the grail bridge').toBe(0);
    expect(r.missingProper.length, 'Blood Crescent vanished from the scan entirely').toBe(1);
    // it keeps its route — the whole point is that it was always routable, just mis-named
    expect(r.missingProper[0].srcs, 'Blood Crescent lost its drop sources').toBeGreaterThan(50);
    expect(r.bridgeProper, 'Blood Crescent is not in the grail bridge').toBe(1);
    expect(r.resolves, 'Blood Crescent does not resolve as an item').toBe(true);
  });

  test('★★ the twelve legitimate roster/registry differences stay legitimate', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    const r = await page.evaluate(() => {
      const w: any = window;
      const roster: string[] = w._gUniqueRoster ? w._gUniqueRoster() : [];
      const reg = w.ITEM_REGISTRY || {};
      const fold = w._regKey || ((x: string) => String(x).toLowerCase().replace(/[^a-z0-9]/g, ''));
      const byFold: Record<string, string[]> = {};
      Object.keys(reg).forEach((k) => { const f = fold(k); (byFold[f] = byFold[f] || []).push(k); });
      const cosmetic: string[] = [];
      roster.forEach((n) => {
        if (reg[n]) return;
        const hits = byFold[fold(n)];
        if (hits && hits.length === 1 && hits[0] !== n) cosmetic.push(`${n} -> ${hits[0]}`);
      });
      return { cosmetic };
    });
    /* Pinned, not asserted-to-zero: these are the apostrophe/qualifier/article differences _regKey
       was written for. A THIRTEENTH would mean a new spelling entered the roster, which is worth a
       look — that is exactly how `bloodcrescent` would have arrived. */
    expect(r.cosmetic.length, 'roster/registry spelling differences: ' + r.cosmetic.join(' | '))
      .toBeLessThanOrEqual(12);
  });
});
