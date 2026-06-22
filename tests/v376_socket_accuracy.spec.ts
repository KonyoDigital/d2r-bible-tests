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
});
