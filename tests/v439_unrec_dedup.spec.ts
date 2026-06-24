import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v439 — near-duplicate throw-out reads (same item, OCR drift in the quoted rune string) must COLLAPSE to one
// (Konyo: "I don't need double registered, 1 combined"). Different bases must stay distinct.
test('_dedupCanon collapses OCR-variant gemmed reads but keeps distinct bases', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1200);
  const r = await page.evaluate(() => {
    const w:any = window;
    const out = w._dedupCanon([
      "Gemmed Conquest Sword 'ShaelKoEld'",
      "Gemmed Conquest Sword 'ShaelK@Eld'",
      "Gemmed Phase Blade 'ShaelKoEld'",
    ]);
    return {
      hasHelper: typeof w._dedupCanon === 'function',
      out,
      canonSame: w._unrecCanon("Gemmed Conquest Sword 'ShaelKoEld'") === w._unrecCanon("Gemmed Conquest Sword 'ShaelK@Eld'"),
    };
  });
  expect(r.hasHelper).toBe(true);
  expect(r.canonSame).toBe(true);
  // the two Conquest Sword OCR variants collapse to ONE; the Phase Blade stays separate → 2 total
  expect(r.out.length).toBe(2);
  expect(r.out.some((n:string)=>/Conquest Sword/.test(n))).toBe(true);
  expect(r.out.some((n:string)=>/Phase Blade/.test(n))).toBe(true);
});
