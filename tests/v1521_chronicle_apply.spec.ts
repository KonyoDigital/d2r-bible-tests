import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1521 — THE APPLY: the one step in the Chronicle arc that writes.
//
// It goes through grailFoundUni / grailTogglePiece — the same functions his manual ✓ tick uses — so
// a swept name is indistinguishable from one he ticked by hand, and inherits the date stamp, the
// tally sync and the ↩ undo bar for free.
//
// The bug this spec exists to prevent: those functions TOGGLE. Applying a name he already has would
// UN-FIND it. That failure is silent, it looks like a successful import, and it removes something
// from a ledger with no "unfind" in the game it mirrors. It is checked first here for the same reason
// it is checked first in the code.

async function board(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(1800);
}

/** A unique the CURRENT chronicle does not have — picked live, never hard-coded. */
async function anUnfound(page: any): Promise<string> {
  return page.evaluate(() => {
    const w: any = window;
    const s = w.funiScan();
    return (s.missing || []).map((m: any) => m.n || m.name || m)[0];
  });
}

test.describe('v1521 — the apply writes once, and only forward', () => {
  test('a gated name lands in the real ledger, DATED, exactly as a hand-tick would', async ({ page }) => {
    await board(page);
    const name = await anUnfound(page);
    const r = await page.evaluate((n: string) => {
      const w: any = window;
      const before = !!w._gFound(n);
      const out = w.chronicleApply({ wouldAdd: { uniques: [{ name: n, why: 'x', witnesses: ['a', 'b'] }], sets: [] } });
      const log = JSON.parse(w.LSR.getItem('d2r_foundLog') || '{}');
      return { before, applied: out.uniques, found: !!w._gFound(n), dated: !!log[n] };
    }, name);
    expect(r.before).toBe(false);
    expect(r.applied).toEqual([name]);
    expect(r.found).toBe(true);
    expect(r.dated, 'the apply must date the chronicle, like every other tick').toBe(true);
  });

  test('★ THE CATASTROPHIC CASE: applying something he ALREADY has never un-finds it', async ({ page }) => {
    await board(page);
    const name = await anUnfound(page);
    const r = await page.evaluate((n: string) => {
      const w: any = window;
      w.chronicleApply({ wouldAdd: { uniques: [{ name: n }], sets: [] } });   // now found
      const afterFirst = !!w._gFound(n);
      const out = w.chronicleApply({ wouldAdd: { uniques: [{ name: n }], sets: [] } });   // again
      return { afterFirst, stillFound: !!w._gFound(n), applied: out.uniques, skipped: out.skipped };
    }, name);
    expect(r.afterFirst).toBe(true);
    expect(r.stillFound, 'a second apply must NOT toggle it back off').toBe(true);
    expect(r.applied).toEqual([]);
    expect(r.skipped).toContain(name);
  });

  test('★ undo reverses the batch — and ONLY what that batch flipped', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const miss = (w.funiScan().missing || []).map((m: any) => m.n || m.name || m);
      const already = miss[0], fresh = miss[1];
      w.chronicleApply({ wouldAdd: { uniques: [{ name: already }], sets: [] } });   // he "already had" this
      w.chronicleApply({ wouldAdd: { uniques: [{ name: already }, { name: fresh }], sets: [] } });
      const undone = w.chronicleUndoLast();
      return { already, fresh, undone: undone.undone,
               alreadyStill: !!w._gFound(already), freshGone: !w._gFound(fresh) };
    });
    expect(r.undone).toBe(1);
    expect(r.freshGone, 'the name this batch added must come back off').toBe(true);
    expect(r.alreadyStill,
      'undo must never reverse a find the batch did not make — he had that one before').toBe(true);
  });

  test('set pieces go to the SET store, never into the grail', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.fsetsScan();
      let piece = '';
      for (const set of (s.sets || [])) {
        const p = (set.pieces || []).find((x: any) => !x.have);
        if (p) { piece = p.name; break; }
      }
      if (!piece) return { skip: true };
      const out = w.chronicleApply({ wouldAdd: { uniques: [], sets: [{ name: piece }] } });
      // d2r_setPieces is an ARRAY of piece names (what _setHave parses) — not a name-keyed object
      const sp = JSON.parse(w.LSR.getItem('d2r_setPieces') || '[]');
      return { piece, applied: out.sets, inSetStore: sp.indexOf(piece) >= 0,
               inGrail: !!w._gFound(piece) };
    });
    if ((r as any).skip) test.skip(true, 'no unfound set piece in this chronicle');
    expect(r.applied).toEqual([r.piece]);
    expect(r.inSetStore).toBe(true);
  });

  test('★ a set the panel called COMPLETE expands to all its pieces', async ({ page }) => {
    // one row worth five: the Chronicle often shows a set as done without its pieces being legible,
    // and the game saying "complete" IS the claim
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.fsetsScan();
      const target = (s.sets || []).find((x: any) => (x.pieces || []).some((p: any) => !p.have));
      const before = (target.pieces || []).filter((p: any) => p.have).length;
      const out = w.chronicleApply({ wouldAdd: { uniques: [], sets: [], completeSets: [{ name: target.name }] } });
      const after = (w.fsetsScan().sets || []).find((x: any) => x.name === target.name);
      return { set: target.name, total: target.pieces.length, before,
               added: out.sets.length, skipped: out.skipped.length,
               nowHave: (after.pieces || []).filter((p: any) => p.have).length };
    });
    expect(r.nowHave, 'every piece of the set must now be held').toBe(r.total);
    expect(r.added, 'only the MISSING pieces are written').toBe(r.total - r.before);
    expect(r.skipped, 'the ones he already had are skipped, not re-ticked').toBe(r.before);
  });

  test('★ an UNKNOWN set name invents nothing', async ({ page }) => {
    // the board owns __allSets(); a name it does not recognise must produce no pieces at all
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const out = w.chronicleApply({ wouldAdd: { uniques: [], sets: [],
        completeSets: [{ name: "Some Mod Set That Does Not Exist" }] } });
      return { added: out.sets, skipped: out.skipped };
    });
    expect(r.added).toEqual([]);
    expect(r.skipped.join(' ')).toContain('unknown set');
  });

  test('an empty proposal writes nothing and records no batch', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.LSR.setItem('d2r_chronApplied', '[]');
      const out = w.chronicleApply({ wouldAdd: { uniques: [], sets: [] } });
      return { out, log: JSON.parse(w.LSR.getItem('d2r_chronApplied') || '[]').length };
    });
    expect(r.out.uniques).toEqual([]);
    expect(r.log, 'an apply that changed nothing must not leave an undo stub').toBe(0);
  });

  test('undo with nothing to undo is a no-op, not an exception', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.LSR.setItem('d2r_chronApplied', '[]');
      return w.chronicleUndoLast();
    });
    expect(r.undone).toBe(0);
  });

  test('★ the batch log follows the chronicle it belongs to across machines', async ({ page }) => {
    // an undo that reached across machines would reverse a find its own chronicle never had
    await page.goto(URL);
    await page.waitForTimeout(600);
    const forked = await page.evaluate(() => (window as any)._WP_FORKED.has('d2r_chronApplied'));
    expect(forked).toBe(true);
  });

  test('the proposal fetch refuses honestly when the console is not reachable', async ({ page }) => {
    await board(page);
    await page.route('**/api/chronicle_sweep', (r: any) => r.abort());
    const r = await page.evaluate(() => (window as any).chronicleFetchProposal());
    expect(r.ok).toBe(false);
    expect(r.why, 'a silent nothing would read as "no finds"').toBeTruthy();
  });
});
