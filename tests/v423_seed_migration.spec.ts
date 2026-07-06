import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v432/v436/v448/v451/v452 — the seeded runewords (now 36, incl. Spirit/Grief/Stone/Enigma/Doom) are a HARD
// FLOOR re-applied every load. Seeded RWs are FORGED FACT: their un-marks are purged on load (they snap back);
// only NON-seeded un-marks stick. So a stuck-at-19 / reset / restored save always snaps back to the full 54.
test('a stuck-at-19 save snaps up to 54 on load', async ({ page }) => {
  await page.addInitScript(() => {
    const old19 = {"Beast":"x","Dream":"x","Fortitude":"x","Rhyme":"x","Chains of Honor":"x","Infinity":"x","Duress":"x","Steel":"x","Nadir":"x","Stealth":"x","Malice":"x","Holy Thunder":"x","Passion":"x","Call to Arms":"x","Splendor":"x","Bone":"x","Crescent Moon":"x","Dragon":"x","Strength":"x"};
    localStorage.setItem('d2r_rwMade', JSON.stringify(old19));
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}');
    return { count: Object.keys(s).length, hasDeath: !!s['Death'], hasEdge: !!s['Edge'] };
  });
  expect(r.count).toBe(54);   // v587 +Hand of Justice, v593 +Flickering Flame
  expect(r.hasDeath).toBe(true);
  expect(r.hasEdge).toBe(true);
});
test('floor re-applies even after the stale one-time flag was set (the real stuck case)', async ({ page }) => {
  await page.addInitScript(() => {
    const old19 = {"Beast":"x","Dream":"x","Fortitude":"x","Rhyme":"x","Chains of Honor":"x","Infinity":"x","Duress":"x","Steel":"x","Nadir":"x","Stealth":"x","Malice":"x","Holy Thunder":"x","Passion":"x","Call to Arms":"x","Splendor":"x","Bone":"x","Crescent Moon":"x","Dragon":"x","Strength":"x"};
    localStorage.setItem('d2r_rwMade', JSON.stringify(old19));
    localStorage.setItem('d2r_rwSeed28', '1');   // stale flag from the fragile v423 attempt
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const n = await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade')||'{}')).length);
  expect(n).toBe(54);   // durable floor ignores the flag
});
test('un-marks: a seeded forged RW snaps back (purged), a non-seeded one stays un-marked', async ({ page }) => {
  await page.addInitScript(() => {
    // both un-marked away (absent from rwMade); the floor must re-assert the SEEDED Death (forged fact)
    // and purge its stale un-mark, while the NON-seeded Faith stays un-marked (not floored).
    localStorage.setItem('d2r_rwUnmade', JSON.stringify({ 'Death': 1, 'Faith': 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}');
    const u = JSON.parse(localStorage.getItem('d2r_rwUnmade')||'{}');
    return { hasDeath: !!s['Death'], hasFaith: !!s['Faith'], count: Object.keys(s).length, unmadeDeath: !!u['Death'], unmadeFaith: !!u['Faith'] };
  });
  expect(r.hasDeath).toBe(true);      // seeded → re-floored (forged fact)
  expect(r.unmadeDeath).toBe(false);  // its stale un-mark purged
  expect(r.hasFaith).toBe(false);     // non-seeded → un-mark respected, NOT floored
  expect(r.unmadeFaith).toBe(true);   // non-seeded un-mark preserved across the reload
  expect(r.count).toBe(54);           // exactly the 54 forged seeds
});
