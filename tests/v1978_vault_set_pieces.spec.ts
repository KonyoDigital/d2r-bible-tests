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

/* 2026-09-30 — WAIT FOR THE PIPE, NEVER DODGE THE PIECE. Red on v3525's and v3526's CI: sets [] and unknown [] for
 * "Laying of Hands". Measured on a fresh headless page once the board had booted: the same apply ticks it (sets
 * ["Laying of Hands (bramble mitts)"], held true). The spec fed the pipe 1.4 s after load, and a slower runner had not
 * finished booting the sets half. It now waits until the board SAYS the pipe is up, and asserts the skip is empty too
 * - so a piece the page already holds is named as that, not read as a pipe that ignores it.
 * 2026-09-30 (later) — AND THE PIECE IS ONE THIS PAGE HAS NOT FOUND, ASKED OF THE PAGE. Red on v3527, v3528 and
 * v3531's CI on the premise itself ("the page already held the piece"): a Playwright page is navigator.webdriver on
 * file:, which bible.html resolves as the OWNER's world on purpose (v2694), and the owner's seeds land there - 118 of
 * the 135 pieces, Laying of Hands among them. My earlier measurement was a plain headless Chrome, not flagged as
 * automated, so it booted an EMPTY store: a different world, and the premise looked true. Measured again with the
 * flag set: 118 held, 17 not. So the spec takes the first slot-suffixed piece the page does not hold, goes in through
 * the BARE name (findSetPiece must hand back the canonical form, the point of v1978), and a named constant can never
 * go stale under the seeds again. */
test('a set piece fed to the sets pipe TICKS — it is not filed as unknown', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => {
    const w: any = window;
    return typeof w.chronicleApply === 'function' && typeof w.findSetPiece === 'function'
      && typeof w._setHave === 'function' && typeof w._chronSetPieceSet === 'function'
      && w._chronSetPieceSet().size > 100;
  }, undefined, { timeout: 30000 });
  const r = await page.evaluate(() => {
    const w: any = window;
    const have = w._setHave();
    const all: string[] = Array.from(w._chronSetPieceSet());
    const canonical = all.find((p) => !have.has(p) && /\(/.test(p));
    if (!canonical) return { none: true, heldN: have.size, allN: all.length } as any;
    const bare = canonical.replace(/\s*\([^)]*\)\s*$/, '');
    const sp = w.findSetPiece(bare);
    const before = w._setHave().has(canonical);
    const res = w.chronicleApply({ wouldAdd: { uniques: [], sets: [sp && sp.piece] } });
    return { sets: res.sets, unknown: res.unknown, skipped: res.skipped, canonical, bare, resolved: sp && sp.piece,
             before, held: w._setHave().has(canonical), heldN: have.size, allN: all.length };
  });
  expect(r.none, `PREMISE: this page holds every set piece (${r.heldN} of ${r.allN}) - nothing is left to tick`).toBeFalsy();
  expect(r.resolved, `the bare name "${r.bare}" did not resolve to its canonical, slot-suffixed piece`).toBe(r.canonical);
  expect(r.before, 'premise: the page already held the piece, so an apply could only skip it').toBe(false);
  expect(r.skipped, 'a piece this page had NOT found was skipped as already found').toEqual([]);
  expect(r.unknown, 'the canonical piece name must NOT land in unknown').toEqual([]);
  expect(r.sets, 'the set grail must actually tick').toContain(r.canonical);
  expect(r.held, 'the sets ledger does not hold the piece after the tick').toBe(true);
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
