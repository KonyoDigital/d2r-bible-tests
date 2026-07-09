import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
test('affix pool renders for rolled jewelry, not for gear/crafted', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    return {
      ring: w._affixPoolHtml('Ring','rare'),
      amulet: w._affixPoolHtml('Amulet','magic'),
      gc: w._affixPoolHtml('Grand Charm','magic'),
      gear: w._affixPoolHtml('Cryptic Axe','rare'),     // not jewelry → empty
      crafted: w._affixPoolHtml('Ring','crafted'),       // crafted → empty
    };
  });
  expect(r.ring).toContain('Dual leech');
  expect(r.ring).toContain('can roll');
  expect(r.amulet).toContain('class skill');
  expect(r.gc).toContain('SKILLER');
  expect(r.gear).toBe('');
  expect(r.crafted).toBe('');
});
test('chronicle seed has all 74 created runewords', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window; const s = w._RWC_SEED || {};
    return { count: Object.keys(s).length, hasDeath: !!s['Death'], hasMosaic: !!s['Mosaic'], hasEdge: !!s['Edge'] };
  });
  expect(r.count).toBe(74);   // v631.1 +Mist +Brand +Wisdom +Phoenix (Jul 9)
  expect(r.hasDeath).toBe(true);
  expect(r.hasMosaic).toBe(true);
  expect(r.hasEdge).toBe(true);
});
