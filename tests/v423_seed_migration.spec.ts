import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v423 — existing 19-runeword saves get topped up to 28 ONCE (additive), then un-marks stick.
test('a stuck-at-19 save is migrated up to 28', async ({ page }) => {
  // seed an OLD 19-entry save + no migration flag BEFORE the app script runs
  await page.addInitScript(() => {
    const old19 = {"Beast":"x","Dream":"x","Fortitude":"x","Rhyme":"x","Chains of Honor":"x","Infinity":"x","Duress":"x","Steel":"x","Nadir":"x","Stealth":"x","Malice":"x","Holy Thunder":"x","Passion":"x","Call to Arms":"x","Splendor":"x","Bone":"x","Crescent Moon":"x","Dragon":"x","Strength":"x"};
    localStorage.setItem('d2r_rwMade', JSON.stringify(old19));
    localStorage.removeItem('d2r_rwSeed28');
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const saved = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}');
    return { count: Object.keys(saved).length, hasDeath: !!saved['Death'], hasEdge: !!saved['Edge'], flag: localStorage.getItem('d2r_rwSeed28') };
  });
  expect(r.count).toBe(28);   // 19 + 9 missing
  expect(r.hasDeath).toBe(true);
  expect(r.hasEdge).toBe(true);
  expect(r.flag).toBe('1');
});
test('after migration, an un-marked runeword stays un-marked (not re-added)', async ({ page }) => {
  await page.addInitScript(() => {
    // migration already ran (flag set); user un-marked Death → 27 entries
    const s:any = {}; ['Beast','Dream','Fortitude','Rhyme','Chains of Honor','Infinity','Duress','Steel','Nadir','Stealth','Malice','Holy Thunder','Passion','Call to Arms','Splendor','Bone','Crescent Moon','Dragon','Strength','Smoke','Mosaic','Harmony','Venom','Pride','Destruction','Edge','Lore'].forEach(k=>s[k]='x');
    localStorage.setItem('d2r_rwMade', JSON.stringify(s));
    localStorage.setItem('d2r_rwSeed28', '1');
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}'); return { hasDeath: !!s['Death'], count: Object.keys(s).length }; });
  expect(r.hasDeath).toBe(false);   // NOT re-added — un-mark respected
  expect(r.count).toBe(27);
});
