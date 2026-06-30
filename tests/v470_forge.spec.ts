import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v470 — FORGE: the AI Organizer / task-doer motherboard. Simulation tests that seed the SAME live
// state the four tools write (runeStash · gemStash · owned + EXTRA_ITEMS socketed bases · rwMade) and
// assert forgeScan() produces the right directive task plan. Test runewords (Insight/White/Black) are
// deliberately NOT in the 44-seed Chronicle floor, so they read as still-to-make.

type Seed = { owned?: string[], runes?: Record<string,number>, gems?: Record<string,number>, made?: Record<string,string> };

async function scan(page: any, seed: Seed) {
  await page.addInitScript((s: Seed) => {
    localStorage.setItem('d2r_owned', JSON.stringify(s.owned || []));
    localStorage.setItem('d2r_runeStash', JSON.stringify(s.runes || {}));
    localStorage.setItem('d2r_gemStash', JSON.stringify(s.gems || {}));
    localStorage.setItem('d2r_rwMade', JSON.stringify(s.made || {}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, seed);
  await page.goto(URL);
  await page.waitForTimeout(1300);
  return await page.evaluate((owned: string[]) => {
    const w: any = window;
    (owned || []).forEach((n) => w._ensureSocketBaseEntry(n));   // build EXTRA_ITEMS socketed entries for seeded bases
    return w.forgeScan();
  }, seed.owned || []);
}
const find = (arr: any[], rw: string) => (arr || []).find((t) => t.rw === rw);

test('the Forge tab, button, and engine exist', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      btn: !!document.querySelector('.tab[data-tab="forge"]'),
      panel: !!document.getElementById('tab-forge'),
      body: !!document.getElementById('forge-body'),
      scan: typeof w.forgeScan === 'function',
      render: typeof w.renderForge === 'function',
    };
  });
  expect(r.btn).toBe(true);
  expect(r.panel).toBe(true);
  expect(r.body).toBe(true);
  expect(r.scan).toBe(true);
  expect(r.render).toBe(true);
});

test('MAKE NOW — runes in hand + an exact-socket base → ready, with the ideal-base flag', async ({ page }) => {
  const s = await scan(page, { owned: ['Thresher (4os)'], runes: { Ral: 1, Tir: 1, Tal: 1, Sol: 1 } });
  const t = find(s.now, 'Insight');
  expect(t).toBeTruthy();
  expect(t.deferred).toBe(false);
  expect(t.base.base).toBe('Thresher');
  expect(t.base.sockets).toBe(4);
  expect(t.ideal).toBe(true);   // Thresher is the bible's meta merc base for Insight (RW_BASES sync)
});

test('PIPELINE — an unsocketed base + runes in hand → socket-then-forge, not "make now"', async ({ page }) => {
  const s = await scan(page, { owned: ['Colossus Voulge (Larzuk base)'], runes: { Ral: 1, Tir: 1, Tal: 1, Sol: 1 } });
  const p = find(s.pipeline, 'Insight');
  expect(p).toBeTruthy();
  expect(p.need).toBe(4);
  expect(find(s.now, 'Insight')).toBeFalsy();   // not "make now" — it needs socketing first
});

test('ONE STEP AWAY — base ready but a rune missing → names the gap', async ({ page }) => {
  const s = await scan(page, { owned: ['Thresher (4os)'], runes: { Ral: 1, Tir: 1, Tal: 1 } });   // no Sol
  const t = find(s.onestep, 'Insight');
  expect(t).toBeTruthy();
  expect(t.sub).toBe('runes');
  expect((t.missing || []).join(' ')).toContain('Sol');
  expect(find(s.now, 'Insight')).toBeFalsy();
});

test('CHRONICLE SYNC — marking it created removes it from Forge automatically', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Thresher (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Thresher (4os)');
    const before = w.forgeScan().now.some((t: any) => t.rw === 'Insight');
    w.rwToggleMade('Insight');                       // ✓ mark created (same path the Chronicle button fires)
    const after = w.forgeScan().now.some((t: any) => t.rw === 'Insight');
    return { before, after };
  });
  expect(r.before).toBe(true);
  expect(r.after).toBe(false);
});

