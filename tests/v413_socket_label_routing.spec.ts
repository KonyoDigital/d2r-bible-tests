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
  expect(r.circlet).toBe('bases');
  expect(r.trident).toBe('bases');
  expect(r.monarch).toBe('bases');
  expect(r.windforce).not.toBe('bases');
});
