import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v506 — when a non-elite WHITE base is intaked, the Forge's upgrade task must NAME the elite target
// (Bone Helm → Bone Visage) and show what the higher-socket elite tier UNLOCKS that the current max can't.
async function upgradeOf(page: any, base: string) {
  await page.addInitScript((b: string) => {
    localStorage.setItem('d2r_owned', JSON.stringify([b]));
    localStorage.setItem('d2r_ethereal', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));   // nothing made → all runewords are candidates
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, base);
  await page.goto(URL);
  await page.waitForTimeout(1300);
  return await page.evaluate((b: string) => {
    const w: any = window;
    w._ensureSocketBaseEntry(b);
    const s = w.forgeScan();
    const baseName = b.replace(/\s*\(.*$/, '');
    return (s.upgrades || []).find((u: any) => u.base && u.base.base === baseName) || null;
  }, base);
}

test('Bone Helm upgrade names Bone Visage and unlocks its 3os helm runewords', async ({ page }) => {
  const u = await upgradeOf(page, 'Bone Helm (Larzuk base)');
  expect(u).not.toBeNull();
  expect(u.eliteName).toBe('Bone Visage');
  expect(u.curMax).toBe(2);
  expect(u.eliteMax).toBe(3);
  // unlocks must be runewords needing MORE than 2 sockets (Bone Helm's max) — 3os caster words
  expect(u.unlocks.length).toBeGreaterThan(0);
  expect(u.unlocks).toContain('Delirium');   // 3os helm runeword Bone Helm can't make, Bone Visage can
});

test('shield/armor/wand upgrades surface the right unlocks', async ({ page }) => {
  const boneShield = await upgradeOf(page, 'Bone Shield (Larzuk base)');
  expect(boneShield?.eliteName).toBe('Troll Nest');
  expect(boneShield?.unlocks).toContain('Sanctuary');   // 3os shield word a 2os Bone Shield can't form

  const yewWand = await upgradeOf(page, 'Yew Wand (Larzuk base)');
  expect(yewWand?.eliteName).toBe('Ghost Wand');
  expect(yewWand?.unlocks.length).toBeGreaterThan(0);   // White/Wind (2os) — Yew Wand maxes at 1
});
