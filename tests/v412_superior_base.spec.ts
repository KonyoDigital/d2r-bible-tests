import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v412→v450 — CORRECTED: a SUPERIOR base IS a normal-quality item and DOES form runewords (it keeps its
// superior bonus on top). The base card now SHOWS the runeword guidance + a positive superior note, and no
// longer warns "cannot make a runeword" or suppresses the guidance. _isSuperior still normalizes across the
// "(Larzuk base)" suffix so the note attaches to the right registered label.
test('superior base shows runeword guidance + positive note (no suppression)', async ({ page }) => {
  const errs:string[]=[]; page.on('pageerror',e=>errs.push(String(e)));
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w:any = window;
    const normalLine = w._baseRWLine ? w._baseRWLine('Monarch', 4) : '';
    eval("superiorBases.add('Monarch (Larzuk base)')");
    const supFlag = w._isSuperior('Monarch');                 // normalized match across the label
    const supLine = w._baseRWLine ? w._baseRWLine('Monarch', 4) : '';
    return {
      normalHasRW: /runeword/i.test(normalLine),
      supFlag,
      supValidNote: /valid runeword base/i.test(supLine),
      supHasRWGuidance: /makeable in your/i.test(supLine),
      supNoFalseWarning: !/cannot make a runeword/i.test(supLine),
    };
  });
  expect(r.normalHasRW).toBe(true);       // normal Monarch → runeword guidance
  expect(r.supFlag).toBe(true);           // _isSuperior matches across the (Larzuk base) suffix
  expect(r.supValidNote).toBe(true);      // superior → "valid runeword base" note shown
  expect(r.supHasRWGuidance).toBe(true);  // …and the "makeable now" guidance is STILL shown
  expect(r.supNoFalseWarning).toBe(true); // …and the old false "cannot make a runeword" warning is gone
  expect(errs).toEqual([]);
});
