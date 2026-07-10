import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v637 — ONE-WAY INHERITANCE (Konyo: "all the progress for non-ladder can be on the ladder
// account too — just it can't go opposite"). Ladder Chronicle = main ∪ ladder; the reverse
// direction is sealed; ladder's own ↺ un-marks are honored against the merge.

async function cleanup(page: any) {
  await page.evaluate(() => {
    Object.keys(localStorage).filter((k) => k.indexOf('L·') === 0).forEach((k) => localStorage.removeItem(k));
    ['d2r_activeProfile'].forEach((k) => localStorage.removeItem(k));
  });
}

test('LIVE sync main→ladder: a fresh MAIN forge appears on the next ladder boot; ladder un-marks stick; nothing flows back', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  // main forges Radiance (a real main-side make)
  await page.evaluate(() => {
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    made['Radiance'] = 'Jul 10, 2026 · 03:00';
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
  });
  const mainSnap = await page.evaluate(() => localStorage.getItem('d2r_rwMade'));
  await page.evaluate(() => localStorage.setItem('d2r_activeProfile', 'ladder'));
  await page.reload(); await page.waitForTimeout(1800);
  const r1 = await page.evaluate(() => {
    const w: any = window;
    const made = JSON.parse(w.LSR.getItem('d2r_rwMade') || '{}');
    return { inherited: !!made['Radiance'], n: Object.keys(made).length };
  });
  // ladder explicitly un-makes an inherited word → must SURVIVE the next boot's merge
  await page.evaluate(() => { (window as any).rwToggleMade('Zephyr'); });   // Zephyr is seeded made on main → this un-marks it on ladder
  await page.reload(); await page.waitForTimeout(1800);
  const r2 = await page.evaluate(() => {
    const w: any = window;
    const made = JSON.parse(w.LSR.getItem('d2r_rwMade') || '{}');
    const un = JSON.parse(w.LSR.getItem('d2r_rwUnmade') || '{}');
    return { zephyrStaysUnmade: !made['Zephyr'] && !!un['Zephyr'], radianceStill: !!made['Radiance'] };
  });
  // nothing flowed back: main's rwMade byte-identical (no Zephyr removal, no ladder additions)
  await page.evaluate(() => localStorage.setItem('d2r_activeProfile', 'main'));
  await page.reload(); await page.waitForTimeout(1500);
  const r3 = await page.evaluate(({ mainSnap }: any) => ({
    identical: localStorage.getItem('d2r_rwMade') === mainSnap,
    zephyrOnMain: !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Zephyr'],
  }), { mainSnap });
  // restore main: drop the test Radiance forge
  await page.evaluate(() => {
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    delete made['Radiance']; localStorage.setItem('d2r_rwMade', JSON.stringify(made));
  });
  await cleanup(page);
  expect(r1.inherited).toBe(true);        // main's fresh forge syncs into ladder automatically
  expect(r1.n).toBe(76);                  // 75 seed + Radiance
  expect(r2.zephyrStaysUnmade).toBe(true);// the ladder ↺ un-mark beats the merge, boot after boot
  expect(r2.radianceStill).toBe(true);
  expect(r3.identical).toBe(true);        // ★ the opposite direction is SEALED
  expect(r3.zephyrOnMain).toBe(true);     // ladder's un-mark never touched main's Zephyr
});
