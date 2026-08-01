import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1540 — 📜 CHRONICLE PHOTO INTAKE.
//
// `chronicle-uniques` / `chronicle-sets` shipped in functions/api/intake.js at v1510 with nine tests
// and ZERO callers — tv/CHRONICLE_ARC.md names it as "a road with no traffic". Both existing lanes
// (live + retro) assume TV DIABLO is running, so on his Windows PC, his phone, or his cousin's box
// there was no Chronicle path at all. This is that path.
//
// What these tests hold is the doctrine, not the plumbing: nothing is written before he presses
// register, a refusal is SHOWN rather than swallowed, and the write goes through the single
// chronicleApply() path so merge-max, the owned-item guard (REG-087) and the batch undo are
// inherited instead of re-implemented.

/** Fake the worker. Every case below is a real response shape from functions/api/intake.js. */
async function stubIntake(page: any, reply: any | any[]) {
  const queue = Array.isArray(reply) ? [...reply] : null;
  await page.route((u: URL) => /\/api\/intake/.test(u.href), (r: any) =>
    r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify(queue ? (queue.shift() || {}) : reply),
    }));
}

/** Drive the intake without a real file picker — a 1×1 png is enough, the worker is stubbed. */
async function read(page: any, ledger: 'uniques' | 'sets', n = 1) {
  return page.evaluate(async ({ ledger, n }: any) => {
    const w: any = window;
    w._chronShotLedger = ledger;
    const png = atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==');
    const bytes = new Uint8Array(png.length);
    for (let i = 0; i < png.length; i++) bytes[i] = png.charCodeAt(i);
    const files = Array.from({ length: n }, (_, i) =>
      new File([bytes], 'chron' + i + '.png', { type: 'image/png' }));
    return await w.chronicleShotIntake(files);
  }, { ledger, n });
}

// He presses these buttons FROM the Forge tab, and the report renders inside it — a .tab-content
// that is display:none until the tab is active. A test that never switches tabs is testing a
// hidden div, which is how the first run "passed" its text assertions while nothing was visible.
const boot = async (page: any) => {
  await page.goto(URL);
  await page.waitForTimeout(1800);
  await page.evaluate(() => { try { (window as any).switchTab('funi'); } catch { /* */ } });
  await page.waitForTimeout(250);
};

