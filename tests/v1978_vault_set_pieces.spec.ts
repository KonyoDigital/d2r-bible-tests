import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1978 — A SET PIECE READ OFF FILM WAS FILED AS A UNIQUE.
 *
 * vaultAccumApply called chronicleApply({ wouldAdd: { uniques: grailNames, sets: [] } }) with `sets`
 * HARDCODED EMPTY. So a Tal Rasha or Disciple piece that a sweep grounded went down the uniques pipe,
 * never reached toggleSetPiece, and the set grail never ticked.
 *
 * The machinery was already there and simply never fed: _chronicleApplyInner reads wouldAdd.sets in
 * seven places and calls toggleSetPiece twice. This was a JOIN, not new logic.
 *
 * THE TRAP THAT MADE THE FIRST FIX WRONG. The sets branch validates every name against
 * _chronSetPieceSet() — 135 entries, all SLOT-SUFFIXED — and pushes anything absent to `unknown`
 * instead of ticking it. Passing the bare read name therefore routed every set piece to `unknown`,
 * which is WORSE than the mis-file it replaced. findSetPiece already returns the canonical suffixed
 * string as `.piece`, so that is what goes through. Caught by feeding the pipe and reading
 * `unknown:["Laying of Hands"]` back — never by inspection.
 */

test('the split sends set pieces one way and uniques the other', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    const u: string[] = [], s: string[] = [];
    ['Laying of Hands', 'Shako', 'Bonesnap', "Tal Rasha's Adjudication (amulet)"].forEach((n) => {
      let sp: any = null; try { sp = w.findSetPiece(n); } catch (e) { /* stays a unique */ }
      if (sp && sp.piece) s.push(sp.piece); else u.push(n);
    });
    return { u, s };
  });
  expect(r.u, 'plain uniques must not be diverted').toEqual(['Shako', 'Bonesnap']);
  expect(r.s.length, 'both set pieces must be caught, bare AND slot-suffixed').toBe(2);
  /* The canonical form is the point: the bare name is rejected downstream. */
  expect(r.s[0]).toMatch(/\(/);
});

test('a set piece fed to the sets pipe TICKS — it is not filed as unknown', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    const sp = w.findSetPiece('Laying of Hands');
    const res = w.chronicleApply({ wouldAdd: { uniques: [], sets: [sp.piece] } });
    return { sets: res.sets, unknown: res.unknown, canonical: sp.piece };
  });
  expect(r.unknown, 'the canonical piece name must NOT land in unknown').toEqual([]);
  expect(r.sets, 'the set grail must actually tick').toContain(r.canonical);
});

/* The regression guard proper: the bare name must still be refused, so if anyone "simplifies" the
   fix back to passing the read name, this fails instead of silently sending pieces to unknown. */
test('the BARE name is still refused by the sets pipe — that is why .piece is used', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      bare: w._chronSetPieceSet().has('Laying of Hands'),
      canonical: w._chronSetPieceSet().has(w.findSetPiece('Laying of Hands').piece),
      size: w._chronSetPieceSet().size,
    };
  });
  expect(r.bare, 'the bare read name is NOT in the piece set — passing it routes to unknown').toBe(false);
  expect(r.canonical, 'the .piece form IS in the piece set').toBe(true);
  expect(r.size, 'the piece set is his 135 set pieces').toBe(135);
});
