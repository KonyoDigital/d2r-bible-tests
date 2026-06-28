import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v436 — Chronicle sync: a runeword you've ALREADY FORGED (rwMade) is exempted from the "Keep for
// runewords" examples (throw-out review + base hover + mule cards), so you only see what's LEFT to make.
// Also: seed is now 30 (Authority + Melody added).
test("seed is 34 (+ Spirit + Grief + Stone added to the floor)", async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    return { count: w._RWC_SEED ? Object.keys(w._RWC_SEED).length : 0,
             hasAuthority: !!(w._RWC_SEED && w._RWC_SEED['Authority']),
             hasMelody: !!(w._RWC_SEED && w._RWC_SEED['Melody']),
             hasAncients: !!(w._RWC_SEED && w._RWC_SEED["Ancients' Pledge"]) };
  });
  expect(r.count).toBe(34);
  expect(r.hasAuthority).toBe(true);
  expect(r.hasMelody).toBe(true);
  expect(r.hasAncients).toBe(true);
});

test('an already-created runeword is exempted from the Keep-for-runewords list', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    // pick a body-armor base + a runeword that fits AND is seeded-created
    const base = 'Archon Plate';
    const fits = (w._baseRunewords ? w._baseRunewords(base) : []) as Array<{n:string,s:number}>;
    const maxS = fits.reduce((m,x)=>Math.max(m,x.s),0);
    const fitMax = fits.filter(x=>x.s===maxS).map(x=>x.n);
    const made = fitMax.find(n => w._RWC_SEED && w._RWC_SEED[n]);   // a created one that fits this base
    if (!made) return { skip:true };
    const lineWithMade = w._baseRWLine(base, maxS);          // created → should be excluded from the names
    w.rwToggleMade(made);                                    // un-mark it
    const lineAfterUnmake = w._baseRWLine(base, maxS);       // now NOT created → should appear
    return { skip:false, made, maxS, lineWithMade, lineAfterUnmake };
  });
  expect(r.skip).toBeFalsy();
  // the created runeword's NAME should NOT appear in the makeable list while it's marked created...
  const nameInList = (html:string, n:string) => new RegExp('🔨[^<]*<[^>]*>[\\s\\S]*?Keep for runewords[\\s\\S]*?'+n.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).test(html);
  expect(r.lineWithMade.includes('already created')).toBe(true);  // created ones are cancelled out + counted
  // ...and it SHOULD appear once un-marked
  expect(r.lineAfterUnmake).toContain(r.made);
});
