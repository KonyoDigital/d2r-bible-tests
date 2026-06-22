// v376 — runeword/socket ACCURACY on base & magic keeper cards:
//  #1 a runeword needs the EXACT socket count = #runes → a known-socket base lists only makeable-now words
//  #2 Larzuk gives a NORMAL base its GUARANTEED max sockets (verified per-base SOCKET_MAX table)
//  #3 the Horadric cube rolls RANDOM 1→max for a normal base (per-slot recipe)
//  #4 a MAGIC item is GEM-only — NOT a runeword base (runewords need white/normal)
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v376 socket accuracy', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
  });

  test('#2 verified per-base MAX sockets (incl. the corrected Cryptic Sword = 4)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return {
        crystal: w._socketMaxFor('Crystal Sword'),
        crypticSword: w._socketMaxFor('Cryptic Sword'),   // corrected: 4, not 6
        grandScepter: w._socketMaxFor('Grand Scepter'),
        monarch: w._socketMaxFor('Monarch'),
        circlet: w._socketMaxFor('Circlet'),
        ringMail: w._socketMaxFor('Ring Mail'),
      };
    });
    expect(r.crystal).toBe(6);
    expect(r.crypticSword).toBe(4);
    expect(r.grandScepter).toBe(3);
    expect(r.monarch).toBe(4);
    expect(r.circlet).toBe(2);
    expect(r.ringMail).toBe(3);
  });

  test('#2/#3 normal base shows guaranteed Larzuk max + random cube range with the right recipe', async ({ page }) => {
    const g = await page.evaluate(() => (window as any)._socketGuideLine('Crystal Sword', 'normal'));
    expect(g).toContain('Larzuk → 6 sockets');
    expect(g).toContain('random 1–6');
    expect(g).toContain('Ral + Amn + Perfect Amethyst');   // weapon cube recipe
  });

  test('#4 a MAGIC socketable item is gem-only, explicitly NOT a runeword base', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return {
        magicSword: w._socketGuideLine('Crystal Sword', 'magic'),
        magicCharm: w._socketGuideLine('Grand Charm', 'magic'),   // not socketable → empty
        rareArmor: w._socketGuideLine('Archon Plate', 'rare'),
      };
    });
    expect(r.magicSword).toContain('NOT a runeword base');
    expect(r.magicSword).toContain('1–2');                 // Larzuk magic = random 1-2
    expect(r.magicCharm).toBe('');                         // charms can't be socketed
    expect(r.rareArmor).toContain('exactly');             // rare → Larzuk gives 1
  });

  test('#1 a known-socket base lists ONLY makeable-now runewords; other counts are separated', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      // Grand Scepter read at 3 sockets — only 3-socket scepter runewords are makeable NOW
      const line = w._baseRWLine('Grand Scepter', 3);
      // the makeable-now segment is before "other socket counts"; 2os words must NOT be in it
      const nowSeg = line.split('other socket counts')[0];
      return { line, nowSeg };
    });
    expect(r.line).toContain('makeable in your 3os now');
    // a 2-socket runeword (e.g. Strength/Wind/Zephyr) must NOT appear as makeable-now in a 3-socket base
    expect(r.nowSeg).not.toContain('Strength');
    expect(r.nowSeg).not.toContain('Zephyr');
  });

  // v385 — a base can NEVER hold more sockets than its max, so NO runeword needing more than the base's
  // max-sockets may appear anywhere in the runeword line (not makeable-now, not as a re-roll target).
  test('#5 runeword line is capped to the base max-sockets — impossible higher-count words removed', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const strip = (s: string) => s.replace(/<[^>]+>/g, ' ');
      const check = (base: string, read: number) => {
        const max = w._socketMaxFor(base);
        const line = strip(w._baseRWLine(base, read));
        // every runeword that needs MORE than `max` sockets, by name
        const over = w._baseRunewords(base).filter((x: any) => x.s > max).map((x: any) => x.n);
        const leaked = over.filter((n: string) => line.indexOf(n) >= 0);
        return { max, leaked };
      };
      return {
        boneShield: check('Bone Shield', 2),   // max 2 — no 3os/4os (Exile, Phoenix, Spirit…)
        breastPlate: check('Breast Plate', 3),  // max 3 — no 4os (Bramble, Chains of Honor, Fortitude)
        broadSword: check('Broad Sword', 4),    // max 4 — no 5os/6os (Call to Arms, Breath of the Dying)
        lightPlate: check('Light Plate', 3),
      };
    });
    expect(r.boneShield.max).toBe(2);
    expect(r.boneShield.leaked, 'Bone Shield (max 2) leaks higher-socket runewords').toEqual([]);
    expect(r.breastPlate.leaked, 'Breast Plate (max 3) leaks 4os runewords').toEqual([]);
    expect(r.broadSword.leaked, 'Broad Sword (max 4) leaks 5-6os runewords').toEqual([]);
    expect(r.lightPlate.leaked, 'Light Plate (max 3) leaks 4os runewords').toEqual([]);
  });

  // v387 — a read with MORE sockets than the base can ever hold = misidentified base. "Mace (5os)" is
  // impossible (a Mace maxes at 2), so it's flagged as a misread that suggests the same-class bases which
  // CAN hold 5 sockets (the flails: Scourge/Flail/Knout). Konyo's repeatedly-flagged Mace/Scourge case.
  test('#6 impossible socket count is flagged as a misread, suggesting same-class bases that fit', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const strip = (s: string) => s.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
      return {
        mace5: strip(w._baseRWLine('Mace', 5)),
        mace2: strip(w._baseRWLine('Mace', 2)),
        scourge5: strip(w._baseRWLine('Scourge', 5)),
      };
    });
    expect(r.mace5).toContain('Likely misidentified');
    expect(r.mace5).toContain('at most 2 sockets');
    expect(r.mace5).toMatch(/Scourge|Flail|Knout/);   // suggests the 5os mace-class flails
    expect(r.mace2).toContain('Keep for runewords');  // a VALID 2os Mace is normal
    expect(r.mace2).not.toContain('misidentified');
    expect(r.scourge5).toContain('Keep for runewords'); // the CORRECT base (Scourge max 5) is fine
    expect(r.scourge5).not.toContain('misidentified');
  });
});
