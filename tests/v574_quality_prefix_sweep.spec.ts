import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v574 — QUALITY-PREFIX RECOGNITION SWEEP (the "check for others like this" pass after the Superior Flail
// case): _baseCats' exact BASE_CLASS lookup missed any quality-prefixed name ("Superior X" / "Ethereal X" /
// "Eth X"), and the regex fallback has known gaps (flails, daggers, orbs, pelts, heads, claws — the very
// reason v386 added the exact map). _baseCats now retries with the prefix/suffix stripped BEFORE the regex,
// and suggestMule's bare-base BASE_CLASS lookup does the same. One fix at the source → every caller
// (throw-out cards + tips, Forge hand-class, meta-base safeguard, vault routing) inherits it.

const GAP_CASES = [
  'Superior Flail', 'Ethereal Flail', 'Superior Dagger', 'Eth Quhab', 'Ethereal Wolf Head',
  'Superior Blood Spirit', 'Eth Preserved Head', 'Superior Templar Coat', 'Superior War Fist',
  'Ethereal Suwayyah', 'Superior Bone Knife', 'Eth Scissors Quhab', 'Superior Flail (5os)',
  'Ethereal Thresher (4os)', 'Superior Monarch',
];

test('every quality-prefixed regex-gap base resolves its type, worthiness, and a sane route', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate((cases: string[]) => {
    const w: any = window;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));   // pin: routing is Chronicle-aware (v562)
    w.switchTab('tools'); w.renderVault && w.renderVault();
    return cases.map((n) => ({
      n,
      cats: Object.keys(w._baseCats(n) || {}).length,
      rw: w._isRunewordBase(n),
      route: (w.suggestMule(n) || {}).id,
    }));
  }, GAP_CASES);
  for (const c of r) {
    expect(c.cats, c.n + ' must resolve a base class').toBeGreaterThan(0);
    expect(c.rw, c.n + ' hosts runewords').toBe(true);
    expect(c.route, c.n + ' routes to the SOCKETED locker').toBe('bases');
  }
});

test('non-runeword prefixed bases still vendor (orbs socket gems only), plain names unchanged', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    w.switchTab('tools'); w.renderVault && w.renderVault();
    return {
      orbCats: Object.keys(w._baseCats('Superior Eagle Orb') || {}).length,
      orbRw: w._isRunewordBase('Superior Eagle Orb'),
      orbRoute: (w.suggestMule('Superior Eagle Orb') || {}).id,
      plainFlail: Object.keys(w._baseCats('Flail') || {}),
      plainMonarch: (w.suggestMule('Monarch') || {}).id,
    };
  });
  expect(r.orbCats).toBeGreaterThan(0);        // recognised as a base type…
  expect(r.orbRw).toBe(false);                 // …but orbs can't host runewords
  expect(r.orbRoute).toBe('__throwout');       // → vendor, exactly like the plain orb rule (v524)
  expect(r.plainFlail.length).toBeGreaterThan(0);
  expect(r.plainMonarch).toBe('bases');
});

// v575 — the SUPERIOR FLAIL chain, end to end: intake keeps 0-socket SUPERIOR bases as Larzuk candidates;
// the Forge cube-gamble fires for an owned unsocketed base that IS the word's ideal meta base (not just
// tagged ones); the throw-out card's "⚒ keep unsocketed" registers it into that flow.
test('v575 — unsocketed Superior Flail: gamble task fires (HotO need 4 < max 5, ideal base)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Superior Flail (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 1, Vex: 1, Pul: 1, Thul: 1 }));  // HotO runes
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');           // suppress the 47-seed so HotO is unmade
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Superior Flail (Larzuk base)');
    const s = w.forgeScan();
    const t = [...(s.pipeline || []), ...(s.now || [])].find((x: any) => x.rw === 'Heart of the Oak');
    return { found: !!t, gamble: !!(t && t.cubeGamble), baseName: t && t.base && t.base.base };
  });
  expect(r.found).toBe(true);                 // the owned Superior Flail is IN the plan, not "go get a base"
  expect(r.gamble).toBe(true);                // …as a cube-socket GAMBLE (Larzuk 5 overshoots HotO's 4)
  expect(String(r.baseName)).toMatch(/Flail/);
});

test('v575 — vaultKeepAsBase registers an unsocketed keeper from the throw-out review', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    localStorage.setItem('d2r_unknownReads', JSON.stringify(['Superior Flail']));
    location.reload();
  });
  await page.waitForTimeout(1800);
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.switchTab('tools'); w.renderVault && w.renderVault();
    await new Promise((res) => setTimeout(res, 300));
    const btn = !!Array.from(document.querySelectorAll('#vault-throwout button'))
      .find((b) => /keep unsocketed/i.test(b.textContent || ''));
    w.vaultKeepAsBase('Superior Flail');
    await new Promise((res) => setTimeout(res, 200));
    return {
      btn,
      owned: JSON.parse(localStorage.getItem('d2r_owned') || '[]').includes('Superior Flail (Larzuk base)'),
      cleared: !JSON.parse(localStorage.getItem('d2r_unknownReads') || '[]').includes('Superior Flail'),
    };
  });
  expect(r.btn).toBe(true);
  expect(r.owned).toBe(true);
  expect(r.cleared).toBe(true);
});
