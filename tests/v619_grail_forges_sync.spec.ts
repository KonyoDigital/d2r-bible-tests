import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v619 — GRAIL FORGES found-sync + completion seals (Konyo: 'same smart automated logic… cancels
// out and stamps when completely finished'). (a) funiScan groups the FULL verified pool per run:
// all-found runs earn the 🏆 Sealed-grounds band; quick-wins all found → the seal, not an empty tab.
// (b) F·Sets: completed sets wear the seal band; toggles from EITHER surface re-scan the other.
// (c) toggleOwned live-syncs an open grail-forge tab both ways.

test('sealed grounds: a run whose whole verified pool is found earns the band and leaves Best runs', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    // find a boss with a small verified pool via the scan itself, then own all its items
    const items = (w.ITEMS || []).filter((x: any) => x.tier === 'grail' || x.tier === 'high' || x.tier === 'common');
    const byBoss: any = {};
    items.forEach((x: any) => {
      let best: any = null, bestR = -1;
      (x.sources || []).forEach((s: any) => { if (!s || s.blocked || s.chance == null) return; const rate = (s.kph || 30) / s.chance; if (rate > bestR) { bestR = rate; best = s; } });
      if (best) (byBoss[best.boss] = byBoss[best.boss] || []).push(x.n);
    });
    const target = Object.keys(byBoss).sort((a, b) => byBoss[a].length - byBoss[b].length).find((k) => byBoss[k].length >= 2)!;
    localStorage.setItem('d2r_owned', JSON.stringify(byBoss[target]));
    return { target, n: byBoss[target].length };
  });
  await page.reload(); await page.waitForTimeout(1800);
  const r2 = await page.evaluate((target: string) => {
    const w: any = window;
    const s = w.funiScan();
    w.switchTab('funi');
    const dom = (document.getElementById('funi-body') || document.body).textContent || '';
    localStorage.removeItem('d2r_owned');
    return {
      sealed: (s.sealed || []).some((g: any) => g.boss === target),
      inRuns: (s.runs || []).some((g: any) => g.boss === target),
      bandInDom: dom.includes('grounds sealed') && dom.includes(target),
    };
  }, r.target);
  expect(r2.sealed).toBe(true);     // the full pool is found → sealed
  expect(r2.inRuns).toBe(false);    // …and it left the farm list (cancel-out sync)
  expect(r2.bandInDom).toBe(true);  // …wearing the horizontal seal in the rendered tab
});

test('completed sets wear the seal band; checklist⇄fsets sync both ways', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const sets = (typeof w.__allSets === 'function') ? w.__allSets() : [];
    const small = sets.slice().sort((a: any, b: any) => a.pieces.length - b.pieces.length)[0];
    localStorage.setItem('d2r_setPieces', JSON.stringify(small.pieces));
    return { set: small.name, n: small.pieces.length };
  });
  await page.reload(); await page.waitForTimeout(1800);
  const r2 = await page.evaluate((setName: string) => {
    const w: any = window;
    w.switchTab('fsets');
    const dom1 = (document.getElementById('fsets-body') || document.body).textContent || '';
    const hadBand = dom1.includes('set complete');
    // un-tick one piece from the CHECKLIST side while fsets is the active tab → the band must leave live
    const s = w.fsetsScan();
    const done = s.done[0];
    w.toggleSetPiece(done.pieces[0].name);
    const dom2 = (document.getElementById('fsets-body') || document.body).textContent || '';
    localStorage.removeItem('d2r_setPieces');
    return { hadBand, stillDone: dom2.includes('set complete') && dom2.includes(setName.replace(/\s*\(set\)$/i, '')) };
  }, r.set);
  expect(r2.hadBand).toBe(true);      // the full set wears the seal
  expect(r2.stillDone).toBe(false);   // checklist un-tick re-scanned the open fsets tab live
});

test('toggleOwned live-syncs an open F·Uniques tab', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => new Promise<any>((res) => {
    const w: any = window;
    w.switchTab('funi');
    setTimeout(() => {
      const s = w.funiScan();
      const target = s.missing[0].n;
      const before = (document.getElementById('funi-body')!.textContent || '').includes(target);
      w.toggleOwned(target);   // found via ANY surface while funi is open
      setTimeout(() => {
        const s2 = w.funiScan();
        const gone = !s2.missing.some((x: any) => x.n === target);
        w.toggleOwned(target);   // restore
        res({ before, gone });
      }, 400);
    }, 500);
  }));
  expect(r.gone).toBe(true);
});
