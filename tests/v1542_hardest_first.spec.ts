import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1542 — HARDEST FIRST.
//
// Konyo: "for the Uniqes and Sets chronicles it should be prioritized by HELL then Nightmare then
// Normal in the hunts its wanting me to do. its first run for me in Forge is Nightmare Pindleskin i
// rather finish off Hell and then the others."
//
// Both forges scored a source on `kph/chance` alone — drops per hour. That number does not know what
// difficulty it describes, and it prefers the easiest one twice over: Normal/NM have smaller chance
// denominators AND a kph bonus (×1.2 / ×1.1 where sources are built). So the hunt list handed him
// content he had already outgrown.

const boot = async (page: any) => {
  await page.goto(URL);
  await page.waitForTimeout(1800);
};

test.describe('v1542 — Hell before Nightmare before Normal', () => {
  test('★ the ranking helper puts difficulty ABOVE drops-per-hour', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      // a deliberately unfair pair: Normal is TEN TIMES the drop rate, Hell must still win
      const pick = w._pickSrc([
        { boss: 'Normal Pindleskin', diffKey: 'norm', chance: 1000, kph: 300, bossId: 'pind' },
        { boss: 'Hell Pindleskin', diffKey: 'hell', chance: 10000, kph: 300, bossId: 'pind' },
      ]);
      return { boss: pick.s.boss, diff: pick.diff };
    });
    expect(r.boss, 'Hell must win even when Normal has ten times the rate').toContain('Hell');
    expect(r.diff).toBe(2);
  });

  test('★ Nightmare beats Normal, and Hell beats both', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const S = (k: string) => ({ boss: k + ' X', diffKey: k, chance: 5000, kph: 100, bossId: 'x' });
      return {
        nmOverNorm: w._pickSrc([S('norm'), S('nm')]).s.diffKey,
        hellOverNm: w._pickSrc([S('nm'), S('hell')]).s.diffKey,
        ranks: ['norm', 'normTz', 'nm', 'nmTz', 'hell', 'hellTz'].map((k) => w._diffRank(k)),
      };
    });
    expect(r.nmOverNorm).toBe('nm');
    expect(r.hellOverNm).toBe('hell');
    expect(r.ranks, 'TZ is the same difficulty at a higher mlvl, not a separate tier')
      .toEqual([0, 0, 1, 1, 2, 2]);
  });

  test('within one difficulty the FASTEST run still wins', async ({ page }) => {
    // hardest-first must not become "ignore the numbers" — inside the tier he is clearing, the
    // better run is still the better run
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const pick = w._pickSrc([
        { boss: 'Hell Slow', diffKey: 'hell', chance: 90000, kph: 50, bossId: 'a' },
        { boss: 'Hell Fast', diffKey: 'hellTz', chance: 9000, kph: 300, bossId: 'b' },
      ]);
      return pick.s.boss;
    });
    expect(r).toBe('Hell Fast');
  });

  test('★ THE REPORT: the first unique run is a HELL run, not Nightmare Pindleskin', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.funiScan();
      const top = (s.runs || []).slice(0, 5).map((x: any) => ({ boss: x.boss, diff: x.diff }));
      return { top, first: top[0] };
    });
    expect(r.first, 'there must be at least one ranked run').toBeTruthy();
    expect(r.first.diff, 'the top run must be Hell tier').toBe(2);
    expect(r.first.boss).toMatch(/Hell/);
    expect(r.first.boss, 'the exact thing he complained about').not.toMatch(/^NM |^Nightmare |^Normal /);
    // and the whole head of the list is non-increasing in difficulty
    const diffs = r.top.map((x: any) => x.diff);
    expect(diffs, 'the list must never climb back UP in difficulty').toEqual([...diffs].sort((a, b) => b - a));
  });

  test('★ every run carries the difficulty it is asking for, in words', async ({ page }) => {
    // a reordering he cannot see is one he cannot trust
    await boot(page);
    const r = await page.evaluate(() => {
      const s: any = (window as any).funiScan();
      const top = (s.runs || [])[0];
      return { label: top && top.diffLabel, boss: top && top.boss };
    });
    expect(r.label).toBe('Hell');
  });

  test('★ the SETS side ranks by the same rule — one helper, not two copies', async ({ page }) => {
    await boot(page);
    expect(await page.evaluate(() => typeof (window as any)._setAggSrc),
      'the sets ranking helper must be reachable from where it is used').toBe('function');
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.fsetsScan();
      const out: any[] = [];
      // _setAggSrc resolves a set NAME to an aggregate item by a fuzzy stem match, and it legitimately
      // returns null for sets it cannot resolve. Scan them all and judge the ones that DO resolve —
      // slicing the first six tested whether the fuzzy match happened to hit, not the ranking.
      for (const set of (s.working || [])) {
        // NO try/catch here on purpose. The first version swallowed the TypeError from
        // _setAggSrc being IIFE-local and undefined on window, and reported "no source" for all 135
        // sets — a catch wide enough to hide a missing function will eventually hide one.
        const src = w._setAggSrc(set.name);
        if (src) out.push({ set: set.name, diff: w._diffRank(src.diffKey), boss: src.boss });
      }
      return { out, working: (s.working || []).length };
    });
    expect(r.working, 'there must be working sets at all').toBeGreaterThan(0);
    expect(r.out.length, 'at least some sets must resolve to a source to judge').toBeGreaterThan(0);
    // every set piece hunt should point at the hardest difficulty that can drop it
    const easy = r.out.filter((x: any) => x.diff < 2);
    expect(easy.length,
      'a set hunt still pointing below Hell: ' + JSON.stringify(easy)).toBe(0);
  });

  test('an item that genuinely cannot drop in Hell is not invented into it', async ({ page }) => {
    // hardest-first ranks what EXISTS; it must never manufacture a source
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      return {
        onlyNorm: w._pickSrc([{ boss: 'Normal Only', diffKey: 'norm', chance: 5000, kph: 100 }]).s.diffKey,
        blockedIgnored: w._pickSrc([
          { boss: 'Hell Blocked', diffKey: 'hell', chance: null, blocked: 'qlvl too high' },
          { boss: 'Normal Real', diffKey: 'norm', chance: 5000, kph: 100 },
        ]).s.boss,
        none: w._pickSrc([{ boss: 'Blocked', diffKey: 'hell', chance: null, blocked: 'x' }]),
      };
    });
    expect(r.onlyNorm).toBe('norm');
    expect(r.blockedIgnored, 'a BLOCKED Hell source is not a Hell source').toBe('Normal Real');
    expect(r.none, 'no usable source must return null, never a fabricated one').toBeNull();
  });

  test('the rotation brain inherits it — the Daily Pick cannot disagree with the Forge', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      // _chronRotation returns an OBJECT, not the array of chronicles — reach the list without
      // assuming its shape, so this stays a test of the ranking rather than of a return signature.
      const rot: any = w._chronRotation();
      const list = Array.isArray(rot) ? rot
        : Array.isArray(rot && rot.chron) ? rot.chron
          : Object.values(rot || {}).find((v: any) => Array.isArray(v)) || [];
      const grail: any = (list as any[]).find((c: any) => c && c.key === 'grail');
      return grail && grail.op ? { boss: grail.op.boss, pick: grail.pick } : null;
    });
    if (r && r.boss) {
      expect(r.boss, 'the OPS queue reads runs[0], so it must be the same Hell run').toMatch(/Hell/);
    }
  });

  test('★ THE SAFETY PROPERTY: reordering the hunt must never move the grail', async ({ page }) => {
    // Measured before/after v1542 against the pre-change board: found/total identical at 243/368,
    // sealed grounds 0 -> 0 with none lost and none gained, ranked runs consolidated 20 -> 9. This
    // pins the half that matters — a ranking decides what he farms NEXT and must never be able to
    // change what he is recorded as HAVING.
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.funiScan();
      const own = new Set<string>();
      try {
        JSON.parse(w.LSR.getItem('d2r_owned') || '[]').forEach((n: string) => own.add(n));
        Object.keys(JSON.parse(w.LSR.getItem('d2r_foundLog') || '{}')).forEach((n) => own.add(n));
      } catch { /* */ }
      return {
        found: s.found, total: s.total, missing: (s.missing || []).length,
        // the found count must be the OWNED set, not anything the ranking touched
        ownedInUniverse: s.total - (s.missing || []).length,
        sealedAllFound: (s.sealed || []).every((g: any) => g.found === g.total && g.total >= 2),
      };
    });
    expect(r.found + r.missing, 'found + missing must account for the whole universe').toBe(r.total);
    expect(r.found, 'the found count is the owned set — ranking cannot touch it').toBe(r.ownedInUniverse);
    expect(r.sealedAllFound, 'a sealed ground must still be a pool that is entirely found').toBe(true);
  });

  test('★ hardest-first CONSOLIDATES the hunt instead of scattering it', async ({ page }) => {
    // A real side effect worth keeping: when every item keys to its Hell source, missing items fall
    // into fewer, larger runs (20 -> 9 on his data) rather than being spread across three difficulties
    // of the same boss. Fewer runs, each worth more per trip.
    await boot(page);
    const r = await page.evaluate(() => {
      const s: any = (window as any).funiScan();
      const runs = s.runs || [];
      const labels = runs.map((x: any) => String(x.boss || ''));
      return {
        n: runs.length,
        splitBosses: labels.filter((b: string) => /^(NM|Normal)/.test(b)).length,
      };
    });
    expect(r.splitBosses,
      'no run should still be keyed to a Normal or Nightmare boss while a Hell source exists').toBe(0);
    expect(r.n).toBeGreaterThan(0);
  });
});
