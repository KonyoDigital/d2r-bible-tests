import { test, expect } from './_net_stub';
import * as path from 'path';

// v1740 — ONE NUMBER PER FARM, AND SAY WHICH QUESTION IT ANSWERS.
//
// Konyo: "the next grail time find is different saying from the sessions like the f-uniques and
// f-sets are showing diffrent number for time farming those specific items... cant have two
// diffrent numbers for farming.. and its obivously not the quickets either cuz i see in the tabs
// f-unqies and f-sets faster ones."
//
// He was reading two answers to two different questions as one contradiction, and the app gave him
// no way to tell them apart:
//
//   * F·UNIQUES ranks ITEMS. Its card prints "~1.2h to find" — the fastest single item.
//   * The SESSIONS ops queue ranks RUNS. It takes funiScan().runs[0] — the route that yields a
//     missing unique fastest — then named ONE item from that run and printed THAT ITEM's odds:
//     "Hell TZ Mephisto 1:449", which is 3.9h.
//
// So the row advertised 3.9h for a decision made on a different number entirely, and 3.9h loses to
// F·Uniques' 1.2h — which is exactly why it read as "not the quickest". The rate that justified the
// pick was computed into `c.op.route` and thrown away before rendering. Measured: that run yields a
// missing unique every 33 MINUTES, which beats every single-item time on the board. The best number
// in the app was the one number it never showed. [[the-unjoined-end]]
//
// WHAT WAS CHECKED AND FOUND INNOCENT, so the fix stayed narrow:
//   * The console's `_ev_hours` (control_app.py) vs the board's `hoursFor`: compared across all 144
//     bridge entries — 144/144 identical, 0 mismatches. No formula drift.
//   * The bridge's item set vs funiScan().missing: identical top 10, nothing dropped.
//   * TWO source-pickers do exist and they differ on paper — `_pickSrc` maximises `kph/chance` with
//     a kph fallback of 30 and skips `blocked`, while the bridge minimises `hoursFor` with a
//     fallback of 100 and skips `chance <= 50`. Measured across 144 items they disagree on the boss
//     for ZERO of them and on the hours for ONE (Gheed's Fortune, 12%). Real, tiny, and NOT what he
//     was seeing — so it is recorded rather than "fixed" on the way past.
//
// The row now prints the item's own time-to-find through `_ttf` — the exact helper the F·Uniques
// card prints with, so the same item shows the same number on both surfaces — AND the run rate that
// justifies the pick, each labelled with what it measures.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1740 — the ops queue and F·Uniques agree about the same item', () => {
  test('★★★ the grail ops row prints the same time-to-find F·Uniques prints for that item',
    async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const w: any = window;
      const rot = w._chronRotation ? w._chronRotation() : null;
      const g = rot && rot.incomplete ? rot.incomplete.find((c: any) => c.key === 'grail') : null;
      if (!g || !g.op) return { err: 'no grail op — nothing to compare' };
      const fu = w.funiScan();
      const item = (fu.missing || []).find((i: any) => i.n === g.op.item);
      if (!item) return { err: 'the op names an item funiScan does not carry: ' + g.op.item };
      const bs = w._pickSrc(item.sources, item.n);
      const funiTtf = bs ? w._ttf(bs.chance != null ? bs.chance : bs.s.chance, bs.s.kph || 30) : null;
      return {
        item: g.op.item, opBoss: g.op.boss, opTtf: g.op.bestHours, opRoute: g.op.route,
        funiBoss: bs ? bs.s.boss : null, funiTtf,
      };
    });
    expect(r.err, r.err || '').toBeUndefined();
    // the number itself — the whole complaint
    expect(r.opTtf, 'the ops row carries no time-to-find at all').toBeTruthy();
    expect(r.opTtf, `ops says ${r.opTtf}, F·Uniques says ${r.funiTtf} for the same item (${r.item})`)
      .toBe(r.funiTtf);
    expect(r.opBoss, 'the two surfaces name different bosses for the same item').toBe(r.funiBoss);
    // and the number the PICK was made on must be present, or the row is advertising the wrong one
    expect(r.opRoute, 'the run rate that justified this pick is not shown').toBeTruthy();
  });

  test('★★★ the rendered row shows both numbers, each labelled', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2800);
    const txt = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('*')]
        .filter((e) => /uniques left/.test(e.textContent || '') && (e.textContent || '').length < 220);
      const row = rows[rows.length - 1];
      return row ? (row.textContent || '').replace(/\s+/g, ' ').trim() : '';
    });
    expect(txt, 'no grail ops row rendered').toBeTruthy();
    // "~3.9h to find" — the item's own number, the one F·Uniques also prints
    expect(txt, 'the row does not state the item time-to-find: ' + txt).toMatch(/~[\d.]+\s*(h|m)\s*to find/);
    // "this run yields ~1 missing unique every 33m" — the number the pick was made on
    expect(txt, 'the row does not state the run rate: ' + txt).toMatch(/run yields .*every/);
    expect(txt, 'the row lost its remaining count: ' + txt).toMatch(/uniques left/);
  });

  test('★★ the console formula and the board formula still agree on every bridge item',
    async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2600);
    const r = await page.evaluate(() => {
      const w: any = window;
      // control_app.py:_ev_hours, transcribed. If these ever diverge, the Sessions flagship and the
      // board start printing different hours for one grail — which is what this whole file is about.
      const evHours = (pRun: number, kph: number, c = 0.5) => {
        const P = Number(pRun), K = Number(kph);
        if (!(P > 0 && P < 1) || !(K > 0)) return null;
        return Math.ceil(Math.log(1 - c) / Math.log(1 - P)) / K;
      };
      const bridge = JSON.parse(w.LSR.getItem('d2r_grailFarm') || 'null') || [];
      const arr = Array.isArray(bridge) ? bridge : (bridge.items || []);
      const scan = w.funiScan();
      const byName: any = {};
      (scan.missing || []).forEach((i: any) => (byName[i.n] = i));
      let compared = 0;
      const bad: string[] = [];
      for (const b of arr) {
        const item = byName[b.name];
        if (!item) continue;
        let best: any = null;
        (item.sources || []).forEach((s: any) => {
          if (!s.chance || s.chance <= 50) return;
          /* effChance/hoursFor are MODULE-scoped, not on window — they are reachable only as bare
             identifiers inside evaluate(). Reading them off `window` returns undefined, which
             leaves `best` null for every item and makes this test pass over an empty set; the
             non-vacuity assertion below is what caught exactly that. */
          let a, h;
          try { a = eval('effChance')(s.chance, s.bossId, s.diffKey); } catch (e) { return; }
          try { h = eval('hoursFor')(a, 0.5, s.kph || 100); } catch (e) { return; }
          if (h !== null && (!best || h < best)) best = h;
        });
        const consoleH = evHours(b.dropChance, b.killsPerHr);
        if (best === null || consoleH === null) continue;
        compared++;
        if (Math.abs(consoleH - best) / best > 0.005) {
          bad.push(`${b.name}: console ${consoleH.toFixed(2)}h vs board ${best.toFixed(2)}h`);
        }
      }
      return { compared, bad: bad.slice(0, 6), badN: bad.length };
    });
    expect(r.compared, 'no bridge items were compared — the bridge may not have been written')
      .toBeGreaterThan(50);
    expect(r.bad, `${r.badN} items where the console and board formulas disagree: ` + r.bad.join(' | '))
      .toEqual([]);
  });
});
