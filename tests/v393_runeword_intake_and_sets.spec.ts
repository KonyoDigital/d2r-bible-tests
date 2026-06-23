import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v393/v394 — intake recognises forged RUNEWORDS (Enigma/Chains of Honor/Spirit) as keepers to register +
// mule (not throw-out); LOW set pieces (Sigon's/Sander's…) are tracked for the grail but routed to throw-out
// (not muled); and Sander's Riprap art is corrected to boots (the crawled d2io_ sprite was a wrong gem).
test.describe('v393 runeword recognition + low-set throw-out + Sander art', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
  });

  test('findRuneword recognises forged runewords by exact + normalized name', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fr = (window as any).findRuneword;
      return {
        enigma: fr('Enigma'),
        coh: fr('Chains of Honor'),
        spirit: fr('Spirit'),
        cta: fr('Call to Arms'),
        notRw: fr("Tyrael's Might"),
      };
    });
    expect(r.enigma).toBe('Enigma');
    expect(r.coh).toBe('Chains of Honor');
    expect(r.spirit).toBe('Spirit');
    expect(r.cta).toBe('Call to Arms');
    expect(r.notRw).toBeNull();
  });

  test("Sander's Riprap renders boots art, not the wrong gem/annihilus sprite", async ({ page }) => {
    const art = await page.evaluate(() => (window as any).artUrl("Sander's Riprap"));
    expect(art).toBe('art/hd_heavy_boots.png');
    expect(art).not.toMatch(/sandersriprap|annihilus|jewel|charm/i);
  });

  test('the low set pieces resolve as set pieces (so intake can grail-track + throw them out)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any).findSetPiece;
      return {
        riprap: !!f("Sander's Riprap"),
        sabot: !!f("Sigon's Sabot"),
      };
    });
    expect(r.riprap).toBe(true);
    expect(r.sabot).toBe(true);
  });

  test('no console errors on load with the runeword/set intake changes', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push(e.message));
    await page.reload();
    await page.waitForTimeout(1200);
    expect(errs).toEqual([]);
  });
});
