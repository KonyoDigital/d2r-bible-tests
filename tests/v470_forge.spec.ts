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
  const s = await scan(page, { owned: ['Colossus Voulge (4os)'], runes: { Ral: 1, Tir: 1, Tal: 1, Sol: 1 } });
  const t = find(s.now, 'Insight');
  expect(t).toBeTruthy();
  expect(t.deferred).toBe(false);
  expect(t.base.base).toBe('Colossus Voulge');
  expect(t.base.sockets).toBe(4);
  expect(t.ideal).toBe(true);   // Colossus Voulge (max 4) is the socket-correct merc polearm for Insight (4os)
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
  expect(t.bestStr).toContain('Colossus Voulge');   // socket-correct merc polearm: Insight is 4os → Colossus Voulge (max 4), not the 5os Thresher
});

test('NO BASE-UPGRADE bucket — white/normal bases cannot be cube-upgraded (v534/v542, game-file confirmed)', async ({ page }) => {
  // cubemain.txt: tier-upgrade recipes accept unique/rare/set only — never a normal/superior/magic white base.
  const s = await scan(page, { owned: ['Wand (2os)', 'Crystal Sword (Larzuk base)', 'Bone Helm (Larzuk base)'] });
  expect('upgrades' in s).toBe(false);   // v542 — the whole "Base upgrades" bucket is REMOVED entirely
});

test('SAFEGUARD — Larzuk gives only a base\'s MAX, so a sub-max word is NOT pipelined on a too-big base', async ({ page }) => {
  // Spirit = 4os; a Crystal Sword maxes at 6, so Larzuk always gives 6 → it can NOT make a 4os Spirit.
  const s = await scan(page, { owned: ['Crystal Sword (Larzuk base)'], runes: { Tal: 1, Thul: 1, Ort: 1, Amn: 1 } });
  expect((s.pipeline || []).find((t: any) => t.rw === 'Spirit')).toBeFalsy();   // the old "Larzuk → 4os" bug — gone
  // invariant: a pipeline task NEVER targets fewer sockets than its base's verified max
  (s.pipeline || []).forEach((t: any) => { if (t.base && t.base.max) expect(t.need).toBe(t.base.max); });
});

test('OPTIMAL ASSIGNMENT — two 6os bases let two 6os words BOTH be make-now (no false defer)', async ({ page }) => {
  // Two 6os 1-HANDED bases (Phase Blade + Berserker Axe) + runes for two 6os 1H words. Both should be
  // "make now" (one per base), NOT one deferred because the engine only tried a single base. (1H per the
  // hand rule — a 2H Grim Scythe would NOT satisfy a 1H player word.)
  const s = await scan(page, {
    owned: ['Phase Blade (6os)', 'Berserker Axe (6os)'],
    runes: { Vex: 2, Hel: 2, El: 2, Eld: 2, Zod: 2, Eth: 2, Dol: 2, Ist: 2, Tir: 2 },  // BotD + Silence runes
  });
  const live = s.now.filter((t: any) => !t.deferred).map((t: any) => t.rw);
  expect(live).toContain('Breath of the Dying');
  expect(live).toContain('Silence');               // the previously-deferred word now uses the free 2nd base
  // and the two live words used two DIFFERENT bases
  const botd = s.now.find((t: any) => t.rw === 'Breath of the Dying');
  const sil = s.now.find((t: any) => t.rw === 'Silence');
  expect(botd.base.name).not.toBe(sil.base.name);
});

test('META-BASE RULE — 1H for player weapons, 2H only for merc, armour never gets a weapon base', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const isWeaponBase = (n: string) => { const c = w._baseCats ? w._baseCats(n) : {}; return !!c['weapon']; };
    const bad: string[] = [];
    Object.keys(w.RUNEWORD_TIP).forEach((rw: string) => {
      const b = String((w.RUNEWORD_TIP[rw] || {}).b || '').toLowerCase();
      const nonWeapon = /body armor|shield|aegis|\bward\b|targe|rondache|helm|circlet|\bcap\b|crown|diadem|tiara/.test(b);
      const names = (w._forgeMetaBase(rw).names) || [];
      if (nonWeapon) names.forEach((n: string) => { if (isWeaponBase(n)) bad.push('ARMOUR/SHIELD/HELM ' + rw + ' → weapon base ' + n); });
    });
    return { bad, botd: w._forgeMetaBase('Breath of the Dying').names.join(' / '),
             coh: w._forgeMetaBase('Chains of Honor').names.join(' / '),
             insight: w._forgeMetaBase('Insight').names.join(' / ') };
  });
  expect(r.bad).toEqual([]);                                  // SAFEGUARD: no armour/shield/helm word recommends a weapon base
  expect(r.botd).toMatch(/Berserker Axe|Phase Blade/);        // player weapon → 1H
  expect(r.botd).not.toContain('Colossus Blade');             // not the 2H sword
  expect(r.coh).not.toMatch(/Colossus|Blade|Axe|Sword/);      // Chains of Honor is body armor → no weapon
  expect(r.insight).toMatch(/Thresher|Cryptic Axe|Colossus Voulge/);  // merc polearm → 2H is correct here
});

test('_upgradeChainFor is REMOVED entirely — the cube-upgrade concept no longer exists in code (v542)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    return { fnType: typeof w._upgradeChainFor };   // was a null stub (v534) → now the function is gone (v542)
  });
  expect(r.fnType).toBe('undefined');
});