test.describe('v1540 — the Chronicle path that needs no console', () => {
  test('★ NOTHING is written by a read — the grail only moves when he registers', async ({ page }) => {
    await boot(page);
    await stubIntake(page, { found: ['Harlequin Crest'], notFound: [], sets: [], witness: 'none',
      printed: {}, read: { found: 1, notFound: 0 }, unrecognized: [] });
    const before = await page.evaluate(() => (window as any).LSR.getItem('d2r_foundLog') || '{}');
    const p = await read(page, 'uniques');
    const after = await page.evaluate(() => (window as any).LSR.getItem('d2r_foundLog') || '{}');
    expect(after, 'a READ must not touch the ledger — there is no unfind in Diablo').toBe(before);
    expect(p.wouldAdd.uniques.length + p.wouldAdd.sets.length).toBeGreaterThan(0);
    // and the proposal is offered, not applied
    expect(await page.isVisible('#chron-shot-go')).toBe(true);
  });

  test('★ register writes through chronicleApply — so the batch is undoable AS a batch', async ({ page }) => {
    await boot(page);
    const name = await page.evaluate(() => {
      const w: any = window;
      const miss = (w.funiScan().missing || [])[0];
      return miss ? (miss.n || miss.name || miss) : '';
    });
    expect(name, 'the board must have at least one missing unique to test with').toBeTruthy();
    await stubIntake(page, { found: [name], notFound: [], sets: [], witness: 'none',
      printed: {}, read: { found: 1, notFound: 0 }, unrecognized: [] });
    await read(page, 'uniques');
    const r = await page.evaluate(() => {
      const w: any = window;
      const res = w.chronicleShotApply();
      const log = JSON.parse(w.LSR.getItem('d2r_chronApplied') || '[]');
      return { res, batched: log.length, lanes: log[log.length - 1]?.lanes };
    });
    expect(r.res.uniques.length, 'it registered').toBe(1);
    expect(r.batched, 'the batch record is what makes an import undoable as an import').toBeGreaterThan(0);
    expect(r.lanes, 'the batch remembers this came from a photo, not a sweep').toContain('photo');
    const undone = await page.evaluate(() => (window as any).chronicleUndoLast().undone);
    expect(undone).toBe(1);
  });

  test('★ an item he ALREADY owns is never re-applied (REG-087 lives in the shared path)', async ({ page }) => {
    await boot(page);
    const name = await page.evaluate(() => {
      const w: any = window;
      const miss = (w.funiScan().missing || [])[0];
      const n = miss ? (miss.n || miss.name || miss) : '';
      w.toggleOwned(n);                       // he already has it, with its found date
      return n;
    });
    await stubIntake(page, { found: [name], notFound: [], sets: [], witness: 'none',
      printed: {}, read: { found: 1, notFound: 0 }, unrecognized: [] });
    const p = await read(page, 'uniques');
    expect(p.wouldAdd.uniques, 'an owned item is not even proposed').toEqual([]);
    expect(p.already).toBe(1);
    const txt = (await page.textContent('#chron-shot-report')) || '';
    expect(txt).toContain('Nothing to register');
    expect(txt, 'and it says WHY it is empty rather than shrugging').toContain('already ticked');
  });

  test('★ a wrong-ledger refusal is SHOWN and contributes nothing', async ({ page }) => {
    await boot(page);
    await stubIntake(page, { found: [], notFound: [], sets: [], note: 'wrong-ledger',
      witness: 'none', printed: {}, read: {}, unrecognized: [] });
    const p = await read(page, 'uniques');
    expect(p.wouldAdd.uniques).toEqual([]);
    const txt = (await page.textContent('#chron-shot-report')) || '';
    expect(txt).toContain('the OTHER ledger');
    expect(await page.locator('#chron-shot-go').count(), 'nothing to register, so nothing is offered').toBe(0);
  });

  test('a no-found-state page claims nothing, and says so', async ({ page }) => {
    await boot(page);
    await stubIntake(page, { found: [], notFound: [], sets: [], note: 'no-found-state',
      witness: 'none', printed: {}, read: {}, unrecognized: [] });
    await read(page, 'uniques');
    expect(await page.textContent('#chron-shot-report')).toContain('no found-marks were visible');
  });

  test('★ MERGE-MAX across pages — a page that scrolled past a row is not evidence it is empty', async ({ page }) => {
    await boot(page);
    const [a, b] = await page.evaluate(() => {
      const m = ((window as any).funiScan().missing || []).slice(0, 2);
      return m.map((x: any) => x.n || x.name || x);
    });
    // page 1 found A and says B was not found; page 2 found B. The union must be BOTH.
    await stubIntake(page, [
      { found: [a], notFound: [b], sets: [], witness: 'none', printed: {}, read: { found: 1, notFound: 1 }, unrecognized: [] },
      { found: [b], notFound: [], sets: [], witness: 'none', printed: {}, read: { found: 1, notFound: 0 }, unrecognized: [] },
    ]);
    const p = await read(page, 'uniques', 2);
    expect(p.wouldAdd.uniques.sort(), 'notFound on one page must never subtract a find from another')
      .toEqual([a, b].sort());
  });

  test('★ the second witness is stated, never resolved in our favour', async ({ page }) => {
    await boot(page);
    const name = await page.evaluate(() => {
      const m = ((window as any).funiScan().missing || [])[0];
      return m.n || m.name || m;
    });
    await stubIntake(page, { found: [name], notFound: [], sets: [], witness: 'differ',
      printed: { found: 9, total: 10 }, read: { found: 1, notFound: 0 }, unrecognized: [] });
    await read(page, 'uniques');
    const txt = (await page.textContent('#chron-shot-report')) || '';
    expect(txt).toContain('DIFFER');
    expect(txt, 'the disagreement is shown BEFORE he registers, while it can still matter')
      .toContain('check before registering');
    expect(await page.isVisible('#chron-shot-go'), 'it still lets him decide — it warns, it does not block').toBe(true);
  });

  test('a partial page is honest that its printed total proves nothing', async ({ page }) => {
    await boot(page);
    const name = await page.evaluate(() => {
      const m = ((window as any).funiScan().missing || [])[0];
      return m.n || m.name || m;
    });
    await stubIntake(page, { found: [name], notFound: [], sets: [], witness: 'none',
      printed: { found: 40, total: 400 }, read: { found: 1, notFound: 0 }, unrecognized: [] });
    await read(page, 'uniques');
    const txt = (await page.textContent('#chron-shot-report')) || '';
    expect(txt).toContain('not a witness');
    expect(txt, 'and that this is normal, so it does not read as a fault').toContain('normal');
  });

  test('★ the SETS ledger is read with the sets vocabulary and lands on set pieces', async ({ page }) => {
    await boot(page);
    // what the game prints is the CLEAN name; the board stores the full "(slot)" piece name
    const { clean, full } = await page.evaluate(() => {
      const w: any = window;
      const V = w._grailVocab();
      const have = w._setHave();
      const clean = Object.keys(V.pieceMap).find((c) => !have.has(V.pieceMap[c])) || '';
      return { clean, full: V.pieceMap[clean] };
    });
    expect(clean).toBeTruthy();
    await stubIntake(page, { found: [clean], notFound: [], sets: [], witness: 'none',
      printed: {}, read: { found: 1, notFound: 0 }, unrecognized: [] });
    const p = await read(page, 'sets');
    expect(p.wouldAdd.sets, 'the clean name must be mapped back to the stored piece name').toEqual([full]);
    expect(p.wouldAdd.uniques, 'a sets read never writes into the uniques ledger').toEqual([]);
    const applied = await page.evaluate(() => {
      const w: any = window;
      w.chronicleShotApply();
      return JSON.parse(w.LSR.getItem('d2r_setPieces') || '[]');
    });
    expect(applied).toContain(full);
  });

  test('★ the two ledgers get DIFFERENT vocabularies — no cross-ledger matching', async ({ page }) => {
    await boot(page);
    const sent: string[] = [];
    await page.route((u: URL) => /\/api\/intake/.test(u.href), async (r: any) => {
      try { sent.push(JSON.stringify(JSON.parse(r.request().postData() || '{}').names || [])); } catch { /* */ }
      await r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ found: [], notFound: [], sets: [], witness: 'none', printed: {}, read: {}, unrecognized: [] }) });
    });
    await read(page, 'uniques');
    await read(page, 'sets');
    expect(sent).toHaveLength(2);
    expect(sent[0], 'the two reads must not be handed the same word list').not.toBe(sent[1]);
    const uni = JSON.parse(sent[0]), sets = JSON.parse(sent[1]);
    expect(uni.length).toBeGreaterThan(50);
    expect(sets.length).toBeGreaterThan(20);
    // The two lists are near-disjoint by construction, and the residue is REAL RotW data rather
    // than a bug: "Wilhelm's Pride" is both a unique and a set piece. That single ambiguous name is
    // exactly why the caller states the ledger instead of the reader classifying the page — with
    // one word list you could not tell which of the two he found. Pinned so that if the catalogue
    // ever drifts into wholesale overlap, this fails loudly rather than degrading quietly.
    const overlap = uni.filter((x: string) => sets.includes(x));
    expect(overlap.length, 'overlap should stay a handful of genuinely ambiguous names: ' + overlap.join(', '))
      .toBeLessThanOrEqual(3);
  });

  test('discard leaves nothing behind', async ({ page }) => {
    await boot(page);
    const name = await page.evaluate(() => {
      const m = ((window as any).funiScan().missing || [])[0];
      return m.n || m.name || m;
    });
    await stubIntake(page, { found: [name], notFound: [], sets: [], witness: 'none',
      printed: {}, read: { found: 1, notFound: 0 }, unrecognized: [] });
    await read(page, 'uniques');
    const r = await page.evaluate(() => {
      const w: any = window;
      w.chronicleShotDiscard();
      return { held: w.chronicleShotProposal(), applied: w.chronicleShotApply() };
    });
    expect(r.held).toBeNull();
    expect(r.applied, 'applying a discarded read must be a no-op, not a crash').toBeNull();
  });

  test('★ every helper it uses is in ITS OWN scope (the REG-083 / REG-087 class)', async ({ page }) => {
    // Both of those bugs were a name that read as available and was declared in another IIFE. The
    // guard is not "it worked once" — it is that the functions are reachable from where they are used.
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      return {
        pick: typeof w._chronShotPick, intake: typeof w.chronicleShotIntake,
        apply: typeof w.chronicleShotApply, discard: typeof w.chronicleShotDiscard,
        held: typeof w.chronicleShotProposal,
        // the shared path it depends on
        chronApply: typeof w.chronicleApply, undo: typeof w.chronicleUndoLast,
        vocab: typeof w._grailVocab, setHave: typeof w._setHave,
      };
    });
    Object.entries(r).forEach(([k, v]) => expect(v, k + ' must be reachable').toBe('function'));
    const src = fs.readFileSync(path.resolve(__dirname, '..', 'bible.html'), 'utf8');
    expect(src, 'the intake escapes with its OWN helper, not a name from another block')
      .toContain('function _cse(x)');
  });
});
