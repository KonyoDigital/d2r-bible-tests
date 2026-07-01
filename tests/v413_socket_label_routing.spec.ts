import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v413 — intake-label socketed bases route to SOCKETED even without an EXTRA_ITEMS entry (suffix detection).
test('socketed-base labels route to SOCKETED', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window; const sm = w.suggestMule;
    return {
      grim: sm('Grim Scythe (6os)').id,
      circlet: sm('Circlet (Larzuk base)').id,
      trident: sm('Trident (3os low base)').id,
      monarch: sm('Monarch (Larzuk base)').id,
      // a real unique with no socket suffix must still route by slot, not to bases
      windforce: sm('Windforce').id,
    };
  });
  expect(r.grim).toBe('bases');
  // v524 — a CIRCLET can't hold a runeword (type=circ, gems/jewels only) → NOT a socketed keeper → throw-out.
  expect(r.circlet).toBe('__throwout');
  expect(r.trident).toBe('bases');
  expect(r.monarch).toBe('bases');
  expect(r.windforce).not.toBe('bases');
});

// v502 — a white base that CANNOT be socketed (orb / throwing weapon / javelin) is NOT a socketed/craft
// base; it has no runeword/craft/socket value → route to throw-out (vendor), not the SOCKETED locker.
test('non-socketable white bases route to throw-out, not SOCKETED', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window; const sm = w.suggestMule;
    return {
      throwingAxe: sm('Throwing Axe').id, hurlbat: sm('Hurlbat').id,
      javelin: sm('Javelin').id, glaive: sm('Glaive').id,
      orb: sm('Eldritch Orb').id,
      // regression: a socketable white weapon still routes to the SOCKETED/bases locker
      crystalSword: sm('Crystal Sword').id, longBow: sm('Long Bow').id,
    };
  });
  expect(r.throwingAxe).toBe('__throwout');
  expect(r.hurlbat).toBe('__throwout');
  expect(r.javelin).toBe('__throwout');
  expect(r.glaive).toBe('__throwout');
  expect(r.orb).toBe('__throwout');
  expect(r.crystalSword).toBe('bases');   // socketable → still a base keeper
  expect(r.longBow).toBe('bases');
});
