// v379 — per-base SOCKETED identity: a worthwhile socketed/Larzuk base registers as its SPECIFIC base
// (Monarch, Crystal Sword…) with its OWN art + EXACT max-socket on the card, NOT a generic bucket.
// The generic buckets remain as a fallback (so v322/v324/v371 stay valid).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v379 per-base socketed identity', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
  });

  test('Larzuk base → specific identity, own art, exact max sockets, routes to SOCKETED', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Monarch (Larzuk base)');
      const ex = (w.EXTRA_ITEMS || {})['Monarch (Larzuk base)'];
      return {
        cat: ex && ex.cat,
        base: ex && ex.base,
        desc: ex && ex.desc,
        art: w.artUrl ? w.artUrl('Monarch (Larzuk base)') : null,
        genericKept: !!(w.EXTRA_ITEMS || {})['Larzuk Shield Base'],
      };
    });
    expect(r.cat).toBe('Socketed bases');          // → SOCKETED locker (same routing as generic)
    expect(r.base).toBe('Monarch');                // specific identity, not "Shield"
    expect(r.desc).toContain('4 sockets');         // EXACT max from verified SOCKET_MAX (Monarch=4)
    expect(r.art).toContain('base_monarch');       // its OWN sprite
    expect(r.genericKept).toBe(true);              // generic bucket preserved (v371 fallback safe)
  });

  test('socketed base → exact current sockets + makeable-now runewords + own art', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Crystal Sword (4os)');
      const ex = (w.EXTRA_ITEMS || {})['Crystal Sword (4os)'];
      return { sockets: ex && ex.sockets, base: ex && ex.base, desc: ex && ex.desc, art: w.artUrl('Crystal Sword (4os)') };
    });
    expect(r.sockets).toBe(4);
    expect(r.base).toBe('Crystal Sword');
    expect(r.desc).toContain('makeable in your 4os now');  // socket-accurate runewords
    expect(r.desc).toContain('6 sockets');                  // Crystal Sword max=6
    expect(r.art).toContain('base_crystalsword');
  });

  test('a base with no specific art still registers (generic fallback art, specific identity)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Colossus Voulge (Larzuk base)');
      const ex = (w.EXTRA_ITEMS || {})['Colossus Voulge (Larzuk base)'];
      return { cat: ex && ex.cat, base: ex && ex.base, hand: ex && ex.hand };
    });
    expect(r.cat).toBe('Socketed bases');
    expect(r.base).toBe('Colossus Voulge');
    expect(r.hand).toBe('2h');   // polearm → 2H footprint
  });
});
