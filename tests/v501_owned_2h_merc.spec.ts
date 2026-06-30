import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test('owned 2H base + runes → runeword shows as a MERC weapon make-now (Honor in a 5os Zweihander)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Zweihander (5os)']));
    // Honor = Amn El Ith Tir Sol — give plenty
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 5, El: 5, Ith: 5, Tir: 5, Sol: 5 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL);
  await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Zweihander (5os)');
    const s = w.forgeScan();
    const honor = (s.now || []).find((t: any) => t.rw === 'Honor');
    return honor ? { found: true, mercOwn: honor.mercOwn, hand: honor.hand, base: honor.base?.base, deferred: honor.deferred } : { found: false };
  });
  expect(r.found).toBe(true);
  expect(r.mercOwn).toBe(true);
  expect(r.hand).toBe('2H merc');
  expect(r.base).toBe('Zweihander');
});
