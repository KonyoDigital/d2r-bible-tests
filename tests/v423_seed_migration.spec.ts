import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v424 — the 28 created runewords are a DURABLE FLOOR re-applied every load (except explicit un-marks),
// so a stuck-at-19 / reset / restored save always snaps back to ≥28 while un-marks still stick.
test('a stuck-at-19 save snaps up to 28 on load', async ({ page }) => {
  await page.addInitScript(() => {
    const old19 = {"Beast":"x","Dream":"x","Fortitude":"x","Rhyme":"x","Chains of Honor":"x","Infinity":"x","Duress":"x","Steel":"x","Nadir":"x","Stealth":"x","Malice":"x","Holy Thunder":"x","Passion":"x","Call to Arms":"x","Splendor":"x","Bone":"x","Crescent Moon":"x","Dragon":"x","Strength":"x"};
    localStorage.setItem('d2r_rwMade', JSON.stringify(old19));
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}');
    return { count: Object.keys(s).length, hasDeath: !!s['Death'], hasEdge: !!s['Edge'] };
  });
  expect(r.count).toBe(28);
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
  expect(n).toBe(28);   // durable floor ignores the flag
});
test('an explicit un-mark stays un-marked across reloads (not re-floored)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwUnmade', JSON.stringify({ 'Death': 1 }));
    const s:any = {}; ['Beast','Dream','Fortitude','Rhyme','Chains of Honor','Infinity','Duress','Steel','Nadir','Stealth','Malice','Holy Thunder','Passion','Call to Arms','Splendor','Bone','Crescent Moon','Dragon','Strength','Smoke','Mosaic','Harmony','Venom','Pride','Destruction','Edge','Lore'].forEach(k=>s[k]='x');
    localStorage.setItem('d2r_rwMade', JSON.stringify(s));   // 27 (Death un-marked)
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}'); return { hasDeath: !!s['Death'], count: Object.keys(s).length }; });
  expect(r.hasDeath).toBe(false);   // un-mark respected, NOT re-floored
  expect(r.count).toBe(27);
});
