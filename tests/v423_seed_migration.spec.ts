import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v432/v436/v448/v451/v452 — the seeded runewords (now 36, incl. Spirit/Grief/Stone/Enigma/Doom) are a HARD
// FLOOR re-applied every load. Seeded RWs are FORGED FACT: their un-marks are purged on load (they snap back);
// only NON-seeded un-marks stick. So a stuck-at-19 / reset / restored save always snaps back to the full 57.
test('a stuck-at-19 save snaps up to 57 on load', async ({ page }) => {
  await page.addInitScript(() => {
    const old19 = {"Beast":"x","Dream":"x","Fortitude":"x","Rhyme":"x","Chains of Honor":"x","Infinity":"x","Duress":"x","Steel":"x","Nadir":"x","Stealth":"x","Malice":"x","Holy Thunder":"x","Passion":"x","Call to Arms":"x","Splendor":"x","Bone":"x","Crescent Moon":"x","Dragon":"x","Strength":"x"};
    localStorage.setItem('d2r_rwMade', JSON.stringify(old19));
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}');
    return { count: Object.keys(s).length, hasDeath: !!s['Death'], hasEdge: !!s['Edge'] };
  });
  expect(r.count).toBe(94);   // v669.1 +Wealth
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
  expect(n).toBe(94);   // durable floor ignores the flag
});
test('un-marks SURVIVE the floor for seeded AND non-seeded words (the v615 ↺ contract)', async ({ page }) => {
  await page.addInitScript(() => {
    // v615 (lockdown) REVERSED the v448 purge: an explicit un-mark is USER TRUTH — the boot floor
    // honors it (the ↺ button used to silently revert on reload, desyncing consumed bases). A wipe
    // still refloors everything because a wipe clears d2r_rwUnmade too (v615_chronicle_lockdown).
    localStorage.setItem('d2r_rwUnmade', JSON.stringify({ 'Death': 1, 'Wrath': 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const s = JSON.parse(localStorage.getItem('d2r_rwMade')||'{}');
    const u = JSON.parse(localStorage.getItem('d2r_rwUnmade')||'{}');
    return { hasDeath: !!s['Death'], hasFaith: !!s['Wrath'], count: Object.keys(s).length, unmadeDeath: !!u['Death'], unmadeFaith: !!u['Wrath'] };
  });
  expect(r.hasDeath).toBe(false);     // seeded + explicitly un-marked → the floor RESPECTS it now
  expect(r.unmadeDeath).toBe(true);   // …and the un-mark record survives
  expect(r.hasFaith).toBe(false);     // non-seeded → unchanged behavior
  expect(r.unmadeFaith).toBe(true);
  expect(r.count).toBe(93);           // 94 minus the honored Death un-mark
});
