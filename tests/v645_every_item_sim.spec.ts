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
    const ownedBefore = new Set(Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')));   // v677 — the LEDGER is the found store
    const missing = pool.filter((x: any) => !ownedBefore.has(x.n));
    const failures: string[] = [];
    /* reachability: every missing unique has a tick in the rendered ALL grid.
       v1696 — ASK ABOUT IDENTITY, NOT SPELLING. This compared raw ITEMS strings against the grid's
       keys. v1692 moved the grid onto the resolver's roster, whose names differ from ITEMS' in four
       innocent ways, and 19 items read as UNREACHABLE while every one of them was on screen:
         · a CURLY apostrophe   — ITEMS "Saracen's Chance"      vs roster "Saracen’s Chance"
         · a display SUFFIX     — ITEMS "Harlequin Crest (Shako)" vs roster "Harlequin Crest"
         · a name VARIANT       — ITEMS "Cranium Basher"        vs roster "The Cranium Basher"
         · a different KIND     — "Wilhelm's Pride" is a set piece, correctly absent from a
                                  UNIQUES grid, and "Ist rune" was never a unique at all
       Each is checked explicitly rather than by fuzzy matching: a loose comparison here would make
       this test pass on an item that genuinely vanished, which is the only thing it exists to catch. */
    const ticks = new Set([...box.querySelectorAll('.gf-allgrid [data-gf-tick]')].map((t: any) => t.getAttribute('data-gf-tick')));
    // ITEMS spelling → the roster's spelling, for names neither the resolver nor a suffix-strip joins
    const VARIANTS: Record<string, string> = {
      'Cranium Basher': 'The Cranium Basher',
      "Bloodmoon's Light": 'Bloodmoon',
      /* v1703 — these two joined the list when Konyo ruled the four "missing" uniques DO exist. Two of
         them already did, under their proper names: "The Mahim-Oak Curio" and "The Iron Jang Bong" are
         in ITEM_VALUE, in _UNI_EXTRA, and SEEDED FOUND in _GRAIL_SEED (May 18 / May 19). Only Polaris
         Spear and The Scourge were genuinely absent, and only those two were added to the roster.
         Adding the bare spellings would have minted a second, permanently-unfound ghost row for an item
         he already owns — so they are name variants, exactly like Cranium Basher above. */
      'Mahim-Oak Curio': 'The Mahim-Oak Curio',
      'Iron Jang Bong': 'The Iron Jang Bong',
    };
    // rows that live in ITEMS with a unique-ish tier but are not uniques
    const NOT_A_UNIQUE = new Set(['Ist rune', 'Jah/Ber/Sur rune']);
    const reachable = (n: string) => {
      if (ticks.has(n)) return true;
      const r = w.d2rResolveItem ? w.d2rResolveItem(n) : null;
      if (r && r.kind && r.kind !== 'unique' && r.kind !== 'unknown') return true;   // set piece etc.
      if (r && r.canonical && ticks.has(r.canonical)) return true;                   // curly apostrophe
      if (ticks.has(String(n).replace(/\s*\([^)]+\)\s*$/, ''))) return true;          // display suffix
      if (VARIANTS[n] && ticks.has(VARIANTS[n])) return true;
      return false;
    };
    missing.forEach((x: any) => {
      if (reachable(x.n)) return;
      if (NOT_A_UNIQUE.has(x.n)) return;
      failures.push('UNREACHABLE: ' + x.n);
    });
    // lifecycle: run the STATE loop for every item via the same API the tick calls (fast path —
    // per-item DOM clicks at 300 items would be minutes of re-renders; the DOM path is proven by v644)
    for (const x of missing) {
      w.toggleOwned(x.n);
      const log1 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      const own1 = !!JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')[x.n];
      if (!own1) failures.push('NOT TALLIED: ' + x.n);
      if (!log1[x.n]) failures.push('NOT DATED: ' + x.n);
      w.toggleOwned(x.n);
      const log2 = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      const own2 = !!JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')[x.n];
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
