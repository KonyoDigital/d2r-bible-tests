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
    // v562 — routing also reads the Chronicle now (all hostable words ✓ forged → throw-out), and a fresh
    // profile seeds Konyo's real 45-word Chronicle. Pin an EMPTY Chronicle so this audit keeps checking the
    // capability agreement (_isRunewordBase ⇄ route); Chronicle-driven throw-outs are specced in v562.
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    const bases: string[] = (typeof w.BASE_CLASS !== 'undefined') ? Object.keys(w.BASE_CLASS) : [];
    let kept = 0, thrown = 0, mismatch: string[] = [];
    bases.forEach((b) => {
      const rw = w._isRunewordBase(b);
      // v580.2 — the route's source of truth is the CHRONICLE-AWARE + endgame-gated keeper list
      // (_baseUnmadeRunewords, v562/v576), not raw capability: a base whose every word is made/gated
      // legitimately vendors even though it CAN host runewords.
      const keeps = (w._baseUnmadeRunewords(b, 0) || []).length > 0;
      const route = (w.suggestMule(b) || {}).id;
      if (route === 'bases') kept++;
      if (route === '__throwout') thrown++;
      if (keeps && route === '__throwout') mismatch.push(b + ' (still-needed but thrown)');
      if (!rw && route === 'bases') mismatch.push(b + ' (non-rw but kept)');
    });
    return { total: bases.length, kept, thrown, mismatch };
  });
  expect(r.total).toBeGreaterThan(490);
  expect(r.mismatch).toEqual([]);           // ZERO mismatches — the whole platform is synced
  expect(r.kept).toBeGreaterThan(370);      // ~387 kept (v576 endgame gate rightly vendors expensive-only bases)
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

test('v526 — game-internal base spelling (Kriss) normalizes to canonical (Kris) → Forge recognises it', async ({ page }) => {
  // the game files / an intake read may spell the dagger "Kriss"; the app canon is "Kris". A mismatch made
  // Ritual show "get a base" even when the dagger was owned. Normalisation resolves it end-to-end.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Kriss (Larzuk base)']));
    // v580.2 — Ritual (top rune Ohm) is now endgame-gated off a plain Kris (its ideal is Fanged Knife);
    // the alias proof uses MALICE (cheap 3os melee word — a 3os-max Kris pipeline) instead.
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ith: 1, El: 1, Eth: 1 })); // Malice runes
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Kriss (Larzuk base)');
    const s = w.forgeScan();
    const ritual = s.now.concat(s.pipeline, s.onestep).find((t: any) => t.rw === 'Malice');
    return {
      krissRecognized: Object.keys(w._baseCats('Kriss')).includes('dagger'),   // alias resolves
      krissRW: (w._baseRunewords('Kriss') || []).length > 0,
      tierChainKris: !!(w._TIER_CHAIN && w._TIER_CHAIN['kris']),                 // line-7638 fix → key exists
      ritualBase: ritual ? (ritual.base && ritual.base.base) : null,   // Malice task carries the canonical Kris
      ritualKind: ritual ? ritual.kind : null,
    };
  });
  expect(r.krissRecognized).toBe(true);   // "Kriss" resolves to dagger cats
  expect(r.krissRW).toBe(true);           // and hosts runewords (was 0 before)
  expect(r.tierChainKris).toBe(true);     // _TIER_CHAIN keyed on the canonical "kris"
  expect(r.ritualBase).toBe('Kris');      // an owned "Kriss" surfaces a task with the recognised base
  expect(r.ritualKind).toBe('pipeline');
});
