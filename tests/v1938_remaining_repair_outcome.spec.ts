import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1938 — THE 116/135 HE ASKED TO SEE FIXED, PINNED ON A REAL BOARD.
 *
 * Konyo, twice: "and sets.. are you sure its 118/135 how is it 87%? ingame im 85%" and then "fix the
 * 118/135 to 116/135 i want to see it fixed!". v1925 shipped the fix — the game's own Chronicle
 * *Remaining* filter, read off his reel, as a negative ledger — and NOTHING pinned the outcome in a
 * browser. tv/test_sets_base_index.py greps the source for the repair's existence; no spec had ever
 * asserted the number it produces. A fix with no guard is a fix that survives until the next edit.
 *
 * WHAT THIS PINS, and each line is a defect that actually happened:
 *   1. the arithmetic closes — 135 roster - 19 the game says he lacks = 116, never 118;
 *   2. the repair removes EXACTLY the names the game named, and invents none;
 *   3. the removals land in d2r_setRepairRemoved (MACHINE truth) and NOT in d2r_grailUnfound
 *      (HIS un-tick). v1925 wrote them into the user store, and eight assertions across four
 *      suites — v1693's nine-conflict resolver among them — read `grailUnfound` and got 2 where
 *      they required 0. Two different claims sharing one store is the whole bug;
 *   4. it is idempotent — a second load does not let the seed floor put them back, which is the
 *      only reason the suppression store has to exist at all.
 */
test.describe('v1938 — the remaining-repair lands on 116/135 and stays there', () => {
  test('★★★ 135 - 19 = 116, the removals are exactly the game’s list, and user truth is untouched',
    async ({ page }) => {
      await page.goto(URL);
      await page.waitForTimeout(1400);

      const roster = await page.evaluate(() => {
        const w: any = window;
        const names: string[] = [];
        (w.__allSets() || []).forEach((s: any) => (s.pieces || []).forEach((p: string) => names.push(p)));
        return { names, missing: ((w._SET_MISSING || {}).names || []) as string[] };
      });
      expect(roster.names.length, 'the set roster is 135 pieces').toBe(135);
      expect(roster.missing.length, 'the game named 19 pieces he does not have').toBe(19);

      /* TICK EVERYTHING, then let the board boot. Starting from a full 135 is what makes the
         subtraction visible: a board that already lacked them could not tell a working repair from
         a repair that never ran. [[feedback_blind_fixture_green_gate]] */
      await page.evaluate((all: string[]) => {
        localStorage.setItem('d2r_setPieces', JSON.stringify(all));
        localStorage.removeItem('d2r_setRepairAt');
        localStorage.removeItem('d2r_setRepairRemoved');
        localStorage.setItem('d2r_grailUnfound', '{}');
      }, roster.names);

      await page.reload();
      await page.waitForTimeout(1600);

      const after = await page.evaluate(() => ({
        pieces: JSON.parse(localStorage.getItem('d2r_setPieces') || '[]') as string[],
        machine: Object.keys(JSON.parse(localStorage.getItem('d2r_setRepairRemoved') || '{}')),
        user: Object.keys(JSON.parse(localStorage.getItem('d2r_grailUnfound') || '{}')),
      }));

      expect(after.pieces.length, 'F·Sets must read 116/135, not 118').toBe(116);
      expect(Math.floor((after.pieces.length / 135) * 100), 'and 85%, the figure on his own screen').toBe(85);

      const stillThere = roster.missing.filter((n) => after.pieces.includes(n));
      expect(stillThere, 'the game says he does not have these and the board still claims them').toEqual([]);

      expect(after.machine.sort(), 'the machine store holds exactly the game’s list')
        .toEqual([...roster.missing].sort());
      expect(after.user, 'a game reading is NOT an un-tick — it must never enter the user store')
        .toEqual([]);

      // idempotent: the seed floor must not resurrect them on the next load
      await page.reload();
      await page.waitForTimeout(1600);
      const again = await page.evaluate(() =>
        (JSON.parse(localStorage.getItem('d2r_setPieces') || '[]') as string[]).length);
      expect(again, 'a second load put removed pieces back').toBe(116);
    });
});
