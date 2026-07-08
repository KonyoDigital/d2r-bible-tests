import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v616 — CLASS-RESTRICTION INVARIANT (Konyo's Wrist Sword→Exile report). Whatever surface leaks,
// the ENGINE is the single source: sweep the full base catalog and assert class-gated runewords can
// never appear on an illegal base type, and every art-home base is a legal host of its word.

test('full-catalog sweep: class-gated words never appear on illegal bases', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const AURIC = /targe|rondache|heraldic|aerin|crown shield|royal shield|gilded|protector shield|zakarum|vortex shield|sacred targe|sacred rondache|akaran|kurast|scutari|hyperion shield|monarch/i;
    const auricStrict = (b: string) => /targe|rondache|heraldic|aerin|crown shield|royal shield|gilded|protector shield|zakarum|vortex shield|akaran|kurast/i.test(b);   // the paladin (auric) shield family
    const CLAW = /katar|wrist|cestus|claws|talon|quhab|fascia|hand scythe|suwayyah|scissors|hatchet hands|war fist/i;   // the full assassin claw family
    const bases = Object.keys(w.BASE_DB || {});
    const leaks: string[] = [];
    bases.forEach((b) => {
      const words = (w._baseRunewords(b) || []).map((x: any) => x.n);
      if (words.includes('Exile') && !auricStrict(b)) leaks.push('Exile→' + b);
      ['Pattern', 'Chaos'].forEach((cw) => { if (words.includes(cw) && !CLAW.test(b)) leaks.push(cw + '→' + b); });
      if (/^(Circlet|Coronet|Tiara|Diadem)$/i.test(b) && words.length) leaks.push('circlet-hosts→' + b);
    });
    return { checked: bases.length, leaks: leaks.slice(0, 20) };
  });
  expect(r.checked).toBeGreaterThan(400);
  expect(r.leaks).toEqual([]);
});

test('every RW_BEST_BASE art home is a legal host of its word', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const bad: string[] = [];
    Object.keys(w.RW_BEST_BASE || {}).forEach((rw) => {
      const home = w.RW_BEST_BASE[rw];
      if (!w.BASE_DB || !(home in w.BASE_DB)) return;   // non-base art names are out of scope
      const words = (w._baseRunewords(home) || []).map((x: any) => x.n);
      if (!words.includes(rw)) bad.push(rw + '→' + home);
    });
    return bad;
  });
  expect(r).toEqual([]);
});
