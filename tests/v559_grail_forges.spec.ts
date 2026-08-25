import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v559 — GRAIL FORGES: Forge·Uniques + Forge·Sets, two ADDITIVE pillars sharing the flagship Forge shell
// (hero / KPI tiles / progress meter / cards) with pillar-specific FARM logic. The runeword Forge is untouched
// (its own battery guards it). Uniques sync ⇄ d2r_owned (the Calculator ✓); Sets sync ⇄ d2r_setPieces (the
// Item Set Tracker). Per-browser stores → a fresh profile (the cousin) naturally starts at zero.

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    // seed ONCE per tab — init scripts re-run on every navigation, and the v561 grail-import flow RELOADS
    // the page after writing the stores; without this guard the seed would wipe the just-imported data.
    if (!sessionStorage.getItem('__v559seeded')) {
      sessionStorage.setItem('__v559seeded', '1');
      localStorage.setItem('d2r_owned', '[]');
      localStorage.setItem('d2r_setPieces', '[]');
    }
  });
  await page.goto(URL); await page.waitForTimeout(1500);
});

test('Forge·Uniques renders the full shell: meter, 4 KPI tiles, hero, run cards', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('funi');
    const b = document.getElementById('funi-body')!;
    return {
      active: document.getElementById('tab-funi')!.classList.contains('active'),
      meter: !!b.querySelector('.forge-progress .fp-fill'),
      tiles: b.querySelectorAll('.forge-tabs .forge-tab').length,
      hero: !!b.querySelector('.forge-hero'),
      heroLead: b.querySelector('.fh-lead')?.textContent || '',
      runCards: b.querySelectorAll('.f-card').length,
      scan: (() => { const s = w.funiScan(); return { total: s.total, found: s.found, missing: s.missing.length, runs: s.runs.length, low: s.low.length, seedN: Object.keys(w._GRAIL_SEED || {}).length }; })(),
    };
  });
  expect(r.active).toBe(true);
  expect(r.meter).toBe(true);
  expect(r.tiles).toBe(4);
  expect(r.hero).toBe(true);
  expect(r.heroLead).toMatch(/best farm/i);
  expect(r.runCards).toBeGreaterThan(3);
  expect(r.scan.total).toBeGreaterThan(250);      // grail+high+common uniques
  /* v1695 — THE SEED IS A FLOOR, AND THIS ASSERTED IT WAS A CEILING. `found === seedN` held only
     while the boot seed was the ONLY way an item could be found; v1693 applied three genuine finds
     read off his own Chronicle (Fleshrender, Gloom's Trap, The Diggler), so found is now 246 against
     a 243 seed and the equality broke on work that was the entire point of the arc — his words:
     "from 236 it NEEDS TO GO UP".
     The exact roster numbers are pinned once, in v659_grail_seed.spec.ts. This spec owns the FORGE
     UI contract, so it states the contract instead of duplicating a constant that will move again
     the next time he farms something: the seed floors the boot, and missing is the remainder. */
  expect(r.scan.found, 'the seed is a FLOOR — found may exceed it, never fall below')
    .toBeGreaterThanOrEqual(r.scan.seedN);
  expect(r.scan.missing).toBe(r.scan.total - r.scan.found);
  expect(r.scan.runs).toBeGreaterThan(10);        // grouped by best source
});

test('v559.2 — runs are ranked by EXPECTED YIELD per hour (Σ kph/odds), the true farming metric', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    const runs = w.funiScan().runs.filter((x: any) => x.ev > 0);
    // v1549 — expected yield still ranks the list, but WITHIN a difficulty tier. Konyo asked for
    // "HELL then Nightmare then Normal in the hunts", so the tier leads and ev orders each tier;
    // a single global descent cannot hold once the list is allowed to step down a difficulty.
    let sorted = true;
    for (let i = 1; i < runs.length; i++) {
      if (runs[i - 1].diff !== runs[i].diff) continue;            // a tier boundary resets it
      if (runs[i - 1].ev < runs[i].ev - 1e-9) sorted = false;
    }
    let tiersDescend = true;
    for (let i = 1; i < runs.length; i++) if (runs[i - 1].diff < runs[i].diff) tiersDescend = false;
    return { sorted, tiersDescend, top: runs[0]?.boss, topEv: runs[0]?.ev, n: runs.length };
  });
  expect(r.sorted).toBe(true);        // descending expected-drops-per-hour INSIDE each tier
  expect(r.tiersDescend).toBe(true);  // …and the tiers themselves never climb back up
  expect(r.topEv).toBeGreaterThan(0);
});

