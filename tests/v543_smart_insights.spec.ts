import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v543 — Smart Chronicle Insights: three panels that read your live Chronicle (d2r_rwMade) + owned bases + rune
// stash, same brain as the loot filter. Progress dashboard · Farm-priority (bases ranked by how many unmade
// runewords each unlocks) · Rune radar (runes you're short on). All pure derivation — no AI, no server.

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 5, Tir: 5, Tal: 5, Sol: 5, Amn: 3, Ber: 0, Jah: 1, Ith: 2 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({ 'Enigma': 'x', 'Spirit': 'x', 'Rhyme': 'x' }));   // v578.1 — explicit small chronicle (fresh profile)
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
});

test('_smartProgress reads the Chronicle: total 100, made floor, remaining, and task buckets', async ({ page }) => {
  const p = await page.evaluate(() => (window as any)._smartProgress());
  expect(p.total).toBe(100);
  expect(p.made).toBeGreaterThan(0);
  expect(p.remaining).toBe(p.total - p.made);
  expect(p.made + p.remaining).toBe(100);
  expect(typeof p.makeNow).toBe('number');
  expect(typeof p.blockedByBase).toBe('number');
});

test('_smartFarmPriority ranks bases by how many unmade runewords each unlocks (desc)', async ({ page }) => {
  const fp = await page.evaluate(() => (window as any)._smartFarmPriority());
  expect(fp.length).toBeGreaterThan(5);
  // sorted descending by count
  for (let i = 1; i < fp.length; i++) expect(fp[i - 1].count).toBeGreaterThanOrEqual(fp[i].count);
  // top base unlocks several, and lists the runewords it serves
  expect(fp[0].count).toBeGreaterThan(1);
  expect(fp[0].runewords.length).toBe(fp[0].count);
});

test('_smartRuneGating surfaces only runes you are SHORT on, ranked by shortfall', async ({ page }) => {
  const rg = await page.evaluate(() => (window as any)._smartRuneGating());
  expect(rg.length).toBeGreaterThan(0);
  for (let i = 1; i < rg.length; i++) expect(rg[i - 1].short).toBeGreaterThanOrEqual(rg[i].short);
  rg.forEach((x: any) => { expect(x.short).toBeGreaterThan(0); expect(x.short).toBe(x.demand - x.owned); });
  // Ber was seeded at 0 and is needed by several words → must appear
  expect(rg.some((x: any) => x.rune === 'Ber')).toBe(true);
});

test('nextUnlock base in progress === the #1 farm-priority base (the panels agree)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    return { next: w._smartProgress().nextUnlockBase, topFarm: w._smartFarmPriority()[0].base };
  });
  expect(r.next).toBe(r.topFarm);
});

test('renderSmartInsights paints all 3 panels into the Tools card', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('tools'); w.renderSmartInsights();
    const t = (document.getElementById('smart-insights-body')?.textContent) || '';
    return {
      card: !!document.getElementById('smart-insights-card'),
      progress: /Progress/.test(t), farm: /Farm priority/.test(t), rune: /Rune radar/.test(t),
      bestNow: /Best you can make now/.test(t), leverage: /Highest-leverage base/.test(t),
    };
  });
  expect(r.card).toBe(true);
  expect(r.progress).toBe(true);
  expect(r.farm).toBe(true);
  expect(r.rune).toBe(true);
  expect(r.bestNow).toBe(true);
  expect(r.leverage).toBe(true);
});
