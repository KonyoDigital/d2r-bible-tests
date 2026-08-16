import { test, expect } from './_net_stub';
import * as path from 'path';

// v1737 — TWO THINGS KONYO PAID FOR.
//
// ── 1. THE LADDER TOGGLE TURNED THINGS OFF, NOT ON ────────────────────────────────────────────
// Konyo: "its showing ladder runewords when it shouldnt be when im in non ladder. only when i
// toggle it on it should show those 9 runewords." And: "in forge tab onestep and make now.. it
// should also be resembling this logic."
//
// `_forgeIncludeLadder()` defaulted to TRUE. An unset preference meant INCLUDE, so a user who had
// never touched the toggle got the ladder-only words in the Forge lanes on a non-ladder character.
// The control only did anything once it had been switched OFF — the opposite of a toggle that
// turns a thing on. Every other surface had always hidden them off-ladder (the v577 rule: "Konyo
// plays NON-ladder, it should not be giving me these"), so the Forge was the odd one out.
//
// Measured through forgeScan() with an empty chronicle and a stocked stash: before, all eight
// ladder-only words sat in MAKE NOW with the toggle unset; after, they sit in the read-only
// `ladder` strip and appear in MAKE NOW only once the toggle is explicitly on.
//
// ⚠ The set holds EIGHT words (Bulwark, Cure, Ground, Hearth, Hysteria, Mania, Metamorphosis,
// Temper) while three comments and Konyo both say "9". Seven other 2.4-era words (Pattern, Plague,
// Obsession, Mist, Flickering Flame, Unbending Will, Wisdom) exist in the file and are NOT marked.
// Nothing in the repo says which — if any — is the ninth, so the set is pinned at 8 rather than
// guessed at, and a change to it has to be deliberate. [[unknown-stays-unknown]]
//
// ── 2. A BASE THE FORGE NAMED, THAT ATE HIS RUNES ─────────────────────────────────────────────
// Konyo: "voice of reason runeword i created a runword for it in it and it didnt work... i wasted
// runewords", and the base was a 4os Broad Sword, socketed in order, no transform.
//
// Reproduced exactly: with a 4os Broad Sword owned and Lem/Ko/El/Eld in the stash, forgeScan()
// returned MAKE NOW · Voice of Reason · Broad Sword (4os).
//
// By every source this file HAS, that pairing is legal — Broad Sword is a sword, maxSockets 4, and
// the word reads "4 socket Swords Maces". That clause is diablo2.io v3.2 data: VANILLA. He plays
// Reign of the Warlock, where the AB wiki is the authority and a correct vanilla fact can be wrong.
// The repo cannot rule on the pairing; his game can, and did. Recorded per RUNEWORD+BASE, because
// Voice of Reason is not broken — that home for it is.
//
// ── WHAT WAS FOUND AND NOT FIXED ──────────────────────────────────────────────────────────────
// 2,763 of 7,692 base×runeword pairs (36%, across 281 of 508 bases) have the runeword needing MORE
// sockets than the base can ever hold — `_baseRunewords('Broad Sword')` offers Breath of the Dying
// (6) and Call to Arms (5) against a cap of 4. None of them reached a Forge lane in testing:
// forgeScan's per-branch guards catch them, and its v553 note explains why the cap is deliberately
// NOT applied at the cross (an owned base that ALREADY has N sockets proves it can hold them, even
// where our max estimate is low — a 2os Wand is real though Wand reports max 1). So this is a
// latent risk rather than a live bug, and it is pinned below rather than "fixed" by a filter that
// would suppress real bases. [[unknown-stays-unknown]]

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const LADDER = ['Bulwark', 'Cure', 'Ground', 'Hearth', 'Hysteria', 'Mania', 'Metamorphosis', 'Temper'];
const RUNES = ['El', 'Eld', 'Tir', 'Nef', 'Eth', 'Ith', 'Tal', 'Ral', 'Ort', 'Thul', 'Amn', 'Sol',
  'Shael', 'Dol', 'Hel', 'Io', 'Lum', 'Ko', 'Fal', 'Lem', 'Pul', 'Um', 'Mal', 'Ist', 'Gul', 'Vex',
  'Ohm', 'Lo', 'Sur', 'Ber', 'Jah', 'Cham', 'Zod'];

/* A default profile has ALL 99 runewords marked MADE (_RWC_SEED), so forgeScan returns zero tiles
   in every bucket and any assertion about the lanes would pass vacuously. The only honest way to
   test PLANNING is an empty chronicle — and the rune stash is read AT BOOT, so it needs a reload
   before the scan. Both facts are v1712's, paid for there. */
async function emptyChronicle(page: any, stash: Record<string, number>) {
  await page.goto(URL);
  await page.waitForTimeout(1200);
  await page.evaluate((st: any) => {
    const w: any = window;
    w.LSR.setItem('d2r_rwProfile', 'fresh');
    w.LSR.setItem('d2r_rwMade', '{}');
    w.LSR.setItem('d2r_rwUnmade', '{}');
    w.LSR.setItem('d2r_runeStash', JSON.stringify(st));
  }, stash);
  await page.reload();
  await page.waitForTimeout(1800);
}

