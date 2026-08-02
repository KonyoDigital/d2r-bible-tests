import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1590 — THE TWO COMPLETED LEDGERS, held to one standard.
//
// Konyo: "for forges COMPLETED section for both F-UNIQUES and F-SETS structure and design this
// better. theres a more intelligent way to tally these right?"
//
// There was, and F·Sets had the least intelligent one available. v1572 gave F·Uniques a dated
// ledger with a live filter and month headings; F·Sets kept a flat wall of piece chips in set
// order — no dates, no grouping, no filter — even though toggleSetPiece has stamped a date into
// the SAME d2r_foundLog since v644. The data was there the whole time and one view read it.
//
// And PIECES ARE THE WRONG UNIT for a set ledger. "108 found" cannot answer either question a set
// ledger exists for: how many sets do I actually have, and which am I close to? The full-set bonus
// is all-or-nothing, so 108 pieces spread across 30 sets and 108 concentrated into 18 complete ones
// are the same number and completely different positions.
//
// These tests pin the SHAPE of both ledgers and the arithmetic behind the numbers, because a tally
// that looks intelligent and adds up wrong is worse than the flat wall it replaced.

async function board(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(2200);
}

test.describe('v1590 — both grail ledgers tell three facts, not one number', () => {
  test('★ F·SETS counts SETS, and the three numbers agree with the scan', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.switchTab('fsets'); w.fsetsSetFilter('done');
      const s = w.fsetsScan();
      const tiles = [...document.querySelectorAll('#tab-fsets .gs-tally .gs-t')]
        .map((t: any) => ({ n: t.querySelector('b').textContent, label: t.querySelector('i').textContent }));
      return {
        tiles,
        scanDone: s.done.length,
        scanWorking: s.sets.filter((x: any) => x.got > 0 && x.left > 0).length,
        havePieces: s.havePieces, totalPieces: s.totalPieces,
        sealedBlocks: document.querySelectorAll('#gs-found-blocks .gs-set-done').length,
        bars: document.querySelectorAll('#gs-found-blocks .gs-bar i').length,
      };
    });
    expect(r.tiles.length, 'three facts, not one').toBe(3);
    expect(Number(r.tiles[0].n), 'sealed count must equal the scan').toBe(r.scanDone);
    expect(Number(r.tiles[1].n), 'in-progress count must equal the scan').toBe(r.scanWorking);
    expect(Number(r.tiles[2].n), 'piece count must equal the scan').toBe(r.havePieces);
    expect(r.sealedBlocks, 'every sealed set gets its own block').toBe(r.scanDone);
    expect(r.bars, 'every in-progress set gets a fill bar').toBe(r.scanWorking);
  });

  test('★ sealed sets are DATED — from the piece store that already had the dates', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.switchTab('fsets'); w.fsetsSetFilter('done');
      const blocks = [...document.querySelectorAll('#gs-found-blocks .gs-set-done')];
      const meta = blocks.map((b: any) => b.querySelector('.gs-set-m').textContent || '');
      return {
        blocks: blocks.length,
        dated: meta.filter((m) => /sealed /.test(m)).length,
        datedChips: document.querySelectorAll('#gs-found-blocks .gp-date').length,
        foundPieces: w.fsetsScan().havePieces,
      };
    });
    expect(r.blocks, 'need at least one sealed set to test with').toBeGreaterThan(0);
    expect(r.dated, 'a sealed set must say WHEN it sealed').toBe(r.blocks);
    expect(r.datedChips, 'every found piece carries its own date, as the uniques ledger does')
      .toBe(r.foundPieces);
  });

  test('★ ONE filter serves both forges — and the uniques ledger still works', async ({ page }) => {
    // The filter was generalised rather than copied. A copy is exactly what REG-090/REG-091 are
    // about, so the risk moved to the OTHER side: the working uniques filter must not regress.
    await board(page);
    const uni = await page.evaluate(() => {
      const w: any = window;
      w.switchTab('funi'); w.funiSetFilter('found');
      const chips = [...document.querySelectorAll('#gf-found-chips .gf-piece')] as any[];
      const mons = [...document.querySelectorAll('#gf-found-chips .gf-mon')] as any[];
      const before = { chips: chips.length, months: mons.length };
      const name = (chips[0].textContent || '').replace(/[✓✕]/g, '').trim().slice(0, 9);
      w._gfFilter(name);
      const narrowed = chips.filter((e) => e.style.display !== 'none').length;
      const monsShown = mons.filter((e) => e.style.display !== 'none').length;
      w._gfFilter('');
      return { before, narrowed, monsShown,
               restored: chips.filter((e) => e.style.display !== 'none').length,
               monsBack: mons.filter((e) => e.style.display !== 'none').length };
    });
    expect(uni.before.chips, 'the uniques ledger must have finds to filter').toBeGreaterThan(10);
    expect(uni.narrowed, 'the filter must narrow').toBeLessThan(uni.before.chips);
    expect(uni.narrowed).toBeGreaterThan(0);
    expect(uni.monsShown, 'a month with no surviving chip must hide').toBeLessThanOrEqual(uni.before.months);
    expect(uni.restored, 'clearing restores every chip').toBe(uni.before.chips);
    expect(uni.monsBack, 'clearing restores every month heading').toBe(uni.before.months);

    const sets = await page.evaluate(() => {
      const w: any = window;
      w.switchTab('fsets'); w.fsetsSetFilter('done');
      const blocks = [...document.querySelectorAll('#gs-found-blocks .gs-set')] as any[];
      const name = (blocks[0].getAttribute('data-grp') || '').slice(0, 8);
      w._gsFilter(name);
      const vis = blocks.filter((e) => e.style.display !== 'none');
      w._gsFilter('');
      return { total: blocks.length, name, visible: vis.length,
               restored: blocks.filter((e) => e.style.display !== 'none').length };
    });
    expect(sets.visible, 'filtering by a SET NAME keeps that set').toBeGreaterThan(0);
    expect(sets.visible, 'and hides the others').toBeLessThan(sets.total);
    expect(sets.restored, 'clearing restores every set block').toBe(sets.total);
  });

  test('★ F·UNIQUES tally adds up to the whole chronicle', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.switchTab('funi'); w.funiSetFilter('found');
      const s = w.funiScan();
      const tiles = [...document.querySelectorAll('#tab-funi .gs-tally .gs-t')]
        .map((t: any) => Number(t.querySelector('b').textContent));
      return { tiles, found: s.found, chronTotal: s.chronTotal };
    });
    expect(r.tiles.length, 'found · still missing · this month').toBe(3);
    expect(r.tiles[0], 'the first number is the found count').toBe(r.found);
    expect(r.tiles[0] + r.tiles[1],
      'found + still missing must equal the whole chronicle, or one of them is lying')
      .toBe(r.chronTotal);
    expect(r.tiles[2], 'this-month can be zero but never negative').toBeGreaterThanOrEqual(0);
    expect(r.tiles[2], 'and never more than the total found').toBeLessThanOrEqual(r.found);
  });
});
