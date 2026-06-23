import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v412 — a SUPERIOR socketed base can't form a runeword; the base card warns + suppresses runeword guidance.
test('superior base warns + suppresses runeword guidance', async ({ page }) => {
  const errs:string[]=[]; page.on('pageerror',e=>errs.push(String(e)));
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w:any = window;
    // a normal Monarch should get runeword guidance; a superior one should warn instead
    const normalLine = w._baseRWLine ? w._baseRWLine('Monarch', 4) : '';
    eval("superiorBases.add('Monarch (Larzuk base)')");
    const supFlag = w._isSuperior('Monarch');                 // normalized match across the label
    const supLine = w._baseRWLine ? w._baseRWLine('Monarch', 4) : '';
    return { normalHasRW: /runeword/i.test(normalLine), supFlag, supWarns: /SUPERIOR base/i.test(supLine), supHasRWGuidance: /makeable in your/i.test(supLine) };
  });
  expect(r.normalHasRW).toBe(true);    // normal Monarch → runeword guidance
  expect(r.supFlag).toBe(true);        // _isSuperior matches across the (Larzuk base) suffix
  expect(r.supWarns).toBe(true);       // superior → warning shown
  expect(r.supHasRWGuidance).toBe(false); // …and the "makeable now" guidance is suppressed
  expect(errs).toEqual([]);
});
