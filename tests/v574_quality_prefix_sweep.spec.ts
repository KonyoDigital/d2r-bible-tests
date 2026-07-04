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
test('v575 — ideal-base cube gamble: PLAIN Flail gambles for HotO; SUPERIOR is Larzuk-only (no gamble)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (Larzuk base)', 'Superior Flail (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 1, Vex: 1, Pul: 1, Thul: 1 }));  // HotO runes
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');           // suppress the 47-seed so HotO is unmade
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Flail (Larzuk base)');
    w._ensureSocketBaseEntry('Superior Flail (Larzuk base)');
    const s = w.forgeScan();
    const t = [...(s.pipeline || []), ...(s.now || [])].find((x: any) => x.rw === 'Heart of the Oak');
    return { found: !!t, gamble: !!(t && t.cubeGamble), baseName: t && t.base && t.base.name,
             sup: !!(t && t.base && t.base.sup) };
  });
  expect(r.found).toBe(true);                 // HotO planned on an owned base, not "go get a base"
  expect(r.gamble).toBe(true);                // …as a cube-socket GAMBLE (Larzuk 5 overshoots HotO's 4)
  expect(r.sup).toBe(false);                  // v575.1 — the PLAIN Flail was chosen: superior can't use the
  expect(String(r.baseName)).toMatch(/^Flail/);   // cube socket recipe (Larzuk-max is its only path)
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

// v576 — ENDGAME-GEAR GATE (Konyo: "im 1000% positive these runewords should not be in these white bases
// regardless of the chronicle — after created I use it on characters"): an EXPENSIVE word (top rune ≥ Ist)
// is only planned on its IDEAL meta base or an ELITE base, and never on a 2H/merc-rescued base. Cheap words
// (Honor…) keep the v501 owned-base rescue. Same gate in _baseUnmadeRunewords so keep/throw advice agrees.
test('v576 — Eternity refuses a plain Flail; HoJ refuses a merc-rescued Colossus Voulge; Honor keeps the rescue', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (5os)', 'Colossus Voulge (Larzuk base)', 'Thresher (5os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ber: 1, Ist: 1, Sol: 2, Sur: 2, Cham: 1, Amn: 1, Lo: 1, El: 1, Ith: 1, Tir: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    ['Flail (5os)', 'Colossus Voulge (Larzuk base)', 'Thresher (5os)'].forEach((n) => w._ensureSocketBaseEntry(n));
    const s = w.forgeScan();
    const all = [...(s.now || []), ...(s.pipeline || [])];
    const eternityOnFlail = all.find((t: any) => t.rw === 'Eternity' && /Flail/.test(t.base && t.base.name || ''));
    const hojOnCV = all.find((t: any) => t.rw === 'Hand of Justice' && /Voulge/.test(t.base && t.base.name || ''));
    const honorRescued = all.find((t: any) => t.rw === 'Honor' && t.mercOwn);
    // keep/throw agrees: a plain 5os Flail is NOT "kept for Eternity"
    const flailKeeps = (w._baseUnmadeRunewords('Flail (5os)', 5) || []).map((x: any) => x.n);
    return { eternityOnFlail: !!eternityOnFlail, hojOnCV: !!hojOnCV, honorRescued: !!honorRescued, flailKeeps };
  });
  expect(r.eternityOnFlail).toBe(false);      // endgame word → not in a normal-tier Flail
  expect(r.hojOnCV).toBe(false);              // endgame word → never on a 2H/merc rescue
  expect(r.honorRescued).toBe(true);          // cheap word keeps the v501 owned-2H rescue
  expect(r.flailKeeps).not.toContain('Eternity');   // vault keep-advice uses the same gate
});

// v577 — LADDER words never appear as EXAMPLE CHIPS in non-ladder mode (Konyo: "I play non-ladder — mixing
// isn't right; when I finish non-ladder I'll flip the toggle and get the last ones"). The engine already
// gated tasks/keep-decisions (v553/v562); this locks the DISPLAY layer (_baseRWLine → throw-out cards,
// Socketed Review, hover tooltips) + the honest "+N ladder-only hidden" tag + the toggle bringing them back.
test('v577 — ladder-only chips hidden off-ladder (with an honest count), shown again in ladder mode', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const off = String(w._baseRWLine('Devil Star', 3));      // 3os mace: Black (non-ladder) + Mania (ladder)
    localStorage.setItem('d2r_ladderMode', 'ladder');        // _rwLadderBlocked reads the store live
    const on = String(w._baseRWLine('Devil Star', 3));
    return {
      offHasBlack: /Black/.test(off), offHasMania: /Mania/.test(off), offHasHiddenTag: /ladder-only hidden/.test(off),
      onHasMania: /Mania/.test(on),
    };
  });
  expect(r.offHasBlack).toBe(true);      // non-ladder examples stay
  expect(r.offHasMania).toBe(false);     // ladder-only example GONE off-ladder
  expect(r.offHasHiddenTag).toBe(true);  // …with an honest "+N ladder-only hidden" tag
  expect(r.onHasMania).toBe(true);       // flip the toggle → it returns
});
