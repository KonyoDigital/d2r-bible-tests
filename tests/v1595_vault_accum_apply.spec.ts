import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1595 — THE VAULT ACCUMULATOR'S WRITE, on the board side.
//
// The console never writes the vault; it asks window.vaultAccumApply. Everything that can go wrong
// here goes wrong QUIETLY, which is why each of these exists:
//
//   MERGE-MAX. The accumulator sweeps sessions in whatever order reels come off disk, and a
//   half-scrolled stash frame is a normal event. If a smaller read can lower a count, the ledger
//   eats his stash one bad frame at a time while looking perfectly healthy.
//
//   THE BASE IS max(memory, localStorage). _snap() prefers the in-memory map and falls back to
//   localStorage. When those disagree — a tab loaded before an import, a store written by another
//   surface — taking one and writing it back DELETES what the other held. The first version of this
//   code did exactly that: localStorage said Ral 9, memory said nothing, and the write put Ral 3 on
//   disk. That is the bug this whole feature exists to not have.
//
//   ROUTE BY KIND. Runes/gems/materials are tallies. A grail item is not, and goes through
//   chronicleApply — the one write path, so it inherits the date, merge-max and the undo bar.
//
//   THROW-OUTS ARE NEVER WRITTEN. There is no un-throw in Diablo.

async function board(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(2200);
}

test.describe('v1595 — the vault accumulator writes through the board, and never subtracts', () => {
  test('★ a SMALLER read never lowers a held count', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.LSR.setItem('d2r_runeStash', JSON.stringify({ Ral: 9 }));
      const out = w.vaultAccumApply({ items: [{ name: 'Ral', kind: 'rune', count: 3 }] });
      return { after: JSON.parse(w.LSR.getItem('d2r_runeStash')), held: out.held, raised: out.raised };
    });
    expect(r.after.Ral,
      'held 9, a later read saw 3 — the count must NOT drop. An obstructed stash frame is normal, ' +
      'not evidence he threw six runes away').toBe(9);
    expect(r.held.join(' '), 'and the shortfall must be reported, not swallowed').toContain('Ral');
    expect(r.raised).toEqual([]);
  });

  test('★ a LARGER read does raise, and a new item is added', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.LSR.setItem('d2r_runeStash', JSON.stringify({ Ist: 1 }));
      const out = w.vaultAccumApply({ items: [
        { name: 'Ist', kind: 'rune', count: 4 },
        { name: 'Tal', kind: 'rune', count: 2 }] });
      return { after: JSON.parse(w.LSR.getItem('d2r_runeStash')), raised: out.raised };
    });
    expect(r.after.Ist).toBe(4);
    expect(r.after.Tal).toBe(2);
    expect(r.raised.length).toBe(2);
  });

  test('★ THE REGRESSION: a value only in localStorage is not destroyed', async ({ page }) => {
    // the exact first-version bug — memory empty, localStorage holding the truth
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      try { if (w.runeStash) Object.keys(w.runeStash).forEach((k) => delete w.runeStash[k]); } catch (e) {}
      w.LSR.setItem('d2r_runeStash', JSON.stringify({ Vex: 2 }));
      w.vaultAccumApply({ items: [{ name: 'Vex', kind: 'rune', count: 1 }] });
      return JSON.parse(w.LSR.getItem('d2r_runeStash'));
    });
    expect(r.Vex,
      'the in-memory map was empty and localStorage held Vex 2 — writing back the empty one would ' +
      'have silently deleted it. The base must be the MAX of both stores.').toBe(2);
  });

  test('★ a throw-out suggestion is counted and NEVER written', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.LSR.setItem('d2r_runeStash', JSON.stringify({ Ral: 5 }));
      const out = w.vaultAccumApply({
        items: [{ name: 'Ral', kind: 'rune', count: 5 }],
        throwOut: [{ name: 'Chipped Topaz' }, { name: 'Cracked Sash' }] });
      const store = JSON.parse(w.LSR.getItem('d2r_runeStash'));
      return { suggestions: out.suggestions, hasTopaz: 'Chipped Topaz' in store, keys: Object.keys(store) };
    });
    expect(r.suggestions, 'the suggestions must be acknowledged in the receipt').toBe(2);
    expect(r.hasTopaz, 'a throw-out must never reach a store — there is no un-throw in Diablo').toBe(false);
    expect(r.keys).toEqual(['Ral']);
  });

  test('★ a grail item goes through chronicleApply, not into a tally store', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      let called: any = null;
      const orig = w.chronicleApply;
      w.chronicleApply = (p: any) => { called = p; return { uniques: ['Shako'], sets: [] }; };
      const out = w.vaultAccumApply({
        items: [{ name: 'Shako', kind: 'item', lane: 'stash', conf: 0.91,
                  witnesses: [{ session: 's_1', frame: 'f_1.jpg' }] }] });
      w.chronicleApply = orig;
      const runes = JSON.parse(w.LSR.getItem('d2r_runeStash') || '{}');
      const rows = (called && called.wouldAdd && called.wouldAdd.uniques) || [];
      return {
        called,
        names: rows.map((x: any) => (x && x.name) || x),   // the row may be a string OR a row object
        row: rows[0],
        grail: out.grail,
        leakedIntoRunes: 'Shako' in runes,
      };
    });
    expect(r.called, 'a grail item must be handed to chronicleApply — the ONE write path').toBeTruthy();
    expect(r.names, 'the payload must NAME the item, whatever shape the row is').toContain('Shako');
    expect(r.leakedIntoRunes, 'and must never be written into a tally store').toBe(false);
    expect(r.grail).toContain('Shako');

    /* ⚠ v1919 — THIS ASSERTION USED TO READ `toContain('Shako')` ON THE ROW ARRAY ITSELF, and v1918
       broke it on CI while every local gate stayed green: carrying provenance turned each row from a
       bare string into {name, lane, conf, witnesses, source}, so the array no longer *contained* the
       string. The test was right to fail — the contract it pinned had changed — and the fix is to
       pin the PROPERTY (the payload names the item) instead of the SHAPE, then pin the new shape
       separately and on purpose, below.

       Why the shape matters and is not incidental: before v1918 a grail item found by the VAULT lane
       arrived at chronicleApply with no reel, no eye and no confidence, so its ledger row could only
       say "accepted from a Chronicle sweep" about an item that never came from the Chronicle.
       [[the-unjoined-end]] */
    expect(typeof r.row, 'the row carries its evidence now, not just a name').toBe('object');
    expect(r.row.lane, 'which surface the vault reader saw it on').toBe('stash');
    expect(r.row.conf, 'and how sure it was').toBe(0.91);
    expect(r.row.source, 'and that it came from the VAULT lane, not the Chronicle').toBe('vault-sweep');
  });

  test('an unreadable count is skipped, never guessed', async ({ page }) => {
    await board(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      w.LSR.setItem('d2r_runeStash', JSON.stringify({}));
      const out = w.vaultAccumApply({ items: [{ name: 'Ohm', kind: 'rune', count: null }] });
      return { store: JSON.parse(w.LSR.getItem('d2r_runeStash')), skipped: out.skipped };
    });
    expect(Object.keys(r.store), 'no count means no row — an invented 1 is a lie about his stash').toEqual([]);
    expect(r.skipped.join(' ')).toContain('Ohm');
  });
});