test('Forge·Sets is PIECE-centric with the F·Uniques logic + IDENTICAL unified sub-tab names', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('funi');
    const uniLabels = [...document.querySelectorAll('#funi-body .forge-tabs .ft-lbl')].map((e) => e.textContent);
    w.switchTab('fsets');
    const b = document.getElementById('fsets-body')!;
    const setLabels = [...b.querySelectorAll('.forge-tabs .ft-lbl')].map((e) => e.textContent);
    const s = w.fsetsScan();
    return {
      active: document.getElementById('tab-fsets')!.classList.contains('active'),
      meter: !!b.querySelector('.forge-progress'),
      uniLabels, setLabels,
      runCards: b.querySelectorAll('.f-card.f-pipe').length,   // run cards, like F·Uniques
      pieceChips: b.querySelectorAll('.gf-piece').length,
      sets: s.sets.length, pieces: s.totalPieces,
      trackerNote: /Item Set Tracker/.test(b.textContent || ''),
    };
  });
  expect(r.active).toBe(true);
  expect(r.meter).toBe(true);
  expect(r.setLabels).toEqual(['All missing', 'Best runs', 'Quick wins', 'Found']);
  expect(r.setLabels).toEqual(r.uniLabels);       // Konyo: SAME exact sub-tab names — same logic, set or unique
  expect(r.sets).toBe(34);
  expect(r.pieces).toBeGreaterThan(130);          // 135 after the v559.1 restoration
  expect(r.runCards).toBeGreaterThan(2);          // farm-run cards lead, F·Uniques style
  expect(r.pieceChips).toBeGreaterThan(20);       // pieces are tickable chips inside run cards
  expect(r.trackerNote).toBe(true);               // checklists stay home in the Item Set Tracker (synced)
});

test('SYNC — ticking found in Forge·Uniques writes the SAME found LEDGER the Calculator uses (v677: d2r_foundLog)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('funi');
    const s = w.funiScan(); const before = s.found; const target = s.missing[0].n;
    w.grailFoundUni(null, target);   // ✓ found it
    const stored = Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}'));   // v677 — grail ticks land in the LEDGER, never the vault
    const after = w.funiScan();
    return { target, before, inOwned: stored.includes(target), foundNow: after.found, missingDropped: !after.missing.some((x: any) => x.n === target) };
  });
  expect(r.inOwned).toBe(true);          // the Calculator's store
  expect(r.foundNow).toBe(r.before + 1);   // v659 — boot starts at the 229 seed, not zero
  expect(r.missingDropped).toBe(true);   // left the hunt immediately
});

test('SYNC — ticking a piece in Forge·Sets writes d2r_setPieces; completing a set moves it to Complete', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('fsets');
    const s = w.fsetsScan();
    // v693.2 recalibration — the v682 seed floors 108 pieces: pick the smallest INCOMPLETE set and
    // tick only its MISSING pieces (blind-ticking a seeded piece UN-ticks it — the old red).
    const incomplete = s.sets.filter((x: any) => x.pieces.some((p: any) => !p.have));
    const smallest = incomplete.slice().sort((a: any, b: any) => a.pieces.length - b.pieces.length)[0];
    smallest.pieces.filter((p: any) => !p.have).forEach((p: any) => w.grailTogglePiece(null, p.name));
    const stored = JSON.parse(localStorage.getItem('d2r_setPieces') || '[]');
    const after = w.fsetsScan();
    const done = after.done.some((r2: any) => r2.name === smallest.name);
    return { set: smallest.name, allStored: smallest.pieces.every((p: any) => stored.includes(p.name)), done, havePieces: after.havePieces };
  });
  expect(r.allStored).toBe(true);
  expect(r.done).toBe(true);
  expect(r.havePieces).toBeGreaterThan(1);
});

