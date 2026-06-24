import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v419 — runeword rune-saver guard: ladder-only stamp + per-RW verified working/failed + cube block.
test('ladder-only stamp + fail-seeded guard on Mania', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    const card = w.runewordDetailHtml ? w.runewordDetailHtml('Mania') : '';
    return {
      ladderStamp: /LADDER/.test(card),
      guard: w._rwGuard ? w._rwGuard('Mania') : null,
      // Heart of the Oak is non-ladder, unverified → caution, no block
      hotoGuard: w._rwGuard ? w._rwGuard('Heart of the Oak') : null,
      ladderData: !!(w._RW_LADDER_ONLY && w._RW_LADDER_ONLY['Mania']),
    };
  });
  expect(r.ladderStamp).toBe(true);
  expect(r.guard.level).toBe('block');       // seeded as failed + ladder-only
  expect(r.ladderData).toBe(true);
  expect(r.hotoGuard.level).toBe('caution'); // not ladder-only, unverified
});
test('marking a runeword worked clears the block', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    w.rwSetVerify('Mania', 'ok');
    return { after: w._rwGuard('Mania').level };
  });
  expect(r.after).toBe('ok');
});
