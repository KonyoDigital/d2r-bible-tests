import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v524 — SINGLE SOURCE OF TRUTH for base keep/discard: a white base is a SOCKETED keeper only if it can hold
// a runeword (_baseRunewords > 0 = _isRunewordBase). Full 498-base audit guard: circlets/orbs/javelins/
// throwing/belts/boots/gloves = NON-runeword → throw-out; grimoires (Vigilance) + all real weapon/armor/
// shield/helm bases = kept. Locks the platform-wide sync (Forge + vault use the same _baseRunewords).

test.beforeEach(async ({ page }) => { await page.goto(URL); await page.waitForTimeout(1600); });

test('_isRunewordBase + suggestMule agree across the whole base batch (no false discards)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    const bases: string[] = (typeof w.BASE_CLASS !== 'undefined') ? Object.keys(w.BASE_CLASS) : [];
    let kept = 0, thrown = 0, mismatch: string[] = [];
    bases.forEach((b) => {
      const rw = w._isRunewordBase(b);
      const route = (w.suggestMule(b) || {}).id;
      if (route === 'bases') kept++;
      if (route === '__throwout') thrown++;
      // a WHITE base's route must agree with its runeword-worthiness (rw → bases, non-rw → throwout)
      if (rw && route === '__throwout') mismatch.push(b + ' (rw but thrown)');
      if (!rw && route === 'bases') mismatch.push(b + ' (non-rw but kept)');
    });
    return { total: bases.length, kept, thrown, mismatch };
  });
  expect(r.total).toBeGreaterThan(490);
  expect(r.mismatch).toEqual([]);           // ZERO mismatches — the whole platform is synced
  expect(r.kept).toBeGreaterThan(390);      // ~404 runeword-worthy bases kept
  expect(r.thrown).toBeGreaterThan(80);     // ~94 non-runeword bases thrown out
});

test('GRIMOIRES hold Vigilance → runeword-worthy → kept (the _RW_TYPE plural gap fix)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    const rw = (n: string) => (w._baseRunewords(n) || []).map((x: any) => x.n);
    return {
      grimoire: rw('Blasphemous Grimoire'),
      codex: rw('Occult Codex'),
      tome: rw('Dark Tome'),
      grimoireIsRW: w._isRunewordBase('Blasphemous Grimoire'),
      grimoireRoute: (w.suggestMule('Blasphemous Grimoire') || {}).id,
    };
  });
  expect(r.grimoire).toContain('Vigilance');   // was [] before the fix
  expect(r.codex).toContain('Vigilance');
  expect(r.tome).toContain('Vigilance');
  expect(r.grimoireIsRW).toBe(true);
  expect(r.grimoireRoute).toBe('bases');        // kept, not thrown out
});

test('non-runeword bases (circlet/orb/javelin/throwing/belt/boot/glove) → throw-out', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    const route = (n: string) => (w.suggestMule(n) || {}).id;
    return {
      tiara: route('Tiara'), diadem: route('Diadem'),
      orb: route('Eldritch Orb'), javelin: route('Matriarchal Javelin'),
      throwAxe: route('Winged Axe'), belt: route('Mesh Belt'),
      boots: route('Chain Boots'), gloves: route('Heavy Gloves'),
      // regression: real runeword bases stay kept
      monarch: route('Monarch'), phase: route('Phase Blade'), archon: route('Archon Plate'),
    };
  });
  ['tiara','diadem','orb','javelin','throwAxe','belt','boots','gloves'].forEach((k) =>
    expect((r as any)[k]).toBe('__throwout'));
  ['monarch','phase','archon'].forEach((k) =>
    expect((r as any)[k]).toBe('bases'));
});

test('a RARE circlet is a keeper (MAGIC & RARE locker); white/magic circlet is not', async ({ page }) => {
  // magicFinds is a module let loaded from localStorage — seed it BEFORE the page loads
  await page.addInitScript(() => {
    localStorage.setItem('d2r_magicFinds', JSON.stringify({
      'Viper Coronet of the Whale': { q: 'rare', base: 'Coronet', mods: [] },
      'Coronet of Frost': { q: 'magic', base: 'Coronet', mods: [] },
    }));
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      rare: (w.suggestMule('Viper Coronet of the Whale') || {}).id,
      magic: (w.suggestMule('Coronet of Frost') || {}).id,
    };
  });
  expect(r.rare).toBe('magic-rare');   // RARE circlet → keeper
  expect(r.magic).toBe('__throwout');  // MAGIC circlet → vendor (Konyo: only rare)
});
