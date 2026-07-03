import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v559 — GRAIL FORGES: Forge·Uniques + Forge·Sets, two ADDITIVE pillars sharing the flagship Forge shell
// (hero / KPI tiles / progress meter / cards) with pillar-specific FARM logic. The runeword Forge is untouched
// (its own battery guards it). Uniques sync ⇄ d2r_owned (the Calculator ✓); Sets sync ⇄ d2r_setPieces (the
// Item Set Tracker). Per-browser stores → a fresh profile (the cousin) naturally starts at zero.

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', '[]');
    localStorage.setItem('d2r_setPieces', '[]');
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
      scan: (() => { const s = w.funiScan(); return { total: s.total, missing: s.missing.length, runs: s.runs.length, low: s.low.length }; })(),
    };
  });
  expect(r.active).toBe(true);
  expect(r.meter).toBe(true);
  expect(r.tiles).toBe(4);
  expect(r.hero).toBe(true);
  expect(r.heroLead).toMatch(/best farm/i);
  expect(r.runCards).toBeGreaterThan(3);
  expect(r.scan.total).toBeGreaterThan(250);      // grail+high+common uniques
  expect(r.scan.missing).toBe(r.scan.total);      // fresh profile → everything missing
  expect(r.scan.runs).toBeGreaterThan(10);        // grouped by best source
});

test('Forge·Sets renders 32 set checklists / 127 pieces with tickable chips', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('fsets');
    const b = document.getElementById('fsets-body')!;
    const s = w.fsetsScan();
    return {
      active: document.getElementById('tab-fsets')!.classList.contains('active'),
      meter: !!b.querySelector('.forge-progress'),
      tiles: b.querySelectorAll('.forge-tabs .forge-tab').length,
      setCards: b.querySelectorAll('.f-card').length,
      pieceChips: b.querySelectorAll('.gf-piece').length,
      sets: s.sets.length, pieces: s.totalPieces,
    };
  });
  expect(r.active).toBe(true);
  expect(r.meter).toBe(true);
  expect(r.tiles).toBe(4);
  expect(r.sets).toBe(32);
  expect(r.pieces).toBeGreaterThan(100);
  expect(r.setCards).toBeGreaterThanOrEqual(32);
  expect(r.pieceChips).toBeGreaterThan(100);
});

test('SYNC — ticking found in Forge·Uniques writes the SAME d2r_owned the Calculator uses', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('funi');
    const s = w.funiScan(); const target = s.missing[0].n;
    w.grailFoundUni(null, target);   // ✓ found it
    const stored = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
    const after = w.funiScan();
    return { target, inOwned: stored.includes(target), foundNow: after.found, missingDropped: !after.missing.some((x: any) => x.n === target) };
  });
  expect(r.inOwned).toBe(true);          // the Calculator's store
  expect(r.foundNow).toBe(1);
  expect(r.missingDropped).toBe(true);   // left the hunt immediately
});

test('SYNC — ticking a piece in Forge·Sets writes d2r_setPieces; completing a set moves it to Complete', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('fsets');
    const s = w.fsetsScan();
    const smallest = s.sets.slice().sort((a: any, b: any) => a.pieces.length - b.pieces.length)[0];
    smallest.pieces.forEach((p: any) => w.grailTogglePiece(null, p.name));   // tick every piece
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
  expect(r.tiles).toBe(6);   // the original 6 sub-tabs, unchanged
});

test('nav: the two new tabs ride after Forge with HD icons; palette picks them up', async ({ page }) => {
  const r = await page.evaluate(() => {
    const tabs = [...document.querySelectorAll('.tabs .tab')].map((t: any) => t.dataset.tab);
    const funiIco = document.querySelector('.tabs .tab[data-tab="funi"] img.tab-hdico');
    const fsetsIco = document.querySelector('.tabs .tab[data-tab="fsets"] img.tab-hdico');
    return { order: tabs.slice(-3), funiIco: !!funiIco, fsetsIco: !!fsetsIco, count: tabs.length };
  });
  expect(r.count).toBe(15);
  expect(r.order).toEqual(['forge', 'funi', 'fsets']);
  expect(r.funiIco).toBe(true);
  expect(r.fsetsIco).toBe(true);
});
