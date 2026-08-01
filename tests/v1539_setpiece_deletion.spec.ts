import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1539 — REG-087: APPLYING A READ COULD DELETE A SET PIECE HE ALREADY OWNED.
//
// Found by the deliberate hunt for REG-083's class (a name called in one <script>/IIFE scope and
// declared in another). `_setHave` is declared inside the IIFE at bible.html:33155; both call sites
// live in the IIFE at 35817, and nothing ever published it.
//
// The reason this was silent for so long is the shape of the guard:
//
//     hv = (typeof _setHave === 'function') && _setHave().has(key)
//
// `typeof` on an UNDECLARED name does not throw — it returns 'undefined'. So the guard was
// permanently false, the catch never ran, the owned-piece early-return never fired, and
// toggleSetPiece() went on to run against a piece already owned. That toggle is destructive three
// ways: it deletes the found date from d2r_foundLog, writes d2r_grailUnfound so the boot seed floor
// can never restore it, and removes the piece.
//
// The proof it was a mistake and not a design is one line above: the `uni` branch guards with
// _gFound, which IS published (window._gFound), and returns early correctly.

test.describe('v1539 — a set piece he owns survives being applied again', () => {
  test('★ the guard that protects an owned piece is REACHABLE from where it is used', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => ({
      published: typeof (window as any)._setHave === 'function',
      // the sibling guard that always worked — the parity this fix restores
      uniPublished: typeof (window as any)._gFound === 'function',
    }));
    expect(r.published, '_setHave must be reachable from the IIFE that guards with it').toBe(true);
    expect(r.uniPublished).toBe(true);
  });

  test('★ THE DATA LOSS: applying a read for an owned piece must NOT un-find it', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => {
      const w: any = window;
      // own a real piece, exactly as a hand-tick would
      const s = w.fsetsScan();
      let piece = '';
      for (const set of (s.sets || [])) {
        const p = (set.pieces || []).find((x: any) => !x.have);
        if (p) { piece = p.name; break; }
      }
      w.toggleSetPiece(piece);                       // now owned + dated
      const ownedBefore = w._setHave().has(piece);
      const datedBefore = !!JSON.parse(w.LSR.getItem('d2r_foundLog') || '{}')[piece];

      // now apply a chronicle/TV·D read that names the SAME piece — the exact path that deleted it
      const out = w.chronicleApply({ wouldAdd: { uniques: [], sets: [{ name: piece }] } });

      const unfound = JSON.parse(w.LSR.getItem('d2r_grailUnfound') || '{}');
      return {
        piece, ownedBefore, datedBefore,
        ownedAfter: w._setHave().has(piece),
        datedAfter: !!JSON.parse(w.LSR.getItem('d2r_foundLog') || '{}')[piece],
        markedUnfound: !!unfound[piece],
        applied: out.sets, skipped: out.skipped,
      };
    });
    expect(r.ownedBefore).toBe(true);
    expect(r.datedBefore).toBe(true);
    expect(r.ownedAfter, 'the piece was DELETED from his set chronicle').toBe(true);
    expect(r.datedAfter, 'the found DATE was erased from d2r_foundLog').toBe(true);
    expect(r.markedUnfound,
      'd2r_grailUnfound was written — the boot seed floor could never have restored it').toBe(false);
    expect(r.applied, 'an owned piece must be SKIPPED, not re-applied').toEqual([]);
    expect(r.skipped).toContain(r.piece);
  });

  test('a piece he does NOT own still registers normally', async ({ page }) => {
    // the fix must not turn the guard into a blanket refusal
    await page.goto(URL);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.fsetsScan();
      let piece = '';
      for (const set of (s.sets || [])) {
        const p = (set.pieces || []).find((x: any) => !x.have);
        if (p) { piece = p.name; break; }
      }
      const out = w.chronicleApply({ wouldAdd: { uniques: [], sets: [{ name: piece }] } });
      return { piece, applied: out.sets, owned: w._setHave().has(piece) };
    });
    expect(r.applied).toEqual([r.piece]);
    expect(r.owned).toBe(true);
  });

  test('★ the guards are KEPT, so they are now real load-order guards', async () => {
    // the fix publishes the helper; it does not delete the typeof checks. If the board is ever
    // restructured so this IIFE runs first, the guard must still hold rather than throw.
    // read the SOURCE, not the DOM: the browser normalises script text and this is a claim about
    // what is written in the file
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    expect(src).toContain("typeof window._setHave==='function'");
    expect(src, 'the bare cross-scope name must be gone from BOTH call sites')
      .not.toContain("(typeof _setHave==='function')");
  });
});
