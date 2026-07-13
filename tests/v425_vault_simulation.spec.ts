import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v425 — VAULT-MANAGER SIMULATION. Walks every item the bible knows (grail uniques/sets/bases + off-grail
// + set pieces + runewords) and asserts the vault routes/mules/saves each one correctly, then a 450-item
// load/capacity pass to prove the vault holds the data without crashing. (Konyo: "simulate all items… make
// sure routing, muling, SAVING the correct things… no fabrications… verify simulate ship end-to-end.")

const VALID_MULES = ['sets-major','sets-rest','uni-weap','uni-armor','uni-small','runewords','bases','magic-rare','shared','dupes','wip'];

test('every item routes to a valid destination — no nulls, no unknown mules, no throws', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate((validMules) => {
    const w: any = window;
    const all: string[] = w.__allItemNames();
    const valid = new Set(validMules);
    const special = new Set(['__keep', '__throwout']);
    const anomalies: any[] = [];
    let routed = 0, kept = 0, shared = 0;
    all.forEach((n) => {
      let id: any;
      try { id = (w.suggestMule(n) || {}).id; }
      catch (e) { anomalies.push({ n, err: 'suggestMule threw: ' + (e as any).message }); return; }
      try { w._isEthereal(n); } catch (e) { anomalies.push({ n, err: '_isEthereal threw' }); }
      try { w._isSuperior(n); } catch (e) { anomalies.push({ n, err: '_isSuperior threw' }); }
      if (id == null) {
        if (w.isSharedStash(n)) { shared++; return; }     // shared-stash items legitimately don't mule
        anomalies.push({ n, why: 'null route but NOT shared-stash' }); return;
      }
      if (special.has(id)) { kept++; return; }
      if (valid.has(id)) { routed++; return; }
      anomalies.push({ n, why: 'unknown mule id: ' + id });
    });
    return { total: all.length, routed, kept, shared, anomalies };
  }, VALID_MULES);
  console.log(`simulated ${r.total} items — routed:${r.routed} kept:${r.kept} shared:${r.shared}`);
  if (r.anomalies.length) console.log('ANOMALIES:', JSON.stringify(r.anomalies.slice(0, 30), null, 1));
  expect(r.total).toBeGreaterThanOrEqual(1200);   // v430 — the FULL catalog (grail + off-grail + set pieces + runewords + all 498 bases), not just 799
  expect(r.anomalies).toEqual([]);
  expect(consoleErrors).toEqual([]);
});

test('never-mule keepers are SAVED (Gheed\'s / Anni / Torch → __keep), sunders shared', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const id = (n: string) => (w.suggestMule(n) || {}).id;
    return {
      gheeds: id("Gheed's Fortune"), anni: id('Annihilus'), torch: id('Hellfire Torch'),
      sunderShared: w.isSharedStash('Latent Cold Rupture'),
      istShared: w.isSharedStash('Ist rune'),
    };
  });
  expect(r.gheeds).toBe('__keep');
  expect(r.anni).toBe('__keep');
  expect(r.torch).toBe('__keep');
  expect(r.sunderShared).toBe(true);
  expect(r.istShared).toBe(true);
});

test('rune-named BASES route to SOCKETED, not shared-stash (the \\brune\\b collision)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));   // v580.2 — pin: routing is Chronicle-aware
    const id = (n: string) => (w.suggestMule(n) || {}).id;
    return {
      runeSword: id('Rune Sword (5os)'), runeBow: id('Rune Bow (4os)'),
      runeStaff: id('Rune Staff (4os)'), runeScepter: id('Rune Scepter (3os)'),
      sharedSword: w.isSharedStash('Rune Sword (5os)'),
    };
  });
  expect(r.runeSword).toBe('bases');
  expect(r.runeBow).toBe('bases');
  expect(r.runeStaff).toBe('bases');
  expect(r.runeScepter).toBe('bases');
  expect(r.sharedSword).toBe(false);
});

test('identifier coverage — every item resolves a rarity/tier + class; set pieces are green', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const all: string[] = w.__allItemNames();
    const noRarity: string[] = [];
    all.forEach((n) => { if (!w._artRarity(n)) noRarity.push(n); });
    const bases = w.BASE_CLASS ? Object.keys(w.BASE_CLASS) : [];
    const noClass = bases.filter((b: string) => { try { return !Object.keys(w._baseCats(b) || {}).length; } catch (e) { return true; } });
    return {
      total: all.length, noRarity: noRarity.length, noRaritySample: noRarity.slice(0, 10),
      baseCount: bases.length, noClass: noClass.length,
      setPieceGreen: w._artRarity("Tal Rasha's Adjudication") === 'set' && w._artRarity("Immortal King's Will") === 'set',
      runeSwordNotRune: w._artRarity('Rune Sword (5os)') !== 'rune',
      istRune: w._artRarity('Ist rune') === 'rune',
    };
  });
  console.log(`rarity coverage — ${r.total} items, ${r.noRarity} without rarity; ${r.baseCount} bases, ${r.noClass} without class`);
  if (r.noRarity) console.log('NO-RARITY:', JSON.stringify(r.noRaritySample));
  expect(r.noRarity).toBe(0);          // every item has a tier/rarity identifier
  expect(r.noClass).toBe(0);           // every base resolves a class
  expect(r.setPieceGreen).toBe(true);  // set pieces resolve green rarity
  expect(r.runeSwordNotRune).toBe(true);
  expect(r.istRune).toBe(true);
});

test('LOAD/CAPACITY — 450 owned items register, render, and persist without crashing', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  // seed 450 real item names into owned BEFORE the app boots
  await page.goto(URL); await page.waitForTimeout(1500);
  const names: string[] = await page.evaluate(() => (window as any).__allItemNames().slice(0, 450));
  // v681 — the v677 boot cleanse strips grail-seed + uni-extra names from d2r_owned unless they're
  // mule-assigned, so mule-assign ONLY that subset to keep all 450 physical. The remaining (non-grail)
  // names stay unassigned → they persist via the registry prune AND render as loose .vault-chip, so the
  // 450-item load/capacity pass still exercises both persistence and chip rendering.
  await page.evaluate((ns) => {
    localStorage.setItem('d2r_owned', JSON.stringify(ns));
    const w: any = window;
    const seed = w._GRAIL_SEED || {}, uex = w._UNI_EXTRA || {};
    const ma: Record<string, string> = {};
    ns.forEach((n) => { if (seed[n] || uex[n]) ma[n] = 'wip'; });
    localStorage.setItem('d2r_muleAssign', JSON.stringify(ma));
  }, names);
  await page.reload(); await page.waitForTimeout(2200);
  const r = await page.evaluate(() => {
    const w: any = window;
    let rendered = -1, threw = '';
    try { if (typeof w.renderVault === 'function') w.renderVault(); } catch (e) { threw = (e as any).message; }
    try { rendered = document.querySelectorAll('.vault-chip').length; } catch (e) {}
    const ownedSaved = JSON.parse(localStorage.getItem('d2r_owned') || '[]').length;
    return { ownedSaved, rendered, threw };
  });
  console.log(`load test — owned persisted:${r.ownedSaved} chips rendered:${r.rendered} threw:"${r.threw}"`);
  expect(r.threw).toBe('');
  expect(r.ownedSaved).toBe(450);
  expect(r.rendered).toBeGreaterThan(50);   // the vault painted a substantial set of chips
  expect(consoleErrors).toEqual([]);
});
