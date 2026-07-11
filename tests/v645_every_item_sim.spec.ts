import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v645 — EVERY-ITEM SIMULATION (Konyo: 'demonstrations and SIMULATIONS for every single item —
// there is a lot — to make sure they all properly work and render/tally/found'). The FULL pools:
// every grail unique and every set piece goes through the complete lifecycle — tick → owned +
// dated + tallied → untick → restored — and every one must be REACHABLE (a tick control exists
// for it in the rendered ALL view). Failures collect into a list so one bad item names itself.

test('ALL grail uniques: reachable + full found lifecycle (tick → dated/tallied → untick → restored)', async ({ page }) => {
  test.setTimeout(600000);
  await page.goto(URL); await page.waitForTimeout(2200);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.switchTab('funi'); await new Promise((res) => setTimeout(res, 800));
    const box = document.getElementById('tab-funi')!;
    const pool = (w.ITEMS || []).filter((x: any) => ['grail','high','common'].includes(x.tier));
    const ownedBefore = new Set(JSON.parse(localStorage.getItem('d2r_owned') || '[]'));
    const missing = pool.filter((x: any) => !ownedBefore.has(x.n));
    const failures: string[] = [];
    // reachability: every missing unique has a tick in the rendered ALL grid
    const ticks = new Set([...box.querySelectorAll('.gf-allgrid [data-gf-tick]')].map((t: any) => t.getAttribute('data-gf-tick')));
    missing.forEach((x: any) => { if (!ticks.has(x.n)) failures.push('UNREACHABLE: ' + x.n); });
    // lifecycle: run the STATE loop for every item via the same API the tick calls (fast path —
    // per-item DOM clicks at 300 items would be minutes of re-renders; the DOM path is proven by v644)
    for (const x of missing) {
      w.toggleOwned(x.n);
      const log1 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      const own1 = JSON.parse(localStorage.getItem('d2r_owned') || '[]').includes(x.n);
      if (!own1) failures.push('NOT TALLIED: ' + x.n);
      if (!log1[x.n]) failures.push('NOT DATED: ' + x.n);
      w.toggleOwned(x.n);
      const log2 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      const own2 = JSON.parse(localStorage.getItem('d2r_owned') || '[]').includes(x.n);
      if (own2) failures.push('NOT RESTORED: ' + x.n);
      if (log2[x.n]) failures.push('LEDGER NOT ERASED: ' + x.n);
    }
    return { poolN: pool.length, missingN: missing.length, failures: failures.slice(0, 25), failN: failures.length };
  });
  console.log('UNI SIM', JSON.stringify({ pool: r.poolN, missing: r.missingN, failN: r.failN }));
  expect(r.failures).toEqual([]);
  expect(r.failN).toBe(0);
  expect(r.poolN).toBeGreaterThan(290);
});

test('VISIBILITY: with every drawer open, ALL missing uniques appear in the run cards AND the wall (302 = 302 = 302)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2200);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.switchTab('funi'); await new Promise((res) => setTimeout(res, 800));
    const box = document.getElementById('tab-funi')!;
    [...box.querySelectorAll('details')].forEach((d: any) => (d.open = true));
    await new Promise((res) => setTimeout(res, 300));
    const missing = w.funiScan().total - w.funiScan().found;
    const runChips = new Set([...box.querySelectorAll('.gf-chip[data-arttip]')].map((c: any) => c.getAttribute('data-arttip')));
    const wall = new Set([...box.querySelectorAll('.gf-allgrid [data-gf-tick]')].map((t: any) => t.getAttribute('data-gf-tick')));
    return { missing, runChipN: runChips.size, wallN: wall.size, chipTicks: box.querySelectorAll('.gf-chip .gf-tick').length };
  });
  expect(r.runChipN).toBe(r.missing);   // every missing unique visible in its run card (v647.1 in-card drawers)
  expect(r.wallN).toBe(r.missing);      // and in the Grail Wall
  expect(r.chipTicks).toBe(r.missing);  // every chip carries its ✓
});

test('ALL set pieces: reachable + full found lifecycle through the Set Tracker store', async ({ page }) => {
  test.setTimeout(600000);
  await page.goto(URL); await page.waitForTimeout(2200);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.switchTab('fsets'); await new Promise((res) => setTimeout(res, 800));
    const box = document.getElementById('tab-fsets')!;
    const sets = w.__allSets ? w.__allSets() : [];
    const haveBefore = new Set(JSON.parse(localStorage.getItem('d2r_setPieces') || '[]'));
    const allPieces: string[] = [];
    sets.forEach((st: any) => (st.pieces || []).forEach((p: string) => allPieces.push(p)));
    const missing = allPieces.filter((p) => !haveBefore.has(p));
    const failures: string[] = [];
    const ticks = new Set([...box.querySelectorAll('.gf-allgrid [data-gf-tick]')].map((t: any) => t.getAttribute('data-gf-tick')));
    missing.forEach((p) => { if (!ticks.has(p)) failures.push('UNREACHABLE: ' + p); });
    for (const p of missing) {
      w.toggleSetPiece(p);
      const log1 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      const have1 = JSON.parse(localStorage.getItem('d2r_setPieces') || '[]').includes(p);
      if (!have1) failures.push('NOT TALLIED: ' + p);
      if (!log1[p]) failures.push('NOT DATED: ' + p);
      w.toggleSetPiece(p);
      if (JSON.parse(localStorage.getItem('d2r_setPieces') || '[]').includes(p)) failures.push('NOT RESTORED: ' + p);
      if (JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')[p]) failures.push('LEDGER NOT ERASED: ' + p);
    }
    return { pieces: allPieces.length, missingN: missing.length, failures: failures.slice(0, 25), failN: failures.length };
  });
  console.log('SET SIM', JSON.stringify({ pieces: r.pieces, missing: r.missingN, failN: r.failN }));
  expect(r.failures).toEqual([]);
  expect(r.failN).toBe(0);
  expect(r.pieces).toBeGreaterThan(100);
});