test.describe('v1737 — the ladder toggle turns things ON, and a proven-bad base stays out', () => {
  test('★★★ ladder-only words stay out of the Forge lanes until the toggle is explicitly on',
    async ({ page }) => {
    const stash: Record<string, number> = {};
    RUNES.forEach((r) => (stash[r] = 20));
    await emptyChronicle(page, stash);

    const r = await page.evaluate((LAD: string[]) => {
      const w: any = window;
      // own every base that can host a ladder-only word, so the lanes actually populate
      const hosts = new Set<string>();
      for (const nm of LAD) ((w._forgeMetaBase(nm) || {}).names || []).forEach((n: string) => hosts.add(n));
      for (const base of hosts) for (const s of [2, 3, 4, 5, 6]) {
        try { w._ensureSocketBaseEntry(base + ' (' + s + 'os)'); w.toggleOwned(base + ' (' + s + 'os)'); } catch (e) {}
      }
      const names = (a: any[]) => (a || []).map((t) => t.rw || t.n || '').filter(Boolean);
      const read = () => {
        const sc = w.forgeScan();
        return {
          lanes: names(sc.now).concat(names(sc.pipeline), names(sc.onestep)).filter((n: string) => LAD.includes(n)),
          strip: names(sc.ladder).filter((n: string) => LAD.includes(n)),
          total: sc.now.length + sc.pipeline.length + sc.onestep.length,
        };
      };
      w.LSR.removeItem('d2r_forgeIncludeLadder');
      const off = read();
      w.LSR.setItem('d2r_forgeIncludeLadder', '1');
      const on = read();
      return { off, on, mode: w.rwLadderMode || (typeof (w as any).rwLadderMode) };
    }, LADDER);

    // non-vacuity: the lanes must actually hold tasks, or "no ladder words" is meaningless
    expect(r.off.total, 'the Forge planned nothing at all — the fixture failed, not the app')
      .toBeGreaterThan(0);
    expect(r.off.lanes, 'ladder-only words in the Forge lanes with the toggle UNSET: '
      + r.off.lanes.join(', ')).toEqual([]);
    expect(r.off.strip.length, 'with the toggle off they belong in the read-only ladder strip')
      .toBeGreaterThan(0);
    // and the toggle must still WORK — a rule that can never be turned on is not a toggle
    expect(r.on.lanes.length, 'toggling ladder ON did not bring the ladder words into the lanes')
      .toBeGreaterThan(0);
  });

  test('★★★ Voice of Reason is never planned in a Broad Sword again', async ({ page }) => {
    await emptyChronicle(page, { Lem: 3, Ko: 3, El: 3, Eld: 3 });
    const r = await page.evaluate(() => {
      const w: any = window;
      try { w._ensureSocketBaseEntry('Broad Sword (4os)'); w.toggleOwned('Broad Sword (4os)'); } catch (e) {}
      const sc = w.forgeScan();
      const tasks = [].concat(sc.now, sc.pipeline, sc.onestep)
        .filter((t: any) => /Voice of Reason/i.test(t.rw || ''))
        .map((t: any) => ({ base: (t.base && (t.base.base || t.base.name)) || null, sub: t.sub }));
      return {
        ownedBases: (w._ownedBases ? w._ownedBases() : []).length,
        broadSwordTasks: tasks.filter((t: any) => /Broad Sword/i.test(t.base || '')),
        anyVoRTask: tasks.length,
        legalBases: w._rwLegalBases ? w._rwLegalBases('Voice of Reason', 40) : [],
        predicate: w._rwBaseFailed ? w._rwBaseFailed('Voice of Reason', 'Broad Sword') : null,
      };
    });
    // non-vacuity: the base really is owned, so a naive engine WOULD offer it
    expect(r.ownedBases, 'the Broad Sword did not register as owned — the test proves nothing')
      .toBeGreaterThan(0);
    expect(r.predicate, 'the proven-bad pairing is not recorded').toBe(true);
    expect(r.broadSwordTasks, 'the Forge still plans Voice of Reason in a Broad Sword: '
      + JSON.stringify(r.broadSwordTasks)).toEqual([]);
    expect(r.legalBases, 'Broad Sword is still offered as a legal base for Voice of Reason')
      .not.toContain('Broad Sword');
    // the word itself must remain plannable — the BASE was disproved, not the runeword
    expect(r.legalBases.length, 'Voice of Reason lost every base, not just the bad one')
      .toBeGreaterThan(0);
  });

  test('★★ the impossible base×runeword pairs are counted, not silently tolerated', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => {
      const w: any = window;
      let pairs = 0, impossible = 0;
      for (const base of Object.keys(BASE_DB)) {
        const declared = (BASE_DB as any)[base].maxSockets || 0;
        let smax = 0;
        try { smax = parseInt(w._socketMaxFor(base), 10) || 0; } catch (e) {}
        const cap = Math.max(declared, smax);
        if (!cap) continue;
        let list: any[] = [];
        try { list = w._baseRunewords(base) || []; } catch (e) { continue; }
        for (const rw of list) { pairs++; if (rw.s > cap) impossible++; }
      }
      return { pairs, impossible };
    });
    expect(r.pairs, 'no base×runeword pairs were produced — nothing was measured')
      .toBeGreaterThan(5000);
    /* 2,763 today. This is NOT asserted to be zero: forgeScan deliberately does not apply the cap
       at the cross, because an owned base that already HAS the sockets proves it can hold them
       even where the max estimate is low. The count is pinned so the number cannot grow unnoticed
       while nobody is looking at it. */
    expect(r.impossible, 'impossible pairs grew — the base↔runeword relation drifted further apart')
      .toBeLessThanOrEqual(2763);
  });
});