test('the runeword Forge is UNTOUCHED: its scan + shell still render independently', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('forge');
    const s = w.forgeScan();
    return {
      active: document.getElementById('tab-forge')!.classList.contains('active'),
      buckets: ['now', 'pipeline', 'onestep', 'crafts'].every((k) => Array.isArray(s[k])),
      meter: !!document.querySelector('#tab-forge .forge-progress'),
      tiles: document.querySelectorAll('#tab-forge .forge-tabs .forge-tab').length,
    };
  });
  expect(r.active).toBe(true);
  expect(r.buckets).toBe(true);
  expect(r.meter).toBe(true);
  // v2099 — 6 → 5. v2096 gated the ⚗️ CRAFTS chip to the room that owns crafts, so the
  // chronicle draws five: All · One step · Make now · Pipeline · Completed. The orange
  // CRAFTS contract did not disappear — it moved to #tab-crafts, and v1621 now measures it
  // there. Measured: #tab-forge .forge-tab = 5, #tab-crafts .forge-tab = 6.
  expect(r.tiles).toBe(5);   // v2096 — the ⚗️ chip belongs to #tab-crafts now
});

test('nav: the two new tabs ride after Forge with HD icons; palette picks them up', async ({ page }) => {
  const r = await page.evaluate(() => {
    const tabs = [...document.querySelectorAll('.tabs .tab')].map((t: any) => t.dataset.tab);
    const funiIco = document.querySelector('.tabs .tab[data-tab="funi"] img.tab-hdico');
    const fsetsIco = document.querySelector('.tabs .tab[data-tab="fsets"] img.tab-hdico');
    return { order: tabs.slice(-3), funiIco: !!funiIco, fsetsIco: !!fsetsIco, count: tabs.length };
  });
  expect(r.count).toBe(19);   // v710.4 +TV·D · v2085 +Vault · v2094 +Crafts — measured, not assumed
  // v2099 — the workshop tail moved when the Vault got its own room: fsets · vault · tvd
  expect(r.order).toEqual(['fsets', 'vault', 'tvd']);
  expect(r.funiIco).toBe(true);
  expect(r.fsetsIco).toBe(true);
});

test('v561 — grail bulk-import: AI-read FOUND names batch-tick into the LEDGER + d2r_setPieces (v677)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  // fire the intake with a stubbed AI endpoint; the flow writes the stores then RELOADS to resync every view
  await page.evaluate(async () => {
    const w: any = window;
    w.fetch = () => Promise.resolve({ json: () => Promise.resolve({ items: ['The Stone of Jordan', 'Windforce', "Cow King's Horns", 'Totally Fake Item'], unrecognized: [] }) });
    const c = document.createElement('canvas'); c.width = 4; c.height = 4;
    const blob: Blob = await new Promise((res) => c.toBlob((b) => res(b!), 'image/jpeg'));
    w.grailIntake([new File([blob], 'g.jpg', { type: 'image/jpeg' })]);   // not awaited — it will navigate
  });
  await page.waitForLoadState('load');
  /* v2106 — WAIT FOR THE TOAST, DO NOT SLEEP AND HOPE. This was a fixed 2,600ms pause followed by a
     synchronous DOM read, and the toast it reads only lives 5,200ms — so on a loaded CI runner the
     boot outran the sleep and the node was not there yet. Measured across tonight's runs: RED at
     c99cc692's parent, GREEN at c99cc692, RED again at c1d4efac, with nothing touching grail import
     in between. That is a flake, and a gate that is sometimes red has stopped carrying information
     — the same defect as one that is always green. Polling for the node removes the timing
     dependence without weakening a single assertion. [[feedback-blind-fixture-green-gate]] */
  await page.locator('.forge-toast').first().waitFor({ state: 'attached', timeout: 15000 });
  const r = await page.evaluate(() => {
    const owned = Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}'));   // v677
    const pieces = JSON.parse(localStorage.getItem('d2r_setPieces') || '[]');
    const toast = document.querySelector('.forge-toast');
    const scan = (window as any).funiScan();
    return {
      soj: owned.includes('The Stone of Jordan'), wf: owned.includes('Windforce'),
      cow: pieces.includes("Cow King's Horns (war bonnet)"),
      fakeNotOwned: !owned.includes('Totally Fake Item'),
      toast: toast ? (toast.textContent || '') : '',
      foundNow: scan.found,
    };
  });
  expect(r.soj).toBe(true);
  expect(r.wf).toBe(true);
  expect(r.cow).toBe(true);            // clean name mapped back to the full "(war bonnet)" piece
  expect(r.fakeNotOwned).toBe(true);   // junk never enters the stores
  expect(r.toast).toMatch(/Grail imported/);
  expect(r.toast).toMatch(/\+2 uniques/);
  expect(r.foundNow).toBeGreaterThanOrEqual(2);   // the Uniques Forge sees them immediately post-reload
});