test('CONTENTION — two ready runewords share the only Io → one auto-deferred, honestly flagged', async ({ page }) => {
  const s = await scan(page, {
    owned: ['Wand (2os)', 'Flail (3os)'],          // White (wand) + Black (mace/flail)
    runes: { Dol: 1, Io: 1, Thul: 1, Nef: 1 },      // both need Io, only ONE owned
  });
  const white = find(s.now, 'White');
  const black = find(s.now, 'Black');
  expect(white).toBeTruthy();
  expect(black).toBeTruthy();
  // exactly one is live, the other deferred (never two false "ready"s)
  const deferred = [white, black].filter((t) => t.deferred);
  expect(deferred.length).toBe(1);
  expect((deferred[0].blockedBy || [])).toContain('Io');
  expect(s.counts.deferred).toBeGreaterThanOrEqual(1);
});

test('CRAFTS — a Perfect Amethyst + Ral surfaces a Caster Amulet task', async ({ page }) => {
  const s = await scan(page, { gems: { 'Perfect Amethyst': 1 }, runes: { Ral: 1 } });
  const c = (s.crafts || []).find((x: any) => x.craft === 'Caster' && x.slot === 'Amulet');
  expect(c).toBeTruthy();
  expect(c.gem).toBe('Perfect Amethyst');
  expect(c.rune).toBe('Ral');
});

test('PIPELINE (cube) — base needs sockets AND the runes need cubing up', async ({ page }) => {
  const s = await scan(page, { owned: ['Colossus Voulge (Larzuk base)'], runes: { Ral: 1, Tir: 1, Tal: 1, Amn: 3 } });  // 3 Amn → cube to Sol
  const p = find(s.pipeline, 'Insight');
  expect(p).toBeTruthy();
  expect(p.sub).toBe('cube');
  expect(p.need).toBe(4);
});

test('ONE STEP (cube-up) — base ready, missing rune obtainable by cubing', async ({ page }) => {
  const s = await scan(page, { owned: ['Thresher (4os)'], runes: { Ral: 1, Tir: 1, Tal: 1, Amn: 3 } });  // no Sol, but 3 Amn cubes to it
  const t = find(s.onestep, 'Insight');
  expect(t).toBeTruthy();
  expect(t.sub).toBe('cube');
  expect(find(s.now, 'Insight')).toBeFalsy();
});

test('NEED A BASE — runes in hand but no matching base → names the meta base to socket', async ({ page }) => {
  const s = await scan(page, { owned: [], runes: { Ral: 1, Tir: 1, Tal: 1, Sol: 1 } });   // have Insight runes, no base at all
  const t = find(s.onestep, 'Insight');
  expect(t).toBeTruthy();
  expect(t.sub).toBe('base');
  expect(t.bestStr).toContain('Thresher');   // RW_BASES meta merc base named for me
});

test('BASE UPGRADE — a Normal runeword base surfaces a cube-up-to-elite pipeline', async ({ page }) => {
  const s = await scan(page, { owned: ['Wand (2os)'] });   // Wand = normal-tier weapon that hosts runewords
  const u = (s.upgrades || []).find((x: any) => x.base.base === 'Wand');
  expect(u).toBeTruthy();
  expect(u.tier).toBe('normal');
  expect(u.steps.length).toBe(2);                          // Normal → Exceptional → Elite
  expect(u.steps[0].recipe).toContain('Perfect Emerald');  // weapon recipe
  expect(u.rws.length).toBeGreaterThan(0);
});

test('SAFEGUARD — Larzuk gives only a base\'s MAX, so a sub-max word is NOT pipelined on a too-big base', async ({ page }) => {
  // Spirit = 4os; a Crystal Sword maxes at 6, so Larzuk always gives 6 → it can NOT make a 4os Spirit.
  const s = await scan(page, { owned: ['Crystal Sword (Larzuk base)'], runes: { Tal: 1, Thul: 1, Ort: 1, Amn: 1 } });
  expect((s.pipeline || []).find((t: any) => t.rw === 'Spirit')).toBeFalsy();   // the old "Larzuk → 4os" bug — gone
  // invariant: a pipeline task NEVER targets fewer sockets than its base's verified max
  (s.pipeline || []).forEach((t: any) => { if (t.base && t.base.max) expect(t.need).toBe(t.base.max); });
});
